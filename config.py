import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TG_BOT_TOKEN") or "11111111"

ADMIN_IDS = [
    123456789
]
