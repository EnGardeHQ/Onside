from fastapi import FastAPI, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.api.v1 import api_router
from src.database import init_db
from src.config import Config, load_config
from src.database.config import get_db
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.security import get_current_user
from src.models.user import User
from src.services.cache_service import get_cache_service
import logging

logger = logging.getLogger(__name__)

__all__ = ['create_app']

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application."""
    config = load_config()

    # Initialize database
    await init_db()

    # Initialize cache service
    logger.info("Initializing cache service...")
    try:
        cache = get_cache_service(
            redis_url=config.REDIS_URL,
            namespace=config.CACHE_NAMESPACE,
            default_ttl=config.CACHE_DEFAULT_TTL
        )
        await cache.initialize()

        # Store cache in app state for easy access
        app.state.cache = cache
        logger.info("Cache service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize cache service: {e}")
        logger.warning("Application will continue with degraded caching functionality")

    yield  # Application runs here

    # Shutdown
    try:
        # Close cache connection
        if hasattr(app.state, 'cache'):
            await app.state.cache.close()
            logger.info("Cache service closed")
    except Exception as e:
        logger.error(f"Error closing cache service: {e}")

    try:
        async for db in get_db():
            await db.close()
    except Exception:
        pass

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    config = load_config()
    
    app = FastAPI(
        title="Capilytics API",
        description="API for Capilytics - Venture Insights for Startups and Growing Enterprises",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {"message": "Welcome to Capilytics API"}

    @app.get("/health")
    def health_check() -> Dict[str, Any]:
        """Health check endpoint"""
        return {"status": "healthy"}
    
    return app

# Create the application instance
app = create_app()
