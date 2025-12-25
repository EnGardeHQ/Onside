"""Unit tests for Data Transformer service.

Tests keyword and competitor transformation between Onside and En Garde formats,
including validation, enrichment, and edge case handling.
"""
import pytest
from typing import Dict, Any

from src.services.data_transformer import (
    DataTransformer,
    TransformationError,
    EnGardeKeywordSchema,
    EnGardeCompetitorSchema,
    OnsideKeywordSchema,
    OnsideCompetitorSchema
)
from src.models.brand_analysis import KeywordSource, CompetitorCategory


@pytest.mark.unit
class TestDataTransformer:
    """Test DataTransformer service."""

    @pytest.fixture
    def transformer(self):
        """Create DataTransformer instance."""
        return DataTransformer()

    @pytest.fixture
    def sample_onside_keyword(self):
        """Sample Onside keyword data."""
        return {
            'keyword': 'email marketing automation',
            'source': 'nlp_extraction',
            'search_volume': 12000,
            'difficulty': 65.5,
            'relevance_score': 0.87,
            'current_ranking': 15,
            'serp_features': {'featured_snippet': True, 'paa': True},
            'confirmed': False
        }

    @pytest.fixture
    def sample_onside_competitor(self):
        """Sample Onside competitor data."""
        return {
            'domain': 'mailchimp.com',
            'name': 'Mailchimp',
            'relevance_score': 0.92,
            'category': 'primary',
            'overlap_percentage': 78.5,
            'keyword_overlap': ['email marketing', 'marketing automation', 'crm'],
            'content_similarity': 0.75,
            'confirmed': False
        }

    # Keyword Transformation Tests

    def test_transform_keyword_basic(self, transformer, sample_onside_keyword):
        """Test basic keyword transformation."""
        result = transformer.transform_keyword_to_engarde(
            sample_onside_keyword,
            enrich=False
        )

        assert isinstance(result, EnGardeKeywordSchema)
        assert result.keyword == 'email marketing automation'
        assert result.search_volume == 12000
        assert result.difficulty == 65.5
        assert result.current_rank == 15
        assert result.intent == 'informational'
        assert result.priority in ['high', 'medium', 'low']

    def test_transform_keyword_with_enrichment(self, transformer, sample_onside_keyword):
        """Test keyword transformation with enrichment."""
        result = transformer.transform_keyword_to_engarde(
            sample_onside_keyword,
            enrich=True
        )

        assert result.cpc is not None
        assert result.cpc > 0
        # Should set target rank based on current rank
        if result.current_rank and result.current_rank > 10:
            assert result.target_rank <= 10

    def test_transform_keyword_priority_calculation(self, transformer):
        """Test priority calculation for keywords."""
        # High priority: high relevance + high volume + low difficulty
        high_priority_kw = {
            'keyword': 'test keyword',
            'source': 'nlp_extraction',
            'search_volume': 50000,
            'difficulty': 25.0,
            'relevance_score': 0.95,
            'current_ranking': None
        }

        result = transformer.transform_keyword_to_engarde(high_priority_kw, enrich=False)
        assert result.priority == 'high'

        # Low priority: low relevance + low volume + high difficulty
        low_priority_kw = {
            'keyword': 'test keyword',
            'source': 'nlp_extraction',
            'search_volume': 50,
            'difficulty': 90.0,
            'relevance_score': 0.2,
            'current_ranking': None
        }

        result = transformer.transform_keyword_to_engarde(low_priority_kw, enrich=False)
        assert result.priority == 'low'

    def test_transform_keyword_intent_mapping(self, transformer):
        """Test intent mapping from source."""
        sources_and_intents = {
            'website_content': 'informational',
            'serp_analysis': 'commercial',
            'nlp_extraction': 'informational'
        }

        for source, expected_intent in sources_and_intents.items():
            kw_data = {
                'keyword': 'test',
                'source': source,
                'relevance_score': 0.5
            }
            result = transformer.transform_keyword_to_engarde(kw_data, enrich=False)
            assert result.intent == expected_intent

    def test_transform_keyword_category_inference(self, transformer):
        """Test keyword category inference."""
        test_cases = [
            ('buy email marketing software', 'product'),
            ('email marketing service provider', 'service'),
            ('how to do email marketing', 'informational'),
            ('mailchimp vs hubspot', 'comparison'),
            ('email marketing near me', 'local'),
            ('random keyword', None)
        ]

        for keyword, expected_category in test_cases:
            kw_data = {
                'keyword': keyword,
                'source': 'nlp_extraction',
                'relevance_score': 0.5
            }
            result = transformer.transform_keyword_to_engarde(kw_data, enrich=False)
            assert result.category == expected_category

    def test_transform_keyword_tag_generation(self, transformer):
        """Test tag generation for keywords."""
        kw_data = {
            'keyword': 'email marketing',
            'source': 'website_content',
            'search_volume': 15000,
            'relevance_score': 0.85,
            'serp_features': {'featured_snippet': True}
        }

        result = transformer.transform_keyword_to_engarde(kw_data, enrich=False)

        assert 'source:website_content' in result.tags
        assert 'high-relevance' in result.tags
        assert 'medium-volume' in result.tags
        assert 'imported' in result.tags

    def test_transform_keyword_missing_optional_fields(self, transformer):
        """Test keyword transformation with missing optional fields."""
        minimal_kw = {
            'keyword': 'test keyword',
            'source': 'nlp_extraction',
            'relevance_score': 0.5
        }

        result = transformer.transform_keyword_to_engarde(minimal_kw, enrich=False)

        assert result.keyword == 'test keyword'
        assert result.search_volume is None
        assert result.difficulty is None
        assert result.current_rank is None

    def test_transform_keyword_invalid_data(self, transformer):
        """Test keyword transformation with invalid data."""
        invalid_kw = {
            'keyword': '',  # Empty keyword
            'source': 'nlp_extraction',
            'relevance_score': 0.5
        }

        with pytest.raises(TransformationError):
            transformer.transform_keyword_to_engarde(invalid_kw)

    def test_transform_keywords_batch(self, transformer):
        """Test batch keyword transformation."""
        keywords = [
            {
                'keyword': f'keyword {i}',
                'source': 'nlp_extraction',
                'relevance_score': 0.5 + (i * 0.1)
            }
            for i in range(5)
        ]

        results = transformer.transform_keywords_batch(keywords, enrich=False)

        assert len(results) == 5
        assert all(isinstance(r, EnGardeKeywordSchema) for r in results)

    def test_transform_keywords_batch_with_errors(self, transformer):
        """Test batch transformation with some invalid keywords."""
        keywords = [
            {'keyword': 'valid keyword', 'source': 'nlp_extraction', 'relevance_score': 0.5},
            {'keyword': '', 'source': 'nlp_extraction', 'relevance_score': 0.5},  # Invalid
            {'keyword': 'another valid', 'source': 'nlp_extraction', 'relevance_score': 0.7},
        ]

        results = transformer.transform_keywords_batch(keywords, enrich=False)

        # Should skip invalid keywords and return valid ones
        assert len(results) == 2
        assert results[0].keyword == 'valid keyword'
        assert results[1].keyword == 'another valid'

    # Competitor Transformation Tests

    def test_transform_competitor_basic(self, transformer, sample_onside_competitor):
        """Test basic competitor transformation."""
        result = transformer.transform_competitor_to_engarde(
            sample_onside_competitor,
            enrich=False
        )

        assert isinstance(result, EnGardeCompetitorSchema)
        assert result.domain == 'mailchimp.com'
        assert result.name == 'Mailchimp'
        assert result.website == 'https://mailchimp.com'
        assert result.tier == 'primary'
        assert len(result.focus_areas) > 0

    def test_transform_competitor_category_mapping(self, transformer):
        """Test competitor category to tier mapping."""
        categories_and_tiers = {
            'primary': 'primary',
            'secondary': 'secondary',
            'emerging': 'secondary',
            'niche': 'tertiary'
        }

        for category, expected_tier in categories_and_tiers.items():
            comp_data = {
                'domain': 'test.com',
                'relevance_score': 0.5,
                'category': category
            }
            result = transformer.transform_competitor_to_engarde(comp_data, enrich=False)
            assert result.tier == expected_tier

    def test_transform_competitor_with_enrichment(self, transformer, sample_onside_competitor):
        """Test competitor transformation with enrichment."""
        result = transformer.transform_competitor_to_engarde(
            sample_onside_competitor,
            enrich=True
        )

        # Should estimate market share from overlap
        assert result.market_share is not None
        assert result.market_share > 0

        # Should add strengths based on content similarity
        if sample_onside_competitor.get('content_similarity', 0) > 0.7:
            assert len(result.strengths) > 0

    def test_transform_competitor_name_extraction(self, transformer):
        """Test brand name extraction from domain."""
        test_cases = [
            ('mailchimp.com', 'Mailchimp'),
            ('hubspot.com', 'Hubspot'),
            ('constant-contact.com', 'Constant Contact'),
            ('example_domain.io', 'Example Domain')
        ]

        for domain, expected_name in test_cases:
            comp_data = {
                'domain': domain,
                'relevance_score': 0.5,
                'category': 'secondary'
            }
            result = transformer.transform_competitor_to_engarde(comp_data, enrich=False)
            assert result.name == expected_name

    def test_transform_competitor_domain_authority_estimation(self, transformer):
        """Test domain authority estimation."""
        # High relevance + high overlap = high DA
        high_da_comp = {
            'domain': 'test.com',
            'relevance_score': 0.95,
            'category': 'primary',
            'overlap_percentage': 85.0
        }

        result = transformer.transform_competitor_to_engarde(high_da_comp, enrich=False)
        assert result.domain_authority is not None
        assert result.domain_authority > 60

        # Low relevance + low overlap = low DA
        low_da_comp = {
            'domain': 'test.com',
            'relevance_score': 0.3,
            'category': 'niche',
            'overlap_percentage': 10.0
        }

        result = transformer.transform_competitor_to_engarde(low_da_comp, enrich=False)
        assert result.domain_authority is not None
        assert result.domain_authority < 40

    def test_transform_competitor_focus_areas(self, transformer):
        """Test focus areas extraction from keyword overlap."""
        comp_data = {
            'domain': 'test.com',
            'relevance_score': 0.5,
            'category': 'secondary',
            'keyword_overlap': [
                'email marketing',
                'marketing automation',
                'crm software',
                'analytics',
                'reporting',
                'extra keyword'
            ]
        }

        result = transformer.transform_competitor_to_engarde(comp_data, enrich=False)

        # Should include top 5 keywords as focus areas
        assert len(result.focus_areas) == 5
        assert 'email marketing' in result.focus_areas

    def test_transform_competitor_missing_name(self, transformer):
        """Test competitor transformation without name."""
        comp_data = {
            'domain': 'newcompetitor.com',
            'relevance_score': 0.5,
            'category': 'secondary'
        }

        result = transformer.transform_competitor_to_engarde(comp_data, enrich=False)

        # Should extract name from domain
        assert result.name == 'Newcompetitor'

    def test_transform_competitors_batch(self, transformer):
        """Test batch competitor transformation."""
        competitors = [
            {
                'domain': f'competitor{i}.com',
                'relevance_score': 0.5 + (i * 0.1),
                'category': 'secondary'
            }
            for i in range(3)
        ]

        results = transformer.transform_competitors_batch(competitors, enrich=False)

        assert len(results) == 3
        assert all(isinstance(r, EnGardeCompetitorSchema) for r in results)

    # Schema Validation Tests

    def test_validate_schema_valid_keyword(self, transformer):
        """Test schema validation with valid keyword data."""
        valid_data = {
            'keyword': 'test keyword',
            'search_volume': 1000,
            'difficulty': 50.0,
            'intent': 'informational'
        }

        is_valid, errors = transformer.validate_schema(valid_data, EnGardeKeywordSchema)

        assert is_valid
        assert len(errors) == 0

    def test_validate_schema_invalid_keyword(self, transformer):
        """Test schema validation with invalid keyword data."""
        invalid_data = {
            'keyword': '',  # Empty keyword
            'difficulty': 150.0  # Out of range
        }

        is_valid, errors = transformer.validate_schema(invalid_data, EnGardeKeywordSchema)

        assert not is_valid
        assert len(errors) > 0

    def test_validate_schema_invalid_intent(self, transformer):
        """Test schema validation with invalid intent."""
        invalid_data = {
            'keyword': 'test',
            'intent': 'invalid_intent'
        }

        is_valid, errors = transformer.validate_schema(invalid_data, EnGardeKeywordSchema)

        assert not is_valid

    # Helper Method Tests

    def test_calculate_keyword_priority(self, transformer):
        """Test keyword priority calculation."""
        # High priority
        priority = transformer._calculate_keyword_priority(
            relevance_score=0.9,
            difficulty=30.0,
            search_volume=20000
        )
        assert priority == 'high'

        # Medium priority
        priority = transformer._calculate_keyword_priority(
            relevance_score=0.6,
            difficulty=50.0,
            search_volume=5000
        )
        assert priority == 'medium'

        # Low priority
        priority = transformer._calculate_keyword_priority(
            relevance_score=0.3,
            difficulty=80.0,
            search_volume=100
        )
        assert priority == 'low'

    def test_infer_keyword_category(self, transformer):
        """Test keyword category inference."""
        assert transformer._infer_keyword_category('buy software') == 'product'
        assert transformer._infer_keyword_category('consulting service') == 'service'
        assert transformer._infer_keyword_category('how to learn') == 'informational'
        assert transformer._infer_keyword_category('mailchimp vs hubspot') == 'comparison'
        assert transformer._infer_keyword_category('near me') == 'local'
        assert transformer._infer_keyword_category('random') is None

    def test_estimate_cpc(self, transformer):
        """Test CPC estimation."""
        # High volume + high difficulty = high CPC
        cpc = transformer._estimate_cpc(search_volume=50000, difficulty=80.0)
        assert cpc > 2.0

        # Low volume + low difficulty = low CPC
        cpc = transformer._estimate_cpc(search_volume=100, difficulty=20.0)
        assert cpc < 1.5

    def test_extract_name_from_domain(self, transformer):
        """Test name extraction from domain."""
        assert transformer._extract_name_from_domain('mailchimp.com') == 'Mailchimp'
        assert transformer._extract_name_from_domain('constant-contact.com') == 'Constant Contact'
        assert transformer._extract_name_from_domain('example.co.uk') == 'Example'

    def test_generate_keyword_tags(self, transformer):
        """Test keyword tag generation."""
        kw_data = {
            'source': 'website_content',
            'relevance_score': 0.9,
            'search_volume': 25000,
            'serp_features': {'featured_snippet': True, 'people_also_ask': True}
        }

        tags = transformer._generate_keyword_tags(kw_data)

        assert 'source:website_content' in tags
        assert 'high-relevance' in tags
        assert 'high-volume' in tags
        assert 'featured-snippet' in tags
        assert 'paa' in tags
        assert 'imported' in tags


@pytest.mark.unit
class TestTransformationEdgeCases:
    """Test edge cases and error handling in data transformation."""

    @pytest.fixture
    def transformer(self):
        """Create DataTransformer instance."""
        return DataTransformer()

    def test_empty_keyword(self, transformer):
        """Test transformation with empty keyword."""
        kw_data = {
            'keyword': '',
            'source': 'nlp_extraction',
            'relevance_score': 0.5
        }

        with pytest.raises(TransformationError):
            transformer.transform_keyword_to_engarde(kw_data)

    def test_negative_search_volume(self, transformer):
        """Test transformation with negative search volume."""
        kw_data = {
            'keyword': 'test',
            'source': 'nlp_extraction',
            'search_volume': -1000,  # Invalid
            'relevance_score': 0.5
        }

        with pytest.raises(TransformationError):
            transformer.transform_keyword_to_engarde(kw_data)

    def test_out_of_range_difficulty(self, transformer):
        """Test transformation with out-of-range difficulty."""
        kw_data = {
            'keyword': 'test',
            'source': 'nlp_extraction',
            'difficulty': 150.0,  # Out of range (0-100)
            'relevance_score': 0.5
        }

        with pytest.raises(TransformationError):
            transformer.transform_keyword_to_engarde(kw_data)

    def test_malformed_competitor_domain(self, transformer):
        """Test competitor transformation with malformed domain."""
        # Should still work - transformer is lenient
        comp_data = {
            'domain': 'not a domain',
            'relevance_score': 0.5,
            'category': 'secondary'
        }

        result = transformer.transform_competitor_to_engarde(comp_data, enrich=False)
        assert result.domain == 'not a domain'

    def test_extreme_relevance_scores(self, transformer):
        """Test with extreme relevance scores."""
        # Relevance score > 1.0
        kw_data = {
            'keyword': 'test',
            'source': 'nlp_extraction',
            'relevance_score': 1.5  # Out of range
        }

        # Should raise error due to validation
        with pytest.raises(TransformationError):
            transformer.transform_keyword_to_engarde(kw_data)

    def test_unicode_keywords(self, transformer):
        """Test transformation with Unicode keywords."""
        kw_data = {
            'keyword': 'email marketing 日本語',
            'source': 'nlp_extraction',
            'relevance_score': 0.5
        }

        result = transformer.transform_keyword_to_engarde(kw_data, enrich=False)
        assert 'email marketing 日本語' in result.keyword

    def test_very_long_keyword(self, transformer):
        """Test transformation with very long keyword."""
        long_keyword = 'a' * 300  # Exceeds max length

        kw_data = {
            'keyword': long_keyword,
            'source': 'nlp_extraction',
            'relevance_score': 0.5
        }

        with pytest.raises(TransformationError):
            transformer.transform_keyword_to_engarde(kw_data)

    def test_none_values(self, transformer):
        """Test transformation with None values in optional fields."""
        kw_data = {
            'keyword': 'test',
            'source': 'nlp_extraction',
            'search_volume': None,
            'difficulty': None,
            'relevance_score': 0.5,
            'current_ranking': None
        }

        result = transformer.transform_keyword_to_engarde(kw_data, enrich=False)

        assert result.search_volume is None
        assert result.difficulty is None
        assert result.current_rank is None
