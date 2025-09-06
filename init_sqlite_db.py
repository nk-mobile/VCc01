#!/usr/bin/env python3
"""
Скрипт для инициализации SQLite базы данных с каталогом модулей.
Запустите этот скрипт для создания базы данных и заполнения данными.
"""

import sys
from sqlite_db import SQLiteManager

def initialize_catalog_database():
    """Инициализация базы данных каталога."""
    print("🚀 Инициализация SQLite базы данных каталога\n")
    
    # Создаем менеджер базы данных
    db_manager = SQLiteManager("catalog.db")
    
    try:
        # Инициализируем базу данных
        if db_manager.initialize_database():
            print("✅ База данных создана и заполнена данными")
            
            # Проверяем данные
            print("\n📋 Проверка данных каталога:")
            items = db_manager.get_all_catalog_items()
            
            if items:Содержание модуля

                print(f"✅ Найдено записей: {len(items)}")
                for item in items:
                    print(f"  {item['id']}. {item['description']}")
            else:
                print("❌ Данные не найдены")
                return False
                
        else:
            print("❌ Ошибка инициализации базы данных")
            return False
            
    except Exception as e:
        print(f"💥 Ошибка во время инициализации: {e}")
        return False
    finally:
        db_manager.disconnect()
    
    print("\n✅ Инициализация завершена успешно!")
    return True

if __name__ == "__main__":
    try:
        success = initialize_catalog_database()
        if success:
            print("\n🎉 База данных готова к использованию!")
            sys.exit(0)
        else:
            print("\n❌ Инициализация не удалась!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)
