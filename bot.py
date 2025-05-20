import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging

# Configuring logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
LANGFLOW_API_KEY = os.getenv('LANGFLOW_API_KEY')
LANGFLOW_ENDPOINT = os.getenv('LANGFLOW_ENDPOINT')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """command handler /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Hi, {user.first_name}! I am your GEDA chatbot.\n"
        " How can I assist you? You can talk to me in any language you prefer."
    )

def extract_message_from_response(response_data):
    """Extracts a text message from a complex JSON response"""
    try:
        message = response_data['outputs'][0]['outputs'][0]['results']['message']['text']
        return message
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Error parsing the API response: {str(e)}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_message = update.message.text
        logger.info(f"Received a message from {update.effective_user.id}: {user_message}")
        
        # Sending a request to the AI model
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
                logger.error("Couldn't extract message from API response")
                await update.message.reply_text("An unexpected response format was received from AI.")
        else:
            error_msg = f"Ошибка API (код {response.status_code}): {response.text}"
            logger.error(error_msg)
            await update.message.reply_text("An error occurred while processing the request. Try again later.")
            
    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}")
        await update.message.reply_text("Oops! Something went wrong. Try again.")

def main():
    """Launching the bot"""
    try:
        logger.info("Запуск бота...")
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("The bot is running in the mode polling")
        app.run_polling()
        
    except Exception as e:
        logger.critical(f"Error when launching the bot: {str(e)}")

if __name__ == "__main__":
    main()