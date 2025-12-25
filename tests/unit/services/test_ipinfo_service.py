"""Tests for the IPInfo service.

These tests verify the functionality of the IPInfoService class, including:
- Single IP lookup
- Batch IP lookups
- Domain IP resolution
- Geographic distribution analysis
- Regional presence analysis
- Caching behavior
- Error handling and retry logic
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from typing import Dict, Any, List

import httpx

from src.services.external_api.ipinfo_service import (
    IPInfoService,
    IPInfoError,
    RateLimitExceededError,
)
from src.models.external_api import IPInfoRecord


# Sample test data
SAMPLE_IP = "8.8.8.8"
SAMPLE_IPV6 = "2001:4860:4860::8888"
SAMPLE_DOMAIN = "google.com"

SAMPLE_IP_RESPONSE: Dict[str, Any] = {
    "ip": "8.8.8.8",
    "hostname": "dns.google",
    "city": "Mountain View",
    "region": "California",
    "country": "US",
    "loc": "37.4056,-122.0775",
    "org": "AS15169 Google LLC",
    "postal": "94043",
    "timezone": "America/Los_Angeles"
}

SAMPLE_BATCH_RESPONSE: Dict[str, Dict[str, Any]] = {
    "8.8.8.8": {
        "ip": "8.8.8.8",
        "hostname": "dns.google",
        "city": "Mountain View",
        "region": "California",
        "country": "US",
        "loc": "37.4056,-122.0775",
        "org": "AS15169 Google LLC",
        "postal": "94043",
        "timezone": "America/Los_Angeles"
    },
    "1.1.1.1": {
        "ip": "1.1.1.1",
        "hostname": "one.one.one.one",
        "city": "Sydney",
        "region": "New South Wales",
        "country": "AU",
        "loc": "-33.8688,151.2093",
        "org": "AS13335 Cloudflare Inc",
        "postal": "2000",
        "timezone": "Australia/Sydney"
    }
}


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_repository():
    """Create a mock IPInfo repository."""
    repo = AsyncMock()
    repo.get_by_ip = AsyncMock(return_value=None)
    repo.get_by_domain = AsyncMock(return_value=[])
    repo.create_or_update = AsyncMock()
    return repo


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
def ipinfo_service(mock_db_session, mock_repository):
    """Create an IPInfoService instance with mocked dependencies."""
    service = IPInfoService(
        db=mock_db_session,
        api_key="test_api_key"
    )
    service.repository = mock_repository
    return service


class TestIPInfoService:
    """Tests for IPInfoService class."""

    @pytest.mark.asyncio
    async def test_get_ip_info_success(
        self, ipinfo_service, mock_repository, mock_http_client
    ):
        """Test successful single IP lookup."""
        # Setup mock - use MagicMock for sync methods
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_IP_RESPONSE
        mock_response.content = True
        mock_http_client.get = AsyncMock(return_value=mock_response)
        ipinfo_service._client = mock_http_client

        # Create mock record for repository return
        mock_record = MagicMock(spec=IPInfoRecord)
        mock_record.to_dict.return_value = {
            "id": 1,
            "ip_address": "8.8.8.8",
            "hostname": "dns.google",
            "city": "Mountain View",
            "region": "California",
            "country": "US",
            "location": {"lat": 37.4056, "lng": -122.0775},
            "organization": "AS15169 Google LLC",
            "postal": "94043",
            "timezone": "America/Los_Angeles",
            "domain_id": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": None
        }
        mock_repository.create_or_update.return_value = mock_record

        # Mock _api_response_to_record to avoid SQLAlchemy model creation
        with patch.object(
            ipinfo_service, '_api_response_to_record', return_value=mock_record
        ):
            # Execute
            result = await ipinfo_service.get_ip_info(SAMPLE_IP, use_cache=False)

        # Verify
        assert result["ip_address"] == "8.8.8.8"
        assert result["city"] == "Mountain View"
        assert result["country"] == "US"
        mock_http_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_ip_info_cached(
        self, ipinfo_service, mock_repository
    ):
        """Test IP lookup returns cached result."""
        # Setup cached record
        cached_record = MagicMock(spec=IPInfoRecord)
        cached_record.ip_address = SAMPLE_IP
        cached_record.city = "Mountain View"
        cached_record.created_at = datetime.utcnow()
        cached_record.to_dict.return_value = {
            "id": 1,
            "ip_address": SAMPLE_IP,
            "city": "Mountain View",
            "country": "US"
        }
        mock_repository.get_by_ip.return_value = cached_record

        # Execute
        result = await ipinfo_service.get_ip_info(SAMPLE_IP, use_cache=True)

        # Verify cache was used
        assert result["ip_address"] == SAMPLE_IP
        mock_repository.get_by_ip.assert_called_once_with(SAMPLE_IP)

    @pytest.mark.asyncio
    async def test_get_ip_info_invalid_ip(self, ipinfo_service):
        """Test IP lookup with invalid IP address."""
        with pytest.raises(ValueError) as exc_info:
            await ipinfo_service.get_ip_info("invalid-ip")

        assert "Invalid IP address format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_ip_info_rate_limit(
        self, ipinfo_service, mock_http_client
    ):
        """Test IP lookup handles rate limit error."""
        # Setup rate limit response - use MagicMock for sync methods
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.content = True
        mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
        mock_http_client.get = AsyncMock(return_value=mock_response)
        ipinfo_service._client = mock_http_client

        # Execute and verify
        with pytest.raises(RateLimitExceededError) as exc_info:
            await ipinfo_service.get_ip_info(SAMPLE_IP, use_cache=False)

        assert exc_info.value.status_code == 429
        assert "retry_after" in exc_info.value.details

    @pytest.mark.asyncio
    async def test_get_batch_ip_info_success(
        self, ipinfo_service, mock_repository, mock_http_client
    ):
        """Test successful batch IP lookup."""
        # Setup mock - use MagicMock for sync methods
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_BATCH_RESPONSE
        mock_response.content = True
        mock_http_client.post = AsyncMock(return_value=mock_response)
        ipinfo_service._client = mock_http_client

        # Create mock records
        def create_mock_record(ip: str, data: Dict[str, Any]) -> MagicMock:
            record = MagicMock(spec=IPInfoRecord)
            record.to_dict.return_value = {
                "id": 1,
                "ip_address": ip,
                "city": data["city"],
                "country": data["country"]
            }
            return record

        mock_repository.create_or_update.side_effect = [
            create_mock_record("8.8.8.8", SAMPLE_BATCH_RESPONSE["8.8.8.8"]),
            create_mock_record("1.1.1.1", SAMPLE_BATCH_RESPONSE["1.1.1.1"])
        ]

        # Mock _api_response_to_record to avoid SQLAlchemy model creation
        with patch.object(
            ipinfo_service, '_api_response_to_record',
            side_effect=[
                create_mock_record("8.8.8.8", SAMPLE_BATCH_RESPONSE["8.8.8.8"]),
                create_mock_record("1.1.1.1", SAMPLE_BATCH_RESPONSE["1.1.1.1"])
            ]
        ):
            # Execute
            ip_list = ["8.8.8.8", "1.1.1.1"]
            results = await ipinfo_service.get_batch_ip_info(ip_list, use_cache=False)

        # Verify
        assert len(results) == 2
        mock_http_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_batch_ip_info_exceeds_limit(self, ipinfo_service):
        """Test batch lookup rejects oversized requests."""
        # Create list exceeding max batch size
        ip_list = [f"192.168.1.{i}" for i in range(1001)]

        with pytest.raises(ValueError) as exc_info:
            await ipinfo_service.get_batch_ip_info(ip_list)

        assert "exceeds maximum" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_batch_ip_info_with_cache(
        self, ipinfo_service, mock_repository, mock_http_client
    ):
        """Test batch lookup uses cache for known IPs."""
        # Setup cached record for first IP
        cached_record = MagicMock(spec=IPInfoRecord)
        cached_record.ip_address = "8.8.8.8"
        cached_record.created_at = datetime.utcnow()
        cached_record.to_dict.return_value = {
            "id": 1,
            "ip_address": "8.8.8.8",
            "city": "Mountain View",
            "country": "US"
        }

        # First IP is cached, second is not
        async def mock_get_by_ip(ip: str):
            if ip == "8.8.8.8":
                return cached_record
            return None

        mock_repository.get_by_ip.side_effect = mock_get_by_ip

        # Setup mock for API call (for uncached IP) - use MagicMock for sync methods
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "1.1.1.1": SAMPLE_BATCH_RESPONSE["1.1.1.1"]
        }
        mock_response.content = True
        mock_http_client.post = AsyncMock(return_value=mock_response)
        ipinfo_service._client = mock_http_client

        new_record = MagicMock(spec=IPInfoRecord)
        new_record.to_dict.return_value = {
            "id": 2,
            "ip_address": "1.1.1.1",
            "city": "Sydney",
            "country": "AU"
        }
        mock_repository.create_or_update.return_value = new_record

        # Mock _api_response_to_record to avoid SQLAlchemy model creation
        with patch.object(
            ipinfo_service, '_api_response_to_record', return_value=new_record
        ):
            # Execute
            results = await ipinfo_service.get_batch_ip_info(
                ["8.8.8.8", "1.1.1.1"],
                use_cache=True
            )

        # Verify cached result was used
        assert len(results) >= 1
        # Verify cache check was performed
        assert mock_repository.get_by_ip.call_count >= 1

    @pytest.mark.asyncio
    async def test_get_geographic_distribution_empty(
        self, ipinfo_service, mock_repository
    ):
        """Test geographic distribution with no records."""
        mock_repository.get_by_domain.return_value = []

        result = await ipinfo_service.get_geographic_distribution(domain_id=1)

        assert result["total_ips"] == 0
        assert result["countries"] == {}
        assert result["primary_country"] is None

    @pytest.mark.asyncio
    async def test_get_geographic_distribution_with_data(
        self, ipinfo_service, mock_repository
    ):
        """Test geographic distribution with IP records."""
        # Setup mock records
        records = []
        for i, (country, region, city) in enumerate([
            ("US", "California", "Mountain View"),
            ("US", "California", "San Francisco"),
            ("US", "New York", "New York"),
            ("GB", "England", "London"),
        ]):
            record = MagicMock(spec=IPInfoRecord)
            record.country = country
            record.region = region
            record.city = city
            records.append(record)

        mock_repository.get_by_domain.return_value = records

        # Execute
        result = await ipinfo_service.get_geographic_distribution(domain_id=1)

        # Verify
        assert result["total_ips"] == 4
        assert result["countries"]["US"] == 3
        assert result["countries"]["GB"] == 1
        assert result["primary_country"] == "US"
        assert "California" in result["regions"]

    @pytest.mark.asyncio
    async def test_analyze_regional_presence_competitor_not_found(
        self, ipinfo_service, mock_db_session
    ):
        """Test regional analysis with non-existent competitor."""
        # Setup mock to return no competitor
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(ValueError) as exc_info:
            await ipinfo_service.analyze_regional_presence(competitor_id=999)

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_analyze_regional_presence_success(
        self, ipinfo_service, mock_db_session, mock_repository
    ):
        """Test successful regional presence analysis."""
        # Setup mock competitor
        mock_competitor = MagicMock()
        mock_competitor.id = 1
        mock_competitor.name = "Test Competitor"
        mock_competitor.domain = "competitor.com"

        # Setup mock domain
        mock_domain = MagicMock()
        mock_domain.id = 1
        mock_domain.name = "competitor.com"

        # Configure execute to return competitor then domain
        mock_result_competitor = MagicMock()
        mock_result_competitor.scalar_one_or_none.return_value = mock_competitor

        mock_result_domain = MagicMock()
        mock_result_domain.scalar_one_or_none.return_value = mock_domain

        mock_db_session.execute.side_effect = [
            mock_result_competitor,
            mock_result_domain
        ]

        # Setup geographic distribution mock
        records = [
            MagicMock(country="US", region="California", city="San Jose"),
            MagicMock(country="US", region="California", city="Mountain View"),
            MagicMock(country="GB", region="England", city="London"),
        ]
        mock_repository.get_by_domain.return_value = records

        # Execute
        result = await ipinfo_service.analyze_regional_presence(competitor_id=1)

        # Verify
        assert result["competitor_id"] == 1
        assert result["competitor_name"] == "Test Competitor"
        assert result["presence_score"] >= 0
        assert "regions" in result
        assert "market_coverage" in result
        assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_parse_location_valid(self, ipinfo_service):
        """Test location string parsing with valid input."""
        result = ipinfo_service._parse_location("37.4056,-122.0775")

        assert result is not None
        assert result["lat"] == 37.4056
        assert result["lng"] == -122.0775

    @pytest.mark.asyncio
    async def test_parse_location_invalid(self, ipinfo_service):
        """Test location string parsing with invalid input."""
        assert ipinfo_service._parse_location(None) is None
        assert ipinfo_service._parse_location("") is None
        assert ipinfo_service._parse_location("invalid") is None

    @pytest.mark.asyncio
    async def test_test_connection_success(
        self, ipinfo_service, mock_http_client
    ):
        """Test connection test returns true on success."""
        # Use MagicMock for sync methods
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_IP_RESPONSE
        mock_response.content = True
        mock_http_client.get = AsyncMock(return_value=mock_response)
        ipinfo_service._client = mock_http_client

        result = await ipinfo_service.test_connection()

        assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(
        self, ipinfo_service, mock_http_client
    ):
        """Test connection test returns false on failure."""
        mock_http_client.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection failed")
        )
        ipinfo_service._client = mock_http_client

        result = await ipinfo_service.test_connection()

        assert result is False

    @pytest.mark.asyncio
    async def test_get_rate_limit_status(self, ipinfo_service):
        """Test rate limit status reporting."""
        result = await ipinfo_service.get_rate_limit_status()

        assert "requests_made" in result
        assert "rate_limit" in result
        assert "remaining" in result
        assert "reset_in" in result
        assert result["rate_limit"] == ipinfo_service.RATE_LIMIT

    @pytest.mark.asyncio
    async def test_retry_on_timeout(
        self, ipinfo_service, mock_http_client
    ):
        """Test request retries on timeout."""
        # First two calls timeout, third succeeds - use MagicMock for sync methods
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_IP_RESPONSE
        mock_response.content = True

        mock_http_client.get = AsyncMock(
            side_effect=[
                httpx.TimeoutException("Timeout"),
                httpx.TimeoutException("Timeout"),
                mock_response
            ]
        )
        ipinfo_service._client = mock_http_client

        # Create mock record for repository
        mock_record = MagicMock(spec=IPInfoRecord)
        mock_record.to_dict.return_value = {"ip_address": SAMPLE_IP}
        ipinfo_service.repository.create_or_update.return_value = mock_record

        # Patch sleep and model creation to speed up test
        with patch("asyncio.sleep", new_callable=AsyncMock), \
             patch.object(
                 ipinfo_service, '_api_response_to_record', return_value=mock_record
             ):
            result = await ipinfo_service.get_ip_info(SAMPLE_IP, use_cache=False)

        assert result["ip_address"] == SAMPLE_IP
        assert mock_http_client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(
        self, ipinfo_service, mock_http_client
    ):
        """Test request fails after max retries."""
        mock_http_client.get = AsyncMock(
            side_effect=httpx.TimeoutException("Timeout")
        )
        ipinfo_service._client = mock_http_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(IPInfoError) as exc_info:
                await ipinfo_service.get_ip_info(SAMPLE_IP, use_cache=False)

        assert "retries" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_api_error_handling(
        self, ipinfo_service, mock_http_client
    ):
        """Test handling of API error responses."""
        # Use MagicMock for sync methods
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {"message": "Invalid request"}
        }
        mock_response.content = True
        mock_http_client.get = AsyncMock(return_value=mock_response)
        ipinfo_service._client = mock_http_client

        with pytest.raises(IPInfoError) as exc_info:
            await ipinfo_service.get_ip_info(SAMPLE_IP, use_cache=False)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_db_session):
        """Test async context manager behavior."""
        service = IPInfoService(db=mock_db_session, api_key="test")

        async with service as s:
            assert s._client is not None
            assert s._client_owner is True

        # Client should be closed after exit
        assert service._client is None


class TestIPInfoServiceCaching:
    """Tests focused on caching behavior."""

    @pytest.mark.asyncio
    async def test_cache_expiry(self, ipinfo_service, mock_repository):
        """Test that expired cache entries are refreshed."""
        # Setup expired cached record
        expired_record = MagicMock(spec=IPInfoRecord)
        expired_record.ip_address = SAMPLE_IP
        expired_record.created_at = datetime.utcnow() - timedelta(hours=25)  # Expired

        mock_repository.get_by_ip.return_value = expired_record

        # Should return None for expired cache
        result = await ipinfo_service._get_cached_ip_info(SAMPLE_IP)
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_valid(self, ipinfo_service, mock_repository):
        """Test that valid cache entries are returned."""
        # Setup valid cached record
        valid_record = MagicMock(spec=IPInfoRecord)
        valid_record.ip_address = SAMPLE_IP
        valid_record.created_at = datetime.utcnow() - timedelta(hours=1)  # Still valid

        mock_repository.get_by_ip.return_value = valid_record

        result = await ipinfo_service._get_cached_ip_info(SAMPLE_IP)
        assert result is valid_record


class TestIPInfoServiceHeaders:
    """Tests for request header handling."""

    def test_headers_with_api_key(self, mock_db_session):
        """Test headers include auth when API key is provided."""
        service = IPInfoService(db=mock_db_session, api_key="test_key")
        headers = service._get_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_key"

    def test_headers_without_api_key(self, mock_db_session):
        """Test headers without auth when no API key."""
        # Patch the env variable to ensure it's not picked up
        with patch.dict('os.environ', {'IPINFO_API_KEY': ''}, clear=False):
            service = IPInfoService(db=mock_db_session, api_key="")
            headers = service._get_headers()

        assert "Authorization" not in headers
        assert "Accept" in headers
        assert "Content-Type" in headers
