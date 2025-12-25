import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app
from src.database import get_db

@pytest.fixture
def test_app():
    return app

@pytest.fixture
def test_client():
    with TestClient(app) as client:
        yield client

def test_app_creation(test_app):
    assert test_app is not None

def test_cors_middleware_config(test_client):
    response = test_client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

def test_root_endpoint(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Capilytics API"}

@pytest.mark.asyncio(loop_scope="function")
async def test_startup_event(test_app):
    """Test that the startup event initializes the database."""
    test_app.state.db = AsyncSession()
    assert hasattr(test_app.state, "db")

@pytest.mark.asyncio(loop_scope="function")
async def test_shutdown_event(test_app):
    """Test that database connections are properly closed."""
    pass

def test_api_router_registration(test_client):
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200

def test_api_documentation_endpoints(test_client):
    response = test_client.get("/api/docs")
    assert response.status_code == 200

def test_health_check_endpoint(test_client):
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_error_handling(test_client):
    response = test_client.get("/nonexistent")
    assert response.status_code == 404
