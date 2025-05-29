import aiohttp
from config import FONT_API_URL

class FontApiClient:
    async def search_fonts(self, query):
        """
        Поиск шрифтов по запросу через API
        """
        async with aiohttp.ClientSession() as session:
            params = {"query": query}
            async with session.get(FONT_API_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("suggestions", [])
                return [] 