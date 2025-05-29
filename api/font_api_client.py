import aiohttp
import logging
import os
import uuid
import aiofiles
from config import FONTS_DIR

class FontApiClient:
    def __init__(self, base_url="https://font.download/api"):
        self.base_url = base_url
        self.session = None

    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def search_fonts(self, query, limit=10):
        """Поиск шрифтов по запросу"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/search?q={query}&limit={limit}"
            
            logging.info(f"Выполняется API запрос: {url}")
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logging.info(f"Получено {len(data)} результатов поиска")
                    return data
                else:
                    logging.error(f"Ошибка API: {response.status}")
                    return []
        except Exception as e:
            logging.error(f"Ошибка при поиске шрифтов: {e}")
            return []

    async def download_font(self, font_slug):
        """Скачивание шрифта по slug"""
        try:
            # Проверяем, существует ли директория для шрифтов
            os.makedirs(FONTS_DIR, exist_ok=True)
            
            # Формируем URL для скачивания
            download_url = f"https://font.download/dl/font/{font_slug}.ttf"
            fallback_url = f"https://font.download/dl/font/{font_slug}.zip"
            
            # Генерируем имя файла
            filename = f"{font_slug}_{uuid.uuid4()}.ttf"
            file_path = os.path.join(FONTS_DIR, filename)
            
            logging.info(f"Скачивание шрифта: {download_url}")
            
            session = await self._get_session()
            
            # Пробуем скачать TTF файл
            async with session.get(download_url) as response:
                if response.status == 200:
                    # Сохраняем файл
                    async with aiofiles.open(file_path, 'wb') as f:
                        await f.write(await response.read())
                    
                    logging.info(f"Шрифт успешно скачан и сохранен: {file_path}")
                    return file_path
                else:
                    logging.warning(f"Не удалось скачать TTF файл. Статус: {response.status}. Пробуем ZIP.")
                    
                    # Если TTF не доступен, пробуем скачать ZIP
                    zip_filename = f"{font_slug}_{uuid.uuid4()}.zip"
                    zip_file_path = os.path.join(FONTS_DIR, zip_filename)
                    
                    async with session.get(fallback_url) as zip_response:
                        if zip_response.status == 200:
                            # Сохраняем ZIP файл
                            async with aiofiles.open(zip_file_path, 'wb') as f:
                                await f.write(await zip_response.read())
                            
                            logging.info(f"ZIP архив успешно скачан и сохранен: {zip_file_path}")
                            
                            # Здесь можно добавить распаковку ZIP и извлечение TTF файла
                            # Но для простоты просто возвращаем путь к ZIP файлу
                            return zip_file_path
                        else:
                            logging.error(f"Не удалось скачать шрифт. Статус: {zip_response.status}")
                            return None
        except Exception as e:
            logging.error(f"Ошибка при скачивании шрифта: {e}")
            return None

    async def close(self):
        """Закрытие сессии"""
        if self.session and not self.session.closed:
            await self.session.close()
            logging.info("Сессия API закрыта")

font_api_client = FontApiClient() 