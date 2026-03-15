from __future__ import annotations

import pytest

from crypto_alert_bot.models.schemas import (
    Alert,
    AlertDirection,
    AlertStatus,
    PriceData,
    User,
    UserPreferences,
)
from crypto_alert_bot.models.database import Database


@pytest.mark.asyncio
async def test_upsert_and_get_user(db: Database) -> None:
    user = User(user_id=12345, username="testuser")
    await db.upsert_user(user)
    fetched = await db.get_user(12345)
    assert fetched is not None
    assert fetched.user_id == 12345
    assert fetched.username == "testuser"
    assert fetched.preferred_exchange == "binance"


@pytest.mark.asyncio
async def test_get_nonexistent_user(db: Database) -> None:
    fetched = await db.get_user(99999)
    assert fetched is None


@pytest.mark.asyncio
async def test_create_and_list_alerts(db: Database) -> None:
    user = User(user_id=100, username="alertuser")
    await db.upsert_user(user)

    alert = Alert(
        id=None,
        user_id=100,
        symbol="BTC",
        target_price=50000.0,
        direction=AlertDirection.ABOVE,
        exchange="binance",
    )
    alert_id = await db.create_alert(alert)
    assert alert_id > 0

    alerts = await db.get_user_alerts(100, status=AlertStatus.ACTIVE)
    assert len(alerts) == 1
    assert alerts[0].symbol == "BTC"
    assert alerts[0].target_price == 50000.0
    assert alerts[0].direction == AlertDirection.ABOVE


@pytest.mark.asyncio
async def test_delete_alert(db: Database) -> None:
    user = User(user_id=200, username="deluser")
    await db.upsert_user(user)

    alert = Alert(
        id=None,
        user_id=200,
        symbol="ETH",
        target_price=3000.0,
        direction=AlertDirection.BELOW,
    )
    alert_id = await db.create_alert(alert)
    deleted = await db.delete_alert(alert_id, 200)
    assert deleted is True

    alerts = await db.get_user_alerts(200)
    assert len(alerts) == 0


@pytest.mark.asyncio
async def test_count_user_alerts(db: Database) -> None:
    user = User(user_id=300, username="countuser")
    await db.upsert_user(user)

    for i in range(5):
        alert = Alert(
            id=None,
            user_id=300,
            symbol=f"SYM{i}",
            target_price=float(i * 100),
            direction=AlertDirection.ABOVE,
        )
        await db.create_alert(alert)

    count = await db.count_user_alerts(300)
    assert count == 5


@pytest.mark.asyncio
async def test_preferences(db: Database) -> None:
    user = User(user_id=400, username="prefuser")
    await db.upsert_user(user)

    prefs = UserPreferences(user_id=400, default_symbols=["SOL", "AVAX"], chart_style="light")
    await db.save_preferences(prefs)

    loaded = await db.get_preferences(400)
    assert loaded.default_symbols == ["SOL", "AVAX"]
    assert loaded.chart_style == "light"
    assert loaded.notification_enabled is True


def test_price_data_creation() -> None:
    pd = PriceData(symbol="BTC", price=50000.0, exchange="binance")
    assert pd.symbol == "BTC"
    assert pd.price == 50000.0
    assert pd.timestamp != ""


def test_alert_symbol_uppercase() -> None:
    alert = Alert(
        id=None,
        user_id=1,
        symbol="btc",
        target_price=100.0,
        direction=AlertDirection.ABOVE,
    )
    assert alert.symbol == "BTC"


def test_user_defaults() -> None:
    user = User(user_id=1)
    assert user.preferred_exchange == "binance"
    assert user.preferred_currency == "USD"
    assert user.created_at != ""
