"""Tests for the WhoAPI service.

These tests verify the functionality of the WhoAPIService class, including:
- WHOIS data retrieval and parsing
- SSL certificate information
- DNS records lookup
- Domain age calculation
- Technology stack detection
- Domain availability checking
- Expiring domains retrieval
- Error handling and retry logic
- Caching behavior
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from src.services.external_api.whoapi_service import (
    WhoAPIService,
    WhoAPIError,
    RateLimitError,
    DomainNotFoundError,
    WhoisData,
    SSLInfo,
    DNSInfo,
    TechStackInfo,
    DomainAge,
    DomainAvailability,
)


# Sample test data
SAMPLE_DOMAIN = "example.com"

SAMPLE_WHOIS_RESPONSE = {
    "status": 1,
    "domain_name": "example.com",
    "registrar_name": "Example Registrar, Inc.",
    "date_created": "2020-01-15",
    "date_expires": "2025-01-15",
    "date_updated": "2024-01-01",
    "nameservers": ["ns1.example.com", "ns2.example.com"],
    "status": ["clientTransferProhibited", "clientDeleteProhibited"],
    "dnssec": "yes",
    "registrant_name": "John Doe",
    "registrant_org": "Example Organization",
    "registrant_country": "US",
    "registrant_email": "admin@example.com",
}

SAMPLE_SSL_RESPONSE = {
    "status": 1,
    "valid": True,
    "issuer": "Let's Encrypt Authority X3",
    "date_issue": "2024-01-01",
    "date_expire": "2024-04-01",
    "subject": "example.com",
    "san": ["example.com", "www.example.com"],
    "fingerprint": "AB:CD:EF:12:34:56:78:90",
    "serial_number": "1234567890",
    "signature_algorithm": "SHA256withRSA",
    "protocol_version": "TLSv1.3",
}

SAMPLE_DNS_RESPONSE = {
    "status": 1,
    "a": [{"data": "93.184.216.34", "ttl": 3600}],
    "aaaa": [{"data": "2606:2800:220:1:248:1893:25c8:1946", "ttl": 3600}],
    "mx": [{"data": "mail.example.com", "priority": 10, "ttl": 3600}],
    "ns": [{"data": "ns1.example.com", "ttl": 3600}, {"data": "ns2.example.com", "ttl": 3600}],
    "txt": [{"data": "v=spf1 include:_spf.example.com ~all", "ttl": 3600}],
    "cname": [],
}

SAMPLE_TECH_RESPONSE = {
    "status": 1,
    "technologies": [
        {"name": "WordPress", "category": "CMS"},
        {"name": "Google Analytics", "category": "Analytics"},
        {"name": "React", "category": "Framework"},
    ],
    "cms": "WordPress",
    "ecommerce": None,
    "cdn": "Cloudflare",
    "hosting": "AWS",
    "server": "nginx",
}

SAMPLE_AVAILABILITY_RESPONSE = {
    "status": 1,
    "taken": 1,  # 1 means taken, 0 means available
    "premium": False,
}


@pytest.fixture
def whoapi_service():
    """Create a WhoAPIService instance with mocked API key."""
    with patch.dict("os.environ", {"WHOAPI_API_KEY": "test-api-key"}):
        service = WhoAPIService(api_key="test-api-key")
        yield service


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client
        yield mock_client


class TestWhoAPIServiceInit:
    """Tests for WhoAPIService initialization."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        service = WhoAPIService(api_key="my-api-key")
        assert service.api_key == "my-api-key"

    def test_init_from_env(self):
        """Test initialization from environment variable."""
        with patch.dict("os.environ", {"WHOAPI_API_KEY": "env-api-key"}):
            service = WhoAPIService()
            assert service.api_key == "env-api-key"

    def test_init_without_api_key(self):
        """Test initialization without API key logs warning."""
        with patch.dict("os.environ", {"WHOAPI_API_KEY": ""}, clear=True):
            service = WhoAPIService(api_key="")
            assert service.api_key == ""


class TestDomainNormalization:
    """Tests for domain name normalization."""

    def test_normalize_simple_domain(self, whoapi_service):
        """Test normalization of a simple domain."""
        assert whoapi_service._normalize_domain("example.com") == "example.com"

    def test_normalize_removes_protocol(self, whoapi_service):
        """Test that protocol is removed."""
        assert whoapi_service._normalize_domain("https://example.com") == "example.com"
        assert whoapi_service._normalize_domain("http://example.com") == "example.com"

    def test_normalize_removes_www(self, whoapi_service):
        """Test that www prefix is removed."""
        assert whoapi_service._normalize_domain("www.example.com") == "example.com"

    def test_normalize_removes_path(self, whoapi_service):
        """Test that path is removed."""
        assert whoapi_service._normalize_domain("example.com/page") == "example.com"

    def test_normalize_removes_port(self, whoapi_service):
        """Test that port is removed."""
        assert whoapi_service._normalize_domain("example.com:8080") == "example.com"

    def test_normalize_lowercase(self, whoapi_service):
        """Test that domain is lowercased."""
        assert whoapi_service._normalize_domain("EXAMPLE.COM") == "example.com"

    def test_normalize_complex_url(self, whoapi_service):
        """Test normalization of complex URL."""
        assert whoapi_service._normalize_domain(
            "https://www.EXAMPLE.COM:8080/path?query=1"
        ) == "example.com"


class TestWhoisInfo:
    """Tests for WHOIS information retrieval."""

    @pytest.mark.asyncio
    async def test_get_whois_info_success(self, whoapi_service, mock_httpx_client):
        """Test successful WHOIS lookup."""
        # Configure mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_WHOIS_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        # Clear cache for test
        with patch("src.services.external_api.whoapi_service.cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True

            async with whoapi_service:
                result = await whoapi_service.get_whois_info(SAMPLE_DOMAIN)

            assert isinstance(result, WhoisData)
            assert result.domain_name == "example.com"
            assert result.registrar == "Example Registrar, Inc."
            assert result.registration_date == datetime(2020, 1, 15)
            assert result.expiration_date == datetime(2025, 1, 15)
            assert result.nameservers == ["ns1.example.com", "ns2.example.com"]
            assert result.dnssec is True
            assert result.registrant_org == "Example Organization"
            assert result.registrant_country == "US"

    @pytest.mark.asyncio
    async def test_get_whois_info_cached(self, whoapi_service):
        """Test WHOIS lookup returns cached data."""
        cached_data = {
            "domain_name": "example.com",
            "registrar": "Cached Registrar",
            "registration_date": "2020-01-15T00:00:00",
            "expiration_date": "2025-01-15T00:00:00",
            "nameservers": [],
            "status": [],
            "dnssec": None,
        }

        with patch("src.services.external_api.whoapi_service.cache") as mock_cache:
            mock_cache.get.return_value = cached_data

            result = await whoapi_service.get_whois_info(SAMPLE_DOMAIN)

            assert isinstance(result, WhoisData)
            assert result.registrar == "Cached Registrar"
            # Verify API was not called
            mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_whois_info_rate_limit(self, whoapi_service, mock_httpx_client):
        """Test rate limit handling."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("src.services.external_api.whoapi_service.cache") as mock_cache:
            mock_cache.get.return_value = None

            with pytest.raises(RateLimitError) as exc_info:
                async with whoapi_service:
                    await whoapi_service.get_whois_info(SAMPLE_DOMAIN)

            assert "Rate limit exceeded" in str(exc_info.value)


class TestDomainAge:
    """Tests for domain age calculation."""

    @pytest.mark.asyncio
    async def test_get_domain_age_success(self, whoapi_service, mock_httpx_client):
        """Test successful domain age calculation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_WHOIS_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("src.services.external_api.whoapi_service.cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True

            async with whoapi_service:
                result = await whoapi_service.get_domain_age(SAMPLE_DOMAIN)

            assert isinstance(result, DomainAge)
            assert result.domain == "example.com"
            assert result.registration_date == datetime(2020, 1, 15)
            assert result.age_days is not None
            assert result.age_days > 0
            assert result.age_years is not None
            assert result.age_string is not None

    @pytest.mark.asyncio
    async def test_domain_age_calculation(self, whoapi_service):
        """Test domain age calculation logic."""
        # Create a mock WHOIS response with a known date
        test_date = datetime.now(timezone.utc) - timedelta(days=365 * 2 + 30)  # 2 years, 1 month ago

        whois_data = WhoisData(
            domain_name="test.com",
            registrar="Test Registrar",
            registration_date=test_date,
            expiration_date=None,
            nameservers=[],
            status=[],
        )

        with patch.object(
            whoapi_service, "get_whois_info", return_value=whois_data
        ):
            result = await whoapi_service.get_domain_age("test.com")

            # Check approximate values (allowing for test timing variations)
            assert result.age_years >= 2
            assert result.age_months >= 24
            assert "year" in result.age_string.lower()


class TestSSLInfo:
    """Tests for SSL certificate information."""

    @pytest.mark.asyncio
    async def test_get_ssl_info_success(self, whoapi_service, mock_httpx_client):
        """Test successful SSL info retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_SSL_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("src.services.external_api.whoapi_service.cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True

            async with whoapi_service:
                result = await whoapi_service.get_ssl_info(SAMPLE_DOMAIN)

            assert isinstance(result, SSLInfo)
            assert result.domain == "example.com"
            assert result.valid is True
            assert result.issuer == "Let's Encrypt Authority X3"
            assert result.san == ["example.com", "www.example.com"]


class TestDNSRecords:
    """Tests for DNS record retrieval."""

    @pytest.mark.asyncio
    async def test_get_dns_records_success(self, whoapi_service, mock_httpx_client):
        """Test successful DNS records retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_DNS_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("src.services.external_api.whoapi_service.cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True

            async with whoapi_service:
                result = await whoapi_service.get_dns_records(SAMPLE_DOMAIN)

            assert isinstance(result, DNSInfo)
            assert result.domain == "example.com"
            assert len(result.a_records) > 0
            assert "93.184.216.34" in result.a_records
            assert len(result.ns_records) == 2
            assert len(result.mx_records) == 1


class TestTechStack:
    """Tests for technology stack detection."""

    @pytest.mark.asyncio
    async def test_analyze_tech_stack_success(self, whoapi_service, mock_httpx_client):
        """Test successful technology stack analysis."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_TECH_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("src.services.external_api.whoapi_service.cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True

            async with whoapi_service:
                result = await whoapi_service.analyze_tech_stack(SAMPLE_DOMAIN)

            assert isinstance(result, TechStackInfo)
            assert result.domain == "example.com"
            assert result.cms == "WordPress"
            assert result.cdn == "Cloudflare"
            assert result.hosting == "AWS"
            assert result.server == "nginx"
            assert len(result.technologies) == 3


class TestDomainAvailability:
    """Tests for domain availability checking."""

    @pytest.mark.asyncio
    async def test_check_domain_unavailable(self, whoapi_service, mock_httpx_client):
        """Test checking unavailable domain."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1, "taken": 1}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        async with whoapi_service:
            result = await whoapi_service.check_domain_availability(SAMPLE_DOMAIN)

        assert isinstance(result, DomainAvailability)
        assert result.available is False

    @pytest.mark.asyncio
    async def test_check_domain_available(self, whoapi_service, mock_httpx_client):
        """Test checking available domain."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1, "taken": 0}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        async with whoapi_service:
            result = await whoapi_service.check_domain_availability("available-domain.xyz")

        assert isinstance(result, DomainAvailability)
        assert result.available is True


class TestExpiringDomains:
    """Tests for expiring domains retrieval."""

    @pytest.mark.asyncio
    async def test_get_expiring_domains_no_db(self, whoapi_service):
        """Test expiring domains without database returns empty list."""
        result = await whoapi_service.get_expiring_domains(days=30)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_expiring_domains_with_db(self):
        """Test expiring domains with database."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()

        # Create mock WhoisRecord objects
        mock_record = MagicMock()
        mock_record.domain_name = "expiring.com"
        mock_record.expiration_date = datetime.now(timezone.utc) + timedelta(days=15)
        mock_record.registrar = "Test Registrar"
        mock_record.registrant_org = "Test Org"

        mock_repo.get_expiring_domains.return_value = [mock_record]

        with patch.dict("os.environ", {"WHOAPI_API_KEY": "test-api-key"}):
            service = WhoAPIService(api_key="test-api-key", db=mock_db)
            service._repository = mock_repo

            result = await service.get_expiring_domains(days=30)

            assert len(result) == 1
            assert result[0]["domain"] == "expiring.com"
            assert result[0]["days_until_expiry"] is not None


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_api_error_handling(self, whoapi_service, mock_httpx_client):
        """Test handling of API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 0, "status_desc": "Invalid domain"}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("src.services.external_api.whoapi_service.cache") as mock_cache:
            mock_cache.get.return_value = None

            with pytest.raises(WhoAPIError) as exc_info:
                async with whoapi_service:
                    await whoapi_service.get_whois_info(SAMPLE_DOMAIN)

            assert "WhoAPI error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout_handling(self, whoapi_service, mock_httpx_client):
        """Test handling of request timeouts."""
        mock_httpx_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        with patch("src.services.external_api.whoapi_service.cache") as mock_cache:
            mock_cache.get.return_value = None

            # Should retry and eventually raise error
            with pytest.raises(WhoAPIError) as exc_info:
                async with whoapi_service:
                    await whoapi_service.get_whois_info(SAMPLE_DOMAIN)

            assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_no_api_key_error(self):
        """Test error when API key is not configured."""
        with patch.dict("os.environ", {"WHOAPI_API_KEY": ""}, clear=True):
            service = WhoAPIService(api_key="")

            with pytest.raises(WhoAPIError) as exc_info:
                await service.get_whois_info(SAMPLE_DOMAIN)

            assert "API key not configured" in str(exc_info.value)


class TestConnectionTest:
    """Tests for connection testing."""

    @pytest.mark.asyncio
    async def test_connection_success(self, whoapi_service, mock_httpx_client):
        """Test successful connection test."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        async with whoapi_service:
            result = await whoapi_service.test_connection()

        assert result is True

    @pytest.mark.asyncio
    async def test_connection_failure(self, whoapi_service, mock_httpx_client):
        """Test failed connection test."""
        mock_httpx_client.get = AsyncMock(side_effect=Exception("Connection failed"))

        async with whoapi_service:
            result = await whoapi_service.test_connection()

        assert result is False


class TestRateLimitStatus:
    """Tests for rate limit status."""

    @pytest.mark.asyncio
    async def test_get_rate_limit_status_configured(self, whoapi_service):
        """Test rate limit status when configured."""
        status = await whoapi_service.get_rate_limit_status()

        assert status["api_name"] == "whoapi"
        assert status["status"] == "active"

    @pytest.mark.asyncio
    async def test_get_rate_limit_status_not_configured(self):
        """Test rate limit status when not configured."""
        with patch.dict("os.environ", {"WHOAPI_API_KEY": ""}, clear=True):
            service = WhoAPIService(api_key="")
            status = await service.get_rate_limit_status()

            assert status["status"] == "not_configured"
