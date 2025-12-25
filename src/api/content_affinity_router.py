from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.database.config import get_db
from src.auth.security import get_current_user
from src.models.user import User
from src.models.content import Content
from src.services.ai.content_affinity import ContentAffinityService
from typing import Dict, Any

router = APIRouter()

@router.get("/api/v1/content/{content_id}/affinity/{comparison_id}", response_model=Dict[str, Any])
async def get_content_affinity(
    content_id: int,
    comparison_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate affinity between two content items"""
    # Get target content
    result = await db.execute(select(Content).where(Content.id == content_id))
    target_content = result.scalar_one_or_none()
    
    if not target_content:
        raise HTTPException(status_code=404, detail="Target content not found")
        
    # Get comparison content
    result = await db.execute(select(Content).where(Content.id == comparison_id))
    comparison_content = result.scalar_one_or_none()
    
    if not comparison_content:
        raise HTTPException(status_code=404, detail="Comparison content not found")
        
    try:
        # Calculate affinity
        affinity_service = ContentAffinityService()
        insights = await affinity_service.calculate_content_affinity(
            target_content,
            [comparison_content],
            db
        )
        
        if not insights:
            raise HTTPException(status_code=404, detail="Could not calculate affinity")
            
        # Get the first (and only) insight
        insight = insights[0]
        
        return {
            "affinity_score": insight.score,
            "factors": {
                "similarity_method": insight.insight_metadata["similarity_method"],
                "confidence": insight.confidence
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
