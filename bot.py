import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import os
from dotenv import load_dotenv
from config import BOT_TOKEN

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска бота"""
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Инициализация базы данных
    from database import init_db
    await init_db()
    logger.info("База данных инициализирована")
    
    # Импорт хендлеров
    from handlers import user, publisher, admin
    
    # Регистрация роутеров
    dp.include_router(admin.router)
    dp.include_router(publisher.router)
    dp.include_router(user.router)
    
    # Настройка команд бота
    await bot.set_my_commands([
        {"command": "start", "description": "Запустить бота"},
        {"command": "profile", "description": "Мой профиль"},
        {"command": "subscribe", "description": "Купить подписку"},
        {"command": "help", "description": "Помощь"},
        {"command": "status", "description": "Проверить статус"},
        {"command": "check_channel", "description": "Проверить канал"},
    ])
    
    bot_info = await bot.get_me()
    logger.info(f"Бот @{bot_info.username} запускается...")
    
    # Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:

        logger.error(f"Ошибка при запуске бота: {e}")

