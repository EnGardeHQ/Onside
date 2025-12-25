"""
Tests for Google OAuth2 integration.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from src.auth.google_oauth import GoogleOAuth

def test_google_oauth_initialization():
    """Test GoogleOAuth initialization with default config."""
    oauth = GoogleOAuth()
    assert oauth is not None
    assert hasattr(oauth, 'client_config')
    assert 'web' in oauth.client_config

def test_get_authorization_url():
    """Test generating authorization URL."""
    oauth = GoogleOAuth()
    auth_url = oauth.get_authorization_url()
    
    assert auth_url.startswith('https://accounts.google.com/o/oauth2/auth')
    assert 'access_type=offline' in auth_url
    assert 'prompt=consent' in auth_url

@patch('google_auth_oauthlib.flow.Flow')
def test_get_tokens(mock_flow):
    """Test exchanging authorization code for tokens."""
    # Setup mock flow
    mock_flow_instance = MagicMock()
    mock_flow_instance.fetch_token.return_value = {
        'access_token': 'test_access_token',
        'refresh_token': 'test_refresh_token',
        'expires_in': 3600,
        'token_type': 'Bearer'
    }
    mock_flow.from_client_config.return_value = mock_flow_instance
    
    oauth = GoogleOAuth()
    tokens = oauth.get_tokens('test_code')
    
    assert tokens['token'] == 'test_access_token'
    assert tokens['refresh_token'] == 'test_refresh_token'
    mock_flow_instance.fetch_token.assert_called_once_with(code='test_code')

def test_get_credentials():
    """Test creating Credentials object from token info."""
    token_info = {
        'token': 'test_token',
        'refresh_token': 'test_refresh',
        'token_uri': 'https://test.com/token',
        'client_id': 'test_client_id',
        'client_secret': 'test_secret',
        'scopes': ['scope1', 'scope2']
    }
    
    credentials = GoogleOAuth.get_credentials(token_info)
    
    assert credentials.token == 'test_token'
    assert credentials.refresh_token == 'test_refresh'
    assert credentials.token_uri == 'https://test.com/token'
    assert credentials.client_id == 'test_client_id'
    assert credentials.client_secret == 'test_secret'
    assert credentials.scopes == ['scope1', 'scope2']

@patch('google.oauth2.credentials.Credentials')
def test_refresh_credentials(mock_credentials):
    """Test refreshing expired credentials."""
    # Setup mock credentials
    mock_creds = MagicMock()
    mock_creds.valid = False
    mock_creds.refresh.return_value = True
    
    # Test refresh needed and successful
    result = GoogleOAuth.refresh_credentials(mock_creds)
    assert result is True
    mock_creds.refresh.assert_called_once()
    
    # Test no refresh needed
    mock_creds.valid = True
    result = GoogleOAuth.refresh_credentials(mock_creds)
    assert result is False
    assert mock_creds.refresh.call_count == 1  # Still only called once
    
    # Test refresh failure
    mock_creds.valid = False
    mock_creds.refresh.side_effect = Exception("Refresh failed")
    result = GoogleOAuth.refresh_credentials(mock_creds)
    assert result is False
