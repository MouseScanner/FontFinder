﻿# FontFinder Bot

Telegram-бот для поиска и скачивания шрифтов. Позволяет находить шрифты по названию, просматривать информацию о них и скачивать файлы шрифтов.

## Возможности

- 🔍 Поиск шрифтов по названию
- 📋 Просмотр детальной информации о шрифтах
- ⬇️ Скачивание шрифтов в формате ZIP
- 📊 Статистика использования
- 📝 История поиска
- 🎨 Удобная навигация с пагинацией

## Скриншоты

### Главное меню
![image](https://github.com/user-attachments/assets/5dab06e9-fa65-4f16-839b-70f1e2cb8770)


### Поиск шрифтов
![image](https://github.com/user-attachments/assets/895a95bd-78fb-4f68-b0a9-bbe2f399c981)


### Результаты поиска
![image](https://github.com/user-attachments/assets/7242e547-56ac-48b2-a4f0-865e058801d5)

### Информация о шрифте
![image](https://github.com/user-attachments/assets/f8ccdc1c-c109-489a-ba05-90e955faa9c4)


## Установка

1. Клонируйте репозиторий:
```bash
git clone %репозиторий%
cd FontFinder
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` и добавьте ваш токен бота:
```env
BOT_TOKEN=your_telegram_bot_token_here
```

4. Запустите бота:
```bash
python main.py
```

## Структура проекта

```
FontFinder/
├── handlers/           # Обработчики команд и сообщений
│   ├── font_search.py  # Поиск и скачивание шрифтов
│   ├── statistics.py   # Статистика использования
│   └── history.py      # История поиска
├── keyboards/          # Клавиатуры для интерфейса
│   ├── main_menu.py    # Главное меню
│   └── font_search.py  # Клавиатуры поиска
├── services/           # Сервисы для работы с API
│   └── font_api_client.py
├── utils/              # Утилиты
│   └── pagination.py   # Пагинация результатов
├── database/           # Работа с базой данных
│   └── db_manager.py
├── fonts/              # Папка для скачанных шрифтов
├── main.py             # Точка входа
└── requirements.txt    # Зависимости
```

## Использование

1. Запустите бота командой `/start`
2. Выберите "🔍 Поиск шрифтов" в главном меню
3. Введите название шрифта для поиска
4. Просмотрите результаты и выберите интересующий шрифт
5. Нажмите "⬇️ Скачать" для загрузки шрифта

## Технологии

- **Python 3.8+** - основной язык программирования
- **aiogram 3.x** - фреймворк для Telegram ботов
- **aiohttp** - асинхронные HTTP запросы
- **aiofiles** - асинхронная работа с файлами
- **SQLite** - база данных для хранения истории и статистики

## Конфигурация

Бот использует следующие переменные окружения:

- `BOT_TOKEN` - токен Telegram бота (обязательно)
- `DATABASE_PATH` - путь к файлу базы данных (по умолчанию: `database.db`)
- `FONTS_DIR` - папка для сохранения шрифтов (по умолчанию: `fonts`)

## Лицензия

Этот проект распространяется под лицензией MIT. Подробности в файле [LICENSE](LICENSE).

## Поддержка

Если у вас возникли вопросы или проблемы, создайте issue в репозитории проекта.
