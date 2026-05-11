import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ZAI_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    DATABASE_URL: str = "sqlite:///support.db"
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    PREMIUM_PRICE_ID: str = ""
    ADMIN_CHAT_ID: int = 0
    APP_URL: str = "http://localhost:8000"
    RATE_LIMIT_PER_MIN: int = 10

    class Config:
        env_file = ".env"

settings = Settings()
