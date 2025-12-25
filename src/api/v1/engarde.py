"""En Garde integration API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import csv
import io

import src.database as database_module
from src.auth.security import get_current_user
from src.models.user import User
from src.models.brand_analysis import (
    BrandAnalysisJob,
    DiscoveredKeyword,
    IdentifiedCompetitor,
    ContentOpportunity,
    AnalysisStatus
)
from src.agents.seo_content_walker import SEOContentWalkerAgent, BrandAnalysisQuestionnaire
from src.services.engarde_integration.import_service import (
    ImportService,
    ImportStrategy,
    ImportStatistics
)
from src.services.engarde_integration.data_transformer import EnGardeDataTransformer
from src.services.engarde_integration.api_client import EnGardeAPIClient, RetryConfig
from src.config import settings

# Use the sync get_db from the parent database module
get_db = database_module.get_db

router = APIRouter(prefix="/engarde", tags=["engarde"])


# Pydantic schemas for request/response models

class BrandAnalysisQuestionnaireSchema(BaseModel):
    """Schema for brand analysis questionnaire.

    This schema defines the required input data for initiating a brand
    digital footprint analysis. All fields help the AI agent understand
    your brand and discover relevant keywords, competitors, and content gaps.
    """
    brand_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Official brand/company name",
        example="Acme Corp"
    )
    primary_website: str = Field(
        ...,
        pattern=r'^https?://',
        description="Primary website URL (must include http:// or https://)",
        example="https://www.acmecorp.com"
    )
    industry: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Primary industry or vertical",
        example="SaaS Marketing Tools"
    )
    target_markets: List[str] = Field(
        default_factory=list,
        description="Geographic or demographic markets you target",
        example=["United States", "Canada", "SMB businesses"]
    )
    products_services: List[str] = Field(
        default_factory=list,
        description="Key products or services offered",
        example=["Email Marketing Platform", "Social Media Scheduler", "Analytics Dashboard"]
    )
    known_competitors: List[str] = Field(
        default_factory=list,
        description="Known competitor domains (optional)",
        example=["mailchimp.com", "hubspot.com"]
    )
    target_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords you want to rank for (optional)",
        example=["email marketing", "marketing automation", "crm software"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "brand_name": "Acme Corp",
                "primary_website": "https://www.acmecorp.com",
                "industry": "SaaS Marketing Tools",
                "target_markets": ["United States", "Canada"],
                "products_services": ["Email Marketing Platform", "Social Media Scheduler"],
                "known_competitors": ["mailchimp.com", "hubspot.com"],
                "target_keywords": ["email marketing", "marketing automation"]
            }
        }


class BrandAnalysisInitiateResponse(BaseModel):
    """Response for initiating brand analysis.

    Returns a job ID that can be used to track the analysis progress
    and retrieve results when complete.
    """
    job_id: str = Field(
        ...,
        description="Unique UUID for this analysis job",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    status: str = Field(
        ...,
        description="Current status of the analysis job",
        example="initiated"
    )
    message: str = Field(
        ...,
        description="Human-readable status message",
        example="Brand analysis initiated successfully"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "initiated",
                "message": "Brand analysis initiated successfully"
            }
        }


class BrandAnalysisStatusResponse(BaseModel):
    """Response for brand analysis status.

    Provides detailed information about the progress and current state
    of a brand analysis job. Poll this endpoint to track job progress.
    """
    job_id: str = Field(
        ...,
        description="UUID of the analysis job",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    status: str = Field(
        ...,
        description="Current job status (initiated, crawling, analyzing, processing, completed, failed)",
        example="analyzing"
    )
    progress: int = Field(
        ...,
        ge=0,
        le=100,
        description="Completion percentage (0-100)",
        example=65
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when job was created",
        example="2025-12-24T10:30:00Z"
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when job was last updated",
        example="2025-12-24T10:35:22Z"
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="Timestamp when job completed (null if still running)",
        example="2025-12-24T10:40:15Z"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error details if status is 'failed'",
        example=None
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "analyzing",
                "progress": 65,
                "created_at": "2025-12-24T10:30:00Z",
                "updated_at": "2025-12-24T10:35:22Z",
                "completed_at": None,
                "error_message": None
            }
        }


class DiscoveredKeywordSchema(BaseModel):
    """Schema for discovered keyword.

    Represents a keyword discovered during the brand analysis process,
    including metrics and metadata about its potential value.
    """
    id: int = Field(
        ...,
        description="Database ID of this keyword",
        example=123
    )
    keyword: str = Field(
        ...,
        description="The keyword phrase",
        example="email marketing automation"
    )
    source: str = Field(
        ...,
        description="How this keyword was discovered (website_content, serp_analysis, nlp_extraction)",
        example="nlp_extraction"
    )
    search_volume: Optional[int] = Field(
        None,
        description="Estimated monthly search volume",
        example=12000
    )
    difficulty: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="SEO difficulty score (0-100, higher = more competitive)",
        example=65.5
    )
    relevance_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Relevance to your brand (0-1, higher = more relevant)",
        example=0.87
    )
    current_ranking: Optional[int] = Field(
        None,
        description="Your current SERP ranking for this keyword (if ranking)",
        example=15
    )
    confirmed: bool = Field(
        ...,
        description="Whether this keyword has been confirmed/imported",
        example=False
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 123,
                "keyword": "email marketing automation",
                "source": "nlp_extraction",
                "search_volume": 12000,
                "difficulty": 65.5,
                "relevance_score": 0.87,
                "current_ranking": 15,
                "confirmed": False
            }
        }


class IdentifiedCompetitorSchema(BaseModel):
    """Schema for identified competitor.

    Represents a competitor identified through SERP analysis,
    including their market position and overlap with your brand.
    """
    id: int = Field(
        ...,
        description="Database ID of this competitor",
        example=456
    )
    domain: str = Field(
        ...,
        description="Competitor's primary domain",
        example="competitor-example.com"
    )
    name: Optional[str] = Field(
        None,
        description="Extracted brand name",
        example="Competitor Example"
    )
    relevance_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Relevance to your market (0-1, higher = more relevant)",
        example=0.78
    )
    category: str = Field(
        ...,
        description="Competitor category (primary, secondary, emerging, niche)",
        example="secondary"
    )
    overlap_percentage: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Percentage of keyword overlap with your brand",
        example=42.5
    )
    confirmed: bool = Field(
        ...,
        description="Whether this competitor has been confirmed/imported",
        example=False
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 456,
                "domain": "competitor-example.com",
                "name": "Competitor Example",
                "relevance_score": 0.78,
                "category": "secondary",
                "overlap_percentage": 42.5,
                "confirmed": False
            }
        }


class ContentOpportunitySchema(BaseModel):
    """Schema for content opportunity.

    Represents a content gap or opportunity identified during analysis,
    with recommendations for creating new content to capture traffic.
    """
    id: int = Field(
        ...,
        description="Database ID of this opportunity",
        example=789
    )
    topic: str = Field(
        ...,
        description="Content topic or theme",
        example="Content about email segmentation strategies"
    )
    gap_type: str = Field(
        ...,
        description="Type of content gap (missing_content, weak_content, competitor_strength)",
        example="missing_content"
    )
    traffic_potential: Optional[int] = Field(
        None,
        description="Estimated monthly traffic potential",
        example=5000
    )
    difficulty: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Difficulty to rank for this content (0-100)",
        example=45.0
    )
    priority: str = Field(
        ...,
        description="Priority level (high, medium, low)",
        example="high"
    )
    recommended_format: Optional[str] = Field(
        None,
        description="Recommended content format (blog, guide, video, infographic)",
        example="guide"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 789,
                "topic": "Content about email segmentation strategies",
                "gap_type": "missing_content",
                "traffic_potential": 5000,
                "difficulty": 45.0,
                "priority": "high",
                "recommended_format": "guide"
            }
        }


class BrandAnalysisResultsResponse(BaseModel):
    """Response for brand analysis results.

    Contains all discovered keywords, competitors, and content opportunities
    from a completed brand analysis job. Use this data to review findings
    before confirming imports.
    """
    job_id: str = Field(
        ...,
        description="UUID of the analysis job",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    status: str = Field(
        ...,
        description="Job status (should be 'completed')",
        example="completed"
    )
    keywords: List[DiscoveredKeywordSchema] = Field(
        ...,
        description="List of discovered keywords with metrics",
        example=[]
    )
    competitors: List[IdentifiedCompetitorSchema] = Field(
        ...,
        description="List of identified competitors",
        example=[]
    )
    opportunities: List[ContentOpportunitySchema] = Field(
        ...,
        description="List of content opportunities",
        example=[]
    )
    results: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional analysis metadata and summary",
        example={
            "keywords_found": 47,
            "competitors_identified": 12,
            "content_opportunities": 8,
            "analysis_timestamp": "2025-12-24T10:40:15Z"
        }
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "keywords": [
                    {
                        "id": 123,
                        "keyword": "email marketing automation",
                        "source": "nlp_extraction",
                        "search_volume": 12000,
                        "difficulty": 65.5,
                        "relevance_score": 0.87,
                        "current_ranking": None,
                        "confirmed": False
                    }
                ],
                "competitors": [
                    {
                        "id": 456,
                        "domain": "mailchimp.com",
                        "name": "Mailchimp",
                        "relevance_score": 0.92,
                        "category": "primary",
                        "overlap_percentage": 78.5,
                        "confirmed": False
                    }
                ],
                "opportunities": [
                    {
                        "id": 789,
                        "topic": "Content about email segmentation strategies",
                        "gap_type": "missing_content",
                        "traffic_potential": 5000,
                        "difficulty": 45.0,
                        "priority": "high",
                        "recommended_format": "guide"
                    }
                ],
                "results": {
                    "keywords_found": 47,
                    "competitors_identified": 12,
                    "content_opportunities": 8,
                    "analysis_timestamp": "2025-12-24T10:40:15Z"
                }
            }
        }


class BrandAnalysisConfirmRequest(BaseModel):
    """Request to confirm and import analysis results.

    After reviewing the analysis results, use this to select which
    keywords and competitors to import into the main En Garde database.
    """
    selected_keywords: List[int] = Field(
        default_factory=list,
        description="Database IDs of keywords to import",
        example=[123, 124, 125]
    )
    selected_competitors: List[int] = Field(
        default_factory=list,
        description="Database IDs of competitors to import",
        example=[456, 457]
    )
    selected_opportunities: Optional[List[int]] = Field(
        default_factory=list,
        description="Database IDs of content opportunities to import (optional)",
        example=[789, 790]
    )
    tenant_uuid: Optional[str] = Field(
        None,
        description="En Garde tenant UUID (required for multi-tenant environments)",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    import_strategy: str = Field(
        default="skip",
        description="Strategy for handling duplicates: skip, merge, replace, create_new",
        example="skip"
    )
    export_format: Optional[str] = Field(
        None,
        description="Optional export format: csv, campaign_json. If provided, returns export instead of importing",
        example=None
    )
    modifications: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional modifications to apply before import",
        example={}
    )

    class Config:
        json_schema_extra = {
            "example": {
                "selected_keywords": [123, 124, 125],
                "selected_competitors": [456, 457],
                "selected_opportunities": [789],
                "tenant_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "import_strategy": "skip",
                "export_format": None,
                "modifications": {}
            }
        }


class BrandAnalysisConfirmResponse(BaseModel):
    """Response for confirming analysis.

    Confirms successful import of selected items into the main database
    with detailed statistics about the import operation.
    """
    imported: bool = Field(
        ...,
        description="Whether the import was successful",
        example=True
    )
    batch_id: str = Field(
        ...,
        description="Unique ID for this import batch (for audit trail)",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    keywords_count: int = Field(
        ...,
        description="Number of keywords imported",
        example=3
    )
    competitors_count: int = Field(
        ...,
        description="Number of competitors imported",
        example=2
    )
    opportunities_count: int = Field(
        default=0,
        description="Number of content opportunities imported",
        example=1
    )
    duplicates_detected: int = Field(
        default=0,
        description="Number of duplicate items detected",
        example=1
    )
    duplicates_skipped: int = Field(
        default=0,
        description="Number of duplicates skipped based on import strategy",
        example=1
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of any errors encountered during import",
        example=[]
    )
    duration_seconds: float = Field(
        ...,
        description="Time taken to complete the import",
        example=2.5
    )
    message: str = Field(
        ...,
        description="Human-readable confirmation message",
        example="Successfully imported 3 keywords and 2 competitors (1 duplicate skipped)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "imported": True,
                "batch_id": "550e8400-e29b-41d4-a716-446655440000",
                "keywords_count": 3,
                "competitors_count": 2,
                "opportunities_count": 1,
                "duplicates_detected": 1,
                "duplicates_skipped": 1,
                "errors": [],
                "duration_seconds": 2.5,
                "message": "Successfully imported 3 keywords and 2 competitors (1 duplicate skipped)"
            }
        }


# Background task processing

async def process_brand_analysis(
    job_id: str,
    questionnaire_data: Dict[str, Any],
    db: Session
):
    """Background task to process brand analysis.

    Args:
        job_id: UUID of the analysis job
        questionnaire_data: Questionnaire data dict
        db: Database session
    """
    try:
        # Create questionnaire object
        questionnaire = BrandAnalysisQuestionnaire.from_dict(questionnaire_data)

        # Initialize agent
        agent = SEOContentWalkerAgent(db)

        # Run analysis
        await agent.analyze_brand(job_id, questionnaire)

    except Exception as e:
        # Update job with error
        job = db.query(BrandAnalysisJob).filter(BrandAnalysisJob.id == job_id).first()
        if job:
            job.status = AnalysisStatus.FAILED
            job.error_message = str(e)
            job.updated_at = datetime.utcnow()
            db.commit()


# API Endpoints

@router.post(
    "/brand-analysis/initiate",
    response_model=BrandAnalysisInitiateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate Brand Analysis",
    description="""
    **Initiate automated brand digital footprint analysis**

    This endpoint starts an AI-powered analysis of your brand's digital presence,
    discovering keywords, competitors, and content opportunities. The analysis runs
    asynchronously in the background.

    **Process Overview:**
    1. Crawls your website to understand your content and messaging
    2. Extracts relevant keywords using NLP and TF-IDF analysis
    3. Analyzes SERP (Search Engine Results Pages) to identify competitors
    4. Generates content opportunity recommendations

    **Expected Duration:** 5-15 minutes depending on website size

    **Returns:** A job ID to track progress via the status endpoint
    """,
    responses={
        201: {
            "description": "Analysis job created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "initiated",
                        "message": "Brand analysis initiated successfully"
                    }
                }
            }
        },
        401: {"description": "Unauthorized - Invalid or missing authentication token"},
        422: {"description": "Validation error - Invalid questionnaire data"}
    }
)
def initiate_brand_analysis(
    questionnaire: BrandAnalysisQuestionnaireSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initiate automated brand digital footprint analysis.

    This endpoint starts the analysis process in the background and returns
    a job ID that can be used to track progress.

    Args:
        questionnaire: Brand analysis questionnaire data
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Authenticated user

    Returns:
        BrandAnalysisInitiateResponse with job ID and status
    """
    # Create analysis job
    job = BrandAnalysisJob(
        id=uuid.uuid4(),
        user_id=current_user.id,
        questionnaire=questionnaire.dict(),
        status=AnalysisStatus.INITIATED,
        progress=0
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Start background processing
    background_tasks.add_task(
        process_brand_analysis,
        str(job.id),
        questionnaire.dict(),
        db
    )

    return BrandAnalysisInitiateResponse(
        job_id=str(job.id),
        status=AnalysisStatus.INITIATED.value,
        message="Brand analysis initiated successfully"
    )


@router.get(
    "/brand-analysis/{job_id}/status",
    response_model=BrandAnalysisStatusResponse,
    summary="Get Analysis Status",
    description="""
    **Poll for brand analysis job status and progress**

    Use this endpoint to check the current status and progress of an analysis job.
    Recommended polling interval: every 5-10 seconds until status is 'completed' or 'failed'.

    **Status Values:**
    - `initiated`: Job created, waiting to start
    - `crawling`: Actively crawling your website
    - `analyzing`: Extracting keywords and analyzing SERP data
    - `processing`: Identifying competitors and generating recommendations
    - `completed`: Analysis finished successfully, results available
    - `failed`: Analysis encountered an error, check error_message

    **Progress:** Integer 0-100 indicating completion percentage
    """,
    responses={
        200: {
            "description": "Status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "analyzing",
                        "progress": 65,
                        "created_at": "2025-12-24T10:30:00Z",
                        "updated_at": "2025-12-24T10:35:22Z",
                        "completed_at": None,
                        "error_message": None
                    }
                }
            }
        },
        400: {"description": "Invalid job ID format"},
        401: {"description": "Unauthorized - Invalid or missing authentication token"},
        404: {"description": "Analysis job not found"}
    }
)
def get_brand_analysis_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get status of brand analysis job.

    Args:
        job_id: UUID of the analysis job
        db: Database session
        current_user: Authenticated user

    Returns:
        BrandAnalysisStatusResponse with job status and progress
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format"
        )

    job = db.query(BrandAnalysisJob).filter(
        BrandAnalysisJob.id == job_uuid,
        BrandAnalysisJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis job not found"
        )

    return BrandAnalysisStatusResponse(
        job_id=str(job.id),
        status=job.status.value,
        progress=job.progress,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        error_message=job.error_message
    )


@router.get(
    "/brand-analysis/{job_id}/results",
    response_model=BrandAnalysisResultsResponse,
    summary="Get Analysis Results",
    description="""
    **Retrieve complete results from a finished brand analysis**

    Only call this endpoint after the job status is 'completed'. Returns all
    discovered keywords, identified competitors, and content opportunities.

    **What You Get:**
    - **Keywords:** Discovered keywords with search volume, difficulty, and relevance scores
    - **Competitors:** Identified competitors with overlap percentages and categorization
    - **Opportunities:** Content gap recommendations with traffic potential and priority

    **Next Steps:**
    1. Review the results in your frontend UI
    2. User selects which keywords/competitors to import
    3. Call the `/confirm` endpoint to import selected items
    """,
    responses={
        200: {
            "description": "Results retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "completed",
                        "keywords": [
                            {
                                "id": 123,
                                "keyword": "email marketing automation",
                                "source": "nlp_extraction",
                                "search_volume": 12000,
                                "difficulty": 65.5,
                                "relevance_score": 0.87,
                                "current_ranking": None,
                                "confirmed": False
                            }
                        ],
                        "competitors": [
                            {
                                "id": 456,
                                "domain": "mailchimp.com",
                                "name": "Mailchimp",
                                "relevance_score": 0.92,
                                "category": "primary",
                                "overlap_percentage": 78.5,
                                "confirmed": False
                            }
                        ],
                        "opportunities": [
                            {
                                "id": 789,
                                "topic": "Content about email segmentation strategies",
                                "gap_type": "missing_content",
                                "traffic_potential": 5000,
                                "difficulty": 45.0,
                                "priority": "high",
                                "recommended_format": "guide"
                            }
                        ],
                        "results": {
                            "keywords_found": 47,
                            "competitors_identified": 12,
                            "content_opportunities": 8
                        }
                    }
                }
            }
        },
        400: {"description": "Analysis not complete or invalid job ID"},
        401: {"description": "Unauthorized - Invalid or missing authentication token"},
        404: {"description": "Analysis job not found"}
    }
)
def get_brand_analysis_results(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get results of completed brand analysis.

    Args:
        job_id: UUID of the analysis job
        db: Database session
        current_user: Authenticated user

    Returns:
        BrandAnalysisResultsResponse with keywords, competitors, and opportunities
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format"
        )

    job = db.query(BrandAnalysisJob).filter(
        BrandAnalysisJob.id == job_uuid,
        BrandAnalysisJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis job not found"
        )

    if job.status != AnalysisStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis is not complete. Current status: {job.status.value}"
        )

    # Get keywords
    keywords = db.query(DiscoveredKeyword).filter(
        DiscoveredKeyword.job_id == job_uuid
    ).all()

    # Get competitors
    competitors = db.query(IdentifiedCompetitor).filter(
        IdentifiedCompetitor.job_id == job_uuid
    ).all()

    # Get opportunities
    opportunities = db.query(ContentOpportunity).filter(
        ContentOpportunity.job_id == job_uuid
    ).all()

    return BrandAnalysisResultsResponse(
        job_id=str(job.id),
        status=job.status.value,
        keywords=[DiscoveredKeywordSchema.from_orm(kw) for kw in keywords],
        competitors=[IdentifiedCompetitorSchema.from_orm(comp) for comp in competitors],
        opportunities=[ContentOpportunitySchema.from_orm(opp) for opp in opportunities],
        results=job.results
    )


@router.post(
    "/brand-analysis/{job_id}/confirm",
    response_model=BrandAnalysisConfirmResponse,
    summary="Confirm and Import Results",
    description="""
    **Import selected keywords and competitors into En Garde production database**

    After reviewing the analysis results, use this endpoint to confirm and import
    the selected items into the En Garde production database. This endpoint:

    1. Validates the selections against the job
    2. Transforms Onside data to En Garde format
    3. Detects and handles duplicates based on import strategy
    4. Imports data into En Garde production database (or via API)
    5. Marks items as confirmed in Onside staging tables
    6. Returns detailed import statistics

    **Import Strategies:**
    - `skip`: Skip duplicate items (safest, default)
    - `merge`: Merge duplicate data with existing records
    - `replace`: Replace existing records with new data
    - `create_new`: Always create new records (may create duplicates)

    **Multi-Tenant Support:**
    - Provide `tenant_uuid` to associate imported data with a specific En Garde tenant
    - Required for multi-tenant En Garde deployments

    **Process:**
    1. User reviews results in frontend
    2. User selects which keywords/competitors to import
    3. Frontend calls this endpoint with selections and import strategy
    4. Backend performs intelligent import with duplicate detection
    5. Returns detailed statistics including duplicates found/skipped

    **Note:** You can call this endpoint multiple times with different selections.
    Each call creates a new import batch with its own audit trail.
    """,
    responses={
        200: {
            "description": "Items confirmed and imported successfully",
            "content": {
                "application/json": {
                    "example": {
                        "imported": True,
                        "batch_id": "550e8400-e29b-41d4-a716-446655440000",
                        "keywords_count": 3,
                        "competitors_count": 2,
                        "opportunities_count": 1,
                        "duplicates_detected": 1,
                        "duplicates_skipped": 1,
                        "errors": [],
                        "duration_seconds": 2.5,
                        "message": "Successfully imported 3 keywords and 2 competitors (1 duplicate skipped)"
                    }
                }
            }
        },
        400: {"description": "Invalid job ID format or validation errors"},
        401: {"description": "Unauthorized - Invalid or missing authentication token"},
        404: {"description": "Analysis job not found"},
        500: {"description": "Import failed due to server error"}
    }
)
def confirm_brand_analysis(
    job_id: str,
    confirmation: BrandAnalysisConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Confirm and import selected analysis results into En Garde production database.

    This endpoint performs the complete import workflow:
    - Data transformation from Onside to En Garde format
    - Duplicate detection and intelligent handling
    - Import into En Garde production database
    - Audit trail tracking with import batches

    Args:
        job_id: UUID of the analysis job
        confirmation: Selected items to import with import strategy
        db: Database session (Onside)
        current_user: Authenticated user

    Returns:
        BrandAnalysisConfirmResponse with detailed import statistics

    Raises:
        HTTPException: If job not found, validation fails, or import error occurs
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format"
        )

    # Verify job exists and belongs to user
    job = db.query(BrandAnalysisJob).filter(
        BrandAnalysisJob.id == job_uuid,
        BrandAnalysisJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis job not found"
        )

    # Validate import strategy
    try:
        strategy = ImportStrategy(confirmation.import_strategy)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid import strategy: {confirmation.import_strategy}. "
                   f"Must be one of: {', '.join([s.value for s in ImportStrategy])}"
        )

    # Prepare user selections
    user_selections = {
        "selected_keywords": confirmation.selected_keywords,
        "selected_competitors": confirmation.selected_competitors,
        "selected_opportunities": confirmation.selected_opportunities or []
    }

    # Validate that at least some items are selected
    total_selected = (
        len(user_selections["selected_keywords"]) +
        len(user_selections["selected_competitors"]) +
        len(user_selections["selected_opportunities"])
    )

    if total_selected == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No items selected for import. Please select at least one keyword or competitor."
        )

    try:
        # Initialize EnGarde API client
        # This client handles all communication with the production EnGarde backend
        engarde_client = EnGardeAPIClient(
            api_url=settings.ENGARDE_API_URL,
            api_key=settings.ENGARDE_API_KEY,
            tenant_uuid=settings.ENGARDE_TENANT_UUID or confirmation.tenant_uuid,
            timeout=settings.ENGARDE_API_TIMEOUT,
            retry_config=RetryConfig(
                max_attempts=settings.ENGARDE_API_MAX_RETRIES,
                initial_delay=float(settings.ENGARDE_API_RETRY_DELAY)
            )
        )

        # Initialize import service with API client
        import_service = ImportService(
            onside_db=db,
            engarde_db=None,  # Not available in this repo
            use_api_import=True,  # Use API mode
            engarde_api_client=engarde_client
        )

        # Execute import with comprehensive statistics
        import_stats = import_service.import_confirmed_results(
            job_id=job_id,
            user_selections=user_selections,
            tenant_uuid=confirmation.tenant_uuid,
            import_strategy=strategy,
            validate_before_import=True
        )

        # Build success message
        message_parts = []
        if import_stats.successfully_imported > 0:
            message_parts.append(
                f"Successfully imported {import_stats.items_by_type['keywords']} keywords, "
                f"{import_stats.items_by_type['competitors']} competitors"
            )
            if import_stats.items_by_type.get('opportunities', 0) > 0:
                message_parts.append(f"{import_stats.items_by_type['opportunities']} content opportunities")

        if import_stats.duplicates_skipped > 0:
            message_parts.append(f"({import_stats.duplicates_skipped} duplicates skipped)")

        if import_stats.errors > 0:
            message_parts.append(f"({import_stats.errors} errors occurred)")

        message = " ".join(message_parts) if message_parts else "No items imported"

        # Map error_details to simple error messages
        error_messages = [
            f"{err.get('type', 'unknown')}: {err.get('error', 'Unknown error')}"
            for err in import_stats.error_details
        ]

        return BrandAnalysisConfirmResponse(
            imported=import_stats.successfully_imported > 0,
            batch_id=import_stats.batch_id,
            keywords_count=import_stats.items_by_type.get("keywords", 0),
            competitors_count=import_stats.items_by_type.get("competitors", 0),
            opportunities_count=import_stats.items_by_type.get("opportunities", 0),
            duplicates_detected=import_stats.duplicates_detected,
            duplicates_skipped=import_stats.duplicates_skipped,
            errors=error_messages,
            duration_seconds=import_stats.duration_seconds,
            message=message
        )

    except ValueError as e:
        # Validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        # Unexpected errors
        logger.error(f"Import failed for job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


@router.get(
    "/brand-analysis/{job_id}/export/csv",
    summary="Export Results to CSV",
    description="""
    **Export Onside analysis results to CSV format compatible with En Garde CSV import**

    This endpoint exports all confirmed (or selected) keywords, competitors, and content
    opportunities into a CSV format that can be imported directly into En Garde's CSV
    import system.

    **CSV Structure:**
    - Headers compatible with En Garde's CSV import expectations
    - One row per keyword/competitor/opportunity
    - Includes all relevant metrics and metadata

    **Use Cases:**
    1. Manual review before importing into campaign
    2. Archival/backup of analysis results
    3. Integration with external tools via CSV
    4. Batch import into En Garde via CSV upload UI

    **Next Steps:**
    - Download the CSV file
    - Upload to En Garde via `/campaign-spaces/import` or CSV import page
    """,
    responses={
        200: {
            "description": "CSV file download",
            "content": {
                "text/csv": {
                    "example": "keyword,search_volume,difficulty,priority,source\\nemail marketing,12000,65.5,high,onside_analysis\\n"
                }
            }
        },
        400: {"description": "Invalid job ID or job not complete"},
        401: {"description": "Unauthorized"},
        404: {"description": "Analysis job not found"}
    }
)
def export_results_to_csv(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export Onside analysis results to CSV format compatible with En Garde CSV import.

    Returns a downloadable CSV file with all keywords, competitors, and content opportunities.
    The CSV format matches En Garde's expected schema for seamless import.
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format"
        )

    # Verify job exists and belongs to user
    job = db.query(BrandAnalysisJob).filter(
        BrandAnalysisJob.id == job_uuid,
        BrandAnalysisJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis job not found"
        )

    if job.status != AnalysisStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis is not complete. Current status: {job.status.value}"
        )

    # Get all keywords, competitors, and opportunities
    keywords = db.query(DiscoveredKeyword).filter(
        DiscoveredKeyword.job_id == job_uuid
    ).all()

    competitors = db.query(IdentifiedCompetitor).filter(
        IdentifiedCompetitor.job_id == job_uuid
    ).all()

    opportunities = db.query(ContentOpportunity).filter(
        ContentOpportunity.job_id == job_uuid
    ).all()

    # Generate CSV
    csv_output = io.StringIO()
    csv_writer = csv.writer(csv_output)

    # Write headers
    csv_writer.writerow([
        "type",
        "keyword",
        "domain",
        "topic",
        "source",
        "search_volume",
        "difficulty",
        "relevance_score",
        "priority",
        "current_ranking",
        "category",
        "traffic_potential",
        "gap_type",
        "recommended_format",
        "overlap_percentage",
        "metadata"
    ])

    # Write keywords
    for kw in keywords:
        csv_writer.writerow([
            "keyword",
            kw.keyword,
            "",  # domain
            "",  # topic
            kw.source,
            kw.search_volume or "",
            kw.difficulty or "",
            kw.relevance_score,
            "high" if kw.relevance_score > 0.7 else "medium" if kw.relevance_score > 0.4 else "low",
            kw.current_ranking or "",
            kw.source,
            "",  # traffic_potential
            "",  # gap_type
            "",  # recommended_format
            "",  # overlap_percentage
            f"onside_id={kw.id},confirmed={kw.confirmed}"
        ])

    # Write competitors
    for comp in competitors:
        csv_writer.writerow([
            "competitor",
            "",  # keyword
            comp.domain,
            "",  # topic
            "competitor_analysis",
            "",  # search_volume
            "",  # difficulty
            comp.relevance_score,
            "high" if comp.relevance_score > 0.7 else "medium" if comp.relevance_score > 0.4 else "low",
            "",  # current_ranking
            comp.category,
            "",  # traffic_potential
            "",  # gap_type
            "",  # recommended_format
            comp.overlap_percentage or "",
            f"onside_id={comp.id},name={comp.name or ''},confirmed={comp.confirmed}"
        ])

    # Write opportunities
    for opp in opportunities:
        csv_writer.writerow([
            "content_opportunity",
            "",  # keyword
            "",  # domain
            opp.topic,
            "content_gap_analysis",
            "",  # search_volume
            opp.difficulty or "",
            "",  # relevance_score
            opp.priority,
            "",  # current_ranking
            "",  # category
            opp.traffic_potential or "",
            opp.gap_type,
            opp.recommended_format or "",
            "",  # overlap_percentage
            f"onside_id={opp.id}"
        ])

    # Get brand name from questionnaire
    brand_name = job.questionnaire.get("brand_name", "brand_analysis")
    safe_filename = brand_name.replace(" ", "_").lower()

    # Return CSV as streaming response
    csv_output.seek(0)
    return StreamingResponse(
        io.BytesIO(csv_output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=onside_analysis_{safe_filename}_{job_id[:8]}.csv"
        }
    )


@router.get(
    "/brand-analysis/{job_id}/export/campaign",
    summary="Export Results to Campaign Format",
    description="""
    **Export Onside analysis results in En Garde campaign format**

    This endpoint exports analysis results as a structured JSON object that matches
    En Garde's campaign creation API format. The returned JSON can be directly POSTed
    to `/campaign-spaces` to create a new campaign.

    **Campaign Structure:**
    - campaign_name: "Brand Analysis - {brand_name}"
    - platform: "onside_analysis" (custom platform identifier)
    - import_source: "onside_brand_analysis"
    - Includes all keywords, competitors, and content ideas
    - Metadata tracks the original analysis job and date

    **Use Cases:**
    1. **Create New Campaign**: POST the returned JSON to `/campaign-spaces`
    2. **Add to Existing Campaign**: POST to `/campaign-spaces/{id}/assets/import`
    3. **Review Before Import**: Inspect the structured data before creating campaign

    **Integration Flow:**
    ```javascript
    // Step 1: Get campaign data
    const campaignData = await fetch('/brand-analysis/{job_id}/export/campaign')

    // Step 2: Create campaign in En Garde
    const response = await fetch('/campaign-spaces', {
      method: 'POST',
      body: JSON.stringify(campaignData)
    })
    ```
    """,
    responses={
        200: {
            "description": "Campaign JSON format",
            "content": {
                "application/json": {
                    "example": {
                        "campaign_name": "Brand Analysis - Acme Corp",
                        "platform": "onside_analysis",
                        "import_source": "onside_brand_analysis",
                        "description": "Automated brand digital footprint analysis",
                        "keywords": [],
                        "competitors": [],
                        "content_opportunities": [],
                        "metadata": {
                            "onside_job_id": "abc-123",
                            "analysis_date": "2025-12-24",
                            "brand_website": "https://acme.com"
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid job ID or job not complete"},
        401: {"description": "Unauthorized"},
        404: {"description": "Analysis job not found"}
    }
)
def export_results_to_campaign_format(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export Onside analysis results in En Garde campaign format.

    Returns a JSON structure compatible with POST /campaign-spaces endpoint.
    The data can be directly used to create a new campaign in En Garde.
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format"
        )

    # Verify job exists and belongs to user
    job = db.query(BrandAnalysisJob).filter(
        BrandAnalysisJob.id == job_uuid,
        BrandAnalysisJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis job not found"
        )

    if job.status != AnalysisStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis is not complete. Current status: {job.status.value}"
        )

    # Get all keywords, competitors, and opportunities
    keywords = db.query(DiscoveredKeyword).filter(
        DiscoveredKeyword.job_id == job_uuid
    ).all()

    competitors = db.query(IdentifiedCompetitor).filter(
        IdentifiedCompetitor.job_id == job_uuid
    ).all()

    opportunities = db.query(ContentOpportunity).filter(
        ContentOpportunity.job_id == job_uuid
    ).all()

    # Transform data using EnGardeDataTransformer
    transformer = EnGardeDataTransformer()

    # Transform keywords
    transformed_keywords = transformer.transform_keywords(keywords)
    keywords_data = [kw.dict() for kw in transformed_keywords]

    # Transform competitors
    transformed_competitors = transformer.transform_competitors(competitors)
    competitors_data = [comp.dict() for comp in transformed_competitors]

    # Transform opportunities
    transformed_opportunities = transformer.transform_content_opportunities(opportunities)
    opportunities_data = [opp.dict() for opp in transformed_opportunities]

    # Get brand info from questionnaire
    questionnaire = job.questionnaire or {}
    brand_name = questionnaire.get("brand_name", "Unknown Brand")
    brand_website = questionnaire.get("primary_website", "")
    industry = questionnaire.get("industry", "")

    # Build campaign structure compatible with En Garde
    campaign_data = {
        "campaign_name": f"Brand Analysis - {brand_name}",
        "platform": "onside_analysis",  # Custom platform identifier
        "import_source": "onside_brand_analysis",
        "description": f"Automated brand digital footprint analysis for {brand_name}. "
                      f"Discovered {len(keywords)} keywords, {len(competitors)} competitors, "
                      f"and {len(opportunities)} content opportunities.",
        "campaign_objective": "Brand digital footprint analysis and SEO strategy",
        "target_audience": questionnaire.get("target_markets", []),
        "is_active": False,  # Start as inactive, user can activate
        "tags": [
            "onside_analysis",
            "brand_audit",
            "seo_research",
            industry.lower().replace(" ", "_") if industry else "general"
        ],
        "category": "brand_analysis",
        "import_metadata": {
            "onside_job_id": str(job_id),
            "analysis_date": job.completed_at.isoformat() if job.completed_at else datetime.utcnow().isoformat(),
            "brand_name": brand_name,
            "brand_website": brand_website,
            "industry": industry,
            "questionnaire": questionnaire,
            "total_keywords": len(keywords),
            "total_competitors": len(competitors),
            "total_opportunities": len(opportunities)
        },
        "keywords": keywords_data,
        "competitors": competitors_data,
        "content_opportunities": opportunities_data,
        "currency": "USD",
        "budget": None  # No budget for analysis campaigns
    }

    return campaign_data


@router.delete(
    "/brand-analysis/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Analysis Job",
    description="""
    **Delete a brand analysis job and all associated data**

    Permanently removes an analysis job and all its related data including:
    - Discovered keywords
    - Identified competitors
    - Content opportunities
    - Analysis metadata

    **Use Cases:**
    - Cleaning up old/unwanted analyses
    - Removing failed jobs
    - Managing storage space

    **Warning:** This action cannot be undone. Confirmed items that have already
    been imported to the main database will NOT be deleted.
    """,
    responses={
        200: {
            "description": "Job deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Brand analysis job deleted successfully"
                    }
                }
            }
        },
        400: {"description": "Invalid job ID format"},
        401: {"description": "Unauthorized - Invalid or missing authentication token"},
        404: {"description": "Analysis job not found"}
    }
)
def delete_brand_analysis(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a brand analysis job and all associated data.

    Args:
        job_id: UUID of the analysis job
        db: Database session
        current_user: Authenticated user

    Returns:
        Success message
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format"
        )

    job = db.query(BrandAnalysisJob).filter(
        BrandAnalysisJob.id == job_uuid,
        BrandAnalysisJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis job not found"
        )

    # Delete job (cascade will delete related records)
    db.delete(job)
    db.commit()

    return {"message": "Brand analysis job deleted successfully"}
