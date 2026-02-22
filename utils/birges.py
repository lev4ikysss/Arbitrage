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
                answer.append({
                    "coin": bind["symbol"].replace("USDT", ""),
                    "price": bind["lastPrice"]
                })            
        return answer

    def check_mexc(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже mexc
        """
        check_binds = self.session.get("https://api.mexc.com/api/v3/ticker/price").json()
        answer = []
        for bind in check_binds:
            if "USDT" in bind["symbol"]:
                answer.append({
                    "coin": bind["symbol"].replace("USDT", ""),
                    "price": bind["price"]
                })
        return answer

    def check_gate(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже gate
        """
        check_binds = self.session.get("https://api.gateio.ws/api/v4/spot/tickers").json()
        answer = []
        for bind in check_binds:
            if "USDT" in bind["currency_pair"]:
                answer.append({
                    "coin": bind["currency_pair"].replace("USDT", "").replace("_", ""),
                    "price": bind["last"]
                })
        return answer

    def check_htx(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже htx
        """
        check_binds = self.session.get("https://api.htx.com/market/tickers").json()["data"]
        answer = []
        for bind in check_binds:
            if "USDT" in bind["symbol"].upper():
                answer.append({
                    "coin": bind["symbol"].upper().replace("USDT", ""),
                    "price": bind["close"]
                })
        return answer

    def check_bitmart(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже bitmart
        """
        check_binds = self.session.get("https://api-cloud.bitmart.com/spot/quotation/v3/tickers").json()["data"]
        answer = []
        for bind in check_binds:
            if "USDT" in bind[0]:
                answer.append({
                    "coin": bind[0].replace("USDT", "").replace("_", ""),
                    "price": bind[1]
                })
        return answer

    def check_kucoin(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже kucoin
        """
        check_binds = self.session.get("https://api.kucoin.com/api/v1/market/allTickers").json()["data"]["ticker"]
        answer = []
        for bind in check_binds:
            if "USDT" in bind["symbol"]:
                answer.append({
                    "coin": bind["symbol"].replace("USDT", "").replace("-", ""),
                    "price": bind["last"]
                })
        return answer

    def check_okx(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже okx
        """
        check_binds = self.session.get("https://www.okx.com/api/v5/market/tickers?instType=SPOT").json()["data"]
        answer = []
        for bind in check_binds:
            if "USDT" in bind["instId"]:
                answer.append({
                    "coin": bind["instId"].replace("USDT", "").replace("-", ""),
                    "price": bind["last"]
                })
        return answer

    def check_coinex(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже coinex
        """
        check_binds = self.session.get("https://api.coinex.com/v1/market/ticker/all").json()["data"]["ticker"]
        answer = []
        for bind in check_binds.keys():
            if "USDT" in bind:
                answer.append({
                    "coin": bind.replace("USDT", ""),
                    "price": check_binds[bind]["last"]
                })
        return answer

    def check_poloniex(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже poloniex
        """
        check_binds = self.session.get("https://api.poloniex.com/markets/price").json()
        answer = []
        for bind in check_binds:
            if "USDT" in bind["symbol"]:
                answer.append({
                    "coin": bind["symbol"].replace("USDT", "").replace("_", ""),
                    "price": bind["price"]
                })
        return answer

    def check_bingx(self) -> list:
        """
            Получает данные о стоимости токенов относительно USDT, по бирже bingx
        """
        check_binds = self.session.get(f"https://open-api.bingx.com/openApi/spot/v1/ticker/24hr?timestamp={int(time.time() * 1000)}").json()["data"]
        answer = []
        for bind in check_binds:
            if "USDT" in bind["symbol"]:
                answer.append({
                    "coin": bind["symbol"].replace("USDT", "").replace("-", ""),
                    "price": bind["lastPrice"]
                })
        return answer

    def check_all(self) -> dict:
        """
            Получает данные о стоимости токенов относительно USDT, по вем биржам
        """
        return {
            "bybit": self.check_bybit(),
            "mexc": self.check_mexc(),
            "gate": self.check_gate(),
            "htx": self.check_htx(),
            "bitmart": self.check_bitmart(),
            "kucoin": self.check_kucoin(),
            "okx": self.check_okx(),
            "coinex": self.check_coinex(),
            "poloniex": self.check_poloniex(),
            "bingx": self.check_bingx()
        }
