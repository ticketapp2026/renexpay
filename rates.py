import requests
import telebot
import schedule
import time
from datetime import datetime

BOT_TOKEN = "8806401975:AAEPH9b1zsUKjh4LYgiC92gw1lEjF7tUYXc"
CHANNEL_ID = "-1003388169563"
SPREAD = 0.30

bot = telebot.TeleBot(BOT_TOKEN)

def get_rates():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/RUB", timeout=10)
        d = r.json()
        usd = 1 / d["rates"]["USD"]
        eur = 1 / d["rates"]["EUR"]
        cny = 1 / d["rates"]["CNY"]
        aed = 1 / d["rates"]["AED"]
        rb = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=USDTRUB", timeout=10)
        bd = rb.json()
        usdt = float(bd["lastPrice"])
        return usd, eur, cny, aed, usdt
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

def post_rates():
    rates = get_rates()
    if not rates:
        return
    usd, eur, cny, aed, usdt = rates
    now = datetime.now().strftime("%H:%M")
    msg = f"""💱 *Курсы RenexPay* — {now}

🇺🇸 *USD / RUB*
  Мы купим у вас: `{usd - SPREAD:.2f} ₽`
  Мы продадим вам: `{usd + SPREAD:.2f} ₽`

🇪🇺 *EUR / RUB*
  Мы купим у вас: `{eur - SPREAD:.2f} ₽`
  Мы продадим вам: `{eur + SPREAD:.2f} ₽`

🇨🇳 *CNY / RUB*
  Мы купим у вас: `{cny - SPREAD:.4f} ₽`
  Мы продадим вам: `{cny + SPREAD:.4f} ₽`

🇦🇪 *AED / RUB*
  Мы купим у вас: `{aed - SPREAD:.2f} ₽`
  Мы продадим вам: `{aed + SPREAD:.2f} ₽`

💵 *USDT / RUB*
  Мы купим у вас: `{usdt - SPREAD:.2f} ₽`
  Мы продадим вам: `{usdt + SPREAD:.2f} ₽`

🕐 Следующее обновление через 30 минут
📱 @RenexPayBot"""

    bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
    print(f"✅ Курсы отправлены в {now}")

def run_scheduler():
    schedule.every(30).minutes.do(post_rates)
    post_rates()
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    print("✅ RenexPay курсы запущены...")
    run_scheduler()
