from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Поиск шрифта", callback_data="search_font")
            ],
            [
                InlineKeyboardButton(text="🖼️ Распознать шрифт по изображению", callback_data="recognize_font")
            ],
            [
                InlineKeyboardButton(text="📂 История поиска", callback_data="history")
            ]
        ]
    )
    return keyboard 