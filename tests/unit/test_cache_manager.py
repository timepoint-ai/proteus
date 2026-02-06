"""
Unit tests for CacheManager service.
Tests caching operations with mocked Redis.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = MagicMock()
    mock.get.return_value = None
    mock.setex.return_value = True
    mock.delete.return_value = 1
    mock.keys.return_value = []
    return mock


@pytest.fixture
def cache_manager(mock_redis):
    """Create CacheManager instance with mocked Redis."""
    with patch('services.cache_manager.redis.Redis', return_value=mock_redis):
        from services.cache_manager import CacheManager
        manager = CacheManager()
        manager.redis_client = mock_redis
        return manager


class TestCacheManagerGet:
    """Tests for CacheManager.get()"""

    @pytest.mark.unit
    def test_get_returns_none_when_key_not_found(self, cache_manager, mock_redis):
        """get() returns None when key doesn't exist."""
        mock_redis.get.return_value = None

        result = cache_manager.get("nonexistent_key")

        assert result is None
        mock_redis.get.assert_called_once_with("nonexistent_key")

    @pytest.mark.unit
    def test_get_returns_deserialized_value(self, cache_manager, mock_redis):
        """get() returns deserialized JSON value."""
        test_data = {"market_id": 1, "status": "active"}
        mock_redis.get.return_value = json.dumps(test_data)

        result = cache_manager.get("test_key")

        assert result == test_data
        mock_redis.get.assert_called_once_with("test_key")

    @pytest.mark.unit
    def test_get_handles_redis_error_gracefully(self, cache_manager, mock_redis):
        """get() returns None on Redis error."""
        mock_redis.get.side_effect = Exception("Redis connection failed")

        result = cache_manager.get("test_key")

        assert result is None

    @pytest.mark.unit
    def test_get_handles_invalid_json(self, cache_manager, mock_redis):
        """get() returns None for invalid JSON."""
        mock_redis.get.return_value = "invalid json {"

        result = cache_manager.get("test_key")

        assert result is None


class TestCacheManagerSet:
    """Tests for CacheManager.set()"""

    @pytest.mark.unit
    def test_set_stores_value_with_default_ttl(self, cache_manager, mock_redis):
        """set() stores value with default TTL."""
        test_data = {"key": "value"}

        result = cache_manager.set("test_key", test_data)

        assert result is True
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "test_key"
        assert call_args[0][1] == 300  # default TTL
        assert json.loads(call_args[0][2]) == test_data

    @pytest.mark.unit
    def test_set_stores_value_with_custom_ttl(self, cache_manager, mock_redis):
        """set() stores value with custom TTL."""
        test_data = {"key": "value"}

        result = cache_manager.set("test_key", test_data, ttl=60)

        assert result is True
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 60

    @pytest.mark.unit
    def test_set_handles_redis_error_gracefully(self, cache_manager, mock_redis):
        """set() returns False on Redis error."""
        mock_redis.setex.side_effect = Exception("Redis connection failed")

        result = cache_manager.set("test_key", {"data": "value"})

        assert result is False


class TestCacheManagerDelete:
    """Tests for CacheManager.delete()"""

    @pytest.mark.unit
    def test_delete_removes_key(self, cache_manager, mock_redis):
        """delete() removes key from cache."""
        result = cache_manager.delete("test_key")

        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")

    @pytest.mark.unit
    def test_delete_handles_redis_error_gracefully(self, cache_manager, mock_redis):
        """delete() returns False on Redis error."""
        mock_redis.delete.side_effect = Exception("Redis connection failed")

        result = cache_manager.delete("test_key")

        assert result is False


class TestCacheManagerClearPattern:
    """Tests for CacheManager.clear_pattern()"""

    @pytest.mark.unit
    def test_clear_pattern_deletes_matching_keys(self, cache_manager, mock_redis):
        """clear_pattern() deletes all matching keys."""
        mock_redis.keys.return_value = ["market:1", "market:2", "market:3"]
        mock_redis.delete.return_value = 3

        result = cache_manager.clear_pattern("market:*")

        assert result == 3
        mock_redis.keys.assert_called_once_with("market:*")
        mock_redis.delete.assert_called_once_with("market:1", "market:2", "market:3")

    @pytest.mark.unit
    def test_clear_pattern_returns_zero_when_no_matches(self, cache_manager, mock_redis):
        """clear_pattern() returns 0 when no keys match."""
        mock_redis.keys.return_value = []

        result = cache_manager.clear_pattern("nonexistent:*")

        assert result == 0
        mock_redis.delete.assert_not_called()

    @pytest.mark.unit
    def test_clear_pattern_handles_redis_error_gracefully(self, cache_manager, mock_redis):
        """clear_pattern() returns 0 on Redis error."""
        mock_redis.keys.side_effect = Exception("Redis connection failed")

        result = cache_manager.clear_pattern("test:*")

        assert result == 0


class TestCacheManagerKeyGenerators:
    """Tests for cache key generator methods."""

    @pytest.mark.unit
    def test_market_key_format(self, cache_manager):
        """market_key() generates correct format."""
        key = cache_manager.market_key(123)
        assert key == "market:123"

    @pytest.mark.unit
    def test_actor_key_format_lowercase(self, cache_manager):
        """actor_key() generates lowercase key."""
        key = cache_manager.actor_key("0xAbCdEf123456")
        assert key == "actor:0xabcdef123456"

    @pytest.mark.unit
    def test_stats_key_format(self, cache_manager):
        """stats_key() generates correct format."""
        key = cache_manager.stats_key()
        assert key == "platform:stats"

    @pytest.mark.unit
    def test_gas_price_key_format(self, cache_manager):
        """gas_price_key() generates correct format."""
        key = cache_manager.gas_price_key()
        assert key == "chain:gas_price"
