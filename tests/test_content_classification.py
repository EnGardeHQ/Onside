import pytest
from src.services.content.content_classification_service import ContentClassificationService

@pytest.fixture
def classification_service():
    return ContentClassificationService()

@pytest.fixture
def sample_content():
    return """
    Artificial Intelligence in Business: A Comprehensive Guide
    
    Artificial Intelligence (AI) is revolutionizing how businesses operate in the modern world.
    This comprehensive guide explores the practical applications of AI in business operations,
    from automation to decision-making processes.
    
    Key benefits of AI implementation include:
    1. Increased efficiency
    2. Cost reduction
    3. Better decision-making
    4. Enhanced customer experience
    
    However, businesses must also consider challenges such as:
    - Implementation costs
    - Training requirements
    - Ethical considerations
    
    Contact us to learn more about how AI can transform your business operations.
    """

@pytest.mark.asyncio
async def test_classify_content(classification_service, sample_content):
    result = await classification_service.classify_content(sample_content)

    # Verify structure
    assert "topics" in result
    assert "style" in result
    assert "format" in result
    assert "emotions" in result
    assert "sentiment" in result
    assert "linguistics" in result
    assert "readability" in result
    assert "structure" in result
    assert "metadata" in result

    # Verify topics
    topics = result["topics"]
    assert "primary_topics" in topics
    assert "secondary_topics" in topics
    assert "topic_relationships" in topics
    assert len(topics["primary_topics"]) > 0

    # Verify style
    style = result["style"]
    assert "primary_style" in style
    assert "style_confidence" in style
    assert 0 <= style["style_confidence"] <= 1

    # Verify format
    format_data = result["format"]
    assert "detected_format" in format_data
    assert "format_confidence" in format_data
    assert 0 <= format_data["format_confidence"] <= 1

@pytest.mark.asyncio
async def test_topic_classification(classification_service, sample_content):
    topics = await classification_service._classify_topics(sample_content)

    assert "primary_topics" in topics
    assert "secondary_topics" in topics
    assert len(topics["primary_topics"]) > 0
    
    # Verify AI/Technology is identified as a primary topic
    primary_topics = [topic.lower() for topic in topics["primary_topics"]]
    assert any("artificial intelligence" in topic or "technology" in topic 
              for topic in primary_topics)

@pytest.mark.asyncio
async def test_style_analysis(classification_service, sample_content):
    style = await classification_service._analyze_style(sample_content)

    assert "primary_style" in style
    assert "style_confidence" in style
    assert "style_elements" in style
    assert "writing_patterns" in style
    
    # Verify it's detected as a formal/technical style
    assert style["primary_style"] in ["Formal", "Technical"]

@pytest.mark.asyncio
async def test_emotion_analysis(classification_service, sample_content):
    emotions = await classification_service._analyze_emotions(sample_content)

    assert "primary_emotions" in emotions
    assert "emotional_flow" in emotions
    assert "emotional_consistency" in emotions
    
    # Verify emotion scores are within range
    for emotion in emotions["primary_emotions"]:
        assert 0 <= emotion["intensity"] <= 1

@pytest.mark.asyncio
async def test_sentiment_analysis(classification_service, sample_content):
    sentiment = await classification_service._analyze_sentiment(sample_content)

    assert "overall_sentiment" in sentiment
    assert "sentiment_score" in sentiment
    assert "sentiment_distribution" in sentiment
    assert "sentiment_stability" in sentiment
    
    # Verify sentiment score range
    assert 0 <= sentiment["sentiment_score"] <= 1

@pytest.mark.asyncio
async def test_readability_analysis(classification_service, sample_content):
    readability = await classification_service._analyze_readability(sample_content)

    assert "readability_scores" in readability
    scores = readability["readability_scores"]
    
    # Verify all readability scores are present
    assert "flesch_kincaid" in scores
    assert "gunning_fog" in scores
    assert "smog_index" in scores
    
    # Verify score ranges
    for score_name, score_value in scores.items():
        assert 0 <= score_value <= 100

@pytest.mark.asyncio
async def test_structure_analysis(classification_service, sample_content):
    structure = await classification_service._analyze_structure(sample_content)

    assert "section_breakdown" in structure
    assert "coherence_score" in structure
    assert "flow_analysis" in structure
    assert "structural_balance" in structure
    
    # Verify coherence score range
    assert 0 <= structure["coherence_score"] <= 1

@pytest.mark.asyncio
async def test_error_handling(classification_service):
    # Test with empty content
    with pytest.raises(Exception):
        await classification_service.classify_content("")

    # Test with non-text content
    with pytest.raises(Exception):
        await classification_service.classify_content("123456789")

    # Test with extremely long content
    long_content = "test " * 10000
    with pytest.raises(Exception):
        await classification_service.classify_content(long_content)
