from __future__ import annotations

from abc import ABC, abstractmethod

import aiohttp
from loguru import logger

from crypto_alert_bot.models.schemas import ExchangeName, PriceData, PriceHistory
from crypto_alert_bot.utils.exceptions import ExchangeAPIError, InvalidSymbolError


class BaseExchange(ABC):
    def __init__(self, timeout: int = 10) -> None:
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    @abstractmethod
    async def get_price(self, symbol: str) -> PriceData: ...

    @abstractmethod
    async def get_price_history(self, symbol: str, days: int = 7) -> PriceHistory: ...

    @abstractmethod
    async def get_supported_symbols(self) -> list[str]: ...


class BinanceExchange(BaseExchange):
    BASE_URL = "https://api.binance.com/api/v3"

    async def get_price(self, symbol: str) -> PriceData:
        pair = f"{symbol.upper()}USDT"
        url = f"{self.BASE_URL}/ticker/24hr"
        try:
            async with aiohttp.ClientSession(timeout=self._timeout) as session:
                async with session.get(url, params={"symbol": pair}) as resp:
                    if resp.status == 400:
                        raise InvalidSymbolError(symbol)
                    if resp.status != 200:
                        raise ExchangeAPIError("binance", f"HTTP {resp.status}")
                    data = await resp.json()
                    return PriceData(
                        symbol=symbol.upper(),
                        price=float(data["lastPrice"]),
                        exchange="binance",
                        volume_24h=float(data["volume"]),
                        change_24h=float(data["priceChangePercent"]),
                        high_24h=float(data["highPrice"]),
                        low_24h=float(data["lowPrice"]),
                    )
        except (InvalidSymbolError, ExchangeAPIError):
            raise
        except Exception as e:
            logger.error("Binance API error for {}: {}", symbol, e)
            raise ExchangeAPIError("binance", str(e)) from e

    async def get_price_history(self, symbol: str, days: int = 7) -> PriceHistory:
        pair = f"{symbol.upper()}USDT"
        url = f"{self.BASE_URL}/klines"
        interval = "1h" if days <= 7 else "1d"
        limit = min(days * 24, 1000) if days <= 7 else min(days, 365)
        try:
            async with aiohttp.ClientSession(timeout=self._timeout) as session:
                async with session.get(url, params={"symbol": pair, "interval": interval, "limit": limit}) as resp:
                    if resp.status != 200:
                        raise ExchangeAPIError("binance", f"HTTP {resp.status}")
                    data = await resp.json()
                    prices = [(str(candle[0]), float(candle[4])) for candle in data]
                    return PriceHistory(symbol=symbol.upper(), exchange="binance", prices=prices)
        except ExchangeAPIError:
            raise
        except Exception as e:
            logger.error("Binance history error for {}: {}", symbol, e)
            raise ExchangeAPIError("binance", str(e)) from e

    async def get_supported_symbols(self) -> list[str]:
        url = f"{self.BASE_URL}/exchangeInfo"
        try:
            async with aiohttp.ClientSession(timeout=self._timeout) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise ExchangeAPIError("binance", f"HTTP {resp.status}")
                    data = await resp.json()
                    return [
                        s["baseAsset"]
                        for s in data["symbols"]
                        if s["quoteAsset"] == "USDT" and s["status"] == "TRADING"
                    ]
        except ExchangeAPIError:
            raise
        except Exception as e:
            raise ExchangeAPIError("binance", str(e)) from e


class CoinGeckoExchange(BaseExchange):
    BASE_URL = "https://api.coingecko.com/api/v3"
    SYMBOL_MAP: dict[str, str] = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "BNB": "binancecoin",
        "SOL": "solana",
        "XRP": "ripple",
        "ADA": "cardano",
        "DOGE": "dogecoin",
        "DOT": "polkadot",
        "MATIC": "matic-network",
        "LINK": "chainlink",
        "AVAX": "avalanche-2",
        "UNI": "uniswap",
        "ATOM": "cosmos",
        "LTC": "litecoin",
    }

    def _resolve_id(self, symbol: str) -> str:
        coin_id = self.SYMBOL_MAP.get(symbol.upper())
        if not coin_id:
            raise InvalidSymbolError(symbol)
        return coin_id

    async def get_price(self, symbol: str) -> PriceData:
        coin_id = self._resolve_id(symbol)
        url = f"{self.BASE_URL}/coins/{coin_id}"
        params = {"localization": "false", "tickers": "false", "community_data": "false", "developer_data": "false"}
        try:
            async with aiohttp.ClientSession(timeout=self._timeout) as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        raise ExchangeAPIError("coingecko", f"HTTP {resp.status}")
                    data = await resp.json()
                    market = data["market_data"]
                    return PriceData(
                        symbol=symbol.upper(),
                        price=float(market["current_price"]["usd"]),
                        exchange="coingecko",
                        volume_24h=float(market.get("total_volume", {}).get("usd", 0)),
                        change_24h=float(market.get("price_change_percentage_24h", 0)),
                        high_24h=float(market.get("high_24h", {}).get("usd", 0)),
                        low_24h=float(market.get("low_24h", {}).get("usd", 0)),
                    )
        except (InvalidSymbolError, ExchangeAPIError):
            raise
        except Exception as e:
            logger.error("CoinGecko API error for {}: {}", symbol, e)
            raise ExchangeAPIError("coingecko", str(e)) from e

    async def get_price_history(self, symbol: str, days: int = 7) -> PriceHistory:
        coin_id = self._resolve_id(symbol)
        url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
        try:
            async with aiohttp.ClientSession(timeout=self._timeout) as session:
                async with session.get(url, params={"vs_currency": "usd", "days": str(days)}) as resp:
                    if resp.status != 200:
                        raise ExchangeAPIError("coingecko", f"HTTP {resp.status}")
                    data = await resp.json()
                    prices = [(str(int(p[0])), float(p[1])) for p in data["prices"]]
                    return PriceHistory(symbol=symbol.upper(), exchange="coingecko", prices=prices)
        except ExchangeAPIError:
            raise
        except Exception as e:
            logger.error("CoinGecko history error for {}: {}", symbol, e)
            raise ExchangeAPIError("coingecko", str(e)) from e

    async def get_supported_symbols(self) -> list[str]:
        return list(self.SYMBOL_MAP.keys())


class KrakenExchange(BaseExchange):
    BASE_URL = "https://api.kraken.com/0/public"
    SYMBOL_MAP: dict[str, str] = {
        "BTC": "XXBTZUSD",
        "ETH": "XETHZUSD",
        "SOL": "SOLUSD",
        "XRP": "XXRPZUSD",
        "ADA": "ADAUSD",
        "DOT": "DOTUSD",
        "LINK": "LINKUSD",
        "LTC": "XLTCZUSD",
        "DOGE": "XDGUSD",
    }

    def _resolve_pair(self, symbol: str) -> str:
        pair = self.SYMBOL_MAP.get(symbol.upper())
        if not pair:
            raise InvalidSymbolError(symbol)
        return pair

    async def get_price(self, symbol: str) -> PriceData:
        pair = self._resolve_pair(symbol)
        url = f"{self.BASE_URL}/Ticker"
        try:
            async with aiohttp.ClientSession(timeout=self._timeout) as session:
                async with session.get(url, params={"pair": pair}) as resp:
                    if resp.status != 200:
                        raise ExchangeAPIError("kraken", f"HTTP {resp.status}")
                    data = await resp.json()
                    if data.get("error"):
                        raise ExchangeAPIError("kraken", str(data["error"]))
                    ticker = list(data["result"].values())[0]
                    return PriceData(
                        symbol=symbol.upper(),
                        price=float(ticker["c"][0]),
                        exchange="kraken",
                        volume_24h=float(ticker["v"][1]),
                        high_24h=float(ticker["h"][1]),
                        low_24h=float(ticker["l"][1]),
                    )
        except (InvalidSymbolError, ExchangeAPIError):
            raise
        except Exception as e:
            logger.error("Kraken API error for {}: {}", symbol, e)
            raise ExchangeAPIError("kraken", str(e)) from e

    async def get_price_history(self, symbol: str, days: int = 7) -> PriceHistory:
        pair = self._resolve_pair(symbol)
        url = f"{self.BASE_URL}/OHLC"
        interval = 60 if days <= 7 else 1440
        try:
            async with aiohttp.ClientSession(timeout=self._timeout) as session:
                async with session.get(url, params={"pair": pair, "interval": interval}) as resp:
                    if resp.status != 200:
                        raise ExchangeAPIError("kraken", f"HTTP {resp.status}")
                    data = await resp.json()
                    if data.get("error"):
                        raise ExchangeAPIError("kraken", str(data["error"]))
                    ohlc = list(data["result"].values())[0]
                    prices = [(str(int(c[0])), float(c[4])) for c in ohlc]
                    return PriceHistory(symbol=symbol.upper(), exchange="kraken", prices=prices)
        except ExchangeAPIError:
            raise
        except Exception as e:
            logger.error("Kraken history error for {}: {}", symbol, e)
            raise ExchangeAPIError("kraken", str(e)) from e

    async def get_supported_symbols(self) -> list[str]:
        return list(self.SYMBOL_MAP.keys())


class ExchangeFactory:
    _exchanges: dict[str, type[BaseExchange]] = {
        ExchangeName.BINANCE.value: BinanceExchange,
        ExchangeName.COINGECKO.value: CoinGeckoExchange,
        ExchangeName.KRAKEN.value: KrakenExchange,
    }

    @classmethod
    def create(cls, name: str, timeout: int = 10) -> BaseExchange:
        exchange_cls = cls._exchanges.get(name.lower())
        if exchange_cls is None:
            raise ExchangeAPIError(name, "Unsupported exchange")
        return exchange_cls(timeout=timeout)

    @classmethod
    def available(cls) -> list[str]:
        return list(cls._exchanges.keys())
