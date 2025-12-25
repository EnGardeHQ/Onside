from src.api.routes.auth import router as auth_router
from src.api.routes.data_ingestion import router as data_ingestion_router
from src.api.routes.recommendations import router as recommendations_router
from src.api.routes.ai_insights import router as ai_insights_router
from src.api.routes.reports import router as reports_router
from src.api.routes.audience import router as audience_router

__all__ = [
    "auth_router",
    "data_ingestion_router",
    "recommendations_router",
    "ai_insights_router",
    "reports_router",
    "audience_router"
]
