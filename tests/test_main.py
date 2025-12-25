import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the app instance and create_app function
from src.main import create_app, app
from src.config import Config
from src.database.config import get_db

@pytest.fixture
def mock_config():
    return Config(
        database_url='sqlite:///test.db',
        secret_key='test_secret',
        environment='test',
        api_version='v1',
        log_level='DEBUG',
        allowed_origins=["*"]
    )

@pytest.fixture
def test_app(mock_config):
    with patch('src.config.load_config', return_value=mock_config):
        return create_app()

@pytest.fixture
def test_client(test_app, db_session):
    """Create a new FastAPI TestClient with the test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    test_app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(test_app) as client:
        yield client
    
    test_app.dependency_overrides.clear()

@pytest.fixture
async def async_test_client(test_app):
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client

def test_app_startup(test_client):
    """Test application startup and root endpoint"""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Capilytics API"}

def test_cors_middleware(test_client):
    """Test CORS middleware configuration"""
    response = test_client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers

def test_router_registration(test_client):
    """Test that all routers are properly registered"""
    # Test auth endpoints
    response = test_client.post("/api/auth/register")
    assert response.status_code in [400, 422]  # Validation error is expected, but route exists
    
    # Test data ingestion endpoints
    response = test_client.post("/api/data/upload")
    assert response.status_code in [401, 422]  # Auth/validation error expected, but route exists
    
    # Test AI insights endpoints
    response = test_client.get("/api/ai")  # Base endpoint
    assert response.status_code == 404  # Base endpoint should not exist
    
    # Test recommendations endpoints
    response = test_client.get("/api/recommendations")  # Base endpoint
    assert response.status_code == 404  # Base endpoint should not exist

def test_health_check(test_client):
    """Test health check endpoint"""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_api_docs_endpoints(test_client):
    """Test API documentation endpoints"""
    # Test Swagger UI endpoint
    response = test_client.get("/api/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()
    
    # Test ReDoc endpoint
    response = test_client.get("/api/redoc")
    assert response.status_code == 200
    assert "redoc" in response.text.lower()

def test_app_creation(mock_config):
    """Test application creation and configuration"""
    with patch('src.config.load_config', return_value=mock_config):
        test_app = create_app()
        # Verify FastAPI configuration
        assert test_app.title == "Capilytics API"
        assert test_app.description == "API for content analytics and insights"
        assert test_app.version == "1.0.0"
        assert test_app.docs_url == "/api/docs"
        assert test_app.redoc_url == "/api/redoc"
        
        # Verify router registration
        route_paths = [route.path for route in test_app.routes]
        assert any("/api/auth" in path for path in route_paths)
        assert any("/api/data" in path for path in route_paths)
        assert any("/api/ai" in path for path in route_paths)
        assert any("/api/recommendations" in path for path in route_paths)
        assert any("/api/reports" in path for path in route_paths)
        assert any("/api/audience" in path for path in route_paths)

@pytest.mark.asyncio
async def test_app_startup_async(async_test_client):
    assert async_test_client is not None

@pytest.mark.asyncio
async def test_cors_middleware_async(async_test_client):
    response = await async_test_client.options("/")
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

@pytest.mark.asyncio
async def test_router_registration_async(async_test_client):
    response = await async_test_client.get("/api/v1/health")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_health_check_async(async_test_client):
    response = await async_test_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_api_docs_endpoints_async(async_test_client):
    response = await async_test_client.get("/docs")
    assert response.status_code == 200
    response = await async_test_client.get("/redoc")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_app_creation_async(async_test_client):
    assert async_test_client is not None
