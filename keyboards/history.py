from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import datetime

def get_history_keyboard(history_items):
    """
    Создает клавиатуру со списком истории поиска
    """
    keyboard = []
    
    for item in history_items:
        search_date = datetime.datetime.fromisoformat(item["search_date"])
        formatted_date = search_date.strftime("%d.%m.%Y %H:%M")
        
        button_text = f"🔍 {item['query']} ({formatted_date})"
        
        keyboard.append([
            InlineKeyboardButton(text=button_text, callback_data=f"history_item_{item['id']}")
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_history_item_keyboard():
    """
    Создает клавиатуру для просмотра деталей элемента истории
    """
    keyboard = [
        [
            InlineKeyboardButton(text="↩️ Назад к истории", callback_data="history")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 