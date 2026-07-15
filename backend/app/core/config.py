import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./texergy.db")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")

settings = Settings()