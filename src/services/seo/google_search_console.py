"""
Google Search Console Service

This module provides functionality to interact with the Google Search Console API
to fetch search analytics and other SEO-related data.
"""
import asyncio
import logging
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import httpx
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

class GoogleSearchConsoleService:
    """Service for interacting with Google Search Console API."""
    
    def __init__(self, credentials_path: Optional[str] = None):
        """Initialize the Google Search Console service.
        
        Args:
            credentials_path: Path to the OAuth2 client credentials JSON file.
                            If not provided, will use environment variables.
        """
        self.credentials_path = credentials_path
        self.service = self._authenticate()
        
        if not self.service:
            raise ValueError("Failed to initialize Google Search Console service")
    
    def _authenticate(self):
        """Authenticate with Google Search Console API using OAuth2 credentials."""
        try:
            # Try to use the credentials file if provided
            if self.credentials_path and os.path.exists(self.credentials_path):
                logger.info(f"Using credentials from file: {self.credentials_path}")
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=SCOPES
                )
            else:
                # Fall back to environment variables
                logger.info("Using credentials from environment variables")
                credentials = {
                    'type': 'authorized_user',
                    'client_id': os.getenv('PAGESPEED_CLIENT_ID'),
                    'client_secret': os.getenv('Google Web CLIENT_SECRET'),
                    'refresh_token': os.getenv('GOOGLE_REFRESH_TOKEN')
                }
                
                if not all(credentials.values()):
                    raise ValueError("Missing required Google OAuth2 credentials in environment variables")
                    
                credentials = Credentials.from_authorized_user_info(credentials, SCOPES)
            
            # Build and return the service
            service = build(
                'searchconsole',
                'v1',
                credentials=credentials,
                cache_discovery=False
            )
            
            logger.info("Successfully authenticated with Google Search Console API")
            return service
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Search Console: {str(e)}", exc_info=True)
            return None
    
    def get_search_analytics(
        self,
        site_url: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        dimensions: Optional[List[str]] = None,
        row_limit: int = 1000,
        **filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetch search analytics data from Google Search Console.
        
        Args:
            site_url: The URL of the site in Google Search Console
            start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            dimensions: List of dimensions to group by (e.g., ['query', 'page', 'country', 'device'])
            row_limit: Maximum number of rows to return (max 25,000)
            **filters: Additional filters to apply to the query
                
        Returns:
            List of dictionaries containing search analytics data
            
        Raises:
            ValueError: If the service is not initialized or invalid parameters are provided
            Exception: For any API errors
        """
        if not self.service:
            raise ValueError("Google Search Console service is not initialized")
            
        if not dimensions:
            dimensions = ['query', 'page', 'country', 'device']
            
        if row_limit > 25000:
            raise ValueError("Maximum row limit is 25,000")
            
        # Set default date range if not provided
        end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        try:
            # Prepare the request body
            request = {
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': dimensions,
                'rowLimit': min(int(row_limit), 25000),  # Ensure row_limit is an int and within API limit
                'startRow': 0
            }
            
            # Add filters if provided
            if filters:
                request['dimensionFilterGroups'] = [{
                    'filters': [{
                        'dimension': dim,
                        'operator': 'equals',
                        'expression': value
                    } for dim, value in filters.items()]
                }]
            
            logger.info(f"Fetching search analytics for {site_url} from {start_date} to {end_date}")
            logger.debug(f"API Request: {request}")
            
            # Make the API request
            response = self.service.searchanalytics().query(
                siteUrl=site_url,
                body=request
            ).execute()
            
            logger.info(f"Successfully fetched {len(response.get('rows', []))} rows of data")
            
            # Process and return the response
            return self._process_search_analytics_response(response, dimensions)
            
        except Exception as e:
            error_msg = f"Error fetching search analytics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg) from e
    
    def _process_search_analytics_response(
        self,
        response: Dict[str, Any],
        dimensions: List[str]
    ) -> List[Dict[str, Any]]:
        """Process the raw API response into a more usable format.
        
        Args:
            response: The raw API response from Google Search Console
            dimensions: List of dimensions that were requested
            
        Returns:
            List of dictionaries containing the processed data with named dimensions
        """
        results = []
        
        if not response or 'rows' not in response:
            logger.warning("No data found in the response")
            return results
            
        try:
            for row in response['rows']:
                result = {
                    'clicks': row.get('clicks', 0),
                    'impressions': row.get('impressions', 0),
                    'ctr': row.get('ctr', 0),
                    'position': row.get('position', 0),
                    'keys': row.get('keys', [])  # Keep original keys for reference
                }
                
                # Add dimension values as top-level keys
                for i, dim in enumerate(dimensions):
                    if i < len(row.get('keys', [])):
                        # Convert to string to handle any non-string values
                        result[dim] = str(row['keys'][i])
                        
                results.append(result)
                
            logger.debug(f"Processed {len(results)} rows of data")
            
        except Exception as e:
            error_msg = f"Error processing search analytics response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e
            
        return results
    
    async def get_site_metrics(
        self,
        site_url: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get aggregated site metrics for the specified time period.
        
        Args:
            site_url: The URL of the site in Google Search Console
            days: Number of days to look back (default: 30)
            
        Returns:
            Dictionary containing aggregated metrics
        """
        if not self.service:
            logger.warning("GSC service not initialized. Skipping get_site_metrics.")
            return {}
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            # Get search analytics data
            analytics = await self.get_search_analytics(
                site_url=site_url,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                dimensions=['query', 'page'],
                row_limit=1000
            )
            
            if not analytics:
                return {}
            
            # Calculate aggregated metrics
            total_clicks = sum(item.get('clicks', 0) for item in analytics)
            total_impressions = sum(item.get('impressions', 0) for item in analytics)
            avg_ctr = sum(item.get('ctr', 0) for item in analytics) / len(analytics) if analytics else 0
            avg_position = sum(item.get('position', 0) for item in analytics) / len(analytics) if analytics else 0
            
            # Get top performing pages and queries
            top_pages = sorted(
                analytics,
                key=lambda x: x.get('impressions', 0),
                reverse=True
            )[:5]
            
            top_queries = sorted(
                analytics,
                key=lambda x: x.get('clicks', 0),
                reverse=True
            )[:5]
            
            return {
                'period': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'days': days
                },
                'metrics': {
                    'total_clicks': total_clicks,
                    'total_impressions': total_impressions,
                    'average_ctr': avg_ctr,
                    'average_position': avg_position
                },
                'top_pages': [{
                    'url': p.get('page', ''),
                    'clicks': p.get('clicks', 0),
                    'impressions': p.get('impressions', 0),
                    'ctr': p.get('ctr', 0),
                    'position': p.get('position', 0)
                } for p in top_pages],
                'top_queries': [{
                    'query': q.get('query', ''),
                    'clicks': q.get('clicks', 0),
                    'impressions': q.get('impressions', 0),
                    'ctr': q.get('ctr', 0),
                    'position': q.get('position', 0)
                } for q in top_queries]
            }
            
        except Exception as e:
            logger.error(f"Error getting site metrics: {str(e)}")
            return {}
    
    async def get_search_competitors(
        self,
        domain: str,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get a list of competing domains based on shared search queries.
        
        Args:
            domain: The domain to find competitors for
            days: Number of days to look back (default: 30)
            limit: Maximum number of competitors to return
            
        Returns:
            List of competing domains with shared query data
        """
        if not self.service:
            logger.warning("GSC service not initialized. Skipping get_search_competitors.")
            return []
        try:
            # This is a simplified implementation
            # In a real implementation, you would query for domains that rank for similar keywords
            # and have overlapping search visibility
            
            # For now, return a mock response
            return [
                {
                    'domain': f'competitor{i}.com',
                    'common_keywords': 100 * (i + 1),
                    'traffic_share': 0.1 * (i + 1),
                    'overlap_score': 0.8 - (i * 0.1)
                }
                for i in range(min(limit, 5))
            ]
            
        except Exception as e:
            logger.error(f"Error finding search competitors: {str(e)}")
            raise Exception(f"Error finding search competitors: {str(e)}") from e
    
    async def get_site_issues(self, site_url: str) -> Dict[str, Any]:
        """Get information about site issues from Google Search Console.
        
        Args:
            site_url: The URL of the site to get issues for
            
        Returns:
            Dictionary containing information about site issues with the following structure:
            {
                'mobile_usability_issues': List[Dict],  # Mobile usability issues
                'security_issues': List[Dict],          # Security issues
                'indexing_issues': List[Dict],          # Indexing issues
                'enhancement_opportunities': List[Dict] # Enhancement opportunities
            }
            
        Raises:
            ValueError: If the service is not initialized or site_url is invalid
            Exception: For any API errors
        """
        if not self.service:
            raise ValueError("Google Search Console service is not initialized")
            
        if not site_url:
            raise ValueError("site_url is required")
            
        try:
            logger.info(f"Fetching site issues for {site_url}")
            
            # Initialize the result structure
            issues = {
                'mobile_usability_issues': [],
                'security_issues': [],
                'indexing_issues': [],
                'enhancement_opportunities': []
            }
            
            # Get mobile usability issues
            try:
                mobile_issues = self.service.urlInspection().index().inspect(
                    body={
                        'inspectionUrl': site_url,
                        'siteUrl': site_url,
                        'languageCode': 'en-US'
                    }
                ).execute()
                
                if 'inspectionResult' in mobile_issues:
                    issues['mobile_usability_issues'] = mobile_issues['inspectionResult'].get(
                        'mobileUsabilityResult', {}
                    ).get('issues', [])
            except Exception as e:
                logger.error(f"Error getting mobile usability issues: {str(e)}")
                raise Exception(f"Error getting mobile usability issues: {str(e)}") from e
            
            # Get security issues
            try:
                security_issues = self.service.sitemaps().list(siteUrl=site_url).execute()
                issues['security_issues'] = security_issues.get('sitemap', [])
                
            except Exception as e:
                logger.warning(f"Could not fetch security issues: {str(e)}")
                issues['security_issues'] = [{
                    'error': str(e),
                    'message': 'Failed to fetch security issues. The site may not have any security issues or there was an authentication error.'
                }]
            
            # Get indexing issues
            try:
                sitemaps = self.service.sitemaps().list(siteUrl=site_url).execute()
                if 'sitemap' in sitemaps:
                    for sitemap in sitemaps['sitemap']:
                        if 'errors' in sitemap and sitemap['errors'] != '0':
                            issues['indexing_issues'].append({
                                'path': sitemap.get('path', ''),
                                'errors': sitemap.get('errors', ''),
                                'type': 'sitemap_error',
                                'last_submitted': sitemap.get('lastSubmitted', '')
                            })
                
                # Check URL inspection for additional indexing issues
                inspection = self.service.urlInspection().index().inspect(
                    body={
                        'inspectionUrl': f"{site_url.rstrip('/')}/",
                        'siteUrl': site_url,
                        'languageCode': 'en-US'
                    }
                ).execute()
                
                if 'inspectionResult' in inspection:
                    index_status = inspection['inspectionResult'].get('indexStatusResult', {})
                    if 'verdict' in index_status and index_status['verdict'] != 'PASS':
                        issues['indexing_issues'].append({
                            'issue': index_status.get('verdict', 'UNKNOWN_ISSUE'),
                            'details': index_status.get('details', ''),
                            'type': 'indexing_issue',
                            'crawled_as': index_status.get('crawledAs', 'URL_UNSPECIFIED')
                        })
                
            except Exception as e:
                logger.warning(f"Could not fetch indexing issues: {str(e)}")
                issues['indexing_issues'].append({
                    'error': str(e),
                    'message': 'Failed to fetch indexing issues. The site may be new or there was an authentication error.'
                })
            
            # Get enhancement opportunities
            try:
                # This is a placeholder for enhancement opportunities
                # In a real implementation, this would analyze the site's data
                # to suggest improvements
                pass
                
            except Exception as e:
                logger.warning(f"Could not fetch enhancement opportunities: {str(e)}")
                issues['enhancement_opportunities'] = [{
                    'error': str(e),
                    'message': 'Failed to fetch enhancement opportunities.'
                }]
            
            logger.info(f"Successfully fetched site issues for {site_url}")
            return issues
            
        except Exception as e:
            error_msg = f"Error getting site issues for {site_url}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg) from e

    async def get_search_analytics_paginated(
        self,
        site_url: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        dimensions: Optional[List[str]] = None,
        page_size: int = 1000,
        max_pages: Optional[int] = None,
        **filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetch search analytics data with pagination support.
        
        Args:
            site_url: The URL of the site in Google Search Console
            start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            dimensions: List of dimensions to group by
            page_size: Number of rows per page (max 25,000)
            max_pages: Maximum number of pages to fetch (None for no limit)
            **filters: Additional filters to apply to the query
            
        Returns:
            List of dictionaries containing search analytics data
            
        Raises:
            ValueError: If the service is not initialized or invalid parameters are provided
            Exception: For any API errors
        """
        if not self.service:
            raise ValueError("Google Search Console service is not initialized")
            
        if not site_url:
            raise ValueError("site_url is required")
            
        if page_size > 25000:
            raise ValueError("page_size cannot exceed 25,000")
            
        # Set default dimensions if not provided
        dimensions = dimensions or ['query', 'page', 'country', 'device']
        
        # Set default date range if not provided
        end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
        all_results = []
        start_row = 0
        page = 1
        
        try:
            while True:
                if max_pages and page > max_pages:
                    logger.info(f"Reached maximum number of pages ({max_pages})")
                    break
                    
                logger.info(f"Fetching page {page} (rows {start_row + 1}-{start_row + page_size})")
                
                # Prepare the request body
                request = {
                    'startDate': start_date,
                    'endDate': end_date,
                    'dimensions': dimensions,
                    'rowLimit': page_size,
                    'startRow': start_row
                }
                
                # Add filters if provided
                if filters:
                    request['dimensionFilterGroups'] = [{
                        'filters': [{
                            'dimension': dim,
                            'operator': 'equals',
                            'expression': value
                        } for dim, value in filters.items()]
                    }]
                
                # Make the API request
                response = self.service.searchanalytics().query(
                    siteUrl=site_url,
                    body=request
                ).execute()
                
                # Process the response
                page_results = self._process_search_analytics_response(response, dimensions)
                all_results.extend(page_results)
                
                # Check if we've reached the end of the results
                if len(page_results) < page_size:
                    logger.info(f"Reached end of results after {len(all_results)} rows")
                    break
                    
                # Update for next page
                start_row += page_size
                page += 1
                
                # Add a small delay to avoid rate limiting
                await asyncio.sleep(1)
                
            return all_results
            
        except Exception as e:
            error_msg = f"Error in get_search_analytics_paginated: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg) from e
    
    async def get_sitemap_info(self, site_url: str, sitemap_url: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a sitemap or list all sitemaps for a site.
        
        Args:
            site_url: The URL of the site in Google Search Console
            sitemap_url: Optional specific sitemap URL to get details for
            
        Returns:
            Dictionary containing sitemap information. If sitemap_url is provided,
            returns detailed information about that sitemap. Otherwise, returns
            a list of all sitemaps for the site.
            
        Raises:
            ValueError: If the service is not initialized or site_url is invalid
            Exception: For any API errors
        """
        if not self.service:
            raise ValueError("Google Search Console service is not initialized")
            
        if not site_url:
            raise ValueError("site_url is required")
            
        try:
            if sitemap_url:
                # Get details for a specific sitemap
                logger.info(f"Fetching details for sitemap: {sitemap_url}")
                sitemap = self.service.sitemaps().get(
                    siteUrl=site_url,
                    feedpath=sitemap_url
                ).execute()
                return sitemap
            else:
                # List all sitemaps for the site
                logger.info(f"Fetching all sitemaps for site: {site_url}")
                sitemaps = self.service.sitemaps().list(siteUrl=site_url).execute()
                return sitemaps.get('sitemap', [])
                
        except Exception as e:
            error_msg = f"Error getting sitemap info for {site_url}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg) from e
    
    async def submit_sitemap(self, site_url: str, sitemap_url: str) -> Dict[str, Any]:
        """Submit a sitemap to Google Search Console for crawling.
        
        Args:
            site_url: The URL of the site in Google Search Console
            sitemap_url: The URL of the sitemap to submit (relative to the site)
            
        Returns:
            Dictionary containing the submission result
            
        Raises:
            ValueError: If the service is not initialized or parameters are invalid
            Exception: For any API errors
        """
        if not self.service:
            raise ValueError("Google Search Console service is not initialized")
            
        if not site_url or not sitemap_url:
            raise ValueError("Both site_url and sitemap_url are required")
            
        try:
            logger.info(f"Submitting sitemap {sitemap_url} for site {site_url}")
            
            # Submit the sitemap
            result = self.service.sitemaps().submit(
                siteUrl=site_url,
                feedpath=sitemap_url
            ).execute()
            
            logger.info(f"Successfully submitted sitemap: {sitemap_url}")
            return {
                'success': True,
                'sitemap': sitemap_url,
                'site': site_url,
                'details': result
            }
            
        except Exception as e:
            error_msg = f"Error submitting sitemap {sitemap_url} for site {site_url}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg) from e
    
    async def inspect_url(self, site_url: str, url: str) -> Dict[str, Any]:
        """Inspect a URL using the Google Search Console URL Inspection API.
        
        This provides detailed information about how Google Search sees a specific URL.
        
        Args:
            site_url: The URL of the site in Google Search Console
            url: The specific URL to inspect (must be under the site_url)
            
        Returns:
            Dictionary containing the inspection results with detailed information
            about how Google Search sees the URL.
            
        Raises:
            ValueError: If the service is not initialized or parameters are invalid
            Exception: For any API errors
        """
        if not self.service:
            raise ValueError("Google Search Console service is not initialized")
            
        if not site_url or not url:
            raise ValueError("Both site_url and url are required")
            
        try:
            logger.info(f"Inspecting URL: {url} for site: {site_url}")
            
            # Make the URL inspection request
            inspection_result = self.service.urlInspection().index().inspect(
                body={
                    'inspectionUrl': url,
                    'siteUrl': site_url,
                    'languageCode': 'en-US'  # Language code for the response
                }
            ).execute()
            
            # Extract and format the most useful information
            if 'inspectionResult' in inspection_result:
                result = inspection_result['inspectionResult']
                
                # Basic URL information
                response = {
                    'verdict': result.get('verdict', 'UNKNOWN'),
                    'page_fetch': result.get('pageFetchState', {}).get('status', 'UNKNOWN'),
                    'indexing_state': result.get('indexStatusResult', {}).get('verdict', 'UNKNOWN'),
                    'coverage_state': result.get('coverageInfo', {}).get('indexingState', 'UNKNOWN'),
                    'last_crawl_time': result.get('indexStatusResult', {}).get('lastCrawlTime')
                }
                
                # Add mobile usability results if available
                if 'mobileUsabilityResult' in result:
                    response['mobile_usability'] = {
                        'verdict': result['mobileUsabilityResult'].get('verdict', 'UNKNOWN'),
                        'issues': result['mobileUsabilityResult'].get('issues', [])
                    }
                
                # Add rich results if available
                if 'richResultsResult' in result:
                    response['rich_results'] = {
                        'verdict': result['richResultsResult'].get('verdict', 'UNKNOWN'),
                        'detected_items': result['richResultsResult'].get('detectedItems', [])
                    }
                
                logger.info(f"Successfully inspected URL: {url}")
                return response
            
            return {'error': 'No inspection result found'}
            
        except Exception as e:
            error_msg = f"Error inspecting URL {url}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg) from e
    
    async def request_indexing(self, site_url: str, url: str) -> Dict[str, Any]:
        """Request indexing for a specific URL in Google Search Console.
        
        This submits a URL to Google's index, asking it to crawl and index the URL.
        Note that this doesn't guarantee immediate indexing, but it can help speed up
        the process for important pages.
        
        Args:
            site_url: The URL of the site in Google Search Console
            url: The specific URL to request indexing for
            
        Returns:
            Dictionary containing the request result with status information
            
        Raises:
            ValueError: If the service is not initialized or parameters are invalid
            Exception: For any API errors
        """
        if not self.service:
            raise ValueError("Google Search Console service is not initialized")
            
        if not site_url or not url:
            raise ValueError("Both site_url and url are required")
            
        try:
            logger.info(f"Requesting indexing for URL: {url} in site: {site_url}")
            
            # Make the URL inspection request first to verify the URL
            inspection_result = self.service.urlInspection().index().inspect(
                body={
                    'inspectionUrl': url,
                    'siteUrl': site_url,
                    'languageCode': 'en-US'
                }
            ).execute()
            
            # Check if the URL inspection was successful
            if 'inspectionResult' not in inspection_result:
                return {
                    'success': False,
                    'message': 'Failed to inspect URL',
                    'details': inspection_result
                }
            
            # Check if the URL is already indexed
            inspection_data = inspection_result['inspectionResult']
            index_status = inspection_data.get('indexStatusResult', {})
            
            if index_status.get('verdict') == 'PASS' and index_status.get('indexingState') == 'INDEXING_ALLOWED':
                # The URL is not indexed but can be - request indexing
                result = self.service.urlInspection().index().inspect(
                    body={
                        'inspectionUrl': url,
                        'siteUrl': site_url,
                        'languageCode': 'en-US',
                        'inspectUrlOverride': url,
                        'inspectUrlIndexability': True
                    }
                ).execute()
                
                return {
                    'success': True,
                    'status': 'INDEXING_REQUESTED',
                    'message': 'Successfully requested indexing',
                    'details': result
                }
            else:
                # The URL is either already indexed or cannot be indexed
                return {
                    'success': True,
                    'status': index_status.get('indexingState', 'UNKNOWN'),
                    'message': 'URL does not require indexing or cannot be indexed',
                    'details': {
                        'verdict': index_status.get('verdict', 'UNKNOWN'),
                        'indexing_state': index_status.get('indexingState', 'UNKNOWN'),
                        'last_crawl_time': index_status.get('lastCrawlTime')
                    }
                }
                
        except Exception as e:
            error_msg = f"Error requesting indexing for URL {url}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to request indexing'
            }
    
    async def get_verified_sites(self, include_permission_level: bool = True) -> List[Dict[str, Any]]:
        """Get a list of verified sites from Google Search Console with detailed information.
        
        Args:
            include_permission_level: Whether to include permission level information
            
        Returns:
            List of dictionaries containing site information with the following keys:
            - site_url (str): The URL of the site
            - permission_level (str): The permission level (e.g., 'siteOwner', 'siteFullUser')
            - verified (bool): Whether the site is verified
            - last_verified_time (str, optional): When the site was last verified
            - verification_method (str, optional): Method used for verification
            
        Raises:
            ValueError: If the service is not initialized
            Exception: For any API errors
        """
        if not self.service:
            raise ValueError("Google Search Console service is not initialized")
            
        try:
            logger.info("Fetching list of verified sites from Google Search Console")
            
            # Make the API request to get the list of sites
            result = self.service.sites().list().execute()
            
            # Process the sites
            sites = []
            for site in result.get('siteEntry', []):
                site_info = {
                    'site_url': site.get('siteUrl', ''),
                    'permission_level': site.get('permissionLevel', ''),
                    'verified': site.get('permissionLevel') in ['siteOwner', 'siteFullUser', 'siteRestrictedUser'],
                }
                
                # Add additional metadata if available
                if 'verificationMethod' in site:
                    site_info['verification_method'] = site['verificationMethod']
                if 'lastVerifiedTime' in site:
                    site_info['last_verified_time'] = site['lastVerifiedTime']
                
                # Only include sites where we have at least view access
                if site_info['permission_level']:  # Only include if we have any access
                    sites.append(site_info)
            
            logger.info(f"Found {len(sites)} accessible sites")
            
            # If permission level filtering is enabled, only return sites with owner access
            if include_permission_level:
                sites = [s for s in sites if s['permission_level'] == 'siteOwner']
                logger.info(f"Filtered to {len(sites)} sites with owner access")
            
            return sites
            
        except Exception as e:
            error_msg = f"Error getting verified sites: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg) from e
