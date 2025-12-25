"""Extended unit tests for SEO Content Walker Agent.

Tests TF-IDF extraction, phrase detection, competitor identification,
and content opportunity generation with mocked dependencies.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List
from datetime import datetime
import uuid

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
from tests.fixtures.brand_analysis_fixtures import (
    SAMPLE_QUESTIONNAIRE_COMPLETE,
    MOCK_WEBSITE_CRAWL_DATA,
    SAMPLE_KEYWORDS,
    SAMPLE_COMPETITORS,
    MOCK_SERP_RESULTS
)
from tests.mocks.http_mock import MockHTTPSession, create_mock_html_page


@pytest.mark.unit
@pytest.mark.asyncio
class TestSEOContentWalkerExtended:
    """Extended tests for SEO Content Walker Agent."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock()
        db.query = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        return db

    @pytest.fixture
    def agent(self, mock_db):
        """Create SEO Content Walker agent with mock dependencies."""
        return SEOContentWalkerAgent(db=mock_db, cache=None)

    @pytest.fixture
    def questionnaire(self):
        """Create sample questionnaire."""
        return BrandAnalysisQuestionnaire.from_dict(SAMPLE_QUESTIONNAIRE_COMPLETE)

    # TF-IDF Keyword Extraction Tests

    def test_extract_tfidf_keywords_basic(self, agent):
        """Test TF-IDF keyword extraction."""
        text = """
        Email marketing is the best way to reach customers.
        Marketing automation helps you scale your email marketing efforts.
        Our email marketing platform provides powerful automation tools.
        """

        keywords = agent._extract_tfidf_keywords(text, max_features=5)

        assert len(keywords) > 0
        assert all('keyword' in kw for kw in keywords)
        assert all('source' in kw for kw in keywords)
        assert all('relevance_score' in kw for kw in keywords)
        assert all(kw['source'] == KeywordSource.NLP_EXTRACTION for kw in keywords)

    def test_extract_tfidf_keywords_filters_short_words(self, agent):
        """Test that TF-IDF filters out short words."""
        text = "a an the is at to by in on it"

        keywords = agent._extract_tfidf_keywords(text, max_features=10)

        # Should filter out stop words and short words
        assert all(len(kw['keyword']) > 2 for kw in keywords)

    def test_extract_tfidf_keywords_empty_text(self, agent):
        """Test TF-IDF with empty text."""
        keywords = agent._extract_tfidf_keywords("", max_features=5)

        # Should return empty list or handle gracefully
        assert keywords == []

    def test_extract_phrases_bigrams_trigrams(self, agent):
        """Test phrase extraction (bi-grams and tri-grams)."""
        text = """
        Email marketing automation platform for small businesses.
        Best email marketing software for growing companies.
        Marketing automation tools help you succeed.
        """

        phrases = agent._extract_phrases(text)

        assert len(phrases) > 0
        # Should have multi-word phrases
        assert any(len(p['keyword'].split()) >= 2 for p in phrases)
        assert all(p['source'] == KeywordSource.NLP_EXTRACTION for p in phrases)

    @pytest.mark.asyncio
    async def test_extract_keywords_combines_tfidf_and_phrases(self, agent, questionnaire):
        """Test that extract_keywords combines TF-IDF and phrases."""
        site_data = MOCK_WEBSITE_CRAWL_DATA

        keywords = await agent.extract_keywords(site_data, questionnaire)

        assert len(keywords) > 0
        assert len(keywords) <= agent.max_keywords

        # Should include user-provided keywords if found in content
        if questionnaire.target_keywords:
            keyword_texts = [kw['keyword'].lower() for kw in keywords]
            for target in questionnaire.target_keywords:
                # Check if any target keyword is in results (may be partial match)
                assert any(target.lower() in kw_text for kw_text in keyword_texts)

    @pytest.mark.asyncio
    async def test_extract_keywords_weights_headings(self, agent, questionnaire):
        """Test that headings are weighted more heavily."""
        site_data = {
            'pages': [
                {
                    'url': 'https://test.com',
                    'title': 'Test',
                    'content': 'random content here',
                    'meta_description': '',
                    'headings': ['email marketing', 'email marketing', 'email marketing']
                }
            ]
        }

        keywords = await agent.extract_keywords(site_data, questionnaire)

        # 'email marketing' should appear due to heading weight
        keyword_texts = [kw['keyword'].lower() for kw in keywords]
        assert any('email' in kw or 'marketing' in kw for kw in keyword_texts)

    # Web Crawling Tests

    @pytest.mark.asyncio
    async def test_crawl_website_basic(self, agent):
        """Test basic website crawling."""
        url = 'https://testsite.com'

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = MockHTTPSession({
                url: create_mock_html_page(
                    'Test Site',
                    ['Heading 1', 'Heading 2'],
                    'Page content here',
                    'Test description'
                )
            })
            mock_session_class.return_value = mock_session

            result = await agent.crawl_website(url)

            assert 'pages' in result
            assert 'total_pages' in result
            assert 'base_url' in result
            assert 'domain' in result
            assert result['base_url'] == url

    @pytest.mark.asyncio
    async def test_crawl_website_respects_max_pages(self, agent):
        """Test that crawling respects max_pages_per_domain limit."""
        agent.max_pages_per_domain = 2

        url = 'https://testsite.com'

        with patch('aiohttp.ClientSession') as mock_session_class:
            # Create responses for multiple pages
            mock_responses = {
                f'https://testsite.com/page{i}': create_mock_html_page(
                    f'Page {i}',
                    [f'Heading {i}'],
                    f'Content {i}'
                )
                for i in range(10)
            }
            mock_responses[url] = create_mock_html_page('Home', ['Home'], 'Home content')

            mock_session = MockHTTPSession(mock_responses)
            mock_session_class.return_value = mock_session

            result = await agent.crawl_website(url)

            # Should not exceed max pages
            assert result['total_pages'] <= agent.max_pages_per_domain

    @pytest.mark.asyncio
    async def test_crawl_website_extracts_meta_description(self, agent):
        """Test meta description extraction."""
        url = 'https://testsite.com'
        test_description = 'This is the meta description'

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = MockHTTPSession({
                url: create_mock_html_page(
                    'Test',
                    ['Heading'],
                    'Content',
                    test_description
                )
            })
            mock_session_class.return_value = mock_session

            result = await agent.crawl_website(url)

            assert len(result['pages']) > 0
            page = result['pages'][0]
            assert page['meta_description'] == test_description

    @pytest.mark.asyncio
    async def test_crawl_website_extracts_headings(self, agent):
        """Test heading extraction."""
        url = 'https://testsite.com'
        test_headings = ['Main Heading', 'Subheading 1', 'Subheading 2']

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = MockHTTPSession({
                url: create_mock_html_page(
                    'Test',
                    test_headings,
                    'Content'
                )
            })
            mock_session_class.return_value = mock_session

            result = await agent.crawl_website(url)

            page = result['pages'][0]
            assert page['headings'] == test_headings

    # Competitor Identification Tests

    @pytest.mark.asyncio
    async def test_identify_competitors_from_serp(self, agent):
        """Test competitor identification from SERP data."""
        serp_data = MOCK_SERP_RESULTS

        competitors = await agent.identify_competitors(serp_data, known_competitors=[])

        assert len(competitors) > 0
        assert len(competitors) <= agent.max_competitors

        # Check competitor structure
        for comp in competitors:
            assert 'domain' in comp
            assert 'relevance_score' in comp
            assert 'category' in comp
            assert comp['category'] in [cat.value for cat in CompetitorCategory]

    @pytest.mark.asyncio
    async def test_identify_competitors_categorization(self, agent):
        """Test that competitors are properly categorized."""
        # Create SERP data where one domain appears frequently
        serp_data = {}
        for i in range(20):
            serp_data[f'keyword{i}'] = {
                'keyword': f'keyword{i}',
                'ranking_domains': ['frequent.com'] * 5 + ['occasional.com', 'rare.com']
            }

        competitors = await agent.identify_competitors(serp_data, known_competitors=[])

        # 'frequent.com' should be primary
        frequent_comp = next((c for c in competitors if c['domain'] == 'frequent.com'), None)
        assert frequent_comp is not None
        assert frequent_comp['category'] == CompetitorCategory.PRIMARY

    @pytest.mark.asyncio
    async def test_identify_competitors_includes_known(self, agent):
        """Test that known competitors are included."""
        serp_data = {
            'keyword1': {
                'keyword': 'keyword1',
                'ranking_domains': ['competitor1.com', 'competitor2.com']
            }
        }

        known_competitors = ['mailchimp.com', 'hubspot.com']

        competitors = await agent.identify_competitors(serp_data, known_competitors)

        # Known competitors should be in results
        competitor_domains = [c['domain'] for c in competitors]
        assert 'mailchimp.com' in competitor_domains
        assert 'hubspot.com' in competitor_domains

    @pytest.mark.asyncio
    async def test_identify_competitors_calculates_overlap(self, agent):
        """Test overlap percentage calculation."""
        serp_data = {}
        for i in range(10):
            serp_data[f'keyword{i}'] = {
                'keyword': f'keyword{i}',
                'ranking_domains': ['test.com']
            }

        competitors = await agent.identify_competitors(serp_data, known_competitors=[])

        # test.com appears in all 10 keywords, so overlap should be 100%
        test_comp = next((c for c in competitors if c['domain'] == 'test.com'), None)
        assert test_comp is not None
        assert test_comp['overlap_percentage'] == 100.0

    # Content Opportunity Generation Tests

    @pytest.mark.asyncio
    async def test_generate_content_opportunities(self, agent):
        """Test content opportunity generation."""
        site_data = MOCK_WEBSITE_CRAWL_DATA
        keywords = SAMPLE_KEYWORDS[:10]
        competitors = SAMPLE_COMPETITORS

        opportunities = await agent.generate_content_opportunities(
            site_data,
            keywords,
            competitors
        )

        assert len(opportunities) > 0
        assert len(opportunities) <= 10  # Agent returns top 10

        # Check opportunity structure
        for opp in opportunities:
            assert 'topic' in opp
            assert 'gap_type' in opp
            assert 'priority' in opp
            assert opp['gap_type'] in [gt.value for gt in GapType]
            assert opp['priority'] in [p.value for p in ContentPriority]

    @pytest.mark.asyncio
    async def test_content_opportunities_identifies_gaps(self, agent):
        """Test that content opportunities identify missing content."""
        site_data = {
            'pages': [
                {
                    'url': 'https://test.com',
                    'title': 'Test',
                    'content': 'Some unrelated content here',
                    'meta_description': '',
                    'headings': []
                }
            ]
        }

        keywords = [
            {
                'keyword': 'unique keyword not in content',
                'source': 'nlp_extraction',
                'relevance_score': 0.8,
                'search_volume': 5000,
                'difficulty': 40.0
            }
        ]

        opportunities = await agent.generate_content_opportunities(
            site_data,
            keywords,
            []
        )

        # Should identify missing content for the unique keyword
        assert len(opportunities) > 0
        assert any(opp['gap_type'] == GapType.MISSING_CONTENT for opp in opportunities)

    @pytest.mark.asyncio
    async def test_content_opportunities_priority_calculation(self, agent):
        """Test content opportunity priority calculation."""
        site_data = {'pages': [{'url': 'https://test.com', 'content': '', 'headings': []}]}

        # High relevance, low coverage = high priority
        high_priority_kw = {
            'keyword': 'high priority keyword',
            'source': 'nlp_extraction',
            'relevance_score': 0.9,
            'search_volume': 10000,
            'difficulty': 30.0
        }

        opportunities = await agent.generate_content_opportunities(
            site_data,
            [high_priority_kw],
            []
        )

        assert len(opportunities) > 0
        assert opportunities[0]['priority'] == ContentPriority.HIGH

    # Helper Method Tests

    def test_extract_meta_description(self, agent):
        """Test meta description extraction from BeautifulSoup."""
        from bs4 import BeautifulSoup

        html = '<html><head><meta name="description" content="Test description"></head></html>'
        soup = BeautifulSoup(html, 'html.parser')

        description = agent._extract_meta_description(soup)
        assert description == 'Test description'

    def test_extract_meta_description_missing(self, agent):
        """Test meta description extraction when missing."""
        from bs4 import BeautifulSoup

        html = '<html><head></head></html>'
        soup = BeautifulSoup(html, 'html.parser')

        description = agent._extract_meta_description(soup)
        assert description == ''

    def test_extract_headings(self, agent):
        """Test heading extraction from BeautifulSoup."""
        from bs4 import BeautifulSoup

        html = '''
        <html><body>
            <h1>Heading 1</h1>
            <h2>Heading 2</h2>
            <h3>Heading 3</h3>
        </body></html>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        headings = agent._extract_headings(soup)
        assert headings == ['Heading 1', 'Heading 2', 'Heading 3']

    def test_extract_brand_name(self, agent):
        """Test brand name extraction from domain."""
        assert agent._extract_brand_name('mailchimp.com') == 'Mailchimp'
        assert agent._extract_brand_name('test.com') == 'Test'
        assert agent._extract_brand_name('example.io') == 'Example'

    def test_calculate_priority(self, agent):
        """Test content priority calculation."""
        # High relevance + low coverage = high priority
        priority = agent._calculate_priority(relevance=0.8, coverage=1)
        assert priority == ContentPriority.HIGH

        # Medium relevance = medium priority
        priority = agent._calculate_priority(relevance=0.5, coverage=2)
        assert priority == ContentPriority.MEDIUM

        # Low relevance = low priority
        priority = agent._calculate_priority(relevance=0.2, coverage=5)
        assert priority == ContentPriority.LOW

    def test_estimate_search_volume(self, agent):
        """Test search volume estimation."""
        # Placeholder implementation - longer keywords = higher volume
        volume1 = agent._estimate_search_volume('test')
        volume2 = agent._estimate_search_volume('test keyword phrase')

        assert volume2 > volume1

    def test_estimate_difficulty(self, agent):
        """Test difficulty estimation."""
        # Placeholder implementation - longer keywords = higher difficulty
        diff1 = agent._estimate_difficulty('test')
        diff2 = agent._estimate_difficulty('longer keyword phrase')

        assert diff2 >= diff1

    @pytest.mark.asyncio
    async def test_save_keywords(self, agent, mock_db):
        """Test saving keywords to database."""
        job_id = str(uuid.uuid4())
        keywords = SAMPLE_KEYWORDS[:3]

        await agent._save_keywords(job_id, keywords)

        # Should add and commit
        assert mock_db.add.call_count == len(keywords)
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_save_competitors(self, agent, mock_db):
        """Test saving competitors to database."""
        job_id = str(uuid.uuid4())
        competitors = SAMPLE_COMPETITORS[:2]

        await agent._save_competitors(job_id, competitors)

        assert mock_db.add.call_count == len(competitors)
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_save_content_opportunities(self, agent, mock_db):
        """Test saving content opportunities to database."""
        job_id = str(uuid.uuid4())
        opportunities = [
            {
                'topic': 'Test topic',
                'gap_type': GapType.MISSING_CONTENT,
                'priority': ContentPriority.HIGH,
                'traffic_potential': 5000,
                'difficulty': 40.0,
                'recommended_format': 'blog'
            }
        ]

        await agent._save_content_opportunities(job_id, opportunities)

        assert mock_db.add.called
        assert mock_db.commit.called
