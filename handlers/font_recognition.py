from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.main_menu import get_main_menu_keyboard

router = Router()

class FontRecognition(StatesGroup):
    waiting_for_image = State()

def register_font_recognition_handlers(dp, db):
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

@router.callback_query(F.data == "recognize_font")
async def recognize_font_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🖼️ Распознавание шрифта по изображению\n\n"
        "Отправьте изображение с текстом, шрифт которого вы хотите распознать:"
    )
    await state.set_state(FontRecognition.waiting_for_image)
    await callback.answer()

@router.message(FontRecognition.waiting_for_image, F.photo)
async def process_font_recognition(message: Message, state: FSMContext):
    # Здесь будет логика распознавания шрифта
    # В данном примере просто заглушка
    
    await message.answer(
        "🔍 Анализирую изображение...\n\n"
        "К сожалению, функция распознавания шрифта находится в разработке.\n"
        "Попробуйте воспользоваться поиском шрифта по названию.",
        reply_markup=get_main_menu_keyboard()
    )
    
    await state.clear()

@router.message(FontRecognition.waiting_for_image)
async def process_invalid_image(message: Message):
    await message.answer(
        "❌ Пожалуйста, отправьте изображение с текстом.\n"
        "Если вы хотите вернуться в главное меню, нажмите кнопку ниже:",
        reply_markup=get_main_menu_keyboard()
    ) 