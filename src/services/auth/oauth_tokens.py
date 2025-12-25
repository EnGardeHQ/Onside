"""
OAuth2 Token Storage Service

This module provides functionality to store and retrieve OAuth2 tokens
in the database for different services.
"""
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, and_
import json
import logging

from src.models.oauth_token import OAuthToken

logger = logging.getLogger(__name__)

class OAuthTokenService:
    """Service for managing OAuth2 tokens in the database."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the OAuth token service with a database session."""
        self.db = db
    
    async def get_token(
        self, 
        user_id: int, 
        service: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve OAuth2 tokens for a user and service.
        
        Args:
            user_id: The ID of the user
            service: The service name (e.g., 'google_analytics')
            
        Returns:
            Dictionary containing token information or None if not found
        """
        try:
            result = await self.db.execute(
                select(OAuthToken)
                .where(and_(
                    OAuthToken.user_id == user_id,
                    OAuthToken.service == service
                ))
            )
            token = result.scalars().first()
            
            if not token:
                return None
                
            return {
                'token': token.access_token,
                'refresh_token': token.refresh_token,
                'token_uri': token.token_uri,
                'client_id': token.client_id,
                'client_secret': token.client_secret,
                'scopes': token.scopes.split() if token.scopes else [],
                'expires_at': token.expires_at.isoformat() if token.expires_at else None
            }
            
        except Exception as e:
            logger.error(f"Error retrieving OAuth token: {str(e)}")
            raise
    
    async def save_token(
        self,
        user_id: int,
        service: str,
        token_data: Dict[str, Any],
        expires_in: Optional[int] = None
    ) -> None:
        """Save or update OAuth2 tokens for a user and service.
        
        Args:
            user_id: The ID of the user
            service: The service name (e.g., 'google_analytics')
            token_data: Dictionary containing token information
            expires_in: Optional expiration time in seconds
        """
        try:
            expires_at = None
            if expires_in:
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            elif 'expires_at' in token_data and token_data['expires_at']:
                expires_at = datetime.fromisoformat(token_data['expires_at'])
            
            # Check if token already exists
            result = await self.db.execute(
                select(OAuthToken)
                .where(and_(
                    OAuthToken.user_id == user_id,
                    OAuthToken.service == service
                ))
            )
            token = result.scalars().first()
            
            if token:
                # Update existing token
                await self.db.execute(
                    update(OAuthToken)
                    .where(and_(
                        OAuthToken.user_id == user_id,
                        OAuthToken.service == service
                    ))
                    .values(
                        access_token=token_data['token'],
                        refresh_token=token_data.get('refresh_token') or token.refresh_token,
                        token_uri=token_data.get('token_uri', token.token_uri),
                        client_id=token_data.get('client_id', token.client_id),
                        client_secret=token_data.get('client_secret', token.client_secret),
                        scopes=' '.join(token_data.get('scopes', token.scopes.split() if token.scopes else [])),
                        expires_at=expires_at,
                        updated_at=datetime.utcnow()
                    )
                )
            else:
                # Create new token
                token = OAuthToken(
                    user_id=user_id,
                    service=service,
                    access_token=token_data['token'],
                    refresh_token=token_data.get('refresh_token'),
                    token_uri=token_data.get('token_uri'),
                    client_id=token_data.get('client_id'),
                    client_secret=token_data.get('client_secret'),
                    scopes=' '.join(token_data.get('scopes', [])),
                    expires_at=expires_at
                )
                self.db.add(token)
            
            await self.db.commit()
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error saving OAuth token: {str(e)}")
            raise
    
    async def delete_token(self, user_id: int, service: str) -> bool:
        """Delete OAuth2 tokens for a user and service.
        
        Args:
            user_id: The ID of the user
            service: The service name
            
        Returns:
            bool: True if token was deleted, False if not found
        """
        try:
            result = await self.db.execute(
                select(OAuthToken)
                .where(and_(
                    OAuthToken.user_id == user_id,
                    OAuthToken.service == service
                ))
            )
            token = result.scalars().first()
            
            if not token:
                return False
                
            await self.db.delete(token)
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting OAuth token: {str(e)}")
            raise
