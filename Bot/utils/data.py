import sqlite3
import json
import datetime
import pandas

class DataUser:
    def __init__(self, path: str):
        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()
        self.cur.execute(f"""
                            CREATE TABLE IF NOT EXISTS users (
                                id_tg INTEGER PRIMARY KEY NOT NULL UNIQUE,
                                register TEXT NOT NULL,
                                payment INTEGER DEFAULT 0,
                                options TEXT NOT NULL DEFAULT '{json.dumps({
                                                                            "birges": {
                                                                                "bybit": False,
                                                                                "mexc": False,
                                                                                "gate": False,
                                                                                "htx": False,
                                                                                "bitmart": False,
                                                                                "kucoin": False,
                                                                                "okx": False,
                                                                                "coinex": False,
                                                                                "poloniex": False,
                                                                                "bingx": False
                                                                            },
                                                                            "strategy": {
                                                                                "min": True,
                                                                                "balance": False,
                                                                                "max": False
                                                                            },
                                                                            "range": {
                                                                                "0-100": True,
                                                                                "100-500": False,
                                                                                ">500": False
                                                                            }
                                                                })}'
                                )
                        """)
        self.con.commit()

    def close(self):
        self.con.close()

    def read_table(self, sql_command: str, params=None) -> dict :
        if params == None :
            params = ()
        return json.loads(pandas.read_sql(sql_command, self.con, params=params).to_json())

    @staticmethod
    def validate_options(options: dict) -> bool:
        chapters = ["strategy", "range"]
        for chapter in chapters:
            trues = 0
            for key in options[chapter].keys() :
                if options[chapter][key] == True: trues += 1
            if trues != 1: return False
        return True

    def register(self, id_tg: int) -> int:    
        """
            status code:
            0 - success
            1 - id_tg is already registered
        """
        time = datetime.datetime.now()
        try:
            self.cur.execute("""
                                INSERT INTO users (id_tg, register)
                                VALUES (?, ?)
                            """, (id_tg, f"{time.year}-{time.month}-{time.day} {time.hour}:{time.minute}:{time.second}"))
            self.con.commit()
        except:
            return 1
        return 0
    
    def get_data(self, id_tg: int) -> dict:
        """
        status code:
        0 - succes
        1 - id_tg does not exist
        """
        try:
            data = self.read_table("""
                                SELECT payment, options FROM users
                                WHERE id_tg = ?
                            """, (id_tg))
            return {
                "status": 0,
                "data": {
                    "payment": data["payment"]["0"],
                    "options": json.loads(data["options"]["0"])
                }
            }
        except:
            return {"status": 1}
        
    def update_options(self, id_tg: int, options: dict) -> int:
        """
        status code:
        0 - succes
        1 - id_tg does not exist
        2 - options is invalid
        """
        try:
            if not self.validate_options(options): return 2
            self.cur.execute("""
                                UPDATE users SET
                                options = ?
                                WHERE id_tg = ?
                            """, (json.dumps(options), id_tg))
            self.con.commit()
            return 0
        except:
            return 1
        
    def update_payment(self, id_tg: int, payment_days_add: int) -> int:
        """
        status code:
        0 - succes
        1 - id_tg does not exist
        """
        data = self.get_data(id_tg)
        if data["status"] == 1: return 1
        self.cur.execute("""
                            UPDATE users SET
                            payment = ?
                            WHERE id_tg = ?
                        """, (int(data["data"]["payment"])+payment_days_add, id_tg))
        self.con.commit()
        return 0