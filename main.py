import threading
import datetime
import time
import json
import asyncio
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from utils.settings import GetParams
from utils.database import Codes
from utils.database import DataBase
from utils.birges import (
    Birga, get_birga_api, fetch_orderbooks_for_symbols,
    close_all_sessions, OrderBook, get_all_symbols, get_universal_symbols,
    BIRGA_REGISTRY
)
from utils.blockchain import get_blockchain_info

params = GetParams("config.conf")

tg = telebot.TeleBot(params.token_tg)
codes = Codes(params.codes_path)
db = DataBase(params.db_path)
birges = ["Bybit", "Mexc", "Gate", "HTX", "Bitmart", "Kucoin", "OKX", "Coinex", "Poloniex", "BingX"]
bad_birges = ["❌ "+i for i in birges]
good_birges = ["✅ "+i for i in birges]

actions = {}
with open('data/listeners.json', 'r') as f: in_searching = json.load(f)

# Динамический список пар (загружается с бирж)
ALL_ARBITRAGE_PAIRS: list[str] = []

def format_notification(pair: str, buy_ob: OrderBook, sell_ob: OrderBook,
                        buy_exchange: str, sell_exchange: str,
                        volume: float, spread: float,
                        net_profit: float, lifetime_hours: float,
                        lifetime_seconds: float = None,
                        blockchain_info: dict = None) -> str:
    """Форматирует уведомление о арбитражной связке"""

    def format_orders(ob: OrderBook) -> str:
        total_qty = sum(e.quantity for e in ob.asks)
        if ob.asks:
            avg_price = sum(e.price * e.quantity for e in ob.asks) / total_qty
            orders_info = f"{len(ob.asks)} ордеров: " + ", ".join(
                f"{e.quantity:.4f} - {e.price}" for e in ob.asks[:3]
            )
            return f"Средняя цена: {avg_price:.6f}\n{orders_info}"
        return "Нет ордеров"

    buy_trade_url = get_exchange_trade_url(buy_exchange, pair)
    buy_withdraw_url = get_exchange_withdraw_url(buy_exchange, pair)
    sell_trade_url = get_exchange_trade_url(sell_exchange, pair)
    sell_deposit_url = get_exchange_deposit_url(sell_exchange, pair)

    base = pair.split('/')[0]

    # Формируем информацию о сети
    if blockchain_info:
        confirmations = getattr(blockchain_info, "confirmations", 6)
        block_time = getattr(blockchain_info, "avg_block_time", 15)
        is_native = getattr(blockchain_info, "is_native", True)
        network_name = getattr(blockchain_info, "name", "N/A")
        confirm_time_minutes = (confirmations * block_time) / 60
        if confirm_time_minutes < 1:
            confirm_time_str = f"~ {int(confirm_time_minutes * 60)} сек"
        elif confirm_time_minutes < 60:
            confirm_time_str = f"~ {int(confirm_time_minutes)} мин"
        else:
            hours = int(confirm_time_minutes / 60)
            mins = int(confirm_time_minutes % 60)
            confirm_time_str = f"~ {hours}ч {mins}м"
        contract_label = "нативная монета" if is_native else f"контракт ({network_name})"
        blockchain_line = f"🔐 Подтверждений: {confirmations} | {confirm_time_str} (block time {block_time:.0f}с)"
    else:
        confirmations = 6
        block_time = 15
        contract_label = "нативная монета"
        blockchain_line = "🔐 Количество подтверждений: 6 | ~ 6 подтверждений (block time N/A)"

    return f"""💠 {pair}

🔹 Купить → {buy_exchange} (<a href="{buy_trade_url}">торговля</a>) | <a href="{buy_withdraw_url}">вывод</a>
         {format_orders(buy_ob)}

🔹 Продать → {sell_exchange} (<a href="{sell_trade_url}">торговля</a>) | <a href="{sell_deposit_url}">депозит</a>
         {format_orders(sell_ob)}


💰 Объём: {volume:.2f} USDT
📊 Спред: {spread:.2f}%
📈 Чистая прибыль: {net_profit:.3f} USDT
⏱️ Время жизни связки: {int(lifetime_seconds // 60)}м {int(lifetime_seconds % 60)}с


🔗 Сети: {base} - вывод ✅, депозит ✅
🏷️ Контракт: {contract_label}
{blockchain_line}
💸 Комиссии: B – {volume * 0.001:.3f} USDT, S – {volume * 0.001:.3f} USDT, W – {volume * 0.0001:.6f} USDT (сеть {base})"""


def get_exchange_trade_url(exchange: str, pair: str) -> str:
    """Получить URL для торговли"""
    p = pair.replace("/", "_")
    urls = {
        "Bybit": f"https://www.bybit.com/ru/trade/{p}",
        "Mexc": f"https://www.mexc.com/ru/trade/{p}",
        "Gate": f"https://www.gate.io/ru/trade/{p}",
        "HTX": f"https://www.htx.com/en-us/exchange/{p.lower()}",
        "Bitmart": f"https://www.bitmart.com/ru/trade/{p}",
        "Kucoin": f"https://www.kucoin.com/ru/trade/{p}",
        "OKX": f"https://www.okx.com/ru/trade/{p.lower()}",
        "Coinex": f"https://www.coinex.com/ru/exchange/{p.lower()}",
        "Poloniex": f"https://poloniex.com/exchange/{p}",
        "BingX": f"https://www.bingx.com/ru/trade/{p}",
    }
    return urls.get(exchange, "#")


def get_exchange_withdraw_url(exchange: str, pair: str) -> str:
    """Получить URL для вывода"""
    p = pair.replace("/", "_")
    urls = {
        "Bybit": "https://www.bybit.com/assets/spot/withdraw",
        "Mexc": "https://www.mexc.com/assets/spot/withdraw",
        "Gate": "https://www.gateio.me/assets/spot/withdraw",
        "HTX": "https://www.htx.com/en-us/finance/withdrawal/",
        "Bitmart": "https://www.bitmart.com/withdraw",
        "Kucoin": "https://www.kucoin.com/assets/withdraw",
        "OKX": "https://www.okx.com/ru/finance/withdraw/",
        "Coinex": "https://www.coinex.com/withdraw",
        "Poloniex": "https://poloniex.com/withdraw",
        "BingX": "https://www.bingx.com/withdraw",
    }
    return urls.get(exchange, "#")


def get_exchange_deposit_url(exchange: str, pair: str) -> str:
    """Получить URL для депозита"""
    p = pair.replace("/", "_")
    urls = {
        "Bybit": "https://www.bybit.com/assets/spot/deposit",
        "Mexc": "https://www.mexc.com/assets/spot/deposit",
        "Gate": "https://www.gateio.me/assets/spot/deposit",
        "HTX": "https://www.htx.com/en-us/finance/deposit/",
        "Bitmart": "https://www.bitmart.com/deposit",
        "Kucoin": "https://www.kucoin.com/assets/deposit",
        "OKX": "https://www.okx.com/ru/finance/deposit/",
        "Coinex": "https://www.coinex.com/deposit",
        "Poloniex": "https://poloniex.com/deposit",
        "BingX": "https://www.bingx.com/deposit",
    }
    return urls.get(exchange, "#")


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
        try:
            vol = int(message.text)
        except ValueError:
            tg.send_message(message.chat.id, "Введите число!")
            return
        settings = db.get_settings(message.from_user.id)
        settings["valuen-min"] = vol
        db.set_settings(message.from_user.id, settings)
        tg.send_message(message.chat.id, "Напишите ваш максимум объём сделки (число):")
        actions[str(message.from_user.id)]["action"] = 1
        return
    elif str(message.from_user.id) in actions.keys() and actions[str(message.from_user.id)]["action"] == 1:
        try:
            vol = int(message.text)
        except ValueError:
            tg.send_message(message.chat.id, "Введите число!")
            return
        settings = db.get_settings(message.from_user.id)
        settings["valuen-max"] = vol
        db.set_settings(message.from_user.id, settings)
        tg.send_message(message.chat.id, "Успешно!")
        actions.pop(str(message.from_user.id))
        menu(message)
        return
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
        user_settings = db.get_settings(message.from_user.id)
        user_birges = user_settings.get("birges", ["Bybit", "Mexc", "Gate", "HTX", "Bitmart", "Kucoin", "OKX", "Coinex", "Poloniex", "BingX"])
        markup = ReplyKeyboardMarkup(
            resize_keyboard=True,
            one_time_keyboard=True,
            row_width=3
        )
        buttons = [KeyboardButton("✅ "+i if i in user_birges else "❌ "+i) for i in birges]
        markup.add(*buttons, KeyboardButton("Вернуться в меню"))
        tg.send_message(message.chat.id, "Выберите биржи:", reply_markup=markup)
        return
    elif message.text in bad_birges:
        user_settings = db.get_settings(message.from_user.id)
        user_birges = user_settings.get("birges", [])
        user_birges.append(message.text[2:])
        user_settings["birges"] = user_birges
        db.set_settings(message.from_user.id, user_settings)
        markup = ReplyKeyboardMarkup(
            resize_keyboard=True,
            one_time_keyboard=True,
            row_width=3
        )
        buttons = [KeyboardButton("✅ "+i if i in user_birges else "❌ "+i) for i in birges]
        markup.add(*buttons, KeyboardButton("Вернуться в меню"))
        tg.send_message(message.chat.id, f"Успешно добавлена биржа {message.text[2:]}!", reply_markup=markup)
        return
    elif message.text in good_birges:
        user_settings = db.get_settings(message.from_user.id)
        user_birges = user_settings.get("birges", [])
        user_birges.remove(message.text[2:])
        user_settings["birges"] = user_birges
        db.set_settings(message.from_user.id, user_settings)
        markup = ReplyKeyboardMarkup(
            resize_keyboard=True,
            one_time_keyboard=True,
            row_width=3
        )
        buttons = [KeyboardButton("✅ "+i if i in user_birges else "❌ "+i) for i in birges]
        markup.add(*buttons, KeyboardButton("Вернуться в меню"))
        tg.send_message(message.chat.id, f"Успешно удалена биржа {message.text[2:]}!", reply_markup=markup)
        return
    elif message.text == "Вернуться в меню":
        menu(message)
    elif message.text == "👤 Личный кабинет":
        settings = db.get_settings(message.from_user.id)
        payment = db.get_payment(message.from_user.id)
        answers = ["Минимальный риск", "Сбалансированная", "Максимум прибыли"]
        volume_min = settings.get("valuen-min", 50)
        volume_max = settings.get("valuen-max", 150)
        strategy = settings.get("strategy", 1)
        user_birgas = settings.get("birges", ["Bybit", "Mexc", "Gate", "HTX", "Bitmart", "Kucoin", "OKX", "Coinex", "Poloniex", "BingX"])
        tg.send_message(message.chat.id, f"""
👤 Личный кабинет

🔑 Статус подписки: {str(payment)+" дней" if payment != 0 else "Не активна"}
💰 Объем сделки: ${volume_min}-{volume_max}
📈 Стратегия: {answers[strategy]}
🏦 Активные биржи: {', '.join(user_birgas)}
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


async def find_arbitrage_opportunities(orderbooks: dict[Birga, dict[str, OrderBook]],
                                  volume_min: float, volume_max: float,
                                  strategy: int = 1,
                                  min_spread: float = 1.0) -> list[dict]:
    """Находит арбитражные возможности между биржами

    :param strategy: 0 = минимальный риск, 1 = сбалансированная, 2 = максимум прибыли
    """
    opportunities = []

    # Собрать все пары из полученных orderbooks
    all_pairs = set()
    for birga_obs in orderbooks.values():
        all_pairs.update(birga_obs.keys())

    # Стратегия влияет на объём:
    # strategy 0: объём = volume_min + 20% от range (консервативно)
    # strategy 1: объём = volume_min + 50% от range (баланс)
    # strategy 2: объём = volume_min + 80% от range (агрессивно)
    strategy_risk = [0.2, 0.5, 0.8][strategy]

    for pair in all_pairs:
        best_buy = None
        best_sell = None
        best_profit = 0.0

        # Собираем лучшие цены покупки и продажи по биржам
        for birga in orderbooks.keys():
            if pair not in orderbooks[birga]:
                continue
            ob = orderbooks[birga][pair]
            if not ob.asks or not ob.bids:
                continue

            # Лучшая цена покупки (asks - мы покупаем)
            best_ask = min(ob.asks, key=lambda x: x.price)
            # Лучшая цена продажи (bids - мы продаем)
            best_bid = max(ob.bids, key=lambda x: x.price)

            # Ищем лучшую связку: купить дешево на одной, продать дорого на другой
            for sell_birga in orderbooks.keys():
                if sell_birga == birga or pair not in orderbooks[sell_birga]:
                    continue
                sell_ob = orderbooks[sell_birga][pair]
                if not sell_ob.bids:
                    continue

                sell_best_bid = max(sell_ob.bids, key=lambda x: x.price)

                # Расчет спреда
                spread = ((sell_best_bid.price - best_ask.price) / best_ask.price) * 100

                if spread <= min_spread:
                    continue

                # Динамический расчёт объёма:
                # 1. Базовый объём от стратегии + бонус за спред
                # 2. Ограничиваем ликвидностью ордербука
                spread_coefficient = max(0, (spread - min_spread) / min_spread)
                volume_range = volume_max - volume_min
                base_volume = volume_min + strategy_risk * volume_range
                dynamic_volume = base_volume + spread_coefficient * volume_range * 0.5

                # Учитываем ликвидность ордербука - ищем максимальный объём который можем закрыть
                cumulative_volume = 0
                target_price = best_ask.price * 1.02  # цена +2% от лучшего аска (допустимый проскальзывание)
                for ask in ob.asks:
                    if ask.price <= target_price:
                        cumulative_volume += ask.quantity * ask.price
                    else:
                        break

                buy_volume = min(dynamic_volume, cumulative_volume, volume_max)
                buy_volume = max(buy_volume, volume_min)

                # Расчет комиссий (примерно 0.1% за торговлю + 0.01% за вывод)
                commission_buy = buy_volume * 0.001
                commission_sell = buy_volume * 0.001
                commission_withdraw = buy_volume * 0.0001

                net_profit = (sell_best_bid.price - best_ask.price) * (buy_volume / best_ask.price)
                net_profit -= commission_buy + commission_sell + commission_withdraw

                # Расчёт времени жизни связки:
                # Время = время на "съедание" ордеров + время на блокчейн-подтверждения
                orders_to_fill = 0
                volume_filled = 0
                avg_fill_time_ms = 200  # среднее время заполнения ордера в мс
                for ask in ob.asks:
                    if volume_filled >= buy_volume:
                        break
                    fill_qty = min(ask.quantity, (buy_volume - volume_filled) / best_ask.price)
                    volume_filled += fill_qty * best_ask.price
                    orders_to_fill += 1
                lifetime_seconds = orders_to_fill * avg_fill_time_ms / 1000 * 600
                # Конвертируем в часы, минимум 1 минута
                lifetime_hours = max(1/3600, min(lifetime_seconds / 3600, 24.0))

                if net_profit > best_profit:
                    best_profit = net_profit
                    best_buy = (birga, ob)
                    best_sell = (sell_birga, sell_ob)

        if best_buy and best_sell:
            # Получаем информацию о блокчейне для базовой монеты
            base_symbol = pair.split('/')[0]
            blockchain_info = await get_blockchain_info(base_symbol)

            opportunities.append({
                "pair": pair,
                "buy_birga": best_buy[0],
                "sell_birga": best_sell[0],
                "buy_ob": best_buy[1],
                "sell_ob": best_sell[1],
                "spread": ((max(best_sell[1].bids, key=lambda x: x.price).price -
                           min(best_buy[1].asks, key=lambda x: x.price).price) /
                          min(best_buy[1].asks, key=lambda x: x.price).price * 100),
                "net_profit": best_profit,
                "volume": buy_volume,
                "lifetime_hours": lifetime_hours,
                "lifetime_seconds": lifetime_seconds,
                "blockchain_info": blockchain_info,
            })

    return opportunities


async def arbitrage_loop_async():
    """Цикл поиска и рассылки арбитражных возможностей"""
    global ALL_ARBITRAGE_PAIRS

    while True:
        try:
            # Загружаем активных слушателей
            with open('data/listeners.json', 'r') as f:
                listeners = json.load(f)

            if not listeners:
                await asyncio.sleep(30)
                continue

            # Получаем список пар с бирж
            all_birgas = list(Birga)
            all_birga_symbols = await get_all_symbols(all_birgas)

            # Универсальные пары (есть на >=2 биржах)
            arbitrage_pairs = get_universal_symbols(all_birga_symbols, min_birgas=2)
            ALL_ARBITRAGE_PAIRS = arbitrage_pairs

            if len(arbitrage_pairs) < 100:
                print(f"Предупреждение: найдено только {len(arbitrage_pairs)} пар")

            # Собираем уникальные настройки пользователей
            user_settings = {}
            for listener in listeners:
                uid = listener["user_id"]
                if uid not in user_settings:
                    settings = db.get_settings(uid)
                    user_birgas = [Birga[b.upper()] for b in settings.get("birges", birges) if b in [b.value for b in Birga]]
                    user_settings[uid] = {
                        "chat_id": listener["chat_id"],
                        "birges": user_birgas,
                        "volume_min": settings.get("valuen-min", 50),
                        "volume_max": settings.get("valuen-max", 150),
                        "strategy": settings.get("strategy", 1),
                    }

            # Обрабатываем батчами по 50 пар
            batch_size = 50
            for i in range(0, len(arbitrage_pairs), batch_size):
                batch_pairs = arbitrage_pairs[i:i+batch_size]

                orderbooks = await fetch_orderbooks_for_symbols(batch_pairs, all_birgas, limit=20)

                # Обрабатываем каждого пользователя
                for uid, uset in user_settings.items():
                    # Проверяем, не отписался ли пользователь
                    with open('data/listeners.json', 'r') as f:
                        current_listeners = json.load(f)
                    if not any(l["user_id"] == uid for l in current_listeners):
                        continue

                    # Находим возможности для настроек пользователя
                    opps = await find_arbitrage_opportunities(orderbooks, uset["volume_min"], uset["volume_max"], uset["strategy"])

                    for opp in opps:
                        # Повторная проверка перед отправкой
                        with open('data/listeners.json', 'r') as f:
                            current_listeners = json.load(f)
                        if not any(l["user_id"] == uid for l in current_listeners):
                            break

                        msg = format_notification(
                            pair=opp["pair"],
                            buy_ob=opp["buy_ob"],
                            sell_ob=opp["sell_ob"],
                            buy_exchange=opp["buy_birga"].value,
                            sell_exchange=opp["sell_birga"].value,
                            volume=opp["volume"],
                            spread=opp["spread"],
                            net_profit=opp["net_profit"],
                            lifetime_hours=opp["lifetime_hours"],
                            lifetime_seconds=opp.get("lifetime_seconds"),
                            blockchain_info=opp.get("blockchain_info"),
                        )
                        try:
                            await asyncio.sleep(0)  # Yield to event loop for tg.send_message
                            tg.send_message(uset["chat_id"], msg, parse_mode="HTML", disable_web_page_preview=True)
                            await asyncio.sleep(0.5)
                        except Exception as e:
                            print(f"Ошибка отправки пользователю {uid}: {e}")

                # Пауза между батчами
                await asyncio.sleep(2)

            # Закрываем сессии
            await close_all_sessions()

            # Пауза между циклами
            await asyncio.sleep(60)

        except Exception as e:
            print(f"Ошибка arbitrage_loop: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(30)


def arbitrage_loop():
    asyncio.run(arbitrage_loop_async())


if __name__ == "__main__":
    th1 = threading.Thread(target=bot_listener, args=())
    th2 = threading.Thread(target=bot_counter, args=())
    th3 = threading.Thread(target=arbitrage_loop, args=())
    th1.start()
    th2.start()
    th3.start()
    th1.join()
    th2.join()
    th3.join()
