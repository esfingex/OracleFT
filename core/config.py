import os
from pathlib import Path
from dotenv import load_dotenv, set_key, dotenv_values
from .database import ConfigurationDB

class ConfigManager:
    def __init__(self, env_path: str | Path = "oci.env"):
        self.base_path = Path(__file__).parent.parent
        self.env_path = self.base_path / env_path
        self.db_path = self.base_path / "oracle_ft.db"
        
        # Initialize Database
        self.db = ConfigurationDB(self.db_path)
        
        # Initial migration: Load oci.env into DB on first run
        if self.env_path.exists():
            env_data = dotenv_values(self.env_path)
            # Filter out None values and only take strings
            clean_data = {k: v for k, v in env_data.items() if v is not None}
            self.db.load_from_env(clean_data)
        
        self.load()

    def load(self):
        # Sync DB back to Environment variables for the rest of the app
        all_settings = self.db.get_all()
        for k, v in all_settings.items():
            os.environ[k] = str(v)
        
    def get(self, key: str, default: str | None = None) -> str | None:
        # DB is source of truth, then OS env
        val = self.db.get(key)
        if val is not None:
            return val
        return os.getenv(key, default)

    def set(self, key: str, value: str | int | bool):
        # Update DB (Source of Truth)
        self.db.set(key, str(value).strip())
        os.environ[key] = str(value).strip()
        
        # Sync with .env for visibility
        if not self.env_path.exists():
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.env_path.touch()
        set_key(str(self.env_path), key, str(value).strip())

    def get_all(self) -> dict[str, str]:
        return self.db.get_all()

config = ConfigManager()
