import threading
import time
import telebot
from utils.settings import GetParams
from utils.database import Codes
from utils.database import DataBase

params = GetParams("config.conf")

tg = telebot.TeleBot(params.token_tg)
codes = Codes(params.codes_path)
db = DataBase(params.db_path)

@tg.message_handler(commands=['start'])
def start(message: telebot.types.Message):
    if not db.is_register(message.from_user.id):
        tg.reply_to(message, "Привет! Введи код регистрации для продолжения")
    elif not db.is_payment(message.from_user.id):
        tg.reply_to(message, "Введи код регистрации для продолжения")
    else:
        

def bot_listener():
    while True:
        try:
            tg.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Ошибка polling: {e}")
            time.sleep(10)

if __name__ == "__main__":
    th1 = threading.Thread(target=bot_listener, args=())
    th1.start()
    th1.join()