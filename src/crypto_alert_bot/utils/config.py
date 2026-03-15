from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from crypto_alert_bot.utils.exceptions import ConfigurationError

load_dotenv()


@dataclass(frozen=True)
class BotConfig:
    token: str
    admin_ids: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class RedisConfig:
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    ttl: int = 60


@dataclass(frozen=True)
class DatabaseConfig:
    path: str = "data/crypto_alert.db"


@dataclass(frozen=True)
class ExchangeConfig:
    default_exchange: str = "binance"
    request_timeout: int = 10
    supported_exchanges: tuple[str, ...] = ("binance", "coingecko", "kraken")


@dataclass(frozen=True)
class AlertConfig:
    max_alerts_per_user: int = 20
    check_interval_seconds: int = 30


@dataclass(frozen=True)
class Settings:
    bot: BotConfig
    redis: RedisConfig
    database: DatabaseConfig
    exchange: ExchangeConfig
    alert: AlertConfig


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        raise ConfigurationError("BOT_TOKEN")

    admin_ids_raw = os.getenv("ADMIN_IDS", "")
    admin_ids = [int(x.strip()) for x in admin_ids_raw.split(",") if x.strip()]

    db_path = os.getenv("DATABASE_PATH", "data/crypto_alert.db")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    return Settings(
        bot=BotConfig(token=token, admin_ids=admin_ids),
        redis=RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            ttl=int(os.getenv("REDIS_TTL", "60")),
        ),
        database=DatabaseConfig(path=db_path),
        exchange=ExchangeConfig(
            default_exchange=os.getenv("DEFAULT_EXCHANGE", "binance"),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "10")),
        ),
        alert=AlertConfig(
            max_alerts_per_user=int(os.getenv("MAX_ALERTS_PER_USER", "20")),
            check_interval_seconds=int(os.getenv("CHECK_INTERVAL", "30")),
        ),
    )
