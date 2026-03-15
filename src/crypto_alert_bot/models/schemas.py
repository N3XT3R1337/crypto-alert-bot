from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AlertDirection(str, Enum):
    ABOVE = "above"
    BELOW = "below"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISABLED = "disabled"


class ExchangeName(str, Enum):
    BINANCE = "binance"
    COINGECKO = "coingecko"
    KRAKEN = "kraken"


@dataclass
class User:
    user_id: int
    username: str = ""
    preferred_exchange: str = "binance"
    preferred_currency: str = "USD"
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class Alert:
    id: int | None
    user_id: int
    symbol: str
    target_price: float
    direction: AlertDirection
    exchange: str = "binance"
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: str = ""
    triggered_at: str | None = None

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self.symbol = self.symbol.upper()


@dataclass
class PriceData:
    symbol: str
    price: float
    exchange: str
    timestamp: str = ""
    volume_24h: float = 0.0
    change_24h: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class PriceHistory:
    symbol: str
    exchange: str
    prices: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class UserPreferences:
    user_id: int
    default_symbols: list[str] = field(default_factory=lambda: ["BTC", "ETH"])
    chart_style: str = "dark"
    notification_enabled: bool = True
