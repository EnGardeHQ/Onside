from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from src.database.config import get_db
from src.auth.security import get_current_user
from src.models.content import Content
from src.models.ai import AIInsight
from src.models.user import User
from src.services.ai.sentiment_analysis import SentimentAnalysisService
from src.services.ai.content_affinity import ContentAffinityService
from src.services.ai.predictive_insights import PredictiveInsightsService

router = APIRouter(tags=["AI Insights"])

sentiment_service = SentimentAnalysisService()
affinity_service = ContentAffinityService()
predictive_service = PredictiveInsightsService()

@router.post("/sentiment/analyze/{content_id}", response_model=Dict[str, Any], summary="Analyze Sentiment", description="Analyze sentiment of content using enhanced AI with fallback mechanisms and chain-of-thought reasoning")
async def analyze_sentiment(
    content_id: int,
    with_reasoning: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze sentiment of content using enhanced AI with fallback mechanisms.
    
    This endpoint is part of the Sprint 4 AI/ML enhancements with resilient LLM service integration.
    It uses a circuit breaker pattern and provider fallback mechanisms to ensure reliable operation.
    
    Parameters:
    - **content_id**: ID of the content to analyze sentiment for
    - **with_reasoning**: Whether to include chain-of-thought reasoning in the response (default: False)
    
    Returns:
    - **sentiment_scores**: List of sentiment analysis results with scores, confidence, and explanations
    - **reasoning_chain** (optional): Step-by-step reasoning process if with_reasoning=True
    """
    try:
        # Get content from database
        result = await db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        # Calculate sentiment with resilient LLM service and fallback
        insights = await sentiment_service.analyze_sentiment(
            content=content, 
            db=db,
            with_reasoning=with_reasoning
        )
        
        # Process response
        response = {
            "sentiment_scores": []
        }
        
        for insight in insights:
            score_data = {
                "content_id": insight.content_id,
                "score": insight.score,
                "confidence": insight.confidence,
                "explanation": insight.explanation,
                "sentiment_labels": insight.metadata.get("sentiment_labels", {})
            }
            
            # Include reasoning chain if requested
            if with_reasoning and "reasoning_chain" in insight.metadata:
                score_data["reasoning_chain"] = insight.metadata["reasoning_chain"]
                
            response["sentiment_scores"].append(score_data)
        
        return response
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=404,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing sentiment analysis: {error_msg}"
            )

@router.post("/affinity/calculate", response_model=Dict[str, Any], summary="Calculate Content Affinity", description="Calculate content affinity between target and comparison contents using enhanced AI with fallback mechanisms and chain-of-thought reasoning")
async def calculate_affinity(
    target_id: int,
    comparison_ids: str,
    with_reasoning: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate content affinity between target and comparison contents using enhanced AI with fallback.
    
    This endpoint is part of the Sprint 4 AI/ML enhancements with Content Affinity Service.
    It uses a hybrid approach with embedding-based similarity as the primary method and
    LLM-based semantic comparison as an enhancement, with fallback mechanisms if either fails.
    
    Parameters:
    - **target_id**: ID of the target content to compare against
    - **comparison_ids**: Comma-separated list of content IDs to compare with the target
    - **with_reasoning**: Whether to include chain-of-thought reasoning in the response (default: False)
    
    Returns:
    - **affinity_scores**: List of affinity scores between target and comparison contents
    - **reasoning_chain** (optional): Step-by-step reasoning process if with_reasoning=True
    """
    try:
        # Validate comparison_ids format first
        try:
            comparison_id_list = [int(id_str) for id_str in comparison_ids.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="Invalid comparison_ids format. Expected comma-separated integers."
            )
        
        # Get target content
        result = await db.execute(
            select(Content).where(Content.id == target_id)
        )
        target_content = result.scalar_one_or_none()
        if not target_content:
            raise HTTPException(status_code=404, detail="Target content not found")
        
        # Get comparison content
        result = await db.execute(
            select(Content).where(Content.id.in_(comparison_id_list))
        )
        comparison_content = result.scalars().all()
        if not comparison_content:
            raise HTTPException(status_code=404, detail="Comparison content not found")
        
        # Calculate affinity with enhanced resilient service
        insights = await affinity_service.calculate_content_affinity(
            target_content=target_content,
            comparison_contents=comparison_content,
            db=db,
            with_reasoning=with_reasoning
        )
        
        # Process response with enhanced information
        response = {
            "affinity_scores": []
        }
        
        for insight in insights:
            score_data = {
                "content_id": insight.content_id,
                "score": insight.score,
                "confidence": insight.confidence,
                "explanation": insight.explanation,
                "target_id": target_id,
                "similarity_method": insight.metadata.get("similarity_method", "hybrid")
            }
            
            # Include reasoning chain if requested
            if with_reasoning and "reasoning_chain" in insight.metadata:
                score_data["reasoning_chain"] = insight.metadata["reasoning_chain"]
                
            response["affinity_scores"].append(score_data)
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating content affinity: {str(e)}"
        )

@router.post("/engagement/predict/{content_id}", response_model=Dict[str, Any])
async def predict_engagement(
    content_id: int,
    days_ahead: int = 7,
    with_reasoning: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Predict engagement for content using enhanced AI with fallback mechanisms
    
    - **content_id**: ID of the content to predict engagement for
    - **days_ahead**: Number of days to predict into the future (default: 7)
    - **with_reasoning**: Whether to include chain-of-thought reasoning in the response (default: False)
    """
    try:
        # Get content from database
        result = await db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        # Calculate predictions with enhanced resilient service
        insight = await predictive_service.predict_engagement_trends(
            content=content,
            db=db,
            days_ahead=days_ahead,
            with_reasoning=with_reasoning
        )
        
        # Prepare response
        response = {
            "content_id": insight.content_id,
            "score": insight.score,
            "confidence": insight.confidence,
            "explanation": insight.explanation,
            "trend_metrics": insight.metadata.get("forecast", {}),
            "recommendations": insight.metadata.get("recommendations", [])
        }
        
        # Include reasoning chain if requested
        if with_reasoning and "reasoning_chain" in insight.metadata:
            response["reasoning_chain"] = insight.metadata["reasoning_chain"]
            
        return response
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=404,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Error predicting engagement: {error_msg}"
            )
