import sqlite3
from datetime import datetime

class LocalDB:
    def __init__(self, db_path="database/sentinel.db"):
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    module TEXT,
                    level TEXT,
                    description TEXT
                )
            """)

    def insert_log(self, module, level, description):
        """Inserta un registro de auditoría."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO logs (timestamp, module, level, description) VALUES (?, ?, ?, ?)",
                         (timestamp, module, level, description))