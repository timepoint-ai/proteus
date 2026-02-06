"""
Unit tests for Redis-backed auth store (services/auth_store.py).

Uses a fake Redis client to test without a running Redis server.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from services.auth_store import AuthStore


class FakeRedis:
    """Minimal in-memory Redis fake for testing."""

    def __init__(self):
        self._store = {}
        self._ttls = {}

    def setex(self, key, ttl, value):
        self._store[key] = value
        self._ttls[key] = ttl

    def get(self, key):
        return self._store.get(key)

    def delete(self, *keys):
        for k in keys:
            self._store.pop(k, None)
            self._ttls.pop(k, None)
        return len(keys)

    def incr(self, key):
        current = int(self._store.get(key, 0))
        current += 1
        self._store[key] = str(current)
        return current

    def expire(self, key, ttl):
        self._ttls[key] = ttl

    def ttl(self, key):
        if key not in self._store:
            return -2
        return self._ttls.get(key, -1)

    def pipeline(self):
        return FakePipeline(self)

    def keys(self, pattern="*"):
        return list(self._store.keys())


class FakePipeline:
    """Fake Redis pipeline that executes commands immediately."""

    def __init__(self, fake_redis):
        self._redis = fake_redis
        self._commands = []

    def setex(self, key, ttl, value):
        self._commands.append(("setex", key, ttl, value))
        return self

    def incr(self, key):
        self._commands.append(("incr", key))
        return self

    def execute(self):
        results = []
        for cmd in self._commands:
            if cmd[0] == "setex":
                self._redis.setex(cmd[1], cmd[2], cmd[3])
                results.append(True)
            elif cmd[0] == "incr":
                results.append(self._redis.incr(cmd[1]))
        self._commands = []
        return results


@pytest.fixture
def fake_redis():
    return FakeRedis()


@pytest.fixture
def auth_store(fake_redis):
    return AuthStore(
        redis_client=fake_redis,
        nonce_ttl=300,
        otp_ttl=300,
        otp_max_send_per_window=3,
        otp_send_window=900,
        otp_max_verify_attempts=5,
        otp_verify_lockout=900,
    )


# -------------------------------------------------------------------------
# Nonce tests
# -------------------------------------------------------------------------

class TestNonceOperations:
    """Tests for nonce storage, retrieval, and deletion."""

    @pytest.mark.unit
    def test_store_and_get_nonce(self, auth_store):
        """Nonce can be stored and retrieved."""
        auth_store.store_nonce("0xABC123", "my-nonce-value")
        result = auth_store.get_nonce("0xABC123")
        assert result == "my-nonce-value"

    @pytest.mark.unit
    def test_nonce_is_case_insensitive(self, auth_store):
        """Address lookup is case-insensitive."""
        auth_store.store_nonce("0xABC123", "nonce1")
        assert auth_store.get_nonce("0xabc123") == "nonce1"

    @pytest.mark.unit
    def test_get_missing_nonce_returns_none(self, auth_store):
        """Getting a non-existent nonce returns None."""
        assert auth_store.get_nonce("0xNONEXISTENT") is None

    @pytest.mark.unit
    def test_delete_nonce(self, auth_store):
        """Deleted nonce is no longer retrievable."""
        auth_store.store_nonce("0xABC", "nonce1")
        auth_store.delete_nonce("0xABC")
        assert auth_store.get_nonce("0xABC") is None

    @pytest.mark.unit
    def test_store_nonce_overwrites_previous(self, auth_store):
        """Storing a new nonce for the same address replaces the old one."""
        auth_store.store_nonce("0xABC", "nonce1")
        auth_store.store_nonce("0xABC", "nonce2")
        assert auth_store.get_nonce("0xABC") == "nonce2"

    @pytest.mark.unit
    def test_nonce_uses_correct_ttl(self, auth_store, fake_redis):
        """Nonce is stored with the configured TTL."""
        auth_store.store_nonce("0xABC", "nonce1")
        key = "auth:nonce:0xabc"
        assert fake_redis._ttls[key] == 300


# -------------------------------------------------------------------------
# OTP tests
# -------------------------------------------------------------------------

class TestOTPOperations:
    """Tests for OTP storage, retrieval, and deletion."""

    @pytest.mark.unit
    def test_store_and_get_otp(self, auth_store):
        """OTP can be stored and retrieved."""
        auth_store.store_otp("test@example.com", "123456")
        assert auth_store.get_otp("test@example.com") == "123456"

    @pytest.mark.unit
    def test_otp_is_case_insensitive(self, auth_store):
        """Email lookup is case-insensitive."""
        auth_store.store_otp("Test@Example.com", "654321")
        assert auth_store.get_otp("test@example.com") == "654321"

    @pytest.mark.unit
    def test_get_missing_otp_returns_none(self, auth_store):
        """Getting a non-existent OTP returns None."""
        assert auth_store.get_otp("nobody@example.com") is None

    @pytest.mark.unit
    def test_delete_otp(self, auth_store):
        """Deleted OTP is no longer retrievable."""
        auth_store.store_otp("test@example.com", "123456")
        auth_store.delete_otp("test@example.com")
        assert auth_store.get_otp("test@example.com") is None

    @pytest.mark.unit
    def test_otp_uses_correct_ttl(self, auth_store, fake_redis):
        """OTP is stored with the configured TTL."""
        auth_store.store_otp("test@example.com", "123456")
        key = "auth:otp:test@example.com"
        assert fake_redis._ttls[key] == 300


# -------------------------------------------------------------------------
# OTP rate limiting tests
# -------------------------------------------------------------------------

class TestOTPRateLimiting:
    """Tests for OTP send rate limiting."""

    @pytest.mark.unit
    def test_first_otp_is_allowed(self, auth_store):
        """First OTP send should be allowed."""
        result = auth_store.check_otp_rate_limit("new@example.com")
        assert result["allowed"] is True
        assert result["remaining"] == 3

    @pytest.mark.unit
    def test_rate_limit_decrements(self, auth_store):
        """Each OTP send decrements remaining count."""
        email = "test@example.com"
        auth_store.store_otp(email, "111111")
        result = auth_store.check_otp_rate_limit(email)
        assert result["remaining"] == 2

    @pytest.mark.unit
    def test_rate_limit_blocks_after_max(self, auth_store):
        """Rate limit blocks after max sends in window."""
        email = "spammer@example.com"
        for i in range(3):
            auth_store.store_otp(email, str(100000 + i))
        result = auth_store.check_otp_rate_limit(email)
        assert result["allowed"] is False
        assert result["remaining"] == 0

    @pytest.mark.unit
    def test_rate_limit_different_emails_independent(self, auth_store):
        """Rate limits are per-email."""
        for i in range(3):
            auth_store.store_otp("user1@example.com", str(100000 + i))
        # user2 should still be allowed
        result = auth_store.check_otp_rate_limit("user2@example.com")
        assert result["allowed"] is True


# -------------------------------------------------------------------------
# OTP brute-force protection tests
# -------------------------------------------------------------------------

class TestOTPBruteForceProtection:
    """Tests for OTP verification attempt limiting."""

    @pytest.mark.unit
    def test_first_attempt_is_allowed(self, auth_store):
        """First verification attempt should be allowed."""
        result = auth_store.check_verify_attempts("test@example.com")
        assert result["allowed"] is True
        assert result["attempts"] == 0

    @pytest.mark.unit
    def test_failed_attempts_are_tracked(self, auth_store):
        """Failed attempts increment the counter."""
        email = "test@example.com"
        count = auth_store.record_failed_attempt(email)
        assert count == 1
        count = auth_store.record_failed_attempt(email)
        assert count == 2

    @pytest.mark.unit
    def test_lockout_after_max_attempts(self, auth_store):
        """Account is locked after max failed attempts."""
        email = "hacker@example.com"
        for _ in range(5):
            auth_store.record_failed_attempt(email)
        result = auth_store.check_verify_attempts(email)
        assert result["allowed"] is False
        assert result["attempts"] == 5

    @pytest.mark.unit
    def test_clear_attempts_after_success(self, auth_store):
        """Successful auth clears attempt counter."""
        email = "test@example.com"
        auth_store.record_failed_attempt(email)
        auth_store.record_failed_attempt(email)
        auth_store.clear_verify_attempts(email)
        result = auth_store.check_verify_attempts(email)
        assert result["allowed"] is True
        assert result["attempts"] == 0

    @pytest.mark.unit
    def test_different_emails_independent(self, auth_store):
        """Attempt tracking is per-email."""
        for _ in range(5):
            auth_store.record_failed_attempt("locked@example.com")
        result = auth_store.check_verify_attempts("other@example.com")
        assert result["allowed"] is True


# -------------------------------------------------------------------------
# Redis error handling tests
# -------------------------------------------------------------------------

class TestRedisErrorHandling:
    """Tests that Redis errors are handled gracefully."""

    @pytest.mark.unit
    def test_store_nonce_handles_redis_error(self):
        """store_nonce returns False on Redis error."""
        mock_redis = MagicMock()
        mock_redis.setex.side_effect = Exception("Connection refused")
        store = AuthStore(redis_client=mock_redis)
        assert store.store_nonce("0xABC", "nonce") is False

    @pytest.mark.unit
    def test_get_nonce_handles_redis_error(self):
        """get_nonce returns None on Redis error."""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("Connection refused")
        store = AuthStore(redis_client=mock_redis)
        assert store.get_nonce("0xABC") is None

    @pytest.mark.unit
    def test_rate_limit_fails_open_on_error(self):
        """Rate limit check allows request on Redis error."""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("Connection refused")
        store = AuthStore(redis_client=mock_redis)
        result = store.check_otp_rate_limit("test@example.com")
        assert result["allowed"] is True

    @pytest.mark.unit
    def test_verify_attempts_fails_open_on_error(self):
        """Verify attempts check allows request on Redis error."""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("Connection refused")
        store = AuthStore(redis_client=mock_redis)
        result = store.check_verify_attempts("test@example.com")
        assert result["allowed"] is True
