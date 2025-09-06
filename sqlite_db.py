"""
Модуль для работы с SQLite базой данных.
Содержит каталог модулей курса.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLiteManager:
    """Класс для управления SQLite базой данных с каталогом модулей."""
    
    def __init__(self, db_path: str = "catalog.db"):
        """
        Инициализация менеджера SQLite базы данных.
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.connection = None
        self._initialized = False
    
    def connect(self) -> bool:
        """
        Установка подключения к SQLite базе данных.
        
        Returns:
            bool: True если подключение успешно, False в противном случае
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
            logger.info(f"Успешное подключение к SQLite базе данных {self.db_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка подключения к SQLite базе данных: {e}")
            return False
    
    def disconnect(self):
        """Закрытие подключения к базе данных."""
        if self.connection:
            self.connection.close()
            logger.info("Подключение к SQLite базе данных закрыто")
    
    def _get_connection(self):
        """
        Получение нового подключения к базе данных.
        Создает новое подключение для каждого запроса для решения проблем с многопоточностью.
        
        Returns:
            sqlite3.Connection: Новое подключение к базе данных
        """
        try:
            connection = sqlite3.connect(self.db_path)
            connection.row_factory = sqlite3.Row
            return connection
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания подключения к SQLite: {e}")
            return None
    
    def create_tables(self) -> bool:
        """
        Создание таблиц в базе данных.
        
        Returns:
            bool: True если таблицы созданы успешно
        """
        if not self.connection:
            logger.error("Нет подключения к базе данных")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Создание таблицы catalog
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS catalog (
                    id INTEGER PRIMARY KEY,
                    description TEXT NOT NULL
                )
            """)
            
            self.connection.commit()
            cursor.close()
            logger.info("Таблицы созданы успешно")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания таблиц: {e}")
            return False
    
    def insert_catalog_data(self) -> bool:
        """
        Вставка данных каталога в таблицу.
        
        Returns:
            bool: True если данные вставлены успешно
        """
        if not self.connection:
            logger.error("Нет подключения к базе данных")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Данные каталога
            catalog_data = [
                (1, "VCc01.Работа с таблицам через API, использование таблиц в виде базы данных"),
                (2, "VCc02.Использование MCP серверов в Cursor"),
                (3, "VCc03.Что такое автономные агент, и как это работает. Пример с базовым парсингом сайта")
            ]
            
            # Очистка таблицы перед вставкой
            cursor.execute("DELETE FROM catalog")
            
            # Вставка данных
            cursor.executemany("""
                INSERT OR REPLACE INTO catalog (id, description) 
                VALUES (?, ?)
            """, catalog_data)
            
            self.connection.commit()
            cursor.close()
            logger.info("Данные каталога вставлены успешно")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка вставки данных каталога: {e}")
            return False
    
    def get_all_catalog_items(self) -> List[Dict[str, Any]]:
        """
        Получение всех элементов каталога.
        
        Returns:
            List[Dict]: Список словарей с данными каталога
        """
        connection = self._get_connection()
        if not connection:
            logger.error("Не удалось создать подключение к базе данных")
            return []
        
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT id, description FROM catalog ORDER BY id")
            results = cursor.fetchall()
            cursor.close()
            
            return [dict(row) for row in results]
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения данных каталога: {e}")
            return []
        finally:
            connection.close()
    
    def get_catalog_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение элемента каталога по ID.
        
        Args:
            item_id: ID элемента каталога
            
        Returns:
            Optional[Dict]: Данные элемента или None
        """
        connection = self._get_connection()
        if not connection:
            logger.error("Не удалось создать подключение к базе данных")
            return None
        
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT id, description FROM catalog WHERE id = ?", (item_id,))
            result = cursor.fetchone()
            cursor.close()
            
            return dict(result) if result else None
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения элемента каталога: {e}")
            return None
        finally:
            connection.close()
    
    def initialize_database(self) -> bool:
        """
        Инициализация базы данных (создание таблиц и вставка данных).
        
        Returns:
            bool: True если инициализация успешна
        """
        if self._initialized:
            return True
            
        if not self.connect():
            return False
        
        if not self.create_tables():
            return False
        
        if not self.insert_catalog_data():
            return False
        
        self._initialized = True
        logger.info("База данных SQLite инициализирована успешно")
        return True
    
    def is_connected(self) -> bool:
        """
        Проверка состояния подключения.
        
        Returns:
            bool: True если база данных инициализирована
        """
        return self._initialized
