"""
Competitor Analysis API endpoints for OnSide application.

This module provides endpoints for competitor identification and analysis.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.competitor_analysis import (
    CompetitorAnalysisRequest,
    CompetitorAnalysisResponse,
    CompetitorIdentificationResponse,
    CompetitorComparisonResponse
)
from src.services.competitor_analysis import CompetitorAnalysisService
from src.services.competitor_service import CompetitorService
from src.exceptions import DomainValidationError

router = APIRouter()

@router.post(
    "/identify",
    response_model=List[CompetitorIdentificationResponse],
    summary="Identify potential competitors",
    response_description="List of identified competitors with relevance scores"
)
async def identify_competitors(
    request: CompetitorAnalysisRequest,
    max_results: int = Query(10, ge=1, le=50, description="Maximum number of competitors to return"),
    min_relevance: float = Query(0.5, ge=0.0, le=1.0, description="Minimum relevance score (0-1)"),
    db: AsyncSession = Depends(get_db)
) -> List[CompetitorIdentificationResponse]:
    """Identify potential competitors for a company.
    
    - **company_id**: ID of the company to analyze
    - **max_results**: Maximum number of competitors to return (1-50)
    - **min_relevance**: Minimum relevance score (0-1) for a competitor to be included
    
    Returns a list of potential competitors with relevance scores and analysis.
    """
    service = CompetitorAnalysisService(db)
    
    try:
        competitors = await service.identify_competitors(
            company_id=request.company_id,
            max_competitors=max_results,
            min_relevance_score=min_relevance
        )
        
        return [
            CompetitorIdentificationResponse(
                domain=comp['domain'],
                name=comp.get('name', ''),
                relevance_score=comp['relevance_score'],
                source=comp.get('source', 'unknown'),
                metrics=comp.get('metrics', {}),
                metadata=comp.get('metadata', {})
            )
            for comp in competitors
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error identifying competitors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while identifying competitors"
        )

@router.get(
    "/compare/{company_id}",
    response_model=CompetitorComparisonResponse,
    summary="Compare company with competitors",
    response_description="Detailed comparison with competitors"
)
async def compare_with_competitors(
    company_id: int,
    competitor_ids: str = Query(..., description="Comma-separated list of competitor IDs"),
    metrics: str = Query("traffic,keywords,backlinks", description="Comma-separated list of metrics to compare"),
    db: AsyncSession = Depends(get_db)
) -> CompetitorComparisonResponse:
    """Compare a company with its competitors across various metrics.
    
    - **company_id**: ID of the company to analyze
    - **competitor_ids**: Comma-separated list of competitor IDs to compare with
    - **metrics**: Comma-separated list of metrics to compare (traffic, keywords, backlinks, etc.)
    
    Returns a detailed comparison with the specified competitors.
    """
    competitor_service = CompetitorService(db)
    analysis_service = CompetitorAnalysisService(db)
    
    try:
        # Get the company
        company = await competitor_service.get_company(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with ID {company_id} not found"
            )
        
        # Parse competitor IDs
        competitor_id_list = [int(cid.strip()) for cid in competitor_ids.split(",") if cid.strip().isdigit()]
        if not competitor_id_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid competitor IDs provided"
            )
        
        # Get competitors
        competitors = []
        for cid in competitor_id_list:
            competitor = await competitor_service.get_competitor(cid)
            if competitor:
                competitors.append(competitor)
        
        if not competitors:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No competitors found with the provided IDs"
            )
        
        # Parse metrics
        metric_list = [m.strip().lower() for m in metrics.split(",")]
        
        # Get comparison data
        comparison = await analysis_service.compare_with_competitors(
            company=company,
            competitors=competitors,
            metrics=metric_list
        )
        
        return CompetitorComparisonResponse(
            company_id=company.id,
            company_name=company.name,
            competitors=[
                {
                    "id": comp.id,
                    "name": comp.name,
                    "domain": comp.domain,
                    **comp_metrics
                }
                for comp, comp_metrics in zip(competitors, comparison["competitor_metrics"])
            ],
            metrics=comparison["metrics"],
            summary=comparison.get("summary", ""),
            insights=comparison.get("insights", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing with competitors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while comparing with competitors"
        )

@router.post(
    "/analyze",
    response_model=CompetitorAnalysisResponse,
    summary="Analyze competitors",
    response_description="Competitor analysis results"
)
async def analyze_competitors(
    request: CompetitorAnalysisRequest,
    db: AsyncSession = Depends(get_db)
) -> CompetitorAnalysisResponse:
    """Perform a comprehensive analysis of competitors.
    
    - **company_id**: ID of the company to analyze
    - **competitor_ids**: List of competitor IDs to analyze (if empty, will identify automatically)
    - **analysis_types**: Types of analysis to perform
    - **timeframe**: Timeframe for the analysis (e.g., "7d", "30d", "90d")
    
    Returns a comprehensive analysis of the specified competitors.
    """
    competitor_service = CompetitorService(db)
    analysis_service = CompetitorAnalysisService(db)
    
    try:
        # Get the company
        company = await competitor_service.get_company(request.company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with ID {request.company_id} not found"
            )
        
        # Get competitors
        competitors = []
        if request.competitor_ids:
            for cid in request.competitor_ids:
                competitor = await competitor_service.get_competitor(cid)
                if competitor:
                    competitors.append(competitor)
        
        # If no competitors specified, identify them automatically
        if not competitors:
            identified = await analysis_service.identify_competitors(
                company_id=company.id,
                max_competitors=5,
                min_relevance_score=0.5
            )
            
            # Convert to Competitor objects
            for comp in identified:
                competitor = await competitor_service.get_competitor_by_domain(comp['domain'])
                if not competitor:
                    # Create a new competitor if it doesn't exist
                    competitor = await competitor_service.create_competitor(
                        CompetitorCreate(
                            name=comp.get('name', ''),
                            domain=comp['domain'],
                            metadata=comp.get('metadata', {})
                        )
                    )
                competitors.append(competitor)
        
        # Perform analysis
        analysis = await analysis_service.analyze_competitors(
            company=company,
            competitors=competitors,
            analysis_types=request.analysis_types,
            timeframe=request.timeframe
        )
        
        return CompetitorAnalysisResponse(
            company_id=company.id,
            company_name=company.name,
            competitors=[
                {
                    "id": comp.id,
                    "name": comp.name,
                    "domain": comp.domain,
                    **comp_analysis
                }
                for comp, comp_analysis in zip(competitors, analysis["competitor_analysis"])
            ],
            summary=analysis.get("summary", ""),
            insights=analysis.get("insights", []),
            recommendations=analysis.get("recommendations", []),
            metrics=analysis.get("metrics", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing competitors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while analyzing competitors"
        )
