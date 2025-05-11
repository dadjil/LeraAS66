import sqlite3
import datetime


class DataStorageManager:
    def __init__(self, storage_name="television_data.db"):
        self.storage_name = storage_name
        self._initialize_storage()

    def _initialize_storage(self):
        with sqlite3.connect(self.storage_name) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ScrapingSessions(
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    items_count INTEGER NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS TelevisionItems(
                    model_name TEXT NOT NULL,
                    price_value INTEGER NOT NULL,
                    session_ref INTEGER NOT NULL
                )
            ''')
            connection.commit()

    def store_scraped_data(self, scraped_items):
        with sqlite3.connect(self.storage_name) as connection:
            cursor = connection.cursor()
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                "INSERT INTO ScrapingSessions (timestamp, items_count) VALUES (?, ?)",
                (current_time, len(scraped_items))
            )
            session_id = cursor.lastrowid

            for model, price in scraped_items.items():
                cursor.execute(
                    "INSERT INTO TelevisionItems VALUES (?, ?, ?)",
                    (model, price, session_id)
                )
            connection.commit()

    def fetch_all_sessions(self):
        with sqlite3.connect(self.storage_name) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM ScrapingSessions")
            return cursor.fetchall()

    def fetch_session_items(self, session_id):
        with sqlite3.connect(self.storage_name) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT * FROM TelevisionItems WHERE session_ref = ?",
                (session_id,)
            )
            return cursor.fetchall()

    def clear_storage(self):
        with sqlite3.connect(self.storage_name) as connection:
            cursor = connection.cursor()
            cursor.execute("DROP TABLE IF EXISTS ScrapingSessions")
            cursor.execute("DROP TABLE IF EXISTS TelevisionItems")
            self._initialize_storage()
            connection.commit()