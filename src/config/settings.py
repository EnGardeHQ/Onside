"""Settings configuration module.

This module handles application settings and environment variables following
Semantic Seed coding standards with proper error handling and logging.

Features:
- Environment variable management
- AI/ML service configuration from Sprint 4
- Logging configuration
- Database settings
"""
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Media directories for file storage
MEDIA_ROOT = BASE_DIR / "media"
os.makedirs(MEDIA_ROOT, exist_ok=True)

# Database settings (following our verified schema)
DATABASE = {
    "USER": os.getenv("DB_USER", "tobymorning"),
    "PASSWORD": os.getenv("DB_PASSWORD", ""),
    "HOST": os.getenv("DB_HOST", "localhost"),
    "PORT": os.getenv("DB_PORT", "5432"),
    "NAME": os.getenv("DB_NAME", "onside"),
    "url": os.getenv("DATABASE_URL", f"postgresql+asyncpg://{os.getenv('DB_USER', 'tobymorning')}:{os.getenv('DB_PASSWORD', '')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'onside')}")
}

# AI/ML Configuration from Sprint 4
AI_CONFIG = {
    "OPENAI": {
        "API_KEY": os.getenv("OPENAI_API_KEY"),
        "MODEL": "gpt-4-turbo",
        "MAX_TOKENS": 2000,
        "TEMPERATURE": 0.7
    },
    "CONFIDENCE_THRESHOLDS": {
        "HIGH": 0.8,
        "MEDIUM": 0.6,
        "LOW": 0.4
    },
    "CHAIN_OF_THOUGHT": {
        "ENABLED": True,
        "MAX_STEPS": 5,
        "LOG_LEVEL": "DEBUG"
    }
}

# Progress Tracking Configuration (S5-04)
PROGRESS = {
    "WEBSOCKET": {
        "PING_INTERVAL": 30,  # Seconds between ping messages
        "PING_TIMEOUT": 10,   # Seconds to wait for pong response
        "CLOSE_TIMEOUT": 5    # Seconds to wait when closing connection
    },
    "STAGES": {
        "DATA_COLLECTION": {
            "WEIGHT": 0.15,
            "TIMEOUT": 300  # 5 minutes
        },
        "COMPETITOR_ANALYSIS": {
            "WEIGHT": 0.25,
            "TIMEOUT": 600  # 10 minutes
        },
        "MARKET_ANALYSIS": {
            "WEIGHT": 0.20,
            "TIMEOUT": 600  # 10 minutes
        },
        "AUDIENCE_ANALYSIS": {
            "WEIGHT": 0.20,
            "TIMEOUT": 600  # 10 minutes
        },
        "REPORT_GENERATION": {
            "WEIGHT": 0.10,
            "TIMEOUT": 300  # 5 minutes
        },
        "VISUALIZATION": {
            "WEIGHT": 0.05,
            "TIMEOUT": 180  # 3 minutes
        },
        "FINALIZATION": {
            "WEIGHT": 0.05,
            "TIMEOUT": 120  # 2 minutes
        }
    },
    "ERROR_HANDLING": {
        "MAX_RETRIES": 3,
        "RETRY_DELAY": 5,  # Seconds between retries
        "FALLBACK_TIMEOUT": 30  # Seconds to wait for fallback response
    },
    "CACHE": {
        "ENABLED": True,
        "TTL": 3600,  # 1 hour cache lifetime
        "MAX_SIZE": 1000  # Maximum number of cached items
    }
}

# Report Generation Settings
REPORT = {
    "OUTPUT_DIR": BASE_DIR / "reports",
    "TEMPLATE_DIR": BASE_DIR / "templates",
    "MAX_COMPETITORS": 10,
    "MAX_LINKS_PER_COMPETITOR": 5,
    "CONFIDENCE_THRESHOLD": 0.6
}

# Web Scraping Settings
SCRAPING = {
    "USER_AGENT": "OnSide/1.0",
    "TIMEOUT": 30,
    "MAX_RETRIES": 3,
    "RATE_LIMIT": 1.0  # Requests per second
}

def get_ai_provider_config(provider: str) -> Dict[str, Any]:
    """Get configuration for a specific AI provider.
    
    Args:
        provider: Name of the AI provider
        
    Returns:
        Provider configuration
    """
    provider = provider.upper()
    if provider not in AI_CONFIG:
        logger.warning(f"Unknown AI provider: {provider}")
        return {}
    return AI_CONFIG[provider]

def get_report_path(report_id: str) -> Path:
    """Get the path for a report file.
    
    Args:
        report_id: ID of the report
        
    Returns:
        Path to the report file
    """
    reports_dir = REPORT["OUTPUT_DIR"]
    reports_dir.mkdir(exist_ok=True)
    return reports_dir / f"report_{report_id}.pdf"

def validate_settings() -> bool:
    """Validate critical settings.
    
    Returns:
        True if all critical settings are valid
    """
    try:
        # Validate database settings - we need to check essential fields
        # Password can be empty for user-based authentication on localhost
        essential_db_fields = ["USER", "HOST", "PORT", "NAME"]
        if not all(DATABASE[field] for field in essential_db_fields):
            logger.error("❌ Missing essential database configuration")
            return False
            
        # Log the detected database configuration
        logger.info(f"📊 Database configuration: {DATABASE['NAME']} on {DATABASE['HOST']}:{DATABASE['PORT']} as {DATABASE['USER']}")
            
        # Validate AI configuration
        if not AI_CONFIG["OPENAI"]["API_KEY"]:
            logger.warning("⚠️ OpenAI API key not configured")
            
        # Validate progress tracking configuration
        progress_weights = sum(
            stage["WEIGHT"] 
            for stage in PROGRESS["STAGES"].values()
        )
        if not (0.99 <= progress_weights <= 1.01):  # Allow small float precision errors
            logger.error("❌ Progress stage weights must sum to 1.0")
            return False
            
        # Validate directories
        REPORT["OUTPUT_DIR"].mkdir(exist_ok=True)
        REPORT["TEMPLATE_DIR"].mkdir(exist_ok=True)
        
        logger.info("✅ Settings validated successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error validating settings: {str(e)}")
        return False
