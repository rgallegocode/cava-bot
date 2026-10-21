import os
from datetime import datetime

import requests


def send_telegram(message: str) -> None:
    """Envía el texto final al chat de Telegram configurado.

    No se expone como tool del agente: el Space es público y cualquiera podría usarlo para mandar mensajes.
    """
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}

    response = requests.post(url, data=payload, timeout=30)
    if not response.ok:
        # Un Markdown mal formado hace fallar el envío: se reintenta como texto plano
        payload.pop("parse_mode")
        response = requests.post(url, data=payload, timeout=30)
    response.raise_for_status()
    print(f"[{datetime.now()}] Mensaje enviado a Telegram con éxito.")
