-- SQL скрипт для создания таблиц в PostgreSQL
-- Выполните этот скрипт в вашей базе данных

-- Создание таблицы пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для таблицы users
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Создание функции для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Создание триггера для автоматического обновления updated_at
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Пример таблицы для анкет (будет использоваться в будущем)
CREATE TABLE IF NOT EXISTS questionnaires (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    data JSONB,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'completed', 'reviewed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Создание индексов для таблицы questionnaires
CREATE INDEX IF NOT EXISTS idx_questionnaires_user_id ON questionnaires(user_id);
CREATE INDEX IF NOT EXISTS idx_questionnaires_status ON questionnaires(status);
CREATE INDEX IF NOT EXISTS idx_questionnaires_data ON questionnaires USING GIN(data);

-- Создание триггера для автоматического обновления updated_at в questionnaires
CREATE TRIGGER update_questionnaires_updated_at 
    BEFORE UPDATE ON questionnaires 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
