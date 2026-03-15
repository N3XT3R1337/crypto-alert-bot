from __future__ import annotations

import pytest

from crypto_alert_bot.models.database import Database
from crypto_alert_bot.models.schemas import Alert, AlertDirection, AlertStatus, User
from crypto_alert_bot.services.alert_checker import AlertChecker
from crypto_alert_bot.services.cache import RedisCache


@pytest.mark.asyncio
async def test_alert_status_update(db: Database) -> None:
    user = User(user_id=500, username="statususer")
    await db.upsert_user(user)

    alert = Alert(
        id=None,
        user_id=500,
        symbol="BTC",
        target_price=45000.0,
        direction=AlertDirection.ABOVE,
    )
    alert_id = await db.create_alert(alert)

    await db.update_alert_status(alert_id, AlertStatus.TRIGGERED, triggered_at="2025-01-01T00:00:00")

    alerts = await db.get_user_alerts(500, status=AlertStatus.TRIGGERED)
    assert len(alerts) == 1
    assert alerts[0].status == AlertStatus.TRIGGERED
    assert alerts[0].triggered_at == "2025-01-01T00:00:00"


@pytest.mark.asyncio
async def test_get_all_active_alerts(db: Database) -> None:
    for uid in [601, 602, 603]:
        user = User(user_id=uid, username=f"user{uid}")
        await db.upsert_user(user)
        alert = Alert(
            id=None,
            user_id=uid,
            symbol="ETH",
            target_price=3000.0,
            direction=AlertDirection.BELOW,
        )
        await db.create_alert(alert)

    active = await db.get_all_active_alerts()
    assert len(active) >= 3


def test_is_triggered_above() -> None:
    cache = RedisCache()
    checker = AlertChecker(database=None, cache=cache)
    assert checker._is_triggered(AlertDirection.ABOVE, 50000.0, 51000.0) is True
    assert checker._is_triggered(AlertDirection.ABOVE, 50000.0, 49000.0) is False
    assert checker._is_triggered(AlertDirection.ABOVE, 50000.0, 50000.0) is True


def test_is_triggered_below() -> None:
    cache = RedisCache()
    checker = AlertChecker(database=None, cache=cache)
    assert checker._is_triggered(AlertDirection.BELOW, 50000.0, 49000.0) is True
    assert checker._is_triggered(AlertDirection.BELOW, 50000.0, 51000.0) is False
    assert checker._is_triggered(AlertDirection.BELOW, 50000.0, 50000.0) is True
