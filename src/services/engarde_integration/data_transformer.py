"""
Data Transformation Layer for En Garde ↔ Onside Integration

This module provides comprehensive data transformation between Onside's
brand analysis format and En Garde's campaign management format.

Features:
- Bidirectional data transformation (Onside ↔ En Garde)
- Field mapping and normalization
- Data enrichment with derived metrics
- Comprehensive validation rules
- Pydantic schemas for type safety
- Error handling and data quality checks
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from decimal import Decimal
import re

from pydantic import BaseModel, Field, validator, ValidationError

logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC SCHEMAS - ONSIDE FORMAT
# ============================================================================

class OnsideKeywordSchema(BaseModel):
    """Onside discovered keyword format."""

    id: Optional[int] = None
    keyword: str = Field(..., min_length=1, max_length=500)
    source: str = Field(..., description="website_content, serp_analysis, nlp_extraction")
    search_volume: Optional[int] = Field(None, ge=0)
    difficulty: Optional[float] = Field(None, ge=0, le=100)
    relevance_score: float = Field(..., ge=0, le=1)
    current_ranking: Optional[int] = Field(None, ge=0)
    serp_features: Optional[Dict[str, Any]] = None
    confirmed: bool = False

    class Config:
        from_attributes = True


class OnsideCompetitorSchema(BaseModel):
    """Onside identified competitor format."""

    id: Optional[int] = None
    domain: str = Field(..., pattern=r'^[a-zA-Z0-9][a-zA-Z0-9-]*\.[a-zA-Z]{2,}$')
    name: Optional[str] = None
    relevance_score: float = Field(..., ge=0, le=1)
    category: str = Field(..., description="primary, secondary, emerging, niche")
    overlap_percentage: Optional[float] = Field(None, ge=0, le=100)
    keyword_overlap: Optional[Dict[str, Any]] = None
    content_similarity: Optional[float] = Field(None, ge=0, le=1)
    confirmed: bool = False

    class Config:
        from_attributes = True


class OnsideContentOpportunitySchema(BaseModel):
    """Onside content opportunity format."""

    id: Optional[int] = None
    topic: str = Field(..., min_length=1, max_length=500)
    theme: Optional[str] = None
    gap_type: str = Field(..., description="missing_content, weak_content, competitor_strength")
    traffic_potential: Optional[int] = Field(None, ge=0)
    difficulty: Optional[float] = Field(None, ge=0, le=100)
    priority: str = Field(..., description="high, medium, low")
    recommended_format: Optional[str] = Field(None, description="blog, guide, video, infographic")
    related_keywords: Optional[List[str]] = None

    class Config:
        from_attributes = True


# ============================================================================
# PYDANTIC SCHEMAS - EN GARDE FORMAT
# ============================================================================

class EnGardeKeywordSchema(BaseModel):
    """En Garde keyword format for campaign management."""

    keyword_text: str = Field(..., min_length=1, max_length=500)
    search_volume: Optional[int] = Field(None, ge=0)
    competition_score: Optional[float] = Field(None, ge=0, le=100)
    cpc_estimate: Optional[Decimal] = Field(None, ge=0)
    current_position: Optional[int] = Field(None, ge=0)
    target_position: Optional[int] = Field(None, ge=1, le=10)
    priority_level: str = Field(default="medium", description="high, medium, low")
    category: Optional[str] = None
    intent_type: Optional[str] = Field(
        None,
        description="informational, navigational, transactional, commercial"
    )
    metadata: Optional[Dict[str, Any]] = None
    source: str = Field(default="onside_analysis", description="Source system")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('cpc_estimate', pre=True)
    def convert_to_decimal(cls, v):
        """Convert float to Decimal for CPC."""
        if v is None:
            return v
        return Decimal(str(v))


class EnGardeCompetitorSchema(BaseModel):
    """En Garde competitor format for competitive analysis."""

    competitor_name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., pattern=r'^[a-zA-Z0-9][a-zA-Z0-9-]*\.[a-zA-Z]{2,}$')
    competitor_type: str = Field(
        default="direct",
        description="direct, indirect, aspirational, emerging"
    )
    market_share: Optional[float] = Field(None, ge=0, le=100)
    strength_score: Optional[float] = Field(None, ge=0, le=100)
    keyword_overlap_count: Optional[int] = Field(None, ge=0)
    shared_keywords: Optional[List[str]] = None
    competitive_advantages: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    monitoring_enabled: bool = Field(default=True)
    metadata: Optional[Dict[str, Any]] = None
    source: str = Field(default="onside_analysis")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EnGardeContentIdeaSchema(BaseModel):
    """En Garde content idea format for content planning."""

    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    content_type: str = Field(
        default="blog_post",
        description="blog_post, guide, video, infographic, case_study, whitepaper"
    )
    priority: str = Field(default="medium", description="high, medium, low")
    estimated_traffic: Optional[int] = Field(None, ge=0)
    difficulty_score: Optional[float] = Field(None, ge=0, le=100)
    target_keywords: Optional[List[str]] = None
    target_audience: Optional[str] = None
    content_gap: Optional[str] = None
    competitor_coverage: Optional[bool] = None
    status: str = Field(default="idea", description="idea, planned, in_progress, published")
    metadata: Optional[Dict[str, Any]] = None
    source: str = Field(default="onside_analysis")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# DATA TRANSFORMER CLASS
# ============================================================================

class EnGardeDataTransformer:
    """
    Transforms data between Onside and En Garde formats.

    Provides bidirectional transformation with:
    - Field mapping and normalization
    - Data enrichment with derived metrics
    - Validation and error handling
    - Type safety with Pydantic schemas
    """

    # Mapping configurations
    COMPETITOR_CATEGORY_MAP = {
        "primary": "direct",
        "secondary": "indirect",
        "emerging": "emerging",
        "niche": "indirect"
    }

    CONTENT_FORMAT_MAP = {
        "blog": "blog_post",
        "guide": "guide",
        "video": "video",
        "infographic": "infographic",
        "case_study": "case_study",
        "whitepaper": "whitepaper"
    }

    PRIORITY_MAP = {
        "high": "high",
        "medium": "medium",
        "low": "low"
    }

    def __init__(self):
        """Initialize data transformer."""
        self.validation_errors: List[Dict[str, Any]] = []
        self.transformation_stats = {
            "keywords_transformed": 0,
            "competitors_transformed": 0,
            "opportunities_transformed": 0,
            "validation_errors": 0,
            "enrichments_applied": 0
        }

    def transform_keywords(
        self,
        onside_keywords: List[Union[Dict[str, Any], OnsideKeywordSchema]]
    ) -> List[EnGardeKeywordSchema]:
        """
        Transform Onside keywords to En Garde format.

        Args:
            onside_keywords: List of Onside keyword dictionaries or schemas

        Returns:
            List of En Garde keyword schemas
        """
        transformed = []

        for keyword_data in onside_keywords:
            try:
                # Ensure we have a validated Onside schema
                if isinstance(keyword_data, dict):
                    onside_keyword = OnsideKeywordSchema(**keyword_data)
                else:
                    onside_keyword = keyword_data

                # Calculate derived metrics
                intent_type = self._infer_search_intent(onside_keyword.keyword)
                cpc_estimate = self._estimate_cpc(
                    onside_keyword.search_volume,
                    onside_keyword.difficulty
                )
                priority = self._calculate_keyword_priority(
                    onside_keyword.search_volume,
                    onside_keyword.difficulty,
                    onside_keyword.relevance_score
                )

                # Map to En Garde format
                engarde_keyword = EnGardeKeywordSchema(
                    keyword_text=onside_keyword.keyword,
                    search_volume=onside_keyword.search_volume,
                    competition_score=onside_keyword.difficulty,
                    cpc_estimate=cpc_estimate,
                    current_position=onside_keyword.current_ranking,
                    target_position=self._calculate_target_position(
                        onside_keyword.current_ranking
                    ),
                    priority_level=priority,
                    category=onside_keyword.source,
                    intent_type=intent_type,
                    metadata={
                        "onside_id": onside_keyword.id,
                        "relevance_score": onside_keyword.relevance_score,
                        "serp_features": onside_keyword.serp_features,
                        "confirmed": onside_keyword.confirmed,
                        "transformation_date": datetime.utcnow().isoformat()
                    },
                    source="onside_analysis"
                )

                transformed.append(engarde_keyword)
                self.transformation_stats["keywords_transformed"] += 1
                self.transformation_stats["enrichments_applied"] += 3  # intent, cpc, priority

            except ValidationError as e:
                logger.error(f"Validation error transforming keyword: {str(e)}")
                self.validation_errors.append({
                    "type": "keyword",
                    "data": keyword_data,
                    "error": str(e)
                })
                self.transformation_stats["validation_errors"] += 1

        return transformed

    def transform_competitors(
        self,
        onside_competitors: List[Union[Dict[str, Any], OnsideCompetitorSchema]]
    ) -> List[EnGardeCompetitorSchema]:
        """
        Transform Onside competitors to En Garde format.

        Args:
            onside_competitors: List of Onside competitor dictionaries or schemas

        Returns:
            List of En Garde competitor schemas
        """
        transformed = []

        for competitor_data in onside_competitors:
            try:
                # Ensure we have a validated Onside schema
                if isinstance(competitor_data, dict):
                    onside_competitor = OnsideCompetitorSchema(**competitor_data)
                else:
                    onside_competitor = competitor_data

                # Map competitor category
                competitor_type = self.COMPETITOR_CATEGORY_MAP.get(
                    onside_competitor.category,
                    "direct"
                )

                # Calculate strength score
                strength_score = self._calculate_competitor_strength(
                    onside_competitor.relevance_score,
                    onside_competitor.overlap_percentage,
                    onside_competitor.content_similarity
                )

                # Extract competitive insights
                competitive_advantages = self._extract_competitive_advantages(
                    onside_competitor
                )

                # Map to En Garde format
                engarde_competitor = EnGardeCompetitorSchema(
                    competitor_name=onside_competitor.name or self._extract_brand_name(
                        onside_competitor.domain
                    ),
                    domain=onside_competitor.domain,
                    competitor_type=competitor_type,
                    market_share=onside_competitor.overlap_percentage,
                    strength_score=strength_score,
                    keyword_overlap_count=self._extract_keyword_count(
                        onside_competitor.keyword_overlap
                    ),
                    shared_keywords=self._extract_shared_keywords(
                        onside_competitor.keyword_overlap
                    ),
                    competitive_advantages=competitive_advantages,
                    weaknesses=None,  # Would require deeper analysis
                    monitoring_enabled=onside_competitor.confirmed,
                    metadata={
                        "onside_id": onside_competitor.id,
                        "relevance_score": onside_competitor.relevance_score,
                        "content_similarity": onside_competitor.content_similarity,
                        "keyword_overlap_data": onside_competitor.keyword_overlap,
                        "transformation_date": datetime.utcnow().isoformat()
                    },
                    source="onside_analysis"
                )

                transformed.append(engarde_competitor)
                self.transformation_stats["competitors_transformed"] += 1
                self.transformation_stats["enrichments_applied"] += 2  # strength, advantages

            except ValidationError as e:
                logger.error(f"Validation error transforming competitor: {str(e)}")
                self.validation_errors.append({
                    "type": "competitor",
                    "data": competitor_data,
                    "error": str(e)
                })
                self.transformation_stats["validation_errors"] += 1

        return transformed

    def transform_content_opportunities(
        self,
        onside_opportunities: List[Union[Dict[str, Any], OnsideContentOpportunitySchema]]
    ) -> List[EnGardeContentIdeaSchema]:
        """
        Transform Onside content opportunities to En Garde content ideas.

        Args:
            onside_opportunities: List of Onside opportunity dictionaries or schemas

        Returns:
            List of En Garde content idea schemas
        """
        transformed = []

        for opportunity_data in onside_opportunities:
            try:
                # Ensure we have a validated Onside schema
                if isinstance(opportunity_data, dict):
                    onside_opportunity = OnsideContentOpportunitySchema(**opportunity_data)
                else:
                    onside_opportunity = opportunity_data

                # Map content format
                content_type = self.CONTENT_FORMAT_MAP.get(
                    onside_opportunity.recommended_format or "blog",
                    "blog_post"
                )

                # Generate description from gap analysis
                description = self._generate_content_description(onside_opportunity)

                # Map to En Garde format
                engarde_content = EnGardeContentIdeaSchema(
                    title=onside_opportunity.topic,
                    description=description,
                    content_type=content_type,
                    priority=self.PRIORITY_MAP.get(
                        onside_opportunity.priority,
                        "medium"
                    ),
                    estimated_traffic=onside_opportunity.traffic_potential,
                    difficulty_score=onside_opportunity.difficulty,
                    target_keywords=onside_opportunity.related_keywords or [],
                    target_audience=None,  # Would require user input
                    content_gap=onside_opportunity.gap_type,
                    competitor_coverage=onside_opportunity.gap_type == "competitor_strength",
                    status="idea",
                    metadata={
                        "onside_id": onside_opportunity.id,
                        "theme": onside_opportunity.theme,
                        "gap_type": onside_opportunity.gap_type,
                        "transformation_date": datetime.utcnow().isoformat()
                    },
                    source="onside_analysis"
                )

                transformed.append(engarde_content)
                self.transformation_stats["opportunities_transformed"] += 1
                self.transformation_stats["enrichments_applied"] += 1  # description

            except ValidationError as e:
                logger.error(f"Validation error transforming opportunity: {str(e)}")
                self.validation_errors.append({
                    "type": "content_opportunity",
                    "data": opportunity_data,
                    "error": str(e)
                })
                self.transformation_stats["validation_errors"] += 1

        return transformed

    def validate_transformed_data(
        self,
        data: Union[
            List[EnGardeKeywordSchema],
            List[EnGardeCompetitorSchema],
            List[EnGardeContentIdeaSchema]
        ]
    ) -> Dict[str, Any]:
        """
        Validate transformed data for integrity and quality.

        Args:
            data: List of transformed schemas

        Returns:
            Validation report with:
                - is_valid: Overall validation status
                - item_count: Number of items validated
                - errors: List of validation errors
                - warnings: List of validation warnings
                - quality_score: Data quality score (0-100)
        """
        if not data:
            return {
                "is_valid": False,
                "item_count": 0,
                "errors": ["No data provided for validation"],
                "warnings": [],
                "quality_score": 0
            }

        errors = []
        warnings = []
        quality_metrics = {
            "complete_records": 0,
            "missing_optional_fields": 0,
            "total_records": len(data)
        }

        for item in data:
            # Check for data completeness
            if isinstance(item, EnGardeKeywordSchema):
                if not item.search_volume:
                    warnings.append(f"Keyword '{item.keyword_text}' missing search volume")
                    quality_metrics["missing_optional_fields"] += 1
                else:
                    quality_metrics["complete_records"] += 1

                if item.competition_score and item.competition_score > 80:
                    warnings.append(
                        f"Keyword '{item.keyword_text}' has very high competition ({item.competition_score})"
                    )

            elif isinstance(item, EnGardeCompetitorSchema):
                if not item.strength_score:
                    warnings.append(f"Competitor '{item.competitor_name}' missing strength score")
                    quality_metrics["missing_optional_fields"] += 1
                else:
                    quality_metrics["complete_records"] += 1

            elif isinstance(item, EnGardeContentIdeaSchema):
                if not item.target_keywords:
                    warnings.append(f"Content idea '{item.title}' missing target keywords")
                    quality_metrics["missing_optional_fields"] += 1
                else:
                    quality_metrics["complete_records"] += 1

        # Calculate quality score
        completeness_score = (
            quality_metrics["complete_records"] / quality_metrics["total_records"]
        ) * 100 if quality_metrics["total_records"] > 0 else 0

        quality_score = completeness_score

        return {
            "is_valid": len(errors) == 0,
            "item_count": len(data),
            "errors": errors,
            "warnings": warnings,
            "quality_score": round(quality_score, 2),
            "metrics": quality_metrics
        }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _infer_search_intent(self, keyword: str) -> str:
        """Infer search intent from keyword text."""
        keyword_lower = keyword.lower()

        # Transactional intent
        transactional_terms = ["buy", "purchase", "order", "price", "cost", "cheap", "discount"]
        if any(term in keyword_lower for term in transactional_terms):
            return "transactional"

        # Navigational intent
        navigational_terms = ["login", "sign in", "website", "official"]
        if any(term in keyword_lower for term in navigational_terms):
            return "navigational"

        # Commercial investigation
        commercial_terms = ["best", "top", "review", "compare", "vs", "alternative"]
        if any(term in keyword_lower for term in commercial_terms):
            return "commercial"

        # Default to informational
        return "informational"

    def _estimate_cpc(
        self,
        search_volume: Optional[int],
        difficulty: Optional[float]
    ) -> Optional[Decimal]:
        """Estimate cost-per-click based on volume and difficulty."""
        if not search_volume or not difficulty:
            return None

        # Simple estimation formula
        base_cpc = 0.5
        volume_factor = min(search_volume / 10000, 2.0)
        difficulty_factor = difficulty / 100

        estimated_cpc = base_cpc * (1 + volume_factor) * (1 + difficulty_factor)

        return Decimal(str(round(estimated_cpc, 2)))

    def _calculate_keyword_priority(
        self,
        search_volume: Optional[int],
        difficulty: Optional[float],
        relevance_score: float
    ) -> str:
        """Calculate keyword priority based on multiple factors."""
        score = 0

        # High relevance is most important
        if relevance_score >= 0.8:
            score += 40
        elif relevance_score >= 0.6:
            score += 20

        # Good volume with reasonable difficulty
        if search_volume and difficulty:
            if search_volume >= 1000 and difficulty <= 50:
                score += 30
            elif search_volume >= 500 and difficulty <= 60:
                score += 20
            elif search_volume >= 100:
                score += 10

        if score >= 60:
            return "high"
        elif score >= 30:
            return "medium"
        else:
            return "low"

    def _calculate_target_position(self, current_position: Optional[int]) -> Optional[int]:
        """Calculate target ranking position based on current position."""
        if not current_position:
            return 10  # Default target

        if current_position <= 3:
            return 1
        elif current_position <= 10:
            return 5
        elif current_position <= 20:
            return 10
        else:
            return min(current_position - 5, 10)

    def _calculate_competitor_strength(
        self,
        relevance_score: float,
        overlap_percentage: Optional[float],
        content_similarity: Optional[float]
    ) -> float:
        """Calculate overall competitor strength score."""
        score = relevance_score * 40  # Max 40 points

        if overlap_percentage:
            score += (overlap_percentage / 100) * 30  # Max 30 points

        if content_similarity:
            score += content_similarity * 30  # Max 30 points

        return round(score, 2)

    def _extract_competitive_advantages(
        self,
        competitor: OnsideCompetitorSchema
    ) -> List[str]:
        """Extract competitive advantages from competitor data."""
        advantages = []

        if competitor.relevance_score >= 0.8:
            advantages.append("High market relevance")

        if competitor.overlap_percentage and competitor.overlap_percentage >= 70:
            advantages.append("Strong keyword overlap")

        if competitor.content_similarity and competitor.content_similarity >= 0.7:
            advantages.append("Similar content strategy")

        if competitor.category == "primary":
            advantages.append("Primary competitor in space")

        return advantages

    def _extract_brand_name(self, domain: str) -> str:
        """Extract brand name from domain."""
        # Remove TLD and format as brand name
        brand = domain.split('.')[0]
        return brand.replace('-', ' ').replace('_', ' ').title()

    def _extract_keyword_count(self, keyword_overlap: Optional[Dict[str, Any]]) -> Optional[int]:
        """Extract keyword count from overlap data."""
        if not keyword_overlap:
            return None

        if isinstance(keyword_overlap, dict):
            if "count" in keyword_overlap:
                return keyword_overlap["count"]
            if "keywords" in keyword_overlap and isinstance(keyword_overlap["keywords"], list):
                return len(keyword_overlap["keywords"])

        return None

    def _extract_shared_keywords(
        self,
        keyword_overlap: Optional[Dict[str, Any]]
    ) -> Optional[List[str]]:
        """Extract shared keywords list from overlap data."""
        if not keyword_overlap:
            return None

        if isinstance(keyword_overlap, dict) and "keywords" in keyword_overlap:
            keywords = keyword_overlap["keywords"]
            if isinstance(keywords, list):
                return keywords[:20]  # Limit to top 20

        return None

    def _generate_content_description(
        self,
        opportunity: OnsideContentOpportunitySchema
    ) -> str:
        """Generate content description from opportunity data."""
        gap_descriptions = {
            "missing_content": "We currently lack content covering this topic, presenting an opportunity to fill this gap.",
            "weak_content": "Our existing content on this topic is underperforming and could be strengthened.",
            "competitor_strength": "Competitors are successfully targeting this area, and we should compete."
        }

        base_description = gap_descriptions.get(
            opportunity.gap_type,
            "Content opportunity identified through brand analysis."
        )

        if opportunity.traffic_potential:
            base_description += f" Estimated traffic potential: {opportunity.traffic_potential} monthly visitors."

        if opportunity.related_keywords:
            base_description += f" Target keywords: {', '.join(opportunity.related_keywords[:5])}."

        return base_description

    def get_transformation_stats(self) -> Dict[str, Any]:
        """Get transformation statistics."""
        return {
            **self.transformation_stats,
            "validation_errors_list": self.validation_errors,
            "timestamp": datetime.utcnow().isoformat()
        }

    def reset_stats(self):
        """Reset transformation statistics."""
        self.validation_errors = []
        self.transformation_stats = {
            "keywords_transformed": 0,
            "competitors_transformed": 0,
            "opportunities_transformed": 0,
            "validation_errors": 0,
            "enrichments_applied": 0
        }
