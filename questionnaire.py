"""
Модуль для управления анкетами пользователей.
Содержит структуру анкеты и логику заполнения.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class QuestionnaireData:
    """Структура данных анкеты пользователя."""
    
    # Личная информация
    full_name: str = ""
    age: int = 0
    phone: str = ""
    email: str = ""
    
    # Образование и опыт
    education: str = ""
    work_experience: str = ""
    skills: str = ""
    
    # Дополнительная информация
    interests: str = ""
    goals: str = ""
    additional_info: str = ""
    
    # Метаданные
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: str = "draft"  # draft, completed, reviewed
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сохранения в БД."""
        data = asdict(self)
        # Преобразуем datetime в строки для JSON
        if data['created_at']:
            data['created_at'] = data['created_at'].isoformat()
        if data['updated_at']:
            data['updated_at'] = data['updated_at'].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestionnaireData':
        """Создание объекта из словаря."""
        # Преобразуем строки обратно в datetime
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)
    
    def is_complete(self) -> bool:
        """Проверка полноты заполнения анкеты."""
        required_fields = [
            self.full_name,
            self.age,
            self.phone,
            self.email,
            self.education,
            self.work_experience
        ]
        return all(field for field in required_fields)
    
    def get_completion_percentage(self) -> int:
        """Получение процента заполнения анкеты."""
        all_fields = [
            self.full_name,
            self.age,
            self.phone,
            self.email,
            self.education,
            self.work_experience,
            self.skills,
            self.interests,
            self.goals,
            self.additional_info
        ]
        filled_fields = sum(1 for field in all_fields if field)
        return int((filled_fields / len(all_fields)) * 100)


class QuestionnaireManager:
    """Менеджер для работы с анкетами пользователей."""
    
    def __init__(self, db_manager):
        """
        Инициализация менеджера анкет.
        
        Args:
            db_manager: Менеджер базы данных PostgreSQL
        """
        self.db_manager = db_manager
        self.current_questionnaires: Dict[int, QuestionnaireData] = {}
    
    def start_questionnaire(self, user_id: int) -> QuestionnaireData:
        """
        Начало заполнения анкеты для пользователя.
        
        Args:
            user_id: ID пользователя в Telegram
            
        Returns:
            QuestionnaireData: Объект анкеты
        """
        questionnaire = QuestionnaireData()
        questionnaire.created_at = datetime.now()
        questionnaire.updated_at = datetime.now()
        
        self.current_questionnaires[user_id] = questionnaire
        logger.info(f"Начато заполнение анкеты для пользователя {user_id}")
        
        return questionnaire
    
    def get_current_questionnaire(self, user_id: int) -> Optional[QuestionnaireData]:
        """
        Получение текущей анкеты пользователя.
        
        Args:
            user_id: ID пользователя в Telegram
            
        Returns:
            Optional[QuestionnaireData]: Анкета пользователя или None
        """
        return self.current_questionnaires.get(user_id)
    
    def update_questionnaire_field(self, user_id: int, field: str, value: Any) -> bool:
        """
        Обновление поля анкеты.
        
        Args:
            user_id: ID пользователя в Telegram
            field: Название поля
            value: Значение поля
            
        Returns:
            bool: True если обновление успешно
        """
        questionnaire = self.get_current_questionnaire(user_id)
        if not questionnaire:
            return False
        
        if hasattr(questionnaire, field):
            setattr(questionnaire, field, value)
            questionnaire.updated_at = datetime.now()
            logger.info(f"Обновлено поле {field} для пользователя {user_id}")
            return True
        
        return False
    
    def save_questionnaire(self, user_id: int) -> bool:
        """
        Сохранение анкеты в базу данных.
        
        Args:
            user_id: ID пользователя в Telegram
            
        Returns:
            bool: True если сохранение успешно
        """
        questionnaire = self.get_current_questionnaire(user_id)
        if not questionnaire:
            return False
        
        # Получаем ID пользователя из PostgreSQL
        user = self.db_manager.get_user_by_telegram_id(user_id)
        if not user:
            logger.error(f"Пользователь {user_id} не найден в базе данных")
            return False
        
        # Проверяем, есть ли уже анкета у пользователя
        existing_questionnaire = self.get_user_questionnaire(user_id)
        
        questionnaire_data = questionnaire.to_dict()
        questionnaire_data['user_id'] = user['id']
        
        # Преобразуем в JSON строку для PostgreSQL
        import json
        json_data = json.dumps(questionnaire_data, ensure_ascii=False)
        
        if existing_questionnaire:
            # Обновляем существующую анкету
            success = self.db_manager.update_questionnaire(
                user_id, json_data, questionnaire.status
            )
        else:
            # Создаем новую анкету
            questionnaire_id = self.db_manager.create_questionnaire(
                user_id, json_data, questionnaire.status
            )
            success = questionnaire_id is not None
        
        if success:
            logger.info(f"Анкета пользователя {user_id} сохранена в базу данных")
            # Очищаем текущую анкету из памяти
            if user_id in self.current_questionnaires:
                del self.current_questionnaires[user_id]
        
        return success
    
    def get_user_questionnaire(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение анкеты пользователя из базы данных.
        
        Args:
            user_id: ID пользователя в Telegram
            
        Returns:
            Optional[Dict]: Данные анкеты или None
        """
        return self.db_manager.get_user_questionnaire(user_id)
    
    def cancel_questionnaire(self, user_id: int) -> bool:
        """
        Отмена заполнения анкеты.
        
        Args:
            user_id: ID пользователя в Telegram
            
        Returns:
            bool: True если отмена успешна
        """
        if user_id in self.current_questionnaires:
            del self.current_questionnaires[user_id]
            logger.info(f"Заполнение анкеты отменено для пользователя {user_id}")
            return True
        return False
    
    def get_questionnaire_progress(self, user_id: int) -> Dict[str, Any]:
        """
        Получение прогресса заполнения анкеты.
        
        Args:
            user_id: ID пользователя в Telegram
            
        Returns:
            Dict: Информация о прогрессе
        """
        questionnaire = self.get_current_questionnaire(user_id)
        if not questionnaire:
            return {"percentage": 0, "completed_fields": 0, "total_fields": 10}
        
        percentage = questionnaire.get_completion_percentage()
        completed_fields = sum(1 for field in [
            questionnaire.full_name,
            questionnaire.age,
            questionnaire.phone,
            questionnaire.email,
            questionnaire.education,
            questionnaire.work_experience,
            questionnaire.skills,
            questionnaire.interests,
            questionnaire.goals,
            questionnaire.additional_info
        ] if field)
        
        return {
            "percentage": percentage,
            "completed_fields": completed_fields,
            "total_fields": 10,
            "is_complete": questionnaire.is_complete()
        }
