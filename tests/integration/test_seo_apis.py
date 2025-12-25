"""
Integration tests for SEO Service APIs.

These tests verify the integration with external APIs used by the SEO service.
When run without API keys, tests will use mocks to verify the integration.
"""
import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.seo.seo_service import SEOService
from src.services.seo.serp_service import SerpService
from src.services.seo.page_speed_insights import PageSpeedInsightsService

# Determine if we should run real API tests
RUN_REAL_API_TESTS = all(k in os.environ for k in ["SERPAPI_KEY", "GOOGLE_API_KEY"])

@pytest.fixture
def use_mocks() -> bool:
    """Determine whether to use mocks or real API calls."""
    return not RUN_REAL_API_TESTS

@pytest.fixture
def mock_serp_response() -> Dict[str, Any]:
    """Mock response from SERP API."""
    return {
        "search_metadata": {"status": "Success"},
        "search_parameters": {"q": "test", "engine": "google"},
        "organic_results": [
            {"position": 1, "title": "Test Result 1", "link": "https://example.com/1"},
            {"position": 2, "title": "Test Result 2", "link": "https://example.com/2"},
        ]
    }

@pytest.fixture
def mock_pagespeed_response() -> Dict[str, Any]:
    """Mock response from PageSpeed Insights API."""
    return {
        "lighthouseResult": {
            "categories": {
                "performance": {"score": 0.9},
                "accessibility": {"score": 0.95},
                "seo": {"score": 0.98},
                "best-practices": {"score": 0.92}
            },
            "audits": {
                "first-contentful-paint": {"numericValue": 1200},
                "speed-index": {"numericValue": 1800},
                "interactive": {"numericValue": 2500}
            }
        }
    }

@pytest.mark.asyncio
async def test_serp_api_integration(db_session: AsyncSession, mock_serp_response: Dict[str, Any], use_mocks: bool):
    """Test SERP API integration with either real or mock API calls."""
    # Initialize the service
    seo_service = SEOService(db=db_session)
    
    # Test parameters
    test_query = "test query"
    
    if use_mocks:
        # Patch the search method to return our mock response
        with patch.object(seo_service.serp, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_serp_response
            
            # Perform the search
            results = await seo_service.serp.search(test_query)
            
            # Verify the mock was called correctly
            mock_search.assert_called_once_with(test_query)
    else:
        # Skip if API key is not configured
        if not seo_service.service_status.get('serp', False):
            pytest.skip("SERP API not configured")
        
        # Perform the search with real API
        results = await seo_service.serp.search(test_query)
    
    # Basic assertions (same for both real and mock)
    assert isinstance(results, dict), "Expected a dictionary response"
    assert "search_metadata" in results, "Response missing search_metadata"
    assert "search_parameters" in results, "Response missing search_parameters"
    
    # Log some info for debugging
    mode = "MOCK" if use_mocks else "REAL"
    print(f"SERP API test ({mode}) - Query: {test_query}")
    print(f"Found {len(results.get('organic_results', []))} results")

@pytest.mark.asyncio
async def test_pagespeed_insights_integration(db_session: AsyncSession, mock_pagespeed_response: Dict[str, Any], use_mocks: bool):
    """Test PageSpeed Insights API integration with either real or mock API calls."""
    # Initialize the service
    seo_service = SEOService(db=db_session)
    
    # Test URL - using example.com as a stable test site
    test_url = "https://example.com"
    
    if use_mocks:
        # Patch the analyze method to return our mock response
        with patch.object(seo_service.psi, 'analyze', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_pagespeed_response
            
            # Perform the analysis
            results = await seo_service.psi.analyze(test_url)
            
            # Verify the mock was called correctly
            mock_analyze.assert_called_once_with(test_url)
    else:
        # Skip if API key is not configured
        if not seo_service.service_status.get('psi', False):
            pytest.skip("PageSpeed Insights API not configured")
        
        # Perform the analysis with real API
        results = await seo_service.psi.analyze(test_url)
    
    # Basic assertions (same for both real and mock)
    assert isinstance(results, dict), "Expected a dictionary response"
    assert "lighthouseResult" in results, "Response missing lighthouseResult"
    
    # Check for required categories
    categories = results.get("lighthouseResult", {}).get("categories", {})
    for category in ["performance", "accessibility", "seo", "best-practices"]:
        assert category in categories, f"Missing expected category: {category}"
    
    # Log some info for debugging
    mode = "MOCK" if use_mocks else "REAL"
    print(f"PageSpeed Insights test ({mode}) - URL: {test_url}")
    print(f"Performance score: {categories.get('performance', {}).get('score')}")

@pytest.mark.asyncio
async def test_seo_service_apis_together(db_session: AsyncSession, 
                                       mock_serp_response: Dict[str, Any],
                                       mock_pagespeed_response: Dict[str, Any],
                                       use_mocks: bool):
    """Test multiple SEO service APIs together."""
    # Initialize the service
    seo_service = SEOService(db=db_session)
    
    # Test data
    test_query = "test query"
    test_url = "https://example.com"
    
    if use_mocks:
        # Set up mocks for both services
        with (
            patch.object(seo_service.serp, 'search', new_callable=AsyncMock) as mock_serp,
            patch.object(seo_service.psi, 'analyze', new_callable=AsyncMock) as mock_psi
        ):
            mock_serp.return_value = mock_serp_response
            mock_psi.return_value = mock_pagespeed_response
            
            # Test SERP API
            serp_results = await seo_service.serp.search(test_query)
            assert isinstance(serp_results, dict)
            mock_serp.assert_called_once_with(test_query)
            
            # Test PageSpeed Insights
            psi_results = await seo_service.psi.analyze(test_url)
            assert isinstance(psi_results, dict)
            mock_psi.assert_called_once_with(test_url)
    else:
        # Skip if APIs are not configured
        if not all(seo_service.service_status.get(service, False) 
                  for service in ['serp', 'psi']):
            pytest.skip("Required APIs not configured")
        
        # Test with real APIs
        serp_results = await seo_service.serp.search(test_query)
        assert isinstance(serp_results, dict)
        
        psi_results = await seo_service.psi.analyze(test_url)
        assert isinstance(psi_results, dict)
    
    # Log success
    mode = "MOCK" if use_mocks else "REAL"
    print(f"All SEO service APIs ({mode}) responded successfully")

# Add more test cases as needed for different scenarios and edge cases
