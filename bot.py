"""
Основной файл телеграм-бота.
Содержит хендлеры и логику работы бота.
"""

import telebot
from telebot import types
import logging
from typing import Optional

from config import Config
from database import DatabaseManager
from sqlite_db import SQLiteManager
from questionnaire import QuestionnaireManager, QuestionnaireData

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = telebot.TeleBot(Config.BOT_TOKEN)

# Инициализация менеджера базы данных
db_manager = DatabaseManager(**Config.get_db_config())

# Инициализация SQLite менеджера для каталога
sqlite_manager = SQLiteManager("catalog.db")

# Инициализация менеджера анкет
questionnaire_manager = None


class UserState:
    """Класс для отслеживания состояния пользователей."""
    
    def __init__(self):
        self.states = {}
    
    def set_state(self, user_id: int, state: str):
        """Установка состояния пользователя."""
        self.states[user_id] = state
    
    def get_state(self, user_id: int) -> Optional[str]:
        """Получение состояния пользователя."""
        return self.states.get(user_id)
    
    def clear_state(self, user_id: int):
        """Очистка состояния пользователя."""
        if user_id in self.states:
            del self.states[user_id]
    
    def is_in_questionnaire(self, user_id: int) -> bool:
        """Проверка, заполняет ли пользователь анкету."""
        state = self.get_state(user_id)
        return state and state.startswith('questionnaire_')


# Глобальный объект для отслеживания состояний
user_states = UserState()


def ensure_user_exists(user_id: int, username: str = None, 
                      first_name: str = None, last_name: str = None) -> bool:
    """
    Проверка существования пользователя в базе данных и создание при необходимости.
    
    Args:
        user_id: ID пользователя в Telegram
        username: Имя пользователя в Telegram
        first_name: Имя
        last_name: Фамилия
        
    Returns:
        bool: True если пользователь существует или был создан
    """
    user = db_manager.get_user_by_telegram_id(user_id)
    if not user:
        user_id_db = db_manager.create_user(user_id, username, first_name, last_name)
        if user_id_db:
            logger.info(f"Создан новый пользователь: {user_id}")
            return True
        else:
            logger.error(f"Ошибка создания пользователя: {user_id}")
            return False
    return True


@bot.message_handler(commands=['start'])
def handle_start(message: types.Message):
    """Обработчик команды /start."""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Проверяем/создаем пользователя в базе данных
    if not ensure_user_exists(user_id, username, first_name, last_name):
        bot.reply_to(message, "Произошла ошибка при инициализации. Попробуйте позже.")
        return
    
    # Очищаем состояние пользователя
    user_states.clear_state(user_id)
    
    # Создаем клавиатуру
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("📚 Содержание модуля"))
    keyboard.add(types.KeyboardButton("📝 Заполнить анкету"))
    keyboard.add(types.KeyboardButton("ℹ️ Информация"))
    keyboard.add(types.KeyboardButton("🔧 Админ панель"))
    
    welcome_text = f"""
👋 Добро пожаловать, {first_name}!

Этот бот поможет вам заполнить анкету и сохранить данные.

Выберите действие:
"""
    
    bot.reply_to(message, welcome_text, reply_markup=keyboard)


@bot.message_handler(commands=['help'])
def handle_help(message: types.Message):
    """Обработчик команды /help."""
    help_text = """
📋 Доступные команды:

/start - Начать работу с ботом
/help - Показать эту справку
/profile - Просмотр профиля
/admin - Админ панель (только для администраторов)

🔧 Основные функции:
• Заполнение анкеты
• Просмотр информации
• Администрирование
"""
    bot.reply_to(message, help_text)


@bot.message_handler(commands=['profile'])
def handle_profile(message: types.Message):
    """Обработчик команды /profile."""
    user_id = message.from_user.id
    user = db_manager.get_user_by_telegram_id(user_id)
    
    if not user:
        bot.reply_to(message, "Пользователь не найден. Используйте /start для регистрации.")
        return
    
    profile_text = f"""
👤 Ваш профиль:

🆔 ID: {user.get('telegram_id', 'Не указан')}
👤 Имя: {user.get('first_name', 'Не указано')}
👤 Фамилия: {user.get('last_name', 'Не указано')}
📱 Username: @{user.get('username', 'Не указан')}
📅 Дата регистрации: {user.get('created_at', 'Не указана')}
"""
    
    bot.reply_to(message, profile_text)


@bot.message_handler(func=lambda message: message.text == "📚 Содержание модуля")
def handle_catalog(message: types.Message):
    """Обработчик кнопки 'Содержание модуля'."""
    user_id = message.from_user.id
    
    # Проверяем существование пользователя
    if not ensure_user_exists(user_id, message.from_user.username, 
                            message.from_user.first_name, message.from_user.last_name):
        bot.reply_to(message, "Произошла ошибка. Попробуйте позже.")
        return
    
    # Получаем данные каталога из SQLite
    catalog_items = sqlite_manager.get_all_catalog_items()
    
    if not catalog_items:
        catalog_text = """
📚 Содержание модуля

К сожалению, каталог модулей временно недоступен.
Попробуйте позже или обратитесь к администратору.
"""
    else:
        catalog_text = "📚 Содержание модуля\n\n"
        for item in catalog_items:
            catalog_text += f"• {item['description']}\n\n"
        
        catalog_text += "Выберите интересующий вас модуль для получения дополнительной информации."
    
    bot.reply_to(message, catalog_text)


@bot.message_handler(func=lambda message: message.text == "📝 Заполнить анкету")
def handle_questionnaire(message: types.Message):
    """Обработчик кнопки 'Заполнить анкету'."""
    user_id = message.from_user.id
    
    # Проверяем существование пользователя
    if not ensure_user_exists(user_id, message.from_user.username, 
                            message.from_user.first_name, message.from_user.last_name):
        bot.reply_to(message, "Произошла ошибка. Попробуйте позже.")
        return
    
    # Проверяем, есть ли уже анкета у пользователя
    existing_questionnaire = db_manager.get_user_questionnaire(user_id)
    
    if existing_questionnaire:
        # Показываем существующую анкету
        questionnaire_text = """
📝 Ваша анкета

У вас уже есть сохраненная анкета. Что вы хотите сделать?
"""
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("👁️ Просмотреть анкету"))
        keyboard.add(types.KeyboardButton("✏️ Редактировать анкету"))
        keyboard.add(types.KeyboardButton("🗑️ Удалить анкету"))
        keyboard.add(types.KeyboardButton("🔙 Назад в меню"))
        
        bot.reply_to(message, questionnaire_text, reply_markup=keyboard)
        user_states.set_state(user_id, "questionnaire_menu")
    else:
        # Начинаем заполнение новой анкеты
        questionnaire_manager.start_questionnaire(user_id)
        
        questionnaire_text = """
📝 Заполнение анкеты

Добро пожаловать! Давайте заполним вашу анкету.

Начнем с личной информации. Введите ваше полное имя (Фамилия Имя Отчество):
"""
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("❌ Отменить заполнение"))
        
        bot.reply_to(message, questionnaire_text, reply_markup=keyboard)
        user_states.set_state(user_id, "questionnaire_full_name")


@bot.message_handler(func=lambda message: message.text == "ℹ️ Информация")
def handle_info(message: types.Message):
    """Обработчик кнопки 'Информация'."""
    info_text = """
ℹ️ Информация о боте

🤖 Этот бот предназначен для сбора анкет пользователей.

📊 Возможности:
• Регистрация пользователей
• Заполнение анкет
• Сохранение данных в базу
• Администрирование

🔒 Ваши данные защищены и используются только в указанных целях.

❓ По вопросам обращайтесь к администратору.
"""
    
    bot.reply_to(message, info_text)


@bot.message_handler(func=lambda message: message.text == "🔧 Админ панель")
def handle_admin(message: types.Message):
    """Обработчик кнопки 'Админ панель'."""
    user_id = message.from_user.id
    
    # TODO: Здесь будет проверка прав администратора
    # Пока что показываем заглушку
    admin_text = """
🔧 Админ панель

Функции администратора находятся в разработке.

Доступные функции (в разработке):
• Просмотр статистики
• Управление пользователями
• Экспорт данных
• Настройки бота
"""
    
    bot.reply_to(message, admin_text)


@bot.message_handler(func=lambda message: message.text == "❌ Отменить заполнение")
def handle_cancel_questionnaire(message: types.Message):
    """Обработчик отмены заполнения анкеты."""
    user_id = message.from_user.id
    
    # Отменяем заполнение анкеты
    questionnaire_manager.cancel_questionnaire(user_id)
    user_states.clear_state(user_id)
    
    # Возвращаемся в главное меню
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("📚 Содержание модуля"))
    keyboard.add(types.KeyboardButton("📝 Заполнить анкету"))
    keyboard.add(types.KeyboardButton("ℹ️ Информация"))
    keyboard.add(types.KeyboardButton("🔧 Админ панель"))
    
    bot.reply_to(message, "❌ Заполнение анкеты отменено.\n🏠 Главное меню", reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == "💾 Сохранить анкету")
def handle_save_questionnaire(message: types.Message):
    """Обработчик сохранения анкеты."""
    user_id = message.from_user.id
    
    # Сохраняем анкету в базу данных
    if questionnaire_manager.save_questionnaire(user_id):
        bot.reply_to(message, "✅ Анкета успешно сохранена!")
    else:
        bot.reply_to(message, "❌ Ошибка при сохранении анкеты. Попробуйте позже.")
    
    # Возвращаемся в главное меню
    user_states.clear_state(user_id)
    handle_back_to_menu(message)


@bot.message_handler(func=lambda message: message.text == "❌ Отменить")
def handle_cancel_questionnaire_review(message: types.Message):
    """Обработчик отмены на этапе просмотра анкеты."""
    user_id = message.from_user.id
    
    # Отменяем заполнение анкеты
    questionnaire_manager.cancel_questionnaire(user_id)
    user_states.clear_state(user_id)
    
    # Возвращаемся в главное меню
    handle_back_to_menu(message)


@bot.message_handler(func=lambda message: message.text == "🔙 Назад в меню")
def handle_back_to_menu(message: types.Message):
    """Обработчик кнопки 'Назад в меню'."""
    user_id = message.from_user.id
    user_states.clear_state(user_id)
    
    # Создаем основную клавиатуру
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("📚 Содержание модуля"))
    keyboard.add(types.KeyboardButton("📝 Заполнить анкету"))
    keyboard.add(types.KeyboardButton("ℹ️ Информация"))
    keyboard.add(types.KeyboardButton("🔧 Админ панель"))
    
    bot.reply_to(message, "🏠 Главное меню", reply_markup=keyboard)


@bot.message_handler(func=lambda message: True)
def handle_other_messages(message: types.Message):
    """Обработчик всех остальных сообщений."""
    user_id = message.from_user.id
    current_state = user_states.get_state(user_id)
    
    if current_state == "questionnaire_full_name":
        handle_questionnaire_full_name(message)
    elif current_state == "questionnaire_age":
        handle_questionnaire_age(message)
    elif current_state == "questionnaire_phone":
        handle_questionnaire_phone(message)
    elif current_state == "questionnaire_email":
        handle_questionnaire_email(message)
    elif current_state == "questionnaire_education":
        handle_questionnaire_education(message)
    elif current_state == "questionnaire_work_experience":
        handle_questionnaire_work_experience(message)
    elif current_state == "questionnaire_skills":
        handle_questionnaire_skills(message)
    elif current_state == "questionnaire_interests":
        handle_questionnaire_interests(message)
    elif current_state == "questionnaire_goals":
        handle_questionnaire_goals(message)
    elif current_state == "questionnaire_additional_info":
        handle_questionnaire_additional_info(message)
    elif current_state == "questionnaire_menu":
        handle_questionnaire_menu(message)
    else:
        # Неизвестное сообщение
        bot.reply_to(message, "Не понимаю эту команду. Используйте /help для справки.")


def handle_questionnaire_full_name(message: types.Message):
    """Обработка ввода полного имени."""
    user_id = message.from_user.id
    full_name = message.text.strip()
    
    if len(full_name) < 2:
        bot.reply_to(message, "❌ Имя слишком короткое. Введите полное имя:")
        return
    
    questionnaire_manager.update_questionnaire_field(user_id, 'full_name', full_name)
    
    bot.reply_to(message, f"✅ Имя сохранено: {full_name}\n\nВведите ваш возраст:")
    user_states.set_state(user_id, "questionnaire_age")


def handle_questionnaire_age(message: types.Message):
    """Обработка ввода возраста."""
    user_id = message.from_user.id
    age_text = message.text.strip()
    
    try:
        age = int(age_text)
        if age < 1 or age > 120:
            bot.reply_to(message, "❌ Возраст должен быть от 1 до 120 лет. Введите корректный возраст:")
            return
    except ValueError:
        bot.reply_to(message, "❌ Введите корректный возраст (число):")
        return
    
    questionnaire_manager.update_questionnaire_field(user_id, 'age', age)
    
    bot.reply_to(message, f"✅ Возраст сохранен: {age} лет\n\nВведите ваш номер телефона:")
    user_states.set_state(user_id, "questionnaire_phone")


def handle_questionnaire_phone(message: types.Message):
    """Обработка ввода телефона."""
    user_id = message.from_user.id
    phone = message.text.strip()
    
    # Простая валидация телефона
    if len(phone) < 10:
        bot.reply_to(message, "❌ Номер телефона слишком короткий. Введите корректный номер:")
        return
    
    questionnaire_manager.update_questionnaire_field(user_id, 'phone', phone)
    
    bot.reply_to(message, f"✅ Телефон сохранен: {phone}\n\nВведите ваш email:")
    user_states.set_state(user_id, "questionnaire_email")


def handle_questionnaire_email(message: types.Message):
    """Обработка ввода email."""
    user_id = message.from_user.id
    email = message.text.strip()
    
    # Простая валидация email
    if '@' not in email or '.' not in email:
        bot.reply_to(message, "❌ Введите корректный email адрес:")
        return
    
    questionnaire_manager.update_questionnaire_field(user_id, 'email', email)
    
    bot.reply_to(message, f"✅ Email сохранен: {email}\n\nВведите ваше образование:")
    user_states.set_state(user_id, "questionnaire_education")


def handle_questionnaire_education(message: types.Message):
    """Обработка ввода образования."""
    user_id = message.from_user.id
    education = message.text.strip()
    
    questionnaire_manager.update_questionnaire_field(user_id, 'education', education)
    
    bot.reply_to(message, f"✅ Образование сохранено\n\nОпишите ваш опыт работы:")
    user_states.set_state(user_id, "questionnaire_work_experience")


def handle_questionnaire_work_experience(message: types.Message):
    """Обработка ввода опыта работы."""
    user_id = message.from_user.id
    work_experience = message.text.strip()
    
    questionnaire_manager.update_questionnaire_field(user_id, 'work_experience', work_experience)
    
    bot.reply_to(message, f"✅ Опыт работы сохранен\n\nОпишите ваши навыки:")
    user_states.set_state(user_id, "questionnaire_skills")


def handle_questionnaire_skills(message: types.Message):
    """Обработка ввода навыков."""
    user_id = message.from_user.id
    skills = message.text.strip()
    
    questionnaire_manager.update_questionnaire_field(user_id, 'skills', skills)
    
    bot.reply_to(message, f"✅ Навыки сохранены\n\nОпишите ваши интересы:")
    user_states.set_state(user_id, "questionnaire_interests")


def handle_questionnaire_interests(message: types.Message):
    """Обработка ввода интересов."""
    user_id = message.from_user.id
    interests = message.text.strip()
    
    questionnaire_manager.update_questionnaire_field(user_id, 'interests', interests)
    
    bot.reply_to(message, f"✅ Интересы сохранены\n\nОпишите ваши цели:")
    user_states.set_state(user_id, "questionnaire_goals")


def handle_questionnaire_goals(message: types.Message):
    """Обработка ввода целей."""
    user_id = message.from_user.id
    goals = message.text.strip()
    
    questionnaire_manager.update_questionnaire_field(user_id, 'goals', goals)
    
    bot.reply_to(message, f"✅ Цели сохранены\n\nДополнительная информация (необязательно):")
    user_states.set_state(user_id, "questionnaire_additional_info")


def handle_questionnaire_additional_info(message: types.Message):
    """Обработка ввода дополнительной информации."""
    user_id = message.from_user.id
    additional_info = message.text.strip()
    
    questionnaire_manager.update_questionnaire_field(user_id, 'additional_info', additional_info)
    
    # Показываем прогресс и предлагаем сохранить
    progress = questionnaire_manager.get_questionnaire_progress(user_id)
    
    progress_text = f"""
✅ Дополнительная информация сохранена

📊 Прогресс заполнения: {progress['percentage']}%
Заполнено полей: {progress['completed_fields']}/{progress['total_fields']}

Анкета готова к сохранению!
"""
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("💾 Сохранить анкету"))
    keyboard.add(types.KeyboardButton("✏️ Редактировать"))
    keyboard.add(types.KeyboardButton("❌ Отменить"))
    
    bot.reply_to(message, progress_text, reply_markup=keyboard)
    user_states.set_state(user_id, "questionnaire_review")


def handle_questionnaire_menu(message: types.Message):
    """Обработка меню анкеты."""
    user_id = message.from_user.id
    text = message.text
    
    if text == "👁️ Просмотреть анкету":
        show_questionnaire(message)
    elif text == "✏️ Редактировать анкету":
        start_edit_questionnaire(message)
    elif text == "🗑️ Удалить анкету":
        delete_questionnaire(message)
    else:
        bot.reply_to(message, "Выберите действие из меню.")


def show_questionnaire(message: types.Message):
    """Показ анкеты пользователя."""
    user_id = message.from_user.id
    questionnaire_data = db_manager.get_user_questionnaire(user_id)
    
    if not questionnaire_data:
        bot.reply_to(message, "❌ Анкета не найдена.")
        return
    
    # Парсим JSON данные анкеты
    import json
    try:
        data = json.loads(questionnaire_data['data']) if isinstance(questionnaire_data['data'], str) else questionnaire_data['data']
        
        questionnaire_text = f"""
📋 Ваша анкета

👤 Личная информация:
• Имя: {data.get('full_name', 'Не указано')}
• Возраст: {data.get('age', 'Не указан')}
• Телефон: {data.get('phone', 'Не указан')}
• Email: {data.get('email', 'Не указан')}

🎓 Образование и опыт:
• Образование: {data.get('education', 'Не указано')}
• Опыт работы: {data.get('work_experience', 'Не указан')}
• Навыки: {data.get('skills', 'Не указаны')}

🎯 Дополнительно:
• Интересы: {data.get('interests', 'Не указаны')}
• Цели: {data.get('goals', 'Не указаны')}
• Доп. информация: {data.get('additional_info', 'Не указана')}

📊 Статус: {questionnaire_data.get('status', 'Неизвестно')}
📅 Создана: {questionnaire_data.get('created_at', 'Неизвестно')}
🔄 Обновлена: {questionnaire_data.get('updated_at', 'Неизвестно')}
"""
    except (json.JSONDecodeError, KeyError) as e:
        questionnaire_text = f"""
📋 Ваша анкета

Статус: {questionnaire_data.get('status', 'Неизвестно')}
Создана: {questionnaire_data.get('created_at', 'Неизвестно')}
Обновлена: {questionnaire_data.get('updated_at', 'Неизвестно')}

⚠️ Ошибка при чтении данных анкеты.
"""
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("✏️ Редактировать анкету"))
    keyboard.add(types.KeyboardButton("🗑️ Удалить анкету"))
    keyboard.add(types.KeyboardButton("🔙 Назад в меню"))
    
    bot.reply_to(message, questionnaire_text, reply_markup=keyboard)


def start_edit_questionnaire(message: types.Message):
    """Начало редактирования анкеты."""
    user_id = message.from_user.id
    
    # Загружаем существующую анкету
    existing_questionnaire = db_manager.get_user_questionnaire(user_id)
    if existing_questionnaire:
        # Здесь можно загрузить данные в текущую анкету
        questionnaire_manager.start_questionnaire(user_id)
        
        bot.reply_to(message, "✏️ Редактирование анкеты\n\nВведите ваше полное имя:")
        user_states.set_state(user_id, "questionnaire_full_name")
    else:
        bot.reply_to(message, "❌ Анкета не найдена.")


def delete_questionnaire(message: types.Message):
    """Удаление анкеты."""
    user_id = message.from_user.id
    
    if questionnaire_manager.db_manager.delete_questionnaire(user_id):
        bot.reply_to(message, "✅ Анкета удалена.")
    else:
        bot.reply_to(message, "❌ Ошибка при удалении анкеты.")
    
    # Возвращаемся в главное меню
    handle_back_to_menu(message)


def main():
    """Основная функция запуска бота."""
    # Проверяем конфигурацию
    if not Config.validate():
        logger.error("Ошибка конфигурации. Проверьте переменные окружения.")
        return
    
    # Подключаемся к базе данных
    if not db_manager.connect():
        logger.error("Не удалось подключиться к базе данных.")
        return
    
    # Инициализируем SQLite базу данных каталога
    if not sqlite_manager.initialize_database():
        logger.error("Не удалось инициализировать SQLite базу данных каталога.")
        return
    
    # Инициализируем менеджер анкет
    global questionnaire_manager
    questionnaire_manager = QuestionnaireManager(db_manager)
    logger.info("Менеджер анкет инициализирован")
    
    try:
        logger.info("Запуск телеграм-бота...")
        bot.polling(none_stop=True, interval=0, timeout=20)
    except KeyboardInterrupt:
        logger.info("Остановка бота...")
    except Exception as e:
        logger.error(f"Ошибка в работе бота: {e}")
    finally:
        db_manager.disconnect()
        sqlite_manager.disconnect()


if __name__ == "__main__":
    main()
