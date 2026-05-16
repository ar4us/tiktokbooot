import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    MAX_FILE_MB = int(os.getenv("MAX_FILE_MB", 50))
    TEMP_DIR = os.getenv("TEMP_DIR", "temp")

    @classmethod
    def validate(cls):
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN must be set in .env")
        
        # Ensure temp directory exists
        if not os.path.exists(cls.TEMP_DIR):
            os.makedirs(cls.TEMP_DIR)
