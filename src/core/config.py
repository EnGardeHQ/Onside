"""Application configuration."""
import os
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings
from pydantic.fields import Field

class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "OnSide SEO Service"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://tobymorning@localhost:5432/onside")

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_URL: str = os.getenv("REDIS_URL", f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/{os.getenv('REDIS_DB', '0')}")

    # Celery Configuration
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 30 * 60  # 30 minutes
    CELERY_TASK_SOFT_TIME_LIMIT: int = 25 * 60  # 25 minutes

    # MinIO Configuration
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minio-access-key")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minio-secret-key")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    MINIO_REGION: str = os.getenv("MINIO_REGION", "us-east-1")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
        
    # Google OAuth Configuration
    GOOGLE_OAUTH_CLIENT_ID: str = Field(
        default=os.getenv("GOOGLE_OAUTH_CLIENT_ID", ""),
        description="Google OAuth Client ID"
    )
    GOOGLE_OAUTH_CLIENT_SECRET: str = Field(
        default=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", ""),
        description="Google OAuth Client Secret"
    )
    GOOGLE_OAUTH_REDIRECT_URI: str = Field(
        default=os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/v1/analytics/auth/callback"),
        description="Google OAuth Redirect URI"
    )
    
    # Google Analytics
    GOOGLE_ANALYTICS_VIEW_ID: Optional[str] = Field(
        default=os.getenv("GOOGLE_ANALYTICS_VIEW_ID"),
        description="Google Analytics View ID"
    )
    
    # Google OAuth Configuration is now defined above using pydantic.Field
    
    class Config:
        """Pydantic config."""
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Allow extra fields from .env file

# Create settings instance
settings = Settings()
