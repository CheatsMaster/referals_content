#!/usr/bin/env python3
"""
Скрипт восстановления БД из Backblaze B2.
"""
import os
import sqlite3
import gzip
from datetime import datetime
import boto3
import argparse

def list_backups():
    """Показать список доступных бэкапов"""
    s3 = boto3.client(
        's3',
        endpoint_url='https://s3.us-west-002.backblazeb2.com',
        aws_access_key_id=os.getenv('B2_KEY_ID'),
        aws_secret_access_key=os.getenv('B2_APP_KEY')
    )
    
    response = s3.list_objects_v2(Bucket=os.getenv('B2_BUCKET', 'telegram-bot-backups'))
    
    if 'Contents' not in response:
        print("📭 Бэкапы не найдены")
        return []
    
    backups = []
    for obj in response['Contents']:
        backups.append({
            'name': obj['Key'],
            'size': obj['Size'],
            'last_modified': obj['LastModified']
        })
    
    # Сортируем по дате (новые первые)
    backups.sort(key=lambda x: x['last_modified'], reverse=True)
    
    print("\n📋 Доступные бэкапы:")
    for i, backup in enumerate(backups):
        print(f"{i+1:3d}. {backup['name']} ({backup['size']/1024:.1f} KB) - {backup['last_modified']}")
    
    return backups

def restore_backup(backup_name, output_path='bot_database_restored.db'):
    """Восстановить бэкап"""
    try:
        s3 = boto3.client(
            's3',
            endpoint_url='https://s3.us-west-002.backblazeb2.com',
            aws_access_key_id=os.getenv('B2_KEY_ID'),
            aws_secret_access_key=os.getenv('B2_APP_KEY')
        )
        
        # Скачиваем бэкап
        temp_path = f'/tmp/{backup_name}'
        s3.download_file(
            Bucket=os.getenv('B2_BUCKET', 'telegram-bot-backups'),
            Key=backup_name,
            Filename=temp_path
        )
        
        # Распаковываем
        with gzip.open(temp_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                f_out.write(f_in.read())
        
        # Удаляем временный файл
        os.remove(temp_path)
        
        print(f"✅ Бэкап восстановлен в: {output_path}")
        print(f"📏 Размер: {os.path.getsize(output_path)/1024:.1f} KB")
        
        # Проверяем БД
        try:
            conn = sqlite3.connect(output_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            
            print(f"📊 Таблиц в БД: {len(tables)}")
            if tables:
                print("   Таблицы:", ', '.join([t[0] for t in tables[:5]]))
                if len(tables) > 5:
                    print(f"   ... и еще {len(tables)-5} таблиц")
            
        except:
            print("⚠️  Не удалось проверить структуру БД")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка восстановления: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Восстановление БД из Backblaze B2')
    parser.add_argument('--list', action='store_true', help='Показать список бэкапов')
    parser.add_argument('--restore', type=str, help='Имя бэкапа для восстановления')
    parser.add_argument('--output', type=str, default='bot_database_restored.db', help='Выходной файл')
    parser.add_argument('--latest', action='store_true', help='Восстановить последний бэкап')
    
    args = parser.parse_args()
    
    # Проверяем переменные окружения
    if not os.getenv('B2_KEY_ID') or not os.getenv('B2_APP_KEY'):
        print("❌ Установите переменные окружения:")
        print("   export B2_KEY_ID=your_key_id")
        print("   export B2_APP_KEY=your_app_key")
        exit(1)
    
    if args.list:
        list_backups()
    
    elif args.latest:
        backups = list_backups()
        if backups:
            latest = backups[0]['name']
            print(f"\n🔄 Восстанавливаю последний бэкап: {latest}")
            restore_backup(latest, args.output)
    
    elif args.restore:
        print(f"\n🔄 Восстанавливаю бэкап: {args.restore}")
        restore_backup(args.restore, args.output)
    
    else:
        parser.print_help()
