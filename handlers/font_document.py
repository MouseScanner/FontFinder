from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Document
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.main_menu import get_main_menu_keyboard
import os
import logging
import uuid

router = Router()

# Папка для сохранения документов
FONTS_DIR = "fonts"

# Создаем папку, если она не существует
os.makedirs(FONTS_DIR, exist_ok=True)

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("font_document.log"),
        logging.StreamHandler()
    ]
)

def register_font_document_handlers(dp, db):
    # Добавляем middleware для передачи db в обработчики
    router.message.middleware(DbMiddleware(db))
    router.callback_query.middleware(DbMiddleware(db))
    
    dp.include_router(router)

class DbMiddleware:
    def __init__(self, db):
        self.db = db
    
    async def __call__(self, handler, event, data):
        # Добавляем объект базы данных в данные обработчика
        data["db"] = self.db
        return await handler(event, data)

@router.message(F.document)
async def process_font_document(message: Message, db):
    """Обработка документов с шрифтами"""
    user_id = message.from_user.id
    document = message.document
    
    logging.info(f"Получен документ: {document.file_name} от пользователя {user_id}")
    
    # Проверяем, является ли документ шрифтом
    if not is_font_file(document.file_name):
        logging.info(f"Файл {document.file_name} не является шрифтом, игнорируем")
        # Если это не шрифт, игнорируем
        return
    
    # Отправляем сообщение о начале обработки
    status_message = await message.answer(f"⏳ Обрабатываю файл шрифта {document.file_name}...")
    
    try:
        # Сохраняем информацию о пользователе
        db.add_user(
            user_id=user_id,
            username=message.from_user.username or "",
            full_name=message.from_user.full_name or ""
        )
        
        # Скачиваем файл
        file_path = await download_font_file(document)
        
        if not file_path:
            await status_message.edit_text(
                "❌ Не удалось сохранить файл шрифта. Пожалуйста, попробуйте еще раз."
            )
            return
        
        logging.info(f"Файл шрифта сохранен: {file_path}")
        
        # Создаем данные о шрифте
        font_name = os.path.splitext(document.file_name)[0]
        font_slug = font_name.lower().replace(" ", "-")
        
        font_data = {
            "font_name": font_name,
            "slug": font_slug,
            "designer": "",
            "manufacturer": "",
            "user_fullname": message.from_user.full_name or "",
            "url": ""
        }
        
        # Добавляем шрифт в локальную базу
        db.add_font_document(user_id, font_data, file_path)
        logging.info(f"Шрифт {font_name} добавлен в базу данных")
        
        # Отправляем сообщение пользователю
        await status_message.edit_text(
            f"✅ Шрифт <b>{font_name}</b> успешно добавлен в локальную базу данных!",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка при обработке документа: {e}")
        await status_message.edit_text(
            f"❌ Произошла ошибка при обработке файла: {str(e)}"
        )

def is_font_file(filename):
    """Проверяет, является ли файл шрифтом по расширению"""
    font_extensions = ['.ttf', '.otf', '.woff', '.woff2', '.eot', '.zip', '.rar']
    ext = os.path.splitext(filename.lower())[1]
    return ext in font_extensions

async def download_font_file(document):
    """Скачивает файл шрифта и возвращает путь к сохраненному файлу"""
    try:
        # Генерируем уникальное имя файла
        unique_filename = f"{uuid.uuid4()}_{document.file_name}"
        file_path = os.path.join(FONTS_DIR, unique_filename)
        
        logging.info(f"Начинаю скачивание файла в {file_path}")
        
        # Скачиваем файл
        await document.download(destination=file_path)
        
        # Проверяем, что файл действительно скачался
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            logging.info(f"Файл успешно скачан: {file_path}, размер: {os.path.getsize(file_path)} байт")
            return file_path
        else:
            logging.error(f"Файл не был скачан или имеет нулевой размер: {file_path}")
            return None
    except Exception as e:
        logging.error(f"Ошибка при скачивании файла: {e}")
        return None 