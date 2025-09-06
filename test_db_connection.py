#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к базе данных PostgreSQL.
Запустите этот скрипт для проверки корректности настроек БД.
"""

import sys
from config import Config
from database import DatabaseManager

def test_database_connection():
    """Тестирование подключения к базе данных PostgreSQL."""
    print("🔍 Проверка конфигурации...")
    
    if not Config.validate():
        print("❌ Ошибка конфигурации!")
        return False
    
    print("✅ Конфигурация корректна")
    
    print("🔌 Подключение к базе данных PostgreSQL...")
    db_manager = DatabaseManager(**Config.get_db_config())
    
    if not db_manager.connect():
        print("❌ Не удалось подключиться к базе данных!")
        return False
    
    print("✅ Подключение к базе данных успешно")
    
    # Проверяем доступные таблицы
    print("📋 Получение списка таблиц...")
    tables = db_manager.get_tables()
    
    if tables:
        print(f"✅ Найдено таблиц: {len(tables)}")
        for table in tables:
            print(f"  - {table}")
    else:
        print("⚠️  Таблицы не найдены")
    
    # Проверяем структуру таблицы users
    if 'users' in tables:
        print("🔍 Проверка структуры таблицы 'users'...")
        structure = db_manager.get_table_structure('users')
        if structure:
            print("✅ Структура таблицы 'users':")
            for column in structure:
                print(f"  - {column['Field']}: {column['Type']}")
        else:
            print("❌ Не удалось получить структуру таблицы 'users'")
    else:
        print("⚠️  Таблица 'users' не найдена. Создайте её с помощью database_schema.sql")
    
    db_manager.disconnect()
    print("🔌 Соединение с базой данных закрыто")
    return True

if __name__ == "__main__":
    print("🚀 Тестирование подключения к базе данных PostgreSQL\n")
    
    try:
        success = test_database_connection()
        if success:
            print("\n✅ Все тесты пройдены успешно!")
            sys.exit(0)
        else:
            print("\n❌ Тесты не пройдены!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Ошибка во время тестирования: {e}")
        sys.exit(1)
