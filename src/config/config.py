"""Configuration class for OnSide project.

This module defines the configuration class following our verified database schema
and Sprint 4 AI/ML capabilities.

Features:
- Database configuration with verified schema
- AI/ML service configuration from Sprint 4
- Proper error handling and logging
- Environment variable management
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration following our verified schema."""
    url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "postgresql://postgres:onside-password@localhost:5432/onside"))
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    echo: bool = True
    application_name: str = "onside_app"

@dataclass
class AIConfig:
    """AI/ML configuration from Sprint 4."""
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    confidence_threshold: float = 0.85  # From Sprint 4 configuration
    chain_of_thought_enabled: bool = True
    fallback_providers: List[str] = field(default_factory=lambda: ["anthropic"])
    model_config: Dict[str, Any] = field(default_factory=lambda: {
        "openai": {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "anthropic": {
            "model": "claude-3-opus-20240229",
            "temperature": 0.7,
            "max_tokens": 2000
        }
    })

@dataclass
class Config:
    """Main configuration class following Semantic Seed standards."""
    # Base paths
    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    REPORTS_DIR: Path = field(default_factory=lambda: Path("reports"))
    TEMPLATES_DIR: Path = field(default_factory=lambda: Path("templates"))
    
    # Database configuration (verified schema)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    
    # AI/ML configuration (Sprint 4)
    ai: AIConfig = field(default_factory=AIConfig)
    
    # Report generation settings
    report_config: Dict[str, Any] = field(default_factory=lambda: {
        "max_competitors": 10,
        "max_links_per_competitor": 5,
        "confidence_threshold": 0.85,  # From Sprint 4
        "chain_of_thought": {
            "enabled": True,
            "detail_level": "comprehensive"
        }
    })
    
    # Singleton instance
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __post_init__(self):
        """Initialize configuration and validate settings."""
        # Create necessary directories
        self.REPORTS_DIR.mkdir(exist_ok=True)
        self.TEMPLATES_DIR.mkdir(exist_ok=True)
        
        # Set allowed origins for CORS
        self.allowed_origins = [
            "http://localhost:3000",
            "http://localhost:8000",
            "https://onside.app",
            "https://www.onside.app"
        ]
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration settings."""
        try:
            # Validate database configuration
            if not self.database.url:
                raise ValueError("Database URL not configured")
            
            # Validate AI configuration
            if not self.ai.openai_api_key:
                logger.warning("⚠️ OpenAI API key not configured")
            
            if not self.ai.anthropic_api_key and "anthropic" in self.ai.fallback_providers:
                logger.warning("⚠️ Anthropic API key not configured but listed as fallback")
            
            # Validate report configuration
            if self.report_config["confidence_threshold"] < 0 or self.report_config["confidence_threshold"] > 1:
                raise ValueError("Invalid confidence threshold")
            
            logger.info("✅ Configuration validated successfully")
            
        except Exception as e:
            logger.error(f"❌ Configuration validation error: {str(e)}")
            raise
    
    @property
    def database_url(self) -> str:
        """Get the database URL with proper asyncpg driver."""
        if self.database.url.startswith("postgresql://"):
            return self.database.url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database.url
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)
    
    def get_report_path(self, report_id: str) -> Path:
        """Get the path for a report file."""
        return self.REPORTS_DIR / f"report_{report_id}.pdf"
    
    def get_ai_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific AI provider."""
        provider = provider.lower()
        if provider not in self.ai.model_config:
            logger.warning(f"Unknown AI provider: {provider}")
            return {}
        return self.ai.model_config[provider]
