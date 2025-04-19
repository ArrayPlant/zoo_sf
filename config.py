import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Напиши BOT_TOKEN в .env")

ADMIN_ID = os.getenv("ADMIN_ID")
if not ADMIN_ID:
    raise RuntimeError("Напиши ADMIN_ID в .env")
ADMIN_ID = int(ADMIN_ID)

BOT_USERNAME = os.getenv("BOT_USERNAME")
if not BOT_USERNAME:
    raise RuntimeError("Укажите BOT_USERNAME в .env")
