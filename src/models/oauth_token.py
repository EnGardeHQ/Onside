"""OAuth2 Token Model

This module defines the database model for storing OAuth2 tokens.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from src.database import Base

class OAuthToken(Base):
    """Model for storing OAuth2 tokens for different services."""
    __tablename__ = 'oauth_tokens'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    service = Column(String(50), nullable=False, index=True)  # e.g., 'google_analytics'
    
    # OAuth2 token data
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    token_uri = Column(String(255))
    client_id = Column(String(255))
    client_secret = Column(String(255))
    scopes = Column(Text)  # Space-separated list of scopes
    
    # Token expiration
    expires_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='oauth_tokens')
    
    def __repr__(self):
        return f"<OAuthToken(user_id={self.user_id}, service='{self.service}')>"
    
    def to_dict(self):
        """Convert the token to a dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'service': self.service,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_uri': self.token_uri,
            'client_id': self.client_id,
            'scopes': self.scopes.split() if self.scopes else [],
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
