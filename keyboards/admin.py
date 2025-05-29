from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import datetime

def get_admin_keyboard():
    """
    Создает клавиатуру для админ-панели
    """
    keyboard = [
        [
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="🔍 Поисковые запросы", callback_data="admin_searches")
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton(text="🗃️ Локальная база шрифтов", callback_data="admin_local_fonts")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_users_keyboard(users, page=1, items_per_page=5):
    """
    Создает клавиатуру со списком пользователей
    """
    keyboard = []
    
    # Пагинация
    total_pages = (len(users) + items_per_page - 1) // items_per_page
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(users))
    
    # Добавляем кнопки для каждого пользователя на текущей странице
    for user in users[start_idx:end_idx]:
        # Форматируем дату регистрации
        reg_date = datetime.datetime.fromisoformat(user["registration_date"])
        formatted_date = reg_date.strftime("%d.%m.%Y")
        
        # Создаем текст кнопки
        admin_mark = "👑 " if user["is_admin"] else ""
        button_text = f"{admin_mark}{user['full_name']} (@{user['username']}) - {formatted_date}"
        
        keyboard.append([
            InlineKeyboardButton(text=button_text, callback_data=f"admin_user_{user['user_id']}")
        ])
    
    # Добавляем кнопки навигации
    navigation = []
    
    if page > 1:
        navigation.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_users_page_{page - 1}")
        )
    
    navigation.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="admin_users_page_info")
    )
    
    if page < total_pages:
        navigation.append(
            InlineKeyboardButton(text="Вперед ➡️", callback_data=f"admin_users_page_{page + 1}")
        )
    
    if navigation:
        keyboard.append(navigation)
    
    # Добавляем кнопки возврата
    keyboard.append([
        InlineKeyboardButton(text="↩️ Назад в админку", callback_data="admin")
    ])
    
    keyboard.append([
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_searches_keyboard(searches, page=1, items_per_page=5):
    """
    Создает клавиатуру со списком поисковых запросов
    """
    keyboard = []
    
    # Пагинация
    total_pages = (len(searches) + items_per_page - 1) // items_per_page
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(searches))
    
    # Добавляем кнопки для каждого поиска на текущей странице
    for search in searches[start_idx:end_idx]:
        # Форматируем дату поиска
        search_date = datetime.datetime.fromisoformat(search["search_date"])
        formatted_date = search_date.strftime("%d.%m.%Y %H:%M")
        
        # Создаем текст кнопки
        button_text = f"🔍 {search['query']} - {formatted_date} ({search['font_count']} шрифтов)"
        
        keyboard.append([
            InlineKeyboardButton(text=button_text, callback_data=f"admin_search_{search['id']}")
        ])
    
    # Добавляем кнопки навигации
    navigation = []
    
    if page > 1:
        navigation.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_searches_page_{page - 1}")
        )
    
    navigation.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="admin_searches_page_info")
    )
    
    if page < total_pages:
        navigation.append(
            InlineKeyboardButton(text="Вперед ➡️", callback_data=f"admin_searches_page_{page + 1}")
        )
    
    if navigation:
        keyboard.append(navigation)
    
    # Добавляем кнопки возврата
    keyboard.append([
        InlineKeyboardButton(text="↩️ Назад в админку", callback_data="admin")
    ])
    
    keyboard.append([
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_user_info_keyboard(user_id):
    """
    Создает клавиатуру для просмотра информации о пользователе
    """
    keyboard = [
        [
            InlineKeyboardButton(text="📂 История поиска", callback_data=f"admin_user_history_{user_id}")
        ],
        [
            InlineKeyboardButton(text="👑 Сделать админом", callback_data=f"admin_make_admin_{user_id}")
        ],
        [
            InlineKeyboardButton(text="↩️ Назад к пользователям", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_local_fonts_keyboard(fonts, page=1, items_per_page=10):
    """
    Создает клавиатуру со списком локальных шрифтов (2 в ряд)
    """
    keyboard = []
    
    # Пагинация
    total_pages = (len(fonts) + items_per_page - 1) // items_per_page
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(fonts))
    
    # Добавляем кнопки для каждого шрифта на текущей странице (2 в ряд)
    current_row = []
    for i, font in enumerate(fonts[start_idx:end_idx], start=start_idx + 1):
        # Форматируем дату добавления
        added_date = datetime.datetime.fromisoformat(font["added_date"])
        formatted_date = added_date.strftime("%d.%m.%Y")
        
        # Создаем текст кнопки с номером
        doc_mark = "📄" if font["is_document"] else "🔤"
        button_text = f"{i}. {doc_mark} {font['font_name']}"
        
        # Добавляем кнопку в текущий ряд
        current_row.append(
            InlineKeyboardButton(text=button_text, callback_data=f"admin_font_{font['id']}")
        )
        
        # Если в ряду уже 2 кнопки или это последний шрифт, добавляем ряд в клавиатуру
        if len(current_row) == 2 or i == end_idx:
            keyboard.append(current_row)
            current_row = []
    
    # Добавляем кнопки навигации
    navigation = []
    
    if page > 1:
        navigation.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_local_fonts_page_{page - 1}")
        )
    
    navigation.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="admin_local_fonts_page_info")
    )
    
    if page < total_pages:
        navigation.append(
            InlineKeyboardButton(text="Вперед ➡️", callback_data=f"admin_local_fonts_page_{page + 1}")
        )
    
    if navigation:
        keyboard.append(navigation)
    
    # Добавляем кнопку поиска
    keyboard.append([
        InlineKeyboardButton(text="🔎 Поиск по базе", callback_data="admin_search_local_fonts")
    ])
    
    # Добавляем кнопки возврата
    keyboard.append([
        InlineKeyboardButton(text="↩️ Назад в админку", callback_data="admin")
    ])
    
    keyboard.append([
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_font_info_keyboard(font_id):
    """
    Создает клавиатуру для просмотра информации о шрифте
    """
    keyboard = [
        [
            InlineKeyboardButton(text="⬇️ Скачать шрифт", callback_data=f"admin_download_font_{font_id}")
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить информацию", callback_data=f"admin_refresh_font_{font_id}"),
            InlineKeyboardButton(text="📊 Статистика", callback_data=f"admin_font_stats_{font_id}")
        ],
        [
            InlineKeyboardButton(text="🗑️ Удалить из базы", callback_data=f"admin_delete_font_{font_id}")
        ],
        [
            InlineKeyboardButton(text="↩️ Назад к шрифтам", callback_data="admin_local_fonts")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 