"""
Tests for Google Analytics OAuth2 integration.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from src.services.seo.google_analytics import GoogleAnalyticsService

def test_google_analytics_oauth_initialization():
    """Test GoogleAnalyticsService initialization with OAuth2."""
    oauth_credentials = {
        'token': 'test_token',
        'refresh_token': 'test_refresh',
        'token_uri': 'https://test.com/token',
        'client_id': 'test_client_id',
        'client_secret': 'test_secret',
        'scopes': ['https://www.googleapis.com/auth/analytics.readonly']
    }
    
    service = GoogleAnalyticsService(
        property_id='properties/123456789',
        oauth_credentials=oauth_credentials
    )
    
    assert service.property_id == 'properties/123456789'
    assert service.oauth_credentials == oauth_credentials

@patch('google.oauth2.credentials.Credentials')
@patch('google.analytics.data_v1beta.BetaAnalyticsDataClient')
def test_initialize_client(mock_client, mock_credentials):
    """Test client initialization with OAuth2 credentials."""
    # Setup mock credentials and client
    mock_creds_instance = MagicMock()
    mock_creds_instance.valid = True
    mock_credentials.return_value = mock_creds_instance
    
    mock_client_instance = MagicMock()
    mock_client.return_value = mock_client_instance
    
    oauth_credentials = {
        'token': 'test_token',
        'refresh_token': 'test_refresh',
        'token_uri': 'https://test.com/token',
        'client_id': 'test_client_id',
        'client_secret': 'test_secret',
        'scopes': ['https://www.googleapis.com/auth/analytics.readonly']
    }
    
    # Test successful initialization
    service = GoogleAnalyticsService(
        property_id='properties/123456789',
        oauth_credentials=oauth_credentials
    )
    
    # Verify credentials were created correctly
    mock_credentials.assert_called_once_with(
        token='test_token',
        refresh_token='test_refresh',
        token_uri='https://test.com/token',
        client_id='test_client_id',
        client_secret='test_secret',
        scopes=['https://www.googleapis.com/auth/analytics.readonly']
    )
    
    # Verify client was created with credentials
    mock_client.assert_called_once_with(credentials=mock_creds_instance)
    assert service.client == mock_client_instance

@patch('google.oauth2.credentials.Credentials')
@patch('google.analytics.data_v1beta.BetaAnalyticsDataClient')
def test_initialize_client_refresh(mock_client, mock_credentials):
    """Test client initialization with token refresh."""
    # Setup mock credentials that need refresh
    mock_creds_instance = MagicMock()
    mock_creds_instance.valid = False
    mock_credentials.return_value = mock_creds_instance
    
    mock_client_instance = MagicMock()
    mock_client.return_value = mock_client_instance
    
    oauth_credentials = {
        'token': 'test_token',
        'refresh_token': 'test_refresh',
        'scopes': ['https://www.googleapis.com/auth/analytics.readonly']
    }
    
    # Test initialization with refresh
    service = GoogleAnalyticsService(
        property_id='properties/123456789',
        oauth_credentials=oauth_credentials
    )
    
    # Verify refresh was called
    mock_creds_instance.refresh.assert_called_once()
    assert service.client == mock_client_instance

def test_initialize_client_missing_credentials():
    """Test initialization fails with missing credentials."""
    with pytest.raises(ValueError, match="OAuth2 credentials are required"):
        GoogleAnalyticsService(
            property_id='properties/123456789',
            oauth_credentials=None
        )

@patch('google.oauth2.credentials.Credentials')
@patch('google.analytics.data_v1beta.BetaAnalyticsDataClient')
@patch('src.services.seo.google_analytics.DateRange')
@patch('src.services.seo.google_analytics.Metric')
@patch('src.services.seo.google_analytics.Dimension')
@patch('src.services.seo.google_analytics.RunReportRequest')
async def test_get_metrics_with_oauth(
    mock_request, mock_dimension, mock_metric, mock_date_range, 
    mock_client, mock_credentials
):
    """Test getting metrics with OAuth2 authentication."""
    # Setup mock credentials and client
    mock_creds_instance = MagicMock()
    mock_creds_instance.valid = True
    mock_credentials.return_value = mock_creds_instance
    
    # Setup mock GA client response
    mock_ga_client = MagicMock()
    mock_client.return_value = mock_ga_client
    
    # Setup mock GA API response
    mock_response = MagicMock()
    mock_response.rows = [
        MagicMock(dimension_values=[MagicMock(value='20230101')], 
                 metric_values=[MagicMock(value='1000'), MagicMock(value='900')])
    ]
    mock_ga_client.run_report.return_value = mock_response
    
    # Setup request mocks
    mock_date_range.return_value = 'date_range'
    mock_metric.side_effect = lambda name: MagicMock(name=name)
    mock_dimension.side_effect = lambda name: MagicMock(name=name)
    mock_request.return_value = 'run_report_request'
    
    # Initialize service with OAuth2 credentials
    oauth_credentials = {
        'token': 'test_token',
        'refresh_token': 'test_refresh',
        'scopes': ['https://www.googleapis.com/auth/analytics.readonly']
    }
    service = GoogleAnalyticsService(
        property_id='properties/123456789',
        oauth_credentials=oauth_credentials
    )
    
    # Call the method
    result = await service.get_metrics(
        start_date='2023-01-01',
        end_date='2023-01-31',
        dimensions=['date'],
        metrics=['sessions', 'users']
    )
    
    # Verify the result
    assert len(result) == 1
    assert result[0]['date'] == '20230101'
    assert result[0]['sessions'] == '1000'
    assert result[0]['users'] == '900'
    
    # Verify the API was called with correct parameters
    mock_ga_client.run_report.assert_called_once_with('run_report_request')
