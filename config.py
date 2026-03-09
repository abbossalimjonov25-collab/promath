import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@host/dbname")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))

# Test settings
QUESTIONS_PER_SESSION = 10       # Har sessiyada nechta savol
OPEN_QUESTION_COUNT = 3          # Ochiq savollar soni
MCQ_COUNT = 7                    # Test (A/B/C/D) soni
PASS_SCORE_PERCENT = 60          # O'tish bali (%)
