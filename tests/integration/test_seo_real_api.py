"""
Integration tests for SEO service with real API calls.

These tests verify that the SEO service can successfully communicate with external APIs.
They are marked with @pytest.mark.integration and will be skipped if the required
API keys are not configured.
"""
import os
import pytest
import pytest_asyncio
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional, AsyncGenerator
from unittest.mock import patch, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from src.services.seo.seo_service import SEOService
from src.services.seo.serp_service import SerpService
from src.services.seo.page_speed_insights import PageSpeedInsightsService
from src.models.domain import Domain
from src.models.company import Company
from src.models.user import User, UserRole
from src.models.seo import ContentAsset

# Skip these tests if we don't have the required API keys
pytestmark = pytest.mark.skipif(
    not os.environ.get('SERPAPI_KEY') or not os.environ.get('PAGESPEED_API_KEY'),
    reason='Missing required API keys for integration tests'
)

# Test domain to use for API calls
TEST_DOMAIN = 'example.com'

# Helper function to create test data
@pytest_asyncio.fixture(scope="function")
async def test_data(db_session: AsyncSession):
    """Fixture to create test data for each test function."""
    # Create a unique identifier for this test run
    test_id = str(uuid.uuid4())[:8]
    
    # Create a test user with a unique email
    user = User(
        email=f"test_{test_id}@example.com",
        username=f"testuser_{test_id}",
        hashed_password="hashed_password",
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create a test company with a unique domain
    company = Company(
        name=f"Test Company {test_id}",
        domain=TEST_DOMAIN,
        user_id=user.id,
        is_active=True
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    
    # Create a test domain with a unique domain
    domain = Domain(
        domain=TEST_DOMAIN,
        company_id=company.id,
        is_primary=True,
        is_active=True
    )
    db_session.add(domain)
    await db_session.commit()
    await db_session.refresh(domain)
    
    try:
        data = (user, company, domain)
        yield data
    finally:
        # Clean up test data
        await db_session.execute(delete(ContentAsset).where(ContentAsset.url.like(f"%{domain.domain}%")))
        await db_session.execute(delete(Domain).where(Domain.id == domain.id)) if domain else None
        await db_session.execute(delete(Company).where(Company.id == company.id)) if company else None
        await db_session.execute(delete(User).where(User.id == user.id)) if user else None
        await db_session.commit()

@pytest.mark.asyncio
async def test_serp_service_real_api():
    """Test SERP API integration with real API calls."""
    # Initialize the service with real API key from environment
    service = SerpService(api_key=os.environ.get('SERPAPI_KEY'))
    
    # Test a basic search
    results = await service.search("test search")
    
    # Verify we got results
    assert isinstance(results, dict)
    assert "search_metadata" in results
    assert "organic_results" in results or "error" not in results, f"API Error: {results.get('error', 'Unknown error')}"

@pytest.mark.asyncio
async def test_pagespeed_insights_real_api():
    """Test PageSpeed Insights API integration with real API calls."""
    # Initialize the service with real API key from environment
    service = PageSpeedInsightsService(api_key=os.environ.get('PAGESPEED_API_KEY'))
    
    # Test page speed analysis
    results = await service.analyze(f"https://{TEST_DOMAIN}")
    
    # Verify we got results
    assert isinstance(results, dict)
    assert "lighthouseResult" in results or "error" not in results, f"API Error: {results.get('error', 'Unknown error')}"

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="Google Search Console authentication required")
async def test_seo_service_integration_real_apis(db_session: AsyncSession, test_data):
    """Test the integration of SEO service with real APIs."""
    # Get test data from fixture
    user, company, domain = test_data
    
    # Initialize the SEO service with real API keys
    seo_service = SEOService(db=db_session)
    
    # Test getting domain metrics with real API calls
    results = await seo_service.get_domain_metrics(TEST_DOMAIN)
    
    # Verify we got results
    assert isinstance(results, dict)
    
    # Check that we have the expected keys in the results
    expected_keys = ['overview', 'traffic', 'backlinks', 'performance', 'mobile_usability']
    for key in expected_keys:
        assert key in results, f"Missing expected key in results: {key}"
    
    # Verify performance metrics if available
    if 'performance' in results and results['performance']:
        assert 'score' in results['performance'], "Missing performance score"
        assert 0 <= results['performance']['score'] <= 1, "Performance score out of range"
    
    # Verify we have some data in the results
    assert any(results.values()), "No data returned from any service"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_seo_service_keyword_ranking_analysis(db_session: AsyncSession, test_data):
    """Test keyword ranking analysis with real API calls."""
    # Get test data from fixture
    user, company, domain = test_data
    
    # Initialize the SERP service with real API key
    serp_service = SerpService(api_key=os.environ.get('SERPAPI_KEY'))
    
    # Test with a known keyword and domain
    keyword = 'digital marketing'
    domain = 'hubspot.com'  # Well-known marketing site
    
    # Get rankings
    rankings = await serp_service.analyze_rankings(db_session, domain, [keyword])
    
    # Verify we got results
    assert isinstance(rankings, dict)
    assert keyword in rankings, f"No ranking data for keyword: {keyword}"
    
    # Position might be None if the domain isn't in the top 100
    position = rankings[keyword]
    if position is not None:
        assert isinstance(position, int), f"Expected position to be an integer, got {type(position)}"
        assert position > 0, f"Expected position to be positive, got {position}"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_seo_service_serp_features_analysis(db_session: AsyncSession, test_data):
    """Test SERP features analysis with real API calls."""
    # Get test data from fixture
    user, company, domain = test_data
    
    # Initialize the SERP service with real API key
    serp_service = SerpService(api_key=os.environ.get('SERPAPI_KEY'))
    
    # Test with a keyword that typically has rich results
    keyword = 'best seo tools 2024'
    
    # Get SERP features
    features = await serp_service.analyze_serp_features(keyword)
    
    # Verify we got results
    assert isinstance(features, dict)
    
    # Check for common SERP features
    has_features = any(features.get(feature) for feature in 
                      ['featured_snippet', 'knowledge_graph', 'related_questions', 'top_stories'])
    assert has_features, f"No SERP features found for keyword: {keyword}"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_seo_service_store_and_retrieve_metrics(db_session: AsyncSession, test_data):
    """Test storing and retrieving SEO metrics using ContentAsset model."""
    # Get test data from fixture
    user, company, domain = test_data
    
    # Initialize the SEO service with real API keys
    seo_service = SEOService(db=db_session)
    
    # Test storing metrics in ContentAsset
    test_metrics = {
        'overview': {'authority_score': 75, 'trust_metrics': {'trust_flow': 50}},
        'traffic': {'organic_traffic': 10000, 'sessions': 15000},
        'backlinks': {'total': 5000, 'referring_domains': 350},
        'performance': {'score': 0.85, 'first_contentful_paint': 1.8},
        'mobile_usability': {'passed': True, 'issues': []},
        'last_updated': datetime.utcnow().isoformat()
    }
    
    # Store metrics in ContentAsset's social_engagement JSON field
    content_asset = ContentAsset(
        url=f"https://{domain.domain}",
        topic="SEO Performance Metrics",
        style="analytical",
        format="metrics",
        google_ranking=1,
        social_engagement=test_metrics,  # Using social_engagement JSON field to store metrics
        likeability_score=0.85,
        market="global"
    )
    db_session.add(content_asset)
    await db_session.commit()
    await db_session.refresh(content_asset)
    
    # Retrieve metrics
    result = await db_session.execute(
        select(ContentAsset)
        .where(ContentAsset.url == f"https://{domain.domain}")
        .order_by(ContentAsset.id.desc())
    )
    latest_data = result.scalars().first()
    
    # Verify we got the data back
    assert latest_data is not None, "No SEO data found in database"
    assert latest_data.social_engagement['overview']['authority_score'] == 75
    assert latest_data.social_engagement['traffic']['organic_traffic'] == 10000

# Add this to run the tests with: pytest tests/integration/test_seo_real_api.py -v --log-cli-level=INFO
