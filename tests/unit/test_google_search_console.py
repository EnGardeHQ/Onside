"""
Unit tests for Google Search Console service.

These tests verify the functionality of the GoogleSearchConsoleService class
using mocks to avoid making real API calls.
"""
import os
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock, mock_open
from typing import Dict, Any, Optional

from src.services.seo.google_search_console import GoogleSearchConsoleService

# Sample test data
SAMPLE_CREDENTIALS = {
    "type": "service_account",
    "project_id": "test-project",
    "private_key_id": "test-key-id",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQD...\n-----END PRIVATE KEY-----\n",
    "client_email": "test@test-project.iam.gserviceaccount.com",
    "client_id": "1234567890",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com"
}

SAMPLE_SEARCH_ANALYTICS_RESPONSE = {
    'rows': [
        {
            'keys': ['test query', 'https://example.com', 'USA', 'MOBILE', '2023-01-01'],
            'clicks': 100,
            'impressions': 1000,
            'ctr': 0.1,
            'position': 5.5
        }
    ]
}

def create_mock_credentials():
    """Create a mock Google credentials object."""
    creds = MagicMock()
    creds.expired = False
    creds.universe_domain = 'googleapis.com'
    return creds

class MockRequest:
    """Mock Google API request object."""
    def __init__(self, execute_side_effect=None):
        self.execute_side_effect = execute_side_effect
    
    def execute(self):
        if callable(self.execute_side_effect):
            return self.execute_side_effect()
        return self.execute_side_effect or {}

class MockService:
    """Mock Google Search Console service."""
    def __init__(self):
        self.searchanalytics = MagicMock()
        self.searchanalytics.query = MagicMock(side_effect=self.mock_query)
    
    def mock_query(self, siteUrl, body):
        return MockRequest(execute_side_effect=lambda: SAMPLE_SEARCH_ANALYTICS_RESPONSE)

@pytest.fixture
def mock_credentials_file():
    """Create a mock credentials file path for testing."""
    return "/path/to/test-credentials.json"

@pytest.fixture
def gsc_service(mock_credentials_file):
    """Create a GoogleSearchConsoleService instance with mock credentials."""
    with patch('google.oauth2.service_account.Credentials.from_service_account_file') as mock_creds:
        mock_creds.return_value = create_mock_credentials()
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_build.return_value = MockService()
            service = GoogleSearchConsoleService(credentials_path=mock_credentials_file)
            yield service

@patch('os.environ', {})
def test_initialization_without_credentials():
    """Test initialization without credentials."""
    # Test initialization without credentials
    with patch('google.oauth2.service_account.Credentials.from_service_account_file') as mock_creds:
        service = GoogleSearchConsoleService()
        assert service.service is None
        mock_creds.assert_not_called()

@patch('google.oauth2.service_account.Credentials.from_service_account_file')
@patch('googleapiclient.discovery.build')
def test_authentication_success(mock_build, mock_creds, mock_credentials_file):
    """Test successful authentication with Google Search Console."""
    # Setup mocks
    mock_creds.return_value = create_mock_credentials()
    mock_service = MockService()
    mock_build.return_value = mock_service
    
    # Create a new instance to test _authenticate directly
    service = GoogleSearchConsoleService(credentials_path=mock_credentials_file)
    
    # Verify the service was built correctly
    assert service.service is not None
    mock_build.assert_called_once_with(
        'searchconsole', 'v1', 
        credentials=mock_creds.return_value, 
        cache_discovery=False
    )
    
    # Verify the service is properly initialized
    assert service.service is not None

@patch('google.oauth2.service_account.Credentials.from_service_account_file')
@patch('googleapiclient.discovery.build')
def test_authentication_failure(mock_build, mock_creds, mock_credentials_file):
    """Test authentication failure with Google Search Console."""
    # Setup mock to raise an exception
    mock_creds.side_effect = Exception("Authentication failed")
    
    # Create a new instance to test _authenticate directly
    with pytest.raises(Exception, match="Authentication failed"):
        GoogleSearchConsoleService(credentials_path=mock_credentials_file)

@patch('google.oauth2.service_account.Credentials.from_service_account_file')
@patch('googleapiclient.discovery.build')
def test_get_search_analytics(mock_build, mock_creds):
    """Test getting search analytics data."""
    # Setup mocks
    mock_creds.return_value = create_mock_credentials()
    mock_service = MockService()
    mock_build.return_value = mock_service
    
    # Create service instance
    service = GoogleSearchConsoleService(credentials_path="dummy_path.json")
    
    # Call the method
    site_url = "https://example.com"
    result = service.get_search_analytics(site_url)
    
    # Verify the result
    assert len(result) == 1
    assert result[0]['query'] == 'test query'
    assert result[0]['page'] == 'https://example.com'
    assert result[0]['clicks'] == 100
    assert result[0]['impressions'] == 1000
    assert result[0]['ctr'] == 0.1
    assert result[0]['position'] == 5.5
    
    # Verify the API was called correctly
    mock_service.searchanalytics.query.assert_called_once_with(
        siteUrl=site_url,
        body={
            'startDate': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'endDate': datetime.now().strftime('%Y-%m-%d'),
            'dimensions': ['query', 'page', 'country', 'device', 'date'],
            'rowLimit': 1000,
            'startRow': 0
        }
    )

@patch('google.oauth2.service_account.Credentials.from_service_account_file')
@patch('googleapiclient.discovery.build')
def test_get_search_analytics_with_filters(mock_build, mock_creds):
    """Test getting search analytics with filters."""
    # Setup mocks
    mock_creds.return_value = create_mock_credentials()
    mock_service = MockService()
    mock_build.return_value = mock_service
    
    # Create service instance
    service = GoogleSearchConsoleService(credentials_path="dummy_path.json")
    
    # Call the method with filters
    site_url = "https://example.com"
    start_date = "2023-01-01"
    end_date = "2023-01-31"
    dimensions = ['query', 'page']
    row_limit = 100
    
    result = service.get_search_analytics(
        site_url=site_url,
        start_date=start_date,
        end_date=end_date,
        dimensions=dimensions,
        row_limit=row_limit
    )
    
    # Verify the result
    assert len(result) == 1
    assert result[0]['query'] == 'test query'
    assert result[0]['page'] == 'https://example.com'
    
    # Verify the API was called with correct parameters
    mock_service.searchanalytics.query.assert_called_once_with(
        siteUrl=site_url,
        body={
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': dimensions,
            'rowLimit': row_limit,
            'startRow': 0
        }
    )
