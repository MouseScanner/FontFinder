import os
from dotenv import load_dotenv

# Получаем абсолютный путь к директории проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Загрузка переменных окружения из .env файла
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# API для поиска шрифтов
FONT_API_URL = "https://font.download/ajax/autocomplete"
FONT_DOWNLOAD_URL = "https://font.download/dl/font/{slug}.zip"

# Количество шрифтов на странице
FONTS_PER_PAGE = 3

# Директории
LOGS_DIR = os.path.join(BASE_DIR, "logs")
FONTS_DIR = os.path.join(BASE_DIR, "fonts")

# Путь к файлу базы данных
DATABASE_PATH = os.path.join(BASE_DIR, "database", "fonts_bot.db")
DB_DIR = os.path.dirname(DATABASE_PATH)

# Создаем необходимые директории
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(FONTS_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

# Настройки логирования
LOG_FILE = os.path.join(LOGS_DIR, "bot.log")
SEARCH_LOG_FILE = os.path.join(LOGS_DIR, "search.log")

# ID администраторов бота (список)
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id] 