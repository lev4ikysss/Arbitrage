import requests
import asyncio
import aiohttp
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class Birga(Enum):
    BYBIT = "Bybit"
    MEXC = "Mexc"
    GATE = "Gate"
    HTX = "HTX"
    BITMART = "Bitmart"
    KUCOIN = "Kucoin"
    OKX = "OKX"
    COINEX = "Coinex"
    POLONIEX = "Poloniex"
    BINGX = "BingX"


@dataclass
class OrderBookEntry:
    price: float
    quantity: float


@dataclass
class OrderBook:
    bids: list[OrderBookEntry]
    asks: list[OrderBookEntry]
    symbol: str
    birga: Birga


class BirgaAPI:
    """Базовый класс для работы с API бирж"""

    name: Birga
    base_url: str
    session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def get_orderbook(self, symbol: str, limit: int = 10) -> Optional[OrderBook]:
        """Получить книгу ордеров"""
        raise NotImplementedError

    async def get_all_symbols(self) -> list[str]:
        """Получить список всех USDT-пар на бирже"""
        raise NotImplementedError

    def _normalize_symbol(self, symbol: str) -> str:
        """Нормализовать символ для API биржи (USDT -> USDT)"""
        return symbol.upper()

    def _format_symbol(self, symbol: str) -> str:
        """Формат символа для API конкретной биржи"""
        raise NotImplementedError

    def _parse_symbol(self, raw_symbol: str, quote: str = "USDT") -> Optional[str]:
        """Из сырого символа биржи получить нормализованный (BASE/QUOTE)"""
        raise NotImplementedError

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()


class BybitAPI(BirgaAPI):
    name = Birga.BYBIT
    base_url = "https://api.bybit.com"

    def _format_symbol(self, symbol: str) -> str:
        s = symbol.upper().replace("/", "")
        return f"{s}"

    def _parse_symbol(self, raw_symbol: str, quote: str = "USDT") -> Optional[str]:
        # Bybit returns symbols like "ATOMUSDT"
        if raw_symbol.endswith(quote):
            base = raw_symbol[:-len(quote)]
            return f"{base}/{quote}"
        return None

    async def get_orderbook(self, symbol: str, limit: int = 10) -> Optional[OrderBook]:
        try:
            session = await self._get_session()
            formatted = self._format_symbol(symbol)
            url = f"{self.base_url}/v5/market/orderbook"
            params = {"category": "spot", "symbol": formatted, "limit": limit}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if data.get("retCode") != 0:
                    return None
                result = data.get("result", {})
                bids = [OrderBookEntry(float(b[0]), float(b[1])) for b in result.get("b", [])[:limit]]
                asks = [OrderBookEntry(float(a[0]), float(a[1])) for a in result.get("a", [])[:limit]]
                return OrderBook(bids=bids, asks=asks, symbol=symbol, birga=self.name)
        except Exception:
            return None

    async def get_all_symbols(self) -> list[str]:
        try:
            session = await self._get_session()
            url = f"{self.base_url}/v5/market/instruments-info"
            params = {"category": "spot"}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                if data.get("retCode") != 0:
                    return []
                result = data.get("result", {})
                symbols = []
                for item in result.get("list", []):
                    if item.get("quoteCoin") == "USDT":
                        sym = self._parse_symbol(item.get("symbol", ""))
                        if sym:
                            symbols.append(sym)
                return symbols
        except Exception:
            return []


class MexcAPI(BirgaAPI):
    name = Birga.MEXC
    base_url = "https://api.mexc.com"

    def _format_symbol(self, symbol: str) -> str:
        return symbol.upper().replace("/", "")

    def _parse_symbol(self, raw_symbol: str, quote: str = "USDT") -> Optional[str]:
        if raw_symbol.endswith(quote):
            base = raw_symbol[:-len(quote)]
            return f"{base}/{quote}"
        return None

    async def get_orderbook(self, symbol: str, limit: int = 10) -> Optional[OrderBook]:
        try:
            session = await self._get_session()
            formatted = self._format_symbol(symbol)
            url = f"{self.base_url}/api/v3/market/orderbook"
            params = {"symbol": formatted, "limit": limit}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                bids = [OrderBookEntry(float(b[0]), float(b[1])) for b in data.get("bids", [])[:limit]]
                asks = [OrderBookEntry(float(a[0]), float(a[1])) for a in data.get("asks", [])[:limit]]
                return OrderBook(bids=bids, asks=asks, symbol=symbol, birga=self.name)
        except Exception:
            return None

    async def get_all_symbols(self) -> list[str]:
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/v3/exchangeInfo"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                symbols = []
                for item in data.get("symbols", []):
                    if item.get("quoteAsset") == "USDT" and item.get("status") == "1" and item.get("isSpotTradingAllowed"):
                        base = item.get("baseAsset", "")
                        symbols.append(f"{base}/USDT")
                return symbols
        except Exception:
            return []


class GateAPI(BirgaAPI):
    name = Birga.GATE
    base_url = "https://api.gateio.ws"

    def _format_symbol(self, symbol: str) -> str:
        s = symbol.upper().replace("/", "_")
        return f"{s}_USDT" if "_" not in s else s

    def _parse_symbol(self, raw_symbol: str, quote: str = "USDT") -> Optional[str]:
        # Gate uses format BASE_QUOTE, e.g. ATOM_USDT
        if raw_symbol.endswith(f"_{quote}"):
            base = raw_symbol[:-len(quote)-1]
            return f"{base}/{quote}"
        return None

    async def get_orderbook(self, symbol: str, limit: int = 10) -> Optional[OrderBook]:
        try:
            session = await self._get_session()
            formatted = self._format_symbol(symbol)
            url = f"{self.base_url}/api/v4/spot/order_book"
            params = {"currency_pair": formatted, "limit": limit}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                bids = [OrderBookEntry(float(b[0]), float(b[1])) for b in data.get("bids", [])[:limit]]
                asks = [OrderBookEntry(float(a[0]), float(a[1])) for a in data.get("asks", [])[:limit]]
                return OrderBook(bids=bids, asks=asks, symbol=symbol, birga=self.name)
        except Exception:
            return None

    async def get_all_symbols(self) -> list[str]:
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/v4/spot/currencies"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                # Gate has separate endpoint for pairs
                url2 = f"{self.base_url}/api/v4/spot/tickers"
                async with session.get(url2, timeout=aiohttp.ClientTimeout(total=10)) as resp2:
                    if resp2.status != 200:
                        return []
                    tickers = await resp2.json()
                    symbols = []
                    for t in tickers:
                        currency_pair = t.get("currency_pair", "")
                        if currency_pair.endswith("_USDT"):
                            sym = self._parse_symbol(currency_pair)
                            if sym:
                                symbols.append(sym)
                    return symbols
        except Exception:
            return []


class HTXAPI(BirgaAPI):
    name = Birga.HTX
    base_url = "https://api.huobi.pro"

    def _format_symbol(self, symbol: str) -> str:
        s = symbol.lower().replace("/", "")
        return s

    def _parse_symbol(self, raw_symbol: str, quote: str = "usdt") -> Optional[str]:
        if raw_symbol.endswith(quote):
            base = raw_symbol[:-len(quote)]
            return f"{base.upper()}/USDT"
        return None

    async def get_orderbook(self, symbol: str, limit: int = 10) -> Optional[OrderBook]:
        try:
            session = await self._get_session()
            formatted = self._format_symbol(symbol)
            url = f"{self.base_url}/market/depth"
            params = {"symbol": formatted, "type": "step0"}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if data.get("status") != "ok":
                    return None
                tick = data.get("tick", {})
                bids = [OrderBookEntry(float(b[0]), float(b[1])) for b in tick.get("bids", [])[:limit]]
                asks = [OrderBookEntry(float(a[0]), float(a[1])) for a in tick.get("asks", [])[:limit]]
                return OrderBook(bids=bids, asks=asks, symbol=symbol, birga=self.name)
        except Exception:
            return None

    async def get_all_symbols(self) -> list[str]:
        try:
            session = await self._get_session()
            url = f"{self.base_url}/v1/common/symbols"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                if data.get("status") != "ok":
                    return []
                symbols = []
                for item in data.get("data", []):
                    if item.get("quote-currency") == "usdt":
                        sym = self._parse_symbol(item.get("symbol", ""))
                        if sym:
                            symbols.append(sym)
                return symbols
        except Exception:
            return []


class BitmartAPI(BirgaAPI):
    name = Birga.BITMART
    base_url = "https://api-cloud.bitmart.com"

    def _format_symbol(self, symbol: str) -> str:
        s = symbol.upper().replace("/", "_")
        return s if "_" in s else f"{s}_USDT"

    def _parse_symbol(self, raw_symbol: str, quote: str = "USDT") -> Optional[str]:
        if raw_symbol.endswith(f"_{quote}"):
            base = raw_symbol[:-len(quote)-1]
            return f"{base}/{quote}"
        return None

    async def get_orderbook(self, symbol: str, limit: int = 10) -> Optional[OrderBook]:
        try:
            session = await self._get_session()
            formatted = self._format_symbol(symbol)
            url = f"{self.base_url}/spot/v1/symbols/book"
            params = {"symbol": formatted, "depth_size": limit}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if data.get("message") != "success":
                    return None
                result = data.get("data", {})
                bids = [OrderBookEntry(float(b[0]), float(b[1])) for b in result.get("bids", [])[:limit]]
                asks = [OrderBookEntry(float(a[0]), float(a[1])) for a in result.get("asks", [])[:limit]]
                return OrderBook(bids=bids, asks=asks, symbol=symbol, birga=self.name)
        except Exception:
            return None

    async def get_all_symbols(self) -> list[str]:
        try:
            session = await self._get_session()
            url = f"{self.base_url}/spot/v1/symbols"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                if data.get("message") != "success":
                    return []
                symbols = []
                for item in data.get("data", {}).get("symbols", []):
                    if item.get("quote_currency") == "USDT" and item.get("trade_status") == "trade":
                        sym = self._parse_symbol(item.get("symbol", ""))
                        if sym:
                            symbols.append(sym)
                return symbols
        except Exception:
            return []


class KucoinAPI(BirgaAPI):
    name = Birga.KUCOIN
    base_url = "https://api.kucoin.com"

    def _format_symbol(self, symbol: str) -> str:
        return symbol.upper().replace("/", "-")

    def _parse_symbol(self, raw_symbol: str, quote: str = "USDT") -> Optional[str]:
        if raw_symbol.endswith(f"-{quote}"):
            base = raw_symbol[:-len(quote)-1]
            return f"{base}/{quote}"
        return None

    async def get_orderbook(self, symbol: str, limit: int = 10) -> Optional[OrderBook]:
        try:
            session = await self._get_session()
            formatted = self._format_symbol(symbol)
            url = f"{self.base_url}/api/v1/orderBook"
            params = {"symbol": formatted, "limit": limit}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if data.get("type") != "success":
                    return None
                result = data.get("data", {})
                bids = [OrderBookEntry(float(b[0]), float(b[1])) for b in result.get("bids", [])[:limit]]
                asks = [OrderBookEntry(float(a[0]), float(a[1])) for a in result.get("asks", [])[:limit]]
                return OrderBook(bids=bids, asks=asks, symbol=symbol, birga=self.name)
        except Exception:
            return None

    async def get_all_symbols(self) -> list[str]:
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/v1/symbols"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                if data.get("type") != "success":
                    return []
                symbols = []
                for item in data.get("data", []):
                    if item.get("quoteCurrency") == "USDT" and item.get("enableTrading") is True:
                        sym = self._parse_symbol(item.get("symbol", ""))
                        if sym:
                            symbols.append(sym)
                return symbols
        except Exception:
            return []


class OKXAPI(BirgaAPI):
    name = Birga.OKX
    base_url = "https://www.okx.com"

    def _format_symbol(self, symbol: str) -> str:
        return symbol.upper().replace("/", "-")

    def _parse_symbol(self, raw_symbol: str, quote: str = "USDT") -> Optional[str]:
        if raw_symbol.endswith(f"-{quote}"):
            base = raw_symbol[:-len(quote)-1]
            return f"{base}/{quote}"
        return None

    async def get_orderbook(self, symbol: str, limit: int = 10) -> Optional[OrderBook]:
        try:
            session = await self._get_session()
            formatted = self._format_symbol(symbol)
            url = f"{self.base_url}/api/v5/market/books"
            params = {"instId": formatted, "sz": limit}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if data.get("code") != "0":
                    return None
                result = data.get("data", [{}])[0]
                bids = [OrderBookEntry(float(b[0]), float(b[1])) for b in result.get("bids", [])[:limit]]
                asks = [OrderBookEntry(float(a[0]), float(a[1])) for a in result.get("asks", [])[:limit]]
                return OrderBook(bids=bids, asks=asks, symbol=symbol, birga=self.name)
        except Exception:
            return None

    async def get_all_symbols(self) -> list[str]:
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/v5/public/instruments"
            params = {"instType": "SPOT", "uly": ""}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                if data.get("code") != "0":
                    return []
                symbols = []
                for item in data.get("data", []):
                    if item.get("quoteCcy") == "USDT":
                        sym = self._parse_symbol(item.get("instId", ""))
                        if sym:
                            symbols.append(sym)
                return symbols
        except Exception:
            return []


class CoinexAPI(BirgaAPI):
    name = Birga.COINEX
    base_url = "https://api.coinex.com"

    def _format_symbol(self, symbol: str) -> str:
        return symbol.upper().replace("/", "")

    def _parse_symbol(self, raw_symbol: str, quote: str = "USDT") -> Optional[str]:
        if raw_symbol.endswith(quote):
            base = raw_symbol[:-len(quote)]
            return f"{base}/{quote}"
        return None

    async def get_orderbook(self, symbol: str, limit: int = 10) -> Optional[OrderBook]:
        try:
            session = await self._get_session()
            formatted = self._format_symbol(symbol)
            url = f"{self.base_url}/v1/market/orderbook"
            params = {"market": formatted, "limit": limit}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if data.get("code") != 0:
                    return None
                result = data.get("data", {})
                bids = [OrderBookEntry(float(b[0]), float(b[1])) for b in result.get("bids", [])[:limit]]
                asks = [OrderBookEntry(float(a[0]), float(a[1])) for a in result.get("asks", [])[:limit]]
                return OrderBook(bids=bids, asks=asks, symbol=symbol, birga=self.name)
        except Exception:
            return None

    async def get_all_symbols(self) -> list[str]:
        try:
            session = await self._get_session()
            url = f"{self.base_url}/v1/common/currencys"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                if data.get("code") != 0:
                    return []
                # Get markets to find USDT pairs
                url2 = f"{self.base_url}/v1/common/market/all"
                async with session.get(url2, timeout=aiohttp.ClientTimeout(total=10)) as resp2:
                    if resp2.status != 200:
                        return []
                    data2 = await resp2.json()
                    if data2.get("code") != 0:
                        return []
                    symbols = []
                    for market in data2.get("data", []):
                        if market.endswith("USDT"):
                            sym = self._parse_symbol(market)
                            if sym:
                                symbols.append(sym)
                    return symbols
        except Exception:
            return []


class PoloniexAPI(BirgaAPI):
    name = Birga.POLONIEX
    base_url = "https://poloniex.com"

    def _format_symbol(self, symbol: str) -> str:
        return symbol.upper()

    def _parse_symbol(self, raw_symbol: str, quote: str = "USDT") -> Optional[str]:
        # Poloniex returns symbols like "ATOM_USDT"
        if raw_symbol.endswith(f"_{quote}"):
            base = raw_symbol[:-len(quote)-1]
            return f"{base}/{quote}"
        return None

    async def get_orderbook(self, symbol: str, limit: int = 10) -> Optional[OrderBook]:
        try:
            session = await self._get_session()
            formatted = self._format_symbol(symbol)
            url = f"{self.base_url}/public"
            params = {"command": "returnOrderBook", "currencyPair": formatted, "depth": limit}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if "error" in data:
                    return None
                bids = [OrderBookEntry(float(b[0]), float(b[1])) for b in data.get("bids", [])[:limit]]
                asks = [OrderBookEntry(float(a[0]), float(a[1])) for a in data.get("asks", [])[:limit]]
                return OrderBook(bids=bids, asks=asks, symbol=symbol, birga=self.name)
        except Exception:
            return None

    async def get_all_symbols(self) -> list[str]:
        try:
            session = await self._get_session()
            url = f"{self.base_url}/public"
            params = {"command": "returnTicker"}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                symbols = []
                for raw_symbol in data.keys():
                    sym = self._parse_symbol(raw_symbol)
                    if sym:
                        symbols.append(sym)
                return symbols
        except Exception:
            return []


class BingXAPI(BirgaAPI):
    name = Birga.BINGX
    base_url = "https://api.bingx.com"

    def _format_symbol(self, symbol: str) -> str:
        return symbol.upper().replace("/", "-")

    def _parse_symbol(self, raw_symbol: str, quote: str = "USDT") -> Optional[str]:
        if raw_symbol.endswith(f"-{quote}"):
            base = raw_symbol[:-len(quote)-1]
            return f"{base}/{quote}"
        return None

    async def get_orderbook(self, symbol: str, limit: int = 10) -> Optional[OrderBook]:
        try:
            session = await self._get_session()
            formatted = self._format_symbol(symbol)
            url = f"{self.base_url}/v1/quote/merged"
            params = {"symbol": formatted}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if data.get("code") != 0:
                    return None
                result = data.get("data", {})
                bids_raw = result.get("bids", [])
                asks_raw = result.get("asks", [])
                bids = [OrderBookEntry(float(b[0]), float(b[1])) for b in bids_raw[:limit]]
                asks = [OrderBookEntry(float(a[0]), float(a[1])) for a in asks_raw[:limit]]
                return OrderBook(bids=bids, asks=asks, symbol=symbol, birga=self.name)
        except Exception:
            return None

    async def get_all_symbols(self) -> list[str]:
        try:
            session = await self._get_session()
            url = f"{self.base_url}/v1/quote/contracts"
            params = {"currency": "USDT"}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                if data.get("code") != 0:
                    return []
                symbols = []
                for item in data.get("data", []):
                    sym = self._parse_symbol(item.get("symbol", ""))
                    if sym:
                        symbols.append(sym)
                return symbols
        except Exception:
            return []


# Реестр API бирж
BIRGA_REGISTRY: dict[Birga, type[BirgaAPI]] = {
    Birga.BYBIT: BybitAPI,
    Birga.MEXC: MexcAPI,
    Birga.GATE: GateAPI,
    Birga.HTX: HTXAPI,
    Birga.BITMART: BitmartAPI,
    Birga.KUCOIN: KucoinAPI,
    Birga.OKX: OKXAPI,
    Birga.COINEX: CoinexAPI,
    Birga.POLONIEX: PoloniexAPI,
    Birga.BINGX: BingXAPI,
}


def get_birga_api(birga: Birga) -> BirgaAPI:
    """Получить экземпляр API для биржи"""
    return BIRGA_REGISTRY[birga]()


async def fetch_orderbooks_for_symbols(
    symbols: list[str],
    birgas: list[Birga],
    limit: int = 10
) -> dict[Birga, dict[str, OrderBook]]:
    """
    Получить книги ордеров для списка символов на указанных биржах.
    Returns: {birga: {symbol: OrderBook}}
    """
    result: dict[Birga, dict[str, OrderBook]] = {b: {} for b in birgas}

    async def fetch_single(api: BirgaAPI, symbol: str):
        ob = await api.get_orderbook(symbol, limit)
        return api.name, symbol, ob

    tasks = []
    for birga in birgas:
        api = get_birga_api(birga)
        for symbol in symbols:
            tasks.append(fetch_single(api, symbol))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for r in results:
        if isinstance(r, Exception):
            continue
        birga_name, symbol, ob = r
        if ob:
            for b in birgas:
                if b.value == birga_name.value:
                    result[b][symbol] = ob
                    break

    return result


async def close_all_sessions():
    """Закрыть все сессии"""
    for api_class in BIRGA_REGISTRY.values():
        api = api_class()
        await api.close()


# Кэш символов
_symbols_cache: dict[Birga, list[str]] = {}
_symbols_cache_time: float = 0
SYMBOLS_CACHE_TTL: float = 300  # 5 минут


async def get_all_symbols(birgas: list[Birga], force_refresh: bool = False) -> dict[Birga, list[str]]:
    """
    Получить все USDT-пары с указанных бирж.
    Результат кэшируется на SYMBOLS_CACHE_TTL секунд.
    """
    global _symbols_cache, _symbols_cache_time
    import time

    now = time.time()
    if not force_refresh and (now - _symbols_cache_time) < SYMBOLS_CACHE_TTL:
        return {b: _symbols_cache.get(b, []) for b in birgas}

    async def fetch_birga_symbols(birga: Birga) -> tuple[Birga, list[str]]:
        api = get_birga_api(birga)
        symbols = await api.get_all_symbols()
        return birga, symbols

    results = await asyncio.gather(*[fetch_birga_symbols(b) for b in birgas], return_exceptions=True)

    new_cache = {}
    for r in results:
        if isinstance(r, Exception):
            continue
        birga, symbols = r
        new_cache[birga] = symbols

    _symbols_cache = new_cache
    _symbols_cache_time = now

    return {b: new_cache.get(b, []) for b in birgas}


def get_universal_symbols(all_birga_symbols: dict[Birga, list[str]], min_birgas: int = 2) -> list[str]:
    """
    Получить символы, которые торгуются как минимум на min_birgas биржах.
    """
    symbol_birga_count: dict[str, int] = {}
    symbol_first_occurrence: dict[str, str] = {}

    for birga, symbols in all_birga_symbols.items():
        for sym in symbols:
            if sym not in symbol_birga_count:
                symbol_first_occurrence[sym] = birga.value
            symbol_birga_count[sym] = symbol_birga_count.get(sym, 0) + 1

    return [s for s, count in symbol_birga_count.items() if count >= min_birgas]
