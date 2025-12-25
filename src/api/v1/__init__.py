from fastapi import APIRouter

api_router = APIRouter()

# Import routers after creating api_router to avoid circular imports
from .health import router as health_router
from .auth import router as auth_router
from .audience import router as audience_router
from .recommendations import router as recommendations_router
from .reports import router as reports_router
from .data_ingestion import router as data_ingestion_router
from .ai_insights import router as ai_insights_router
from .seo import router as seo_router
from .web_scraper import router as web_scraper_router
from .link_search import router as link_search_router
from .engagement_extraction import router as engagement_extraction_router
from .competitor import router as competitor_router
from .domain import router as domain_router
from .competitor_analysis import router as competitor_analysis_router
from .google_analytics import router as google_analytics_router
from .gnews import router as gnews_router
from .competitor_news import router as competitor_news_router
from .ipinfo import router as ipinfo_router
from .whoapi import router as whoapi_router

# New routers for backend features
from .report_schedules import router as report_schedules_router
from .search_history import router as search_history_router
from .scraping import router as scraping_router
from .email_delivery import router as email_delivery_router
from .link_deduplication import router as link_deduplication_router
from .user_preferences import router as user_preferences_router
from .seo_services import router as seo_services_router
from .engarde import router as engarde_router
from .cache import router as cache_router
from .websockets import router as websockets_router
from .brand_discovery_chat import router as brand_discovery_chat_router

# Include all routers
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(audience_router, prefix="/audience", tags=["audience"])
api_router.include_router(recommendations_router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(data_ingestion_router, prefix="/data-ingestion", tags=["data-ingestion"])
api_router.include_router(ai_insights_router, prefix="/ai-insights", tags=["ai-insights"])
api_router.include_router(seo_router, prefix="/seo", tags=["seo"])
api_router.include_router(web_scraper_router, prefix="/web-scraper", tags=["web-scraper"])
api_router.include_router(link_search_router, prefix="/link-search", tags=["link-search"])
api_router.include_router(engagement_extraction_router, prefix="/engagement-extraction", tags=["engagement-extraction"])
api_router.include_router(competitor_router, prefix="/competitors", tags=["competitors"])
api_router.include_router(domain_router, prefix="/domains", tags=["domains"])
api_router.include_router(competitor_analysis_router, prefix="/competitor-analysis", tags=["competitor-analysis"])
api_router.include_router(google_analytics_router, prefix="/analytics", tags=["google-analytics"])
api_router.include_router(gnews_router, prefix="/gnews", tags=["gnews"])
api_router.include_router(competitor_news_router, tags=["competitor-news"])
api_router.include_router(ipinfo_router, prefix="/ipinfo", tags=["ipinfo"])
api_router.include_router(whoapi_router, prefix="/whoapi", tags=["whoapi"])

# Include new backend feature routers
api_router.include_router(report_schedules_router, tags=["report-schedules"])
api_router.include_router(search_history_router, tags=["search-history"])
api_router.include_router(scraping_router, tags=["scraping"])
api_router.include_router(email_delivery_router, tags=["email"])
api_router.include_router(link_deduplication_router, tags=["link-deduplication"])
api_router.include_router(user_preferences_router, tags=["user-preferences"])
api_router.include_router(seo_services_router, tags=["seo-services"])
api_router.include_router(engarde_router, tags=["engarde"])
api_router.include_router(websockets_router, tags=["websockets"])
api_router.include_router(brand_discovery_chat_router, tags=["brand-discovery-chat"])

__all__ = ["api_router"]
