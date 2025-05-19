import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import asyncio

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
PORT = int(os.getenv('PORT', 10000))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот с AI-моделью. Задайте вопрос.")

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
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('outputs', [{}])[0].get('outputs', [{}])[0].get('results', {}).get('message', '')
            text = message if isinstance(message, str) else message.get('text', 'Не удалось обработать ответ')
            await update.message.reply_text(text)
        else:
            await update.message.reply_text("Ошибка API, попробуйте позже")
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("Произошла ошибка")

def main():
    """Основная функция для запуска на Render"""
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Удаляем старый webhook и устанавливаем новый
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        drop_pending_updates=True,
        secret_token=None
    )

if __name__ == "__main__":
    # Для Render используем просто main() без asyncio.run
    main()