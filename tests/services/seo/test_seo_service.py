"""
Tests for the SEO Service module.

This module contains unit tests for the SEOService class and its methods.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.seo.seo_service import SEOService
from src.models.domain import Domain

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session

@pytest.fixture
def seo_service(mock_db_session):
    """Create an instance of SEOService with a mock database session."""
    return SEOService(db=mock_db_session)

@pytest.fixture
def sample_domain_metrics():
    """Return sample domain metrics for testing."""
    return {
        'overview': {
            'authority_score': 75,
            'trust_metrics': {'score': 8.5, 'backlinks': 1000}
        },
        'traffic': {
            'organic_traffic': 5000,
            'sessions': 4500,
            'bounce_rate': 45.5,
            'avg_session_duration': 120
        },
        'backlinks': {
            'total': 1000,
            'referring_domains': 250
        },
        'performance': {
            'first_contentful_paint': 1.8,
            'speed_index': 3.2,
            'time_to_interactive': 3.5,
            'largest_contentful_paint': 2.1,
            'cumulative_layout_shift': 0.15
        },
        'mobile_usability': {
            'passed': True,
            'issues': []
        },
        'last_updated': '2023-05-20T12:00:00Z'
    }

@pytest.mark.asyncio
async def test_get_competing_domains(seo_service):
    """Test getting competing domains from multiple sources."""
    # Mock the service methods
    seo_service.semrush.get_competitors = AsyncMock(return_value=[
        {'domain': 'competitor1.com', 'common_keywords': 150, 'traffic_share': 0.3}
    ])
    seo_service.gsc.get_search_competitors = AsyncMock(return_value=[
        {'domain': 'competitor2.com', 'position': 2, 'ctr': 0.05}
    ])
    seo_service.serp.get_competitors = AsyncMock(return_value=[
        {'domain': 'competitor3.com', 'ranking': 3, 'traffic_share': 0.2}
    ])
    
    # Call the method
    competitors = await seo_service.get_competing_domains('example.com')
    
    # Assertions
    assert len(competitors) == 3
    assert any(c['domain'] == 'competitor1.com' for c in competitors)
    assert any(c['domain'] == 'competitor2.com' for c in competitors)
    assert any(c['domain'] == 'competitor3.com' for c in competitors)
    assert all('source' in c for c in competitors)
    assert all('last_updated' in c for c in competitors)

@pytest.mark.asyncio
async def test_get_domain_metrics(seo_service, sample_domain_metrics):
    """Test getting comprehensive domain metrics."""
    # Mock the service methods
    seo_service.semrush.get_domain_overview = AsyncMock(return_value={
        'authority_score': 75,
        'trust_metrics': {'score': 8.5, 'backlinks': 1000},
        'traffic': 5000,
        'paid_traffic': 1000,
        'backlinks': 1000,
        'referring_domains': 250
    })
    
    seo_service.gsc.get_site_metrics = AsyncMock(return_value={
        'clicks': 1000,
        'impressions': 10000,
        'ctr': 0.1,
        'position': 5.5,
        'top_keywords': [{'keyword': 'test', 'position': 1, 'clicks': 100}]
    })
    
    seo_service.ga.get_metrics = AsyncMock(return_value={
        'sessions': 4500,
        'users': 4000,
        'pageviews': 9000,
        'bounceRate': 45.5,
        'avgSessionDuration': 120
    })
    
    seo_service.psi.analyze = AsyncMock(return_value={
        'firstContentfulPaint': 1800,
        'speedIndex': 3200,
        'interactive': 3500,
        'totalBlockingTime': 200,
        'largestContentfulPaint': 2100,
        'cumulativeLayoutShift': 0.15,
        'mobileUsability': {
            'passed': True,
            'issues': []
        }
    })
    
    # Call the method
    metrics = await seo_service.get_domain_metrics('example.com')
    
    # Assertions
    assert metrics['overview']['authority_score'] == 75
    assert metrics['traffic']['organic_traffic'] == 5000
    assert metrics['backlinks']['total'] == 1000
    assert 'health_score' in metrics
    assert 0 <= metrics['health_score'] <= 100

@pytest.mark.asyncio
async def test_calculate_health_score(seo_service, sample_domain_metrics):
    """Test the health score calculation."""
    # Call the method
    health_score = seo_service._calculate_health_score(sample_domain_metrics)
    
    # Assertions
    assert isinstance(health_score, float)
    assert 0 <= health_score <= 100
    
    # Test with missing data
    incomplete_metrics = {'overview': {}, 'traffic': {}, 'backlinks': {}, 'performance': {}, 'mobile_usability': {}}
    health_score = seo_service._calculate_health_score(incomplete_metrics)
    assert health_score == 0.0

@pytest.mark.asyncio
async def test_get_domain_metrics_batch(seo_service):
    """Test getting metrics for multiple domains in batch."""
    # Mock the get_domain_metrics method
    seo_service.get_domain_metrics = AsyncMock(side_effect=[
        {'overview': {'authority_score': 75}, 'traffic': {}},
        {'overview': {'authority_score': 80}, 'traffic': {}},
        Exception("Test error")  # Simulate an error for the third domain
    ])
    
    # Call the method
    domains = ['example1.com', 'example2.com', 'example3.com']
    results = await seo_service.get_domain_metrics_batch(domains)
    
    # Assertions
    assert len(results) == 3
    assert 'example1.com' in results
    assert 'example2.com' in results
    assert 'example3.com' in results
    assert results['example1.com']['overview']['authority_score'] == 75
    assert results['example2.com']['overview']['authority_score'] == 80
    assert not results['example3.com']  # Empty dict for failed domain

@pytest.mark.asyncio
async def test_update_domain_metrics(seo_service, mock_db_session, sample_domain_metrics):
    """Test updating domain metrics in the database."""
    # Setup mock repository
    mock_repo = MagicMock()
    mock_repo.get_by_domain = AsyncMock(return_value=Domain(id=1, domain='example.com'))
    mock_repo.update = AsyncMock()
    seo_service.domain_repo = mock_repo
    
    # Call the method
    await seo_service._update_domain_metrics('example.com', sample_domain_metrics)
    
    # Assertions
    mock_repo.get_by_domain.assert_called_once_with('example.com')
    mock_repo.update.assert_called_once()
    
    # Check that the update data contains the metrics and updated_at
    call_args = mock_repo.update.call_args[1]
    assert 'seo_metrics' in call_args
    assert 'updated_at' in call_args
    assert call_args['seo_metrics'] == sample_domain_metrics

@pytest.mark.asyncio
async def test_service_error_handling(seo_service):
    """Test error handling when external services fail."""
    # Make all services fail
    seo_service.semrush.get_domain_overview = AsyncMock(side_effect=Exception("API Error"))
    seo_service.gsc.get_site_metrics = AsyncMock(side_effect=Exception("API Error"))
    seo_service.ga.get_metrics = AsyncMock(side_effect=Exception("API Error"))
    seo_service.psi.analyze = AsyncMock(side_effect=Exception("API Error"))
    
    # Call the method - it should not raise an exception
    metrics = await seo_service.get_domain_metrics('example.com')
    
    # Assertions
    assert metrics == {
        'overview': {},
        'traffic': {},
        'backlinks': {},
        'keywords': [],
        'performance': {},
        'mobile_usability': {},
        'last_updated': metrics['last_updated'],
        'health_score': 0.0
    }
