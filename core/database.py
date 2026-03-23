import sqlite3
from pathlib import Path

class ConfigurationDB:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

    def get(self, key: str, default: str = None) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def set(self, key: str, value: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))

    def get_all(self) -> dict[str, str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT key, value FROM settings")
            return {row[0]: row[1] for row in cursor.fetchall()}

    def load_from_env(self, env_data: dict[str, str]):
        """Bulk load settings from a dictionary (e.g., from .env) if not already in DB."""
        with sqlite3.connect(self.db_path) as conn:
            for key, value in env_data.items():
                conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))
