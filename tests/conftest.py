from __future__ import annotations

import os
import sys

import pytest
import pytest_asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from crypto_alert_bot.models.database import Database
from crypto_alert_bot.services.cache import RedisCache
from crypto_alert_bot.services.chart import ChartService


@pytest_asyncio.fixture
async def db(tmp_path):
    database = Database(str(tmp_path / "test.db"))
    await database.connect()
    yield database
    await database.close()


@pytest.fixture
def cache():
    return RedisCache(host="localhost", port=6379, db=15, ttl=5)


@pytest.fixture
def chart_service():
    return ChartService(default_style="dark")
