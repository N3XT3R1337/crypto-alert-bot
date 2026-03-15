from __future__ import annotations

import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from crypto_alert_bot.handlers import alerts, charts, prices, start
from crypto_alert_bot.models.database import Database
from crypto_alert_bot.services.alert_checker import AlertChecker
from crypto_alert_bot.services.cache import RedisCache
from crypto_alert_bot.utils.config import load_settings
from crypto_alert_bot.utils.logging import setup_logging


async def on_alert_triggered(bot: Bot, user_id: int, symbol: str, target: float, current: float, direction: str) -> None:
    arrow = "\u2b06" if direction == "above" else "\u2b07"
    text = (
        f"\U0001f6a8 <b>Alert Triggered!</b>\n\n"
        f"{arrow} <b>{symbol}</b> is now {direction} your target\n"
        f"\U0001f3af Target: <code>${target:,.2f}</code>\n"
        f"\U0001f4b0 Current: <code>${current:,.2f}</code>"
    )
    try:
        await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
    except Exception as e:
        logger.error("Failed to notify user {}: {}", user_id, e)


async def scheduled_alert_check(bot: Bot, checker: AlertChecker) -> None:
    try:
        triggered = await checker.check_alerts()
        for user_id, symbol, target, current, direction in triggered:
            await on_alert_triggered(bot, user_id, symbol, target, current, direction)
        if triggered:
            logger.info("Alert check complete: {} alerts triggered", len(triggered))
    except Exception as e:
        logger.error("Alert check failed: {}", e)


async def main() -> None:
    setup_logging()
    settings = load_settings()

    bot = Bot(
        token=settings.bot.token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    db = Database(settings.database.path)
    await db.connect()

    cache = RedisCache(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        ttl=settings.redis.ttl,
    )
    await cache.connect()

    checker = AlertChecker(db, cache, exchange_timeout=settings.exchange.request_timeout)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scheduled_alert_check,
        "interval",
        seconds=settings.alert.check_interval_seconds,
        args=[bot, checker],
        id="alert_check",
        replace_existing=True,
    )
    scheduler.start()

    dp.include_router(start.router)
    dp.include_router(prices.router)
    dp.include_router(charts.router)
    dp.include_router(alerts.router)

    dp["db"] = db
    dp["cache"] = cache
    dp["settings"] = settings

    logger.info("Bot starting...")

    try:
        await dp.start_polling(bot, db=db, cache=cache, settings=settings)
    finally:
        scheduler.shutdown()
        await cache.close()
        await db.close()
        await bot.session.close()
        logger.info("Bot stopped")


def run() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown by user")
    except Exception as e:
        logger.critical("Fatal error: {}", e)
        sys.exit(1)


if __name__ == "__main__":
    run()
