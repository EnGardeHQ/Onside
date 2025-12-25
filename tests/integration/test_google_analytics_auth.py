"""Integration tests for Google Analytics OAuth2 endpoints."""
import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator, Generator, Any, Dict, Optional
from unittest.mock import patch, MagicMock, AsyncMock, ANY
import pytest
import pytest_asyncio
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select, text, create_engine, exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Set test environment before importing app
os.environ["ENVIRONMENT"] = "test"

# Add the root directory to the Python path
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import the FastAPI app and dependencies
from src.main import app
from src.database import Base, get_db, SessionLocal, engine, init_db
from src.models.user import User, UserRole
from src.models.oauth_token import OAuthToken
from src.core.security import create_access_token, get_password_hash
from src.api.v1.google_analytics import router as google_analytics_router
from src.services.auth.google_oauth import GoogleOAuth

# Create test FastAPI app
def create_test_app():
    app = FastAPI()
    app.include_router(google_analytics_router, prefix="/api/v1/google-analytics")
    return app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test database URL - using the actual database as per project requirements
TEST_DATABASE_URL = "postgresql+asyncpg://tobymorning@localhost/onside"

# Create test engine and session
AsyncTestingSessionLocal = async_sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession
)

# Fixture to create a test app with overridden dependencies
def create_test_app():
    """Create a test FastAPI application with overridden dependencies."""
    # Create a fresh FastAPI app
    test_app = FastAPI()
    
    # Include the router
    test_app.include_router(google_analytics_router)
    
    return test_app

# Database session factory
@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    # Initialize database
    await init_db()
    
    # Create a new session for testing
    session = AsyncTestingSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()

# Override get_db dependency
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncTestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Test application fixture with dependency overrides
@pytest_asyncio.fixture(scope="function")
async def test_app():
    """Create a test FastAPI application with overridden dependencies."""
    # Create test app
    test_app = create_test_app()
    
    # Override dependencies
    test_app.dependency_overrides[get_db] = override_get_db
    
    return test_app

# Test client fixture
@pytest.fixture(scope="function")
def test_client(test_app):
    """Create a test client for the FastAPI application."""
    return TestClient(test_app, raise_server_exceptions=False)

# Test user fixture
@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    # Clean up any existing test users first
    await db_session.execute(text("DELETE FROM users WHERE email LIKE :email"), {"email": "%test%"})
    await db_session.commit()
    
    # Create a test user
    test_user = User(
        email="test@example.com",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # 'secret' hashed
        is_active=True,
        role=UserRole.ADMIN
    )
    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)
    return test_user

# Test token fixture
@pytest.fixture(scope="function")
def test_token(test_user: User):
    """Create a test JWT token."""
    return create_access_token({"sub": str(test_user.id)})

@pytest.mark.asyncio
class TestGoogleAnalyticsAuth:
    """Test Google Analytics OAuth2 endpoints."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, test_client, test_token, test_user, db_session: AsyncSession):
        """Set up test client and test data."""
        self.client = test_client
        self.test_token = test_token
        self.test_user = test_user
        self.db_session = db_session
        self.test_token_data = {
            "access_token": "test_access_token",
            "token_type": "bearer",
            "expires_in": 3600,
            "refresh_token": "test_refresh_token"
        }
        
        # Patch the GoogleOAuth class to return our mock
        self.patcher = patch('src.api.v1.google_analytics.GoogleOAuth')
        self.mock_google_oauth = self.patcher.start()
        self.mock_oauth_instance = AsyncMock()
        self.mock_google_oauth.return_value = self.mock_oauth_instance
        
        # Ensure we have a clean state
        await self.cleanup()
        
        # Add test data
        await self.setup_test_data()
        
        # Run the test
        yield
        
        # Clean up after tests
        await self.cleanup()
        self.patcher.stop()
    
    async def setup_test_data(self):
        """Set up test data in the database."""
        # Create a test OAuth token
        expires_at = datetime.utcnow() + timedelta(days=1)
        oauth_token = OAuthToken(
            user_id=self.test_user.id,
            service="google_analytics",
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            token_uri="https://oauth2.googleapis.com/token",
            client_id="test_client_id",
            client_secret="test_client_secret",
            scopes="https://www.googleapis.com/auth/analytics.readonly",
            expires_at=expires_at
        )
        self.db_session.add(oauth_token)
        await self.db_session.commit()
    
    async def cleanup(self):
        """Clean up test data from the database."""
        # Clean up any test data
        await self.db_session.execute(text("DELETE FROM oauth_tokens"))
        await self.db_session.commit()
    
    async def test_get_auth_url(self):
        """Test getting Google OAuth URL."""
        # Set up the mock return value
        expected_url = "https://accounts.google.com/o/oauth2/auth?test=123"
        self.mock_oauth_instance.get_authorization_url.return_value = expected_url
        
        # Make the request
        response = self.client.get(
            "/api/v1/google-analytics/auth/url",
            params={"redirect_uri": "http://localhost:3000/callback"},
            headers={"Authorization": f"Bearer {self.test_token}"}
        )
        
        # Assert the response
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}. Response: {response.text}"
        data = response.json()
        assert "authorization_url" in data, "Response missing 'authorization_url' field"
        assert "state" in data, "Response missing 'state' field"
        assert data["authorization_url"] == expected_url
        
        # Verify the GoogleOAuth was called with the correct parameters
        self.mock_google_oauth.assert_called_once()
        self.mock_oauth_instance.get_authorization_url.assert_awaited_once_with("http://localhost:3000/callback")
    

    @pytest.mark.asyncio
    async def test_oauth_callback(self):
        """Test OAuth callback with valid code."""
        with patch('src.services.auth.google_oauth.GoogleOAuth.get_access_token') as mock_get_token, \
             patch('src.services.auth.google_oauth.GoogleOAuth.save_token') as mock_save_token:
            
            # Mock the token response
            mock_token_data = {
                'access_token': 'test_access_token',
                'token_type': 'Bearer',
                'expires_in': 3600,
                'refresh_token': 'test_refresh_token',
                'scope': 'https://www.googleapis.com/auth/analytics.readonly'
            }
            mock_get_token.return_value = mock_token_data
            mock_save_token.return_value = MagicMock()
            
            # Make the request with form data
            response = self.client.post(
                "/api/v1/google-analytics/auth/callback",
                data={"code": "test_code"},
                headers={
                    "Authorization": f"Bearer {self.test_token}",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            
            # Assert the response
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["status"] == "success"
            assert response_data["access_token"] == "test_access_token"
            
            # Verify the mocks were called
            mock_get_token.assert_awaited_once_with("test_code", ANY)
            mock_save_token.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_check_auth_status_authenticated(self):
        """Test checking auth status when authenticated."""
        # Make the request
        response = await self.client.get(
            "/api/v1/google-analytics/auth/status",
            headers={"Authorization": f"Bearer {self.test_token}"}
        )
        
        # Assert the response
        assert response.status_code == 200
        data = response.json()
    
    @pytest.mark.asyncio
    async def test_revoke_auth(self):
        """Test revoking Google OAuth access."""
        with patch('src.services.auth.google_oauth.GoogleOAuth') as mock_oauth:
            # Mock the GoogleOAuth class
            mock_instance = AsyncMock()
            mock_instance.revoke_token.return_value = True
            mock_oauth.return_value = mock_instance
            
            # Make the request
            response = await self.client.post(
                "/api/v1/google-analytics/auth/revoke",
                headers={"Authorization": f"Bearer {self.test_token}"}
            )
            
            # Assert the response
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert data["status"] == "success"
            
            # Verify the GoogleOAuth was called with the correct parameters
            mock_oauth.assert_called_once()
            mock_instance.revoke_token.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_oauth_callback_success(self):
        """Test successful OAuth callback."""
        # Mock the GoogleOAuth class
        with patch('src.services.auth.google_oauth.GoogleOAuth') as mock_oauth:
            mock_instance = AsyncMock()
            mock_instance.get_token.return_value = self.test_token_data
            mock_oauth.return_value = mock_instance
            
            # Make the request
            response = await self.client.post(
                "/api/v1/google-analytics/auth/callback",
                headers={"Authorization": f"Bearer {self.test_token}"},
                json={"code": "test_auth_code"}
            )
            
            # Assert the response
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}. Response: {response.text}"
            data = response.json()
            assert "status" in data, "Response missing 'status' field"
            assert data["status"] == "success", f"Expected status 'success', got {data.get('status')}"
            
            # Verify the GoogleOAuth was called with the correct parameters
            mock_oauth.assert_called_once()
            mock_instance.get_token.assert_awaited_once_with("test_auth_code")

    @pytest.mark.asyncio
    async def test_get_ga_properties(self):
        """Test getting Google Analytics properties."""
        with patch('src.services.analytics.google_analytics.GoogleAnalyticsService') as mock_service:
            # Mock the GoogleAnalyticsService
            mock_instance = AsyncMock()
            mock_instance.list_properties.return_value = [
                {"id": "123", "name": "Test Property 1"},
                {"id": "456", "name": "Test Property 2"}
            ]
            mock_service.return_value = mock_instance
            
            # Make the request
            response = await self.client.get(
                "/api/v1/google-analytics/properties",
                headers={"Authorization": f"Bearer {self.test_token}"}
            )
            
            # Assert the response
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]["id"] == "123"
            assert data[1]["name"] == "Test Property 2"
            
            # Verify the service was called with the correct parameters
            mock_service.assert_called_once()
            mock_instance.list_properties.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_get_ga_overview(self):
        """Test getting Google Analytics overview metrics."""
        with patch('src.services.analytics.google_analytics.GoogleAnalyticsService') as mock_service:
            # Mock the GoogleAnalyticsService
            mock_instance = AsyncMock()
            mock_instance.get_overview_metrics.return_value = {
                "users": 100,
                "sessions": 150,
                "pageviews": 300,
                "avgSessionDuration": 120.5
            }
            mock_service.return_value = mock_instance
            
            # Make the request
            response = await self.client.get(
                "/api/v1/google-analytics/overview",
                params={
                    "start_date": "2023-01-01",
                    "end_date": "2023-01-31",
                    "metrics": "users,sessions,pageviews,avgSessionDuration"
                },
                headers={"Authorization": f"Bearer {self.test_token}"}
            )
            
            # Assert the response
            assert response.status_code == 200
            data = response.json()
            assert "users" in data
            assert "sessions" in data
            assert "pageviews" in data
            assert "avgSessionDuration" in data
            
            # Verify the service was called with the correct parameters
            mock_service.assert_called_once()
            mock_instance.get_overview_metrics.assert_awaited_once_with(
                start_date="2023-01-01",
                end_date="2023-01-31",
                metrics=["users", "sessions", "pageviews", "avgSessionDuration"]
            )

    @pytest.mark.asyncio
    async def test_oauth_callback_success(self):
        """Test successful OAuth callback."""
        with patch('src.api.v1.google_analytics.GoogleOAuth') as mock_oauth:
            # Mock the GoogleOAuth class
            mock_instance = AsyncMock()
            mock_instance.get_access_token.return_value = {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "expires_in": 3600,
                "scope": "https://www.googleapis.com/auth/analytics.readonly"
            }
            mock_instance.get_user_info.return_value = {
                "email": "test@example.com",
                "name": "Test User"
            }
            mock_oauth.return_value = mock_instance
            
            # Make the request
            response = self.client.get(
                "/api/v1/google-analytics/oauth2callback",
                params={"code": "test_code", "state": "test_state"},
                headers={"Authorization": f"Bearer {self.test_token}"}
            )
            
            # Assert the response
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Google Analytics account connected successfully"
            
            # Verify the GoogleOAuth methods were called correctly
            mock_oauth.assert_called_once_with(db=self.async_db)
            mock_instance.get_access_token.assert_awaited_once_with(
                code="test_code",
                redirect_uri=ANY
            )
            mock_instance.get_user_info.assert_awaited_once_with(
                access_token="test_access_token"
            )

    @pytest.mark.asyncio
    async def test_get_ga_properties(self):
        """Test getting Google Analytics properties."""
        with patch('src.services.auth.google_oauth.GoogleOAuth.get_token') as mock_get_token, \
             patch('src.services.analytics.google_analytics.GoogleAnalyticsService.get_properties') as mock_get_props:
            
            # Mock a valid token
            mock_token = MagicMock()
            mock_token.access_token = "test_access_token"
            mock_get_token.return_value = mock_token
            
            # Mock the properties
            mock_properties = [
                {"id": "123", "name": "Test Property 1"},
                {"id": "456", "name": "Test Property 2"}
            ]
            mock_get_props.return_value = mock_properties
            
            # Make the request
            response = self.client.get(
                "/api/v1/analytics/properties",
                headers={"Authorization": f"Bearer {self.test_token}"}
            )
            
            # Assert the response
            assert response.status_code == 200
            assert response.json() == mock_properties
            
            # Verify the mocks were called
            mock_get_token.assert_awaited_once()
            mock_get_props.assert_awaited_once()

    async def _get_test_token(self, session: AsyncSession) -> str:
        """Get a test JWT token for the test user."""
        return create_access_token(data={"sub": str(self.test_user.id)})
