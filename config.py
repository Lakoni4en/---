"""
⚙️ Конфигурация бота "Бесконечная гача"
"""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
_admin_id = os.getenv("ADMIN_ID", "0")
try:
    ADMIN_ID = int(_admin_id)
except ValueError:
    ADMIN_ID = 0

DATABASE_PATH = "gacha_bot.db"

# Ежедневные бесплатные тяги
DAILY_FREE_PULLS = 3

# Стартовые ресурсы
START_GOLD = 1000
START_STARS = 0

# Ежедневный бонус
DAILY_BONUS_GOLD = 200
DAILY_BONUS_STARS = 1

# Реферальная система
REFERRAL_BONUS_REFERRER_STARS = 10
REFERRAL_BONUS_REFERRER_GOLD = 500
REFERRAL_BONUS_REFEREE_STARS = 5
REFERRAL_BONUS_REFEREE_GOLD = 200
