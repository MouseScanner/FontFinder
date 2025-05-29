from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import FONTS_PER_PAGE
import math

def get_search_results_keyboard(fonts, current_page, total_fonts):
    keyboard = []
    
    for font in fonts:
        font_data = font["data"]
        font_name = font["value"]
        font_slug = font_data["slug"]
        
        keyboard.append([
            InlineKeyboardButton(text=f"🔤 {font_name}", callback_data=f"font_{font_slug}")
        ])
    
    navigation = []
    total_pages = math.ceil(total_fonts / FONTS_PER_PAGE)
    
    if current_page > 1:
        navigation.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{current_page - 1}")
        )
    
    navigation.append(
        InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="page_info")
    )
    
    if current_page < total_pages:
        navigation.append(
            InlineKeyboardButton(text="Вперед ➡️", callback_data=f"page_{current_page + 1}")
        )
    
    keyboard.append(navigation)
    
    keyboard.append([
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_font_info_keyboard(font_slug, current_page):
    keyboard = [
        [
            InlineKeyboardButton(text="⬇️ Скачать шрифт", callback_data=f"download_{font_slug}")
        ],
        [
            InlineKeyboardButton(text="↩️ Назад к результатам", callback_data=f"page_{current_page}")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 