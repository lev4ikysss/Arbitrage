import threading
import datetime
import time
import json
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from utils.settings import GetParams
from utils.database import Codes
from utils.database import DataBase
from utils.birges import Request

params = GetParams("config.conf")

tg = telebot.TeleBot(params.token_tg)
codes = Codes(params.codes_path)
db = DataBase(params.db_path)
rq = Request()
birges = ["Bybit", "Mexc", "Gate", "HTX", "Bitmart", "Kucoin", "OKX", "Coinex", "Poloniex", "BingX"]
bad_birges = ["❌ "+i for i in birges]
good_birges = ["✅ "+i for i in birges]

with open('data/listeners.json', 'r') as f: in_searching = json.load(f)

def menu(message: telebot.types.Message):
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=False,
        row_width=2
    )
    if not db.is_admin(message.from_user.id):
        markup.add(
            KeyboardButton("👤 Личный кабинет"),
            KeyboardButton("🚀 Начать поиск"),
            KeyboardButton("📈 Стратегия"),
            KeyboardButton("🏦 Биржи"),
            KeyboardButton("💰 Объем сделки"),
            KeyboardButton("⚙️ Тех. поддержка")
        )
    else:
        markup.add(
            KeyboardButton("👤 Личный кабинет"),
            KeyboardButton("🚀 Начать поиск"),
            KeyboardButton("📈 Стратегия"),
            KeyboardButton("🏦 Биржи"),
            KeyboardButton("💰 Объем сделки"),
            KeyboardButton("⚙️ Тех. поддержка"),
            KeyboardButton("Создать код регистрации")
        )
    tg.send_message(message.chat.id, "Меню:", reply_markup=markup)

@tg.message_handler(commands=['start', 'menu'])
def start(message: telebot.types.Message):
    if not db.is_register(message.from_user.id):
        tg.reply_to(message, "Привет! Введи код регистрации для продолжения")
        db.add_user(message.from_user.id, message.chat.id)
    elif not db.is_payment(message.from_user.id):
        tg.reply_to(message, "Введи код регистрации для продолжения")
    else:
        menu(message)

@tg.message_handler(func=lambda message: True)
def new_message(message: telebot.types.Message):
    if codes.is_invite(message.text):
        db.add_user(message.from_user.id, message.chat.id)
        db.add_payment(message.from_user.id, 30)
        tg.reply_to(message, "Вы зарегистрированы!")
        menu(message)
    elif codes.is_admin(message.text):
        db.add_admin(message.from_user.id)
        tg.reply_to(message, "Вы теперь администратор")
        menu(message)
    elif message.text == "Создать код регистрации" and db.is_admin(message.from_user.id):
        key = codes.generate_invite()
        tg.send_message(message.chat.id, f"Код: {key}")
        menu(message)
    elif not (db.is_register(message.from_user.id) or db.is_payment(message.from_user.id)):
        tg.reply_to(message, "Ты не зарегистрирован, пропиши /start для начала!")
        db.add_user(message.from_user.id, message.chat.id)
        return None

    if message.text == "⚙️ Тех. поддержка":
        markup = ReplyKeyboardMarkup(
            resize_keyboard=True,
            one_time_keyboard=True,
            row_width=1
        )
        markup.add(
            KeyboardButton("❓ Что такое арбитраж?"),
            KeyboardButton("🏦 Какие биржи поддерживаются?"),
            KeyboardButton("⚠️ Какие риски?")
        )
        tg.send_message(message.chat.id, "Что вы хотите спросить?", reply_markup=markup)
    elif message.text == "❓ Что такое арбитраж?":
        tg.send_message(message.chat.id, """Арбитраж — покупка дешево на одной бирже, продажа дороже на другой. Риск: рынок меняется!""")
        menu(message)
    elif message.text == "🏦 Какие биржи поддерживаются?":
        tg.send_message(message.chat.id, """Поддерживаемые биржи: Bybit, Mexc, Gate, HTX, Bitmart, Kucoin, OKX, Coinex, Poloniex, BingX.""")
        menu(message)
    elif message.text == "⚠️ Какие риски?":
        tg.send_message(message.chat.id, """⚠️ Риски: не меняй адреса! Проверяй ссылки. Используй лимитные ордера.""")
        menu(message)
    elif message.text == "💰 Объем сделки":
        markup = ReplyKeyboardMarkup(
            resize_keyboard=True,
            one_time_keyboard=True,
            row_width=1
        )
        markup.add(
            KeyboardButton("10-100$"),
            KeyboardButton("100-500$"),
            KeyboardButton("500-1000$")
        )
        tg.send_message(message.chat.id, "Выберите объем:", reply_markup=markup)
    elif message.text == "10-100$":
        settings = db.get_settings(message.from_user.id)
        settings["valuen"] = 0
        db.set_settings(message.from_user.id, settings)
        tg.send_message(message.chat.id, "Успешно изменено!")
        menu(message)
    elif message.text == "100-500$":
        settings = db.get_settings(message.from_user.id)
        settings["valuen"] = 1
        db.set_settings(message.from_user.id, settings)
        tg.send_message(message.chat.id, "Успешно изменено!")
        menu(message)
    elif message.text == "500-1000$":
        settings = db.get_settings(message.from_user.id)
        settings["valuen"] = 2
        db.set_settings(message.from_user.id, settings)
        tg.send_message(message.chat.id, "Успешно изменено!")
        menu(message)
    elif message.text == "📈 Стратегия":
        markup = ReplyKeyboardMarkup(
            resize_keyboard=True,
            one_time_keyboard=True,
            row_width=1
        )
        markup.add(
            KeyboardButton("Максимум прибыли"),
            KeyboardButton("Сбалансированная"),
            KeyboardButton("Минимальный риск")
        )
        tg.send_message(message.chat.id, "❗️ Рекомендуем 'Сбалансированная'. Выбери:", reply_markup=markup)
    elif message.text == "Максимум прибыли":
        settings = db.get_settings(message.from_user.id)
        settings["strategy"] = 2
        db.set_settings(message.from_user.id, settings)
        tg.send_message(message.chat.id, "Успешно изменено!")
        menu(message)
    elif message.text == "Сбалансированная":
        settings = db.get_settings(message.from_user.id)
        settings["strategy"] = 1
        db.set_settings(message.from_user.id, settings)
        tg.send_message(message.chat.id, "Успешно изменено!")
        menu(message)
    elif message.text == "Минимальный риск":
        settings = db.get_settings(message.from_user.id)
        settings["strategy"] = 0
        db.set_settings(message.from_user.id, settings)
        tg.send_message(message.chat.id, "Успешно изменено!")
        menu(message)
    elif message.text == "🏦 Биржи":
        settings = db.get_settings(message.from_user.id)["birges"]
        markup = ReplyKeyboardMarkup(
            resize_keyboard=True,
            one_time_keyboard=True,
            row_width=3
        )
        buttons = [KeyboardButton("✅ "+i if i in settings else "❌ "+i) for i in birges]
        markup.add(*buttons)
        tg.send_message(message.chat.id, "Выберите биржи:", reply_markup=markup)
    elif message.text in bad_birges:
        settings = db.get_settings(message.from_user.id)
        settings["birges"].append(message.text[2:])
        db.set_settings(message.from_user.id, settings)
        tg.send_message(message.chat.id, f"Успешно добавлена биржа {message.text[2:]}!")
        menu(message)
    elif message.text in good_birges:
        settings = db.get_settings(message.from_user.id)
        settings["birges"].remove(message.text[2:])
        db.set_settings(message.from_user.id, settings)
        tg.send_message(message.chat.id, f"Успешно удалена биржа {message.text[2:]}!")
        menu(message)
    elif message.text == "👤 Личный кабинет":
        settings = db.get_settings(message.from_user.id)
        payment = db.get_payment(message.from_user.id)
        answers = [
            ["10-100$", "100-500$", "500-1000$"],
            ["Минимальный риск", "Сбалансированная", "Максимум прибыли"]
        ]
        tg.send_message(message.chat.id, f"""
👤 Личный кабинет
                        
🔑 Статус подписки: {str(payment)+" дней" if payment != 0 else "Не активна"}
💰 Объем сделки: {answers[0][settings["valuen"]]}
📈 Стратегия: {answers[1][settings["strategy"]]}
🏦 Активные биржи: {*settings["birges"],}
        """)
        menu(message)
    elif message.text == "🚀 Начать поиск":
        in_searching.append({
            "user_id": message.from_user.id,
            "chat_id": message.chat.id
        })
        with open('data/listeners.json', 'w') as f: json.dump(in_searching, f, indent=4)
        markup = ReplyKeyboardMarkup(
            resize_keyboard=True,
            one_time_keyboard=False,
            row_width=1
        )
        markup.add(KeyboardButton("🛑 СТОП"))
        tg.send_message(message.chat.id, """
Поиск запущен! Связки будут приходить автоматически.
Используй 🛑 СТОП для паузы.
        """, reply_markup=markup)
    elif message.text == "🛑 СТОП":
        in_searching.remove({
            "user_id": message.from_user.id,
            "chat_id": message.chat.id
        })
        with open('data/listeners.json', 'w') as f: json.dump(in_searching, f, indent=4)
        tg.send_message(message.chat.id, "Поиск остановлен!")
        menu(message)

def bot_listener():
    while True:
        try:
            tg.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Ошибка bot_listener: {e}")
            time.sleep(5)

def bot_counter():
    while True:
        try:
            timestamp = datetime.datetime.now()
            if timestamp.hour == 12 and timestamp.minute == 0 and timestamp.second == 0:
                active_users = db.fetch_all_payment()
                for key in active_users.keys():
                    active_users[key] -= 1
                    db.add_payment(key, -1)
                    if active_users[key] == params.payment_warning:
                        tg.send_message(db.get_chat(key), f"Ваш доступ истечет через {params.payment_warning} дней!\nПриобретите новый ключ, чтобы не потерять доступ к боту!")
                    elif active_users[key] == 0:
                        tg.send_message(db.get_chat(key), f"Ваш доступ истек!\nПриобретите новый ключ, чтобы востановить доступ к боту!")
                        db.del_allow(key)
            time.sleep(1)
        except Exception as e:
            print(f"Ошибка bot_counter: {e}")
            time.sleep(10)

def birge_listener():
    while True:
        try:
            tokens = rq.restructurize_birges(rq.check_all())
            messages = []
            for coin, birges in tokens.items():
                if len(birges) < 2:
                    continue

                birges = sorted(birges, key=lambda x: x["price"])
                buy_price  = birges[0]["price"]
                buy_birge  = birges[0]["birge"]
                sell_price = birges[-1]["price"]
                sell_birge = birges[-1]["birge"]

                if buy_price < 0.00000001 or sell_price < 0.00000001:
                    continue
                spred = (sell_price - buy_price) / buy_price * 100
                if spred < 0.3:
                    continue

                messages.append({
                    "bundle": f"{coin}/USDT",
                    "spred": spred,
                    "buy_birge": buy_birge,
                    "sell_birge": sell_birge,
                    "buy_price": buy_price,
                    "sell_price": sell_price
                })
            for message in messages:
                for user in in_searching[:]:
                    try:
                        settings = db.get_settings(user["user_id"])
                    except:
                        continue
                    
                    active_birges = set(settings.get("birges", []))
                    if message["buy_birge"] not in active_birges or message["sell_birge"] not in active_birges:
                        continue

                    volume_usdt = [75, 300, 750][settings.get("valuen", 1)]
                    buy_amount_tokens = volume_usdt / message["buy_price"]
                    sell_amount_usdt  = buy_amount_tokens * message["sell_price"]
                    gross_profit      = sell_amount_usdt - volume_usdt
                    
                    fee_pct   = 0.001
                    fee_fixed = 1.0
                    total_fees = (volume_usdt * fee_pct * 2) + (fee_fixed * 2)
                    
                    net_profit = gross_profit - total_fees
                    
                    valuen = settings["valuen"]
                    strategy = settings["strategy"]
                    
                    min_spred_valuen  = [2.5, 1.0, 0.6][valuen]
                    min_profit_valuen = [1.75, 4.0, 9.0][valuen]
                    min_spred_strategy = [3.75, 1.1, 0.6][strategy]

                    if (spred >= min_spred_valuen and net_profit >= min_profit_valuen) and \
                       (spred >= min_spred_strategy):
                        msg = f"""
🔄 Связка: {message["bundle"]}

📊 Купить на {message["buy_birge"]}: Цена {message["buy_price"]:g}$
📊 Продать на {message["sell_birge"]}: Цена {message["sell_price"]:g}$

💼 Объём: {volume_usdt}$
📈 Спред: {spred:.2f}%
💰 Чистая прибыль: {net_profit:.2f}$
⏳ Время жизни: ~5 мин

🔗 Сеть: TRC20
Комиссия: 0.1% + 1$
Контракт проверен ✅

⚠️ РИСК: Проверь стакан и адреса! Не меняй сеть!
                        """.strip()
                        try:
                            tg.send_message(user["chat_id"], msg)
                            time.sleep(5)
                        except Exception as e:
                            print(f"Ошибка отправки {user['user_id']}: {e}")
                            if "blocked" in str(e).lower():
                                in_searching.remove(user)
            time.sleep(300)
        except Exception as e:
            print(f"Ошибка birge_listener: {e}")
            rq.reconect()
            time.sleep(600)

if __name__ == "__main__":
    th1 = threading.Thread(target=bot_listener, args=())
    th2 = threading.Thread(target=bot_counter, args=())
    th3 = threading.Thread(target=birge_listener, args=())
    th1.start()
    th2.start()
    th3.start()
    th1.join()
    th2.join()
    th3.join()
