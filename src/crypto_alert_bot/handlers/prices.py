from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from loguru import logger

from crypto_alert_bot.keyboards.inline import exchange_selector, symbol_selector
from crypto_alert_bot.models.database import Database
from crypto_alert_bot.services.cache import RedisCache
from crypto_alert_bot.services.exchange import ExchangeFactory
from crypto_alert_bot.utils.exceptions import ExchangeAPIError, InvalidSymbolError

router = Router(name="prices")


def _format_price(symbol: str, price: float, change: float, high: float, low: float, exchange: str) -> str:
    arrow = "\U0001f7e2" if change >= 0 else "\U0001f534"
    sign = "+" if change >= 0 else ""
    return (
        f"{arrow} <b>{symbol}/USD</b> — <code>${price:,.2f}</code>\n"
        f"\U0001f4c8 24h: {sign}{change:.2f}%\n"
        f"\U0001f4c8 High: ${high:,.2f} | Low: ${low:,.2f}\n"
        f"\U0001f3e6 Exchange: {exchange.capitalize()}"
    )


@router.message(Command("price"))
async def cmd_price(message: Message, db: Database, cache: RedisCache) -> None:
    if message.text is None:
        return
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer(
            "\U0001f4b0 Select a cryptocurrency:",
            reply_markup=symbol_selector(),
        )
        return
    symbol = parts[1].upper()
    user = await db.get_user(message.from_user.id) if message.from_user else None
    exchange_name = user.preferred_exchange if user else "binance"
    await _send_price(message, symbol, exchange_name, cache)


@router.message(F.text == "\U0001f4b0 Prices")
async def menu_prices(message: Message) -> None:
    await message.answer(
        "\U0001f4b0 Select a cryptocurrency:",
        reply_markup=symbol_selector(),
    )


@router.callback_query(F.data.startswith("symbol:"))
async def on_symbol_selected(callback: CallbackQuery, db: Database, cache: RedisCache) -> None:
    if callback.data is None or callback.message is None:
        return
    symbol = callback.data.split(":")[1]
    user = await db.get_user(callback.from_user.id)
    exchange_name = user.preferred_exchange if user else "binance"
    await callback.answer()
    await _send_price(callback.message, symbol, exchange_name, cache)


async def _send_price(target: Message, symbol: str, exchange_name: str, cache: RedisCache) -> None:
    cached = await cache.get_price(symbol, exchange_name)
    if cached:
        text = _format_price(
            cached.symbol, cached.price, cached.change_24h,
            cached.high_24h, cached.low_24h, cached.exchange,
        )
        await target.answer(text, parse_mode="HTML")
        return

    try:
        exchange = ExchangeFactory.create(exchange_name)
        price_data = await exchange.get_price(symbol)
        await cache.set_price(price_data)
        text = _format_price(
            price_data.symbol, price_data.price, price_data.change_24h,
            price_data.high_24h, price_data.low_24h, price_data.exchange,
        )
        await target.answer(text, parse_mode="HTML")
    except InvalidSymbolError:
        await target.answer(f"\u274c Symbol <b>{symbol}</b> not found on {exchange_name}.", parse_mode="HTML")
    except ExchangeAPIError as e:
        logger.error("Price fetch error: {}", e)
        await target.answer("\u26a0\ufe0f Failed to fetch price. Try again later.")
