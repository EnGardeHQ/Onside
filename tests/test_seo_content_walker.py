"""Unit tests for SEO Content Walker Agent.

Tests keyword extraction, competitor identification, content opportunity generation,
and web crawling functionality with mocked external HTTP calls.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List
from datetime import datetime

from src.agents.seo_content_walker import (
    SEOContentWalkerAgent,
    BrandAnalysisQuestionnaire
)
from src.models.brand_analysis import (
    BrandAnalysisJob,
    DiscoveredKeyword,
    IdentifiedCompetitor,
    ContentOpportunity,
    AnalysisStatus,
    KeywordSource,
    CompetitorCategory,
    GapType,
    ContentPriority
)


@pytest.mark.unit
class TestBrandAnalysisQuestionnaire:
    """Test BrandAnalysisQuestionnaire data class."""

    def test_create_questionnaire_from_dict(self):
        """Test creating questionnaire from dictionary."""
        data = {
            'brand_name': 'Test Brand',
            'primary_website': 'https://testbrand.com',
            'industry': 'Technology',
            'target_markets': ['USA', 'Canada'],
            'products_services': ['Software', 'Consulting'],
            'known_competitors': ['competitor.com'],
            'target_keywords': ['keyword1', 'keyword2']
        }

        questionnaire = BrandAnalysisQuestionnaire.from_dict(data)

        assert questionnaire.brand_name == 'Test Brand'
        assert questionnaire.primary_website == 'https://testbrand.com'
        assert questionnaire.industry == 'Technology'
        assert questionnaire.target_markets == ['USA', 'Canada']
        assert questionnaire.products_services == ['Software', 'Consulting']
        assert questionnaire.known_competitors == ['competitor.com']
        assert questionnaire.target_keywords == ['keyword1', 'keyword2']

    def test_questionnaire_to_dict(self):
        """Test converting questionnaire to dictionary."""
        questionnaire = BrandAnalysisQuestionnaire(
            brand_name='Test Brand',
            primary_website='https://testbrand.com',
            industry='Technology',
            target_markets=['USA'],
            products_services=['Software'],
            known_competitors=['competitor.com'],
            target_keywords=['keyword1']
        )

        data = questionnaire.to_dict()

        assert data['brand_name'] == 'Test Brand'
        assert data['primary_website'] == 'https://testbrand.com'
        assert data['industry'] == 'Technology'
        assert data['target_markets'] == ['USA']
        assert data['products_services'] == ['Software']
        assert data['known_competitors'] == ['competitor.com']
        assert data['target_keywords'] == ['keyword1']

    def test_questionnaire_default_values(self):
        """Test questionnaire with default values."""
        questionnaire = BrandAnalysisQuestionnaire(
            brand_name='Test',
            primary_website='https://test.com',
            industry='Tech'
        )

        assert questionnaire.target_markets == []
        assert questionnaire.products_services == []
        assert questionnaire.known_competitors == []
        assert questionnaire.target_keywords == []


@pytest.mark.unit
class TestSEOContentWalkerAgent:
    """Test SEOContentWalkerAgent core functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock()
        db.query = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        return db

    @pytest.fixture
    def agent(self, mock_db):
        """Create SEO Content Walker Agent instance."""
        return SEOContentWalkerAgent(mock_db)

    def test_agent_initialization(self, agent):
        """Test agent initialization with default values."""
        assert agent.max_pages_per_domain == 10
        assert agent.max_keywords == 50
        assert agent.max_competitors == 15

    def test_extract_meta_description(self, agent):
        """Test meta description extraction from HTML."""
        from bs4 import BeautifulSoup

        html = '<html><head><meta name="description" content="Test description"></head></html>'
        soup = BeautifulSoup(html, 'html.parser')

        description = agent._extract_meta_description(soup)
        assert description == "Test description"

    def test_extract_meta_description_missing(self, agent):
        """Test meta description extraction when meta tag is missing."""
        from bs4 import BeautifulSoup

        html = '<html><head></head></html>'
        soup = BeautifulSoup(html, 'html.parser')

        description = agent._extract_meta_description(soup)
        assert description == ""

    def test_extract_headings(self, agent):
        """Test extracting headings from HTML."""
        from bs4 import BeautifulSoup

        html = '''
        <html>
            <body>
                <h1>Main Heading</h1>
                <h2>Subheading 1</h2>
                <h3>Subheading 2</h3>
                <h2>Another Subheading</h2>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        headings = agent._extract_headings(soup)
        assert len(headings) == 4
        assert "Main Heading" in headings
        assert "Subheading 1" in headings
        assert "Subheading 2" in headings
        assert "Another Subheading" in headings

    def test_extract_brand_name(self, agent):
        """Test extracting brand name from domain."""
        assert agent._extract_brand_name("testcompany.com") == "Testcompany"
        assert agent._extract_brand_name("my-brand.io") == "My-brand"
        assert agent._extract_brand_name("example.co.uk") == "Example"

    def test_calculate_priority_high(self, agent):
        """Test calculating high priority for content."""
        priority = agent._calculate_priority(relevance=0.8, coverage=1)
        assert priority == ContentPriority.HIGH

    def test_calculate_priority_medium(self, agent):
        """Test calculating medium priority for content."""
        priority = agent._calculate_priority(relevance=0.5, coverage=2)
        assert priority == ContentPriority.MEDIUM

    def test_calculate_priority_low(self, agent):
        """Test calculating low priority for content."""
        priority = agent._calculate_priority(relevance=0.3, coverage=5)
        assert priority == ContentPriority.LOW

    def test_estimate_search_volume(self, agent):
        """Test estimating search volume placeholder."""
        volume = agent._estimate_search_volume("test keyword")
        assert volume == 2000  # 2 words * 1000

        volume = agent._estimate_search_volume("test")
        assert volume == 1000  # 1 word * 1000

    def test_estimate_difficulty(self, agent):
        """Test estimating keyword difficulty placeholder."""
        difficulty = agent._estimate_difficulty("seo")
        assert difficulty == 15.0  # 3 chars * 5

        difficulty = agent._estimate_difficulty("very long keyword phrase")
        assert difficulty == 100.0  # Capped at 100


@pytest.mark.unit
class TestKeywordExtraction:
    """Test keyword extraction functionality."""

    @pytest.fixture
    def agent(self):
        """Create agent with mock db."""
        return SEOContentWalkerAgent(Mock())

    @pytest.mark.asyncio
    async def test_extract_keywords_from_site_data(self, agent):
        """Test extracting keywords from crawled site data."""
        site_data = {
            'pages': [
                {
                    'url': 'https://test.com',
                    'title': 'Test Page',
                    'content': 'software development testing automation quality assurance ' * 10,
                    'headings': ['Software Development', 'Quality Assurance'],
                    'meta_description': 'Best software development practices'
                }
            ],
            'total_pages': 1,
            'domain': 'test.com'
        }

        questionnaire = BrandAnalysisQuestionnaire(
            brand_name='Test',
            primary_website='https://test.com',
            industry='Technology',
            target_keywords=['automation', 'testing']
        )

        keywords = await agent.extract_keywords(site_data, questionnaire)

        # Should extract keywords
        assert len(keywords) > 0
        assert all(isinstance(kw, dict) for kw in keywords)
        assert all('keyword' in kw for kw in keywords)
        assert all('source' in kw for kw in keywords)
        assert all('relevance_score' in kw for kw in keywords)

        # Should include user-provided keywords if found in content
        keyword_texts = [kw['keyword'] for kw in keywords]
        assert 'automation' in keyword_texts or 'testing' in keyword_texts

    def test_extract_tfidf_keywords(self, agent):
        """Test TF-IDF keyword extraction."""
        text = "software development testing automation quality assurance " * 20

        keywords = agent._extract_tfidf_keywords(text, max_features=10)

        assert len(keywords) <= 10
        assert all(isinstance(kw, dict) for kw in keywords)
        assert all('keyword' in kw for kw in keywords)
        assert all('source' in kw for kw in keywords)
        assert all(kw['source'] == KeywordSource.NLP_EXTRACTION for kw in keywords)
        assert all(kw['relevance_score'] > 0 for kw in keywords)
        assert all(len(kw['keyword']) > 2 for kw in keywords)  # No short words

    def test_extract_phrases(self, agent):
        """Test extracting multi-word phrases."""
        text = "software development software testing quality assurance test automation " * 10

        phrases = agent._extract_phrases(text)

        assert len(phrases) <= 20
        assert all(isinstance(phrase, dict) for phrase in phrases)
        assert all('keyword' in phrase for phrase in phrases)
        assert all(len(phrase['keyword'].split()) >= 2 for phrase in phrases)  # Multi-word
        assert all(phrase['source'] == KeywordSource.NLP_EXTRACTION for phrase in phrases)

    def test_extract_keywords_empty_content(self, agent):
        """Test extracting keywords from empty content."""
        text = ""
        keywords = agent._extract_tfidf_keywords(text)
        assert keywords == []


@pytest.mark.unit
class TestCompetitorIdentification:
    """Test competitor identification functionality."""

    @pytest.fixture
    def agent(self):
        """Create agent with mock db."""
        return SEOContentWalkerAgent(Mock())

    @pytest.mark.asyncio
    async def test_identify_competitors_from_serp(self, agent):
        """Test identifying competitors from SERP data."""
        serp_data = {
            'keyword1': {
                'ranking_domains': ['competitor1.com', 'competitor2.com', 'competitor1.com']
            },
            'keyword2': {
                'ranking_domains': ['competitor1.com', 'competitor3.com']
            },
            'keyword3': {
                'ranking_domains': ['competitor2.com', 'competitor1.com']
            }
        }

        competitors = await agent.identify_competitors(serp_data)

        assert len(competitors) > 0
        # competitor1.com should have highest count (4 appearances)
        top_competitor = competitors[0]
        assert 'domain' in top_competitor
        assert 'relevance_score' in top_competitor
        assert 'category' in top_competitor
        assert top_competitor['domain'] == 'competitor1.com'

    @pytest.mark.asyncio
    async def test_identify_competitors_with_known_competitors(self, agent):
        """Test adding known competitors to identified list."""
        serp_data = {
            'keyword1': {
                'ranking_domains': ['competitor1.com']
            }
        }

        known_competitors = ['knowncomp.com', 'anotherknown.com']
        competitors = await agent.identify_competitors(serp_data, known_competitors)

        domains = [c['domain'] for c in competitors]
        assert 'knowncomp.com' in domains
        assert 'anotherknown.com' in domains

    @pytest.mark.asyncio
    async def test_competitor_categorization(self, agent):
        """Test competitor categorization by relevance."""
        # Create SERP data with varying frequency
        serp_data = {}
        for i in range(20):
            serp_data[f'keyword{i}'] = {
                'ranking_domains': ['primary_competitor.com'] * 3 +
                                   ['secondary_competitor.com'] * 2 +
                                   ['emerging_competitor.com']
            }

        competitors = await agent.identify_competitors(serp_data)

        # Find each competitor
        primary = next((c for c in competitors if c['domain'] == 'primary_competitor.com'), None)
        secondary = next((c for c in competitors if c['domain'] == 'secondary_competitor.com'), None)

        assert primary is not None
        assert primary['category'] == CompetitorCategory.PRIMARY
        assert secondary is not None


@pytest.mark.unit
class TestContentOpportunities:
    """Test content opportunity generation."""

    @pytest.fixture
    def agent(self):
        """Create agent with mock db."""
        return SEOContentWalkerAgent(Mock())

    @pytest.mark.asyncio
    async def test_generate_content_opportunities(self, agent):
        """Test generating content opportunities."""
        site_data = {
            'pages': [
                {
                    'url': 'https://test.com/page1',
                    'content': 'existing content about topic A'
                },
                {
                    'url': 'https://test.com/page2',
                    'content': 'more content about topic A'
                }
            ]
        }

        keywords = [
            {'keyword': 'topic A', 'relevance_score': 0.8, 'search_volume': 1000, 'difficulty': 50},
            {'keyword': 'topic B', 'relevance_score': 0.7, 'search_volume': 2000, 'difficulty': 60},
            {'keyword': 'topic C', 'relevance_score': 0.6, 'search_volume': 1500, 'difficulty': 40},
        ]

        competitors = [
            {'domain': 'competitor.com', 'relevance_score': 0.8}
        ]

        opportunities = await agent.generate_content_opportunities(
            site_data, keywords, competitors
        )

        assert len(opportunities) > 0
        assert all(isinstance(opp, dict) for opp in opportunities)
        assert all('topic' in opp for opp in opportunities)
        assert all('gap_type' in opp for opp in opportunities)
        assert all('priority' in opp for opp in opportunities)
        assert all('recommended_format' in opp for opp in opportunities)

    @pytest.mark.asyncio
    async def test_opportunities_identify_missing_content(self, agent):
        """Test identifying missing content opportunities."""
        site_data = {
            'pages': [
                {'url': 'https://test.com', 'content': 'unrelated content'}
            ]
        }

        keywords = [
            {'keyword': 'missing topic', 'relevance_score': 0.9, 'search_volume': 5000, 'difficulty': 45}
        ]

        opportunities = await agent.generate_content_opportunities(site_data, keywords, [])

        # Should identify missing content for "missing topic"
        assert len(opportunities) > 0
        assert opportunities[0]['gap_type'] == GapType.MISSING_CONTENT


@pytest.mark.unit
class TestWebCrawling:
    """Test web crawling functionality."""

    @pytest.fixture
    def agent(self):
        """Create agent with mock db."""
        return SEOContentWalkerAgent(Mock())

    @pytest.mark.asyncio
    async def test_crawl_website_mock(self, agent):
        """Test website crawling with mocked HTTP responses."""
        mock_html = '''
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="Test description">
            </head>
            <body>
                <h1>Main Heading</h1>
                <p>Test content with keywords software development testing</p>
                <a href="/page2">Link to page 2</a>
            </body>
        </html>
        '''

        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=mock_html)
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await agent.crawl_website('https://test.com')

            assert 'pages' in result
            assert 'total_pages' in result
            assert 'domain' in result
            assert result['domain'] == 'test.com'
            assert len(result['pages']) > 0

            # Check extracted content
            page = result['pages'][0]
            assert 'title' in page
            assert 'content' in page
            assert 'headings' in page
            assert 'url' in page

    @pytest.mark.asyncio
    async def test_crawl_website_handles_errors(self, agent):
        """Test website crawling handles HTTP errors gracefully."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock error response
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await agent.crawl_website('https://test.com')

            # Should return empty result without crashing
            assert 'pages' in result
            assert result['total_pages'] == 0


@pytest.mark.unit
class TestAnalyzeBrandWorkflow:
    """Test complete brand analysis workflow."""

    @pytest.fixture
    def agent(self, mock_db_session):
        """Create agent with mock db."""
        return SEOContentWalkerAgent(mock_db_session)

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        db = Mock()

        # Mock job query
        mock_job = Mock(spec=BrandAnalysisJob)
        mock_job.id = 'test-job-id'
        mock_job.status = AnalysisStatus.INITIATED
        mock_job.progress = 0

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_job
        db.query.return_value = mock_query

        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()

        return db

    @pytest.mark.asyncio
    async def test_analyze_serp_placeholder(self, agent):
        """Test SERP analysis placeholder functionality."""
        keywords = [
            {'keyword': 'test keyword 1', 'relevance_score': 0.8},
            {'keyword': 'test keyword 2', 'relevance_score': 0.7}
        ]

        serp_results = await agent.analyze_serp(keywords)

        assert isinstance(serp_results, dict)
        assert len(serp_results) == 2
        assert 'test keyword 1' in serp_results
        assert 'test keyword 2' in serp_results

        # Check structure
        for keyword, data in serp_results.items():
            assert 'keyword' in data
            assert 'search_volume' in data
            assert 'difficulty' in data
            assert 'ranking_domains' in data
            assert 'serp_features' in data
