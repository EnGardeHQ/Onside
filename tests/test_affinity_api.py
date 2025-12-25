from datetime import datetime
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.auth.models import User
from src.models.ai import AIInsight, InsightType
from src.auth.security import create_access_token, get_current_user
from src.database.config import get_db
from src.services.ai.content_affinity import ContentAffinityService

class MockContent:
    def __init__(self, id, user_id, title, content_text, content_metadata, created_at, updated_at, insights):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.content_text = content_text
        self.content_metadata = content_metadata
        self.created_at = created_at
        self.updated_at = updated_at
        self.insights = insights

class MockUser:
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

class MockAIInsight:
    def __init__(self, content_id, type, score, confidence, insight_metadata):
        self.content_id = content_id
        self.type = type
        self.score = score
        self.confidence = confidence
        self.insight_metadata = insight_metadata

@pytest.fixture
def mock_db():
    """Create a mock database session"""
    mock_db = AsyncMock(spec=AsyncSession)
    
    # Mock execute method
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result
    
    # Mock commit and rollback
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    return mock_db

@pytest.fixture
def mock_user():
    """Create a mock user"""
    return MockUser(id=1, username="test_user", email="test@example.com")

@pytest.fixture
def mock_token(mock_user):
    """Create a mock JWT token"""
    token_data = {
        "sub": str(mock_user.id),
        "email": mock_user.email,
        "username": mock_user.username
    }
    return create_access_token(token_data)

@pytest.fixture
def sample_contents():
    """Create sample content objects for testing"""
    return [
        MockContent(
            id=1,
            user_id=1,
            title="Test Content 1",
            content_text="This is test content 1",
            content_metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            insights=[]
        ),
        MockContent(
            id=2,
            user_id=1,
            title="Test Content 2",
            content_text="This is test content 2",
            content_metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            insights=[]
        )
    ]

@pytest.fixture
def mock_affinity_service():
    """Create a mock ContentAffinityService"""
    mock_service = AsyncMock(spec=ContentAffinityService)
    
    async def mock_calculate_affinity(target_content, comparison_contents, db):
        insights = []
        for content in comparison_contents:
            insight = MockAIInsight(
                content_id=content.id,
                type=InsightType.TOPIC,
                score=0.85,  # Mock similarity score
                confidence=1.0,
                insight_metadata={
                    "target_content_id": target_content.id,
                    "similarity_method": "cosine"
                }
            )
            insights.append(insight)
        return insights
    
    mock_service.calculate_content_affinity = mock_calculate_affinity
    return mock_service

@pytest.fixture
async def client(mock_db, mock_user, mock_affinity_service):
    """Create a TestClient with mocked dependencies"""
    from src.main import app

    async def override_get_current_user():
        return mock_user

    async def override_get_db():
        yield mock_db

    # Override dependencies
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db
    
    # Patch the ContentAffinityService
    with patch('src.api.routes.ai_insights.affinity_service', mock_affinity_service):
        # Create test client
        test_client = TestClient(app)
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_content_affinity_api_endpoint(
    client,
    mock_db,
    mock_user,
    sample_contents,
    mock_token
):
    """Test the content affinity API endpoint"""
    # Setup
    target_id = sample_contents[0].id
    comparison_id = sample_contents[1].id

    # Mock database queries
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.side_effect = [sample_contents[0]]  # For target content
    mock_result.scalars.return_value.all.return_value = [sample_contents[1]]  # For comparison content
    mock_db.execute.return_value = mock_result

    # Make request
    response = client.post(
        f"/api/ai/affinity/calculate?target_id={target_id}&comparison_ids={comparison_id}",
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    # Print error response for debugging
    if response.status_code != 200:
        print(f"Error Response: {response.json()}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "affinity_scores" in data
    assert isinstance(data["affinity_scores"], list)
    assert len(data["affinity_scores"]) == 1
    assert data["affinity_scores"][0]["content_id"] == comparison_id
    assert data["affinity_scores"][0]["score"] >= 0.0
    assert data["affinity_scores"][0]["score"] <= 1.0
    assert data["affinity_scores"][0]["confidence"] == 1.0
    assert "metadata" in data["affinity_scores"][0]

@pytest.mark.asyncio
async def test_content_affinity_invalid_content(
    client,
    mock_db,
    mock_user,
    mock_token
):
    """Test the content affinity API endpoint with invalid content ID"""
    # Setup
    target_id = 999  # Non-existent ID
    comparison_id = 1000  # Non-existent ID

    # Mock database queries to return None for non-existent content
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    # Make request
    response = client.post(
        f"/api/ai/affinity/calculate?target_id={target_id}&comparison_ids={comparison_id}",
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()

@pytest.mark.asyncio
async def test_content_affinity_invalid_comparison_ids(
    client,
    mock_db,
    mock_user,
    mock_token
):
    """Test the content affinity API endpoint with invalid comparison IDs format"""
    # Setup
    target_id = 1
    comparison_ids = "invalid,format"

    # Make request
    response = client.post(
        f"/api/ai/affinity/calculate?target_id={target_id}&comparison_ids={comparison_ids}",
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    # Assertions
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "Invalid comparison_ids format" in data["detail"]
