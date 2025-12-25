"""
Google Analytics Service

This module provides functionality to interact with the Google Analytics Data API (GA4)
to fetch website traffic and user engagement metrics using OAuth2 authentication.
"""
import logging
import json
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
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
from google.auth.transport.requests import Request
from ..auth.google_oauth import GoogleOAuth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleAnalyticsService:
    """Service for interacting with Google Analytics Data API (GA4) using OAuth2."""
    
    def __init__(self, property_id: str, oauth_credentials: Optional[Dict[str, Any]] = None):
        """Initialize the Google Analytics service with OAuth2 credentials.
        
        Args:
            property_id: The GA4 property ID (format: properties/XXXXXXXXXX)
            oauth_credentials: Dictionary containing OAuth2 credentials including:
                             - token: Access token
                             - refresh_token: Refresh token
                             - token_uri: Token endpoint
                             - client_id: OAuth2 client ID
                             - client_secret: OAuth2 client secret
                             - scopes: List of OAuth2 scopes
        """
        self.property_id = property_id
        self.oauth_credentials = oauth_credentials
        self.client = self._initialize_client()
    
    def _initialize_client(self) -> BetaAnalyticsDataClient:
        """Initialize and return the GA4 client with OAuth2 credentials."""
        if not self.oauth_credentials:
            raise ValueError("OAuth2 credentials are required")
            
        try:
            # Create credentials from the provided OAuth2 token info
            credentials = Credentials(
                token=self.oauth_credentials.get('token'),
                refresh_token=self.oauth_credentials.get('refresh_token'),
                token_uri=self.oauth_credentials.get('token_uri', 'https://oauth2.googleapis.com/token'),
                client_id=self.oauth_credentials.get('client_id'),
                client_secret=self.oauth_credentials.get('client_secret'),
                scopes=self.oauth_credentials.get('scopes', ['https://www.googleapis.com/auth/analytics.readonly'])
            )
            
            # Refresh token if needed
            if not credentials.valid:
                credentials.refresh(Request())
                
            return BetaAnalyticsDataClient(credentials=credentials)
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Analytics client: {str(e)}")
            raise
    
    async def get_metrics(
        self,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        dimensions: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
        dimension_filters: Optional[Dict[str, str]] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Fetch metrics from Google Analytics.
        
        Args:
            start_date: Start date in YYYY-MM-DD format or datetime object
            end_date: End date in YYYY-MM-DD format or datetime object
            dimensions: List of dimension names (e.g., ['pagePath', 'country'])
            metrics: List of metric names (e.g., ['sessions', 'users'])
            dimension_filters: Dictionary of dimension filters (e.g., {'country': 'United States'})
            limit: Maximum number of rows to return
            
        Returns:
            List of dictionaries containing the requested metrics
        """
        try:
            # Set default date range if not provided
            end_date = end_date or datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)
                
            # Convert string dates to datetime objects if needed
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                
            # Format dates for API
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            # Set default dimensions and metrics if not provided
            if not dimensions:
                dimensions = ['pagePath', 'country', 'deviceCategory']
                
            if not metrics:
                metrics = ['sessions', 'users', 'bounceRate', 'avgSessionDuration']
            
            # Build the request
            request = RunReportRequest(
                property=self.property_id,
                date_ranges=[DateRange(start_date=start_date_str, end_date=end_date_str)],
                dimensions=[Dimension(name=dim) for dim in dimensions],
                metrics=[Metric(name=metric) for metric in metrics],
                limit=limit
            )
            
            # Add dimension filters if provided
            if dimension_filters:
                filter_expressions = []
                for dim, value in dimension_filters.items():
                    filter_expressions.append(
                        FilterExpression(
                            filter=Filter(
                                field_name=dim,
                                string_filter=Filter.StringFilter(value=value, match_type=Filter.StringFilter.MatchType.EXACT)
                            )
                        )
                    )
                
                # Combine filters with AND logic
                request.dimension_filter = FilterExpression(
                    and_group=FilterExpressionList(expressions=filter_expressions)
                )
            
            # Make the API request
            response = await self.client.run_report(request)
            
            # Process the response
            results = []
            
            for row in response.rows:
                result = {}
                
                # Add dimension values
                for i, dim in enumerate(dimensions):
                    if i < len(row.dimension_values):
                        result[dim] = row.dimension_values[i].value
                
                # Add metric values
                for i, metric in enumerate(metrics):
                    if i < len(row.metric_values):
                        # Convert to appropriate type
                        value = row.metric_values[i].value
                        if metric in ['bounceRate', 'avgSessionDuration']:
                            result[metric] = float(value) if value else 0.0
                        else:
                            result[metric] = int(float(value)) if value else 0
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching Google Analytics data: {str(e)}")
            raise
    
    async def get_site_metrics(
        self,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None
    ) -> Dict[str, Any]:
        """Get aggregated site metrics for the specified time period.
        
        Args:
            start_date: Start date in YYYY-MM-DD format or datetime object
            end_date: End date in YYYY-MM-DD format or datetime object
            
        Returns:
            Dictionary containing aggregated metrics
        """
        try:
            # Get metrics for the site
            metrics = await self.get_metrics(
                start_date=start_date,
                end_date=end_date,
                metrics=[
                    'sessions', 'users', 'newUsers', 'bounceRate', 
                    'avgSessionDuration', 'pageviewsPerSession', 'goalCompletionsAll'
                ]
            )
            
            if not metrics:
                return {}
                
            # Return the first (and only) row of metrics
            row = metrics[0]
            
            return {
                'sessions': row.get('sessions', 0),
                'users': row.get('users', 0),
                'new_users': row.get('newUsers', 0),
                'bounce_rate': row.get('bounceRate', 0.0),
                'avg_session_duration': row.get('avgSessionDuration', 0.0),
                'pages_per_session': row.get('pageviewsPerSession', 0.0),
                'goal_completions': row.get('goalCompletionsAll', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting site metrics: {str(e)}")
            raise
    
    async def get_engagement_metrics(
        self,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None
    ) -> Dict[str, Any]:
        """Get user engagement metrics.
        
        Args:
            start_date: Start date in YYYY-MM-DD format or datetime object
            end_date: End date in YYYY-MM-DD format or datetime object
            
        Returns:
            Dictionary containing engagement metrics
        """
        try:
            # Convert string dates to datetime objects if needed
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                
            # Format dates for the period
            period = {
                'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
                'end_date': end_date.strftime('%Y-%m-%d') if end_date else None
            }
            
            # Get user engagement metrics
            metrics = await self.get_metrics(
                start_date=start_date,
                end_date=end_date,
                metrics=[
                    'sessions', 'users', 'bounceRate', 'avgSessionDuration',
                    'pageviewsPerSession', 'screenPageViews'
                ]
            )
            
            if not metrics:
                return {'period': period}
                
            # Get the first (and only) row of metrics
            row = metrics[0]
            
            return {
                'sessions': row.get('sessions', 0),
                'users': row.get('users', 0),
                'bounce_rate': row.get('bounceRate', 0.0),
                'avg_session_duration': row.get('avgSessionDuration', 0.0),
                'pages_per_session': row.get('pageviewsPerSession', 0.0),
                'pageviews': row.get('screenPageViews', 0),
                'period': period
            }
            
        except Exception as e:
            logger.error(f"Error getting engagement metrics: {str(e)}")
            return {}
    
    async def get_page_metrics(
        self,
        page_path: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None
    ) -> Dict[str, Any]:
        """Get metrics for a specific page.
        
        Args:
            page_path: The path of the page (e.g., '/about')
            start_date: Start date in YYYY-MM-DD format or datetime object
            end_date: End date in YYYY-MM-DD format or datetime object
            
        Returns:
            Dictionary containing page metrics
        """
        try:
            # Get metrics for the specific page
            metrics = await self.get_metrics(
                start_date=start_date,
                end_date=end_date,
                dimensions=['pagePath', 'pageTitle'],
                metrics=[
                    'sessions', 'users', 'bounceRate', 'avgSessionDuration',
                    'pageviews', 'entrances', 'exits', 'pageValue'
                ],
                dimension_filters={'pagePath': page_path}
            )
            
            if not metrics:
                return {}
                
            # Return the first matching page
            row = metrics[0]
            
            return {
                'page_path': row.get('pagePath', ''),
                'page_title': row.get('pageTitle', ''),
                'sessions': row.get('sessions', 0),
                'users': row.get('users', 0),
                'bounce_rate': row.get('bounceRate', 0.0),
                'avg_session_duration': row.get('avgSessionDuration', 0.0),
                'pageviews': row.get('pageviews', 0),
                'entrances': row.get('entrances', 0),
                'exits': row.get('exits', 0),
                'page_value': row.get('pageValue', 0.0),
                'period': {
                    'start_date': start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else start_date,
                    'end_date': end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else end_date
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting page metrics: {str(e)}")
            return {}
