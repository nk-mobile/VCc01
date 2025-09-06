"""
Файл конфигурации для телеграм-бота.
Содержит все настройки подключения к базе данных и токен бота.
"""

import os
from typing import Optional
from dotenv import load_dotenv


load_dotenv()


class Config:
    """Класс конфигурации для бота и базы данных."""
    
    # Настройки Telegram бота
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    
    # Настройки базы данных PostgreSQL
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    DB_NAME: str = os.getenv('DB_NAME', 'nk-mobile_db')
    DB_USER: str = os.getenv('DB_USER', '')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    
    # Настройки логирования
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls) -> bool:
        """
        Проверка корректности конфигурации.
        
        Returns:
            bool: True если все обязательные параметры заданы
        """
        required_params = [
            cls.BOT_TOKEN,
            cls.DB_NAME,
            cls.DB_USER,
            cls.DB_PASSWORD
        ]
        
        missing_params = [param for param in required_params if not param]
        
        if missing_params:
            print("Ошибка: Не заданы следующие обязательные параметры:")
            if not cls.BOT_TOKEN:
                print("- BOT_TOKEN")
            if not cls.DB_NAME:
                print("- DB_NAME")
            if not cls.DB_USER:
                print("- DB_USER")
            if not cls.DB_PASSWORD:
                print("- DB_PASSWORD")
            return False
        
        return True
    
    @classmethod
    def get_db_config(cls) -> dict:
        """
        Получение конфигурации для подключения к базе данных.
        
        Returns:
            dict: Словарь с параметрами подключения
        """
        return {
            'host': cls.DB_HOST,
            'port': cls.DB_PORT,
            'database': cls.DB_NAME,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD
        }
