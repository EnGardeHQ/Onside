from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

# Create the FastAPI application with default Swagger UI
app = FastAPI(
    title="OnSide API",
    description="API components for OnSide platform - Completed through Sprint 4",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers from v1 API
# Import only the routers that exist in the project
try:
    from .v1 import auth, reports, ai_insights, audience, data_ingestion, recommendations
    from .v1 import engagement_extraction, link_search, web_scraper, seo, health, google_analytics
except ImportError as e:
    import logging
    logging.error(f"Error importing routers: {e}")
    # Provide fallback imports for critical components
    from .v1 import auth, health

# Register all routers with appropriate prefixes
try:
    app.include_router(auth.router, prefix="/api/v1/auth")
    app.include_router(reports.router, prefix="/api/v1/reports")
    app.include_router(ai_insights.router, prefix="/api/v1/ai-insights")
    app.include_router(audience.router, prefix="/api/v1/audience")
    app.include_router(data_ingestion.router, prefix="/api/v1/data-ingestion")
    app.include_router(recommendations.router, prefix="/api/v1/recommendations")
    app.include_router(engagement_extraction.router, prefix="/api/v1/engagement-extraction")
    app.include_router(link_search.router, prefix="/api/v1/link-search")
    app.include_router(web_scraper.router, prefix="/api/v1/web-scraper")
    app.include_router(seo.router, prefix="/api/v1/seo")
    app.include_router(google_analytics.router, prefix="/api/v1/google-analytics")
    app.include_router(health.router, prefix="/api/v1/health")
except NameError as e:
    import logging
    logging.error(f"Error including routers: {e}")
    # Always include health router as fallback
    app.include_router(health.router, prefix="/api/v1/health")

@app.get("/")
async def root():
    return {"message": "Welcome to OnSide API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Using default Swagger UI instead of custom implementation

# Override the default OpenAPI schema to add security definitions
from fastapi.routing import APIRoute

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
        
    openapi_schema = get_openapi(
        title="OnSide API",
        version="1.0.0",
        description="""## OnSide API Documentation
        
        This API provides access to the OnSide platform capabilities.
        
        ### Sprint 4 Enhancements:
        - Report Generator API for Content and Sentiment reports with job status tracking
        - AI/ML enhancements with chain-of-thought reasoning
        - Fallback mechanisms for LLM calls
        - Circuit breaker pattern for resilient LLM service
        
        ### Authentication
        Most endpoints require authentication using JWT tokens.
        """,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"] = {
        "securitySchemes": {
            "Bearer": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    }
    
    # Apply security globally
    openapi_schema["security"] = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Initialize database on startup
from src.database.config import init_db

@app.on_event("startup")
async def startup_event():
    await init_db()
