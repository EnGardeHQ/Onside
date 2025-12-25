"""Audience Data Service Module.

This module provides audience data retrieval and processing functionality.
Following Semantic Seed coding standards with proper error handling,
logging, and type hints.
"""
import logging
import random
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta

from src.repositories.company_repository import CompanyRepository


class AudienceDataService:
    """Service for retrieving and processing audience data."""

    def __init__(self, company_repository: CompanyRepository):
        """Initialize the audience data service.
        
        Args:
            company_repository: Repository for company data
        """
        self.company_repo = company_repository
        self.logger = logging.getLogger(__name__)
        
        # Define demographic segments
        self.demographic_segments = {
            "age_range": ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
            "gender": ["male", "female", "non_binary", "other"],
            "location": ["urban", "suburban", "rural"],
            "income_level": ["low", "medium", "high"],
            "education": ["high_school", "college", "graduate", "post_graduate"],
            "interests": ["real_estate", "investment", "commercial_property", "residential_property", 
                         "property_management", "sustainability", "technology", "finance"]
        }
    
    async def get_audience_data(
        self,
        company_id: int,
        segment_id: Optional[int],
        timeframe: str,
        demographic_filters: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], float]:
        """Get audience data for specified company, segment, and timeframe.
        
        Args:
            company_id: ID of the company
            segment_id: Optional specific segment to analyze
            timeframe: Time range for analysis (e.g., "last_quarter")
            demographic_filters: Filters for demographic analysis
            
        Returns:
            Tuple of (audience_data, quality_score)
        """
        try:
            # Get company information
            company = await self.company_repo.get_by_id(company_id)
            if not company:
                self.logger.error(f"Company with ID {company_id} not found")
                return {}, 0.5
            
            # Parse timeframe
            date_range = self._parse_timeframe(timeframe)
            if not date_range:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return {}, 0.5
            
            start_date, end_date = date_range
            
            # Apply demographic filters
            filtered_segments = self._apply_demographic_filters(demographic_filters)
            
            # Generate audience data
            audience_data = {
                "company": {
                    "id": company.id,
                    "name": company.name,
                    "industry": company.industry
                },
                "timeframe": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "description": timeframe
                },
                "segment_id": segment_id,
                "demographics": self._generate_demographic_data(filtered_segments),
                "behavior": self._generate_behavior_data(filtered_segments),
                "engagement": self._generate_engagement_data(start_date, end_date),
                "content_preferences": self._generate_content_preferences(filtered_segments)
            }
            
            # Calculate data quality score based on completeness and recency
            quality_score = self._calculate_quality_score(audience_data)
            
            return audience_data, quality_score
            
        except Exception as e:
            self.logger.error(f"Error retrieving audience data: {str(e)}")
            return {}, 0.5
    
    def _parse_timeframe(self, timeframe: str) -> Optional[Tuple[datetime, datetime]]:
        """Parse timeframe string into start and end dates.
        
        Args:
            timeframe: Time range description (e.g., "last_quarter")
            
        Returns:
            Tuple of (start_date, end_date) or None if invalid
        """
        now = datetime.utcnow()
        
        if timeframe == "last_month":
            start_date = now - timedelta(days=30)
            end_date = now
        elif timeframe == "last_quarter":
            start_date = now - timedelta(days=90)
            end_date = now
        elif timeframe == "last_year":
            start_date = now - timedelta(days=365)
            end_date = now
        elif timeframe == "ytd":  # Year to date
            start_date = datetime(now.year, 1, 1)
            end_date = now
        else:
            return None
        
        return start_date, end_date
    
    def _apply_demographic_filters(
        self, 
        filters: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Apply demographic filters to audience segments.
        
        Args:
            filters: Demographic filters to apply
            
        Returns:
            Filtered demographic segments
        """
        filtered_segments = self.demographic_segments.copy()
        
        for key, values in filters.items():
            if key in filtered_segments and values:
                if isinstance(values, list):
                    # Keep only the specified values in the segment
                    filtered_segments[key] = [v for v in filtered_segments[key] if v in values]
                else:
                    # Single value filter
                    filtered_segments[key] = [v for v in filtered_segments[key] if v == values]
        
        return filtered_segments
    
    def _generate_demographic_data(
        self, 
        segments: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Generate demographic data for audience segments.
        
        Args:
            segments: Demographic segments to include
            
        Returns:
            Generated demographic data
        """
        demographic_data = {}
        
        for segment_type, segment_values in segments.items():
            if not segment_values:
                continue
                
            # Generate distribution data
            distribution = {}
            remaining = 100.0
            
            for i, value in enumerate(segment_values):
                # Last segment gets the remainder to ensure sum is 100%
                if i == len(segment_values) - 1:
                    distribution[value] = round(remaining, 1)
                else:
                    # Generate a random percentage
                    percentage = round(random.uniform(5.0, remaining / (len(segment_values) - i)), 1)
                    distribution[value] = percentage
                    remaining -= percentage
            
            demographic_data[segment_type] = {
                "distribution": distribution,
                "primary": max(distribution.items(), key=lambda x: x[1])[0],
                "secondary": sorted(distribution.items(), key=lambda x: x[1], reverse=True)[1][0] if len(distribution) > 1 else None
            }
        
        return demographic_data
    
    def _generate_behavior_data(
        self, 
        segments: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Generate behavior data for audience segments.
        
        Args:
            segments: Demographic segments to include
            
        Returns:
            Generated behavior data
        """
        # Define possible behaviors
        behaviors = {
            "visit_frequency": ["daily", "weekly", "monthly", "quarterly", "rarely"],
            "session_duration": ["short", "medium", "long"],
            "conversion_path": ["direct", "search", "referral", "social", "email"],
            "device_usage": ["desktop", "mobile", "tablet"]
        }
        
        behavior_data = {}
        
        for behavior_type, behavior_values in behaviors.items():
            # Generate distribution data
            distribution = {}
            remaining = 100.0
            
            for i, value in enumerate(behavior_values):
                # Last behavior gets the remainder to ensure sum is 100%
                if i == len(behavior_values) - 1:
                    distribution[value] = round(remaining, 1)
                else:
                    # Generate a random percentage
                    percentage = round(random.uniform(5.0, remaining / (len(behavior_values) - i)), 1)
                    distribution[value] = percentage
                    remaining -= percentage
            
            behavior_data[behavior_type] = {
                "distribution": distribution,
                "primary": max(distribution.items(), key=lambda x: x[1])[0]
            }
        
        # Add user journey data
        behavior_data["user_journey"] = {
            "average_touchpoints": round(random.uniform(3.0, 8.0), 1),
            "common_paths": [
                ["landing_page", "product_page", "contact_form"],
                ["search", "blog", "service_page", "contact_form"],
                ["social_media", "landing_page", "case_study", "contact_form"]
            ],
            "conversion_rate": round(random.uniform(1.5, 5.0), 1)
        }
        
        return behavior_data
    
    def _generate_engagement_data(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate engagement data for the specified time period.
        
        Args:
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            Generated engagement data
        """
        # Generate time series data
        days = (end_date - start_date).days
        data_points = max(5, days // 7)  # Weekly data points
        
        metrics = ["page_views", "time_on_site", "bounce_rate", "conversion_rate"]
        
        time_series = {}
        for metric in metrics:
            # Set base values and trends
            if metric == "page_views":
                base_value = random.uniform(1000, 5000)
                trend_factor = random.uniform(-0.05, 0.15)
            elif metric == "time_on_site":
                base_value = random.uniform(60, 180)  # seconds
                trend_factor = random.uniform(-0.05, 0.1)
            elif metric == "bounce_rate":
                base_value = random.uniform(30, 60)  # percentage
                trend_factor = random.uniform(-0.1, 0.05)  # negative trend is good
            else:  # conversion_rate
                base_value = random.uniform(1, 5)  # percentage
                trend_factor = random.uniform(-0.05, 0.1)
            
            series = []
            for i in range(data_points):
                point_date = start_date + timedelta(days=(i * days // data_points))
                progress = i / (data_points - 1) if data_points > 1 else 0
                
                # Add trend and some noise
                value = base_value * (1 + trend_factor * progress + random.uniform(-0.05, 0.05))
                
                series.append({
                    "date": point_date.isoformat(),
                    "value": round(value, 2),
                    "confidence": round(random.uniform(0.7, 0.95), 2)
                })
            
            time_series[metric] = series
        
        # Generate content engagement data
        content_engagement = {
            "most_engaged_pages": [
                {"path": "/services/commercial", "engagement_score": round(random.uniform(7.0, 9.5), 1)},
                {"path": "/case-studies", "engagement_score": round(random.uniform(6.5, 9.0), 1)},
                {"path": "/about", "engagement_score": round(random.uniform(6.0, 8.5), 1)},
                {"path": "/blog/market-trends", "engagement_score": round(random.uniform(5.5, 8.0), 1)}
            ],
            "least_engaged_pages": [
                {"path": "/terms", "engagement_score": round(random.uniform(1.0, 3.0), 1)},
                {"path": "/privacy", "engagement_score": round(random.uniform(1.5, 3.5), 1)},
                {"path": "/careers/benefits", "engagement_score": round(random.uniform(2.0, 4.0), 1)}
            ]
        }
        
        return {
            "metrics": time_series,
            "content": content_engagement,
            "channels": {
                "organic_search": round(random.uniform(25.0, 40.0), 1),
                "direct": round(random.uniform(20.0, 35.0), 1),
                "referral": round(random.uniform(10.0, 20.0), 1),
                "social": round(random.uniform(5.0, 15.0), 1),
                "email": round(random.uniform(5.0, 15.0), 1),
                "paid": round(random.uniform(5.0, 15.0), 1)
            }
        }
    
    def _generate_content_preferences(
        self, 
        segments: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Generate content preference data for audience segments.
        
        Args:
            segments: Demographic segments to include
            
        Returns:
            Generated content preference data
        """
        # Define content types and formats
        content_types = ["market_reports", "case_studies", "how_to_guides", "industry_news", 
                         "property_listings", "company_updates", "thought_leadership"]
        
        content_formats = ["blog_posts", "videos", "infographics", "webinars", 
                          "podcasts", "newsletters", "social_media_posts"]
        
        # Generate preferences for content types
        type_preferences = {}
        remaining = 100.0
        
        for i, content_type in enumerate(content_types):
            if i == len(content_types) - 1:
                type_preferences[content_type] = round(remaining, 1)
            else:
                percentage = round(random.uniform(5.0, remaining / (len(content_types) - i)), 1)
                type_preferences[content_type] = percentage
                remaining -= percentage
        
        # Generate preferences for content formats
        format_preferences = {}
        remaining = 100.0
        
        for i, content_format in enumerate(content_formats):
            if i == len(content_formats) - 1:
                format_preferences[content_format] = round(remaining, 1)
            else:
                percentage = round(random.uniform(5.0, remaining / (len(content_formats) - i)), 1)
                format_preferences[content_format] = percentage
                remaining -= percentage
        
        # Generate topic interests based on demographic segments
        topics = []
        
        # Add topics based on interests
        if "interests" in segments:
            for interest in segments["interests"]:
                if interest == "real_estate":
                    topics.extend(["property_market_trends", "real_estate_investment"])
                elif interest == "investment":
                    topics.extend(["investment_strategies", "market_analysis"])
                elif interest == "commercial_property":
                    topics.extend(["office_space_trends", "retail_property_market"])
                elif interest == "residential_property":
                    topics.extend(["housing_market_trends", "home_buying_guides"])
                elif interest == "property_management":
                    topics.extend(["property_management_best_practices", "tenant_relations"])
                elif interest == "sustainability":
                    topics.extend(["green_buildings", "sustainable_real_estate"])
                elif interest == "technology":
                    topics.extend(["proptech_innovations", "smart_buildings"])
                elif interest == "finance":
                    topics.extend(["real_estate_financing", "mortgage_trends"])
        
        # Ensure we have at least some topics
        if not topics:
            topics = ["property_market_trends", "real_estate_investment", "market_analysis"]
        
        # Remove duplicates
        topics = list(set(topics))
        
        return {
            "content_types": type_preferences,
            "content_formats": format_preferences,
            "top_topics": topics,
            "preferred_channels": {
                "website": round(random.uniform(20.0, 40.0), 1),
                "email": round(random.uniform(15.0, 30.0), 1),
                "linkedin": round(random.uniform(10.0, 25.0), 1),
                "twitter": round(random.uniform(5.0, 15.0), 1),
                "facebook": round(random.uniform(5.0, 15.0), 1),
                "youtube": round(random.uniform(5.0, 15.0), 1)
            }
        }
    
    def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """Calculate data quality score based on completeness and recency.
        
        Args:
            data: Audience data
            
        Returns:
            Quality score between 0 and 1
        """
        # Check completeness
        completeness = 0.0
        required_sections = ["demographics", "behavior", "engagement", "content_preferences"]
        
        for section in required_sections:
            if section in data and data[section]:
                completeness += 0.25
        
        # Check recency
        recency = 0.0
        if "timeframe" in data and "end_date" in data["timeframe"]:
            try:
                end_date = datetime.fromisoformat(data["timeframe"]["end_date"])
                days_ago = (datetime.utcnow() - end_date).days
                
                if days_ago <= 30:
                    recency = 1.0
                elif days_ago <= 90:
                    recency = 0.8
                elif days_ago <= 180:
                    recency = 0.6
                elif days_ago <= 365:
                    recency = 0.4
                else:
                    recency = 0.2
            except:
                recency = 0.5
        
        # Calculate final score
        return (completeness * 0.6) + (recency * 0.4)
