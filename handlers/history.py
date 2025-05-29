from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards.history import get_history_keyboard, get_history_item_keyboard
from keyboards.main_menu import get_main_menu_keyboard
import datetime

router = Router()

def register_history_handlers(dp, db):
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

@router.message(Command("history"))
async def cmd_history(message: Message, db):
    user_id = message.from_user.id
    
    # Получаем историю поиска пользователя
    history = db.get_user_search_history(user_id)
    
    if not history:
        await message.answer(
            "📂 У вас пока нет истории поиска.\n"
            "Воспользуйтесь поиском шрифтов, чтобы начать создавать историю.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await message.answer(
        "📂 История поиска\n\n"
        "Выберите запрос для просмотра подробной информации:",
        reply_markup=get_history_keyboard(history)
    )

@router.callback_query(F.data == "history")
async def show_history(callback: CallbackQuery, db):
    user_id = callback.from_user.id
    
    # Получаем историю поиска пользователя
    history = db.get_user_search_history(user_id)
    
    if not history:
        await callback.message.edit_text(
            "📂 У вас пока нет истории поиска.\n"
            "Воспользуйтесь поиском шрифтов, чтобы начать создавать историю.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await callback.message.edit_text(
        "📂 История поиска\n\n"
        "Выберите запрос для просмотра подробной информации:",
        reply_markup=get_history_keyboard(history)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("history_item_"))
async def show_history_item(callback: CallbackQuery, db):
    search_id = int(callback.data.split("_")[2])
    
    # Получаем подробную информацию о поиске
    search_details = db.get_search_details(search_id)
    
    if not search_details:
        await callback.answer("Информация о поиске не найдена.")
        return
    
    # Форматируем дату
    search_date = datetime.datetime.fromisoformat(search_details["search_date"])
    formatted_date = search_date.strftime("%d.%m.%Y %H:%M")
    
    # Формируем сообщение с информацией о поиске
    message_text = (
        f"🔍 Поиск: <b>{search_details['query']}</b>\n"
        f"📅 Дата: {formatted_date}\n\n"
        f"Найдено шрифтов: {len(search_details['fonts'])}\n\n"
    )
    
    # Добавляем информацию о найденных шрифтах
    for i, font in enumerate(search_details['fonts'], 1):
        message_text += (
            f"{i}. <b>{font['font_name']}</b>\n"
            f"👤 Дизайнер: {font['designer'] or 'Не указан'}\n"
            f"🔗 <a href='{font['download_url']}'>Скачать шрифт</a>\n\n"
        )
    
    await callback.message.edit_text(
        message_text,
        reply_markup=get_history_item_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer() 