import sqlite3
import json
from uuid import uuid4

class Codes:
    def __init__(self, path: str):
        """
            Работа с кодами
            :path: путь до json файла
        """
        self.path = path

    def is_admin(self, code: str) -> bool:
        """
            Проверка кода администратора
            :code: код пользователя
            True - Код действителен
            False - Код неверен
        """
        with open(self.path, 'r') as f:
            return json.load(f)["admin"] == code

    def is_invite(self, code: str) -> bool:
        """
            Проверка кода приглашения
            :code: код пользователя
            True - Код действителен
            False - Код неверен
        """
        with open(self.path, 'r') as f:
            file = json.load(f)
        if not code in file["invite"]:
            return False
        file["invite"].remove(code)
        with open(self.path, 'w') as f:
            file = json.dump(file, f, indent=4)
        return True
    
    def write_admin(self, new_code: str) -> None:
        """
            Задаёт новый код для администратора
            :new_code: Новый код для записи
        """
        with open(self.path, 'r') as f:
            file = json.load(f)
        file["admin"] = new_code
        with open(self.path, 'w') as f:
            json.dump(file, f, indent=4)

    def generate_invite(self) -> str:
        """
            Генерация кода приглашения
            return - Новый код приглашения
        """
        with open(self.path, 'r') as f:
            file = json.load(f)
        code = str(uuid4())
        file["invite"].append(code)
        with open(self.path, 'w') as f:
            json.dump(file, f, indent=4)
        return code

class DataBase:
    def __init__(self, path: str):
        """
            Работа с базой данных
            :path: путь до базы данных
        """
        self.con = sqlite3.connect(path, check_same_thread=False)
        self.cur = self.con.cursor()

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY NOT NULL,
                chat_id     INTEGER UNIQUE NOT NULL,
                is_allowed  BOOLEAN NOT NULL DEFAULT FALSE,
                is_admin    BOOLEAN NOT NULL DEFAULT FALSE,
                day_payment INTEGER NOT NULL DEFAULT 0,
                settings    TEXT NOT NULL DEFAULT '{}'
            )
        """)
        self.con.commit()

    def close(self):
        """
            Закрывает соединение
        """
        self.con.close()
    
    def add_user(self, user_id: int, chat_id: int) -> int:
        """
            Добавление id и chat id пользователя в таблицу
            :user_id: id пользователя
            :chat_id: id чата пользователя
            0 - Пользователь записан
            1 - id уже был записан
        """
        try:
            self.cur.execute("""
                INSERT INTO users (user_id, chat_id)
                VALUES (?, ?)
            """, (user_id, chat_id))
            self.con.commit()
            self.cur.execute("""
                UPDATE users
                SET settings = ?
                WHERE settings = '{}'
            """, (json.dumps({"valuen": 0, "strategy": 1, "birges": []}, ensure_ascii=False),))
            self.con.commit()
        except:
            return 1
        return 0
    
    def is_register(self, user_id: int) -> bool:
        """
            Проверка регистрации пользователя
            :user_id: id пользователя
            True - пользователь зарегистрирован
            False - пользователь не зарегистрирован
        """
        self.cur.execute("""
            SELECT * FROM users
            WHERE user_id = ?
        """, (user_id,))
        if not self.cur.fetchall():
            return False
        return True

    def is_payment(self, user_id: int) -> bool:
        """
            Проверяет подписку у пользователя
            :user_id: id пользователя
        """
        self.cur.execute("""
            SELECT * FROM users
            WHERE user_id = ? AND is_allowed = TRUE
        """, (user_id,))
        if not self.cur.fetchall():
            return False
        return True
    
    def add_payment(self, user_id: int, payment_add: int) -> None:
        """
            Добавление проплаченных дней пользователю
            :user_id: id пользователя
            :payment_add: кол-во дней добавления
        """
        self.cur.execute("""
            UPDATE users SET
            is_allowed = TRUE, day_payment = day_payment + ?
            WHERE user_id = ?
        """, (payment_add, user_id))
        self.con.commit()

    def del_allow(self, user_id: int) -> None:
        """
            Удаление статуса is_allowed
        """
        self.cur.execute("""
            UPDATE users SET
            is_allowed = FALSE
            WHERE user_id = ?
        """, (user_id,))
        self.con.commit()

    def get_payment(self, user_id: int) -> int:
        """
            Получает кол-во проплаченных дней пользователя
            :user_id: id пользователя
        """
        self.cur.execute("""
            SELECT day_payment FROM users
            WHERE user_id = ?
        """, (user_id,))
        return self.cur.fetchone()[0]

    def add_admin(self, user_id: int) -> None:
        """
            Добавляет роль администратора
            :user_id: id пользователя
        """
        self.cur.execute("""
            UPDATE users SET
            is_admin = TRUE, is_allowed = TRUE, day_payment = -1
            WHERE user_id = ?
        """, (user_id,))
        self.con.commit()

    def is_admin(self, user_id: int) -> bool:
        """
            Проверяет, админ ли пользователь
            :user_id: id пользователя
        """
        self.cur.execute("""
            SELECT 1 FROM users
            WHERE user_id = ? AND is_admin = TRUE
        """, (user_id,))
        return self.cur.fetchone() is not None
    
    def get_settings(self, user_id: int) -> dict:
        """
            Получает настройки пользователя
            :user_id: id пользователя
        """
        self.cur.execute("""
            SELECT settings FROM users
            WHERE user_id = ?
        """, (user_id,))
        return json.loads(self.cur.fetchone()[0])
    
    def set_settings(self, user_id: int, settings: dict) -> None:
        """
            Устанавливает настройки пользователя
            :user_id: id пользователя
        """
        self.cur.execute("""
            UPDATE users SET
            settings = ?
            WHERE user_id = ?
        """, (json.dumps(settings), user_id))
        self.con.commit()

    def fetch_all_payment(self) -> dict:
        """
            Получает инфо о сроке подписке всех пользователей
        """
        self.cur.execute("""
            SELECT user_id, day_payment FROM users
            WHERE is_allowed = TRUE
        """)
        answer = {}
        for i in self.cur.fetchall():
            answer[i[0]] = i[1]
        return answer

    def get_chat(self, user_id: int) -> int:
        """
            Получает id чата, по id пользователя
            :user_id: id пользователя
        """
        self.cur.execute("""
            SELECT chat_id FROM users
            WHERE user_id = ?
        """, (user_id,))
        return self.cur.fetchone()[0]
    
    