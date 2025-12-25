"""
Tests for the Google Analytics service.

This module contains unit tests for the GoogleAnalyticsService class and its methods.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock
from datetime import datetime, timedelta
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportResponse,
    Row,
    DimensionValue,
    MetricValue
)

from src.services.seo.google_analytics import GoogleAnalyticsService

# Pytest will automatically handle async tests with the asyncio plugin
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_ga_service():
    """Create a mock Google Analytics service instance."""
    # Patch the _initialize_client method to avoid loading real credentials
    with patch.object(GoogleAnalyticsService, '_initialize_client', return_value=MagicMock(spec=BetaAnalyticsDataClient)):
        service = GoogleAnalyticsService(
            property_id='properties/123456789',
            credentials_path=None  # Don't use a real credentials file
        )
        # Mock the client
        service.client = MagicMock(spec=BetaAnalyticsDataClient)
        return service

async def test_initialize_client(mock_ga_service):
    """Test that the GA client is initialized correctly."""
    assert mock_ga_service.client is not None
    assert isinstance(mock_ga_service.client, MagicMock)

async def test_get_metrics(mock_ga_service):
    """Test getting metrics from Google Analytics."""
    # Mock the API response
    mock_response = RunReportResponse(
        rows=[
            Row(
                dimension_values=[
                    DimensionValue(value="/home"),
                    DimensionValue(value="United States"),
                    DimensionValue(value="desktop")
                ],
                metric_values=[
                    MetricValue(value="1000"),
                    MetricValue(value="900"),
                    MetricValue(value="45.5"),
                    MetricValue(value="120")
                ]
            )
        ]
    )
    
    # Set up the mock
    mock_ga_service.client.run_report = AsyncMock(return_value=mock_response)
    
    # Call the method
    metrics = await mock_ga_service.get_metrics(
        start_date="2023-01-01",
        end_date="2023-01-31",
        dimensions=['pagePath', 'country', 'deviceCategory'],
        metrics=['sessions', 'users', 'bounceRate', 'avgSessionDuration']
    )
    
    # Assertions
    assert len(metrics) == 1
    assert metrics[0]['pagePath'] == '/home'
    assert metrics[0]['country'] == 'United States'
    assert metrics[0]['deviceCategory'] == 'desktop'
    assert metrics[0]['sessions'] == 1000
    assert metrics[0]['users'] == 900
    assert metrics[0]['bounceRate'] == 45.5
    assert metrics[0]['avgSessionDuration'] == 120.0
    
    # Verify the API was called with the correct parameters
    mock_ga_service.client.run_report.assert_called_once()
    request = mock_ga_service.client.run_report.call_args[0][0]
    assert request.property == 'properties/123456789'
    assert request.date_ranges[0].start_date == '2023-01-01'
    assert request.date_ranges[0].end_date == '2023-01-31'
    assert [d.name for d in request.dimensions] == ['pagePath', 'country', 'deviceCategory']
    assert [m.name for m in request.metrics] == ['sessions', 'users', 'bounceRate', 'avgSessionDuration']

async def test_get_site_metrics(mock_ga_service):
    """Test getting aggregated site metrics."""
    # Setup the mock for get_metrics
    mock_ga_service.get_metrics = AsyncMock(return_value=[{
        'sessions': 1000,
        'users': 900,
        'bounceRate': 45.5,
        'avgSessionDuration': 120.0,
        'newUsers': 800,
        'pageviewsPerSession': 3.2,
        'goalCompletionsAll': 50
    }])
    
    # Call the method
    metrics = await mock_ga_service.get_site_metrics(
        start_date="2023-01-01",
        end_date="2023-01-31"
    )
    
    # Assertions
    assert metrics['sessions'] == 1000
    assert metrics['users'] == 900
    assert metrics['bounce_rate'] == 45.5
    assert metrics['avg_session_duration'] == 120.0
    
    # Verify get_metrics was called with the correct parameters
    mock_ga_service.get_metrics.assert_called_once()
    args, kwargs = mock_ga_service.get_metrics.call_args
    assert kwargs['start_date'] == "2023-01-01"
    assert kwargs['end_date'] == "2023-01-31"
    assert kwargs['metrics'] == [
        'sessions', 'users', 'newUsers', 'bounceRate', 
        'avgSessionDuration', 'pageviewsPerSession', 'goalCompletionsAll'
    ]

async def test_get_engagement_metrics(mock_ga_service):
    """Test getting user engagement metrics."""
    # Setup the mock for get_metrics
    mock_ga_service.get_metrics = AsyncMock(return_value=[{
        'sessions': 1000,
        'users': 900,
        'bounceRate': 45.5,
        'avgSessionDuration': 120.0,
        'pageviewsPerSession': 3.2,
        'screenPageViews': 3200
    }])
    
    # Call the method
    metrics = await mock_ga_service.get_engagement_metrics(
        start_date="2023-01-01",
        end_date="2023-01-31"
    )
    
    # Assertions
    assert metrics['sessions'] == 1000
    assert metrics['users'] == 900
    assert metrics['bounce_rate'] == 45.5
    assert metrics['avg_session_duration'] == 120.0
    assert metrics['pages_per_session'] == 3.2
    assert metrics['pageviews'] == 3200
    
    # Verify get_metrics was called with the correct parameters
    mock_ga_service.get_metrics.assert_called_once()
    args, kwargs = mock_ga_service.get_metrics.call_args
    
    # Check that dates were converted to datetime objects
    from datetime import datetime
    assert isinstance(kwargs['start_date'], datetime)
    assert kwargs['start_date'].strftime('%Y-%m-%d') == "2023-01-01"
    assert isinstance(kwargs['end_date'], datetime)
    assert kwargs['end_date'].strftime('%Y-%m-%d') == "2023-01-31"
    assert kwargs['metrics'] == [
        'sessions', 'users', 'bounceRate', 'avgSessionDuration',
        'pageviewsPerSession', 'screenPageViews'
    ]

async def test_get_page_metrics(mock_ga_service):
    """Test getting metrics for a specific page."""
    # Setup the mock for get_metrics
    mock_ga_service.get_metrics = AsyncMock(return_value=[{
        'sessions': 500,
        'users': 450,
        'bounceRate': 40.0,
        'avgSessionDuration': 150.0,
        'pagePath': '/about',
        'pageTitle': 'About Us'
    }])
    
    # Call the method
    metrics = await mock_ga_service.get_page_metrics(
        page_path="/about",
        start_date="2023-01-01",
        end_date="2023-01-31"
    )
    
    # Assertions
    assert metrics['sessions'] == 500
    assert metrics['users'] == 450
    assert metrics['bounce_rate'] == 40.0
    assert metrics['avg_session_duration'] == 150.0
    assert metrics['page_path'] == '/about'
    
    # Verify get_metrics was called with the correct parameters
    mock_ga_service.get_metrics.assert_called_once()
    args, kwargs = mock_ga_service.get_metrics.call_args
    assert kwargs['start_date'] == "2023-01-01"
    assert kwargs['end_date'] == "2023-01-31"
    assert kwargs['dimension_filters'] == {'pagePath': '/about'}
    assert 'pageTitle' in kwargs['dimensions']
    assert 'pagePath' in kwargs['dimensions']

async def test_error_handling(mock_ga_service):
    """Test error handling when the API call fails."""
    # Setup the mock to raise an exception
    mock_ga_service.client.run_report = AsyncMock(side_effect=Exception("API Error"))
    
    # Call the method and verify it handles the exception
    with pytest.raises(Exception) as exc_info:
        await mock_ga_service.get_metrics(
            start_date="2023-01-01",
            end_date="2023-01-31"
        )
    
    assert "API Error" in str(exc_info.value)
