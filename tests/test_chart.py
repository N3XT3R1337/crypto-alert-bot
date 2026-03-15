from __future__ import annotations

import io

import pytest

from crypto_alert_bot.models.schemas import PriceHistory
from crypto_alert_bot.services.chart import ChartService
from crypto_alert_bot.utils.exceptions import ChartGenerationError


def test_generate_chart_dark() -> None:
    svc = ChartService(default_style="dark")
    history = PriceHistory(
        symbol="BTC",
        exchange="binance",
        prices=[
            ("1700000000", 42000.0),
            ("1700003600", 42500.0),
            ("1700007200", 41800.0),
            ("1700010800", 43000.0),
            ("1700014400", 43200.0),
        ],
    )
    buf = svc.generate_price_chart(history)
    assert isinstance(buf, io.BytesIO)
    data = buf.read()
    assert len(data) > 0
    assert data[:8].startswith(b"\x89PNG")


def test_generate_chart_light() -> None:
    svc = ChartService(default_style="light")
    history = PriceHistory(
        symbol="ETH",
        exchange="coingecko",
        prices=[
            ("1700000000", 2000.0),
            ("1700003600", 2050.0),
            ("1700007200", 1980.0),
        ],
    )
    buf = svc.generate_price_chart(history, style="light")
    assert isinstance(buf, io.BytesIO)
    data = buf.read()
    assert data[:8].startswith(b"\x89PNG")


def test_generate_chart_empty_prices() -> None:
    svc = ChartService()
    history = PriceHistory(symbol="SOL", exchange="binance", prices=[])
    with pytest.raises(ChartGenerationError):
        svc.generate_price_chart(history)


def test_chart_service_default_style() -> None:
    svc = ChartService(default_style="light")
    assert svc._default_style == "light"
