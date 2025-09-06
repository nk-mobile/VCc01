#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к базе данных nk-mobile_db.
"""

import sys
import json
from config import Config
from database import DatabaseManager
from questionnaire import QuestionnaireManager, QuestionnaireData

def test_database_connection():
    """Тестирование подключения к базе данных."""
    print("🔍 Проверка конфигурации...")
    
    if not Config.validate():
        print("❌ Ошибка конфигурации!")
        return False
    
    print("✅ Конфигурация корректна")
    print(f"📊 Подключение к базе: {Config.DB_NAME} на {Config.DB_HOST}:{Config.DB_PORT}")
    
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
        print("⚠️  Таблица 'users' не найдена")
    
    # Проверяем структуру таблицы questionnaires
    if 'questionnaires' in tables:
        print("🔍 Проверка структуры таблицы 'questionnaires'...")
        structure = db_manager.get_table_structure('questionnaires')
        if structure:
            print("✅ Структура таблицы 'questionnaires':")
            for column in structure:
                print(f"  - {column['Field']}: {column['Type']}")
        else:
            print("❌ Не удалось получить структуру таблицы 'questionnaires'")
    else:
        print("⚠️  Таблица 'questionnaires' не найдена")
    
    db_manager.disconnect()
    print("🔌 Соединение с базой данных закрыто")
    return True

def test_questionnaire_save():
    """Тестирование сохранения анкеты."""
    print("\n🧪 Тестирование сохранения анкеты...")
    
    db_manager = DatabaseManager(**Config.get_db_config())
    if not db_manager.connect():
        print("❌ Не удалось подключиться к базе данных!")
        return False
    
    questionnaire_manager = QuestionnaireManager(db_manager)
    
    # Создаем тестовую анкету
    test_user_id = 890904904
  # Тестовый ID
    questionnaire = questionnaire_manager.start_questionnaire(test_user_id)
    
    if not questionnaire:
        print("❌ Не удалось создать анкету")
        return False
    
    # Заполняем тестовыми данными
    test_data = {
        'full_name': 'Тестов Тест Тестович',
        'age': 25,
        'phone': '+7 (999) 123-45-67',
        'email': 'test@example.com',
        'education': 'Высшее техническое',
        'work_experience': '3 года в IT',
        'skills': 'Python, JavaScript, SQL',
        'interests': 'Программирование, спорт',
        'goals': 'Развитие в области AI',
        'additional_info': 'Тестовая анкета'
    }
    
    print("📝 Заполнение тестовой анкеты...")
    for field, value in test_data.items():
        success = questionnaire_manager.update_questionnaire_field(test_user_id, field, value)
        if not success:
            print(f"❌ Ошибка заполнения поля {field}")
            return False
        print(f"✅ Поле {field} заполнено")
    
    # Проверяем прогресс
    progress = questionnaire_manager.get_questionnaire_progress(test_user_id)
    print(f"📊 Прогресс заполнения: {progress['percentage']}%")
    
    # Сохраняем анкету
    print("💾 Сохранение анкеты в базу данных...")
    if questionnaire_manager.save_questionnaire(test_user_id):
        print("✅ Анкета успешно сохранена!")
        
        # Проверяем, что анкета сохранилась
        saved_questionnaire = questionnaire_manager.get_user_questionnaire(test_user_id)
        if saved_questionnaire:
            print("✅ Анкета найдена в базе данных")
            print(f"📋 Статус: {saved_questionnaire.get('status', 'Неизвестно')}")
        else:
            print("❌ Анкета не найдена в базе данных")
            return False
    else:
        print("❌ Ошибка сохранения анкеты")
        return False
    
    db_manager.disconnect()
    return True

def main():
    """Основная функция тестирования."""
    print("🚀 Тестирование подключения к базе данных nk-mobile_db\n")
    
    try:
        # Тестируем подключение
        if not test_database_connection():
            return False
        
        # Тестируем сохранение анкеты
        if not test_questionnaire_save():
            return False
        
        print("\n✅ Все тесты пройдены успешно!")
        return True
        
    except Exception as e:
        print(f"\n💥 Ошибка во время тестирования: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 Тестирование завершено успешно!")
            sys.exit(0)
        else:
            print("\n❌ Тестирование не удалось!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)
