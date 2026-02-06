"""
Redis-backed authentication store for nonces and OTPs.

Replaces in-memory dicts with persistent Redis storage with TTL expiry,
rate limiting for OTP sends, and brute-force protection for OTP verification.
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import redis

from utils.logging_config import get_logger

logger = get_logger(__name__)


class AuthStore:
    """Redis-backed store for auth nonces and OTPs with TTL expiry."""

    # Redis key prefixes
    NONCE_PREFIX = "auth:nonce:"
    OTP_PREFIX = "auth:otp:"
    OTP_RATE_PREFIX = "auth:otp_rate:"
    OTP_ATTEMPTS_PREFIX = "auth:otp_attempts:"

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        nonce_ttl: int = 300,
        otp_ttl: int = 300,
        otp_max_send_per_window: int = 3,
        otp_send_window: int = 900,
        otp_max_verify_attempts: int = 5,
        otp_verify_lockout: int = 900,
    ):
        self.redis = redis_client or redis.Redis(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", 6379)),
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        self.nonce_ttl = nonce_ttl
        self.otp_ttl = otp_ttl
        self.otp_max_send_per_window = otp_max_send_per_window
        self.otp_send_window = otp_send_window
        self.otp_max_verify_attempts = otp_max_verify_attempts
        self.otp_verify_lockout = otp_verify_lockout

    # -------------------------------------------------------------------------
    # Nonce operations
    # -------------------------------------------------------------------------

    def store_nonce(self, address: str, nonce: str) -> bool:
        """Store a nonce for a wallet address with TTL."""
        key = self.NONCE_PREFIX + address.lower()
        data = {
            "nonce": nonce,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            self.redis.setex(key, self.nonce_ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.error("Failed to store nonce", address=address, error=str(e))
            return False

    def get_nonce(self, address: str) -> Optional[str]:
        """Get the stored nonce for an address. Returns None if expired/missing."""
        key = self.NONCE_PREFIX + address.lower()
        try:
            raw = self.redis.get(key)
            if raw:
                data = json.loads(raw)
                return data.get("nonce")
            return None
        except Exception as e:
            logger.error("Failed to get nonce", address=address, error=str(e))
            return None

    def delete_nonce(self, address: str) -> bool:
        """Delete a used nonce."""
        key = self.NONCE_PREFIX + address.lower()
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error("Failed to delete nonce", address=address, error=str(e))
            return False

    # -------------------------------------------------------------------------
    # OTP operations
    # -------------------------------------------------------------------------

    def check_otp_rate_limit(self, email: str) -> Dict[str, Any]:
        """Check if OTP send rate limit has been exceeded.

        Returns:
            Dict with 'allowed' bool and 'remaining' count.
        """
        key = self.OTP_RATE_PREFIX + email.lower()
        try:
            count = self.redis.get(key)
            current = int(count) if count else 0
            remaining = max(0, self.otp_max_send_per_window - current)
            return {"allowed": current < self.otp_max_send_per_window, "remaining": remaining}
        except Exception as e:
            logger.error("Failed to check OTP rate limit", email=email, error=str(e))
            # Fail open to avoid locking out users on Redis errors
            return {"allowed": True, "remaining": self.otp_max_send_per_window}

    def store_otp(self, email: str, otp: str) -> bool:
        """Store an OTP for an email with TTL and increment rate counter."""
        otp_key = self.OTP_PREFIX + email.lower()
        rate_key = self.OTP_RATE_PREFIX + email.lower()

        data = {
            "otp": otp,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            pipe = self.redis.pipeline()
            pipe.setex(otp_key, self.otp_ttl, json.dumps(data))
            pipe.incr(rate_key)
            # Only set TTL on rate key if it's new (INCR returns 1 for new keys)
            pipe.execute()

            # Ensure rate key has expiry
            if self.redis.ttl(rate_key) == -1:
                self.redis.expire(rate_key, self.otp_send_window)

            return True
        except Exception as e:
            logger.error("Failed to store OTP", email=email, error=str(e))
            return False

    def get_otp(self, email: str) -> Optional[str]:
        """Get stored OTP for an email. Returns None if expired/missing."""
        key = self.OTP_PREFIX + email.lower()
        try:
            raw = self.redis.get(key)
            if raw:
                data = json.loads(raw)
                return data.get("otp")
            return None
        except Exception as e:
            logger.error("Failed to get OTP", email=email, error=str(e))
            return None

    def delete_otp(self, email: str) -> bool:
        """Delete a used OTP."""
        key = self.OTP_PREFIX + email.lower()
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error("Failed to delete OTP", email=email, error=str(e))
            return False

    # -------------------------------------------------------------------------
    # OTP brute-force protection
    # -------------------------------------------------------------------------

    def check_verify_attempts(self, email: str) -> Dict[str, Any]:
        """Check if OTP verification attempts have been exceeded.

        Returns:
            Dict with 'allowed' bool and 'attempts' count.
        """
        key = self.OTP_ATTEMPTS_PREFIX + email.lower()
        try:
            count = self.redis.get(key)
            current = int(count) if count else 0
            return {
                "allowed": current < self.otp_max_verify_attempts,
                "attempts": current,
            }
        except Exception as e:
            logger.error("Failed to check verify attempts", email=email, error=str(e))
            return {"allowed": True, "attempts": 0}

    def record_failed_attempt(self, email: str) -> int:
        """Record a failed OTP verification attempt. Returns new attempt count."""
        key = self.OTP_ATTEMPTS_PREFIX + email.lower()
        try:
            count = self.redis.incr(key)
            if count == 1:
                self.redis.expire(key, self.otp_verify_lockout)
            return count
        except Exception as e:
            logger.error("Failed to record attempt", email=email, error=str(e))
            return 0

    def clear_verify_attempts(self, email: str) -> bool:
        """Clear verification attempts after successful auth."""
        key = self.OTP_ATTEMPTS_PREFIX + email.lower()
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error("Failed to clear attempts", email=email, error=str(e))
            return False


def get_auth_store() -> AuthStore:
    """Get or create the auth store singleton with config values."""
    global _auth_store
    if _auth_store is None:
        try:
            from config_chain import chain_config

            _auth_store = AuthStore(
                nonce_ttl=getattr(chain_config, "NONCE_TTL", 300),
                otp_ttl=getattr(chain_config, "OTP_TTL", 300),
                otp_max_send_per_window=getattr(chain_config, "OTP_MAX_SEND_PER_WINDOW", 3),
                otp_send_window=getattr(chain_config, "OTP_SEND_WINDOW", 900),
                otp_max_verify_attempts=getattr(chain_config, "OTP_MAX_VERIFY_ATTEMPTS", 5),
                otp_verify_lockout=getattr(chain_config, "OTP_VERIFY_LOCKOUT", 900),
            )
        except Exception as e:
            logger.warning("Failed to load config, using defaults", error=str(e))
            _auth_store = AuthStore()
    return _auth_store


_auth_store: Optional[AuthStore] = None
