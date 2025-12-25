"""Google Analytics API endpoints.

This module provides FastAPI endpoints for Google Analytics integration.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl, Field

from src.database import get_db
from src.models.user import User
from src.api.deps import get_current_active_user
from src.services.google_analytics import GoogleAnalyticsOAuth2Client, GoogleAnalyticsClient
from src.core.config import settings

router = APIRouter(
    prefix="",
    tags=["google-analytics"],
    responses={"404": {"description": "Not found"}},
)

class GoogleAnalyticsAuthRequest(BaseModel):
    """Request model for initiating Google Analytics OAuth2 flow."""
    redirect_uri: HttpUrl = Field(..., description="The redirect URI after OAuth2 authorization")

class GoogleAnalyticsCallbackRequest(BaseModel):
    """Request model for handling OAuth2 callback."""
    code: str = Field(..., description="The authorization code from Google")
    state: Optional[str] = Field(None, description="The state parameter for CSRF protection")
    redirect_uri: HttpUrl = Field(..., description="The redirect URI used in the authorization request")

class GoogleAnalyticsProperty(BaseModel):
    """Google Analytics property model."""
    id: str = Field(..., description="The property ID")
    name: str = Field(..., description="The property name")
    website_url: str = Field(..., description="The website URL for this property")

class GoogleAnalyticsMetrics(BaseModel):
    """Google Analytics metrics model."""
    sessions: int = 0
    users: int = 0
    page_views: int = 0
    avg_session_duration: float = 0.0
    bounce_rate: float = 0.0
    engagement_rate: float = 0.0

class GoogleAnalyticsPageView(BaseModel):
    """Google Analytics page view model."""
    page_path: str = Field(..., alias="pagePath")
    page_title: str = Field(..., alias="pageTitle")
    sessions: int = 0
    page_views: int = 0
    avg_session_duration: float = 0.0
    bounce_rate: float = 0.0

class GoogleAnalyticsTrafficSource(BaseModel):
    """Google Analytics traffic source model."""
    source: str = "(direct)"
    medium: str = "(none)"
    sessions: int = 0
    users: int = 0
    page_views: int = 0
    avg_session_duration: float = 0.0
    bounce_rate: float = 0.0

@router.get("/auth/url", response_model=Dict[str, str])
async def get_google_analytics_auth_url(
    redirect_uri: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the Google Analytics OAuth2 authorization URL.
    
    This endpoint returns the URL to redirect the user to for Google OAuth2 authorization.
    """
    try:
        oauth_client = GoogleAnalyticsOAuth2Client(user_id=current_user.id, db=db)
        auth_url = oauth_client.get_authorization_url(redirect_uri=str(redirect_uri))
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get authorization URL: {str(e)}"
        )

@router.post("/auth/callback", response_model=Dict[str, bool])
async def handle_google_analytics_callback(
    request: GoogleAnalyticsCallbackRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Handle the OAuth2 callback from Google.
    
    This endpoint exchanges the authorization code for an access token
    and saves it to the database.
    """
    try:
        oauth_client = GoogleAnalyticsOAuth2Client(user_id=current_user.id, db=db)
        token_data = oauth_client.fetch_token(
            authorization_response=str(request.redirect_uri),
            redirect_uri=str(request.redirect_uri)
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to authenticate with Google Analytics: {str(e)}"
        )

@router.get("/auth/status", response_model=Dict[str, bool])
async def get_google_analytics_auth_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Check if the user is authenticated with Google Analytics."""
    try:
        oauth_client = GoogleAnalyticsOAuth2Client(user_id=current_user.id, db=db)
        credentials = oauth_client.get_credentials()
        return {"authenticated": credentials is not None}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to check authentication status: {str(e)}"
        )

@router.delete("/auth/revoke", response_model=Dict[str, bool])
async def revoke_google_analytics_auth(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Revoke Google Analytics authentication."""
    try:
        oauth_client = GoogleAnalyticsOAuth2Client(user_id=current_user.id, db=db)
        success = oauth_client.revoke_token()
        return {"success": success}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to revoke authentication: {str(e)}"
        )

@router.get("/properties", response_model=List[GoogleAnalyticsProperty])
async def get_google_analytics_properties(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get list of Google Analytics properties for the authenticated user."""
    # Note: This is a simplified implementation. In a real app, you would need to use the
    # Google Analytics Admin API to list properties. For now, we'll return a mock response.
    # You'll need to implement this based on your specific requirements.
    return [
        {
            "id": settings.GOOGLE_ANALYTICS_PROPERTY_ID,
            "name": "My Website",
            "website_url": "https://example.com"
        }
    ]

@router.get("/metrics/overview", response_model=GoogleAnalyticsMetrics)
async def get_google_analytics_metrics(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    property_id: str = Query(..., description="Google Analytics property ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get Google Analytics metrics for the specified date range."""
    try:
        ga_client = GoogleAnalyticsClient(user_id=current_user.id, property_id=property_id)
        metrics = ga_client.get_site_metrics(start_date=start_date, end_date=end_date)
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch Google Analytics metrics: {str(e)}"
        )

@router.get("/metrics/top-pages", response_model=List[GoogleAnalyticsPageView])
async def get_google_analytics_top_pages(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    property_id: str = Query(..., description="Google Analytics property ID"),
    limit: int = Query(10, description="Number of top pages to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get top pages by page views."""
    try:
        ga_client = GoogleAnalyticsClient(user_id=current_user.id, property_id=property_id)
        pages = ga_client.get_top_pages(
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return [
            {
                "pagePath": page.get("pagePath", ""),
                "pageTitle": page.get("pageTitle", "(No title)"),
                "sessions": int(page.get("sessions", 0)),
                "page_views": int(page.get("screenPageViews", 0)),
                "avg_session_duration": float(page.get("averageSessionDuration", 0)),
                "bounce_rate": float(page.get("bounceRate", 0)),
            }
            for page in pages
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch top pages: {str(e)}"
        )

@router.get("/metrics/traffic-sources", response_model=List[GoogleAnalyticsTrafficSource])
async def get_google_analytics_traffic_sources(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    property_id: str = Query(..., description="Google Analytics property ID"),
    limit: int = Query(10, description="Number of traffic sources to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get traffic sources."""
    try:
        ga_client = GoogleAnalyticsClient(user_id=current_user.id, property_id=property_id)
        sources = ga_client.get_traffic_sources(
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return sources
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch traffic sources: {str(e)}"
        )
