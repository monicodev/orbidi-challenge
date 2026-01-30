from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # API Metadata
    PROJECT_NAME: str = "Orbidi API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str  # Mandatory in .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Load from .env file
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.sample"), 
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()