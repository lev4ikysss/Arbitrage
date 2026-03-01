import requests
import time

class Request:
    def __init__(self):
        """
            Метод для получения информации от бирж
        """
        self.session = requests.Session()
        self.session.verify = True
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; py3xui-like)"
        })

    def reconect(self) -> None:
        """
            Пересоздаёт сессию
        """
        self.session.close()
        self.session = requests.Session()
        self.session.verify = True
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; py3xui-like)"
        })

    def close(self) -> None:
        """
            Закрывает сессию
        """
        self.session.close()

    def check_bybit(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже bybit
        """
        check_binds = self.session.get("https://api.bybit.com/v5/market/tickers?category=spot").json()["result"]["list"]
        answer = []
        for bind in check_binds:
            if "USDT" in bind["symbol"]:
                try:
                    answer.append({
                        "coin": bind["symbol"].replace("USDT", ""),
                        "price": float(bind["lastPrice"])
                    })
                except:
                    pass      
        return answer

    def check_mexc(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже mexc
        """
        check_binds = self.session.get("https://api.mexc.com/api/v3/ticker/price").json()
        answer = []
        for bind in check_binds:
            if "USDT" in bind["symbol"]:
                try:
                    answer.append({
                        "coin": bind["symbol"].replace("USDT", ""),
                        "price": float(bind["price"])
                    })
                except:
                    pass
        return answer

    def check_gate(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже gate
        """
        check_binds = self.session.get("https://api.gateio.ws/api/v4/spot/tickers").json()
        answer = []
        for bind in check_binds:
            if "USDT" in bind["currency_pair"]:
                try:
                    answer.append({
                        "coin": bind["currency_pair"].replace("USDT", "").replace("_", ""),
                        "price": float(bind["last"])
                    })
                except:
                    pass
        return answer

    def check_htx(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже htx
        """
        check_binds = self.session.get("https://api.htx.com/market/tickers").json()["data"]
        answer = []
        for bind in check_binds:
            if "USDT" in bind["symbol"].upper():
                try:
                    answer.append({
                        "coin": bind["symbol"].upper().replace("USDT", ""),
                        "price": float(bind["close"])
                    })
                except:
                    pass
        return answer

    def check_bitmart(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже bitmart
        """
        check_binds = self.session.get("https://api-cloud.bitmart.com/spot/quotation/v3/tickers").json()["data"]
        answer = []
        for bind in check_binds:
            if "USDT" in bind[0]:
                try:
                    answer.append({
                        "coin": bind[0].replace("USDT", "").replace("_", ""),
                        "price": float(bind[1])
                    })
                except:
                    pass
        return answer

    def check_kucoin(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже kucoin
        """
        check_binds = self.session.get("https://api.kucoin.com/api/v1/market/allTickers").json()["data"]["ticker"]
        answer = []
        for bind in check_binds:
            if "USDT" in bind["symbol"]:
                try:
                    answer.append({
                        "coin": bind["symbol"].replace("USDT", "").replace("-", ""),
                        "price": float(bind["last"])
                    })
                except:
                    pass
        return answer

    def check_okx(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже okx
        """
        check_binds = self.session.get("https://www.okx.com/api/v5/market/tickers?instType=SPOT").json()["data"]
        answer = []
        for bind in check_binds:
            if "USDT" in bind["instId"]:
                try:
                    answer.append({
                        "coin": bind["instId"].replace("USDT", "").replace("-", ""),
                        "price": float(bind["last"])
                    })
                except:
                    pass
        return answer

    def check_coinex(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже coinex
        """
        check_binds = self.session.get("https://api.coinex.com/v1/market/ticker/all").json()["data"]["ticker"]
        answer = []
        for bind in check_binds.keys():
            if "USDT" in bind:
                try:
                    answer.append({
                        "coin": bind.replace("USDT", ""),
                        "price": float(check_binds[bind]["last"])
                    })
                except:
                    pass
        return answer

    def check_poloniex(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже poloniex
        """
        check_binds = self.session.get("https://api.poloniex.com/markets/price").json()
        answer = []
        for bind in check_binds:
            if "USDT" in bind["symbol"]:
                try:
                    answer.append({
                        "coin": bind["symbol"].replace("USDT", "").replace("_", ""),
                        "price": float(bind["price"])
                    })
                except:
                    pass
        return answer

    def check_bingx(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже bingx
        """
        check_binds = self.session.get(f"https://open-api.bingx.com/openApi/spot/v1/ticker/24hr?timestamp={int(time.time() * 1000)}").json()["data"]
        answer = []
        for bind in check_binds:
            if "USDT" in bind["symbol"]:
                try:
                    answer.append({
                        "coin": bind["symbol"].replace("USDT", "").replace("-", ""),
                        "price": float(bind["lastPrice"])
                    })
                except:
                    pass
        return answer

    def check_all(self) -> dict:
        """
            Получает данные о стоимости токенов относительно USDT, по вем биржам
        """
        return {
            "Bybit": self.check_bybit(),
            "Mexc": self.check_mexc(),
            "Gate": self.check_gate(),
            "HTX": self.check_htx(),
            "Bitmart": self.check_bitmart(),
            "Kucoin": self.check_kucoin(),
            "OKX": self.check_okx(),
            "Coinex": self.check_coinex(),
            "Poloniex": self.check_poloniex(),
            "BingX": self.check_bingx()
        }

    @staticmethod
    def restructurize_birges(birges: dict) -> dict:
        """
            Реструктуризирует биржи в лучший вид
        """
        answer = {}
        for key in birges.keys():
            for i in birges[key]:
                try:
                    answer[i["coin"]].append({
                        "birge": key,
                        "price": i["price"]
                    })
                except:
                    answer[i["coin"]] = []
                    answer[i["coin"]].append({
                        "birge": key,
                        "price": i["price"]
                    })
        return answer

    def get_orderbook(self, exchange: str, symbol: str, limit: int = 50):
        exch = exchange.lower()
        symbol_upper = symbol.upper()

        # Нормализация символа
        if exch in ["gate", "bitmart", "poloniex"]:
            sym = symbol_upper.replace("USDT", "_USDT")
        elif exch in ["kucoin", "okx"]:
            sym = symbol_upper.replace("USDT", "-USDT")
        elif exch == "htx":
            sym = symbol_upper.lower()
        elif exch == "coinex":
            sym = symbol_upper.replace("-", "").replace("_", "")
        else:
            sym = symbol_upper.replace("-", "").replace("_", "")

        try:
            if exch == "bybit":
                url = f"https://api.bybit.com/v5/market/orderbook?category=spot&symbol={sym}&limit={limit}"
                r = self.session.get(url, timeout=5).json()
                if r.get("retCode") != 0:
                    return None
                d = r["result"]
                return {
                    "bids": [[float(p), float(q)] for p, q in d.get("b", [])],
                    "asks": [[float(p), float(q)] for p, q in d.get("a", [])]
                }

            elif exch == "mexc":
                url = f"https://api.mexc.com/api/v3/depth?symbol={sym}&limit={limit}"
                r = self.session.get(url, timeout=5).json()
                return {
                    "bids": [[float(p), float(q)] for p, q in r.get("bids", [])],
                    "asks": [[float(p), float(q)] for p, q in r.get("asks", [])]
                }

            elif exch == "gate":
                url = f"https://api.gateio.ws/api/v4/spot/order_book?currency_pair={sym}&limit={limit}"
                r = self.session.get(url, timeout=5).json()
                return {
                    "bids": [[float(p), float(q)] for p, q in r.get("bids", [])],
                    "asks": [[float(p), float(q)] for p, q in r.get("asks", [])]
                }

            elif exch == "htx":
                url = f"https://api.htx.com/market/depth?symbol={sym}&type=step0"
                r = self.session.get(url, timeout=5).json()
                if r.get("status") != "ok":
                    return None
                d = r["tick"]
                return {
                    "bids": [[float(p), float(q)] for p, q in d.get("bids", [])],
                    "asks": [[float(p), float(q)] for p, q in d.get("asks", [])]
                }

            elif exch == "bitmart":
                url = f"https://api-cloud.bitmart.com/spot/quotation/v3/books?symbol={sym}&limit={min(limit, 50)}"
                r = self.session.get(url, timeout=5).json()
                if r.get("code") != 1000:
                    return None
                d = r["data"]
                return {
                    "bids": [[float(p), float(q)] for p, q in d.get("bids", [])],
                    "asks": [[float(p), float(q)] for p, q in d.get("asks", [])]
                }

            elif exch == "kucoin":
                url = f"https://api.kucoin.com/api/v1/market/orderbook/level2_100?symbol={sym}"
                r = self.session.get(url, timeout=5).json()
                if r.get("code") != "200000":
                    return None
                d = r["data"]
                return {
                    "bids": [[float(p), float(q)] for p, q in d.get("bids", [])],
                    "asks": [[float(p), float(q)] for p, q in d.get("asks", [])]
                }

            elif exch == "okx":
                url = f"https://www.okx.com/api/v5/market/books?instId={sym}&sz={min(limit, 400)}"
                r = self.session.get(url, timeout=5).json()
                if r.get("code") != "0":
                    return None
                d = r["data"][0]
                # OKX возвращает 4 элемента: [price, qty, ?, ?]
                return {
                    "bids": [[float(row[0]), float(row[1])] for row in d.get("bids", [])],
                    "asks": [[float(row[0]), float(row[1])] for row in d.get("asks", [])]
                }

            elif exch == "coinex":
                url = f"https://api.coinex.com/v2/spot/depth?market={sym}&limit={min(limit, 50)}&interval=0"
                r = self.session.get(url, timeout=5).json()
                if r.get("code") != 0:
                    return None
                d = r["data"]["depth"]
                return {
                    "bids": [[float(p), float(q)] for p, q in d.get("bids", [])],
                    "asks": [[float(p), float(q)] for p, q in d.get("asks", [])]
                }

            elif exch == "poloniex":
                url = f"https://api.poloniex.com/markets/{sym}/orderBook?depth={limit}"
                r = self.session.get(url, timeout=5).json()
                bids_raw = r.get("bids", [])
                asks_raw = r.get("asks", [])
                # Poloniex: плоский список [price, qty, price, qty, ...]
                bids = [[float(bids_raw[i]), float(bids_raw[i+1])] for i in range(0, len(bids_raw), 2)]
                asks = [[float(asks_raw[i]), float(asks_raw[i+1])] for i in range(0, len(asks_raw), 2)]
                return {"bids": bids, "asks": asks}

            elif exch == "bingx":
                url = f"https://open-api.bingx.com/openApi/spot/v1/market/depth?symbol={sym}&limit={limit}"
                resp = self.session.get(url, timeout=5)
                if resp.status_code != 200:
                    print(f"BingX HTTP {resp.status_code}")
                    return None
                r = resp.json()
                if r.get("code") != 0:
                    print(f"BingX error: {r}")
                    return None
                d = r.get("data", {})
                # BingX иногда возвращает строку вместо dict — проверяем
                if isinstance(d, str):
                    print(f"BingX вернул строку вместо dict: {d}")
                    return None
                return {
                    "bids": [[float(p), float(q)] for p, q in d.get("bids", [])],
                    "asks": [[float(p), float(q)] for p, q in d.get("asks", [])]
                }

            else:
                print(f"Биржа {exch} не поддерживается")
                return None

        except Exception as e:
            print(f"Ошибка get_orderbook {exch} {symbol}: {type(e).__name__}: {e}")
            return None

    def get_depth(self, base_token: str, quote_token: str = "USDT", exchanges: list[str] = None) -> dict:
        """
        Получает глубину стакана (order book) на двух указанных биржах для пары {base_token}{quote_token}.
        
        Аргументы:
            base_token: базовый токен (например "BTC", "ETH")
            quote_token: котируемый токен (по умолчанию "USDT")
            exchanges: список из двух бирж, например ["Bybit", "MEXC"]
        
        Возвращает:
            dict вида:
            {
                "buy_exchange": {
                    "exchange": "Bybit",
                    "symbol": "BTCUSDT",
                    "mid_price": 67000.5,
                    "depth_buy_usdt": 45000.0,    # сколько USDT можно купить до 0.3% slippage
                    "depth_sell_usdt": 38000.0,   # сколько USDT можно продать
                    "safe_volume_usdt": 26600.0,  # min(depth_buy, depth_sell) * 0.7
                    "levels": 50,
                    "success": True,
                    "error": None
                },
                "sell_exchange": { ... аналогично ... }
            }
        """
        if len(exchanges) != 2:
            raise ValueError("Ожидается ровно два названия биржи в списке exchanges")

        symbol = f"{base_token.upper()}{quote_token.upper()}"
        result = {}

        MAX_SLIPPAGE_PCT = 0.3
        SAFETY_FACTOR = 0.7

        for idx, exch in enumerate(exchanges):
            exch_lower = exch.lower()
            key = "buy_exchange" if idx == 0 else "sell_exchange"

            try:
                ob = self.get_orderbook(exch, symbol, limit=50)
                if not ob or not ob.get("asks") or not ob.get("bids"):
                    result[key] = {
                        "exchange": exch,
                        "symbol": symbol,
                        "success": False,
                        "error": "Не удалось получить стакан или он пустой"
                    }
                    continue

                best_bid = ob["bids"][0][0] if ob["bids"] else 0
                best_ask = ob["asks"][0][0] if ob["asks"] else 0
                mid_price = (best_bid + best_ask) / 2 if best_bid and best_ask else 0

                if mid_price == 0:
                    result[key] = {
                        "exchange": exch,
                        "symbol": symbol,
                        "mid_price": 0,
                        "depth_buy_usdt": 0,
                        "depth_sell_usdt": 0,
                        "safe_volume_usdt": 0,
                        "success": False,
                        "error": "Не удалось определить среднюю цену"
                    }
                    continue

                target_ask = mid_price * (1 + MAX_SLIPPAGE_PCT / 100)
                depth_buy = 0.0
                for price, qty in ob["asks"]:
                    if price > target_ask:
                        break
                    depth_buy += price * qty

                target_bid = mid_price * (1 - MAX_SLIPPAGE_PCT / 100)
                depth_sell = 0.0
                for price, qty in ob["bids"]:
                    if price < target_bid:
                        break
                    depth_sell += price * qty

                safe_volume = min(depth_buy, depth_sell) * SAFETY_FACTOR

                result[key] = {
                    "exchange": exch,
                    "symbol": symbol,
                    "mid_price": round(mid_price, 2),
                    "depth_buy_usdt": round(depth_buy, 2),
                    "depth_sell_usdt": round(depth_sell, 2),
                    "safe_volume_usdt": round(safe_volume, 2),
                    "levels": len(ob["asks"]) + len(ob["bids"]),
                    "success": True,
                    "error": None
                }

            except Exception as e:
                result[key] = {
                    "exchange": exch,
                    "symbol": symbol,
                    "success": False,
                    "error": str(e)
                }

        return result