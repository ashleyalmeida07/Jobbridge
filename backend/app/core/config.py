import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "JobBridge"
    TARGET_COUNTRY: str = "US"  # configurable via env
    
    # Database (Neon DB)
    DATABASE_URL: str
    
    # Security / Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    
    # Fernet for encrypting Gmail token
    FERNET_KEY: str
    
    # Telegram 
    TELEGRAM_BOT_TOKEN: str = ""
    
    # Frontend URL for CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # Scraper config
    SCRAPER_DELAY_SECONDS: int = 5
    USER_AGENT: str = "JobBridge Scraper/1.0"
    SCRAPER_ADMIN_KEY: str = "secret-admin-key"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

settings = Settings()
