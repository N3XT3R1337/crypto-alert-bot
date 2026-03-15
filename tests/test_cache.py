from __future__ import annotations

import pytest

from crypto_alert_bot.models.schemas import PriceData
from crypto_alert_bot.services.cache import RedisCache


def test_cache_not_available_by_default() -> None:
    cache = RedisCache()
    assert cache.is_available is False


@pytest.mark.asyncio
async def test_cache_get_returns_none_when_unavailable() -> None:
    cache = RedisCache()
    result = await cache.get_price("BTC", "binance")
    assert result is None


@pytest.mark.asyncio
async def test_cache_set_noop_when_unavailable() -> None:
    cache = RedisCache()
    pd = PriceData(symbol="BTC", price=50000.0, exchange="binance")
    await cache.set_price(pd)


@pytest.mark.asyncio
async def test_cache_invalidate_noop_when_unavailable() -> None:
    cache = RedisCache()
    await cache.invalidate("BTC", "binance")


def test_cache_price_key() -> None:
    cache = RedisCache()
    key = cache._price_key("btc", "binance")
    assert key == "price:binance:BTC"
