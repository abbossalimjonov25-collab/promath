import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID")        # masalan: -1001234567890
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")  # masalan: @mening_kanalim
