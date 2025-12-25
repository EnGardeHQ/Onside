"""Tests for content affinity calculation functionality."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers import SentenceTransformer

from src.services.ai.content_affinity import ContentAffinityService
from src.models import Content, AIInsight
from src.models.ai import InsightType

class MockContent:
    """Mock Content class for testing."""
    def __init__(self, id, user_id, title, content_text, content_metadata=None):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.content_text = content_text
        self.content_metadata = content_metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.insights = []

@pytest.fixture
def mock_sentence_transformer():
    """Create a mock sentence transformer."""
    mock = MagicMock(spec=SentenceTransformer)
    mock.encode.return_value = np.array([[0.5] * 384])  # Match model's embedding size
    return mock

@pytest.fixture
def sample_contents():
    """Create sample content objects for testing."""
    return [
        MockContent(
            id=1,
            user_id=1,
            title="Test Content 1",
            content_text="This is test content 1"
        ),
        MockContent(
            id=2,
            user_id=1,
            title="Test Content 2",
            content_text="This is test content 2"
        )
    ]

@pytest.mark.asyncio
async def test_content_affinity_calculation(
    db_session: AsyncSession,
    mock_sentence_transformer,
    sample_contents
):
    """Test the content affinity calculation service."""
    # Setup
    service = ContentAffinityService()
    target_content = sample_contents[0]
    comparison_contents = [sample_contents[1]]

    # Mock database queries
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = target_content
    mock_result.scalars.return_value.all.return_value = comparison_contents
    db_session.execute = AsyncMock(return_value=mock_result)

    # Mock the SentenceTransformer
    with patch(
        'src.services.ai.content_affinity.SentenceTransformer',
        return_value=mock_sentence_transformer
    ):
        insights = await service.calculate_content_affinity(
            target_content,
            comparison_contents,
            db_session
        )

    # Assertions
    assert len(insights) == len(comparison_contents)
    assert isinstance(insights[0], AIInsight)
    assert insights[0].content_id == comparison_contents[0].id
    assert insights[0].type == InsightType.TOPIC
    assert 0 <= insights[0].score <= 1
    assert insights[0].confidence > 0

@pytest.mark.asyncio
async def test_content_affinity_empty_content(
    db_session: AsyncSession,
    mock_sentence_transformer,
    sample_contents
):
    """Test content affinity calculation with empty content."""
    # Setup
    service = ContentAffinityService()
    empty_content = MockContent(
        id=3,
        user_id=1,
        title="",
        content_text=""
    )

    # Mock database queries
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = empty_content
    mock_result.scalars.return_value.all.return_value = [sample_contents[0]]
    db_session.execute = AsyncMock(return_value=mock_result)

    # Mock the SentenceTransformer
    with patch(
        'src.services.ai.content_affinity.SentenceTransformer',
        return_value=mock_sentence_transformer
    ):
        insights = await service.calculate_content_affinity(
            empty_content,
            [sample_contents[0]],
            db_session
        )

    # Assertions
    assert len(insights) == 1
    assert insights[0].score >= 0.0  # Empty content should have low but not zero affinity
    assert insights[0].score <= 1.0
    assert insights[0].confidence > 0
