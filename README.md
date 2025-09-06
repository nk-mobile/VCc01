# Телеграм-бот для сбора анкет
<img width="546" height="906" alt="Выделение_930" src="https://github.com/user-attachments/assets/4e33632e-6015-4dec-be3a-66954ff140c5" />

Телеграм-бот на PyTelegramBotAPI для сбора анкет пользователей с сохранением в удаленную базу данных PostgreSQL.

## Структура проекта

```
├── bot.py              # Основной файл бота с хендлерами
├── database.py         # Модуль для работы с PostgreSQL
├── sqlite_db.py        # Модуль для работы с SQLite каталогом
├── questionnaire.py    # Модуль для работы с анкетами
├── config.py           # Конфигурация и настройки
├── init_sqlite_db.py   # Скрипт инициализации SQLite БД
├── requirements.txt    # Зависимости Python
├── catalog.db          # SQLite база данных каталога
└── README.md          # Документация
```

## Установка и настройка

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта со следующими переменными:

```env
# Токен телеграм-бота (получить у @BotFather)
BOT_TOKEN=your_bot_token_here

# Настройки базы данных PostgreSQL (nk-mobile_db)
DB_HOST=your_database_host
DB_PORT=5432
DB_NAME=nk-mobile_db
DB_USER=your_database_user
DB_PASSWORD=your_database_password

# Уровень логирования (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

### 3. Структура базы данных

Бот подключается к базе данных **nk-mobile_db** и ожидает наличие следующих таблиц:

**Таблица users:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Таблица questionnaires:**
```sql
CREATE TABLE questionnaires (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    data JSONB,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'completed', 'reviewed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

Выполните скрипт `database_schema.sql` для создания всех необходимых таблиц и индексов.

## Запуск

```bash
python bot.py
```

## Функциональность

### Текущие возможности:
- ✅ Регистрация пользователей
- ✅ Основное меню с кнопками
- ✅ Просмотр профиля
- ✅ Подключение к удаленной PostgreSQL БД
- ✅ SQLite каталог модулей
- ✅ Просмотр содержания модулей
- ✅ **Полнофункциональная анкета пользователей**
- ✅ Валидация данных анкеты
- ✅ Сохранение анкет в PostgreSQL
- ✅ Редактирование и удаление анкет
- ✅ Модульная архитектура

### В разработке:
- 🔄 Админ панель
- 🔄 Экспорт данных
- 🔄 Статистика

## Архитектура

### Модули:

1. **bot.py** - Основной файл бота
   - Хендлеры команд и сообщений
   - Логика состояний пользователей
   - Интерфейс взаимодействия

2. **database.py** - Модуль работы с PostgreSQL
   - Подключение к PostgreSQL
   - CRUD операции
   - Получение структуры таблиц

3. **sqlite_db.py** - Модуль работы с SQLite каталогом
   - Управление каталогом модулей
   - CRUD операции для каталога
   - Автоматическая инициализация

4. **questionnaire.py** - Модуль работы с анкетами
   - Структура данных анкеты
   - Управление состоянием заполнения
   - Валидация данных
   - Сохранение в PostgreSQL

5. **config.py** - Конфигурация
   - Настройки подключения к БД
   - Токен бота
   - Валидация параметров

## API модуля database.py

### Основные методы:

- `connect()` - Подключение к БД
- `disconnect()` - Закрытие соединения
- `execute_query(query, params)` - SELECT запросы
- `execute_insert(query, params)` - INSERT запросы
- `execute_update(query, params)` - UPDATE запросы
- `get_tables()` - Получение списка таблиц
- `get_table_structure(table_name)` - Структура таблицы
- `get_user_by_telegram_id(telegram_id)` - Поиск пользователя
- `create_user(...)` - Создание пользователя

## API модуля sqlite_db.py

### Основные методы:
- `connect()` - Подключение к SQLite БД
- `disconnect()` - Закрытие соединения
- `initialize_database()` - Инициализация БД с данными
- `get_all_catalog_items()` - Получение всех элементов каталога
- `get_catalog_item_by_id(item_id)` - Поиск элемента по ID

## API модуля questionnaire.py

### Основные классы и методы:

**QuestionnaireData:**
- `to_dict()` - Преобразование в словарь
- `from_dict(data)` - Создание из словаря
- `is_complete()` - Проверка полноты
- `get_completion_percentage()` - Процент заполнения

**QuestionnaireManager:**
- `start_questionnaire(user_id)` - Начало заполнения
- `update_questionnaire_field(user_id, field, value)` - Обновление поля
- `save_questionnaire(user_id)` - Сохранение в БД
- `get_questionnaire_progress(user_id)` - Прогресс заполнения
- `cancel_questionnaire(user_id)` - Отмена заполнения

## Структура анкеты

Анкета содержит следующие поля:
- **Личная информация**: полное имя, возраст, телефон, email
- **Образование и опыт**: образование, опыт работы, навыки
- **Дополнительно**: интересы, цели, дополнительная информация

## Особенности PostgreSQL

- Использует `psycopg2-binary` для подключения
- Поддерживает JSONB для хранения данных анкет
- Автоматические триггеры для обновления `updated_at`
- GIN индексы для эффективного поиска по JSONB

## Особенности SQLite каталога

- Локальная база данных для каталога модулей
- Автоматическая инициализация при запуске бота
- Простая структура: id, description
- Быстрый доступ к данным каталога
- **Безопасная многопоточность**: каждое подключение создается для отдельного запроса
- Решение проблемы "SQLite objects created in a thread can only be used in that same thread"

## Инициализация SQLite каталога

Для инициализации каталога модулей выполните:

```bash
python init_sqlite_db.py
```

Это создаст файл `catalog.db` с таблицей `catalog` и заполнит её данными модулей.

## Тестирование подключения к базе данных

Для тестирования подключения к базе данных `nk-mobile_db` выполните:

```bash
python test_nk_mobile_db.py
```

Этот скрипт проверит:
- Подключение к PostgreSQL
- Структуру таблиц
- Сохранение тестовой анкеты
- Получение данных из базы

## Логирование

Бот ведет подробные логи всех операций:
- Подключение к БД
- Регистрация пользователей
- Ошибки выполнения
- Состояния пользователей

## Безопасность

- Все SQL запросы используют параметризованные запросы
- Пароли и токены хранятся в переменных окружения
- Валидация входных данных
- Обработка ошибок подключения к БД
