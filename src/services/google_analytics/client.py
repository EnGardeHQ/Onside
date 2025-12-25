"""Google Analytics API Client.

This module provides a client for interacting with the Google Analytics API.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Dimension,
    Metric,
    FilterExpression,
    Filter,
    FilterExpressionList,
)
from google.oauth2.credentials import Credentials

from .oauth2 import GoogleAnalyticsOAuth2Client

logger = logging.getLogger(__name__)

class GoogleAnalyticsClient:
    """Client for interacting with Google Analytics API."""
    
    def __init__(self, user_id: int, property_id: str):
        """Initialize the Google Analytics client.
        
        Args:
            user_id: The ID of the user
            property_id: The Google Analytics 4 property ID (format: properties/XXXXXX)
        """
        self.user_id = user_id
        self.property_id = property_id
        self.oauth_client = GoogleAnalyticsOAuth2Client(user_id=user_id)
        self.client = None
        
    def _get_client(self) -> BetaAnalyticsDataClient:
        """Get an authenticated API client.
        
        Returns:
            BetaAnalyticsDataClient: Authenticated client
            
        Raises:
            ValueError: If authentication fails
        """
        if self.client:
            return self.client
            
        credentials = self.oauth_client.get_credentials()
        if not credentials:
            raise ValueError("Not authenticated with Google Analytics")
            
        self.client = BetaAnalyticsDataClient(credentials=credentials)
        return self.client
    
    def get_page_views(
        self,
        start_date: str,
        end_date: str,
        dimensions: Optional[List[str]] = None,
        dimension_filter: Optional[Dict[str, str]] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get page view data from Google Analytics.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            dimensions: List of dimensions to include in the report
            dimension_filter: Dictionary of dimension filters (dimension: value)
            limit: Maximum number of rows to return
            
        Returns:
            List of dictionaries containing the report data
        """
        # Set default dimensions if none provided
        if not dimensions:
            dimensions = ['pagePath', 'pageTitle']
            
        # Create the request
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name=dim) for dim in dimensions],
            metrics=[
                Metric(name='sessions'),
                Metric(name='screenPageViews'),
                Metric(name='averageSessionDuration'),
                Metric(name='bounceRate'),
            ],
            limit=limit
        )
        
        # Add dimension filters if provided
        if dimension_filter:
            filter_expressions = []
            for dim, value in dimension_filter.items():
                filter_expressions.append(
                    FilterExpression(
                        filter=Filter(
                            field_name=dim,
                            string_filter=Filter.StringFilter(
                                match_type=Filter.StringFilter.MatchType.EXACT,
                                value=value
                            )
                        )
                    )
                )
            
            if len(filter_expressions) > 1:
                request.dimension_filter = FilterExpression(
                    and_group=FilterExpressionList(expressions=filter_expressions)
                )
            else:
                request.dimension_filter = filter_expressions[0]
        
        try:
            # Make the API request
            client = self._get_client()
            response = client.run_report(request)
            
            # Process the response
            results = []
            
            # Get dimension and metric headers
            dimension_headers = [header.name for header in response.dimension_headers]
            metric_headers = [header.name for header in response.metric_headers]
            
            # Process each row
            for row in response.rows:
                result = {}
                
                # Add dimensions
                for i, value in enumerate(row.dimension_values):
                    result[dimension_headers[i]] = value.value
                
                # Add metrics
                for i, value in enumerate(row.metric_values):
                    result[metric_headers[i]] = value.value
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching Google Analytics data: {str(e)}")
            raise
    
    def get_site_metrics(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Get overall site metrics.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary containing site metrics
        """
        try:
            # Create the request for overall metrics
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                metrics=[
                    Metric(name='sessions'),
                    Metric(name='users'),
                    Metric(name='screenPageViews'),
                    Metric(name='averageSessionDuration'),
                    Metric(name='bounceRate'),
                    Metric(name='engagementRate'),
                ]
            )
            
            # Make the API request
            client = self._get_client()
            response = client.run_report(request)
            
            # Extract metrics from the response
            if not response.rows:
                return {}
                
            row = response.rows[0]
            metric_values = row.metric_values
            
            return {
                'sessions': int(metric_values[0].value) if metric_values[0].value else 0,
                'users': int(metric_values[1].value) if metric_values[1].value else 0,
                'page_views': int(metric_values[2].value) if metric_values[2].value else 0,
                'avg_session_duration': float(metric_values[3].value) if metric_values[3].value else 0,
                'bounce_rate': float(metric_values[4].value) if metric_values[4].value else 0,
                'engagement_rate': float(metric_values[5].value) if metric_values[5].value else 0,
            }
            
        except Exception as e:
            logger.error(f"Error fetching site metrics from Google Analytics: {str(e)}")
            raise
    
    def get_top_pages(
        self,
        start_date: str,
        end_date: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top pages by page views.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            limit: Number of top pages to return
            
        Returns:
            List of dictionaries containing page data
        """
        return self.get_page_views(
            start_date=start_date,
            end_date=end_date,
            dimensions=['pagePath', 'pageTitle'],
            limit=limit
        )
    
    def get_traffic_sources(
        self,
        start_date: str,
        end_date: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get traffic sources.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            limit: Number of traffic sources to return
            
        Returns:
            List of dictionaries containing traffic source data
        """
        try:
            # Create the request
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimensions=[
                    Dimension(name='sessionSource'),
                    Dimension(name='sessionMedium'),
                ],
                metrics=[
                    Metric(name='sessions'),
                    Metric(name='users'),
                    Metric(name='screenPageViews'),
                    Metric(name='averageSessionDuration'),
                    Metric(name='bounceRate'),
                ],
                limit=limit
            )
            
            # Make the API request
            client = self._get_client()
            response = client.run_report(request)
            
            # Process the response
            results = []
            
            for row in response.rows:
                result = {
                    'source': row.dimension_values[0].value,
                    'medium': row.dimension_values[1].value,
                    'sessions': int(row.metric_values[0].value) if row.metric_values[0].value else 0,
                    'users': int(row.metric_values[1].value) if row.metric_values[1].value else 0,
                    'page_views': int(row.metric_values[2].value) if row.metric_values[2].value else 0,
                    'avg_session_duration': float(row.metric_values[3].value) if row.metric_values[3].value else 0,
                    'bounce_rate': float(row.metric_values[4].value) if row.metric_values[4].value else 0,
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching traffic sources from Google Analytics: {str(e)}")
            raise
