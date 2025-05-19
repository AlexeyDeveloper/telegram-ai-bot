import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
from typing import Optional, Dict, Any
import os

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_TOKEN = "7547401041:AAFa6kFA-nT8PpAuDwjqFAzIOYzrxmPXxgY"
LANGFLOW_API_KEY = "sk-ric-EXqYeklFtuOzW7TqJdXB39oOgzBLys92mpUwRcg"
LANGFLOW_ENDPOINT = "https://agents.kolbplus.de/api/v1/run/30d8502d-e8af-4a48-a095-8c8e59c20d6e?stream=false"
WEBHOOK_URL = "https://telegram-ai-bot-peh1.onrender.com/webhook"  # Замените на ваш HTTPS URL
WEBAPP_HOST = "0.0.0.0"  # Для Docker/Render оставьте 0.0.0.0
WEBAPP_PORT = int(os.environ.get('PORT', 5000))  # Порт для Render/Heroku

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я тестовый бот с AI-моделью.\n"
        "Просто напиши мне любой вопрос, и я постараюсь ответить!"
    )

def extract_message(response_data: Dict[str, Any]) -> Optional[str]:
    """Извлекает текстовое сообщение из ответа API"""
    try:
        # Основной путь к сообщению
        if 'outputs' in response_data and len(response_data['outputs']) > 0:
            first_output = response_data['outputs'][0]
            if 'outputs' in first_output and len(first_output['outputs']) > 0:
                message_data = first_output['outputs'][0]
                if 'results' in message_data and 'message' in message_data['results']:
                    message = message_data['results']['message']
                    if isinstance(message, str):
                        return message
                    elif isinstance(message, dict):
                        return message.get('text') or message.get('data', {}).get('text')
        
        # Альтернативные пути
        paths_to_check = [
            ['artifacts', 'message'],
            ['messages', 0, 'message'],
            ['text']
        ]
        
        for path in paths_to_check:
            try:
                result = response_data
                for key in path:
                    result = result[key]
                if isinstance(result, str):
                    return result
            except (KeyError, TypeError, IndexError):
                continue

        logger.warning(f"Неизвестный формат ответа: {response_data}")
        return None

    except Exception as e:
        logger.error(f"Ошибка при разборе ответа API: {str(e)}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    try:
        user_message = update.message.text
        logger.info(f"Получено сообщение от {update.effective_user.id}: {user_message}")
        
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
            ai_message = extract_message(response.json())
            await update.message.reply_text(ai_message or "Не удалось обработать ответ AI")
        else:
            logger.error(f"Ошибка API: {response.status_code} - {response.text}")
            await update.message.reply_text("Ошибка при обработке запроса")

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        await update.message.reply_text("Внутренняя ошибка сервера")

async def setup_webhook(app: Application):
    """Настройка webhook при запуске"""
    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.bot.set_webhook(
        url=WEBHOOK_URL,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )
    logger.info(f"Webhook установлен на {WEBHOOK_URL}")

def main():
    """Запуск бота в режиме webhook"""
    try:
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Регистрация обработчиков
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Настройка webhook при запуске
        app.run_webhook(
            listen=WEBAPP_HOST,
            port=WEBAPP_PORT,
            webhook_url=WEBHOOK_URL,
            setup_webhook=setup_webhook
        )
        
        logger.info("Бот запущен в режиме webhook")

    except Exception as e:
        logger.critical(f"Ошибка запуска: {str(e)}")
        raise

if __name__ == "__main__":
    main()