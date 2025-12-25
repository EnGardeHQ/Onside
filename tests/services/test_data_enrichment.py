"""
Unit tests for DataEnrichmentService.

This module provides comprehensive unit tests for the data enrichment service,
following BDD/TDD methodology with pytest. Tests cover data validation,
transformation logic, error handling, and external dependency mocking.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any
import logging

from src.services.data.data_enrichment import DataEnrichmentService
from src.exceptions import ServiceUnavailableError


class TestDataEnrichmentService:
    """Test suite for DataEnrichmentService following BDD methodology."""

    @pytest_asyncio.fixture
    async def mock_db_session(self):
        """Create a mock database session for testing."""
        mock_session = AsyncMock()
        return mock_session

    @pytest_asyncio.fixture
    async def service(self, mock_db_session):
        """Create a DataEnrichmentService instance for testing."""
        return DataEnrichmentService(db=mock_db_session)

    @pytest_asyncio.fixture
    def sample_company_data(self) -> Dict[str, Any]:
        """Provide sample company data for testing."""
        return {
            'id': 'company_123',
            'name': 'Test Company Inc',
            'industry': 'Technology',
            'location': 'San Francisco, CA'
        }

    class TestInitialization:
        """Test service initialization and configuration."""

        @pytest_asyncio.async_test
        async def test_service_initializes_with_db_session(self, mock_db_session):
            """Given a database session, when initializing service, then it should store the session."""
            # When
            service = DataEnrichmentService(db=mock_db_session)
            
            # Then
            assert service.db == mock_db_session
            assert service.timeout == 30.0

        @pytest_asyncio.async_test
        async def test_service_sets_default_timeout(self, mock_db_session):
            """Given initialization, when creating service, then it should set default timeout."""
            # When
            service = DataEnrichmentService(db=mock_db_session)
            
            # Then
            assert service.timeout == 30.0

    class TestEnrichCompanyData:
        """Test company data enrichment functionality."""

        @pytest_asyncio.async_test
        async def test_enrich_company_data_returns_copy_with_no_enrichment(
            self, service, sample_company_data
        ):
            """Given basic company data with no enrichment flags, when enriching, then returns copy of original data."""
            # When
            result = await service.enrich_company_data(sample_company_data)
            
            # Then
            assert result == sample_company_data
            assert result is not sample_company_data  # Should be a copy

        @pytest_asyncio.async_test
        async def test_enrich_company_data_with_financials_flag_true(
            self, service, sample_company_data
        ):
            """Given company data and financials flag, when enriching, then includes financial data."""
            # Given
            expected_financials = {
                'revenue': None,
                'profit': None,
                'employees': None,
                'last_updated': None
            }
            
            # When
            result = await service.enrich_company_data(
                sample_company_data, 
                include_financials=True
            )
            
            # Then
            assert 'financials' in result
            assert result['financials'] == expected_financials
            assert result['name'] == sample_company_data['name']

        @pytest_asyncio.async_test
        async def test_enrich_company_data_with_news_flag_true(
            self, service, sample_company_data
        ):
            """Given company data and news flag, when enriching, then includes news data."""
            # When
            result = await service.enrich_company_data(
                sample_company_data, 
                include_news=True
            )
            
            # Then
            assert 'news' in result
            assert result['news'] == []
            assert result['name'] == sample_company_data['name']

        @pytest_asyncio.async_test
        async def test_enrich_company_data_with_social_flag_true(
            self, service, sample_company_data
        ):
            """Given company data and social flag, when enriching, then includes social media data."""
            # Given
            expected_social = {
                'followers': {},
                'engagement': {},
                'sentiment': {}
            }
            
            # When
            result = await service.enrich_company_data(
                sample_company_data, 
                include_social=True
            )
            
            # Then
            assert 'social_media' in result
            assert result['social_media'] == expected_social
            assert result['name'] == sample_company_data['name']

        @pytest_asyncio.async_test
        async def test_enrich_company_data_with_all_flags_true(
            self, service, sample_company_data
        ):
            """Given company data and all enrichment flags, when enriching, then includes all data types."""
            # When
            result = await service.enrich_company_data(
                sample_company_data,
                include_financials=True,
                include_news=True,
                include_social=True
            )
            
            # Then
            assert 'financials' in result
            assert 'news' in result
            assert 'social_media' in result
            assert result['name'] == sample_company_data['name']

    class TestFinancialDataEnrichment:
        """Test financial data enrichment with error handling."""

        @pytest_asyncio.async_test
        async def test_get_financial_data_returns_placeholder_structure(self, service):
            """Given a company ID, when getting financial data, then returns expected structure."""
            # When
            result = await service._get_financial_data('company_123')
            
            # Then
            expected_keys = {'revenue', 'profit', 'employees', 'last_updated'}
            assert set(result.keys()) == expected_keys
            assert all(value is None for value in result.values())

        @pytest_asyncio.async_test
        async def test_enrich_company_data_handles_financial_data_exception(
            self, service, sample_company_data
        ):
            """Given financial data retrieval failure, when enriching, then handles error gracefully."""
            # Given
            with patch.object(service, '_get_financial_data', side_effect=Exception("API Error")):
                # When
                result = await service.enrich_company_data(
                    sample_company_data, 
                    include_financials=True
                )
            
            # Then
            assert 'financials' in result
            assert 'error' in result['financials']
            assert result['financials']['error'] == 'Failed to retrieve financial data'
            assert result['financials']['details'] == 'API Error'

        @pytest_asyncio.async_test
        async def test_enrich_company_data_logs_financial_error(
            self, service, sample_company_data, caplog
        ):
            """Given financial data retrieval failure, when enriching, then logs error message."""
            # Given
            with patch.object(service, '_get_financial_data', side_effect=Exception("API Error")):
                with caplog.at_level(logging.ERROR):
                    # When
                    await service.enrich_company_data(
                        sample_company_data, 
                        include_financials=True
                    )
            
            # Then
            assert "Error enriching financial data: API Error" in caplog.text

    class TestNewsDataEnrichment:
        """Test news data enrichment with error handling."""

        @pytest_asyncio.async_test
        async def test_get_news_data_returns_empty_list(self, service):
            """Given a company name, when getting news data, then returns empty list."""
            # When
            result = await service._get_news_data('Test Company')
            
            # Then
            assert result == []
            assert isinstance(result, list)

        @pytest_asyncio.async_test
        async def test_enrich_company_data_handles_news_data_exception(
            self, service, sample_company_data
        ):
            """Given news data retrieval failure, when enriching, then handles error gracefully."""
            # Given
            with patch.object(service, '_get_news_data', side_effect=Exception("News API Error")):
                # When
                result = await service.enrich_company_data(
                    sample_company_data, 
                    include_news=True
                )
            
            # Then
            assert 'news' in result
            assert 'error' in result['news']
            assert result['news']['error'] == 'Failed to retrieve news data'
            assert result['news']['details'] == 'News API Error'

        @pytest_asyncio.async_test
        async def test_enrich_company_data_logs_news_error(
            self, service, sample_company_data, caplog
        ):
            """Given news data retrieval failure, when enriching, then logs error message."""
            # Given
            with patch.object(service, '_get_news_data', side_effect=Exception("News API Error")):
                with caplog.at_level(logging.ERROR):
                    # When
                    await service.enrich_company_data(
                        sample_company_data, 
                        include_news=True
                    )
            
            # Then
            assert "Error enriching news data: News API Error" in caplog.text

    class TestSocialMediaDataEnrichment:
        """Test social media data enrichment with error handling."""

        @pytest_asyncio.async_test
        async def test_get_social_media_data_returns_expected_structure(self, service):
            """Given a company name, when getting social media data, then returns expected structure."""
            # When
            result = await service._get_social_media_data('Test Company')
            
            # Then
            expected_keys = {'followers', 'engagement', 'sentiment'}
            assert set(result.keys()) == expected_keys
            assert all(isinstance(value, dict) for value in result.values())
            assert all(value == {} for value in result.values())

        @pytest_asyncio.async_test
        async def test_enrich_company_data_handles_social_media_exception(
            self, service, sample_company_data
        ):
            """Given social media data retrieval failure, when enriching, then handles error gracefully."""
            # Given
            with patch.object(service, '_get_social_media_data', side_effect=Exception("Social API Error")):
                # When
                result = await service.enrich_company_data(
                    sample_company_data, 
                    include_social=True
                )
            
            # Then
            assert 'social_media' in result
            assert 'error' in result['social_media']
            assert result['social_media']['error'] == 'Failed to retrieve social media data'
            assert result['social_media']['details'] == 'Social API Error'

        @pytest_asyncio.async_test
        async def test_enrich_company_data_logs_social_media_error(
            self, service, sample_company_data, caplog
        ):
            """Given social media data retrieval failure, when enriching, then logs error message."""
            # Given
            with patch.object(service, '_get_social_media_data', side_effect=Exception("Social API Error")):
                with caplog.at_level(logging.ERROR):
                    # When
                    await service.enrich_company_data(
                        sample_company_data, 
                        include_social=True
                    )
            
            # Then
            assert "Error enriching social media data: Social API Error" in caplog.text

    class TestEdgeCases:
        """Test edge cases and boundary conditions."""

        @pytest_asyncio.async_test
        async def test_enrich_empty_company_data(self, service):
            """Given empty company data, when enriching, then handles gracefully."""
            # Given
            empty_data = {}
            
            # When
            result = await service.enrich_company_data(empty_data)
            
            # Then
            assert result == {}

        @pytest_asyncio.async_test
        async def test_enrich_company_data_missing_id(self, service):
            """Given company data without ID, when enriching with financials, then handles gracefully."""
            # Given
            data_without_id = {'name': 'Test Company'}
            
            # When
            result = await service.enrich_company_data(data_without_id, include_financials=True)
            
            # Then
            assert 'financials' in result
            # Should still work with None as company_id

        @pytest_asyncio.async_test
        async def test_enrich_company_data_missing_name(self, service):
            """Given company data without name, when enriching with news/social, then handles gracefully."""
            # Given
            data_without_name = {'id': 'company_123'}
            
            # When
            result = await service.enrich_company_data(
                data_without_name, 
                include_news=True, 
                include_social=True
            )
            
            # Then
            assert 'news' in result
            assert 'social_media' in result
            # Should still work with None as company_name

        @pytest_asyncio.async_test
        async def test_enrich_company_data_with_none_input(self, service):
            """Given None as company data, when enriching, then raises appropriate error."""
            # When/Then
            with pytest.raises(AttributeError):
                await service.enrich_company_data(None)

    class TestDataValidation:
        """Test data validation and transformation."""

        @pytest_asyncio.async_test
        async def test_enrich_company_data_preserves_original_data_integrity(
            self, service, sample_company_data
        ):
            """Given company data, when enriching, then preserves all original fields."""
            # When
            result = await service.enrich_company_data(
                sample_company_data,
                include_financials=True,
                include_news=True,
                include_social=True
            )
            
            # Then
            for key, value in sample_company_data.items():
                assert result[key] == value

        @pytest_asyncio.async_test
        async def test_enrich_company_data_does_not_mutate_input(
            self, service, sample_company_data
        ):
            """Given company data, when enriching, then does not mutate original data."""
            # Given
            original_data = sample_company_data.copy()
            
            # When
            await service.enrich_company_data(
                sample_company_data,
                include_financials=True,
                include_news=True,
                include_social=True
            )
            
            # Then
            assert sample_company_data == original_data

    class TestConcurrentEnrichment:
        """Test concurrent enrichment scenarios."""

        @pytest_asyncio.async_test
        async def test_multiple_enrichment_calls_handle_concurrency(self, service, sample_company_data):
            """Given multiple concurrent enrichment calls, when processing, then all complete successfully."""
            import asyncio
            
            # When - Make multiple concurrent calls
            tasks = [
                service.enrich_company_data(sample_company_data, include_financials=True),
                service.enrich_company_data(sample_company_data, include_news=True),
                service.enrich_company_data(sample_company_data, include_social=True)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Then
            assert len(results) == 3
            assert 'financials' in results[0]
            assert 'news' in results[1]
            assert 'social_media' in results[2]

    class TestTypeHandling:
        """Test type handling and validation."""

        @pytest_asyncio.async_test
        async def test_enrich_company_data_with_string_flags(self, service, sample_company_data):
            """Given string flags instead of boolean, when enriching, then handles appropriately."""
            # When
            result = await service.enrich_company_data(
                sample_company_data,
                include_financials="true",  # String instead of bool
                include_news=1,  # Integer instead of bool
                include_social=""  # Empty string (falsy)
            )
            
            # Then - Python's truthiness should handle these
            assert 'financials' in result  # "true" is truthy
            assert 'news' in result  # 1 is truthy
            assert 'social_media' not in result  # "" is falsy