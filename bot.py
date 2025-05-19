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
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '7547401041:AAFa6kFA-nT8PpAuDwjqFAzIOYzrxmPXxgY')
LANGFLOW_API_KEY = os.getenv('LANGFLOW_API_KEY', 'sk-ric-EXqYeklFtuOzW7TqJdXB39oOgzBLys92mpUwRcg')
LANGFLOW_ENDPOINT = "https://agents.kolbplus.de/api/v1/run/30d8502d-e8af-4a48-a095-8c8e59c20d6e?stream=false"
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://telegram-ai-bot-peh1.onrender.com/webhook')
PORT = int(os.getenv('PORT', 5000))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот с AI-моделью. Задайте вопрос.")

def extract_message(response_data: dict) -> str:
    """Упрощенный парсер ответа API"""
    try:
        # Основной путь к сообщению
        message = (response_data.get('outputs', [{}])[0]
                  .get('outputs', [{}])[0]
                  .get('results', {})
                  .get('message', {}))
        
        if isinstance(message, str):
            return message
        return message.get('text', 'Не удалось обработать ответ')
    except Exception as e:
        logger.error(f"Ошибка парсинга: {e}")
        return "Ошибка обработки ответа"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.post(
            LANGFLOW_ENDPOINT,
            headers={
                "Content-Type": "application/json",
                "x-api-key": LANGFLOW_API_KEY
            },
            json={
                "input_value": update.message.text,
                "output_type": "chat",
                "input_type": "chat"
            },
            timeout=10
        )
        await update.message.reply_text(extract_message(response.json()))
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("Произошла ошибка, попробуйте позже")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Удаляем старый webhook перед запуском
    app.bot.delete_webhook(drop_pending_updates=True)
    
    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Устанавливаем новый webhook
    app.bot.set_webhook(
        url=WEBHOOK_URL,
        drop_pending_updates=True
    )
    
    # Запускаем приложение (для Render)
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()