"""Google Analytics OAuth2 Client.

This module handles the OAuth2 flow for Google Analytics API access.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from sqlalchemy.orm import Session

from src.config import settings
from src.models.oauth_token import OAuthToken
from src.database import get_db

logger = logging.getLogger(__name__)

# Google OAuth2 scopes for Google Analytics
SCOPES = [
    'https://www.googleapis.com/auth/analytics.readonly',
    'https://www.googleapis.com/auth/webmasters.readonly',
]

class GoogleAnalyticsOAuth2Client:
    """Handles OAuth2 authentication for Google Analytics API."""
    
    def __init__(self, user_id: str, db: Optional[Session] = None):
        """Initialize the OAuth2 client.
        
        Args:
            user_id: The UUID of the user to authenticate
            db: Optional database session. If not provided, a new one will be created.
        """
        self.user_id = user_id
        self.db = db or next(get_db())
        self.credentials = None
        self.token = None
        
    async def get_authorization_url(self, redirect_uri: str) -> str:
        """Generate the authorization URL for the OAuth2 flow.
        
        Args:
            redirect_uri: The redirect URI to use after authorization
            
        Returns:
            str: The authorization URL
        """
        flow = Flow.from_client_config(
            settings.GOOGLE_OAUTH_CONFIG,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        
        # Enable offline access so we can get a refresh token
        flow.include_granted_scopes = 'true'
        flow.prompt = 'consent'
        flow.access_type = 'offline'
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return authorization_url
    
    async def fetch_token(self, authorization_response: str, redirect_uri: str) -> Dict[str, Any]:
        """Fetch the OAuth2 token using the authorization response.
        
        Args:
            authorization_response: The full redirect URL after user authorization
            redirect_uri: The redirect URI used in the authorization request
            
        Returns:
            Dict containing the token information
            
        Raises:
            ValueError: If token fetch fails
        """
        try:
            flow = Flow.from_client_config(
                settings.GOOGLE_OAUTH_CONFIG,
                scopes=SCOPES,
                redirect_uri=redirect_uri
            )
            
            # Exchange the authorization code for tokens
            flow.fetch_token(authorization_response=authorization_response)
            credentials = flow.credentials
            
            # Save the token
            token_data = {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': settings.GOOGLE_OAUTH_CONFIG['web']['client_secret'],
                'scopes': credentials.scopes,
                'expires_at': credentials.expiry.isoformat() if credentials.expiry else None
            }
            
            self._save_token(token_data)
            return token_data
            
        except Exception as e:
            logger.error(f"Failed to fetch token: {str(e)}")
            raise ValueError(f"Failed to fetch token: {str(e)}")
    
    async def get_credentials(self) -> Optional[Credentials]:
        """Get valid OAuth2 credentials for the user.
        
        Returns:
            Optional[Credentials]: Valid credentials if available, None otherwise
        """
        # Try to load token from database
        token = await self._load_token()
        if not token:
            return None
            
        # Create credentials from token data
        credentials = Credentials(
            token=token.access_token,
            refresh_token=token.refresh_token,
            token_uri=token.token_uri,
            client_id=token.client_id,
            client_secret=token.client_secret,
            scopes=token.scopes.split() if token.scopes else SCOPES,
            expiry=token.expires_at
        )
        
        # Refresh token if expired
        if credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
                # Save the refreshed token
                token_data = {
                    'access_token': credentials.token,
                    'refresh_token': credentials.refresh_token or token.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': token.client_secret,
                    'scopes': credentials.scopes,
                    'expires_at': credentials.expiry.isoformat() if credentials.expiry else None
                }
                await self._save_token(token_data)
            except RefreshError as e:
                logger.error(f"Failed to refresh token: {str(e)}")
                return None
                
        return credentials
    
    async def _load_token(self) -> Optional[OAuthToken]:
        """Load the OAuth token from the database.
        
        Returns:
            Optional[OAuthToken]: The token if found, None otherwise
        """
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession
        
        if not isinstance(self.db, AsyncSession):
            # Fallback to sync query if not using async session
            return self.db.query(OAuthToken).filter(
                OAuthToken.user_id == self.user_id,
                OAuthToken.service == 'google_analytics'
            ).first()
            
        # Use async query
        stmt = select(OAuthToken).where(
            OAuthToken.user_id == self.user_id,
            OAuthToken.service == 'google_analytics'
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def _save_token(self, token_data: Dict[str, Any]) -> OAuthToken:
        """Save or update the OAuth token in the database.
        
        Args:
            token_data: Dictionary containing token information
            
        Returns:
            OAuthToken: The saved or updated token
        """
        # Convert scopes list to space-separated string
        scopes = token_data.get('scopes', [])
        if isinstance(scopes, list):
            scopes = ' '.join(scopes)
            
        # Parse expires_at if it's a string
        expires_at = token_data.get('expires_at')
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
            
        # Check if token already exists
        token = await self._load_token()
        
        if token:
            # Update existing token
            token.access_token = token_data['access_token']
            token.refresh_token = token_data.get('refresh_token') or token.refresh_token
            token.token_uri = token_data.get('token_uri')
            token.client_id = token_data.get('client_id')
            token.client_secret = token_data.get('client_secret')
            token.scopes = scopes
            token.expires_at = expires_at
        else:
            # Create new token
            token = OAuthToken(
                user_id=self.user_id,
                service='google_analytics',
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token'),
                token_uri=token_data.get('token_uri'),
                client_id=token_data.get('client_id'),
                client_secret=token_data.get('client_secret'),
                scopes=scopes,
                expires_at=expires_at
            )
            self.db.add(token)
        
        self.db.commit()
        self.db.refresh(token)
        return token
    
    async def revoke_token(self) -> bool:
        """Revoke the OAuth token.
        
        Returns:
            bool: True if token was revoked, False otherwise
        """
        token = self._load_token()
        if not token:
            return False
            
        try:
            credentials = Credentials(
                token=token.access_token,
                refresh_token=token.refresh_token,
                token_uri=token.token_uri,
                client_id=token.client_id,
                client_secret=token.client_secret,
                scopes=token.scopes.split() if token.scopes else None,
                expiry=token.expires_at
            )
            
            # Revoke the token
            credentials.revoke(Request())
            
            # Delete the token from the database
            await self.db.delete(token)
            await self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke token: {str(e)}")
            return False
