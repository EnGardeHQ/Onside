"""Request Models for OnSide API (S5-04)

This module defines Pydantic models for API requests following
Semantic Seed Venture Studio Coding Standards V2.0.

Features:
1. Request validation for report generation
2. Integration with AI/ML services from Sprint 4
3. Progress tracking support
4. Comprehensive error handling
"""
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, validator

class CompetitorReportRequest(BaseModel):
    """Request model for competitor report generation.
    
    Integrates with:
    - Competitor Analysis Service
    - Market Analysis Service
    - Audience Analysis Service
    """
    company_id: int = Field(..., description="ID of the company to analyze")
    competitor_ids: List[int] = Field(
        ...,
        description="List of competitor IDs to include in analysis",
        max_items=10
    )
    include_market_analysis: bool = Field(
        True,
        description="Whether to include market analysis in report"
    )
    include_audience_analysis: bool = Field(
        True,
        description="Whether to include audience analysis in report"
    )
    confidence_threshold: float = Field(
        0.6,
        description="Minimum confidence score for insights",
        ge=0.0,
        le=1.0
    )
    
    @validator("competitor_ids")
    def validate_competitor_count(cls, v: List[int]) -> List[int]:
        """Validate number of competitors.
        
        Args:
            v: List of competitor IDs
            
        Returns:
            Validated list of competitor IDs
            
        Raises:
            ValueError: If too many competitors specified
        """
        if len(v) > 10:
            raise ValueError("Maximum of 10 competitors allowed")
        return v

class ProgressUpdateRequest(BaseModel):
    """Request model for progress updates.
    
    Used by WebSocket connections to receive real-time
    progress updates during report generation.
    """
    report_id: int = Field(..., description="ID of the report to track")
    user_id: int = Field(..., description="ID of the user requesting updates")
    stages: Optional[List[str]] = Field(
        None,
        description="Optional list of stages to track. If None, track all stages."
    )
    
    @validator("stages", pre=True)
    def validate_stages(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate progress stages.
        
        Args:
            v: List of stage names
            
        Returns:
            Validated list of stage names
            
        Raises:
            ValueError: If invalid stage specified
        """
        if v is None:
            return v
            
        valid_stages = {
            "DATA_COLLECTION",
            "COMPETITOR_ANALYSIS",
            "MARKET_ANALYSIS",
            "AUDIENCE_ANALYSIS",
            "REPORT_GENERATION",
            "VISUALIZATION",
            "FINALIZATION"
        }
        
        invalid_stages = set(v) - valid_stages
        if invalid_stages:
            raise ValueError(
                f"Invalid stages: {', '.join(invalid_stages)}. "
                f"Valid stages are: {', '.join(valid_stages)}"
            )
        return v

class MarketReportRequest(BaseModel):
    """Request model for market analysis report generation.
    
    Integrates with:
    - Market Analysis Service with predictive analytics
    - Competitive Landscape Analysis
    - Industry Trend Forecasting
    """
    company_id: int = Field(..., description="ID of the company to analyze")
    industry_id: int = Field(..., description="ID of the industry to analyze")
    competitor_ids: List[int] = Field(
        ...,
        description="List of competitor IDs to include in market analysis",
        max_items=10
    )
    time_period: str = Field(
        "12M",
        description="Time period for market analysis (3M, 6M, 12M, 24M, 36M)"
    )
    include_predictive_trends: bool = Field(
        True,
        description="Whether to include AI-driven predictive trend analysis"
    )
    focus_areas: Optional[List[str]] = Field(
        None,
        description="Optional specific market areas to focus analysis on"
    )
    confidence_threshold: float = Field(
        0.7,
        description="Minimum confidence score for market insights",
        ge=0.0,
        le=1.0
    )
    
    @validator("time_period")
    def validate_time_period(cls, v: str) -> str:
        """Validate time period format.
        
        Args:
            v: Time period string (e.g., "12M")
            
        Returns:
            Validated time period string
            
        Raises:
            ValueError: If invalid time period specified
        """
        valid_periods = {"3M", "6M", "12M", "24M", "36M"}
        if v not in valid_periods:
            raise ValueError(
                f"Invalid time period: {v}. "
                f"Valid periods are: {', '.join(valid_periods)}"
            )
        return v

    @validator("competitor_ids")
    def validate_competitor_count(cls, v: List[int]) -> List[int]:
        """Validate number of competitors.
        
        Args:
            v: List of competitor IDs
            
        Returns:
            Validated list of competitor IDs
            
        Raises:
            ValueError: If too many competitors specified
        """
        if len(v) > 10:
            raise ValueError("Maximum of 10 competitors allowed for market analysis")
        return v

class AudienceReportRequest(BaseModel):
    """Request model for audience analysis report generation.
    
    Integrates with:
    - Audience Analysis Service with AI-driven persona generation
    - Competitor audience overlap analysis
    - Target market segmentation
    """
    company_id: int = Field(..., description="ID of the company to analyze")
    target_market_segments: List[str] = Field(
        ...,
        description="List of target market segments to analyze",
        min_items=1,
        max_items=5
    )
    competitor_ids: Optional[List[int]] = Field(
        [],
        description="Optional list of competitor IDs for audience overlap analysis"
    )
    include_persona_generation: bool = Field(
        True,
        description="Whether to include AI-driven persona generation"
    )
    persona_count: int = Field(
        3,
        description="Number of audience personas to generate",
        ge=1,
        le=5
    )
    demographic_filters: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Optional demographic filters for audience analysis"
    )
    confidence_threshold: float = Field(
        0.65,
        description="Minimum confidence score for audience insights",
        ge=0.0,
        le=1.0
    )
    
    @validator("target_market_segments")
    def validate_market_segments(cls, v: List[str]) -> List[str]:
        """Validate market segments.
        
        Args:
            v: List of market segments
            
        Returns:
            Validated list of market segments
            
        Raises:
            ValueError: If too many segments specified
        """
        if len(v) > 5:
            raise ValueError("Maximum of 5 market segments allowed for analysis")
        if len(v) < 1:
            raise ValueError("At least 1 market segment must be specified")
        return v
    
    @validator("persona_count")
    def validate_persona_count(cls, v: int, values: Dict[str, Any]) -> int:
        """Validate persona count based on include_persona_generation.
        
        Args:
            v: Number of personas to generate
            values: Other values in the model
            
        Returns:
            Validated persona count
            
        Raises:
            ValueError: If invalid count with persona generation enabled
        """
        # Skip validation if persona generation is disabled
        if not values.get("include_persona_generation", True):
            return v
            
        if v < 1 or v > 5:
            raise ValueError("Persona count must be between 1 and 5")
        return v

class TemporalReportRequest(BaseModel):
    """Request model for temporal analysis report generation.
    
    Integrates with:
    - Temporal pattern detection
    - Trend forecasting
    - Seasonal analysis
    - Historical performance evaluation
    """
    company_id: int = Field(..., description="ID of the company to analyze")
    competitor_ids: Optional[List[int]] = Field(
        [],
        description="Optional list of competitor IDs for comparative temporal analysis"
    )
    metrics: List[str] = Field(
        ...,
        description="List of metrics to analyze over time",
        min_items=1
    )
    start_date: str = Field(
        ..., 
        description="Start date for temporal analysis (ISO format: YYYY-MM-DD)"
    )
    end_date: str = Field(
        ...,
        description="End date for temporal analysis (ISO format: YYYY-MM-DD)"
    )
    interval: str = Field(
        "month",
        description="Time interval for analysis (day, week, month, quarter, year)"
    )
    include_forecasting: bool = Field(
        True,
        description="Whether to include AI-driven forecasting in the analysis"
    )
    forecast_periods: int = Field(
        3,
        description="Number of future periods to forecast",
        ge=1,
        le=12
    )
    confidence_threshold: float = Field(
        0.7,
        description="Minimum confidence score for temporal insights",
        ge=0.0,
        le=1.0
    )
    
    @validator("metrics")
    def validate_metrics(cls, v: List[str]) -> List[str]:
        """Validate metrics list.
        
        Args:
            v: List of metrics to analyze
            
        Returns:
            Validated list of metrics
            
        Raises:
            ValueError: If invalid metric count
        """
        if len(v) < 1:
            raise ValueError("At least 1 metric must be specified for analysis")
            
        valid_metrics = {
            "revenue", "growth_rate", "market_share", "engagement", 
            "conversion", "retention", "churn", "customer_acquisition_cost",
            "lifetime_value", "average_order_value", "web_traffic"
        }
        
        invalid_metrics = set(v) - valid_metrics
        if invalid_metrics:
            raise ValueError(
                f"Invalid metrics: {', '.join(invalid_metrics)}. "
                f"Valid metrics are: {', '.join(valid_metrics)}"
            )
        return v
    
    @validator("interval")
    def validate_interval(cls, v: str) -> str:
        """Validate time interval.
        
        Args:
            v: Time interval string
            
        Returns:
            Validated time interval
            
        Raises:
            ValueError: If invalid interval specified
        """
        valid_intervals = {"day", "week", "month", "quarter", "year"}
        if v not in valid_intervals:
            raise ValueError(
                f"Invalid interval: {v}. "
                f"Valid intervals are: {', '.join(valid_intervals)}"
            )
        return v
    
    @validator("end_date")
    def validate_date_range(cls, v: str, values: Dict[str, Any]) -> str:
        """Validate that end_date is after start_date.
        
        Args:
            v: End date string
            values: Other values in the model
            
        Returns:
            Validated end date
            
        Raises:
            ValueError: If end_date is before start_date
        """
        from datetime import datetime
        
        if "start_date" not in values:
            return v
            
        try:
            start = datetime.fromisoformat(values["start_date"])
            end = datetime.fromisoformat(v)
            
            if end <= start:
                raise ValueError("End date must be after start date")
                
        except ValueError as e:
            if str(e) == "End date must be after start date":
                raise
            raise ValueError("Dates must be in ISO format: YYYY-MM-DD")
            
        return v

class SEOReportRequest(BaseModel):
    """Request model for SEO analysis report generation.
    
    Integrates with:
    - SEO performance analysis
    - Keyword optimization
    - Content gap analysis
    - Competitor SEO comparison
    """
    company_id: int = Field(..., description="ID of the company to analyze")
    domain_id: int = Field(..., description="ID of the primary domain to analyze")
    competitor_domains: Optional[List[int]] = Field(
        [],
        description="Optional list of competitor domain IDs for SEO comparison",
        max_items=5
    )
    keyword_focus: Optional[List[str]] = Field(
        None,
        description="Optional list of focus keywords for analysis",
        max_items=10
    )
    include_content_gap_analysis: bool = Field(
        True,
        description="Whether to include content gap analysis"
    )
    include_backlink_analysis: bool = Field(
        True,
        description="Whether to include backlink analysis"
    )
    include_technical_seo: bool = Field(
        True,
        description="Whether to include technical SEO analysis"
    )
    page_limit: int = Field(
        100,
        description="Maximum number of pages to analyze",
        ge=10,
        le=500
    )
    confidence_threshold: float = Field(
        0.7,
        description="Minimum confidence score for SEO insights",
        ge=0.0,
        le=1.0
    )
    
    @validator("competitor_domains")
    def validate_competitor_domains(cls, v: List[int]) -> List[int]:
        """Validate competitor domains list.
        
        Args:
            v: List of competitor domain IDs
            
        Returns:
            Validated list of domain IDs
            
        Raises:
            ValueError: If too many domains specified
        """
        if len(v) > 5:
            raise ValueError("Maximum of 5 competitor domains allowed for SEO analysis")
        return v
    
    @validator("keyword_focus")
    def validate_keywords(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate focus keywords.
        
        Args:
            v: List of focus keywords
            
        Returns:
            Validated list of keywords
            
        Raises:
            ValueError: If too many keywords specified
        """
        if v is None:
            return v
            
        if len(v) > 10:
            raise ValueError("Maximum of 10 focus keywords allowed")
            
        # Validate keyword length and format
        for keyword in v:
            if len(keyword) < 2:
                raise ValueError("Keywords must be at least 2 characters long")
            if len(keyword) > 50:
                raise ValueError("Keywords must be less than 50 characters long")
                
        return v

class ContentReportRequest(BaseModel):
    """Request model for content analysis report generation.
    
    Integrates with:
    - Content quality analysis
    - Content performance metrics
    - Content gap identification
    - Content strategy recommendations
    """
    company_id: int = Field(..., description="ID of the company to analyze")
    competitor_ids: Optional[List[int]] = Field(
        [],
        description="Optional list of competitor IDs for content comparison",
        max_items=5
    )
    content_types: List[str] = Field(
        ["blog", "webpage", "social"],
        description="Types of content to analyze"
    )
    include_sentiment_analysis: bool = Field(
        True,
        description="Whether to include sentiment analysis"
    )
    include_readability_analysis: bool = Field(
        True,
        description="Whether to include readability analysis"
    )
    include_topic_modeling: bool = Field(
        True, 
        description="Whether to include AI-driven topic modeling"
    )
    max_content_items: int = Field(
        100,
        description="Maximum number of content items to analyze",
        ge=10,
        le=500
    )
    time_range: Optional[str] = Field(
        "last_6_months",
        description="Time range for content analysis (last_month, last_3_months, last_6_months, last_year, all_time)"
    )
    confidence_threshold: float = Field(
        0.65,
        description="Minimum confidence score for content insights",
        ge=0.0,
        le=1.0
    )
    
    @validator("content_types")
    def validate_content_types(cls, v: List[str]) -> List[str]:
        """Validate content types.
        
        Args:
            v: List of content types
            
        Returns:
            Validated list of content types
            
        Raises:
            ValueError: If invalid content types specified
        """
        valid_types = {"blog", "webpage", "social", "email", "whitepaper", "case_study", "video"}
        
        if not v:
            raise ValueError("At least one content type must be specified")
            
        invalid_types = set(v) - valid_types
        if invalid_types:
            raise ValueError(
                f"Invalid content types: {', '.join(invalid_types)}. "
                f"Valid types are: {', '.join(valid_types)}"
            )
        return v
    
    @validator("time_range")
    def validate_time_range(cls, v: Optional[str]) -> Optional[str]:
        """Validate time range.
        
        Args:
            v: Time range string
            
        Returns:
            Validated time range
            
        Raises:
            ValueError: If invalid time range specified
        """
        if v is None:
            return v
            
        valid_ranges = {"last_month", "last_3_months", "last_6_months", "last_year", "all_time"}
        if v not in valid_ranges:
            raise ValueError(
                f"Invalid time range: {v}. "
                f"Valid ranges are: {', '.join(valid_ranges)}"
            )
        return v

class SentimentReportRequest(BaseModel):
    """Request model for sentiment analysis report generation.
    
    Integrates with:
    - LLM-based sentiment analysis
    - Emotional tone assessment
    - Brand perception analysis
    - Competitive sentiment comparison
    """
    company_id: int = Field(..., description="ID of the company to analyze")
    content_source_ids: List[int] = Field(
        ...,
        description="List of content source IDs to analyze for sentiment",
        min_items=1
    )
    competitor_ids: Optional[List[int]] = Field(
        [],
        description="Optional list of competitor IDs for sentiment comparison",
        max_items=5
    )
    include_emotional_tone: bool = Field(
        True,
        description="Whether to include emotional tone analysis"
    )
    include_brand_perception: bool = Field(
        True,
        description="Whether to include brand perception analysis"
    )
    time_period: str = Field(
        "last_3_months",
        description="Time period for sentiment analysis (last_month, last_3_months, last_6_months, last_year, all_time)"
    )
    languages: Optional[List[str]] = Field(
        ["en"],
        description="List of language codes to analyze (ISO 639-1 codes)"
    )
    granularity: str = Field(
        "weekly",
        description="Granularity of sentiment trends (daily, weekly, monthly, quarterly)"
    )
    confidence_threshold: float = Field(
        0.7,
        description="Minimum confidence score for sentiment insights",
        ge=0.0,
        le=1.0
    )
    
    @validator("content_source_ids")
    def validate_content_sources(cls, v: List[int]) -> List[int]:
        """Validate content sources.
        
        Args:
            v: List of content source IDs
            
        Returns:
            Validated list of content source IDs
            
        Raises:
            ValueError: If no content sources specified
        """
        if not v:
            raise ValueError("At least one content source must be specified")
        return v
    
    @validator("time_period")
    def validate_time_period(cls, v: str) -> str:
        """Validate time period.
        
        Args:
            v: Time period string
            
        Returns:
            Validated time period
            
        Raises:
            ValueError: If invalid time period specified
        """
        valid_periods = {"last_month", "last_3_months", "last_6_months", "last_year", "all_time"}
        if v not in valid_periods:
            raise ValueError(
                f"Invalid time period: {v}. "
                f"Valid periods are: {', '.join(valid_periods)}"
            )
        return v
    
    @validator("languages")
    def validate_languages(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate language codes.
        
        Args:
            v: List of language codes
            
        Returns:
            Validated list of language codes
            
        Raises:
            ValueError: If invalid language codes specified
        """
        if not v:
            return ["en"]
            
        valid_languages = {"en", "fr", "ja", "es", "de", "zh", "ru", "pt", "it", "nl"}
        invalid_languages = set(v) - valid_languages
        if invalid_languages:
            raise ValueError(
                f"Invalid language codes: {', '.join(invalid_languages)}. "
                f"Valid codes are: {', '.join(valid_languages)}"
            )
        return v
    
    @validator("granularity")
    def validate_granularity(cls, v: str) -> str:
        """Validate granularity.
        
        Args:
            v: Granularity string
            
        Returns:
            Validated granularity
            
        Raises:
            ValueError: If invalid granularity specified
        """
        valid_granularities = {"daily", "weekly", "monthly", "quarterly"}
        if v not in valid_granularities:
            raise ValueError(
                f"Invalid granularity: {v}. "
                f"Valid granularities are: {', '.join(valid_granularities)}"
            )
        return v

class CancellationRequest(BaseModel):
    """Request model for cancelling report generation."""
    report_id: int = Field(..., description="ID of the report to cancel")
    user_id: int = Field(..., description="ID of the user requesting cancellation")
    reason: Optional[str] = Field(
        None,
        description="Optional reason for cancellation"
    )
