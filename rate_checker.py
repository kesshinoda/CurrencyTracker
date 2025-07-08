import warnings
warnings.filterwarnings(
    "ignore",
    message="python-telegram-bot is using upstream urllib3",
    category=UserWarning,
    module="telegram.utils.request"
)

import json
import os
import requests
from datetime import datetime, timezone
from telegram import Bot


TARGET_RATE_ABOVE = 150.0
TARGET_DIFF_FROM_YESTERDAY = 1.0
URL = "https://api.frankfurter.app/latest?from=USD&to=JPY"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HISTORY_FILE = "rate_history.py"

def get_usd_to_jpy() -> float | None:
    try:
        res = requests.get(URL)
        data = res.json()
        rate = data["rates"]["JPY"]
        return rate
    except Exception as e:
        print(f"Exception thrown while fetching rate: {e}")
        return None
    
def load_rate_history() -> dict:
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load rate history: {e}")
        return {}
    
def save_rate_history(history: dict) -> None:
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Failed to save rate history: {e}")

def get_yesterday_rate(history: dict) -> float | None:
    today = datetime.now(timezone.utc).date()
    dates = sorted(history.keys(), reverse=True)
    for date_str in dates:
        if date_str != today.isoformat():
            return history[date_str]
    return None

def check_rate() -> None:
    rate = get_usd_to_jpy()
    if rate is None:
        return
    
    print(f"Current USD/JPY: {rate:.2f}")
    history = load_rate_history()
    yesterday_rate = get_yesterday_rate(history)

    alert = False

    if rate >= TARGET_RATE_ABOVE:
        print(f"ALERT: USD/JPY is above {TARGET_RATE_ABOVE}! Consider transferring money.")
        alert = True

    if yesterday_rate is not None:
        diff = rate - yesterday_rate
        print(f"Yesterday's rate: {yesterday_rate:.2f}, Change: {diff:.2f}")
        if diff >= TARGET_DIFF_FROM_YESTERDAY:
            print(f"ALERT: Rate increased by {diff:.2f} since yesterday.")
            alert = True

    if alert:
        send_telegram_alert(rate)
    else:
        print("No alert conditions met. No action taken.")


    today_str = datetime.now(timezone.utc).date().isoformat()
    history[today_str] = rate
    save_rate_history(history)

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