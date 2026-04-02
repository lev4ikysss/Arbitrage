import asyncio
import aiohttp
import time
from dataclasses import dataclass
from typing import Optional

# Кэш данных о блокчейнах
_blockchain_cache: dict[str, dict] = {}
_blockchain_cache_time: float = 0
BLOCKCHAIN_CACHE_TTL: float = 3600  # 1 час


@dataclass
class BlockchainInfo:
    """Информация о блокчейне монеты"""
    name: str
    symbol: str
    confirmations: int
    avg_block_time: float  # в секундах
    is_native: bool  # True для нативных монет (BTC, ETH), False для токенов


# Известные сети и их параметры
KNOWN_NETWORKS = {
    # Ethereum ecosystem
    "ETH": {"confirmations": 12, "block_time": 15, "is_native": True},
    "USDT": {"confirmations": 12, "block_time": 15, "is_native": False, "network": "ERC20"},
    "USDC": {"confirmations": 12, "block_time": 15, "is_native": False, "network": "ERC20"},
    "BICO": {"confirmations": 12, "block_time": 15, "is_native": True},

    # Tron ecosystem
    "TRX": {"confirmations": 19, "block_time": 3, "is_native": True},
    "USDT_TRON": {"confirmations": 19, "block_time": 3, "is_native": False, "network": "TRC20"},

    # Bitcoin ecosystem
    "BTC": {"confirmations": 3, "block_time": 600, "is_native": True},

    # Binance ecosystem
    "BNB": {"confirmations": 1, "block_time": 3, "is_native": True},

    # Other chains
    "SOL": {"confirmations": 1, "block_time": 0.4, "is_native": True},
    "MATIC": {"confirmations": 12, "block_time": 2, "is_native": True},
    "AVAX": {"confirmations": 12, "block_time": 2, "is_native": True},
    "ATOM": {"confirmations": 12, "block_time": 7, "is_native": True},
    "NEAR": {"confirmations": 5, "block_time": 1, "is_native": True},
    "ALGO": {"confirmations": 4, "block_time": 4, "is_native": True},
    "XRP": {"confirmations": 1, "block_time": 4, "is_native": True},
    "ADA": {"confirmations": 1, "block_time": 20, "is_native": True},
    "DOT": {"confirmations": 10, "block_time": 6, "is_native": True},
    "FTM": {"confirmations": 12, "block_time": 1, "is_native": True},
    "ONE": {"confirmations": 1, "block_time": 2, "is_native": True},
    "KAVA": {"confirmations": 12, "block_time": 5, "is_native": True},
    "SUI": {"confirmations": 1, "block_time": 0.3, "is_native": True},
    "SEI": {"confirmations": 1, "block_time": 0.5, "is_native": True},
    "TIA": {"confirmations": 12, "block_time": 15, "is_native": True},
    "INJ": {"confirmations": 12, "block_time": 1, "is_native": True},
    "APT": {"confirmations": 1, "block_time": 1, "is_native": True},
    "ARB": {"confirmations": 12, "block_time": 1, "is_native": True},
    "OP": {"confirmations": 12, "block_time": 2, "is_native": True},
}

# Маппинг монет к их сетям
COIN_NETWORKS = {
    "BICO": "ETH",
    "ETH": "ETH",
    "BTC": "BTC",
    "USDT": "ERC20",
    "USDC": "ERC20",
    "BNB": "BNB",
    "SOL": "SOL",
    "MATIC": "MATIC",
    "AVAX": "AVAX",
    "ATOM": "ATOM",
    "NEAR": "NEAR",
    "ALGO": "ALGO",
    "XRP": "XRP",
    "ADA": "ADA",
    "DOT": "DOT",
    "FTM": "FTM",
    "TRX": "TRX",
    "INSP": "ERC20",
}


def get_network_for_coin(symbol: str) -> str:
    """Определить сеть по символу монеты"""
    # Сначала ищем прямое совпадение
    if symbol in COIN_NETWORKS:
        return COIN_NETWORKS[symbol]

    # Пытаемся определить по символу
    symbol_upper = symbol.upper()

    # Известные токены ERC20 (普遍)
    erc20_tokens = ["USDT", "USDC", "UNI", "LINK", "AAVE", "CRV", "MKR", "COMP",
                    "YFI", "SUSHI", "APE", "MANA", "SAND", "AXS", "ENJ", "CHZ",
                    "BAT", "ZRX", "COMP", "SNX", "uma", "bal", "ren", "kava",
                    "ankr", "storj", "lpt", "api3", "fetch", "ocean", "trac",
                    "rlc", "cfx", "aud", "bull", "bear", "half", "halve"]

    if symbol_upper in erc20_tokens:
        return "ERC20"

    # TRC20 tokens (USDT on Tron)
    if symbol_upper == "USDT_TRON" or symbol.startswith("TRX"):
        return "TRC20"

    # По умолчанию - ERC20 (самый распространенный)
    return "ERC20"


async def fetch_eth_scan_confirmations() -> dict:
    """Получить данные о gas price и block time из Etherscan"""
    global _blockchain_cache, _blockchain_cache_time
    import os

    if time.time() - _blockchain_cache_time < BLOCKCHAIN_CACHE_TTL and "eth" in _blockchain_cache:
        return _blockchain_cache

    api_key = os.getenv("ETHERSCAN_API_KEY", "")
    url = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={api_key}" if api_key else None

    if url:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") == "1":
                            result = data.get("result", {})
                            _blockchain_cache["eth"] = {
                                "gas_price_gwei": float(result.get("SafeGasPrice", 30)),
                                "block_time": 15,
                            }
                            _blockchain_cache_time = time.time()
        except Exception:
            pass

    if "eth" not in _blockchain_cache:
        _blockchain_cache["eth"] = {"gas_price_gwei": 30, "block_time": 15}
        _blockchain_cache_time = time.time()

    return _blockchain_cache


async def fetch_blockchair_stats(coin: str = "ethereum") -> dict:
    """Получить статистику блокчейна из Blockchair"""
    global _blockchain_cache, _blockchain_cache_time

    cache_key = f"blockchair_{coin}"
    if time.time() - _blockchain_cache_time < BLOCKCHAIN_CACHE_TTL and cache_key in _blockchain_cache:
        return _blockchain_cache

    url = f"https://api.blockchair.com/{coin}/stats"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("data", {}).get("context", {}).get("block_no"):
                        block_time = data["data"]["context"].get("prev_block_time_diff", 30)
                        _blockchain_cache[cache_key] = {
                            "block_height": data["data"]["context"]["block_no"],
                            "block_time": abs(block_time) if block_time else 30,
                        }
                        _blockchain_cache_time = time.time()
                        return _blockchain_cache
    except Exception:
        pass

    return {}


async def get_blockchain_info(symbol: str) -> BlockchainInfo:
    """Получить информацию о блокчейне для монеты"""
    network = get_network_for_coin(symbol)

    # Проверяем кэш
    cache_key = f"{symbol}_{network}"
    if time.time() - _blockchain_cache_time < BLOCKCHAIN_CACHE_TTL and cache_key in _blockchain_cache:
        return _blockchain_cache[cache_key]

    # Используем известные данные
    if network in KNOWN_NETWORKS:
        network_data = KNOWN_NETWORKS[network]
        info = BlockchainInfo(
            name=network,
            symbol=symbol,
            confirmations=network_data["confirmations"],
            avg_block_time=network_data["block_time"],
            is_native=network_data.get("is_native", symbol == network)
        )
        _blockchain_cache[cache_key] = info
        return info

    # Пытаемся получить из API
    if network in ["ETH", "ERC20"]:
        await fetch_eth_scan_confirmations()
        eth_data = _blockchain_cache.get("eth", {})
        info = BlockchainInfo(
            name="Ethereum",
            symbol=symbol,
            confirmations=12,
            avg_block_time=eth_data.get("block_time", 15),
            is_native=symbol == "ETH"
        )
    elif network == "BTC":
        info = BlockchainInfo(
            name="Bitcoin",
            symbol=symbol,
            confirmations=3,
            avg_block_time=600,
            is_native=True
        )
    elif network == "TRC20":
        info = BlockchainInfo(
            name="Tron",
            symbol=symbol,
            confirmations=19,
            avg_block_time=3,
            is_native=symbol == "TRX"
        )
    else:
        # Дефолтные значения для неизвестных сетей
        info = BlockchainInfo(
            name=network,
            symbol=symbol,
            confirmations=12,
            avg_block_time=15,
            is_native=False
        )

    _blockchain_cache[cache_key] = info
    return info


def format_blockchain_info(info: BlockchainInfo, volume: float) -> str:
    """Форматировать информацию о блокчейне для уведомления"""
    # Время для подтверждений в минутах
    confirm_time_minutes = (info.confirmations * info.avg_block_time) / 60

    if confirm_time_minutes < 1:
        confirm_time_str = f"~ {int(confirm_time_minutes * 60)} сек"
    elif confirm_time_minutes < 60:
        confirm_time_str = f"~ {int(confirm_time_minutes)} мин"
    else:
        hours = int(confirm_time_minutes / 60)
        mins = int(confirm_time_minutes % 60)
        confirm_time_str = f"~ {hours}ч {mins}м"

    contract_type = ""
    if not info.is_native:
        if info.name in ["ERC20", "TRC20", "BEP20"]:
            contract_type = f" ({info.name})"

    return (f"🔐 Подтверждений: {info.confirmations} | {confirm_time_str} "
            f"(block time {info.avg_block_time:.0f}с){contract_type}")


if __name__ == "__main__":
    # Тест
    async def test():
        for sym in ["BICO", "ETH", "USDT", "BTC", "SOL", "ATOM"]:
            info = await get_blockchain_info(sym)
            print(f"{sym}: {info}")
            print(format_blockchain_info(info, 100))
            print()

    asyncio.run(test())
