"""Configuration package initialization.

This module initializes configuration following Semantic Seed coding standards
and our verified database schema requirements.

Features:
- Proper async database initialization
- Settings validation
- Comprehensive error handling
- Detailed logging
- Sprint 4 AI/ML capabilities
"""
import logging
import os
from typing import Optional, Dict, Any
from pathlib import Path
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import config first to avoid circular imports
from .config import Config, DatabaseConfig, AIConfig

def load_config() -> Config:
    """Load and return the application configuration.
    
    Returns:
        Config: The application configuration
    """
    return Config()

# Import settings after Config is defined
from .settings import (
    DATABASE,
    AI_CONFIG,
)

@lru_cache()
def get_settings() -> Dict[str, Any]:
    """Get application settings with validation.
    
    Returns:
        Dictionary containing all application settings
        
    Raises:
        ValueError: If settings validation fails
    """
    try:
        settings = {
            'database': DATABASE,
            'ai': AI_CONFIG,
        }
        
        # Validate settings
        if not settings['database'].get('url'):
            raise ValueError("Database URL is required")
            
        if not settings['ai'].get('openai_api_key'):
            logger.warning("OpenAI API key not found. Some features may be limited.")
            
        return settings
        
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        raise

# Import database functions
from .database import (
    init_db,
    get_session,
    close_db,
    get_database_url
)

async def initialize_app() -> bool:
    """Initialize the application.
    
    Following OnSide project's verified database configuration:
    - Database name: onside
    - Owner: tobymorning
    - Connection: localhost:5432
    - Authentication: User-based (tobymorning)
    
    And Sprint 4 AI/ML capabilities:
    - Chain-of-thought reasoning
    - Data quality validation
    - Confidence scoring
    - Structured JSON prompts
    
    Returns:
        True if initialization successful
    """
    try:
        # Initialize database
        await init_db()
        
        # Initialize AI services
        # (Add AI service initialization here)
        
        # Create necessary directories
        Path(DATABASE.get("REPORTS_DIR", "reports")).mkdir(exist_ok=True)
        Path("templates").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        logger.info("✅ Application initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        await cleanup_app()
        raise

async def cleanup_app():
    """Clean up application resources."""
    try:
        await close_db()
        logger.info("✅ Application resources cleaned up")
    except Exception as e:
        logger.error(f"Error during application cleanup: {e}")
        raise

__all__ = [
    'get_settings',
    'init_db',
    'get_session',
    'close_db',
    'get_database_url',
    'DATABASE',
    'AI_CONFIG',
    'initialize_app',
    'cleanup_app',
    'Config',
    'DatabaseConfig',
    'AIConfig',
    'load_config'
]
