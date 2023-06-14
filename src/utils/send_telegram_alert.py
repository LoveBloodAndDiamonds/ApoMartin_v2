import os

import requests

from .logs_configure import logger


def send_telegram_alert(message: str) -> None:
    """Sends a message to a Telegram chat using a bot token and chat ID."""
    try:
        url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage"
        data = {"chat_id": os.getenv('ADMIN_TELEGRAM_ID'), "text": message, "parse_mode": "HTML"}
        response = requests.post(url, json=data)
        if response.status_code != 200:
            logger.error(f"Unable to send message: {response.text}")
    except Exception as error:
        logger.error(f"Unable to send message: {error}")
