from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import (
    auth_router,
    data_ingestion_router,
    recommendations_router,
    ai_insights_router,
    reports_router,
    audience_router
)
from src.api.content_affinity_router import router as content_affinity_router

app = FastAPI(title="Capilytics API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/api/auth")
app.include_router(data_ingestion_router, prefix="/api/data")
app.include_router(recommendations_router, prefix="/api/recommendations")
app.include_router(ai_insights_router)
app.include_router(reports_router, prefix="/api/reports")
app.include_router(audience_router)
app.include_router(content_affinity_router)

@app.get("/")
async def root():
    return {"message": "Welcome to Capilytics API"}
