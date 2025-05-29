import sqlite3
import datetime
from datetime import datetime
import os
import logging
from typing import List, Dict, Any, Optional, Tuple

class Database:
    def __init__(self, db_file):
        self.db_path = db_file
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """Создание необходимых таблиц в базе данных"""
        # Таблица пользователей
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            is_admin INTEGER DEFAULT 0,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Таблица истории поиска
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query TEXT,
            search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        """)
        
        # Таблица найденных шрифтов
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS found_fonts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_id INTEGER,
            font_name TEXT,
            font_slug TEXT,
            designer TEXT,
            manufacturer TEXT,
            user_fullname TEXT,
            url TEXT,
            download_url TEXT,
            FOREIGN KEY (search_id) REFERENCES search_history (id)
        )
        """)
        
        # Таблица локальных шрифтов (кеш)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS local_fonts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            font_name TEXT,
            font_slug TEXT,
            designer TEXT,
            manufacturer TEXT,
            user_fullname TEXT,
            url TEXT,
            download_url TEXT,
            file_path TEXT,
            added_by_user_id INTEGER,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            download_count INTEGER DEFAULT 0,
            is_document BOOLEAN DEFAULT 0,
            FOREIGN KEY (added_by_user_id) REFERENCES users (user_id)
        )
        """)
        
        # Таблица статистики по локальным шрифтам
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS font_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_fonts INTEGER DEFAULT 0,
            total_documents INTEGER DEFAULT 0,
            local_searches INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Таблица логов поиска в локальной базе
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS local_search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query TEXT,
            results_count INTEGER,
            search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        """)
        
        # Вставляем начальную запись в таблицу статистики, если она пуста
        self.cursor.execute("SELECT COUNT(*) FROM font_stats")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("INSERT INTO font_stats (total_fonts, total_documents, local_searches) VALUES (0, 0, 0)")
        
        self.connection.commit()
    
    def add_user(self, user_id: int, username: str, full_name: str) -> None:
        """Добавление нового пользователя или обновление информации о существующем"""
        self.cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name)
        )
        self.connection.commit()
    
    def set_admin(self, user_id: int, is_admin: bool = True) -> None:
        """Установка или снятие прав администратора"""
        self.cursor.execute(
            "UPDATE users SET is_admin = ? WHERE user_id = ?",
            (1 if is_admin else 0, user_id)
        )
        self.connection.commit()
    
    def is_admin(self, user_id):
        """Проверка, является ли пользователь администратором"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            
            return bool(result and result[0])
        except Exception as e:
            logging.error(f"Ошибка при проверке статуса администратора: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def add_search_query(self, user_id: int, query: str) -> int:
        """Добавление поискового запроса в историю"""
        self.cursor.execute(
            "INSERT INTO search_history (user_id, query) VALUES (?, ?)",
            (user_id, query)
        )
        self.connection.commit()
        return self.cursor.lastrowid
    
    def add_found_font(self, search_id: int, font_data: Dict[str, Any]) -> None:
        """Добавление найденного шрифта в базу данных"""
        data = font_data["data"]
        download_url = f"https://font.download/dl/font/{data['slug']}.zip"
        
        self.cursor.execute(
            """
            INSERT INTO found_fonts 
            (search_id, font_name, font_slug, designer, manufacturer, user_fullname, url, download_url) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                search_id,
                data.get("font_name", ""),
                data.get("slug", ""),
                data.get("designer", ""),
                data.get("manufacturer", ""),
                data.get("user_fullname", ""),
                data.get("url", ""),
                download_url
            )
        )
        self.connection.commit()
        
        # Автоматически добавляем шрифт в локальную базу, если его там еще нет
        self._add_to_local_fonts(data, search_id)
    
    def _add_to_local_fonts(self, font_data: Dict[str, Any], search_id: int = None) -> None:
        """Внутренний метод для добавления шрифта в локальную базу"""
        # Проверяем, есть ли уже такой шрифт в базе
        self.cursor.execute(
            "SELECT id FROM local_fonts WHERE font_slug = ?",
            (font_data.get("slug", ""),)
        )
        
        if self.cursor.fetchone() is None:
            # Получаем информацию о пользователе, который выполнил поиск
            user_id = None
            if search_id:
                self.cursor.execute(
                    "SELECT user_id FROM search_history WHERE id = ?",
                    (search_id,)
                )
                result = self.cursor.fetchone()
                if result:
                    user_id = result[0]
            
            download_url = f"https://font.download/dl/font/{font_data.get('slug', '')}.zip"
            
            # Добавляем шрифт в локальную базу
            self.cursor.execute(
                """
                INSERT INTO local_fonts 
                (font_name, font_slug, designer, manufacturer, user_fullname, url, download_url, added_by_user_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    font_data.get("font_name", ""),
                    font_data.get("slug", ""),
                    font_data.get("designer", ""),
                    font_data.get("manufacturer", ""),
                    font_data.get("user_fullname", ""),
                    font_data.get("url", ""),
                    download_url,
                    user_id
                )
            )
            
            # Обновляем статистику
            self.cursor.execute(
                """
                UPDATE font_stats 
                SET total_fonts = total_fonts + 1, 
                    last_updated = CURRENT_TIMESTAMP
                """
            )
            
            self.connection.commit()
    
    def add_font_document(self, user_id: int, font_data: Dict[str, Any], file_path: str) -> None:
        """Добавление шрифта, отправленного как документ"""
        download_url = f"https://font.download/dl/font/{font_data.get('slug', '')}.zip"
        
        self.cursor.execute(
            """
            INSERT INTO local_fonts 
            (font_name, font_slug, designer, manufacturer, user_fullname, url, download_url, 
             file_path, added_by_user_id, is_document) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                font_data.get("font_name", ""),
                font_data.get("slug", ""),
                font_data.get("designer", ""),
                font_data.get("manufacturer", ""),
                font_data.get("user_fullname", ""),
                font_data.get("url", ""),
                download_url,
                file_path,
                user_id
            )
        )
        
        # Обновляем статистику
        self.cursor.execute(
            """
            UPDATE font_stats 
            SET total_fonts = total_fonts + 1, 
                total_documents = total_documents + 1,
                last_updated = CURRENT_TIMESTAMP
            """
        )
        
        self.connection.commit()
    
    def increment_font_download_count(self, font_id: int) -> None:
        """Увеличение счетчика загрузок шрифта"""
        self.cursor.execute(
            "UPDATE local_fonts SET download_count = download_count + 1 WHERE id = ?",
            (font_id,)
        )
        self.connection.commit()
    
    def get_local_fonts(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Получение списка локальных шрифтов"""
        self.cursor.execute(
            """
            SELECT lf.id, lf.font_name, lf.font_slug, lf.designer, lf.manufacturer, 
                   lf.user_fullname, lf.url, lf.download_url, lf.file_path, 
                   lf.added_date, lf.download_count, lf.is_document,
                   u.user_id, u.username, u.full_name
            FROM local_fonts lf
            LEFT JOIN users u ON lf.added_by_user_id = u.user_id
            ORDER BY lf.added_date DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )
        
        fonts = []
        for row in self.cursor.fetchall():
            (font_id, font_name, font_slug, designer, manufacturer, 
             user_fullname, url, download_url, file_path, 
             added_date, download_count, is_document,
             user_id, username, full_name) = row
            
            fonts.append({
                "id": font_id,
                "font_name": font_name,
                "font_slug": font_slug,
                "designer": designer,
                "manufacturer": manufacturer,
                "user_fullname": user_fullname,
                "url": url,
                "download_url": download_url,
                "file_path": file_path,
                "added_date": added_date,
                "download_count": download_count,
                "is_document": bool(is_document),
                "added_by": {
                    "user_id": user_id,
                    "username": username,
                    "full_name": full_name
                } if user_id else None
            })
        
        return fonts
    
    def log_local_search(self, user_id: int, query: str, results_count: int) -> bool:
        """Логирование поиска в локальной базе"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Записываем информацию о поиске
            search_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                'INSERT INTO local_search_logs (user_id, query, results_count, search_date) VALUES (?, ?, ?, ?)',
                (user_id, query, results_count, search_date)
            )
            
            # Обновляем счетчик локальных поисков
            cursor.execute('UPDATE font_stats SET local_searches = local_searches + 1 WHERE id = 1')
            
            conn.commit()
            logging.info(f"Поиск пользователя {user_id} по запросу '{query}' успешно залогирован")
            
            return True
        except Exception as e:
            logging.error(f"Ошибка при логировании поиска: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_local_search_stats(self):
        """Получение статистики по локальным поискам"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем общее количество поисков
            cursor.execute('SELECT COUNT(*) FROM local_search_logs')
            total_searches = cursor.fetchone()[0]
            
            # Получаем количество уникальных пользователей
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM local_search_logs')
            unique_users = cursor.fetchone()[0]
            
            # Получаем количество уникальных запросов
            cursor.execute('SELECT COUNT(DISTINCT query) FROM local_search_logs')
            unique_queries = cursor.fetchone()[0]
            
            # Получаем среднее количество результатов
            cursor.execute('SELECT AVG(results_count) FROM local_search_logs')
            avg_results = cursor.fetchone()[0] or 0
            
            # Получаем топ-5 популярных запросов
            cursor.execute('''
                SELECT query, COUNT(*) as count 
                FROM local_search_logs 
                GROUP BY query 
                ORDER BY count DESC 
                LIMIT 5
            ''')
            top_queries = cursor.fetchall()
            
            return {
                "total_searches": total_searches,
                "unique_users": unique_users,
                "unique_queries": unique_queries,
                "avg_results": avg_results,
                "top_queries": top_queries
            }
        except Exception as e:
            logging.error(f"Ошибка при получении статистики локальных поисков: {e}")
            return {
                "total_searches": 0,
                "unique_users": 0,
                "unique_queries": 0,
                "avg_results": 0,
                "top_queries": []
            }
        finally:
            if conn:
                conn.close()
    
    def get_font_stats(self):
        """Получение статистики по шрифтам"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем статистику из таблицы font_stats
            cursor.execute('SELECT * FROM font_stats WHERE id = 1')
            row = cursor.fetchone()
            
            if row:
                return {
                    "total_fonts": row[1],
                    "total_downloads": row[2],
                    "document_count": row[3],
                    "local_searches": row[4]
                }
            else:
                return {
                    "total_fonts": 0,
                    "total_downloads": 0,
                    "document_count": 0,
                    "local_searches": 0
                }
        except Exception as e:
            logging.error(f"Ошибка при получении статистики по шрифтам: {e}")
            return {
                "total_fonts": 0,
                "total_downloads": 0,
                "document_count": 0,
                "local_searches": 0
            }
        finally:
            if conn:
                conn.close()
    
    def search_local_fonts(self, query):
        """Поиск шрифтов в локальной базе данных"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Выполняем поиск по имени шрифта или slug
            search_query = f"%{query}%"
            cursor.execute('''
                SELECT * FROM local_fonts 
                WHERE font_name LIKE ? OR font_slug LIKE ?
                ORDER BY download_count DESC
            ''', (search_query, search_query))
            
            results = [dict(row) for row in cursor.fetchall()]
            
            logging.info(f"Найдено {len(results)} шрифтов в локальной базе по запросу '{query}'")
            return results
        except Exception as e:
            logging.error(f"Ошибка при поиске в локальной базе: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def _calculate_relevance(self, query: str, font_name: str, designer: str, manufacturer: str) -> float:
        """Вычисляет релевантность шрифта для поискового запроса"""
        query = query.lower()
        font_name = font_name.lower()
        designer = (designer or "").lower()
        manufacturer = (manufacturer or "").lower()
        
        relevance = 0.0
        
        # Точное совпадение с названием шрифта
        if query == font_name:
            relevance += 10.0
        # Название шрифта начинается с запроса
        elif font_name.startswith(query):
            relevance += 5.0
        # Запрос содержится в названии шрифта
        elif query in font_name:
            relevance += 3.0
        
        # Проверяем совпадения по отдельным словам
        query_words = query.split()
        font_name_words = font_name.split()
        
        # Совпадение слов в названии
        for word in query_words:
            if word in font_name_words:
                relevance += 2.0
            elif any(word in name_word for name_word in font_name_words):
                relevance += 1.0
        
        # Совпадение с дизайнером
        if query in designer:
            relevance += 1.5
        
        # Совпадение с производителем
        if query in manufacturer:
            relevance += 1.0
        
        return relevance
    
    def delete_local_font(self, font_id: int) -> bool:
        """Удаление шрифта из локальной базы"""
        # Проверяем, существует ли шрифт
        self.cursor.execute("SELECT file_path, is_document FROM local_fonts WHERE id = ?", (font_id,))
        result = self.cursor.fetchone()
        if not result:
            return False
        
        file_path, is_document = result
        
        # Удаляем файл, если он существует и является документом
        if file_path and is_document and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass  # Игнорируем ошибки при удалении файла
        
        # Обновляем статистику
        self.cursor.execute(
            """
            UPDATE font_stats 
            SET total_fonts = total_fonts - 1,
                total_documents = CASE WHEN ? THEN total_documents - 1 ELSE total_documents END,
                last_updated = CURRENT_TIMESTAMP
            """,
            (bool(is_document),)
        )
        
        # Удаляем запись из базы
        self.cursor.execute("DELETE FROM local_fonts WHERE id = ?", (font_id,))
        self.connection.commit()
        
        return True
    
    def get_user_search_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение истории поиска пользователя"""
        self.cursor.execute(
            """
            SELECT id, query, search_date
            FROM search_history
            WHERE user_id = ?
            ORDER BY search_date DESC
            """,
            (user_id,)
        )
        
        history = []
        for row in self.cursor.fetchall():
            search_id, query, search_date = row
            
            # Получаем найденные шрифты для этого поиска
            self.cursor.execute(
                """
                SELECT font_name, font_slug, designer, manufacturer, user_fullname, url, download_url
                FROM found_fonts
                WHERE search_id = ?
                """,
                (search_id,)
            )
            
            fonts = []
            for font_row in self.cursor.fetchall():
                font_name, font_slug, designer, manufacturer, user_fullname, url, download_url = font_row
                fonts.append({
                    "font_name": font_name,
                    "font_slug": font_slug,
                    "designer": designer,
                    "manufacturer": manufacturer,
                    "user_fullname": user_fullname,
                    "url": url,
                    "download_url": download_url
                })
            
            history.append({
                "id": search_id,
                "query": query,
                "search_date": search_date,
                "fonts": fonts
            })
        
        return history
    
    def get_search_details(self, search_id: int) -> Optional[Dict[str, Any]]:
        """Получение подробной информации о конкретном поиске"""
        self.cursor.execute(
            """
            SELECT sh.id, sh.query, sh.search_date, u.user_id, u.username, u.full_name
            FROM search_history sh
            JOIN users u ON sh.user_id = u.user_id
            WHERE sh.id = ?
            """,
            (search_id,)
        )
        
        row = self.cursor.fetchone()
        if not row:
            return None
        
        search_id, query, search_date, user_id, username, full_name = row
        
        # Получаем найденные шрифты для этого поиска
        self.cursor.execute(
            """
            SELECT font_name, font_slug, designer, manufacturer, user_fullname, url, download_url
            FROM found_fonts
            WHERE search_id = ?
            """,
            (search_id,)
        )
        
        fonts = []
        for font_row in self.cursor.fetchall():
            font_name, font_slug, designer, manufacturer, user_fullname, url, download_url = font_row
            fonts.append({
                "font_name": font_name,
                "font_slug": font_slug,
                "designer": designer,
                "manufacturer": manufacturer,
                "user_fullname": user_fullname,
                "url": url,
                "download_url": download_url
            })
        
        return {
            "id": search_id,
            "query": query,
            "search_date": search_date,
            "user": {
                "user_id": user_id,
                "username": username,
                "full_name": full_name
            },
            "fonts": fonts
        }
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получение списка всех пользователей"""
        self.cursor.execute(
            """
            SELECT user_id, username, full_name, is_admin, registration_date
            FROM users
            ORDER BY registration_date DESC
            """
        )
        
        users = []
        for row in self.cursor.fetchall():
            user_id, username, full_name, is_admin, registration_date = row
            
            # Получаем количество поисков для этого пользователя
            self.cursor.execute(
                "SELECT COUNT(*) FROM search_history WHERE user_id = ?",
                (user_id,)
            )
            search_count = self.cursor.fetchone()[0]
            
            users.append({
                "user_id": user_id,
                "username": username,
                "full_name": full_name,
                "is_admin": bool(is_admin),
                "registration_date": registration_date,
                "search_count": search_count
            })
        
        return users
    
    def get_all_searches(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение списка всех поисков"""
        self.cursor.execute(
            """
            SELECT sh.id, sh.query, sh.search_date, u.user_id, u.username, u.full_name
            FROM search_history sh
            JOIN users u ON sh.user_id = u.user_id
            ORDER BY sh.search_date DESC
            LIMIT ?
            """,
            (limit,)
        )
        
        searches = []
        for row in self.cursor.fetchall():
            search_id, query, search_date, user_id, username, full_name = row
            
            # Получаем количество найденных шрифтов для этого поиска
            self.cursor.execute(
                "SELECT COUNT(*) FROM found_fonts WHERE search_id = ?",
                (search_id,)
            )
            font_count = self.cursor.fetchone()[0]
            
            searches.append({
                "id": search_id,
                "query": query,
                "search_date": search_date,
                "user": {
                    "user_id": user_id,
                    "username": username,
                    "full_name": full_name
                },
                "font_count": font_count
            })
        
        return searches
    
    def close(self):
        """Закрытие соединения с базой данных"""
        self.connection.close()

    def add_local_font(self, font_name, font_slug, file_path, designer=None, manufacturer=None, user_fullname=None, url=None):
        """Добавление шрифта в локальную базу данных"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем, есть ли уже такой шрифт в базе
            cursor.execute('SELECT id FROM local_fonts WHERE font_slug = ?', (font_slug,))
            existing_font = cursor.fetchone()
            
            added_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if existing_font:
                # Если шрифт уже есть, обновляем информацию
                cursor.execute('''
                    UPDATE local_fonts 
                    SET file_path = ?, designer = ?, manufacturer = ?, user_fullname = ?, url = ?
                    WHERE font_slug = ?
                ''', (file_path, designer, manufacturer, user_fullname, url, font_slug))
                
                font_id = existing_font[0]
                logging.info(f"Обновлена информация о шрифте {font_name} (slug: {font_slug}) в локальной базе")
            else:
                # Если шрифта нет, добавляем новый
                cursor.execute('''
                    INSERT INTO local_fonts 
                    (font_name, font_slug, file_path, designer, manufacturer, user_fullname, url, added_date, download_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                ''', (font_name, font_slug, file_path, designer, manufacturer, user_fullname, url, added_date))
                
                font_id = cursor.lastrowid
                
                # Обновляем счетчик шрифтов в статистике
                cursor.execute('UPDATE font_stats SET total_fonts = total_fonts + 1 WHERE id = 1')
                
                logging.info(f"Добавлен новый шрифт {font_name} (slug: {font_slug}) в локальную базу")
            
            conn.commit()
            return font_id
        except Exception as e:
            logging.error(f"Ошибка при добавлении шрифта в локальную базу: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_local_font_by_slug(self, font_slug):
        """Получение информации о шрифте из локальной базы по slug"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM local_fonts WHERE font_slug = ?', (font_slug,))
            font = cursor.fetchone()
            
            if font:
                return dict(font)
            else:
                return None
        except Exception as e:
            logging.error(f"Ошибка при получении информации о шрифте: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def increment_font_downloads(self, font_slug):
        """Увеличение счетчика загрузок шрифта"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Обновляем счетчик загрузок для конкретного шрифта
            cursor.execute('UPDATE local_fonts SET download_count = download_count + 1 WHERE font_slug = ?', (font_slug,))
            
            # Обновляем общий счетчик загрузок
            cursor.execute('UPDATE font_stats SET total_downloads = total_downloads + 1 WHERE id = 1')
            
            conn.commit()
            logging.info(f"Увеличен счетчик загрузок для шрифта {font_slug}")
            return True
        except Exception as e:
            logging.error(f"Ошибка при обновлении счетчика загрузок: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_user_count(self):
        """Получение количества пользователей"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            logging.error(f"Ошибка при получении количества пользователей: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    def get_admin_count(self):
        """Получение количества администраторов"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = 1')
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            logging.error(f"Ошибка при получении количества администраторов: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    def get_search_count(self):
        """Получение количества поисков"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM search_history')
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            logging.error(f"Ошибка при получении количества поисков: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    def get_font_count(self):
        """Получение количества шрифтов в локальной базе"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM local_fonts')
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            logging.error(f"Ошибка при получении количества шрифтов: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    def get_document_count(self):
        """Получение количества документов"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT document_count FROM font_stats WHERE id = 1')
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            logging.error(f"Ошибка при получении количества документов: {e}")
            return 0
        finally:
            if conn:
                conn.close() 