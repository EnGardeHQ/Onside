"""Tests for the SEO service.

These tests verify the functionality of the SEOService class, including:
- Competitor analysis from multiple sources
- Domain metrics collection
- Caching behavior
- Error handling and service degradation
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock, Mock
from datetime import datetime

from src.services.seo.seo_service import SEOService

# Mock the SemrushService import at the module level
with patch('src.services.seo.seo_service.SemrushService') as mock_semrush_class, \
     patch('src.services.seo.seo_service.SerpService') as mock_serp_class, \
     patch('src.services.seo.seo_service.GoogleSearchConsoleService') as mock_gsc_class, \
     patch('src.services.seo.seo_service.GoogleAnalyticsService') as mock_ga_class, \
     patch('src.services.seo.seo_service.PageSpeedInsightsService') as mock_psi_class:
    
    # Create mock instances
    mock_semrush = AsyncMock()
    mock_serp = AsyncMock()
    mock_gsc = AsyncMock()
    mock_ga = AsyncMock()
    mock_psi = AsyncMock()
    
    # Configure class mocks to return our mock instances
    mock_semrush_class.return_value = mock_semrush
    mock_serp_class.return_value = mock_serp
    mock_gsc_class.return_value = mock_gsc
    mock_ga_class.return_value = mock_ga
    mock_psi_class.return_value = mock_psi

# Sample test data
SAMPLE_DOMAIN = "example.com"
SAMPLE_COMPETITORS = [
    {"domain": "competitor1.com", "traffic_share": 1000, "common_keywords": ["seo", "marketing"]},
    {"domain": "competitor2.com", "traffic_share": 2000, "common_keywords": ["seo", "analytics"]}
]

SAMPLE_METRICS = {
    "overview": {"authority_score": 85, "trust_metrics": {"trust_flow": 42}},
    "traffic": {"organic_traffic": 10000, "sessions": 15000},
    "backlinks": {"total": 5000, "referring_domains": 350},
    "performance": {"first_contentful_paint": 1.8},
    "mobile_usability": {"passed": True, "issues": []}
}


@pytest.fixture
def mock_services():
    """Create mock services for testing."""
    # These mocks are already set up at the module level
    return {
        'SemrushService': mock_semrush_class,
        'SerpService': mock_serp_class,
        'GoogleSearchConsoleService': mock_gsc_class,
        'GoogleAnalyticsService': mock_ga_class,
        'PageSpeedInsightsService': mock_psi_class
    }


@pytest.fixture
def seo_service(mock_services):
    """Create an SEOService instance with mocked dependencies."""
    # Configure mock methods
    mock_semrush.get_competitors.return_value = SAMPLE_COMPETITORS
    mock_semrush.get_domain_overview.return_value = {
        "authority_score": 85, 
        "traffic": 10000, 
        "backlinks": 5000
    }
    
    mock_gsc.get_search_competitors.return_value = [
        {"domain": "competitor2.com", "clicks": 5000}
    ]
    mock_gsc.get_site_metrics.return_value = {
        "clicks": 12000, 
        "impressions": 100000, 
        "ctr": 0.12
    }
    
    mock_ga.get_metrics.return_value = {
        "sessions": 15000, 
        "users": 12000, 
        "bounceRate": 45.5
    }
    
    mock_psi.analyze.return_value = {
        "firstContentfulPaint": 1.8,
        "speedIndex": 2.1,
        "mobileUsability": {"passed": True, "issues": []}
    }
    
    # Mock SerpService
    mock_serp.get_competitors.return_value = []
    
    # Mock cache
    with patch('src.services.seo.seo_service.cache') as mock_cache:
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        
        # Create the service instance
        service = SEOService()
        
        # Make sure our mocks are used
        assert service.semrush_service == mock_semrush
        assert service.serp_service == mock_serp
        assert service.gsc_service == mock_gsc
        assert service.ga_service == mock_ga
        assert service.psi_service == mock_psi
        
        yield service


@pytest.mark.asyncio
async def test_get_competing_domains(seo_service):
    """Test getting competing domains from multiple sources."""
    # Act
    competitors = await seo_service.get_competing_domains(SAMPLE_DOMAIN)
    
    # Assert
    assert len(competitors) == 2  # Should have 2 unique competitors
    assert all(c['domain'] in ['competitor1.com', 'competitor2.com'] for c in competitors)
    assert all('traffic_share' in c for c in competitors)
    assert all('common_keywords' in c for c in competitors)


@pytest.mark.asyncio
async def test_get_domain_metrics(seo_service):
    """Test getting comprehensive domain metrics."""
    # Act
    metrics = await seo_service.get_domain_metrics(SAMPLE_DOMAIN)
    
    # Assert
    assert 'overview' in metrics
    assert 'traffic' in metrics
    assert 'backlinks' in metrics
    assert 'performance' in metrics
    assert 'mobile_usability' in metrics
    assert 'health_score' in metrics
    
    # Verify some key metrics
    assert metrics['overview']['authority_score'] == 85
    assert metrics['traffic']['organic_traffic'] == 10000
    assert metrics['backlinks']['total'] == 5000
    assert metrics['mobile_usability']['passed'] is True
    assert 0 <= metrics['health_score'] <= 100


@pytest.mark.asyncio
async def test_service_degradation(seo_service):
    """Test that the service degrades gracefully when external services fail."""
    # Simulate SEMrush failure
    seo_service.service_status['semrush'] = False
    
    # Should still work without SEMrush
    competitors = await seo_service.get_competing_domains(SAMPLE_DOMAIN)
    assert len(competitors) > 0  # Should still get competitors from other sources
    
    # Verify metrics still work
    metrics = await seo_service.get_domain_metrics(SAMPLE_DOMAIN)
    assert 'health_score' in metrics
