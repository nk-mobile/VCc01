"""
Модуль для работы с базой данных PostgreSQL.
Обеспечивает подключение к удаленной БД и выполнение SQL-запросов.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import Error
from typing import List, Dict, Any, Optional
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Класс для управления подключением к базе данных и выполнения запросов."""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        """
        Инициализация менеджера базы данных PostgreSQL.
        
        Args:
            host: Хост базы данных
            port: Порт базы данных
            database: Название базы данных
            user: Имя пользователя
            password: Пароль
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
    
    def connect(self) -> bool:
        """
        Установка подключения к базе данных PostgreSQL.
        
        Returns:
            bool: True если подключение успешно, False в противном случае
        """
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.connection.autocommit = True
            logger.info(f"Успешное подключение к базе данных {self.database}")
            return True
        except Error as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            return False
    
    def disconnect(self):
        """Закрытие подключения к базе данных."""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("Подключение к базе данных закрыто")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Выполнение SELECT запроса.
        
        Args:
            query: SQL запрос
            params: Параметры для запроса
            
        Returns:
            List[Dict]: Список словарей с результатами запроса
        """
        if not self.connection or self.connection.closed:
            logger.error("Нет подключения к базе данных")
            return []
        
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in results]
        except Error as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            return []
    
    def execute_insert(self, query: str, params: Optional[tuple] = None) -> Optional[int]:
        """
        Выполнение INSERT запроса.
        
        Args:
            query: SQL запрос
            params: Параметры для запроса
            
        Returns:
            Optional[int]: ID вставленной записи или None при ошибке
        """
        if not self.connection or self.connection.closed:
            logger.error("Нет подключения к базе данных")
            return None
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            inserted_id = cursor.fetchone()[0] if cursor.description else None
            cursor.close()
            return inserted_id
        except Error as e:
            logger.error(f"Ошибка выполнения INSERT запроса: {e}")
            return None
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> bool:
        """
        Выполнение UPDATE запроса.
        
        Args:
            query: SQL запрос
            params: Параметры для запроса
            
        Returns:
            bool: True если запрос выполнен успешно
        """
        if not self.connection or self.connection.closed:
            logger.error("Нет подключения к базе данных")
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            cursor.close()
            return True
        except Error as e:
            logger.error(f"Ошибка выполнения UPDATE запроса: {e}")
            return False
    
    def get_tables(self) -> List[str]:
        """
        Получение списка таблиц в базе данных.
        
        Returns:
            List[str]: Список названий таблиц
        """
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """
        results = self.execute_query(query)
        return [row['table_name'] for row in results]
    
    def get_table_structure(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Получение структуры таблицы.
        
        Args:
            table_name: Название таблицы
            
        Returns:
            List[Dict]: Информация о колонках таблицы
        """
        query = """
        SELECT 
            column_name as "Field",
            data_type as "Type",
            is_nullable as "Null",
            column_default as "Default",
            character_maximum_length as "Length"
        FROM information_schema.columns 
        WHERE table_name = %s AND table_schema = 'public'
        ORDER BY ordinal_position
        """
        return self.execute_query(query, (table_name,))
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение пользователя по Telegram ID.
        
        Args:
            telegram_id: ID пользователя в Telegram
            
        Returns:
            Optional[Dict]: Данные пользователя или None
        """
        query = "SELECT * FROM users WHERE telegram_id = %s"
        results = self.execute_query(query, (telegram_id,))
        return results[0] if results else None
    
    def create_user(self, telegram_id: int, username: str = None, first_name: str = None, 
                   last_name: str = None) -> Optional[int]:
        """
        Создание нового пользователя.
        
        Args:
            telegram_id: ID пользователя в Telegram
            username: Имя пользователя в Telegram
            first_name: Имя
            last_name: Фамилия
            
        Returns:
            Optional[int]: ID созданного пользователя или None при ошибке
        """
        query = """
        INSERT INTO users (telegram_id, username, first_name, last_name, created_at)
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
        RETURNING id
        """
        return self.execute_insert(query, (telegram_id, username, first_name, last_name))
    
    def is_connected(self) -> bool:
        """
        Проверка состояния подключения.
        
        Returns:
            bool: True если подключение активно
        """
        return self.connection and not self.connection.closed
    
    def get_user_questionnaire(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение анкеты пользователя.
        
        Args:
            telegram_id: ID пользователя в Telegram
            
        Returns:
            Optional[Dict]: Данные анкеты или None
        """
        user = self.get_user_by_telegram_id(telegram_id)
        if not user:
            return None
        
        query = "SELECT * FROM questionnaires WHERE user_id = %s"
        results = self.execute_query(query, (user['id'],))
        return results[0] if results else None
    
    def create_questionnaire(self, telegram_id: int, data: str, status: str = 'draft') -> Optional[int]:
        """
        Создание новой анкеты пользователя.
        
        Args:
            telegram_id: ID пользователя в Telegram
            data: JSON данные анкеты (строка)
            status: Статус анкеты
            
        Returns:
            Optional[int]: ID созданной анкеты или None
        """
        user = self.get_user_by_telegram_id(telegram_id)
        if not user:
            return None
        
        query = """
        INSERT INTO questionnaires (user_id, data, status, created_at, updated_at)
        VALUES (%s, %s::jsonb, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING id
        """
        return self.execute_insert(query, (user['id'], data, status))
    
    def update_questionnaire(self, telegram_id: int, data: str, status: str = 'draft') -> bool:
        """
        Обновление анкеты пользователя.
        
        Args:
            telegram_id: ID пользователя в Telegram
            data: JSON данные анкеты (строка)
            status: Статус анкеты
            
        Returns:
            bool: True если обновление успешно
        """
        user = self.get_user_by_telegram_id(telegram_id)
        if not user:
            return False
        
        query = """
        UPDATE questionnaires 
        SET data = %s::jsonb, status = %s, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = %s
        """
        return self.execute_update(query, (data, status, user['id']))
    
    def get_all_questionnaires(self, status: str = None) -> List[Dict[str, Any]]:
        """
        Получение всех анкет.
        
        Args:
            status: Фильтр по статусу (опционально)
            
        Returns:
            List[Dict]: Список анкет
        """
        if status:
            query = """
            SELECT q.*, u.telegram_id, u.first_name, u.last_name, u.username
            FROM questionnaires q
            JOIN users u ON q.user_id = u.id
            WHERE q.status = %s
            ORDER BY q.created_at DESC
            """
            return self.execute_query(query, (status,))
        else:
            query = """
            SELECT q.*, u.telegram_id, u.first_name, u.last_name, u.username
            FROM questionnaires q
            JOIN users u ON q.user_id = u.id
            ORDER BY q.created_at DESC
            """
            return self.execute_query(query)
    
    def delete_questionnaire(self, telegram_id: int) -> bool:
        """
        Удаление анкеты пользователя.
        
        Args:
            telegram_id: ID пользователя в Telegram
            
        Returns:
            bool: True если удаление успешно
        """
        user = self.get_user_by_telegram_id(telegram_id)
        if not user:
            return False
        
        query = "DELETE FROM questionnaires WHERE user_id = %s"
        return self.execute_update(query, (user['id'],))
