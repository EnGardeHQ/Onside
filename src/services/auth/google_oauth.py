"""Google OAuth2 service for authentication."""
import json
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from src.models.oauth_token import OAuthToken
from src.core.config import settings

class GoogleOAuth:
    """Google OAuth2 service for handling authentication with Google APIs."""

    def __init__(self, db: AsyncSession):
        """Initialize the Google OAuth service.
        
        Args:
            db: Async database session
        """
        self.db = db
        self.token_url = "https://oauth2.googleapis.com/token"
        self.user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    async def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Generate the Google OAuth2 authorization URL.
        
        Args:
            redirect_uri: The redirect URI after authorization
            state: Optional state parameter for CSRF protection
            
        Returns:
            The authorization URL
        """
        params = {
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/analytics.readonly",
            "redirect_uri": redirect_uri,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        if state:
            params["state"] = state
            
        query_params = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://accounts.google.com/o/oauth2/auth?{query_params}"
    
    async def get_access_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token.
        
        Args:
            code: The authorization code from Google
            redirect_uri: The redirect URI used in the authorization request
            
        Returns:
            Token data including access_token, refresh_token, etc.
            
        Raises:
            HTTPException: If token exchange fails
        """
        data = {
            "code": code,
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get access token: {str(e)}"
            )
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user info using the access token.
        
        Args:
            access_token: The access token
            
        Returns:
            User info including email, name, etc.
            
        Raises:
            HTTPException: If user info retrieval fails
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.user_info_url, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get user info: {str(e)}"
            )
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an expired access token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            New token data
            
        Raises:
            HTTPException: If token refresh fails
        """
        data = {
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to refresh token: {str(e)}"
            )
    
    async def save_token(self, user_id: str, token_data: Dict[str, Any]) -> OAuthToken:
        """Save or update OAuth token in the database.
        
        Args:
            user_id: The UUID of the user
            token_data: Token data from Google
            
        Returns:
            The saved or updated OAuthToken
        """
        expires_at = None
        if "expires_in" in token_data:
            expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
        
        # Check if token already exists for this user and service
        stmt = select(OAuthToken).where(
            OAuthToken.user_id == user_id,
            OAuthToken.service == "google_analytics"
        )
        
        result = await self.db.execute(stmt)
        token = result.scalars().first()
        
        if token:
            # Update existing token
            stmt = (
                update(OAuthToken)
                .where(OAuthToken.id == token.id)
                .values(
                    access_token=token_data["access_token"],
                    refresh_token=token_data.get("refresh_token", token.refresh_token),
                    expires_at=expires_at,
                    updated_at=datetime.utcnow()
                )
            )
            await self.db.execute(stmt)
        else:
            # Create new token
            token = OAuthToken(
                user_id=user_id,
                service="google_analytics",
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_uri=self.token_url,
                client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
                client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
                scopes=token_data.get("scope", ""),
                expires_at=expires_at
            )
            self.db.add(token)
        
        await self.db.commit()
        await self.db.refresh(token)
        return token
