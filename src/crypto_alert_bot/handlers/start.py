from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from loguru import logger

from crypto_alert_bot.keyboards.reply import main_menu
from crypto_alert_bot.models.database import Database
from crypto_alert_bot.models.schemas import User

router = Router(name="start")

WELCOME_TEXT = (
    "\U0001f680 <b>Welcome to Crypto Alert Bot!</b>\n\n"
    "Monitor cryptocurrency prices across multiple exchanges "
    "and get notified when they hit your target.\n\n"
    "<b>Features:</b>\n"
    "\u2022 Real-time prices from Binance, CoinGecko, Kraken\n"
    "\u2022 Customizable price alerts\n"
    "\u2022 Interactive charts\n"
    "\u2022 Multiple exchange support\n\n"
    "Use the menu below to get started!"
)

HELP_TEXT = (
    "\U0001f4d6 <b>How to use Crypto Alert Bot</b>\n\n"
    "<b>Commands:</b>\n"
    "/start — Show welcome message\n"
    "/price [symbol] — Get current price\n"
    "/chart [symbol] — View price chart\n"
    "/alert [symbol] [price] — Create alert\n"
    "/alerts — List your alerts\n"
    "/settings — Bot settings\n"
    "/help — Show this message\n\n"
    "<b>Menu buttons:</b>\n"
    "\U0001f4b0 Prices — Quick price check\n"
    "\U0001f4ca Chart — View price charts\n"
    "\U0001f514 My Alerts — Manage alerts\n"
    "\u2795 New Alert — Create new alert\n"
    "\u2699\ufe0f Settings — Configure bot\n\n"
    "<b>Supported exchanges:</b> Binance, CoinGecko, Kraken"
)


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database) -> None:
    if message.from_user is None:
        return
    user = User(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
    )
    await db.upsert_user(user)
    logger.info("User {} started the bot", message.from_user.id)
    await message.answer(WELCOME_TEXT, parse_mode="HTML", reply_markup=main_menu())


@router.message(Command("help"))
@router.message(F.text == "\u2753 Help")
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode="HTML")
