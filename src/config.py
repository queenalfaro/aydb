import os
from dotenv import load_dotenv

load_dotenv()

TG_MESSAGE_SHORTEN_LIMIT = int(os.getenv("TG_MESSAGE_SHORTEN_LIMIT", "0"))

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")

TG_PROXY_URL = os.getenv("TG_PROXY_URL", "")
