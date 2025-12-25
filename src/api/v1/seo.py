from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models.seo import Subject, Subtopic, ContentAsset, OpportunityScore, MarketScope
from src.services.seo.semrush_service import SemrushService
from src.services.seo.serp_service import SerpService
from src.services.content.asset_tracker import ContentAssetTracker
from src.services.seo.scoring_service import ScoringService
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter()

class SubjectCreate(BaseModel):
    name: str
    market_scope: MarketScope
    language: str

class SubtopicResponse(BaseModel):
    id: int
    name: str
    search_volume: int
    competition: float

class ContentAssetCreate(BaseModel):
    subject_id: int
    url: str
    topic: str
    style: str
    format: str

@router.post("/subjects/", response_model=Dict[str, Any])
async def create_subject(
    subject_data: SubjectCreate,
    db: AsyncSession = Depends(get_db)
):
    subject = Subject(**subject_data.dict())
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    return {"id": subject.id, "name": subject.name, "market_scope": subject.market_scope, "language": subject.language}

@router.get("/subjects/{subject_id}/subtopics/", response_model=List[SubtopicResponse])
async def get_subtopics(
    subject_id: int,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Subtopic).where(Subtopic.subject_id == subject_id)
    result = await db.execute(stmt)
    subtopics = result.scalars().all()
    return subtopics

@router.post("/subjects/{subject_id}/analyze/")
async def analyze_subject(
    subject_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Get subject
    stmt = select(Subject).where(Subject.id == subject_id)
    result = await db.execute(stmt)
    subject = result.scalar_one_or_none()
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Initialize services
    semrush = SemrushService()
    serp = SerpService()
    scoring_service = ScoringService(semrush, serp)
    
    # Get keywords and competition data
    keywords = await semrush.get_keywords(subject.name)
    serp_data = await serp.analyze_serp(keywords)
    
    # Create subtopics from analysis
    for kw_data in keywords:
        subtopic = Subtopic(
            subject_id=subject.id,
            name=kw_data["keyword"],
            search_volume=kw_data["search_volume"],
            competition=kw_data["competition"]
        )
        db.add(subtopic)
    
    await db.commit()
    return {"message": "Subject analyzed successfully", "subject_id": subject_id}

@router.post("/content-assets/", response_model=Dict[str, Any])
async def create_content_asset(
    asset_data: ContentAssetCreate,
    db: AsyncSession = Depends(get_db)
):
    asset = ContentAsset(**asset_data.dict())
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return {
        "id": asset.id,
        "subject_id": asset.subject_id,
        "url": asset.url,
        "topic": asset.topic,
        "style": asset.style,
        "format": asset.format
    }

@router.get("/content-assets/{asset_id}/metrics/")
async def get_content_metrics(
    asset_id: int,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ContentAsset).where(ContentAsset.id == asset_id)
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Content asset not found")
    
    # Initialize services
    semrush = SemrushService()
    serp = SerpService()
    tracker = ContentAssetTracker(semrush, serp)
    
    # Get metrics
    metrics = await tracker.get_metrics(asset.url)
    
    return metrics

@router.get("/subjects/{subject_id}/opportunity-score/")
async def calculate_opportunity_score(
    subject_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Get subject and its subtopics
    stmt = select(Subject).where(Subject.id == subject_id)
    result = await db.execute(stmt)
    subject = result.scalar_one_or_none()
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
        
    stmt = select(Subtopic).where(Subtopic.subject_id == subject_id)
    result = await db.execute(stmt)
    subtopics = result.scalars().all()
    
    if not subtopics:
        raise HTTPException(status_code=404, detail="No subtopics found for subject")
    
    # Calculate opportunity score
    total_search_volume = sum(st.search_volume for st in subtopics)
    avg_competition = sum(st.competition for st in subtopics) / len(subtopics)
    
    opportunity_index = total_search_volume * (1 - avg_competition)
    niche_potential = 1 / (avg_competition + 0.1)  # Add small constant to avoid division by zero
    
    # Create or update opportunity score
    stmt = select(OpportunityScore).where(OpportunityScore.subject_id == subject_id)
    result = await db.execute(stmt)
    score = result.scalar_one_or_none()
    
    if score:
        score.opportunity_index = opportunity_index
        score.niche_potential_index = niche_potential
    else:
        score = OpportunityScore(
            subject_id=subject_id,
            opportunity_index=opportunity_index,
            niche_potential_index=niche_potential
        )
        db.add(score)
    
    await db.commit()
    return {
        "opportunity_index": opportunity_index,
        "niche_potential_index": niche_potential,
        "subject_id": subject_id
    }

@router.get("/subjects/{subject_id}/competitors/")
async def get_competitor_content(
    subject_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Get subject
    stmt = select(Subject).where(Subject.id == subject_id)
    result = await db.execute(stmt)
    subject = result.scalar_one_or_none()
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Initialize services
    semrush = SemrushService()
    serp = SerpService()
    tracker = ContentAssetTracker(semrush, serp)
    
    # Get competitor content
    competitors = await tracker.get_competitor_content(subject.name)
    
    return competitors

@router.get("/content/{content_id}/likeability", response_model=Dict[str, float])
async def get_likeability_index(
    content_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get the Likeability Index for a piece of content"""
    stmt = select(ContentAsset).where(ContentAsset.id == content_id)
    result = await db.execute(stmt)
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    semrush = SemrushService()
    serp = SerpService()
    scoring_service = ScoringService(semrush, serp)
    score = await scoring_service.calculate_likeability_index(content)
    return {"likeability_index": score}

@router.get("/subjects/{subject_id}/opportunity/{subtopic_id}", response_model=Dict[str, float])
async def get_opportunity_index(
    subject_id: int,
    subtopic_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get the Opportunity Performance Index (OPI) for a subtopic"""
    stmt = select(Subject).where(Subject.id == subject_id)
    result = await db.execute(stmt)
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    stmt = select(Subtopic).where(Subtopic.id == subtopic_id)
    result = await db.execute(stmt)
    subtopic = result.scalar_one_or_none()
    if not subtopic:
        raise HTTPException(status_code=404, detail="Subtopic not found")
    
    semrush = SemrushService()
    serp = SerpService()
    scoring_service = ScoringService(semrush, serp)
    score = await scoring_service.calculate_opportunity_index(subject, subtopic)
    return {"opportunity_index": score}

@router.get("/subjects/{subject_id}/niche-potential", response_model=Dict[str, float])
async def get_niche_potential(
    subject_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get the Niche Potential Index (NPI) for a subject"""
    stmt = select(Subject).where(Subject.id == subject_id)
    result = await db.execute(stmt)
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    semrush = SemrushService()
    serp = SerpService()
    scoring_service = ScoringService(semrush, serp)
    score = await scoring_service.calculate_niche_potential(subject)
    return {"niche_potential_index": score}

@router.get("/subjects/{subject_id}/market-segments", response_model=Dict[str, List[Dict[str, Any]]])
async def get_market_segments(
    subject_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get market segmentation analysis for a subject"""
    stmt = select(Subject).where(Subject.id == subject_id)
    result = await db.execute(stmt)
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    semrush = SemrushService()
    serp = SerpService()
    scoring_service = ScoringService(semrush, serp)
    segments = await scoring_service.segment_market(subject)
    return segments
