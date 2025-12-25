"""
Unit tests for Rate Limiting Service

Tests the rate limiter functionality including:
- Sliding window algorithm
- Redis backend
- In-memory fallback
- Per-endpoint limits
- Admin bypass
"""
import pytest
import time
from unittest.mock import Mock, MagicMock, patch

from src.services.rate_limiting.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    get_rate_limiter
)


class TestRateLimitConfig:
    """Tests for RateLimitConfig."""

    def test_get_exact_match(self):
        """Test getting exact endpoint match."""
        config = RateLimitConfig.get_limit('/api/v1/auth/login')
        assert config['limit'] == 5
        assert config['window'] == 60

    def test_get_default_limit(self):
        """Test getting default limit for unknown endpoint."""
        config = RateLimitConfig.get_limit('/api/v1/unknown/endpoint')
        assert config['limit'] == 100
        assert config['window'] == 60

    def test_get_pattern_match(self):
        """Test pattern matching for dynamic routes."""
        config = RateLimitConfig.get_limit('/api/v1/companies/123')
        assert config['limit'] == 100
        assert config['window'] == 60


class TestRateLimiterMemory:
    """Tests for RateLimiter with in-memory backend."""

    @pytest.fixture
    def limiter(self):
        """Create rate limiter with in-memory backend."""
        return RateLimiter(redis_client=None)

    def test_initialization(self, limiter):
        """Test rate limiter initialization."""
        assert limiter.use_redis is False
        assert isinstance(limiter.memory_store, dict)

    def test_allow_within_limit(self, limiter):
        """Test allowing requests within limit."""
        identifier = "test_user_1"
        endpoint = "/api/v1/test"

        # First request should be allowed
        is_allowed, info = limiter.check_rate_limit(
            identifier, endpoint, limit=5, window=60
        )
        assert is_allowed is True
        assert info['limit'] == 5
        assert info['remaining'] == 4

    def test_block_over_limit(self, limiter):
        """Test blocking requests over limit."""
        identifier = "test_user_2"
        endpoint = "/api/v1/test"
        limit = 3

        # Make requests up to limit
        for i in range(limit):
            is_allowed, info = limiter.check_rate_limit(
                identifier, endpoint, limit=limit, window=60
            )
            assert is_allowed is True

        # Next request should be blocked
        is_allowed, info = limiter.check_rate_limit(
            identifier, endpoint, limit=limit, window=60
        )
        assert is_allowed is False
        assert info['remaining'] == 0

    def test_sliding_window(self, limiter):
        """Test sliding window expiration."""
        identifier = "test_user_3"
        endpoint = "/api/v1/test"
        limit = 2
        window = 1  # 1 second window

        # Use up the limit
        limiter.check_rate_limit(identifier, endpoint, limit=limit, window=window)
        limiter.check_rate_limit(identifier, endpoint, limit=limit, window=window)

        # Should be blocked
        is_allowed, _ = limiter.check_rate_limit(
            identifier, endpoint, limit=limit, window=window
        )
        assert is_allowed is False

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        is_allowed, info = limiter.check_rate_limit(
            identifier, endpoint, limit=limit, window=window
        )
        assert is_allowed is True
        assert info['remaining'] == 1

    def test_admin_bypass(self, limiter):
        """Test admin users bypass rate limits."""
        identifier = "admin_user"
        endpoint = "/api/v1/test"
        limit = 1

        # Admin should be allowed unlimited requests
        for i in range(10):
            is_allowed, info = limiter.check_rate_limit(
                identifier, endpoint, limit=limit, window=60, is_admin=True
            )
            assert is_allowed is True
            assert info['remaining'] == limit

    def test_different_endpoints_separate_limits(self, limiter):
        """Test different endpoints have separate rate limits."""
        identifier = "test_user_4"
        endpoint1 = "/api/v1/endpoint1"
        endpoint2 = "/api/v1/endpoint2"
        limit = 2

        # Use up limit on endpoint1
        limiter.check_rate_limit(identifier, endpoint1, limit=limit, window=60)
        limiter.check_rate_limit(identifier, endpoint1, limit=limit, window=60)

        # endpoint1 should be blocked
        is_allowed, _ = limiter.check_rate_limit(
            identifier, endpoint1, limit=limit, window=60
        )
        assert is_allowed is False

        # endpoint2 should still be allowed
        is_allowed, _ = limiter.check_rate_limit(
            identifier, endpoint2, limit=limit, window=60
        )
        assert is_allowed is True

    def test_reset_limit(self, limiter):
        """Test resetting rate limit."""
        identifier = "test_user_5"
        endpoint = "/api/v1/test"
        limit = 2

        # Use up the limit
        limiter.check_rate_limit(identifier, endpoint, limit=limit, window=60)
        limiter.check_rate_limit(identifier, endpoint, limit=limit, window=60)

        # Should be blocked
        is_allowed, _ = limiter.check_rate_limit(
            identifier, endpoint, limit=limit, window=60
        )
        assert is_allowed is False

        # Reset limit
        success = limiter.reset_limit(identifier, endpoint)
        assert success is True

        # Should be allowed again
        is_allowed, info = limiter.check_rate_limit(
            identifier, endpoint, limit=limit, window=60
        )
        assert is_allowed is True
        assert info['remaining'] == 1

    def test_get_stats(self, limiter):
        """Test getting rate limit statistics."""
        identifier = "test_user_6"
        endpoint = "/api/v1/test"

        # Make some requests
        limiter.check_rate_limit(identifier, endpoint, limit=5, window=60)
        limiter.check_rate_limit(identifier, endpoint, limit=5, window=60)

        # Get stats
        stats = limiter.get_stats(identifier, endpoint)
        assert stats['endpoint'] == endpoint
        assert stats['identifier'] == identifier
        assert stats['requests_in_window'] == 2
        assert 'reset_at' in stats


class TestRateLimiterRedis:
    """Tests for RateLimiter with Redis backend."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis_mock = MagicMock()
        redis_mock.ping.return_value = True
        redis_mock.zcard.return_value = 0
        redis_mock.zadd.return_value = 1
        redis_mock.expire.return_value = True
        redis_mock.zremrangebyscore.return_value = 0
        redis_mock.delete.return_value = 1
        return redis_mock

    @pytest.fixture
    def limiter(self, mock_redis):
        """Create rate limiter with Redis backend."""
        return RateLimiter(redis_client=mock_redis)

    def test_redis_initialization(self, limiter, mock_redis):
        """Test Redis initialization."""
        assert limiter.use_redis is True
        mock_redis.ping.assert_called_once()

    def test_redis_allow_within_limit(self, limiter, mock_redis):
        """Test allowing requests within limit using Redis."""
        identifier = "test_user_1"
        endpoint = "/api/v1/test"

        mock_redis.zcard.return_value = 0

        is_allowed, info = limiter.check_rate_limit(
            identifier, endpoint, limit=5, window=60
        )

        assert is_allowed is True
        assert info['limit'] == 5
        assert info['remaining'] == 4

        # Verify Redis calls
        mock_redis.zremrangebyscore.assert_called_once()
        mock_redis.zadd.assert_called_once()
        mock_redis.expire.assert_called_once()

    def test_redis_block_over_limit(self, limiter, mock_redis):
        """Test blocking requests over limit using Redis."""
        identifier = "test_user_2"
        endpoint = "/api/v1/test"

        mock_redis.zcard.return_value = 5  # Already at limit

        is_allowed, info = limiter.check_rate_limit(
            identifier, endpoint, limit=5, window=60
        )

        assert is_allowed is False
        assert info['remaining'] == 0

        # Should not add to Redis when blocked
        mock_redis.zadd.assert_not_called()

    def test_redis_fallback_on_error(self, limiter, mock_redis):
        """Test fallback to allowing request on Redis error."""
        identifier = "test_user_3"
        endpoint = "/api/v1/test"

        # Simulate Redis error
        mock_redis.zcard.side_effect = Exception("Redis connection error")

        is_allowed, info = limiter.check_rate_limit(
            identifier, endpoint, limit=5, window=60
        )

        # Should allow request on error (fail open)
        assert is_allowed is True

    def test_redis_reset_limit(self, limiter, mock_redis):
        """Test resetting limit in Redis."""
        identifier = "test_user_4"
        endpoint = "/api/v1/test"

        success = limiter.reset_limit(identifier, endpoint)
        assert success is True
        mock_redis.delete.assert_called_once()

    def test_redis_unavailable_fallback(self):
        """Test fallback to memory when Redis is unavailable."""
        mock_redis = MagicMock()
        mock_redis.ping.side_effect = Exception("Redis unavailable")

        limiter = RateLimiter(redis_client=mock_redis)

        # Should fall back to memory backend
        assert limiter.use_redis is False
        assert isinstance(limiter.memory_store, dict)


def test_get_rate_limiter_singleton():
    """Test rate limiter singleton."""
    limiter1 = get_rate_limiter()
    limiter2 = get_rate_limiter()

    assert limiter1 is limiter2
