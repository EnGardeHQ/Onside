"""
Google Search Console Service using OAuth 2.0 Refresh Token

This module provides a simplified way to interact with the Google Search Console API
using OAuth 2.0 refresh tokens for authentication.
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
DEFAULT_DIMENSIONS = ['query', 'page', 'country', 'device', 'date']
MAX_RETRIES = 3

class GoogleSearchConsoleError(Exception):
    """Custom exception for Google Search Console errors."""
    pass

class GoogleSearchConsoleService:
    """Service for interacting with Google Search Console API using OAuth 2.0 refresh tokens."""
    
    def __init__(self):
        """Initialize the Google Search Console service with OAuth 2.0 refresh token."""
        self.service = self._authenticate()
        if not self.service:
            raise GoogleSearchConsoleError("Failed to initialize Google Search Console service")
    
    def _authenticate(self):
        """Authenticate with Google Search Console API using OAuth 2.0 refresh token."""
        try:
            # Get credentials from environment variables
            client_id = os.getenv('PAGESPEED_CLIENT_ID')
            client_secret = os.getenv('Google Web CLIENT_SECRET')
            refresh_token = os.getenv('GOOGLE_REFRESH_TOKEN')
            
            if not all([client_id, client_secret, refresh_token]):
                raise GoogleSearchConsoleError(
                    "Missing required OAuth 2.0 credentials. Please set the following environment variables:\n"
                    "- PAGESPEED_CLIENT_ID\n"
                    "- Google Web CLIENT_SECRET\n"
                    "- GOOGLE_REFRESH_TOKEN"
                )
            
            # Create credentials object
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=client_id,
                client_secret=client_secret,
                scopes=SCOPES
            )
            
            # Refresh the token to ensure it's valid
            creds.refresh(Request())
            
            # Build and return the service
            service = build(
                'searchconsole',
                'v1',
                credentials=creds,
                cache_discovery=False,
                static_discovery=False
            )
            
            logger.info("Successfully authenticated with Google Search Console API")
            return service
            
        except RefreshError as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise GoogleSearchConsoleError(
                "Failed to refresh access token. The refresh token may be invalid or expired. "
                "Please generate a new refresh token using the generate_google_token.py script."
            )
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}", exc_info=True)
            raise GoogleSearchConsoleError(f"Authentication failed: {str(e)}")
    
    def get_search_analytics(
        self,
        site_url: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        dimensions: Optional[List[str]] = None,
        row_limit: int = 1000,
        retry_count: int = 0
    ) -> List[Dict[str, Any]]:
        """Fetch search analytics data from Google Search Console.
        
        Args:
            site_url: The URL of the property as defined in Search Console.
            start_date: Start date in 'YYYY-MM-DD' format or datetime object.
            end_date: End date in 'YYYY-MM-DD' format or datetime object.
            dimensions: List of dimensions to group results by.
            row_limit: Maximum number of rows to return (max 25000).
            retry_count: Internal counter for retry attempts.
            
        Returns:
            List of dictionaries containing search analytics data.
            
        Raises:
            GoogleSearchConsoleError: If there's an error fetching the data.
        """
        try:
            # Set default date range (last 30 days)
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Convert dates to string if they're datetime objects
            if isinstance(start_date, datetime):
                start_date = start_date.strftime('%Y-%m-%d')
            if isinstance(end_date, datetime):
                end_date = end_date.strftime('%Y-%m-%d')
            
            # Set default dimensions if not provided
            if not dimensions:
                dimensions = DEFAULT_DIMENSIONS
            
            # Prepare the request body
            request_body = {
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': dimensions,
                'rowLimit': min(row_limit, 25000),  # API max is 25000
                'startRow': 0
            }
            
            logger.info(f"Fetching search analytics for {site_url} from {start_date} to {end_date}")
            logger.debug(f"Request body: {json.dumps(request_body, indent=2)}")
            
            # Make the API request
            response = self.service.searchanalytics().query(
                siteUrl=site_url,
                body=request_body
            ).execute()
            
            # Process the response
            rows = response.get('rows', [])
            logger.info(f"Retrieved {len(rows)} rows of data")
            
            # Format the results
            results = []
            for row in rows:
                result = {
                    'clicks': row.get('clicks', 0),
                    'impressions': row.get('impressions', 0),
                    'ctr': row.get('ctr', 0),
                    'position': row.get('position', 0),
                }
                
                # Add dimension values
                for i, key in enumerate(dimensions):
                    if i < len(row.get('keys', [])):
                        result[key] = row['keys'][i]
                
                results.append(result)
            
            return results
            
        except Exception as e:
            error_msg = f"Error fetching search analytics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Retry on rate limit or server errors
            if retry_count < MAX_RETRIES and ('quota' in str(e).lower() or 'rate' in str(e).lower()):
                retry_delay = (2 ** retry_count) * 5  # Exponential backoff
                logger.warning(f"Rate limited. Retrying in {retry_delay} seconds... (Attempt {retry_count + 1}/{MAX_RETRIES})")
                time.sleep(retry_delay)
                return self.get_search_analytics(
                    site_url, start_date, end_date, dimensions, row_limit, retry_count + 1
                )
                
            raise GoogleSearchConsoleError(error_msg)
    
    def list_sites(self) -> List[Dict[str, str]]:
        """List all sites available in the Search Console account.
        
        Returns:
            List of dictionaries containing site URLs and permission levels.
        """
        try:
            response = self.service.sites().list().execute()
            return response.get('siteEntry', [])
        except Exception as e:
            error_msg = f"Error listing sites: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise GoogleSearchConsoleError(error_msg)
