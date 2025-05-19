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

# Конфигурация (лучше вынести в переменные окружения)
TELEGRAM_TOKEN = "7547401041:AAFa6kFA-nT8PpAuDwjqFAzIOYzrxmPXxgY"
LANGFLOW_API_KEY = "sk-ric-EXqYeklFtuOzW7TqJdXB39oOgzBLys92mpUwRcg"
LANGFLOW_ENDPOINT = "https://agents.kolbplus.de/api/v1/run/30d8502d-e8af-4a48-a095-8c8e59c20d6e?stream=false"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я тестовый бот с AI-моделью.\n"
        "Просто напиши мне любой вопрос, и я постараюсь ответить!"
    )

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
            timeout=10  # Таймаут 10 секунд
        )
        
        if response.status_code == 200:
            ai_response = response.json()
            # Проверяем, что ответ содержит текст
            if isinstance(ai_response, str):
                reply_text = ai_response
            elif isinstance(ai_response, dict) and "text" in ai_response:
                reply_text = ai_response["text"]
            else:
                reply_text = str(ai_response)
            
            await update.message.reply_text(reply_text)
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