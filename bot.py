import asyncio
import logging
import threading
import time
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ==================== ПРОСТОЙ БЭКАП ====================
def simple_backup():
    """Простой бэкап раз в час"""
    import sqlite3
    import gzip
    from datetime import datetime
    
    while True:
        try:
            # Ждем час
            time.sleep(3600)
            
            # Проверяем есть ли ключи B2
            if not os.getenv('B2_KEY_ID') or not os.getenv('B2_APPLICATION_KEY'):
                logger.info("⚠️  Бэкапы отключены (нет ключей B2)")
                continue
            
            # Делаем бэкап
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f'backup_{timestamp}.db.gz'
            
            # Создаем сжатый бэкап
            with open('bot_database.db', 'rb') as f_in:
                with gzip.open(f'/tmp/{backup_name}', 'wb') as f_out:
                    f_out.write(f_in.read())
            
            # Загружаем в B2
            import boto3
            s3 = boto3.client(
                's3',
                endpoint_url='https://s3.us-east-005.backblazeb2.com',
                aws_access_key_id=os.getenv('B2_KEY_ID'),
                aws_secret_access_key=os.getenv('B2_APPLICATION_KEY')
            )
            
            s3.upload_file(
                Filename=f'/tmp/{backup_name}',
                Bucket=os.getenv('B2_BUCKET', 'referals-content'),
                Key=backup_name
            )
            
            logger.info(f"📦 Бэкап создан: {backup_name}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка бэкапа: {e}")
            time.sleep(300)  # ждем 5 минут при ошибке

# ==================== ОСНОВНОЙ БОТ ====================
async def main():
    """Основная функция запуска бота"""
    
    logger.info("🚀 Запуск бота...")
    
    # Проверка токена
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не установлен!")
        return
    
    # Создаем бота
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Инициализация базы данных
    try:
        from database import init_db
        await init_db()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        return
    
    # Импорт хендлеров
    try:
        from handlers import user, publisher, admin
        
        # Регистрация роутеров
        dp.include_router(admin.router)
        dp.include_router(publisher.router)
        dp.include_router(user.router)
        logger.info("✅ Хендлеры загружены")
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта хендлеров: {e}")
        return
    
    # Настройка команд бота
    try:
        await bot.set_my_commands([
            {"command": "start", "description": "Запустить бота"},
            {"command": "profile", "description": "Мой профиль"},
            {"command": "subscribe", "description": "Купить подписку"},
            {"command": "help", "description": "Помощь"},
            {"command": "status", "description": "Проверить статус"},
        ])
        logger.info("✅ Команды бота настроены")
    except Exception as e:
        logger.warning(f"⚠️  Не удалось настроить команды: {e}")
    
    # Получаем информацию о боте
    try:
        bot_info = await bot.get_me()
        logger.info(f"🤖 Бот @{bot_info.username} запущен")
    except Exception as e:
        logger.error(f"❌ Не удалось получить информацию о боте: {e}")
        return
    
    # Запускаем бэкап-сервис в фоне
    backup_thread = threading.Thread(target=simple_backup, daemon=True)
    backup_thread.start()
    logger.info("✅ Служба бэкапов запущена (раз в час)")
    
    # Запуск бота
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, drop_pending_updates=True)
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
    except Exception as e:
        logger.error(f"💥 Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

