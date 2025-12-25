from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

class Config(BaseSettings):
    # Database settings
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
    
    # Security settings
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application settings
    api_version: str = os.getenv("API_VERSION", "v1")
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    SQL_ECHO: bool = os.getenv("SQL_ECHO", "false").lower() == "true"
    
    # CORS settings
    allowed_origins: List[str] = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # SEO API Configuration
    SEMRUSH_API_KEY: str = os.getenv("SEMRUSH_API_KEY", "")
    SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")
    
    # Web scraper settings
    SCRAPER_USER_AGENT: str = os.getenv("SCRAPER_USER_AGENT", "Mozilla/5.0 (compatible; OnSideBot/1.0; +https://onside.ai)")
    SCRAPER_TIMEOUT: int = int(os.getenv("SCRAPER_TIMEOUT", "30"))
    SCRAPER_MAX_RETRIES: int = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
    SCRAPER_RETRY_DELAY: int = int(os.getenv("SCRAPER_RETRY_DELAY", "5"))
    
    # SEO Service Configuration
    SEO_DEFAULT_MARKET: str = os.getenv("SEO_DEFAULT_MARKET", "us")
    SEO_DEFAULT_LANGUAGE: str = os.getenv("SEO_DEFAULT_LANGUAGE", "en")
    SEO_API_RATE_LIMIT: int = int(os.getenv("SEO_API_RATE_LIMIT", "5"))
    
    # New API Configurations
    MELTWATER_API_KEY: str = os.getenv("MELTWATER_API_KEY", "")
    MELTWATER_API_URL: str = os.getenv("MELTWATER_API_URL", "https://api.meltwater.com/v3")
    MELTWATER_API_RATE_LIMIT: int = int(os.getenv("MELTWATER_API_RATE_LIMIT", "100"))

    # WhoAPI Configuration
    WHOAPI_API_KEY: str = os.getenv("WHOAPI_API_KEY", "")
    WHOAPI_BASE_URL: str = os.getenv("WHOAPI_BASE_URL", "https://api.whoapi.com")
    WHOAPI_TIMEOUT: int = int(os.getenv("WHOAPI_TIMEOUT", "30"))
    WHOAPI_MAX_RETRIES: int = int(os.getenv("WHOAPI_MAX_RETRIES", "3"))
    
    # Real-time Analytics Configuration
    REALTIME_ANALYTICS_ENDPOINT: str = os.getenv("REALTIME_ANALYTICS_ENDPOINT", "")
    REALTIME_ANALYTICS_KEY: str = os.getenv("REALTIME_ANALYTICS_KEY", "")
    ANALYTICS_UPDATE_INTERVAL: int = int(os.getenv("ANALYTICS_UPDATE_INTERVAL", "300"))  # 5 minutes
    
    # Temporal Analysis Configuration
    MAX_CONTENT_AGE_DAYS: int = int(os.getenv("MAX_CONTENT_AGE_DAYS", "365"))
    TREND_ANALYSIS_WINDOW: int = int(os.getenv("TREND_ANALYSIS_WINDOW", "30"))
    MIN_TREND_DATA_POINTS: int = int(os.getenv("MIN_TREND_DATA_POINTS", "5"))

    # Cache Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_NAMESPACE: str = os.getenv("CACHE_NAMESPACE", "onside")
    CACHE_DEFAULT_TTL: int = int(os.getenv("CACHE_DEFAULT_TTL", "300"))  # 5 minutes

    # Cache TTL values for different data types (in seconds)
    CACHE_TTL_WEBSITE_CRAWL: int = int(os.getenv("CACHE_TTL_WEBSITE_CRAWL", "3600"))  # 1 hour
    CACHE_TTL_SERP_RESULTS: int = int(os.getenv("CACHE_TTL_SERP_RESULTS", "86400"))  # 24 hours
    CACHE_TTL_KEYWORD_DATA: int = int(os.getenv("CACHE_TTL_KEYWORD_DATA", "604800"))  # 7 days
    CACHE_TTL_API_RESPONSE: int = int(os.getenv("CACHE_TTL_API_RESPONSE", "300"))  # 5 minutes
    CACHE_TTL_ANALYTICS: int = int(os.getenv("CACHE_TTL_ANALYTICS", "1800"))  # 30 minutes
    
    model_config = {
        'env_file': '.env',
        'env_prefix': '',
        'case_sensitive': False,
        'env_file_encoding': 'utf-8',
        'extra': 'ignore',
        'env_nested_delimiter': '__',
        'validate_default': True,
        'env_naming_strategy': {
            'database_url': 'DATABASE_URL',
            'secret_key': 'SECRET_KEY',
            'api_version': 'API_VERSION',
            'environment': 'ENVIRONMENT',
            'log_level': 'LOG_LEVEL',
            'allowed_origins': 'ALLOWED_ORIGINS',
            'SEMRUSH_API_KEY': 'SEMRUSH_API_KEY',
            'SERPAPI_KEY': 'SERPAPI_KEY',
            'SEO_DEFAULT_MARKET': 'SEO_DEFAULT_MARKET',
            'SEO_DEFAULT_LANGUAGE': 'SEO_DEFAULT_LANGUAGE',
            'SEO_API_RATE_LIMIT': 'SEO_API_RATE_LIMIT',
            'MELTWATER_API_KEY': 'MELTWATER_API_KEY',
            'MELTWATER_API_URL': 'MELTWATER_API_URL',
            'MELTWATER_API_RATE_LIMIT': 'MELTWATER_API_RATE_LIMIT',
            'WHOAPI_API_KEY': 'WHOAPI_API_KEY',
            'WHOAPI_BASE_URL': 'WHOAPI_BASE_URL',
            'WHOAPI_TIMEOUT': 'WHOAPI_TIMEOUT',
            'WHOAPI_MAX_RETRIES': 'WHOAPI_MAX_RETRIES',
            'REALTIME_ANALYTICS_ENDPOINT': 'REALTIME_ANALYTICS_ENDPOINT',
            'REALTIME_ANALYTICS_KEY': 'REALTIME_ANALYTICS_KEY',
            'ANALYTICS_UPDATE_INTERVAL': 'ANALYTICS_UPDATE_INTERVAL',
            'MAX_CONTENT_AGE_DAYS': 'MAX_CONTENT_AGE_DAYS',
            'TREND_ANALYSIS_WINDOW': 'TREND_ANALYSIS_WINDOW',
            'MIN_TREND_DATA_POINTS': 'MIN_TREND_DATA_POINTS',
            'debug': 'DEBUG'
        }
    }

    def _set_environment_specific_config(self):
        """Set environment-specific configuration values"""
        if self.environment == "production":
            self.log_level = "WARNING"
            self.allowed_origins = ["https://api.capilytics.com"]
        elif self.environment == "test":
            self.database_url = "sqlite:///test.db"
            self.log_level = "DEBUG"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not kwargs.get('_skip_post_init', False):
            self._set_environment_specific_config()

def validate_database_url(url: str) -> bool:
    """Validate the database URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) or result.scheme == "sqlite" or result.scheme == "sqlite+aiosqlite"
    except:
        return False

@lru_cache()
def load_config(validate: bool = False) -> Config:
    """Load and validate configuration from environment variables"""
    config = Config()
    
    if validate:
        if not config.secret_key:
            raise ValueError("SECRET_KEY must be set")
            
        if not validate_database_url(config.database_url):
            raise ValueError("Invalid DATABASE_URL format")
    
    return config

@lru_cache()
def get_settings() -> Config:
    """Get cached settings instance."""
    return Config()

# Create a global settings instance
settings = get_settings()
