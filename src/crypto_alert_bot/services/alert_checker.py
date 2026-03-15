from __future__ import annotations

from datetime import datetime

from loguru import logger

from crypto_alert_bot.models.database import Database
from crypto_alert_bot.models.schemas import AlertDirection, AlertStatus, PriceData
from crypto_alert_bot.services.cache import RedisCache
from crypto_alert_bot.services.exchange import ExchangeFactory
from crypto_alert_bot.utils.exceptions import ExchangeAPIError


class AlertChecker:
    def __init__(self, database: Database, cache: RedisCache, exchange_timeout: int = 10) -> None:
        self._db = database
        self._cache = cache
        self._exchange_timeout = exchange_timeout
        self._price_cache: dict[str, PriceData] = {}

    async def _fetch_price(self, symbol: str, exchange_name: str) -> PriceData | None:
        cache_key = f"{exchange_name}:{symbol}"
        if cache_key in self._price_cache:
            return self._price_cache[cache_key]

        cached = await self._cache.get_price(symbol, exchange_name)
        if cached:
            self._price_cache[cache_key] = cached
            return cached

        try:
            exchange = ExchangeFactory.create(exchange_name, timeout=self._exchange_timeout)
            price_data = await exchange.get_price(symbol)
            await self._cache.set_price(price_data)
            self._price_cache[cache_key] = price_data
            return price_data
        except ExchangeAPIError as e:
            logger.warning("Failed to fetch price for {} on {}: {}", symbol, exchange_name, e)
            return None

    def _is_triggered(self, direction: AlertDirection, target_price: float, current_price: float) -> bool:
        if direction == AlertDirection.ABOVE:
            return current_price >= target_price
        return current_price <= target_price

    async def check_alerts(self) -> list[tuple[int, str, float, float, str]]:
        self._price_cache.clear()
        triggered: list[tuple[int, str, float, float, str]] = []

        alerts = await self._db.get_all_active_alerts()
        if not alerts:
            return triggered

        logger.debug("Checking {} active alerts", len(alerts))

        for alert in alerts:
            price_data = await self._fetch_price(alert.symbol, alert.exchange)
            if price_data is None:
                continue

            if self._is_triggered(alert.direction, alert.target_price, price_data.price):
                now = datetime.utcnow().isoformat()
                await self._db.update_alert_status(alert.id, AlertStatus.TRIGGERED, triggered_at=now)
                triggered.append((
                    alert.user_id,
                    alert.symbol,
                    alert.target_price,
                    price_data.price,
                    alert.direction.value,
                ))
                logger.info(
                    "Alert triggered: user={} symbol={} target={} current={} direction={}",
                    alert.user_id,
                    alert.symbol,
                    alert.target_price,
                    price_data.price,
                    alert.direction.value,
                )

        return triggered
