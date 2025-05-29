from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keyboards.main_menu import get_main_menu_keyboard

router = Router()

def register_start_handlers(dp, db):
    router.message.middleware(UserMiddleware(db))
    router.callback_query.middleware(UserMiddleware(db))
    dp.include_router(router)

class UserMiddleware:
    def __init__(self, db):
        self.db = db
    
    async def __call__(self, handler, event, data):
        # Получаем информацию о пользователе
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
        else:
            return await handler(event, data)
        
        # Добавляем пользователя в базу данных
        self.db.add_user(
            user_id=user.id,
            username=user.username or "",
            full_name=f"{user.first_name} {user.last_name or ''}".strip()
        )
        
        # Добавляем объект базы данных в данные обработчика
        data["db"] = self.db
        
        return await handler(event, data)

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "👋 Добро пожаловать в бот для поиска и распознавания шрифтов!\n\n"
        "🔍 Вы можете искать шрифты по названию или загрузить изображение для распознавания шрифта.\n\n"
        "Выберите действие в меню ниже:",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "main_menu")
async def return_to_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "👋 Главное меню\n\n"
        "🔍 Вы можете искать шрифты по названию или загрузить изображение для распознавания шрифта.\n\n"
        "Выберите действие в меню ниже:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer() 