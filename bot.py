import telebot
import sqlite3
import requests
from datetime import datetime

BOT_TOKEN = "8806401975:AAEPH9b1zsUKjh4LYgiC92gw1lEjF7tUYXc"
bot = telebot.TeleBot(BOT_TOKEN)
SPREAD = 0.30

def init_db():
    conn = sqlite3.connect("renexpay.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, telegram_id INTEGER UNIQUE, username TEXT, balance REAL DEFAULT 0.0, created_at TEXT)""")
    conn.commit()
    conn.close()

def get_or_create_user(telegram_id, username):
    conn = sqlite3.connect("renexpay.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (telegram_id, username, balance, created_at) VALUES (?, ?, 0.0, ?)", (telegram_id, username, datetime.now().isoformat()))
        conn.commit()
        c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        user = c.fetchone()
    conn.close()
    return user

def get_rates():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/RUB", timeout=10)
        d = r.json()
        usd = 1/d["rates"]["USD"]; eur = 1/d["rates"]["EUR"]; cny = 1/d["rates"]["CNY"]; aed = 1/d["rates"]["AED"]
        rb = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=USDTRUB", timeout=10)
        usdt = float(rb.json()["lastPrice"])
        return usd, eur, cny, aed, usdt
    except:
        return None

@bot.message_handler(commands=["start"])
def start(message):
    user = get_or_create_user(message.from_user.id, message.from_user.username)
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💳 Мои карты", "💰 Баланс")
    markup.row("➕ Пополнить", "💱 Курсы")
    markup.row("📋 История", "ℹ️ Помощь")
    bot.send_message(message.chat.id, f"👋 Добро пожаловать в RenexPay!\n\nБаланс: {user[3]:.2f} USDT\n\nВыбери действие:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "💰 Баланс")
def balance(message):
    user = get_or_create_user(message.from_user.id, message.from_user.username)
    bot.send_message(message.chat.id, f"💰 Твой баланс: *{user[3]:.2f} USDT*", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "➕ Пополнить")
def topup(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton("💲 Через USDT (TRC-20)", callback_data="topup_usdt"))
    markup.row(telebot.types.InlineKeyboardButton("🏦 Через СБП", callback_data="topup_sbp"))
    bot.send_message(message.chat.id, "➕ *Пополнение баланса*\n\nВыбери способ:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("topup_"))
def topup_callback(call):
    if call.data == "topup_usdt":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "💲 *Пополнение через USDT (TRC-20)*\n\nПереведи USDT на адрес:\n\n`ТВОЙ_USDT_АДРЕС`\n\nМинимум: 10 USDT", parse_mode="Markdown")
    elif call.data == "topup_sbp":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🏦 *Пополнение через СБП*\n\nПереведи рубли по номеру:\n\n`+7 (XXX) XXX-XX-XX`\n\nМинимум: 1000 ₽", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💱 Курсы")
@bot.message_handler(commands=["rates"])
def show_rates(message):
    bot.send_message(message.chat.id, "⏳ Загружаю курсы...")
    rates = get_rates()
    if not rates:
        bot.send_message(message.chat.id, "❌ Не удалось загрузить курсы.")
        return
    usd, eur, cny, aed, usdt = rates
    now = datetime.now().strftime("%H:%M")
    msg = f"💱 *Курсы RenexPay* — {now}\n\n🇺🇸 *USD/RUB*\n  Купим: `{usd-SPREAD:.2f} ₽` | Продадим: `{usd+SPREAD:.2f} ₽`\n\n🇪🇺 *EUR/RUB*\n  Купим: `{eur-SPREAD:.2f} ₽` | Продадим: `{eur+SPREAD:.2f} ₽`\n\n🇨🇳 *CNY/RUB*\n  Купим: `{cny-SPREAD:.4f} ₽` | Продадим: `{cny+SPREAD:.4f} ₽`\n\n🇦🇪 *AED/RUB*\n  Купим: `{aed-SPREAD:.2f} ₽` | Продадим: `{aed+SPREAD:.2f} ₽`\n\n💵 *USDT/RUB*\n  Купим: `{usdt-SPREAD:.2f} ₽` | Продадим: `{usdt+SPREAD:.2f} ₽`\n\n📢 @RenexPayRates"
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💳 Мои карты")
def my_cards(message):
    bot.send_message(message.chat.id, "💳 У тебя пока нет карт.\n\nВиртуальная карта — $10\nФизическая карта — $100 + доставка\n\nДля заказа: /order_card")

@bot.message_handler(func=lambda m: m.text == "ℹ️ Помощь")
def help_msg(message):
    bot.send_message(message.chat.id, "📌 *RenexPay*\n\n• Пополнение — USDT или СБП\n• Карта — /order_card\n• Курсы — /rates\n• Поддержка: @renexpay\\_support", parse_mode="Markdown")

@bot.message_handler(commands=["order_card"])
def order_card(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton("💳 Виртуальная — $10", callback_data="card_virtual"))
    markup.row(telebot.types.InlineKeyboardButton("💳 Физическая — $100", callback_data="card_physical"))
    markup.row(telebot.types.InlineKeyboardButton("❌ Отмена", callback_data="card_cancel"))
    bot.send_message(message.chat.id, "💳 *Заказ карты RenexPay*\n\n• Виртуальная — $10, выпуск 5 минут\n• Физическая — $100 + доставка 7-14 дней", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("card_"))
def card_callback(call):
    if call.data == "card_virtual":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "✅ *Оформляем виртуальную карту.*\n\nВведи имя латиницей:\n_Пример: IVAN IVANOV_", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, get_cardholder_name)
    elif call.data == "card_physical":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📦 *Физическая карта*\n\nСвяжись: @renexpay\\_support", parse_mode="Markdown")
    elif call.data == "card_cancel":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "❌ Заказ отменён.")

def get_cardholder_name(message):
    name = message.text.upper().strip()
    if len(name) < 3:
        bot.send_message(message.chat.id, "❌ Введи корректное имя.")
        return
    bot.send_message(message.chat.id, f"✅ *Карта оформляется!*\n\nИмя: *{name}*\nТип: Виртуальная Visa\nСтатус: 🔄 В обработке\n\nГотова через 5 минут.", parse_mode="Markdown")

if __name__ == "__main__":
    init_db()
    print("✅ RenexPay бот запущен...")
    bot.infinity_polling()
