"""Google Analytics API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from src.database import get_db
from src.models.user import User
from src.core.security import get_current_active_user
from src.services.auth.google_oauth import GoogleOAuth
from src.core.config import settings

router = APIRouter()

@router.get("/auth/url")
async def get_google_auth_url(
    redirect_uri: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Get Google OAuth2 authorization URL.
    
    Args:
        redirect_uri: The redirect URI after authorization
        current_user: The current authenticated user
        db: Database session
        
    Returns:
        Dict containing the authorization URL and state
    """
    oauth = GoogleOAuth(db)
    auth_url = await oauth.get_authorization_url(redirect_uri)
    return {"authorization_url": auth_url, "state": "state"}  # In a real app, generate a secure state

@router.post("/auth/callback")
async def google_auth_callback(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Handle Google OAuth2 callback.
    
    Args:
        request: The request object
        current_user: The current authenticated user
        db: Database session
        
    Returns:
        Dict containing the token information
    """
    try:
        # Get the authorization code from the request
        form_data = await request.form()
        code = form_data.get("code")
        error = form_data.get("error")
        
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth error: {error}"
            )
            
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code not found in request"
            )
            
        # Exchange the authorization code for tokens
        oauth = GoogleOAuth(db)
        token = await oauth.fetch_token(code)
        
        return {
            "access_token": token.access_token,
            "token_type": "Bearer",
            "expires_in": (token.expires_at - datetime.datetime.utcnow()).total_seconds() if token.expires_at else None,
            "refresh_token": token.refresh_token
        }
        
    except Exception as e:
        logger.error(f"Error in Google OAuth callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to authenticate with Google: {str(e)}"
        )

@router.get("/auth/status")
async def get_auth_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, bool]:
    """
    Check if the current user has authenticated with Google Analytics.
    
    Args:
        current_user: The current authenticated user
        db: Database session
        
    Returns:
        Dict containing authentication status
    """
    oauth = GoogleOAuth(db)
    is_authenticated = await oauth.is_authenticated(current_user.id)
    return {"authenticated": is_authenticated}

@router.post("/auth/revoke")
async def revoke_auth(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Revoke Google OAuth2 access.
    
    Args:
        current_user: The current authenticated user
        db: Database session
        
    Returns:
        Dict containing the status message
    """
    oauth = GoogleOAuth(db)
    success = await oauth.revoke_token(current_user.id)
    if success:
        return {"status": "success", "message": "Successfully revoked Google OAuth access"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to revoke Google OAuth access"
        )

@router.get("/properties")
async def get_ga_properties(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get list of Google Analytics properties for the authenticated user.
    
    Args:
        current_user: The current authenticated user
        db: Database session
        
    Returns:
        Dict containing the list of GA properties
    """
    oauth = GoogleOAuth(db)
    properties = await oauth.get_ga_properties(current_user.id)
    return {"properties": properties}

@router.get("/metrics/overview")
async def get_ga_overview(
    start_date: str,
    end_date: str,
    metrics: str = "ga:users,ga:sessions,ga:pageviews",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get Google Analytics overview metrics.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        metrics: Comma-separated list of metrics
        current_user: The current authenticated user
        db: Database session
        
    Returns:
        Dict containing the requested metrics
    """
    oauth = GoogleOAuth(db)
    data = await oauth.get_ga_data(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        metrics=metrics
    )
    return data
