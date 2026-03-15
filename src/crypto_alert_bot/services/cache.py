from __future__ import annotations

import json
from typing import Any

from loguru import logger

from crypto_alert_bot.models.schemas import PriceData
from crypto_alert_bot.utils.exceptions import CacheConnectionError

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None


class RedisCache:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, ttl: int = 60) -> None:
        self._host = host
        self._port = port
        self._db = db
        self._ttl = ttl
        self._client: Any = None
        self._available = False

    async def connect(self) -> None:
        if aioredis is None:
            logger.warning("redis package not installed, cache disabled")
            return
        try:
            self._client = aioredis.Redis(host=self._host, port=self._port, db=self._db, decode_responses=True)
            await self._client.ping()
            self._available = True
            logger.info("Redis connected at {}:{}", self._host, self._port)
        except Exception as e:
            logger.warning("Redis unavailable, running without cache: {}", e)
            self._available = False

    async def close(self) -> None:
        if self._client and self._available:
            await self._client.close()
            logger.info("Redis connection closed")

    @property
    def is_available(self) -> bool:
        return self._available

    def _price_key(self, symbol: str, exchange: str) -> str:
        return f"price:{exchange}:{symbol.upper()}"

    async def get_price(self, symbol: str, exchange: str) -> PriceData | None:
        if not self._available:
            return None
        try:
            key = self._price_key(symbol, exchange)
            data = await self._client.get(key)
            if data is None:
                return None
            parsed = json.loads(data)
            return PriceData(**parsed)
        except Exception as e:
            logger.warning("Cache read error: {}", e)
            return None

    async def set_price(self, price_data: PriceData) -> None:
        if not self._available:
            return
        try:
            key = self._price_key(price_data.symbol, price_data.exchange)
            data = json.dumps({
                "symbol": price_data.symbol,
                "price": price_data.price,
                "exchange": price_data.exchange,
                "timestamp": price_data.timestamp,
                "volume_24h": price_data.volume_24h,
                "change_24h": price_data.change_24h,
                "high_24h": price_data.high_24h,
                "low_24h": price_data.low_24h,
            })
            await self._client.setex(key, self._ttl, data)
        except Exception as e:
            logger.warning("Cache write error: {}", e)

    async def invalidate(self, symbol: str, exchange: str) -> None:
        if not self._available:
            return
        try:
            key = self._price_key(symbol, exchange)
            await self._client.delete(key)
        except Exception as e:
            logger.warning("Cache invalidate error: {}", e)

    async def flush_all(self) -> None:
        if not self._available:
            return
        try:
            await self._client.flushdb()
            logger.info("Cache flushed")
        except Exception as e:
            raise CacheConnectionError(str(e)) from e
