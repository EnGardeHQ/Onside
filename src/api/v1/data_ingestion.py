from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
from src.database.config import get_db
from src.auth.security import get_current_user
from src.models.content import Content
from src.models.engagement import EngagementMetrics
from src.models.user import User
from src.services.data_ingestion import DataIngestionService

router = APIRouter(tags=["data-ingestion"])

@router.post("/upload", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
async def upload_content(
    file: UploadFile = File(...),
    metadata: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        metadata_dict = json.loads(metadata)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid metadata format")
    
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")
    
    content_bytes = await file.read()
    if len(content_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file provided")
        
    ingestion_service = DataIngestionService()
    content = await ingestion_service.upload_content(
        content_bytes,
        metadata_dict,
        current_user.id,
        db
    )
    
    return {
        "id": content.id,
        "title": metadata_dict.get("title"),
        "description": metadata_dict.get("description"),
        "tags": metadata_dict.get("tags", []),
        "type": content.content_type
    }

@router.get("/social/{content_id}", response_model=Dict[str, Any])
async def fetch_social_metrics(
    content_id: int,
    platform: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if platform not in ["twitter", "facebook", "linkedin"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid platform")

    # Get content
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    # Get metrics
    metrics = db.query(EngagementMetrics).filter(
        EngagementMetrics.content_id == content_id,
        EngagementMetrics.source == platform
    ).all()

    return {
        "content_id": content_id,
        "platform": platform,
        "metrics": [
            {
                "id": metric.id,
                "metric_type": metric.metric_type,
                "value": metric.value,
                "source": metric.source,
                "metadata": metric.metric_metadata
            }
            for metric in metrics
        ]
    }
