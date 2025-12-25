from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from src.database.config import get_db
from src.auth.security import get_current_user
from src.models.user import User
from src.models.content import Content
from src.models.engagement import EngagementMetrics
from src.services.ai.content_recommendations import ContentRecommendationService

router = APIRouter(tags=["recommendations"])

@router.post("/generate", response_model=Dict[str, Any])
async def generate_recommendations(
    content_type: Optional[str] = Query(None),
    target_platform: Optional[str] = Query(None),
    target_audience: Optional[str] = Query(None),
    count: Optional[int] = Query(default=5),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate content recommendations based on historical performance."""
    # Validate count
    if not count or count < 1 or count > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Count must be between 1 and 20"
        )

    # Get user's historical content and performance data
    content_query = db.query(Content).filter(
        Content.user_id == current_user.id,
        Content.created_at >= datetime.now() - timedelta(days=90)  # Last 90 days
    )
    
    if content_type:
        content_query = content_query.filter(Content.content_type == content_type)
    
    historical_content = content_query.all()
    content_ids = [content.id for content in historical_content]
    
    # Get engagement metrics
    engagement_metrics = db.query(EngagementMetrics).filter(
        EngagementMetrics.content_id.in_(content_ids)
    ).all() if content_ids else []
    
    # Generate recommendations using the service
    recommendation_service = ContentRecommendationService()
    recommendations = await recommendation_service.generate_recommendations(
        historical_content=historical_content,
        engagement_metrics=engagement_metrics,
        target_platform=target_platform,
        target_audience=target_audience,
        count=count,
        db=db
    )
    
    # Format recommendations to match test expectations
    formatted_recommendations = []
    for rec in recommendations:
        # Get predicted performance metrics
        predicted_engagement = await recommendation_service.predict_engagement(
            recommendation=rec,
            platform=target_platform,
            db=db
        )
        
        # Format recommendation
        formatted_rec = {
            "content": {
                "content_type": rec.get("content_type", ""),
                "title": rec.get("topic", ""),
                "suggested_topics": rec.get("suggested_topics", []),
                "target_platform": target_platform,
                "target_audience": target_audience
            },
            "score": rec.get("scores", {}).get("total_score", 0.0),
            "predicted_performance": predicted_engagement,
            "suggested_timing": rec.get("suggested_timing", {}),
            "reasoning": rec.get("reasoning", "")
        }
        formatted_recommendations.append(formatted_rec)
    
    return {
        "recommendations": formatted_recommendations,
        "metadata": {
            "based_on_content": len(historical_content),
            "target_platform": target_platform,
            "target_audience": target_audience,
            "generated_at": datetime.now(),
            "model_version": recommendation_service.get_model_version()
        }
    }
