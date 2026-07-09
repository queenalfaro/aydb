
import logging

import requests

import config

logger = logging.getLogger(__name__)


def send_message(
    text: str,
    parse_mode: str = "HTML",
    bot_token: str = config.TG_BOT_TOKEN,
    chat_id: str = config.TG_CHAT_ID,
) -> bool:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }

    proxies = {
        "http": config.TG_PROXY_URL,
        "https": config.TG_PROXY_URL,
    } if config.TG_PROXY_URL else None

    logger.debug("Sending Telegram message (chat_id=%s, %d chars)",
                 chat_id, len(text))
    response = requests.post(url, json=payload, timeout=10, proxies=proxies)
    logger.debug("Telegram response status: %d", response.status_code)
    response.raise_for_status()
    logger.info("Message sent (chat_id=%s)", chat_id)
