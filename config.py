import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TG_BOT_TOKEN")
ADMIN_IDS = [int(i) for i in os.getenv("ADMIN_ID", "").split(",") if i.strip()]

