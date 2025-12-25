import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import text
from src.services.ai.sentiment_analysis import SentimentAnalysisService
from src.models.content import Content
from src.auth.models import User

@pytest.fixture
def sentiment_service():
    """Create a sentiment analysis service instance"""
    return SentimentAnalysisService()

@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session

@pytest.fixture
def mock_content():
    content = MagicMock(spec=Content)
    content.id = 1
    content.user_id = 1
    content.title = "Test Title"
    content.content_text = "Test content text for sentiment analysis"
    content.content_metadata = {}
    content.created_at = datetime.now()
    content.updated_at = datetime.now()
    return content

@pytest.mark.asyncio
async def test_analyze_sentiment(mock_db_session: AsyncSession):
    """Test sentiment analysis for a single piece of content."""
    # Create test content
    content = Content(
        id=1,
        user_id=1,
        title="Test Content",
        content_text="This is a very positive and engaging piece of content!",
        content_type="article"
    )
    
    # Initialize service
    service = SentimentAnalysisService()
    
    # Analyze sentiment
    sentiment = await service.analyze_sentiment(content, mock_db_session)
    
    # Assertions
    assert sentiment is not None
    assert "score" in sentiment
    assert "confidence" in sentiment
    assert -1 <= sentiment["score"] <= 1
    assert 0 <= sentiment["confidence"] <= 1

@pytest.mark.asyncio
async def test_analyze_sentiment_batch(mock_db_session: AsyncSession):
    """Test batch sentiment analysis."""
    # Create test content
    contents = [
        Content(
            id=1,
            user_id=1,
            title="Test Content 1",
            content_text="This is positive content!",
            content_type="article"
        ),
        Content(
            id=2,
            user_id=1,
            title="Test Content 2",
            content_text="This is negative content.",
            content_type="article"
        )
    ]
    
    # Initialize service
    service = SentimentAnalysisService()
    
    # Analyze sentiments
    sentiments = await service.analyze_sentiment_batch(contents, mock_db_session)
    
    # Assertions
    assert sentiments is not None
    assert len(sentiments) == 2
    for sentiment in sentiments:
        assert "score" in sentiment
        assert "confidence" in sentiment
        assert -1 <= sentiment["score"] <= 1
        assert 0 <= sentiment["confidence"] <= 1

@pytest.mark.asyncio
async def test_analyze_sentiment_empty_content(mock_db_session: AsyncSession):
    """Test sentiment analysis with empty content."""
    content = Content(
        id=1,
        user_id=1,
        title="Empty Content",
        content_text="",
        content_type="article"
    )
    
    service = SentimentAnalysisService()
    sentiment = await service.analyze_sentiment(content, mock_db_session)
    
    assert sentiment is not None
    assert sentiment["score"] == 0
    assert sentiment["confidence"] == 0

@pytest.mark.asyncio
async def test_analyze_sentiment_invalid_input(mock_db_session: AsyncSession):
    """Test sentiment analysis with invalid input."""
    with pytest.raises(ValueError):
        service = SentimentAnalysisService()
        await service.analyze_sentiment(None, mock_db_session)

@pytest.mark.asyncio
async def test_analyze_sentiment_with_context(mock_db_session: AsyncSession):
    """Test sentiment analysis with context consideration."""
    content = Content(
        id=1,
        user_id=1,
        title="Test Content",
        content_text="The product has some issues but overall it's great!",
        content_type="article"
    )
    
    service = SentimentAnalysisService()
    sentiment = await service.analyze_sentiment(
        content,
        mock_db_session,
        context={"domain": "product_review"}
    )
    
    assert sentiment is not None
    assert "score" in sentiment
    assert "confidence" in sentiment
    assert "context_factors" in sentiment

@pytest.mark.asyncio
async def test_analyze_sentiment(sentiment_service, mock_db_session, mock_content):
    """Test sentiment analysis for a single content item"""
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = mock_content
    mock_db_session.execute.return_value = mock_result

    result = await sentiment_service.analyze_content_sentiment(1, session=mock_db_session)
    
    assert result is not None
    assert "sentiment_score" in result
    assert "sentiment_magnitude" in result
    assert isinstance(result["sentiment_score"], float)
    assert isinstance(result["sentiment_magnitude"], float)

@pytest.mark.asyncio
async def test_analyze_sentiment_batch(sentiment_service, mock_db_session, mock_content):
    """Test sentiment analysis for multiple content items"""
    # Mock content items
    contents = [
        MagicMock(spec=Content, id=1, user_id=1, title="Title 1", content_text="Content 1"),
        MagicMock(spec=Content, id=2, user_id=1, title="Title 2", content_text="Content 2")
    ]

    # Mock database queries
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = mock_content
    mock_db_session.execute.return_value = mock_result

    # Test batch analysis
    content_ids = [c.id for c in contents]
    results = await sentiment_service.analyze_batch_sentiment(content_ids, session=mock_db_session)
    
    assert len(results) == 2
    for result in results:
        assert "content_id" in result
        assert "sentiment_score" in result
        assert "sentiment_magnitude" in result

@pytest.mark.asyncio
async def test_analyze_sentiment_empty_content(sentiment_service, mock_db_session):
    """Test sentiment analysis with empty content"""
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    with pytest.raises(ValueError, match="Content not found"):
        await sentiment_service.analyze_content_sentiment(999, session=mock_db_session)

@pytest.mark.asyncio
async def test_analyze_sentiment_invalid_input(sentiment_service, mock_db_session):
    """Test sentiment analysis with invalid input"""
    with pytest.raises(ValueError, match="Invalid content ID"):
        await sentiment_service.analyze_content_sentiment(None, session=mock_db_session)

@pytest.mark.asyncio
async def test_analyze_sentiment_with_context(sentiment_service, mock_db_session, mock_content):
    """Test sentiment analysis with additional context"""
    context = {"industry": "tech", "audience": "developers"}

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = mock_content
    mock_db_session.execute.return_value = mock_result

    result = await sentiment_service.analyze_content_sentiment(
        1,
        context=context,
        session=mock_db_session
    )
    
    assert result is not None
    assert "sentiment_score" in result
    assert "sentiment_magnitude" in result
    assert "context" in result
    assert result["context"] == context
