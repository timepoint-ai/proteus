"""
Phase 7.3: Performance Optimization - Caching Layer
Implements caching for blockchain queries with Redis
"""

import json
import logging
from typing import Any, Optional
from datetime import timedelta
import redis
import os

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Manages caching for blockchain queries to improve performance
    Phase 7 optimization for reducing RPC calls
    """
    
    def __init__(self):
        """Initialize Redis connection for caching"""
        self.redis_client = redis.Redis(
            host=os.environ.get('REDIS_HOST', 'localhost'),
            port=int(os.environ.get('REDIS_PORT', 6379)),
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        self.default_ttl = 300  # 5 minutes default cache
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.debug(f"Cache get error for {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with TTL"""
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.debug(f"Cache set error for {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Cache delete error for {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.debug(f"Cache clear error for pattern {pattern}: {e}")
            return 0
    
    # Cache key generators for common queries
    
    def market_key(self, market_id: int) -> str:
        """Generate cache key for market data"""
        return f"market:{market_id}"
    
    def actor_key(self, actor_address: str) -> str:
        """Generate cache key for actor data"""
        return f"actor:{actor_address.lower()}"
    
    def stats_key(self) -> str:
        """Generate cache key for platform stats"""
        return "platform:stats"
    
    def gas_price_key(self) -> str:
        """Generate cache key for gas price"""
        return "chain:gas_price"

# Singleton instance
cache_manager = CacheManager()