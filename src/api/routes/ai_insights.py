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

@router.post("/sentiment/analyze/{content_id}", response_model=Dict[str, Any])
async def analyze_sentiment(
    content_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze sentiment of content"""
    try:
        # Get content from database
        result = await db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        # Calculate sentiment
        insights = await sentiment_service.analyze_sentiment(content, db)
        
        return {
            "sentiment_scores": [
                {
                    "content_id": insight.content_id,
                    "score": insight.score,
                    "confidence": insight.confidence,
                    "metadata": insight.insight_metadata
                }
                for insight in insights
            ]
        }
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

@router.post("/affinity/calculate", response_model=Dict[str, Any])
async def calculate_affinity(
    target_id: int,
    comparison_ids: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate content affinity between target and comparison contents"""
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
        
        insights = await affinity_service.calculate_content_affinity(
            target_content,
            comparison_content,
            db
        )
        
        return {
            "affinity_scores": [
                {
                    "content_id": insight.content_id,
                    "score": insight.score,
                    "confidence": insight.confidence,
                    "metadata": insight.insight_metadata
                }
                for insight in insights
            ]
        }
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Predict engagement for content"""
    try:
        # Get content from database
        result = await db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        # Calculate predictions
        predictions = await predictive_service.predict_engagement(content, days_ahead, db)
        
        return {
            "predictions": [
                {
                    "content_id": prediction.content_id,
                    "score": prediction.score,
                    "confidence": prediction.confidence,
                    "metadata": prediction.insight_metadata
                }
                for prediction in predictions
            ]
        }
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
