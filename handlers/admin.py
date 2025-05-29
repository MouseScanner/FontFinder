from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.admin import (
    get_admin_keyboard, get_users_keyboard, get_searches_keyboard, 
    get_user_info_keyboard, get_local_fonts_keyboard, get_font_info_keyboard
)
from keyboards.main_menu import get_main_menu_keyboard
from config import ADMIN_IDS
import datetime
import os
import logging
import aiohttp
import aiofiles
import uuid

router = Router()

# Папка для сохранения шрифтов
FONTS_DIR = "fonts"

# Создаем папку, если она не существует
os.makedirs(FONTS_DIR, exist_ok=True)

class AdminAction(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_font_search = State()

def register_admin_handlers(dp, db):
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

# Проверка на администратора
def is_admin_filter(message):
    return message.from_user.id in ADMIN_IDS

@router.message(Command("admin"))
async def cmd_admin(message: Message, db):
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS and not db.is_admin(user_id):
        await message.answer("У вас нет доступа к админ-панели.")
        return
    
    # Устанавливаем пользователя как администратора в базе данных
    db.set_admin(user_id, True)
    
    await message.answer(
        "👑 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard()
    )

@router.callback_query(F.data == "admin")
async def show_admin_panel(callback: CallbackQuery, db):
    user_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS and not db.is_admin(user_id):
        await callback.answer("У вас нет доступа к админ-панели.")
        return
    
    await callback.message.edit_text(
        "👑 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_users")
async def show_users(callback: CallbackQuery, db):
    user_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS and not db.is_admin(user_id):
        await callback.answer("У вас нет доступа к админ-панели.")
        return
    
    # Получаем список пользователей
    users = db.get_all_users()
    
    await callback.message.edit_text(
        "👥 Пользователи\n\n"
        f"Всего пользователей: {len(users)}",
        reply_markup=get_users_keyboard(users)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_users_page_"))
async def navigate_users(callback: CallbackQuery, db):
    user_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS and not db.is_admin(user_id):
        await callback.answer("У вас нет доступа к админ-панели.")
        return
    
    # Получаем номер страницы
    page = int(callback.data.split("_")[3])
    
    # Получаем список пользователей
    users = db.get_all_users()
    
    await callback.message.edit_text(
        "👥 Пользователи\n\n"
        f"Всего пользователей: {len(users)}",
        reply_markup=get_users_keyboard(users, page)
    )
    await callback.answer()

@router.callback_query(F.data == "admin_searches")
async def show_searches(callback: CallbackQuery, db):
    user_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS and not db.is_admin(user_id):
        await callback.answer("У вас нет доступа к админ-панели.")
        return
    
    # Получаем список поисковых запросов
    searches = db.get_all_searches()
    
    await callback.message.edit_text(
        "🔍 Поисковые запросы\n\n"
        f"Всего запросов: {len(searches)}",
        reply_markup=get_searches_keyboard(searches)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_searches_page_"))
async def navigate_searches(callback: CallbackQuery, db):
    user_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS and not db.is_admin(user_id):
        await callback.answer("У вас нет доступа к админ-панели.")
        return
    
    # Получаем номер страницы
    page = int(callback.data.split("_")[3])
    
    # Получаем список поисковых запросов
    searches = db.get_all_searches()
    
    await callback.message.edit_text(
        "🔍 Поисковые запросы\n\n"
        f"Всего запросов: {len(searches)}",
        reply_markup=get_searches_keyboard(searches, page)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_user_"))
async def show_user_info(callback: CallbackQuery, db):
    admin_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if admin_id not in ADMIN_IDS and not db.is_admin(admin_id):
        await callback.answer("У вас нет доступа к админ-панели.")
        return
    
    # Получаем ID пользователя
    user_id = int(callback.data.split("_")[2])
    
    # Получаем информацию о пользователе
    users = db.get_all_users()
    user_info = None
    
    for user in users:
        if user["user_id"] == user_id:
            user_info = user
            break
    
    if not user_info:
        await callback.answer("Пользователь не найден.")
        return
    
    # Форматируем дату регистрации
    reg_date = datetime.datetime.fromisoformat(user_info["registration_date"])
    formatted_date = reg_date.strftime("%d.%m.%Y %H:%M")
    
    # Формируем сообщение с информацией о пользователе
    admin_status = "Да" if user_info["is_admin"] else "Нет"
    
    message_text = (
        f"👤 <b>Информация о пользователе</b>\n\n"
        f"ID: {user_info['user_id']}\n"
        f"Имя: {user_info['full_name']}\n"
        f"Username: @{user_info['username']}\n"
        f"Администратор: {admin_status}\n"
        f"Дата регистрации: {formatted_date}\n"
        f"Количество поисков: {user_info['search_count']}"
    )
    
    await callback.message.edit_text(
        message_text,
        reply_markup=get_user_info_keyboard(user_id),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_search_"))
async def show_search_info(callback: CallbackQuery, state: FSMContext, db):
    user_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS and not db.is_admin(user_id):
        await callback.answer("У вас нет доступа к админ-панели.")
        return
    
    # Проверяем, является ли это запросом на поиск локальных шрифтов
    if callback.data == "admin_search_local_fonts":
        await search_local_fonts_prompt(callback, state)
        return
    
    # Получаем ID поиска
    search_id = int(callback.data.split("_")[2])
    
    # Получаем информацию о поиске
    search_details = db.get_search_details(search_id)
    
    if not search_details:
        await callback.answer("Информация о поиске не найдена.")
        return
    
    # Форматируем дату
    search_date = datetime.datetime.fromisoformat(search_details["search_date"])
    formatted_date = search_date.strftime("%d.%m.%Y %H:%M")
    
    # Формируем сообщение с информацией о поиске
    message_text = (
        f"🔍 <b>Информация о поиске</b>\n\n"
        f"ID: {search_details['id']}\n"
        f"Запрос: {search_details['query']}\n"
        f"Дата: {formatted_date}\n"
        f"Пользователь: {search_details['user']['full_name']} (@{search_details['user']['username']})\n\n"
        f"Найдено шрифтов: {len(search_details['fonts'])}\n\n"
    )
    
    # Добавляем информацию о найденных шрифтах
    for i, font in enumerate(search_details['fonts'], 1):
        message_text += (
            f"{i}. <b>{font['font_name']}</b>\n"
            f"👤 Дизайнер: {font['designer'] or 'Не указан'}\n"
            f"🔗 <a href='{font['download_url']}'>Скачать шрифт</a>\n\n"
        )
    
    # Создаем клавиатуру для возврата
    keyboard = [
        [
            InlineKeyboardButton(text="↩️ Назад к поискам", callback_data="admin_searches")
        ],
        [
            InlineKeyboardButton(text="👑 Назад в админку", callback_data="admin")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    
    await callback.message.edit_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_user_history_"))
async def show_user_history(callback: CallbackQuery, db):
    admin_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if admin_id not in ADMIN_IDS and not db.is_admin(admin_id):
        await callback.answer("У вас нет доступа к админ-панели.")
        return
    
    # Получаем ID пользователя
    user_id = int(callback.data.split("_")[3])
    
    # Получаем историю поиска пользователя
    history = db.get_user_search_history(user_id)
    
    if not history:
        await callback.answer("У пользователя нет истории поиска.")
        return
    
    # Формируем сообщение с историей поиска
    message_text = f"📂 <b>История поиска пользователя</b>\n\n"
    
    for i, item in enumerate(history, 1):
        # Форматируем дату
        search_date = datetime.datetime.fromisoformat(item["search_date"])
        formatted_date = search_date.strftime("%d.%m.%Y %H:%M")
        
        message_text += (
            f"{i}. <b>{item['query']}</b>\n"
            f"📅 Дата: {formatted_date}\n"
            f"Найдено шрифтов: {len(item['fonts'])}\n\n"
        )
    
    # Создаем клавиатуру для возврата
    keyboard = [
        [
            InlineKeyboardButton(text=f"↩️ Назад к информации о пользователе", callback_data=f"admin_user_{user_id}")
        ],
        [
            InlineKeyboardButton(text="👑 Назад в админку", callback_data="admin")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    
    await callback.message.edit_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_make_admin_"))
async def make_admin(callback: CallbackQuery, db):
    admin_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if admin_id not in ADMIN_IDS and not db.is_admin(admin_id):
        await callback.answer("У вас нет доступа к админ-панели.")
        return
    
    # Получаем ID пользователя
    user_id = int(callback.data.split("_")[3])
    
    # Делаем пользователя администратором
    db.set_admin(user_id, True)
    
    await callback.answer("Пользователь назначен администратором!")
    
    # Обновляем информацию о пользователе
    await show_user_info(callback, db)

@router.callback_query(F.data == "admin_stats")
async def show_statistics(callback: CallbackQuery, db):
    user_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if not db.is_admin(user_id):
        await callback.answer("У вас нет доступа к этой функции", show_alert=True)
        return
    
    # Получаем статистику
    user_count = db.get_user_count()
    admin_count = db.get_admin_count()
    search_count = db.get_search_count()
    font_count = db.get_font_count()
    doc_count = db.get_document_count()
    font_stats = db.get_font_stats()
    total_downloads = font_stats.get("total_downloads", 0) if font_stats else 0
    
    # Получаем статистику локальных поисков
    local_search_stats = db.get_local_search_stats()
    local_search_count = local_search_stats.get("total_searches", 0) if local_search_stats else 0
    unique_users = local_search_stats.get("unique_users", 0) if local_search_stats else 0
    unique_queries = local_search_stats.get("unique_queries", 0) if local_search_stats else 0
    avg_results = local_search_stats.get("avg_results", 0) if local_search_stats else 0
    top_queries = local_search_stats.get("top_queries", []) if local_search_stats else []
    
    # Формируем сообщение со статистикой
    stats_message = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: {user_count}\n"
        f"👑 Администраторов: {admin_count}\n"
        f"🔍 Всего поисков: {search_count}\n"
        f"🔤 Шрифтов в базе: {font_count}\n"
        f"📄 Документов: {doc_count}\n"
        f"⬇️ Всего загрузок: {total_downloads}\n\n"
        f"<b>Статистика локальных поисков:</b>\n"
        f"🔍 Всего локальных поисков: {local_search_count}\n"
        f"👤 Уникальных пользователей: {unique_users}\n"
        f"❓ Уникальных запросов: {unique_queries}\n"
        f"📊 Среднее количество результатов: {avg_results:.1f}\n"
    )
    
    # Добавляем топ запросов, если они есть
    if top_queries:
        stats_message += "\n<b>Популярные запросы:</b>\n"
        for i, (query, count) in enumerate(top_queries[:5], 1):
            stats_message += f"{i}. {query} - {count} раз\n"
    
    # Создаем клавиатуру для возврата в админ-панель
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в админ-панель", callback_data="admin")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(stats_message, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_local_fonts")
async def show_local_fonts(callback: CallbackQuery, db):
    user_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS and not db.is_admin(user_id):
        await callback.answer("У вас нет доступа к админ-панели.")
        return
    
    # Получаем список локальных шрифтов
    fonts = db.get_local_fonts()
    
    # Формируем сообщение
    message_text = f"🗃️ <b>Локальная база шрифтов</b>\n\nВсего шрифтов: {len(fonts)}"
    
    # Если шрифтов нет, добавляем соответствующее сообщение
    if not fonts:
        message_text += "\n\nБаза пуста. Шрифты будут добавляться автоматически при поиске."
    
    # Создаем клавиатуру
    keyboard = get_local_fonts_keyboard(fonts)
    
    await callback.message.edit_text(
        message_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_local_fonts_page_"))
async def navigate_local_fonts(callback: CallbackQuery, db):
    user_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS and not db.is_admin(user_id):
        await callback.answer("У вас нет доступа к админ-панели.")
        return
    
    # Получаем номер страницы
    page = int(callback.data.split("_")[-1])
    
    # Получаем список локальных шрифтов
    fonts = db.get_local_fonts()
    
    # Формируем сообщение
    message_text = f"🗃️ <b>Локальная база шрифтов</b>\n\nВсего шрифтов: {len(fonts)}"
    
    # Создаем клавиатуру
    keyboard = get_local_fonts_keyboard(fonts, page=page)
    
    await callback.message.edit_text(
        message_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_font_"))
async def show_font_info(callback: CallbackQuery, db):
    user_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS and not db.is_admin(user_id):
        await callback.answer("У вас нет доступа к админ-панели.")
        return
    
    # Получаем ID шрифта
    font_id = int(callback.data.split("_")[-1])
    
    # Получаем информацию о шрифте
    fonts = db.get_local_fonts()
    font = next((f for f in fonts if f["id"] == font_id), None)
    
    if not font:
        await callback.answer("Шрифт не найден.")
        return
    
    # Форматируем дату добавления
    added_date = datetime.datetime.fromisoformat(font["added_date"])
    formatted_date = added_date.strftime("%d.%m.%Y %H:%M")
    
    # Проверяем наличие файла
    file_exists = font["file_path"] and os.path.exists(font["file_path"])
    file_size = "Нет файла"
    if file_exists:
        size_bytes = os.path.getsize(font["file_path"])
        if size_bytes < 1024:
            file_size = f"{size_bytes} байт"
        elif size_bytes < 1024 * 1024:
            file_size = f"{size_bytes / 1024:.1f} КБ"
        else:
            file_size = f"{size_bytes / (1024 * 1024):.1f} МБ"
    
    # Формируем сообщение с информацией о шрифте
    message_text = (
        f"🔤 <b>{font['font_name']}</b>\n\n"
        f"🆔 ID: {font['id']}\n"
        f"🔍 Slug: {font['font_slug']}\n"
        f"👨‍🎨 Дизайнер: {font['designer'] or 'Не указан'}\n"
        f"🏭 Производитель: {font['manufacturer'] or 'Не указан'}\n"
        f"👤 Пользователь: {font['user_fullname'] or 'Не указан'}\n"
        f"📅 Добавлен: {formatted_date}\n"
        f"⬇️ Загрузок: {font['download_count']}\n"
        f"📄 Тип: {'Документ' if font['is_document'] else 'Найден при поиске'}\n"
    )
    
    # Добавляем информацию о пользователе, добавившем шрифт
    if font["added_by"]:
        message_text += f"👤 Добавил: {font['added_by']['full_name']} (@{font['added_by']['username']})\n"
    
    # Добавляем информацию о файле
    if file_exists:
        message_text += f"📂 Файл: {os.path.basename(font['file_path'])}\n"
        message_text += f"📊 Размер: {file_size}\n"
        message_text += f"✅ Статус: Файл доступен\n"
    else:
        if font["file_path"]:
            message_text += f"📂 Файл: {os.path.basename(font['file_path'])}\n"
            message_text += f"❌ Статус: Файл не найден\n"
        else:
            message_text += f"❌ Статус: Файл не загружен\n"
    
    # Создаем клавиатуру
    keyboard = get_font_info_keyboard(font_id)
    
    await callback.message.edit_text(
        message_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_download_font_"))
async def download_font(callback: CallbackQuery, db):
    user_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS and not db.is_admin(user_id):
        await callback.answer("У вас нет доступа к админ-панели.")
        return
    
    # Получаем ID шрифта
    font_id = int(callback.data.split("_")[-1])
    
    # Получаем информацию о шрифте
    fonts = db.get_local_fonts()
    font = next((f for f in fonts if f["id"] == font_id), None)
    
    if not font:
        await callback.answer("Шрифт не найден.")
        return
    
    # Увеличиваем счетчик загрузок
    db.increment_font_download_count(font_id)
    
    # Отправляем сообщение о начале скачивания
    status_message = await callback.message.answer(f"⏳ Начинаю скачивание шрифта {font['font_name']}...")
    
    try:
        # Если это документ и файл существует, отправляем его
        if font["is_document"] and font["file_path"] and os.path.exists(font["file_path"]):
            logging.info(f"Отправка локального файла шрифта: {font['file_path']}")
            
            try:
                await callback.message.answer_document(
                    FSInputFile(font["file_path"], filename=os.path.basename(font["file_path"])),
                    caption=f"Шрифт: {font['font_name']}"
                )
                await status_message.edit_text(f"✅ Шрифт {font['font_name']} успешно отправлен!")
            except Exception as e:
                logging.error(f"Ошибка при отправке локального файла: {e}")
                await status_message.edit_text(f"❌ Ошибка при отправке файла: {str(e)}")
        else:
            # Скачиваем шрифт по ссылке
            download_url = font["download_url"]
            logging.info(f"Скачивание шрифта по ссылке: {download_url}")
            
            # Генерируем уникальное имя файла
            filename = f"{uuid.uuid4()}_{font['font_slug']}.zip"
            file_path = os.path.join(FONTS_DIR, filename)
            
            try:
                # Скачиваем файл
                async with aiohttp.ClientSession() as session:
                    async with session.get(download_url) as response:
                        if response.status == 200:
                            # Сохраняем файл
                            async with aiofiles.open(file_path, 'wb') as f:
                                await f.write(await response.read())
                            
                            # Обновляем путь к файлу в базе данных
                            db.cursor.execute(
                                "UPDATE local_fonts SET file_path = ? WHERE id = ?",
                                (file_path, font_id)
                            )
                            db.connection.commit()
                            
                            # Отправляем файл пользователю
                            await callback.message.answer_document(
                                FSInputFile(file_path, filename=f"{font['font_name']}.zip"),
                                caption=f"Шрифт: {font['font_name']}"
                            )
                            
                            await status_message.edit_text(f"✅ Шрифт {font['font_name']} успешно скачан и отправлен!")
                            logging.info(f"Шрифт успешно скачан и сохранен: {file_path}")
                        else:
                            # Если не удалось скачать, отправляем ссылку
                            await callback.message.answer(
                                f"⬇️ Ссылка для скачивания шрифта {font['font_name']}:\n{download_url}",
                                disable_web_page_preview=True
                            )
                            await status_message.edit_text(f"⚠️ Не удалось скачать шрифт. Отправлена ссылка для ручного скачивания.")
                            logging.warning(f"Не удалось скачать шрифт. Статус: {response.status}")
            except Exception as e:
                # В случае ошибки отправляем ссылку
                await callback.message.answer(
                    f"⬇️ Ссылка для скачивания шрифта {font['font_name']}:\n{download_url}",
                    disable_web_page_preview=True
                )
                await status_message.edit_text(f"❌ Ошибка при скачивании: {str(e)}")
                logging.error(f"Ошибка при скачивании шрифта: {e}")
    except Exception as e:
        logging.error(f"Общая ошибка при скачивании шрифта: {e}")
        await status_message.edit_text(f"❌ Произошла ошибка: {str(e)}")
    
    await callback.answer()

@router.callback_query(F.data.startswith("admin_delete_font_"))
async def delete_font(callback: CallbackQuery, db):
    user_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS and not db.is_admin(user_id):
        await callback.answer("У вас нет доступа к админ-панели.")
        return
    
    # Получаем ID шрифта
    font_id = int(callback.data.split("_")[-1])
    
    # Получаем информацию о шрифте
    fonts = db.get_local_fonts()
    font = next((f for f in fonts if f["id"] == font_id), None)
    
    if not font:
        await callback.answer("Шрифт не найден.")
        return
    
    # Удаляем шрифт из базы
    success = db.delete_local_font(font_id)
    
    if success:
        await callback.answer("Шрифт успешно удален из базы.")
        # Возвращаемся к списку шрифтов
        await show_local_fonts(callback, db)
    else:
        await callback.answer("Не удалось удалить шрифт.")

@router.callback_query(F.data == "admin_search_local_fonts")
async def search_local_fonts_prompt(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS and not db.is_admin(user_id):
        await callback.answer("У вас нет доступа к админ-панели.")
        return
    
    # Получаем объект базы данных из атрибута роутера
    db = router.db
    
    # Устанавливаем состояние ожидания поискового запроса
    await state.set_state(AdminAction.waiting_for_font_search)
    
    # Отправляем сообщение с запросом поискового запроса
    await callback.message.answer(
        "🔎 Введите поисковый запрос для поиска по локальной базе шрифтов:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_local_fonts")]
        ])
    )
    await callback.answer()

@router.message(AdminAction.waiting_for_font_search)
async def search_local_fonts(message: Message, state: FSMContext, db):
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS and not db.is_admin(user_id):
        await message.answer("У вас нет доступа к админ-панели.")
        return
    
    # Получаем поисковый запрос
    query = message.text.strip()
    
    # Сбрасываем состояние
    await state.clear()
    
    # Отправляем сообщение о начале поиска
    status_message = await message.answer(f"🔎 Выполняю поиск по запросу: {query}...")
    
    try:
        # Выполняем поиск в локальной базе
        fonts = db.search_local_fonts(query)
        
        # Формируем сообщение
        if fonts:
            message_text = (
                f"🔎 <b>Результаты поиска по запросу:</b> {query}\n\n"
                f"Найдено шрифтов: {len(fonts)}\n\n"
            )
            
            # Добавляем информацию о первых 3 результатах
            for i, font in enumerate(fonts[:3], 1):
                message_text += (
                    f"{i}. <b>{font['font_name']}</b>\n"
                    f"👤 Дизайнер: {font.get('designer', '') or 'Не указан'}\n"
                    f"🏢 Производитель: {font.get('manufacturer', '') or 'Не указан'}\n\n"
                )
        else:
            message_text = f"🔎 <b>По запросу {query} ничего не найдено</b>"
        
        # Создаем клавиатуру
        keyboard = get_local_fonts_keyboard(fonts) if fonts else InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад к шрифтам", callback_data="admin_local_fonts")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await status_message.edit_text(
            message_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка при поиске шрифтов: {e}")
        await status_message.edit_text(
            f"❌ Произошла ошибка при поиске: {str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="↩️ Назад к шрифтам", callback_data="admin_local_fonts")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ])
        )

@router.callback_query(F.data.startswith("admin_refresh_font_"))
async def refresh_font_info(callback: CallbackQuery, db):
    user_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS and not db.is_admin(user_id):
        await callback.answer("У вас нет доступа к админ-панели.")
        return
    
    # Получаем ID шрифта
    font_id = int(callback.data.split("_")[-1])
    
    # Отправляем сообщение о начале обновления
    await callback.answer("Обновляю информацию о шрифте...")
    
    # Просто перезагружаем информацию о шрифте
    await show_font_info(callback, db)

@router.callback_query(F.data.startswith("admin_font_stats_"))
async def show_font_stats(callback: CallbackQuery, db):
    user_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS and not db.is_admin(user_id):
        await callback.answer("У вас нет доступа к админ-панели.")
        return
    
    # Получаем ID шрифта
    font_id = int(callback.data.split("_")[-1])
    
    # Получаем информацию о шрифте
    fonts = db.get_local_fonts()
    font = next((f for f in fonts if f["id"] == font_id), None)
    
    if not font:
        await callback.answer("Шрифт не найден.")
        return
    
    # Получаем дополнительную статистику
    # Например, сколько раз шрифт был скачан за последний месяц
    # В данном случае у нас нет такой информации, поэтому просто показываем общую статистику
    
    # Форматируем дату добавления
    added_date = datetime.datetime.fromisoformat(font["added_date"])
    formatted_date = added_date.strftime("%d.%m.%Y %H:%M")
    
    # Вычисляем, сколько дней прошло с момента добавления
    days_since_added = (datetime.datetime.now() - added_date).days
    
    # Вычисляем среднее количество скачиваний в день
    downloads_per_day = font["download_count"] / max(days_since_added, 1)
    
    # Формируем сообщение со статистикой
    message_text = (
        f"📊 <b>Статистика шрифта {font['font_name']}</b>\n\n"
        f"🆔 ID: {font['id']}\n"
        f"📅 Добавлен: {formatted_date} ({days_since_added} дней назад)\n"
        f"⬇️ Всего загрузок: {font['download_count']}\n"
        f"📈 Среднее количество загрузок в день: {downloads_per_day:.2f}\n"
        f"📄 Тип: {'Документ' if font['is_document'] else 'Найден при поиске'}\n"
    )
    
    # Создаем клавиатуру для возврата
    keyboard = [
        [
            InlineKeyboardButton(text="↩️ Назад к информации о шрифте", callback_data=f"admin_font_{font_id}")
        ],
        [
            InlineKeyboardButton(text="↩️ Назад к шрифтам", callback_data="admin_local_fonts")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    
    await callback.message.edit_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )
    await callback.answer() 