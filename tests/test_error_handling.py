"""Comprehensive test suite for error handling and validation.

Tests all error scenarios, validation rules, fallback mechanisms,
and recovery strategies for the En Garde integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from src.services.engarde_integration.error_handling import (
    BrandAnalysisError,
    WebsiteUnreachableError,
    InsufficientDataError,
    AnalysisTimeoutError,
    InvalidQuestionnaireError,
    SERPAPIError,
    ScrapingError,
    handle_analysis_failure,
    retry_with_backoff,
    fallback_to_manual,
    save_partial_results
)

from src.services.engarde_integration.validation import (
    validate_url,
    validate_domain,
    validate_questionnaire,
    sanitize_input,
    check_rate_limit,
    validate_analysis_results
)

from src.models.brand_analysis import BrandAnalysisJob, AnalysisStatus


# ============================================================================
# Exception Tests
# ============================================================================

@pytest.mark.unit
class TestCustomExceptions:
    """Test custom exception classes."""

    def test_brand_analysis_error_basic(self):
        """Test basic BrandAnalysisError creation."""
        error = BrandAnalysisError("Test error")
        assert error.message == "Test error"
        assert error.error_code == "BRAND_ANALYSIS_ERROR"
        assert error.fallback_available is False

    def test_brand_analysis_error_to_dict(self):
        """Test exception to_dict conversion."""
        error = BrandAnalysisError(
            message="Test error",
            error_code="TEST_ERROR",
            details="Additional details",
            suggestion="Try this",
            fallback_available=True
        )

        error_dict = error.to_dict()
        assert error_dict["error"]["code"] == "TEST_ERROR"
        assert error_dict["error"]["message"] == "Test error"
        assert error_dict["error"]["details"] == "Additional details"
        assert error_dict["error"]["suggestion"] == "Try this"
        assert error_dict["error"]["fallback_available"] is True

    def test_website_unreachable_error(self):
        """Test WebsiteUnreachableError."""
        error = WebsiteUnreachableError(
            url="https://example.com",
            reason="Connection timeout"
        )

        assert error.error_code == "WEBSITE_UNREACHABLE"
        assert "example.com" in error.message
        assert error.url == "https://example.com"
        assert error.reason == "Connection timeout"
        assert error.fallback_available is True

    def test_insufficient_data_error(self):
        """Test InsufficientDataError."""
        error = InsufficientDataError(
            data_type="keywords",
            threshold=10,
            actual=3
        )

        assert error.error_code == "INSUFFICIENT_DATA"
        assert error.data_type == "keywords"
        assert error.threshold == 10
        assert error.actual == 3
        assert "3" in error.message
        assert "10" in error.message

    def test_analysis_timeout_error(self):
        """Test AnalysisTimeoutError."""
        error = AnalysisTimeoutError(
            operation="crawling",
            timeout_seconds=300
        )

        assert error.error_code == "ANALYSIS_TIMEOUT"
        assert error.operation == "crawling"
        assert error.timeout_seconds == 300
        assert "crawling" in error.message

    def test_invalid_questionnaire_error(self):
        """Test InvalidQuestionnaireError."""
        error = InvalidQuestionnaireError(
            field="brand_name",
            reason="cannot be empty"
        )

        assert error.error_code == "INVALID_QUESTIONNAIRE"
        assert error.field == "brand_name"
        assert error.reason == "cannot be empty"
        assert error.fallback_available is False

    def test_serp_api_error(self):
        """Test SERPAPIError."""
        error = SERPAPIError(
            api_name="SerpAPI",
            status_code=429,
            reason="Rate limit exceeded"
        )

        assert error.error_code == "SERP_API_ERROR"
        assert error.api_name == "SerpAPI"
        assert error.status_code == 429
        assert error.fallback_available is True

    def test_scraping_error(self):
        """Test ScrapingError."""
        error = ScrapingError(
            url="https://example.com",
            reason="Anti-bot protection detected",
            status_code=403
        )

        assert error.error_code == "SCRAPING_ERROR"
        assert error.url == "https://example.com"
        assert error.status_code == 403
        assert error.fallback_available is True


# ============================================================================
# Error Handler Tests
# ============================================================================

@pytest.mark.unit
class TestErrorHandlers:
    """Test error handler functions."""

    @pytest.mark.asyncio
    async def test_handle_website_unreachable(self, test_db, test_user):
        """Test handling of website unreachable error."""
        # Create job
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test", "primary_website": "https://example.com"},
            status=AnalysisStatus.INITIATED
        )
        test_db.add(job)
        test_db.commit()
        test_db.refresh(job)

        error = WebsiteUnreachableError(
            url="https://example.com",
            reason="Connection timeout"
        )

        result = await handle_analysis_failure(
            str(job.id),
            error,
            job.questionnaire,
            test_db
        )

        assert result["status"] == "failed"
        assert "fallback" in result
        assert result["fallback"]["method"] == "manual_input"

        # Verify job was updated
        test_db.refresh(job)
        assert job.status == AnalysisStatus.FAILED
        assert job.error_message == error.message

    @pytest.mark.asyncio
    async def test_handle_insufficient_data(self, test_db, test_user):
        """Test handling of insufficient data error."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"},
            status=AnalysisStatus.ANALYZING
        )
        test_db.add(job)
        test_db.commit()
        test_db.refresh(job)

        error = InsufficientDataError(
            data_type="keywords",
            threshold=10,
            actual=3
        )

        partial_results = {"keywords": ["kw1", "kw2", "kw3"]}

        result = await handle_analysis_failure(
            str(job.id),
            error,
            job.questionnaire,
            test_db,
            partial_results
        )

        assert result["status"] == "completed_with_warnings"
        assert "partial_results" in result

        # Verify job was updated to completed with warnings
        test_db.refresh(job)
        assert job.status == AnalysisStatus.COMPLETED
        assert "Warning" in job.error_message

    @pytest.mark.asyncio
    async def test_save_partial_results(self, test_db, test_user):
        """Test saving partial results."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        test_db.commit()
        test_db.refresh(job)

        partial_results = {
            "keywords": ["kw1", "kw2"],
            "competitors": ["comp1.com"]
        }

        success = await save_partial_results(
            str(job.id),
            partial_results,
            test_db
        )

        assert success is True

        test_db.refresh(job)
        assert job.results is not None
        assert job.results["partial"] is True
        assert "partial_data" in job.results

    @pytest.mark.asyncio
    async def test_fallback_to_manual(self, test_db, test_user):
        """Test fallback to manual input."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={
                "brand_name": "Test Brand",
                "primary_website": "https://test.com"
            }
        )
        test_db.add(job)
        test_db.commit()
        test_db.refresh(job)

        result = await fallback_to_manual(str(job.id), test_db)

        assert result["status"] == "manual_input_required"
        assert "required_inputs" in result
        assert "keywords" in result["required_inputs"]
        assert "competitors" in result["required_inputs"]


# ============================================================================
# Retry Mechanism Tests
# ============================================================================

@pytest.mark.unit
class TestRetryMechanism:
    """Test retry with backoff decorator."""

    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self):
        """Test function succeeds on first attempt."""
        call_count = 0

        @retry_with_backoff(max_retries=3)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await test_func()

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test function succeeds after retries."""
        call_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        result = await test_func()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_all_attempts_fail(self):
        """Test all retry attempts fail."""
        call_count = 0

        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Permanent failure")

        with pytest.raises(ConnectionError):
            await test_func()

        assert call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_retry_with_fallback_value(self):
        """Test retry returns fallback value on failure."""
        @retry_with_backoff(
            max_retries=2,
            initial_delay=0.01,
            fallback_value={"status": "fallback"}
        )
        async def test_func():
            raise ConnectionError("Always fails")

        result = await test_func()

        assert result == {"status": "fallback"}

    @pytest.mark.asyncio
    async def test_retry_specific_exceptions(self):
        """Test retry only catches specific exceptions."""
        @retry_with_backoff(
            max_retries=2,
            initial_delay=0.01,
            exceptions=(ConnectionError,)
        )
        async def test_func():
            raise ValueError("Different exception")

        # Should not retry ValueError
        with pytest.raises(ValueError):
            await test_func()


# ============================================================================
# URL Validation Tests
# ============================================================================

@pytest.mark.unit
class TestURLValidation:
    """Test URL validation."""

    @pytest.mark.asyncio
    async def test_validate_url_valid_https(self):
        """Test valid HTTPS URL."""
        is_valid, error = await validate_url(
            "https://example.com",
            check_reachability=False
        )

        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_url_valid_http(self):
        """Test valid HTTP URL."""
        is_valid, error = await validate_url(
            "http://example.com",
            check_reachability=False
        )

        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_url_invalid_format(self):
        """Test invalid URL format."""
        is_valid, error = await validate_url(
            "not-a-url",
            check_reachability=False
        )

        assert is_valid is False
        assert error is not None

    @pytest.mark.asyncio
    async def test_validate_url_missing_protocol(self):
        """Test URL without protocol."""
        is_valid, error = await validate_url(
            "example.com",
            check_reachability=False
        )

        assert is_valid is False
        assert "http" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_url_blocklisted_domain(self):
        """Test blocklisted domain."""
        is_valid, error = await validate_url(
            "http://localhost",
            check_reachability=False
        )

        assert is_valid is False
        assert "not allowed" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_url_too_long(self):
        """Test URL exceeding max length."""
        long_url = "https://example.com/" + ("x" * 3000)
        is_valid, error = await validate_url(
            long_url,
            check_reachability=False
        )

        assert is_valid is False
        assert "maximum length" in error.lower()


# ============================================================================
# Domain Validation Tests
# ============================================================================

@pytest.mark.unit
class TestDomainValidation:
    """Test domain validation."""

    @pytest.mark.asyncio
    async def test_validate_domain_valid(self):
        """Test valid domain."""
        is_valid, error = await validate_domain(
            "example.com",
            check_dns=False
        )

        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_domain_with_subdomain(self):
        """Test subdomain."""
        is_valid, error = await validate_domain(
            "blog.example.com",
            check_dns=False
        )

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_domain_invalid_format(self):
        """Test invalid domain format."""
        is_valid, error = await validate_domain(
            "not a domain",
            check_dns=False
        )

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_domain_strips_protocol(self):
        """Test domain validation strips protocol."""
        is_valid, error = await validate_domain(
            "https://example.com",
            check_dns=False
        )

        assert is_valid is True


# ============================================================================
# Questionnaire Validation Tests
# ============================================================================

@pytest.mark.unit
class TestQuestionnaireValidation:
    """Test questionnaire validation."""

    @pytest.mark.asyncio
    async def test_validate_questionnaire_valid(self):
        """Test valid questionnaire."""
        data = {
            "brand_name": "Test Brand",
            "primary_website": "https://test.com",
            "industry": "Technology"
        }

        is_valid, errors = await validate_questionnaire(data)

        assert is_valid is True
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_validate_questionnaire_missing_required(self):
        """Test missing required field."""
        data = {
            "brand_name": "Test Brand",
            # Missing primary_website and industry
        }

        with pytest.raises(InvalidQuestionnaireError):
            await validate_questionnaire(data)

    @pytest.mark.asyncio
    async def test_validate_questionnaire_invalid_url(self):
        """Test invalid URL in questionnaire."""
        data = {
            "brand_name": "Test Brand",
            "primary_website": "not-a-url",
            "industry": "Tech"
        }

        with pytest.raises(InvalidQuestionnaireError) as exc_info:
            await validate_questionnaire(data)

        assert "primary_website" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_questionnaire_with_lists(self):
        """Test validation with optional list fields."""
        data = {
            "brand_name": "Test Brand",
            "primary_website": "https://test.com",
            "industry": "Technology",
            "target_markets": ["USA", "Canada"],
            "products_services": ["Product A", "Product B"],
            "known_competitors": ["competitor.com"],
            "target_keywords": ["keyword1", "keyword2"]
        }

        is_valid, errors = await validate_questionnaire(data)

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_questionnaire_malicious_input(self):
        """Test detection of malicious input."""
        data = {
            "brand_name": "Test'; DROP TABLE users;--",
            "primary_website": "https://test.com",
            "industry": "Tech"
        }

        with pytest.raises(InvalidQuestionnaireError):
            await validate_questionnaire(data)


# ============================================================================
# Input Sanitization Tests
# ============================================================================

@pytest.mark.unit
class TestInputSanitization:
    """Test input sanitization."""

    def test_sanitize_input_basic(self):
        """Test basic input sanitization."""
        from src.services.engarde_integration.validation import sanitize_input

        result = sanitize_input("  Test Input  ")
        assert result == "Test Input"

    def test_sanitize_input_html_tags(self):
        """Test HTML tag removal."""
        from src.services.engarde_integration.validation import sanitize_input

        result = sanitize_input("<script>alert('xss')</script>Test")
        assert "<script>" not in result
        assert "Test" in result

    def test_sanitize_input_null_bytes(self):
        """Test null byte removal."""
        from src.services.engarde_integration.validation import sanitize_input

        result = sanitize_input("Test\x00Input")
        assert "\x00" not in result

    def test_sanitize_input_normalize_whitespace(self):
        """Test whitespace normalization."""
        from src.services.engarde_integration.validation import sanitize_input

        result = sanitize_input("Test    Multiple   Spaces")
        assert result == "Test Multiple Spaces"


# ============================================================================
# Rate Limiting Tests
# ============================================================================

@pytest.mark.unit
class TestRateLimiting:
    """Test rate limiting."""

    @pytest.mark.asyncio
    async def test_rate_limit_under_limit(self, test_db, test_user):
        """Test user under rate limit."""
        is_allowed, error = await check_rate_limit(
            test_user.id,
            test_db,
            max_requests=10
        )

        assert is_allowed is True
        assert error is None

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, test_db, test_user):
        """Test rate limit exceeded."""
        # Create multiple jobs
        for i in range(11):
            job = BrandAnalysisJob(
                user_id=test_user.id,
                questionnaire={"brand_name": f"Test {i}"}
            )
            test_db.add(job)

        test_db.commit()

        is_allowed, error = await check_rate_limit(
            test_user.id,
            test_db,
            max_requests=10
        )

        assert is_allowed is False
        assert error is not None
        assert "exceeded" in error.lower()


# ============================================================================
# Results Validation Tests
# ============================================================================

@pytest.mark.unit
class TestResultsValidation:
    """Test analysis results validation."""

    @pytest.mark.asyncio
    async def test_validate_results_valid(self):
        """Test valid results."""
        results = {
            "keywords": [
                {"keyword": "test", "relevance_score": 0.8},
                {"keyword": "example", "relevance_score": 0.6}
            ],
            "competitors": [
                {"domain": "competitor.com", "relevance_score": 0.7}
            ],
            "opportunities": []
        }

        is_valid, errors = await validate_analysis_results(results)

        assert is_valid is True
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_validate_results_invalid_keyword(self):
        """Test invalid keyword data."""
        results = {
            "keywords": [
                {"keyword": "test"}  # Missing relevance_score
            ]
        }

        is_valid, errors = await validate_analysis_results(results)

        assert is_valid is False
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_validate_results_invalid_score(self):
        """Test invalid relevance score."""
        results = {
            "keywords": [
                {"keyword": "test", "relevance_score": 1.5}  # Score > 1
            ]
        }

        is_valid, errors = await validate_analysis_results(results)

        assert is_valid is False
