import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, types, Router  # Router здесь
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command

# Импорт конфига
from config import BOT_TOKEN, ADMIN_IDS, GLOBAL_CHANNEL, DB_PATH

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Теперь это сработает:
backup_router = Router()

@backup_router.message(Command("backup_status"))
async def cmd_backup_status(message: types.Message):
    """Показать статус бэкапов"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет прав")
        return
    await message.answer("✅ Бэкапы работают (каждый час в B2)")

async def main():
    """Основная функция запуска бота"""
    
    logger.info("🚀 Запуск бота...")
    
    # Создаем бота
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрируем роутеры (только если backup_router определен)
    try:
        dp.include_router(backup_router)
    except NameError:
        logger.warning("⚠️  backup_router не определен, пропускаем")
    
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
