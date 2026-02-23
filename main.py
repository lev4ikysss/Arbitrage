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
        markup.add(*buttons, KeyboardButton("Вернуться в меню"))
        tg.send_message(message.chat.id, "Выберите биржи:", reply_markup=markup)
    elif message.text in bad_birges:
        settings = db.get_settings(message.from_user.id)
        settings["birges"].append(message.text[2:])
        db.set_settings(message.from_user.id, settings)
        markup = ReplyKeyboardMarkup(
            resize_keyboard=True,
            one_time_keyboard=True,
            row_width=3
        )
        buttons = [KeyboardButton("✅ "+i if i in settings["birges"] else "❌ "+i) for i in birges]
        markup.add(*buttons, KeyboardButton("Вернуться в меню"))
        tg.send_message(message.chat.id, f"Успешно добавлена биржа {message.text[2:]}!", reply_markup=markup)
    elif message.text in good_birges:
        settings = db.get_settings(message.from_user.id)
        settings["birges"].remove(message.text[2:])
        db.set_settings(message.from_user.id, settings)
        markup = ReplyKeyboardMarkup(
            resize_keyboard=True,
            one_time_keyboard=True,
            row_width=3
        )
        buttons = [KeyboardButton("✅ "+i if i in settings["birges"] else "❌ "+i) for i in birges]
        markup.add(*buttons, KeyboardButton("Вернуться в меню"))
        tg.send_message(message.chat.id, f"Успешно удалена биржа {message.text[2:]}!", reply_markup=markup)
    elif message.text == "Вернуться в меню":
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
    last_sent = {}
    while True:
        try:
            tokens = rq.restructurize_birges(rq.check_all())
            for user in in_searching[:]:
                user_id = user["user_id"]
                chat_id = user["chat_id"]
                if user_id in last_sent and time.time() - last_sent[user_id] < 300:
                    continue
                try:
                    settings = db.get_settings(user_id)
                except:
                    continue
                active_birges = set(settings.get("birges", []))
                if len(active_birges) < 2:
                    continue
                volume_usdt = [75, 300, 750][settings.get("valuen", 1)]
                strategy    = settings.get("strategy", 1)
                min_spred_strategy = [3.75, 1.1, 0.6][strategy]
                sent_count = 0
                for coin, all_birges in tokens.items():
                    if sent_count >= 5:
                        break
                    user_birges = [b for b in all_birges if b["birge"] in active_birges]
                    if len(user_birges) < 2:
                        continue
                    user_birges = sorted(user_birges, key=lambda x: x["price"])
                    buy_price  = user_birges[0]["price"]
                    buy_birge  = user_birges[0]["birge"]
                    sell_price = user_birges[-1]["price"]
                    sell_birge = user_birges[-1]["birge"]
                    if buy_price < 0.00000001 or sell_price < 0.00000001:
                        continue
                    spred = (sell_price - buy_price) / buy_price * 100
                    if spred < 0.3 or spred > 500:
                        continue
                    buy_amount_tokens = volume_usdt / buy_price
                    sell_amount_usdt = buy_amount_tokens * sell_price
                    gross_profit = sell_amount_usdt - volume_usdt
                    fee_pct = 0.01
                    fee_fixed = 1.0
                    total_fees = (volume_usdt * fee_pct * 2) + (fee_fixed * 2)
                    net_profit = gross_profit - total_fees
                    min_spred_valuen = [2.5, 1.0, 0.6][settings["valuen"]]
                    min_profit_valuen = [1.75, 4.0, 9.0][settings["valuen"]]
                    if (spred >= min_spred_valuen and net_profit >= min_profit_valuen) and \
                       (spred >= min_spred_strategy):
                        msg = f"""
🔄 Связка: {coin}/USDT

📊 Купить на {buy_birge}: Цена {buy_price:.8g}$
📊 Продать на {sell_birge}: Цена {sell_price:.8g}$

💼 Объём: {volume_usdt}$
📈 Спред: {spred:.2f}%
💰 Чистая прибыль: {net_profit:.2f}$
⏳ Время жизни: ~5 мин

🔗 Сеть: TRC20
Комиссия: 1% + 1$
Контракт проверен ✅

⚠️ РИСК: Проверь стакан и адреса! Не меняй сеть!
                        """.strip()
                        msg = msg.replace("Bybit", f'<a href="https://www.bybit.com/ru-RU/trade/spot/{coin}/USDT">Bybit</a>')
                        msg = msg.replace("Mexc", f'<a href="https://www.mexc.com/ru-RU/exchange/{coin}_USDT?_from=market">Mexc</a>')
                        msg = msg.replace("Gate", f'<a href="https://www.gate.com/ru/trade/{coin}_USDT">Gate</a>')
                        msg = msg.replace("HTX", f'<a href="https://www.htx.com/trade/{coin.lower()}_usdt?type=spot">HTX</a>')
                        msg = msg.replace("Bitmart", f'<a href="https://www.bitmart.com/ru-RU/trade/{coin}_USDT?type=spot">Bitmart</a>')
                        msg = msg.replace("Kucoin", f'<a href="https://www.kucoin.com/trade/{coin}-USDT">Kucoin</a>')
                        msg = msg.replace("OKX", f'<a href="https://www.okx.com/ru/trade-spot/{coin.lower()}-usdt">OKX</a>')
                        msg = msg.replace("Coinex", f'<a href="https://www.coinex.com/ru/exchange/{coin.lower()}-usdt">Coinex</a>')
                        msg = msg.replace("Poloniex", f'<a href="https://www.poloniex.com/ru/trade/{coin}_USDT">Poloniex</a>')
                        msg = msg.replace("BingX", f'<a href="https://bingx.com/en/spot/{coin}USDT">BingX</a>')
                        try:
                            tg.send_message(
                                chat_id,
                                msg,
                                parse_mode="HTML",
                                disable_web_page_preview=True
                            )
                            sent_count += 1
                            last_sent[user_id] = time.time()
                            time.sleep(1.5)
                        except telebot.apihelper.ApiTelegramException as e:
                            if e.error_code == 429:
                                retry_after = e.result_json.get("parameters", {}).get("retry_after", 30)
                                print(f"Rate limit для {user_id}. Ждём {retry_after} сек")
                                time.sleep(retry_after + 2)
                            elif "blocked" in str(e).lower() or "forbidden" in str(e).lower():
                                print(f"Пользователь {user_id} заблокировал бота — удаляем")
                                in_searching.remove(user)
                            else:
                                print(f"Другая ошибка отправки {user_id}: {e}")
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
