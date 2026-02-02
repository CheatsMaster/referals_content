import asyncio
import logging
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Простой HTTP сервер для healthcheck
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Отключаем логирование

def start_health_server():
    server = HTTPServer(('0.0.0.0', 8080), HealthHandler)
    print("✅ Healthcheck сервер запущен на порту 8080")
    server.serve_forever()

# Запускаем health сервер
health_thread = threading.Thread(target=start_health_server, daemon=True)
health_thread.start()

# ==================== ОСНОВНОЙ КОД ====================

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

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
    
    # Запуск бота С drop_pending_updates
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, drop_pending_updates=True)  # ← ВАЖНО!
        logger.info("✅ Бот запущен с drop_pending_updates=True")
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
