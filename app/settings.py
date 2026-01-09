from typing import List, Optional
from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    # API Configuration
    APP_NAME: str = "QuantStock Pro API"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    API_VERSION: str = "v1.0"
    
    # Security
    GEMINI_API_KEY: str
    API_KEY: Optional[str] = None
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Model Configuration
    GEMINI_MODEL: str = "gemini-2.5-pro"
    GEMINI_TEMPERATURE: float = 0.2
    GEMINI_TOP_P: float = 0.95
    
    # Cache Configuration
    DATA_CACHE_TTL: int = 300
    AI_CACHE_TTL: int = 1800
    
    # Timeouts
    YFINANCE_TIMEOUT: int = 10
    AI_TIMEOUT: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="QUANTSTOCK_",
        extra="ignore"
    )

settings = Settings()