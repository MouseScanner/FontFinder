import logging
import os
import uuid
import aiohttp
import aiofiles

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.font_search import get_search_results_keyboard, get_font_info_keyboard
from services.font_api_client import FontApiClient
from utils.pagination import paginate_results
from keyboards.main_menu import get_main_menu_keyboard

router = Router()
font_api_client = FontApiClient()

# Папка для сохранения шрифтов
FONTS_DIR = "fonts"

# Создаем папку, если она не существует
os.makedirs(FONTS_DIR, exist_ok=True)

class FontSearch(StatesGroup):
    waiting_for_query = State()


def register_font_search_handlers(dp, db):
    # Сохраняем базу данных в атрибуте роутера
    router.db = db
    
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


@router.callback_query(F.data == "search_font")
async def search_font_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔍 Поиск шрифтов\n\n"
        "Введите название шрифта для поиска:"
    )
    await state.set_state(FontSearch.waiting_for_query)
    await callback.answer()


@router.message(FontSearch.waiting_for_query)
async def process_font_search(message: Message, state: FSMContext, db):
    query = message.text.strip()
    user_id = message.from_user.id

    if not query:
        await message.answer("Пожалуйста, введите название шрифта для поиска.")
        return

    await message.answer(f"🔍 Ищу шрифты по запросу: {query}...")

    # Получаем результаты поиска
    search_results = await font_api_client.search_fonts(query)

    # Добавляем запрос в историю поиска
    search_id = db.add_search_query(user_id, query)

    if not search_results:
        await message.answer(
            "😕 По вашему запросу ничего не найдено.\n"
            "Попробуйте другой запрос или вернитесь в главное меню.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        return

    # Сохраняем найденные шрифты в базе данных
    for font in search_results:
        db.add_found_font(search_id, font)

    # Сохраняем результаты поиска и текущую страницу
    await state.update_data(
        search_results=search_results,
        current_page=1,
        query=query,
        search_id=search_id
    )

    # Отображаем первую страницу результатов
    paginated_results = paginate_results(search_results, 1)

    await message.answer(
        f"🔍 Результаты поиска по запросу: {query}\n"
        f"Найдено шрифтов: {len(search_results)}",
        reply_markup=get_search_results_keyboard(paginated_results, 1, len(search_results))
    )


@router.callback_query(F.data.startswith("page_"))
async def process_page_navigation(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[1])

    # Получаем сохраненные данные
    data = await state.get_data()
    search_results = data.get("search_results", [])
    query = data.get("query", "")

    # Отображаем выбранную страницу результатов
    paginated_results = paginate_results(search_results, page)

    await callback.message.edit_text(
        f"🔍 Результаты поиска по запросу: {query}\n"
        f"Найдено шрифтов: {len(search_results)}",
        reply_markup=get_search_results_keyboard(paginated_results, page, len(search_results))
    )

    # Обновляем текущую страницу
    await state.update_data(current_page=page)
    await callback.answer()


@router.callback_query(F.data.startswith("font_"))
async def show_font_info(callback: CallbackQuery, state: FSMContext):
    font_slug = callback.data.split("_")[1]

    # Получаем сохраненные данные
    data = await state.get_data()
    search_results = data.get("search_results", [])

    # Находим информацию о выбранном шрифте
    font_info = None
    for font in search_results:
        if font["data"]["slug"] == font_slug:
            font_info = font
            break

    if not font_info:
        await callback.answer("Информация о шрифте не найдена.")
        return

    # Формируем сообщение с информацией о шрифте
    font_data = font_info["data"]
    font_name = font_data["font_name"]
    designer = font_data.get("designer", "Не указан")
    manufacturer = font_data.get("manufacturer", "Не указан")
    user_fullname = font_data.get("user_fullname", "")

    message_text = (
        f"🔤 <b>{font_name}</b>\n\n"
        f"👤 Дизайнер: {designer}\n"
        f"🏢 Производитель: {manufacturer}\n"
        f"ℹ️ {user_fullname}\n\n"
        f"🔗 <a href='{font_data['url']}'>Страница шрифта</a>"
    )

    await callback.message.edit_text(
        message_text,
        reply_markup=get_font_info_keyboard(font_slug, data.get("current_page", 1)),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("download_"))
async def download_font(callback: CallbackQuery, db):
    font_slug = callback.data.split("_")[1]
    download_url = f"https://font.download/dl/font/{font_slug}.zip"
    
    # Отправляем сообщение о начале скачивания
    status_message = await callback.message.answer(f"⏳ Начинаю скачивание шрифта {font_slug}...")
    
    try:
        logging.info(f"Скачивание шрифта по ссылке: {download_url}")
        
        # Генерируем уникальное имя файла
        filename = f"{uuid.uuid4()}_{font_slug}.zip"
        file_path = os.path.join(FONTS_DIR, filename)
        
        # Скачиваем файл
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as response:
                if response.status == 200:
                    # Сохраняем файл
                    async with aiofiles.open(file_path, 'wb') as f:
                        await f.write(await response.read())
                    
                    # Проверяем, что файл действительно скачался
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        logging.info(f"Шрифт успешно скачан и сохранен: {file_path}")
                        
                        # Ищем шрифт в локальной базе
                        db.cursor.execute(
                            "SELECT id FROM local_fonts WHERE font_slug = ?",
                            (font_slug,)
                        )
                        result = db.cursor.fetchone()
                        
                        if result:
                            # Если шрифт уже есть в базе, обновляем путь к файлу
                            font_id = result[0]
                            db.cursor.execute(
                                "UPDATE local_fonts SET file_path = ? WHERE id = ?",
                                (file_path, font_id)
                            )
                            db.connection.commit()
                            
                            # Увеличиваем счетчик загрузок
                            db.increment_font_download_count(font_id)
                        
                        # Отправляем файл пользователю
                        await callback.message.answer_document(
                            FSInputFile(file_path, filename=f"{font_slug}.zip"),
                            caption=f"Шрифт: {font_slug}"
                        )
                        
                        await status_message.edit_text(f"✅ Шрифт {font_slug} успешно скачан и отправлен!")
                    else:
                        logging.error(f"Файл не был скачан или имеет нулевой размер: {file_path}")
                        await callback.message.answer(
                            f"⬇️ Скачать шрифт: <a href='{download_url}'>{font_slug}</a>",
                            parse_mode="HTML"
                        )
                        await status_message.edit_text(f"⚠️ Не удалось скачать шрифт. Отправлена ссылка для ручного скачивания.")
                else:
                    logging.warning(f"Не удалось скачать шрифт. Статус: {response.status}")
                    await callback.message.answer(
                        f"⬇️ Скачать шрифт: <a href='{download_url}'>{font_slug}</a>",
                        parse_mode="HTML"
                    )
                    await status_message.edit_text(f"⚠️ Не удалось скачать шрифт. Отправлена ссылка для ручного скачивания.")
    except Exception as e:
        logging.error(f"Ошибка при скачивании шрифта: {e}")
        await callback.message.answer(
            f"⬇️ Скачать шрифт: <a href='{download_url}'>{font_slug}</a>",
            parse_mode="HTML"
        )
        await status_message.edit_text(f"❌ Ошибка при скачивании: {str(e)}")
    
    await callback.answer()
