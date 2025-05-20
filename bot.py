import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
LANGFLOW_API_KEY = os.getenv('LANGFLOW_API_KEY')
LANGFLOW_ENDPOINT = os.getenv('LANGFLOW_ENDPOINT')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я тестовый бот с AI-моделью.\n"
        "Просто напиши мне любой вопрос, и я постараюсь ответить!"
    )

def extract_message_from_response(response_data):
    """Извлекает текстовое сообщение из сложного JSON-ответа"""
    try:
        # Основной путь к сообщению в вашем JSON
        message = response_data['outputs'][0]['outputs'][0]['results']['message']['text']
        return message
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Ошибка при разборе ответа API: {str(e)}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    try:
        user_message = update.message.text
        logger.info(f"Получено сообщение от {update.effective_user.id}: {user_message}")
        
        # Отправка запроса к AI-модели
        response = requests.post(
            LANGFLOW_ENDPOINT,
            headers={
                "Content-Type": "application/json",
                "x-api-key": LANGFLOW_API_KEY
            },
            json={
                "input_value": user_message,
                "output_type": "chat",
                "input_type": "chat"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            response_data = response.json()
            ai_message = extract_message_from_response(response_data)
            
            if ai_message:
                await update.message.reply_text(ai_message)
            else:
                logger.error("Не удалось извлечь сообщение из ответа API")
                await update.message.reply_text("Получен неожиданный формат ответа от AI.")
        else:
            error_msg = f"Ошибка API (код {response.status_code}): {response.text}"
            logger.error(error_msg)
            await update.message.reply_text("Произошла ошибка при обработке запроса. Попробуйте позже.")
            
    except Exception as e:
        logger.error(f"Ошибка в handle_message: {str(e)}")
        await update.message.reply_text("Упс! Что-то пошло не так. Попробуйте еще раз.")

def main():
    """Запуск бота"""
    try:
        logger.info("Запуск бота...")
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Регистрируем обработчики
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Запускаем бота в режиме polling
        logger.info("Бот запущен в режиме polling")
        app.run_polling()
        
    except Exception as e:
        logger.critical(f"Ошибка при запуске бота: {str(e)}")

if __name__ == "__main__":
    main()