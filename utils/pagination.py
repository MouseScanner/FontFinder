from config import FONTS_PER_PAGE

def paginate_results(results, page):
    """
    Разбивает результаты поиска на страницы
    """
    start_idx = (page - 1) * FONTS_PER_PAGE
    end_idx = start_idx + FONTS_PER_PAGE
    
    return results[start_idx:end_idx] 