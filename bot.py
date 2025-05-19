import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
from typing import Optional, Dict, Any

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я тестовый бот с AI-моделью.\n"
        "Просто напиши мне любой вопрос, и я постараюсь ответить!"
    )

def extract_message(response_data: Dict[str, Any]) -> Optional[str]:
    """Извлекает текстовое сообщение из ответа API с учётом разных форматов"""
    try:
        # Вариант 1: Основной путь к сообщению (как в первом примере)
        if 'outputs' in response_data and len(response_data['outputs']) > 0:
            first_output = response_data['outputs'][0]
            if 'outputs' in first_output and len(first_output['outputs']) > 0:
                message_data = first_output['outputs'][0]
                
                # Проверяем разные возможные пути к тексту
                if 'results' in message_data and 'message' in message_data['results']:
                    message = message_data['results']['message']
                    if isinstance(message, str):
                        return message
                    elif isinstance(message, dict):
                        if 'text' in message:
                            return message['text']
                        elif 'data' in message and 'text' in message['data']:
                            return message['data']['text']
                
                # Вариант 2: Альтернативный путь (как во втором примере)
                if 'artifacts' in message_data and 'message' in message_data['artifacts']:
                    return message_data['artifacts']['message']
                
                # Вариант 3: Самый глубокий уровень
                if 'messages' in message_data and len(message_data['messages']) > 0:
                    return message_data['messages'][0]['message']

        # Если ничего не найдено, попробуем найти текст в корне ответа
        if 'text' in response_data:
            return response_data['text']
        
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
            ai_message = extract_message(response_data)
            
            if ai_message:
                await update.message.reply_text(ai_message)
            else:
                logger.error(f"Не удалось извлечь сообщение из ответа: {response_data}")
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
        
        # Удаляем возможный старый webhook перед запуском polling
        app.bot.delete_webhook(drop_pending_updates=True)
        
        # Запускаем бота в режиме polling
        logger.info("Бот запущен в режиме polling")
        app.run_polling()
        
    except Exception as e:
        logger.critical(f"Ошибка при запуске бота: {str(e)}")

if __name__ == "__main__":
    main()