import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.ai.predictive_insights import PredictiveInsightsService
from src.models.content import Content
from src.models.ai import AIInsight, InsightType
from src.services.ai.llm_service import LLMService
from tests.utils import MockContent, MockEngagement, get_mock_db_session

# BDD-style tests for the enhanced PredictiveInsightsService with LLM and fallback mechanisms
    
@pytest.fixture
def mock_db():
    """Fixture for mocking database session"""
    db = get_mock_db_session()
    return db
    
@pytest.fixture
def insights_service():
    """Fixture for predictive insights service"""
    service = PredictiveInsightsService()
    return service
    
@pytest.fixture
def mock_content():
    """Fixture for mock content with engagement data"""
    content = MockContent(
        id=1,
        title="Test Content for Prediction",
        text="This is test content for testing predictive insights",
        user_id=1,
        created_at=datetime.now() - timedelta(days=30)
    )
    
    # Mock engagement data history
    engagement_data = []
    base_date = datetime.now() - timedelta(days=30)
    for i in range(30):
        current_date = base_date + timedelta(days=i)
        engagement_data.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "views": 100 + i * 10,
            "likes": 20 + i * 2,
            "shares": 5 + i,
            "comments": 10 + i
        })
    
    content.engagement_data = engagement_data
    return content
    
    @pytest.fixture
    def mock_prophet_service(self):
        """Mock Prophet time series prediction service"""
        with patch('src.services.ai.predictive_insights.Prophet') as mock_prophet:
            prophet_instance = mock_prophet.return_value
            prophet_instance.fit = MagicMock()
            prophet_instance.make_future_dataframe = MagicMock()
            prophet_instance.predict = MagicMock(return_value=pd.DataFrame({
                'ds': pd.date_range(start=datetime.now(), periods=7),
                'yhat': [200, 210, 220, 230, 240, 250, 260],
                'yhat_lower': [180, 190, 200, 210, 220, 230, 240],
                'yhat_upper': [220, 230, 240, 250, 260, 270, 280]
            }))
            yield prophet_instance
    
    @pytest.mark.asyncio
    async def test_prophet_prediction_success(self, insights_service, mock_db, mock_content, mock_prophet_service):
        """Should successfully predict trends using Prophet when it works"""
        # Arrange
        # Mock data preparation to return a valid DataFrame for Prophet
        with patch.object(insights_service, '_prepare_data_for_prophet', return_value=pd.DataFrame({
            'ds': pd.date_range(start=datetime.now() - timedelta(days=30), periods=30),
            'y': [100 + i * 10 for i in range(30)]
        })):
            # Act
            insight = await insights_service.predict_engagement_trends(
                mock_content, 
                mock_db, 
                days_ahead=7,
                with_reasoning=False
            )
            
            # Assert
            assert insight is not None
            assert insight.content_id == mock_content.id
            assert insight.score > 0
            assert "forecast" in insight.metadata
            assert len(insight.metadata["forecast"]) > 0
            # Should not include reasoning chain when not requested
            assert "reasoning_chain" not in insight.metadata
    
    @pytest.mark.asyncio
    async def test_prophet_prediction_with_reasoning(self, insights_service, mock_db, mock_content, mock_prophet_service):
        """Should include chain-of-thought reasoning when requested"""
        # Arrange
        # Mock data preparation to return a valid DataFrame for Prophet
        with patch.object(insights_service, '_prepare_data_for_prophet', return_value=pd.DataFrame({
            'ds': pd.date_range(start=datetime.now() - timedelta(days=30), periods=30),
            'y': [100 + i * 10 for i in range(30)]
        })):
            # Act
            insight = await insights_service.predict_engagement_trends(
                mock_content, 
                mock_db, 
                days_ahead=7,
                with_reasoning=True
            )
            
            # Assert
            assert insight is not None
            assert "reasoning_chain" in insight.metadata
            assert isinstance(insight.metadata["reasoning_chain"], list)
            assert len(insight.metadata["reasoning_chain"]) > 0
    
    @pytest.mark.asyncio
    async def test_prophet_failure_llm_fallback(self, insights_service, mock_db, mock_content):
        """Should fall back to LLM-based prediction when Prophet fails"""
        # Arrange
        # Make Prophet fail
        with patch('src.services.ai.predictive_insights.Prophet', side_effect=Exception("Prophet failed")):
            # Mock the LLM service for fallback
            with patch.object(LLMService, 'generate_response', new_callable=AsyncMock) as mock_llm:
                # Return a properly formatted JSON string response
                mock_llm.return_value = '''
                {
                    "forecast": {
                        "views": {"day_1": 210, "day_7": 280},
                        "likes": {"day_1": 42, "day_7": 56},
                        "shares": {"day_1": 15, "day_7": 22},
                        "comments": {"day_1": 31, "day_7": 38}
                    },
                    "trend_metrics": {
                        "views_growth_rate": 0.33,
                        "likes_growth_rate": 0.33,
                        "engagement_ratio": 0.42,
                        "virality_score": 0.65
                    }
                }
                '''
                
                # Act
                insight = await insights_service.predict_engagement_trends(
                    mock_content, 
                    mock_db, 
                    days_ahead=7,
                    with_reasoning=True
                )
                
                # Assert
                assert insight is not None
                assert insight.content_id == mock_content.id
                assert "forecast" in insight.metadata
                assert "reasoning_chain" in insight.metadata
                # Verify that a step about Prophet failure and LLM fallback exists
                reasoning_steps = insight.metadata["reasoning_chain"]
                fallback_steps = [step for step in reasoning_steps if "fallback" in str(step).lower()]
                assert len(fallback_steps) > 0
    
    @pytest.mark.asyncio
    async def test_complete_failure_rule_based_fallback(self, insights_service, mock_db, mock_content):
        """Should use rule-based prediction as last resort when both Prophet and LLM fail"""
        # Arrange
        # Make Prophet fail
        with patch('src.services.ai.predictive_insights.Prophet', side_effect=Exception("Prophet failed")):
            # Make the LLM service fail too
            with patch.object(LLMService, 'generate_response', new_callable=AsyncMock) as mock_llm:
                mock_llm.side_effect = Exception("LLM service failed")
                
                # Mock the trend calculation method to return simple metrics
                with patch.object(insights_service, '_calculate_trend_metrics', return_value={
                    "views_growth_rate": 0.25,
                    "likes_growth_rate": 0.2,
                    "engagement_ratio": 0.4,
                    "virality_score": 0.3
                }):
                    # Act
                    insight = await insights_service.predict_engagement_trends(
                        mock_content, 
                        mock_db, 
                        days_ahead=7,
                        with_reasoning=True
                    )
                    
                    # Assert
                    assert insight is not None
                    assert insight.content_id == mock_content.id
                    # Even with both failures, should still have forecast data
                    assert "forecast" in insight.metadata
                    # Should have recommendations from rule-based system
                    assert "recommendations" in insight.metadata
                    assert len(insight.metadata["recommendations"]) > 0
                    # Reasoning chain should show the complete failure path
                    reasoning_steps = insight.metadata["reasoning_chain"]
                    rule_based_steps = [step for step in reasoning_steps if "rule" in str(step).lower()]
                    assert len(rule_based_steps) > 0
    
    def test_get_trend_interpretations(self, insights_service):
        """Should generate correct rule-based interpretations based on trend metrics"""
        # Arrange
        trend_metrics = {
            "views_growth_rate": 0.25,  # Positive growth
            "likes_growth_rate": -0.1,  # Negative growth
            "engagement_ratio": 0.4,    # Moderate engagement
            "virality_score": 0.8       # High virality
        }
        
        # Act
        interpretations = insights_service._get_trend_interpretations(trend_metrics)
        
        # Assert
        assert len(interpretations) >= 4  # At least one interpretation per metric
        # Check for specific keywords that should be present based on the metrics
        assert any("increasing" in interp.lower() for interp in interpretations)
        assert any("decreasing" in interp.lower() for interp in interpretations)
        assert any("viral" in interp.lower() for interp in interpretations)
    
    def test_get_content_recommendations(self, insights_service):
        """Should generate appropriate recommendations based on trend metrics"""
        # Arrange - Test with poor metrics
        poor_metrics = {
            "views_growth_rate": -0.25,
            "likes_growth_rate": -0.3,
            "engagement_ratio": 0.1,
            "virality_score": 0.1
        }
        
        # Act
        poor_recommendations = insights_service._get_content_recommendations(poor_metrics)
        
        # Assert
        assert len(poor_recommendations) > 0
        
        # Arrange - Test with good metrics
        good_metrics = {
            "views_growth_rate": 0.25,
            "likes_growth_rate": 0.3,
            "engagement_ratio": 0.6,
            "virality_score": 0.7
        }
        
        # Act
        good_recommendations = insights_service._get_content_recommendations(good_metrics)
        
        # Assert
        assert len(good_recommendations) > 0
        # Recommendations should be different based on metrics
        assert set(poor_recommendations) != set(good_recommendations)
