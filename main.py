import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, DATABASE_PATH, LOGS_DIR, FONTS_DIR, LOG_FILE
from handlers import register_all_handlers
from database.db import Database

# Создаем директорию для базы данных, если она не существует
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# Создаем директорию для логов, если она не существует
os.makedirs(LOGS_DIR, exist_ok=True)

# Создаем директорию для шрифтов, если она не существует
os.makedirs(FONTS_DIR, exist_ok=True)

# Инициализация базы данных
db = Database(DATABASE_PATH)

async def main():
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    
    logging.info("Запуск бота...")
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Регистрация всех обработчиков
    register_all_handlers(dp, db)
    
    logging.info("Бот запущен и готов к работе")
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
    finally:
        # Закрываем соединение с базой данных при завершении работы
        logging.info("Завершение работы бота")
        db.close() 