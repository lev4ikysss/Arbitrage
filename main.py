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

actions = {}
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
        tg.send_message(message.chat.id, "Напишите ваш минимум объём сделки (число):")
        actions[str(message.from_user.id)] = {
            "chat_id": message.chat.id,
            "action": 0
        }
    elif str(message.from_user.id) in actions.keys() and actions[str(message.from_user.id)]["action"] == 0:
        settings = db.get_settings(message.from_user.id)
        settings["valuen-min"] = int(message.text)
        db.set_settings(message.from_user.id, settings)
        tg.send_message(message.chat.id, "Напишите ваш максимум объём сделки (число):")
        actions[str(message.from_user.id)]["action"] = 1
    elif str(message.from_user.id) in actions.keys() and actions[str(message.from_user.id)]["action"] == 1:
        settings = db.get_settings(message.from_user.id)
        settings["valuen-max"] = int(message.text)
        db.set_settings(message.from_user.id, settings)
        tg.send_message(message.chat.id, "Успешно!")
        actions.pop(str(message.from_user.id))
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
        answers = ["Минимальный риск", "Сбалансированная", "Максимум прибыли"]
        tg.send_message(message.chat.id, f"""
👤 Личный кабинет
                        
🔑 Статус подписки: {str(payment)+" дней" if payment != 0 else "Не активна"}
💰 Объем сделки: ${settings["valuen-min"]}-{settings["valuen-max"]}
📈 Стратегия: {answers[settings["strategy"]]}
🏦 Активные биржи: {', '.join(settings["birges"])}
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
    MAX_SENT_PER_CYCLE = 5
    COOLDOWN_SEC = 300
    SLIPPAGE_PCT = 0.3
    SAFETY_FACTOR = 0.7

    while True:
        try:
            tokens = rq.restructurize_birges(rq.check_all())
            print(f"Получено {len(tokens)} монет с котировками")  # отладка

            for user in in_searching[:]:
                user_id = user["user_id"]
                chat_id = user["chat_id"]

                if user_id in last_sent and time.time() - last_sent[user_id] < COOLDOWN_SEC:
                    continue

                try:
                    settings = db.get_settings(user_id)
                except Exception as e:
                    print(f"Не удалось получить настройки {user_id}: {e}")
                    continue

                active_birges = set(settings.get("birges", []))
                if len(active_birges) < 2:
                    continue

                user_min_vol = settings.get("valuen-min", 10)
                user_max_vol = settings.get("valuen-max", 1000)
                strategy = settings.get("strategy", 1)

                strategy_mult = [0.6, 1.0, 1.4][strategy]
                base_vol = (user_min_vol + user_max_vol) / 2
                max_allowed_vol = min(user_max_vol * strategy_mult, user_max_vol)

                sent_count = 0

                for coin, all_birges in tokens.items():
                    if sent_count >= MAX_SENT_PER_CYCLE:
                        break

                    user_birges = [b for b in all_birges if b["birge"] in active_birges]
                    if len(user_birges) < 2:
                        continue

                    user_birges = sorted(user_birges, key=lambda x: x["price"])

                    buy_price  = user_birges[0]["price"]
                    buy_birge  = user_birges[0]["birge"]
                    sell_price = user_birges[-1]["price"]
                    sell_birge = user_birges[-1]["birge"]

                    if buy_price < 1e-8 or sell_price < 1e-8:
                        continue

                    spred = (sell_price - buy_price) / buy_price * 100

                    # Временно слабляем фильтр для теста (потом вернёшь)
                    if spred < 0.3 or spred > 100:  # было 0.3 — снизили до 0.15%
                        continue

                    print(f"Потенциальная связка {coin}: спред {spred:.2f}% на {buy_birge} → {sell_birge}")

                    # === Пытаемся получить стакан ===
                    depth_buy_usdt = depth_sell_usdt = 0
                    volume_usdt = base_vol * strategy_mult  # fallback
                    volume_usdt = max(user_min_vol, min(volume_usdt, user_max_vol))

                    try:
                        depth_data = rq.get_depth(
                            base_token=coin,
                            quote_token="USDT",
                            exchanges=[buy_birge, sell_birge]
                        )

                        buy_info  = depth_data.get("buy_exchange",  {})
                        sell_info = depth_data.get("sell_exchange", {})

                        if buy_info.get("success") and sell_info.get("success"):
                            depth_buy_usdt  = buy_info.get("depth_buy_usdt",  0)
                            depth_sell_usdt = sell_info.get("depth_sell_usdt", 0)
                            safe_volume = min(depth_buy_usdt, depth_sell_usdt) * SAFETY_FACTOR

                            # Реальный объём = минимум из стакана и лимитов пользователя
                            volume_usdt = min(safe_volume, max_allowed_vol)
                            volume_usdt = max(volume_usdt, user_min_vol)

                            print(f"  → стакан OK, volume={volume_usdt:.1f}$ (buy:{depth_buy_usdt:.0f}, sell:{depth_sell_usdt:.0f})")

                        else:
                            print(f"  → стакан не получен, использую fallback {volume_usdt:.1f}$")

                    except Exception as e:
                        print(f"  → ошибка get_depth для {coin}: {e}")

                    if volume_usdt < user_min_vol * 0.5:
                        print(f"  → объём слишком мал ({volume_usdt:.1f}$), пропуск")
                        continue

                    # Расчёт прибыли
                    buy_amount_tokens = volume_usdt / buy_price
                    sell_amount_usdt  = buy_amount_tokens * sell_price
                    gross_profit      = sell_amount_usdt - volume_usdt

                    fee_pct   = 0.005   # 0.5%
                    fee_fixed = 1.0
                    total_fees = (volume_usdt * fee_pct * 2) + (fee_fixed * 2)
                    net_profit = gross_profit - total_fees

                    min_spred_strategy = [3.75, 1.1, 0.6][strategy]
                    min_spred_valuen   = [1.0, 0.4, 0.2][settings["strategy"]]
                    min_profit_valuen  = [0.5, 2.0, 5.0][settings["strategy"]]

                    if (spred >= min_spred_valuen and net_profit >= min_profit_valuen) and \
                       (spred >= min_spred_strategy):

                        msg = f"""
🔄 Связка: {coin}/USDT

📊 Купить на {buy_birge}: {buy_price:.8g}$
📊 Продать на {sell_birge}: {sell_price:.8g}$

💼 Объём: {volume_usdt:.0f}$
📈 Спред: {spred:.2f}%
💰 Чистая прибыль: {net_profit:.2f}$
⏳ Время жизни: ~5 мин

🔗 Сеть: TRC20
Комиссия: {fee_pct*100:.2f}% + 1$
Контракт проверен ✅

⚠️ РИСК: Проверь стакан и адреса!
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
                            print(f"Сообщение отправлено {user_id} по {coin}")
                            sent_count += 1
                            last_sent[user_id] = time.time()
                            time.sleep(1.5)

                        except Exception as e:
                            print(f"Ошибка отправки {user_id} по {coin}: {e}")
                            if "429" in str(e):
                                time.sleep(30)

            time.sleep(300)

        except Exception as e:
            print(f"Глобальная ошибка birge_listener: {e}")
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
