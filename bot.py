import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "7547401041:AAFa6kFA-nT8PpAuDwjqFAzIOYzrxmPXxgY"
LANGFLOW_API_KEY = "sk-ric-EXqYeklFtuOzW7TqJdXB39oOgzBLys92mpUwRcg"
LANGFLOW_ENDPOINT = "https://agents.kolbplus.de/api/v1/run/30d8502d-e8af-4a48-a095-8c8e59c20d6e?stream=false"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я бот с AI-моделью. Задайте мне вопрос!')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    # Отправка запроса к вашей AI-модели
    headers = {
        "Content-Type": "application/json",
        "x-api-key": LANGFLOW_API_KEY
    }
    
    data = {
        "input_value": user_message,
        "output_type": "chat",
        "input_type": "chat"
    }
    
    response = requests.post(LANGFLOW_ENDPOINT, headers=headers, json=data)
    
    if response.status_code == 200:
        ai_response = response.json()  # Может потребоваться адаптация под ваш API
        await update.message.reply_text(ai_response)
    else:
        await update.message.reply_text("Извините, произошла ошибка при обработке запроса")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()

if __name__ == "__main__":
    main()