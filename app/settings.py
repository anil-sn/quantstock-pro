from typing import List, Optional, Dict
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
    API_VERSION: str = "v7.3.0-Institutional"
    
    # Security
    GEMINI_API_KEY: str
    TAVILY_API_KEY: Optional[str] = None
    GOOGLE_SEARCH_API_KEY: Optional[str] = None
    GOOGLE_CSE_ID: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    FINNHUB_API_KEY: Optional[str] = None
    WT_KEY: Optional[str] = None
    API_KEY: Optional[str] = None
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    SENTRY_DSN: Optional[str] = None
    
    # Redis Configuration
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Model Configuration
    GEMINI_MODEL: str = "gemini-2.5-pro"
    GEMINI_TEMPERATURE: float = 0.2
    GEMINI_TOP_P: float = 0.95
    
    # Cache Configuration
    DATA_CACHE_TTL: int = 3600  # 1 hour per production recommendation
    AI_CACHE_TTL: int = 1800
    CACHE_MAXSIZE: int = 128
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100  # per minute
    RATE_LIMIT_PERIOD: int = 60
    
    # Timeouts
    YFINANCE_TIMEOUT: int = 10
    AI_TIMEOUT: int = 60

    # Risk Parameters
    MAX_POSITION_PCT: float = 5.0
    MAX_CAPITAL_RISK_PCT: float = 0.5
    CONFIDENCE_THRESHOLD: float = 70.0
    DEGRADED_CONFIDENCE_PENALTY: float = 20.0
    DEGRADED_POSITION_CAP: float = 0.5

    # Trading Rules
    ADX_TREND_THRESHOLD: float = 15.0
    INSIDER_SELL_THRESHOLD: int = 3
    INSIDER_SELL_WINDOW_DAYS: int = 90
    
    # Validation Rules
    CCI_ZSCORE_THRESHOLD: float = 3.0
    VOLUME_LIQUIDITY_BASELINE: float = 100000.0

    # Fundamental Inference Thresholds
    PE_VALUE_THRESHOLD: float = 15.0
    PE_PREMIUM_THRESHOLD: float = 30.0
    GROWTH_EXPLOSIVE_THRESHOLD: float = 0.25
    GROWTH_STEADY_THRESHOLD: float = 0.10
    HEALTH_LIQUIDITY_RATIO: float = 1.5
    HEALTH_DEBT_CAP: float = 0.5
    EARNINGS_QUALITY_THRESHOLD: float = 1.0
    INSTITUTIONAL_OWNERSHIP_HIGH: float = 0.70
    SMALL_CAP_REVENUE_THRESHOLD: int = 500000000

    # Analysis Parameters
    MAX_COMPARABLE_PEERS: int = 5
    DEFAULT_DISCOUNT_RATE: float = 0.10
    DEFAULT_TERMINAL_GROWTH: float = 0.03
    MINIMUM_TERMINAL_GROWTH: float = 0.02
    MAXIMUM_TERMINAL_GROWTH: float = 0.04
    TV_DOMINANCE_WARNING_THRESHOLD: float = 0.70

    # Valuation Defaults
    TECH_TARGET_FCF_MARGIN: float = 0.20
    INDUSTRIAL_TARGET_FCF_MARGIN: float = 0.15
    FINANCIAL_TARGET_FCF_MARGIN: float = 0.25
    TV_DOMINANCE_WARNING: float = 0.70
    
    # Safety Bounds
    MAX_GROWTH_ASSUMPTION: float = 0.30  # 30% max
    MIN_FCF_MARGIN: float = 0.05
    MAX_TERMINAL_DOMINANCE: float = 0.70  # Audit requirement: Flag if >70%

    # Sector-Specific Benchmarks (Enhanced)
    SECTOR_BENCHMARKS: Dict[str, Dict[str, float]] = {
        "Technology": {
            "pe": 25.0,
            "de": 0.5,
            "margin": 0.15,
            "growth": 0.20,
            "fcf_margin": 0.15, # Standardized
            "roe": 0.15
        },
        "Healthcare": {
            "pe": 20.0,
            "de": 0.6,
            "margin": 0.12,
            "growth": 0.15,
            "fcf_margin": 0.12,
            "roe": 0.12
        },
        "Financial Services": {
            "pe": 12.0,
            "de": 1.5,
            "margin": 0.30,
            "growth": 0.08,
            "fcf_margin": 0.20,
            "roe": 0.12
        },
        "Energy": {
            "pe": 10.0,
            "de": 0.8,
            "margin": 0.10,
            "growth": 0.05,
            "fcf_margin": 0.15,
            "roe": 0.10
        },
        "Default": {
            "pe": 20.0,
            "de": 0.7,
            "margin": 0.10,
            "growth": 0.10,
            "fcf_margin": 0.10,
            "roe": 0.10
        }
    }

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="QUANTSTOCK_",
        extra="ignore"
    )

settings = Settings()
