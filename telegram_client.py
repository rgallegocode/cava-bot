import os
from datetime import datetime

import requests


def send_telegram(message: str) -> None:
    """Sends the final text to the configured Telegram chat.

    Deliberately not exposed as an agent tool: the demo Space is public and anyone could use it to send messages.
    """
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}

    response = requests.post(url, data=payload, timeout=30)
    if not response.ok:
        # Malformed Markdown makes Telegram reject the message: retry as plain text
        payload.pop("parse_mode")
        response = requests.post(url, data=payload, timeout=30)
    response.raise_for_status()
    print(f"[{datetime.now()}] Message sent to Telegram.")
