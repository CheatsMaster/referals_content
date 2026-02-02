import asyncio
import logging
import sys

# Импорт aiogram
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Импорт конфига
from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска бота"""
    
    # ==================== HEALTHCHECK СЕРВЕР ====================
    from aiohttp import web
    
    async def health_handler(request):
        return web.Response(text='OK')
    
    async def start_health_server():
        app = web.Application()
        app.router.add_get('/health', health_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        logger.info("✅ Healthcheck сервер запущен на порту 8080")
        # Бесконечный цикл
        while True:
            await asyncio.sleep(3600)
    
    # Запускаем health сервер
    health_task = asyncio.create_task(start_health_server())
    
    # ==================== ОСНОВНОЙ КОД БОТА ====================
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
            {"command": "check_channel", "description": "Проверить канал"},
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
    
    # Запуск бота
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
    except Exception as e:
        logger.error(f"💥 Ошибка при запуске бота: {e}")
    finally:
        # Отменяем health task
        health_task.cancel()
        try:
            await health_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
