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