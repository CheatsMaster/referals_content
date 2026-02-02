#!/bin/bash

# Проверяем переменные B2
if [ -z "$B2_KEY_ID" ] || [ -z "$B2_APP_KEY" ]; then
    echo "⚠️  Переменные B2 не установлены. Бэкапы отключены."
    echo "ℹ️  Для включения бэкапов добавьте в Railway Variables:"
    echo "   - B2_KEY_ID"
    echo "   - B2_APP_KEY"
    echo "   - B2_BUCKET (опционально)"
    
    # Запускаем только бота без бэкапов
    python bot.py
else
    echo "✅ B2 настроен. Запускаю бота с бэкапами..."
    
    # Запускаем службу бэкапов в фоне
    python backup_to_b2.py &
    BACKUP_PID=$!
    
    # Ждем немного
    sleep 3
    
    # Запускаем основного бота
    python bot.py
    
    # Если бот упал, убиваем бэкап-сервис
    kill $BACKUP_PID 2>/dev/null
fi
