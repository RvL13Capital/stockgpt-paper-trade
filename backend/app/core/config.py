from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets
import time

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    PROJECT_NAME: str = "StockGPT Paper Trade Terminal"
    APP_VERSION: str = "1.0.0"
    START_TIME: float = time.time()
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = "postgresql://stockgpt:stockgpt@localhost:5432/stockgpt_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # External APIs
    POLYGON_API_KEY: str = ""
    TIINGO_API_KEY: str = ""
    ALPHA_VANTAGE_API_KEY: str = ""
    FINNHUB_API_KEY: str = ""
    TWELVEDATA_API_KEY: str = ""
    FMP_API_KEY: str = ""
    
    # Email Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    
    # OTP Settings
    OTP_LENGTH: int = 4
    OTP_EXPIRE_MINUTES: int = 5
    OTP_DAILY_RESET_HOUR: int = 0  # UTC hour for daily OTP reset
    
    # Model Settings
    MODEL_VERSION: str = "v2.1.3"
    MODEL_PATH: str = "./models"
    
    # Feature Flags
    FEATURE_REAL_TIME_DATA: bool = True
    FEATURE_ADVANCED_CHARTS: bool = True
    FEATURE_MODEL_INSIGHTS: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()