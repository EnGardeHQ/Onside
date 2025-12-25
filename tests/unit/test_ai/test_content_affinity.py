import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import numpy as np
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.ai.content_affinity import ContentAffinityService
from src.models.content import Content
from src.models.ai import AIInsight, InsightType
from src.services.ai.llm_service import LLMService
from tests.utils import MockContent, get_mock_db_session

# BDD-style tests for the ContentAffinityService with LLM fallback capabilities
    
@pytest.fixture
def mock_db():
    """Fixture for mocking database session"""
    return get_mock_db_session()
    
@pytest.fixture
def content_service():
    """Fixture for content affinity service"""
    with patch('src.services.ai.content_affinity.SentenceTransformer'):
        service = ContentAffinityService()
        service.model.encode = MagicMock(side_effect=lambda x: 
                                        [np.random.rand(384) for _ in range(len(x))] if isinstance(x, list) 
                                        else np.random.rand(384))
        return service
    
@pytest.fixture
def mock_content():
    """Fixture for mock content"""
    return MockContent(
        id=1,
        title="Test Content",
        text="This is test content for testing affinity service",
        user_id=1,
        metadata={"source": "test", "format": "text"}
    )

@pytest.fixture
def mock_comparison_contents():
    """Fixture for mock comparison contents"""
    contents = []
    for i in range(3):
        content = MockContent(
            id=i + 2,
            title=f"Comparison Content {i+1}",
            text=f"This is comparison content number {i+1} for testing",
            user_id=1,
            metadata={"source": "test", "format": "text"}
        )
        contents.append(content)
    return contents
    
@pytest.mark.asyncio
async def test_embedding_based_similarity_calculation(content_service, mock_db, mock_content, mock_comparison_contents):
        """Should calculate similarities using embeddings when everything works"""
        # Arrange
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_content
        
        # Mock the LLM service to avoid actual API calls
        with patch.object(LLMService, 'generate_response', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "0.75000"
            
            # Act
            insights = await content_service.calculate_content_affinity(
                mock_content, 
                mock_comparison_contents, 
                mock_db
            )
            
            # Assert
            assert len(insights) == len(mock_comparison_contents)
            assert all(isinstance(insight, AIInsight) for insight in insights)
            assert all(insight.type == InsightType.TOPIC for insight in insights)
            assert all(0 <= insight.score <= 1 for insight in insights)
            assert all(insight.confidence <= 1.0 for insight in insights)
            assert mock_db.commit.called
    
@pytest.mark.asyncio
async def test_llm_enhanced_similarity_calculation(content_service, mock_db, mock_content, mock_comparison_contents):
        """Should enhance similarity scores with LLM for top matches"""
        # Arrange
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_content
        
        # Mock the LLM service to return consistent values for testing
        with patch.object(LLMService, 'generate_response', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "0.85000"
            
            # Act
            insights = await content_service.calculate_content_affinity(
                mock_content, 
                mock_comparison_contents, 
                mock_db,
                with_reasoning=True
            )
            
            # Assert
            assert len(insights) == len(mock_comparison_contents)
            assert all(insight.confidence >= 0.8 for insight in insights)
            # Verify that reasoning chain is included when requested
            assert all("reasoning_chain" in insight.insight_metadata for insight in insights)
            # Verify that explanation is generated
            assert all(insight.explanation is not None and len(insight.explanation) > 0 for insight in insights)
    
@pytest.mark.asyncio
async def test_embedding_failure_llm_fallback(content_service, mock_db, mock_content, mock_comparison_contents):
        """Should fall back to LLM-only similarities when embeddings fail"""
        # Arrange
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_content
        
        # Make the embedding model fail
        content_service.model.encode.side_effect = Exception("Embedding model failed")
        
        # Mock the LLM service for fallback
        with patch.object(LLMService, 'generate_response', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "0.60000"
            
            # Act
            insights = await content_service.calculate_content_affinity(
                mock_content, 
                mock_comparison_contents, 
                mock_db
            )
            
            # Assert
            assert len(insights) == len(mock_comparison_contents)
            assert all(isinstance(insight, AIInsight) for insight in insights)
            # In fallback mode, all scores should be approximately equal to the mocked LLM response
            assert all(0.59 <= insight.score <= 0.61 for insight in insights)
    
@pytest.mark.asyncio
async def test_total_failure_random_fallback(content_service, mock_db, mock_content, mock_comparison_contents):
        """Should use random similarities as last resort when both embeddings and LLM fail"""
        # Arrange
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_content
        
        # Make the embedding model fail
        content_service.model.encode.side_effect = Exception("Embedding model failed")
        
        # Make the LLM service fail
        with patch.object(LLMService, 'generate_response', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("LLM service failed")
            
            # Act
            insights = await content_service.calculate_content_affinity(
                mock_content, 
                mock_comparison_contents, 
                mock_db
            )
            
            # Assert
            assert len(insights) == len(mock_comparison_contents)
            assert all(isinstance(insight, AIInsight) for insight in insights)
            # In last resort mode, scores should be in the random range we defined (0.4-0.6)
            assert all(0.39 <= insight.score <= 0.61 for insight in insights)
    
def test_generate_affinity_explanation(content_service, mock_content, mock_comparison_contents):
        """Should generate appropriate explanations based on affinity score tiers"""
        # Arrange
        comparison = mock_comparison_contents[0]
        
        # Act - Test high affinity explanation
        high_explanation = content_service._generate_affinity_explanation(mock_content, comparison, 0.8)
        
        # Act - Test moderate affinity explanation
        moderate_explanation = content_service._generate_affinity_explanation(mock_content, comparison, 0.6)
        
        # Act - Test low affinity explanation
        low_explanation = content_service._generate_affinity_explanation(mock_content, comparison, 0.3)
        
        # Assert
        assert "strong content affinity" in high_explanation
        assert "moderate content affinity" in moderate_explanation
        assert "minimal content affinity" in low_explanation
        assert mock_content.title in high_explanation
        assert comparison.title in high_explanation
