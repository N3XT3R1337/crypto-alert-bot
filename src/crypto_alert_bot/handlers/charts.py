from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from loguru import logger

from crypto_alert_bot.keyboards.inline import chart_timeframe_selector, symbol_selector
from crypto_alert_bot.models.database import Database
from crypto_alert_bot.services.chart import ChartService
from crypto_alert_bot.services.exchange import ExchangeFactory
from crypto_alert_bot.utils.exceptions import ChartGenerationError, ExchangeAPIError, InvalidSymbolError

router = Router(name="charts")


@router.message(Command("chart"))
async def cmd_chart(message: Message) -> None:
    if message.text is None:
        return
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer(
            "\U0001f4ca Select a cryptocurrency for chart:",
            reply_markup=symbol_selector(),
        )
        return
    symbol = parts[1].upper()
    await message.answer(
        f"\U0001f4ca Select timeframe for <b>{symbol}</b>:",
        parse_mode="HTML",
        reply_markup=chart_timeframe_selector(symbol),
    )


@router.message(F.text == "\U0001f4ca Chart")
async def menu_chart(message: Message) -> None:
    await message.answer(
        "\U0001f4ca Select a cryptocurrency for chart:",
        reply_markup=symbol_selector(),
    )


@router.callback_query(F.data.startswith("chart:"))
async def on_chart_timeframe(callback: CallbackQuery, db: Database) -> None:
    if callback.data is None or callback.message is None:
        return
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Invalid selection")
        return

    symbol = parts[1]
    days = int(parts[2])
    await callback.answer(f"Generating {symbol} chart...")

    user = await db.get_user(callback.from_user.id)
    exchange_name = user.preferred_exchange if user else "binance"
    prefs = await db.get_preferences(callback.from_user.id)

    try:
        exchange = ExchangeFactory.create(exchange_name)
        history = await exchange.get_price_history(symbol, days=days)
        chart_svc = ChartService(default_style=prefs.chart_style)
        buf = chart_svc.generate_price_chart(history, style=prefs.chart_style)
        photo = BufferedInputFile(buf.read(), filename=f"{symbol}_chart.png")
        await callback.message.answer_photo(
            photo=photo,
            caption=f"\U0001f4ca <b>{symbol}/USD</b> — {days}D chart via {exchange_name.capitalize()}",
            parse_mode="HTML",
        )
    except InvalidSymbolError:
        await callback.message.answer(f"\u274c Symbol <b>{symbol}</b> not supported.", parse_mode="HTML")
    except ExchangeAPIError as e:
        logger.error("Chart data error: {}", e)
        await callback.message.answer("\u26a0\ufe0f Failed to fetch chart data.")
    except ChartGenerationError as e:
        logger.error("Chart render error: {}", e)
        await callback.message.answer("\u26a0\ufe0f Failed to generate chart.")
