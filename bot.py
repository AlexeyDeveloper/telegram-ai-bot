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
WEBHOOK_URL = "https://ваш-домен.ру/webhook"  # Обязательно HTTPS!
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get('PORT', 5000))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text("Привет! Я бот с AI-моделью. Задайте мне вопрос!")

def extract_message(response_data: Dict[str, Any]) -> Optional[str]:
    """Извлекает текстовое сообщение из ответа API"""
    try:
        # Основной путь к сообщению
        if outputs := response_data.get('outputs', []):
            if outputs[0].get('outputs'):
                if message := outputs[0]['outputs'][0].get('results', {}).get('message'):
                    if isinstance(message, str):
                        return message
                    return message.get('text') or message.get('data', {}).get('text')
        
        # Альтернативные пути поиска текста
        for path in [['artifacts', 'message'], ['messages', 0, 'message'], ['text']]:
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
        logger.error(f"Ошибка парсинга: {str(e)}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    try:
        response = requests.post(
            LANGFLOW_ENDPOINT,
            headers={"Content-Type": "application/json", "x-api-key": LANGFLOW_API_KEY},
            json={
                "input_value": update.message.text,
                "output_type": "chat",
                "input_type": "chat"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            if message := extract_message(response.json()):
                await update.message.reply_text(message)
            else:
                await update.message.reply_text("Не удалось обработать ответ AI")
        else:
            logger.error(f"API error: {response.status_code}")
            await update.message.reply_text("Ошибка сервера, попробуйте позже")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await update.message.reply_text("Внутренняя ошибка")

async def setup_webhook(app: Application):
    """Настройка webhook при запуске"""
    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.bot.set_webhook(
        url=WEBHOOK_URL,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )
    logger.info(f"Webhook настроен на {WEBHOOK_URL}")

def main():
    """Запуск приложения"""
    try:
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Регистрация обработчиков
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Настройка и запуск webhook
        app.run_webhook(
            listen=WEBAPP_HOST,
            port=WEBAPP_PORT,
            webhook_url=WEBHOOK_URL,
            secret_token=None,
            setup_webhook=setup_webhook
        )

    except Exception as e:
        logger.critical(f"Ошибка запуска: {str(e)}")
        raise

if __name__ == "__main__":
    main()