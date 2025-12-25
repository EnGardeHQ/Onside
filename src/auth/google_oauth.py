"""
Google OAuth2 Authentication

This module provides OAuth2 authentication for Google APIs, specifically for Google Analytics.
"""
import os
from typing import Dict, Optional, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from fastapi import HTTPException, status

class GoogleOAuth:
    """Handles OAuth2 authentication with Google APIs."""
    
    # OAuth2 scopes for Google Analytics
    SCOPES = [
        'https://www.googleapis.com/auth/analytics.readonly',
        'https://www.googleapis.com/auth/userinfo.email',
        'openid'
    ]
    
    def __init__(self, client_config: Optional[Dict[str, Any]] = None):
        """Initialize Google OAuth with client configuration.
        
        Args:
            client_config: Dictionary containing Google OAuth client config.
                         If None, will load from environment variables.
        """
        self.client_config = client_config or {
            "web": {
                "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
                "project_id": os.getenv("GOOGLE_CLOUD_PROJECT"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [
                    os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")
                ]
            }
        }
        self.flow = self._create_flow()
    
    def _create_flow(self):
        """Create and return a Flow instance for OAuth2."""
        return Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri=self.client_config["web"]["redirect_uris"][0]
        )
    
    def get_authorization_url(self) -> str:
        """Generate authorization URL for OAuth2 flow.
        
        Returns:
            str: Authorization URL to redirect the user to
        """
        authorization_url, _ = self.flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return authorization_url
    
    async def get_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens.
        
        Args:
            code: Authorization code from Google
            
        Returns:
            Dict containing access_token, refresh_token, and other OAuth2 tokens
            
        Raises:
            HTTPException: If token exchange fails
        """
        try:
            self.flow.fetch_token(code=code)
            credentials = self.flow.credentials
            return {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
                'expiry': credentials.expiry.isoformat() if credentials.expiry else None
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to fetch tokens: {str(e)}"
            )
    
    @staticmethod
    def get_credentials(token_info: Dict[str, Any]) -> Credentials:
        """Get Credentials object from token info.
        
        Args:
            token_info: Dictionary containing token information
            
        Returns:
            google.oauth2.credentials.Credentials: OAuth2 credentials
        """
        return Credentials(
            token=token_info['token'],
            refresh_token=token_info.get('refresh_token'),
            token_uri=token_info.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=token_info.get('client_id'),
            client_secret=token_info.get('client_secret'),
            scopes=token_info.get('scopes', [])
        )
    
    @staticmethod
    def refresh_credentials(credentials: Credentials) -> bool:
        """Refresh access token if expired.
        
        Args:
            credentials: OAuth2 credentials
            
        Returns:
            bool: True if token was refreshed, False otherwise
        """
        if not credentials.valid:
            try:
                request = Request()
                credentials.refresh(request)
                return True
            except RefreshError:
                return False
        return False
