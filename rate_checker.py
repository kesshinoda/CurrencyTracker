import warnings
warnings.filterwarnings(
    "ignore",
    message="python-telegram-bot is using upstream urllib3",
    category=UserWarning,
    module="telegram.utils.request"
)

import os
import requests
from telegram import Bot


TARGET_RATE = 150.0
URL = "https://api.frankfurter.app/latest?from=USD&to=JPY"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_usd_to_jpy() -> float | None:
    try:
        res = requests.get(URL)
        data = res.json()
        rate = data["rates"]["JPY"]
        return rate
    except Exception as e:
        print(f"Exception thrown while fetching rate: {e}")
        return None

def check_rate() -> None:
    rate = get_usd_to_jpy()
    if rate is None:
        return None
    print(f"Current USD/JPY: {rate:.2f}")

    if rate >= TARGET_RATE:
        print(f"ALERT: USD/JPY is above {TARGET_RATE}! Consider transferring money.")
        send_telegram_alert(rate)
    else:
        print("Rate not high enough yet. No action needed.")

def send_telegram_alert(rate) -> None:
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        msg = f"USD/JPY Alert: {rate:.2f} ¥/USD — consider transferring!"
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        print("📨 Telegram alert sent.")
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

if __name__ == "__main__":
    check_rate()