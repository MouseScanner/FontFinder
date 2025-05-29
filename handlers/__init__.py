from aiogram import Dispatcher
from .start import register_start_handlers
from .font_search import register_font_search_handlers
from .font_recognition import register_font_recognition_handlers
from .history import register_history_handlers
from .admin import register_admin_handlers
from .font_document import register_font_document_handlers

def register_all_handlers(dp: Dispatcher, db):
    register_start_handlers(dp, db)
    register_font_search_handlers(dp, db)
    register_font_recognition_handlers(dp, db)
    register_history_handlers(dp, db)
    register_admin_handlers(dp, db)
    register_font_document_handlers(dp, db) 