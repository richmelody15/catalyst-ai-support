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
    ADMIN_EMAIL: str = ""
    APP_URL: str = "http://localhost:8000"
    RATE_LIMIT_PER_MIN: int = 10
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    JWT_SECRET: str = ""
    # Push notification VAPID keys
    VAPID_PRIVATE_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    VAPID_CLAIM_EMAIL: str = "mailto:admin@catalystsignals.com"
    # Domain monitoring
    DOMAIN_NAME: str = "catalyst-signals.up.railway.app"

    class Config:
        env_file = ".env"

settings = Settings()
