"""Data transformation service for converting Onside format to En Garde format.

This service provides:
- Format conversion between Onside and En Garde schemas
- Data enrichment logic
- Schema validation using Pydantic
- Bidirectional transformation
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator, ConfigDict

from src.models.brand_analysis import (
    KeywordSource,
    CompetitorCategory,
    GapType,
    ContentPriority
)

logger = logging.getLogger(__name__)


class TransformationError(Exception):
    """Exception raised for transformation errors."""
    pass


# Pydantic schemas for En Garde format


class EnGardeKeywordSchema(BaseModel):
    """En Garde keyword schema."""
    model_config = ConfigDict(use_enum_values=True)

    keyword: str = Field(..., min_length=1, max_length=255)
    search_volume: Optional[int] = Field(None, ge=0)
    difficulty: Optional[float] = Field(None, ge=0, le=100)
    cpc: Optional[float] = Field(None, ge=0)
    intent: Optional[str] = Field(None)
    category: Optional[str] = Field(None)
    priority: Optional[str] = Field(None)
    current_rank: Optional[int] = Field(None, ge=0)
    target_rank: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = Field(None)
    tags: List[str] = Field(default_factory=list)

    @validator('intent')
    def validate_intent(cls, v):
        """Validate keyword intent."""
        if v and v not in ['informational', 'navigational', 'transactional', 'commercial']:
            raise ValueError('Invalid keyword intent')
        return v


class EnGardeCompetitorSchema(BaseModel):
    """En Garde competitor schema."""
    model_config = ConfigDict(use_enum_values=True)

    domain: str = Field(..., min_length=1, max_length=255)
    name: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None)
    tier: Optional[str] = Field(None)
    focus_areas: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    market_share: Optional[float] = Field(None, ge=0, le=100)
    domain_authority: Optional[int] = Field(None, ge=0, le=100)
    monthly_traffic: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = Field(None)

    @validator('tier')
    def validate_tier(cls, v):
        """Validate competitor tier."""
        if v and v not in ['primary', 'secondary', 'tertiary']:
            raise ValueError('Invalid competitor tier')
        return v


class OnsideKeywordSchema(BaseModel):
    """Onside keyword schema (from brand analysis)."""
    model_config = ConfigDict(use_enum_values=True)

    keyword: str
    source: str
    search_volume: Optional[int] = None
    difficulty: Optional[float] = None
    relevance_score: float
    current_ranking: Optional[int] = None
    serp_features: Optional[Dict[str, Any]] = None
    confirmed: bool = False


class OnsideCompetitorSchema(BaseModel):
    """Onside competitor schema (from brand analysis)."""
    model_config = ConfigDict(use_enum_values=True)

    domain: str
    name: Optional[str] = None
    relevance_score: float
    category: str
    overlap_percentage: Optional[float] = None
    keyword_overlap: Optional[List[str]] = None
    content_similarity: Optional[float] = None
    confirmed: bool = False


class DataTransformer:
    """Service for transforming data between Onside and En Garde formats.

    Provides:
    - Onside → En Garde format conversion
    - Data enrichment during transformation
    - Schema validation
    - Bidirectional transformations
    """

    # Mapping from Onside categories to En Garde tiers
    CATEGORY_TO_TIER_MAP = {
        CompetitorCategory.PRIMARY.value: 'primary',
        CompetitorCategory.SECONDARY.value: 'secondary',
        CompetitorCategory.EMERGING.value: 'secondary',
        CompetitorCategory.NICHE.value: 'tertiary',
    }

    # Mapping from KeywordSource to intent
    SOURCE_TO_INTENT_MAP = {
        KeywordSource.WEBSITE_CONTENT.value: 'informational',
        KeywordSource.SERP_ANALYSIS.value: 'commercial',
        KeywordSource.NLP_EXTRACTION.value: 'informational',
    }

    # Priority mapping
    PRIORITY_MAP = {
        ContentPriority.HIGH.value: 'high',
        ContentPriority.MEDIUM.value: 'medium',
        ContentPriority.LOW.value: 'low',
    }

    def __init__(self):
        """Initialize the data transformer."""
        pass

    def transform_keyword_to_engarde(
        self,
        onside_keyword: Dict[str, Any],
        enrich: bool = True
    ) -> EnGardeKeywordSchema:
        """Transform Onside keyword to En Garde format.

        Args:
            onside_keyword: Keyword data in Onside format
            enrich: Whether to enrich data during transformation

        Returns:
            EnGardeKeywordSchema instance

        Raises:
            TransformationError: If transformation fails
        """
        try:
            # Validate input
            onside_schema = OnsideKeywordSchema(**onside_keyword)

            # Calculate priority based on relevance score
            priority = self._calculate_keyword_priority(
                relevance_score=onside_schema.relevance_score,
                difficulty=onside_schema.difficulty,
                search_volume=onside_schema.search_volume
            )

            # Infer intent from source
            intent = self.SOURCE_TO_INTENT_MAP.get(
                onside_schema.source,
                'informational'
            )

            # Determine category from keyword
            category = self._infer_keyword_category(onside_schema.keyword)

            # Generate tags
            tags = self._generate_keyword_tags(onside_keyword)

            # Build En Garde keyword
            engarde_keyword = EnGardeKeywordSchema(
                keyword=onside_schema.keyword,
                search_volume=onside_schema.search_volume,
                difficulty=onside_schema.difficulty,
                current_rank=onside_schema.current_ranking,
                intent=intent,
                category=category,
                priority=priority,
                tags=tags,
                notes=f"Imported from brand analysis (source: {onside_schema.source})"
            )

            # Enrich if requested
            if enrich:
                engarde_keyword = self._enrich_keyword(engarde_keyword, onside_keyword)

            logger.debug(f"Transformed keyword: {onside_schema.keyword} → En Garde format")

            return engarde_keyword

        except Exception as e:
            logger.error(f"Failed to transform keyword: {str(e)}")
            raise TransformationError(f"Keyword transformation failed: {str(e)}")

    def transform_competitor_to_engarde(
        self,
        onside_competitor: Dict[str, Any],
        enrich: bool = True
    ) -> EnGardeCompetitorSchema:
        """Transform Onside competitor to En Garde format.

        Args:
            onside_competitor: Competitor data in Onside format
            enrich: Whether to enrich data during transformation

        Returns:
            EnGardeCompetitorSchema instance

        Raises:
            TransformationError: If transformation fails
        """
        try:
            # Validate input
            onside_schema = OnsideCompetitorSchema(**onside_competitor)

            # Map category to tier
            tier = self.CATEGORY_TO_TIER_MAP.get(
                onside_schema.category,
                'secondary'
            )

            # Build website URL
            website = f"https://{onside_schema.domain}"

            # Extract focus areas from keyword overlap
            focus_areas = []
            if onside_schema.keyword_overlap:
                focus_areas = onside_schema.keyword_overlap[:5]  # Top 5 overlapping keywords

            # Estimate domain authority from relevance score
            domain_authority = self._estimate_domain_authority(
                onside_schema.relevance_score,
                onside_schema.overlap_percentage
            )

            # Build En Garde competitor
            engarde_competitor = EnGardeCompetitorSchema(
                domain=onside_schema.domain,
                name=onside_schema.name or self._extract_name_from_domain(onside_schema.domain),
                website=website,
                tier=tier,
                focus_areas=focus_areas,
                domain_authority=domain_authority,
                notes=f"Imported from brand analysis (relevance: {onside_schema.relevance_score:.2f})"
            )

            # Enrich if requested
            if enrich:
                engarde_competitor = self._enrich_competitor(engarde_competitor, onside_competitor)

            logger.debug(f"Transformed competitor: {onside_schema.domain} → En Garde format")

            return engarde_competitor

        except Exception as e:
            logger.error(f"Failed to transform competitor: {str(e)}")
            raise TransformationError(f"Competitor transformation failed: {str(e)}")

    def transform_keywords_batch(
        self,
        onside_keywords: List[Dict[str, Any]],
        enrich: bool = True
    ) -> List[EnGardeKeywordSchema]:
        """Transform batch of keywords to En Garde format.

        Args:
            onside_keywords: List of keyword dicts in Onside format
            enrich: Whether to enrich data

        Returns:
            List of EnGardeKeywordSchema instances
        """
        transformed = []
        errors = []

        for kw in onside_keywords:
            try:
                engarde_kw = self.transform_keyword_to_engarde(kw, enrich=enrich)
                transformed.append(engarde_kw)
            except TransformationError as e:
                errors.append(str(e))
                logger.warning(f"Skipping keyword due to transformation error: {str(e)}")

        logger.info(
            f"Transformed {len(transformed)} keywords "
            f"({len(errors)} errors)"
        )

        return transformed

    def transform_competitors_batch(
        self,
        onside_competitors: List[Dict[str, Any]],
        enrich: bool = True
    ) -> List[EnGardeCompetitorSchema]:
        """Transform batch of competitors to En Garde format.

        Args:
            onside_competitors: List of competitor dicts in Onside format
            enrich: Whether to enrich data

        Returns:
            List of EnGardeCompetitorSchema instances
        """
        transformed = []
        errors = []

        for comp in onside_competitors:
            try:
                engarde_comp = self.transform_competitor_to_engarde(comp, enrich=enrich)
                transformed.append(engarde_comp)
            except TransformationError as e:
                errors.append(str(e))
                logger.warning(f"Skipping competitor due to transformation error: {str(e)}")

        logger.info(
            f"Transformed {len(transformed)} competitors "
            f"({len(errors)} errors)"
        )

        return transformed

    # Helper methods for enrichment and inference

    def _calculate_keyword_priority(
        self,
        relevance_score: float,
        difficulty: Optional[float],
        search_volume: Optional[int]
    ) -> str:
        """Calculate keyword priority based on metrics.

        Args:
            relevance_score: Relevance score (0-1)
            difficulty: Keyword difficulty (0-100)
            search_volume: Monthly search volume

        Returns:
            Priority string: 'high', 'medium', or 'low'
        """
        # Weighted scoring
        score = relevance_score * 100  # Base score from relevance

        # Adjust for search volume
        if search_volume:
            if search_volume > 10000:
                score += 20
            elif search_volume > 1000:
                score += 10
            elif search_volume > 100:
                score += 5

        # Adjust for difficulty (inverse - lower difficulty is better)
        if difficulty is not None:
            if difficulty < 30:
                score += 15
            elif difficulty < 50:
                score += 10
            elif difficulty < 70:
                score += 5

        # Determine priority
        if score >= 80:
            return 'high'
        elif score >= 50:
            return 'medium'
        else:
            return 'low'

    def _infer_keyword_category(self, keyword: str) -> Optional[str]:
        """Infer category from keyword content.

        Args:
            keyword: Keyword string

        Returns:
            Inferred category or None
        """
        keyword_lower = keyword.lower()

        # Category patterns
        patterns = {
            'product': ['buy', 'purchase', 'price', 'cost', 'shop', 'store'],
            'service': ['service', 'consultant', 'agency', 'provider'],
            'informational': ['how to', 'what is', 'guide', 'tutorial', 'learn'],
            'comparison': ['vs', 'versus', 'compare', 'best', 'top'],
            'local': ['near me', 'in', 'local', 'nearby'],
        }

        for category, pattern_words in patterns.items():
            if any(word in keyword_lower for word in pattern_words):
                return category

        return None

    def _generate_keyword_tags(self, keyword_data: Dict[str, Any]) -> List[str]:
        """Generate tags for a keyword.

        Args:
            keyword_data: Keyword data dict

        Returns:
            List of tag strings
        """
        tags = []

        # Add source as tag
        source = keyword_data.get('source', '')
        if source:
            tags.append(f"source:{source}")

        # Add relevance tier
        relevance = keyword_data.get('relevance_score', 0)
        if relevance >= 0.8:
            tags.append('high-relevance')
        elif relevance >= 0.5:
            tags.append('medium-relevance')

        # Add volume tier
        volume = keyword_data.get('search_volume', 0)
        if volume and volume > 10000:
            tags.append('high-volume')
        elif volume and volume > 1000:
            tags.append('medium-volume')

        # Check for SERP features
        serp_features = keyword_data.get('serp_features', [])
        if serp_features:
            if 'featured_snippet' in serp_features:
                tags.append('featured-snippet')
            if 'people_also_ask' in serp_features:
                tags.append('paa')

        # Add import tag
        tags.append('imported')

        return tags

    def _estimate_domain_authority(
        self,
        relevance_score: float,
        overlap_percentage: Optional[float]
    ) -> Optional[int]:
        """Estimate domain authority from relevance metrics.

        Args:
            relevance_score: Relevance score (0-1)
            overlap_percentage: Keyword overlap percentage

        Returns:
            Estimated domain authority (0-100) or None
        """
        # Simple estimation based on relevance and overlap
        base_da = int(relevance_score * 50)  # Base from relevance

        if overlap_percentage:
            overlap_bonus = int((overlap_percentage / 100) * 40)
            base_da += overlap_bonus

        return min(base_da, 100)

    def _extract_name_from_domain(self, domain: str) -> str:
        """Extract brand name from domain.

        Args:
            domain: Domain string

        Returns:
            Extracted brand name
        """
        # Remove TLD
        parts = domain.split('.')
        if len(parts) > 1:
            name = parts[0]
        else:
            name = domain

        # Clean up
        name = name.replace('-', ' ').replace('_', ' ')
        name = name.title()

        return name

    def _enrich_keyword(
        self,
        keyword: EnGardeKeywordSchema,
        original_data: Dict[str, Any]
    ) -> EnGardeKeywordSchema:
        """Enrich keyword with additional data.

        Args:
            keyword: EnGardeKeywordSchema to enrich
            original_data: Original Onside data

        Returns:
            Enriched keyword
        """
        # Add CPC estimate if we have search volume and difficulty
        if keyword.search_volume and keyword.difficulty:
            keyword.cpc = self._estimate_cpc(keyword.search_volume, keyword.difficulty)

        # Set target rank based on current rank
        if keyword.current_rank:
            if keyword.current_rank > 10:
                keyword.target_rank = min(keyword.current_rank - 5, 10)
            else:
                keyword.target_rank = min(keyword.current_rank - 1, 1)

        return keyword

    def _enrich_competitor(
        self,
        competitor: EnGardeCompetitorSchema,
        original_data: Dict[str, Any]
    ) -> EnGardeCompetitorSchema:
        """Enrich competitor with additional data.

        Args:
            competitor: EnGardeCompetitorSchema to enrich
            original_data: Original Onside data

        Returns:
            Enriched competitor
        """
        # Estimate market share from overlap percentage
        overlap = original_data.get('overlap_percentage')
        if overlap:
            competitor.market_share = min(overlap / 10, 15.0)  # Scale to reasonable market share

        # Add strengths based on content similarity
        content_sim = original_data.get('content_similarity')
        if content_sim and content_sim > 0.7:
            competitor.strengths = ['Strong content alignment', 'Similar target audience']

        return competitor

    def _estimate_cpc(self, search_volume: int, difficulty: float) -> float:
        """Estimate CPC based on volume and difficulty.

        Args:
            search_volume: Monthly search volume
            difficulty: Keyword difficulty (0-100)

        Returns:
            Estimated CPC in USD
        """
        # Simple heuristic: higher volume + higher difficulty = higher CPC
        base_cpc = 0.5

        # Volume adjustment
        if search_volume > 10000:
            base_cpc += 2.0
        elif search_volume > 1000:
            base_cpc += 1.0
        elif search_volume > 100:
            base_cpc += 0.5

        # Difficulty adjustment
        difficulty_multiplier = 1 + (difficulty / 100)
        estimated_cpc = base_cpc * difficulty_multiplier

        return round(estimated_cpc, 2)

    def validate_schema(
        self,
        data: Dict[str, Any],
        schema_class: type[BaseModel]
    ) -> tuple[bool, List[str]]:
        """Validate data against a Pydantic schema.

        Args:
            data: Data dictionary to validate
            schema_class: Pydantic model class

        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            schema_class(**data)
            return True, []
        except Exception as e:
            error_messages = str(e).split('\n')
            return False, error_messages
