from __future__ import annotations

import pytest

from crypto_alert_bot.services.exchange import (
    BinanceExchange,
    CoinGeckoExchange,
    ExchangeFactory,
    KrakenExchange,
)
from crypto_alert_bot.utils.exceptions import ExchangeAPIError, InvalidSymbolError


def test_exchange_factory_create() -> None:
    exchange = ExchangeFactory.create("binance")
    assert isinstance(exchange, BinanceExchange)

    exchange = ExchangeFactory.create("coingecko")
    assert isinstance(exchange, CoinGeckoExchange)

    exchange = ExchangeFactory.create("kraken")
    assert isinstance(exchange, KrakenExchange)


def test_exchange_factory_unsupported() -> None:
    with pytest.raises(ExchangeAPIError):
        ExchangeFactory.create("nonexistent")


def test_exchange_factory_available() -> None:
    available = ExchangeFactory.available()
    assert "binance" in available
    assert "coingecko" in available
    assert "kraken" in available
    assert len(available) == 3


def test_coingecko_resolve_id() -> None:
    cg = CoinGeckoExchange()
    assert cg._resolve_id("BTC") == "bitcoin"
    assert cg._resolve_id("ETH") == "ethereum"


def test_coingecko_invalid_symbol() -> None:
    cg = CoinGeckoExchange()
    with pytest.raises(InvalidSymbolError):
        cg._resolve_id("FAKECOIN999")


def test_kraken_resolve_pair() -> None:
    kr = KrakenExchange()
    assert kr._resolve_pair("BTC") == "XXBTZUSD"
    assert kr._resolve_pair("ETH") == "XETHZUSD"


def test_kraken_invalid_symbol() -> None:
    kr = KrakenExchange()
    with pytest.raises(InvalidSymbolError):
        kr._resolve_pair("NOTREAL")
