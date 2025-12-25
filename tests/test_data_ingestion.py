import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.main import app
from src.models.content import Content
from src.models.engagement import EngagementMetrics
from src.auth.models import User
from src.database.config import get_db
from src.auth.security import get_current_user
import io
import json
from datetime import datetime, timezone
from fastapi import status

# Test Fixtures
@pytest.fixture
def mock_db():
    """Create a mock database session"""
    mock = MagicMock(spec=Session)
    return mock

@pytest.fixture
def mock_current_user():
    """Create a mock user"""
    return User(
        id=1,
        email="test@example.com",
        name="Test User",
        role="user"
    )

@pytest.fixture
def mock_token():
    """Create a mock JWT token"""
    return "test-token"

@pytest.fixture
def client(mock_db, mock_current_user):
    """Create a test client with mocked dependencies"""
    def override_get_db():
        return mock_db
        
    def override_get_current_user():
        return mock_current_user
        
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    client = TestClient(app)
    yield client
    
    # Clean up
    app.dependency_overrides.clear()

@pytest.fixture
def mock_content():
    """Create a mock content item"""
    return Content(
        id=1,
        title="Test Content",
        content_type="article",
        source="upload",
        content_metadata={"description": "Test description"},
        user_id=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

@pytest.fixture
def mock_metrics():
    """Create mock social metrics"""
    return [
        EngagementMetrics(
            id=1,
            content_id=1,
            metric_type="likes",
            value=100,
            source="twitter",
            metric_metadata={
                "details": "test",
                "timestamp": "2025-02-03T13:00:00Z"
            }
        ),
        EngagementMetrics(
            id=2,
            content_id=1,
            metric_type="retweets",
            value=50,
            source="twitter",
            metric_metadata={
                "details": "test",
                "timestamp": "2025-02-03T13:00:00Z"
            }
        )
    ]

# Content Upload Tests
def test_upload_content_success(client, mock_db, mock_current_user, mock_token):
    """Test successful content upload"""
    # Setup
    file_content = b"This is a test article about AI and machine learning"
    file = io.BytesIO(file_content)
    metadata = {
        "title": "Test Article",
        "description": "An article about AI",
        "tags": ["AI", "ML"]
    }

    # Mock database operations
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None

    # Create mock content
    mock_content = Content(
        id=1,
        user_id=1,
        content_type="article",
        text=file_content.decode(),
        created_at=datetime.now(timezone.utc)
    )

    # Mock ingestion service
    with patch('src.services.data_ingestion.DataIngestionService.upload_content',
               return_value=mock_content):
        response = client.post(
            "/api/data/upload",
            files={"file": ("test.txt", file, "text/plain")},
            data={"metadata": json.dumps(metadata)},
            headers={"Authorization": f"Bearer {mock_token}"}
        )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == metadata["title"]
    assert data["description"] == metadata["description"]
    assert data["tags"] == metadata["tags"]

def test_upload_content_invalid_metadata(client, mock_db, mock_current_user, mock_token):
    """Test content upload with invalid metadata JSON"""
    # Setup
    file = io.BytesIO(b"test content")

    response = client.post(
        "/api/data/upload",
        files={"file": ("test.txt", file, "text/plain")},
        data={"metadata": "invalid json"},
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "Invalid metadata format" in data["detail"]

def test_upload_content_missing_file(client, mock_db, mock_current_user, mock_token):
    """Test content upload without a file"""
    metadata = {
        "title": "Test Article",
        "description": "An article about AI"
    }

    response = client.post(
        "/api/data/upload",
        data={"metadata": json.dumps(metadata)},
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "field required" in data["detail"][0]["msg"].lower()

def test_upload_content_empty_file(client, mock_db, mock_current_user, mock_token):
    """Test content upload with empty file"""
    file = io.BytesIO(b"")
    metadata = {
        "title": "Test Article",
        "description": "An article about AI"
    }

    response = client.post(
        "/api/data/upload",
        files={"file": ("test.txt", file, "text/plain")},
        data={"metadata": json.dumps(metadata)},
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "Empty file provided" in data["detail"]

# Social Metrics Tests
def test_fetch_social_metrics_success(client, mock_db, mock_current_user, mock_token):
    """Test successful social metrics retrieval"""
    # Mock data
    mock_content = Content(
        id=1,
        user_id=1,
        content_type="article",
        text="Test article",
        created_at=datetime.now(timezone.utc)
    )
    mock_metrics = [
        EngagementMetrics(
            id=1,
            content_id=1,
            metric_type="likes",
            value=100,
            source="twitter",
            metric_metadata={
                "details": "test",
                "timestamp": "2025-02-03T13:00:00Z"
            }
        ),
        EngagementMetrics(
            id=2,
            content_id=1,
            metric_type="retweets",
            value=50,
            source="twitter",
            metric_metadata={
                "details": "test",
                "timestamp": "2025-02-03T13:00:00Z"
            }
        )
    ]
    mock_db.query.return_value.filter.return_value.first.return_value = mock_content
    mock_db.query.return_value.filter.return_value.all.return_value = mock_metrics

    response = client.get(
        "/api/data/social/1?platform=twitter",
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["metrics"]) == 2
    assert data["metrics"][0]["metric_type"] == "likes"
    assert data["metrics"][0]["value"] == 100
    assert data["metrics"][1]["metric_type"] == "retweets"
    assert data["metrics"][1]["value"] == 50

def test_fetch_social_metrics_content_not_found(client, mock_db, mock_current_user, mock_token):
    """Test social metrics retrieval for non-existent content"""
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.get(
        "/api/data/social/999?platform=twitter",
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "Content not found" in data["detail"]

def test_fetch_social_metrics_invalid_platform(client, mock_db, mock_current_user, mock_token):
    """Test social metrics retrieval with invalid platform"""
    mock_content = Content(
        id=1,
        user_id=1,
        content_type="article",
        text="Test article",
        created_at=datetime.now(timezone.utc)
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_content

    response = client.get(
        "/api/data/social/1?platform=invalid",
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "Invalid platform" in data["detail"]

def test_fetch_social_metrics_no_metrics(client, mock_db, mock_current_user, mock_token):
    """Test social metrics retrieval when no metrics exist"""
    # Mock database queries
    mock_content = Content(
        id=1,
        user_id=1,
        content_type="article",
        text="Test article",
        created_at=datetime.now(timezone.utc)
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_content
    mock_db.query.return_value.filter.return_value.all.return_value = []

    response = client.get(
        "/api/data/social/1?platform=twitter",
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["metrics"]) == 0
