import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Базовые настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в файле .env")

# ID администраторов (через запятую)
ADMIN_IDS = []
admin_ids_str = os.getenv("ADMIN_IDS", "")
if admin_ids_str:
    ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]

# Глобальный канал для обязательной подписки
GLOBAL_CHANNEL = os.getenv("GLOBAL_CHANNEL", "@your_channel")

# Тарифы (рубли → кредиты)
TARIFFS = {
    "basic": {"price": 100, "credits": 10},
    "standard": {"price": 250, "credits": 30},
    "premium": {"price": 500, "credits": 70}
}

# Настройки базы данных
DB_PATH = "bot_database.db"

# Настройки бота
BOT_USERNAME = None  # Будет установлен при запуске