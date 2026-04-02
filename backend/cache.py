"""
LinkedIn Platform — Redis Cache Layer
Provides caching utilities for SQL query results and frequently accessed data.
"""

import json
import redis
from typing import Optional, Any
from config import settings


class RedisCache:
    """Redis-based caching layer for SQL query optimization."""

    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
        self.default_ttl = settings.REDIS_CACHE_TTL

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache. Returns None if key doesn't exist."""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except (redis.ConnectionError, json.JSONDecodeError):
            return None

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set a value in cache with optional TTL (seconds)."""
        try:
            serialized = json.dumps(value, default=str)
            self.client.setex(key, ttl or self.default_ttl, serialized)
            return True
        except (redis.ConnectionError, TypeError):
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        try:
            self.client.delete(key)
            return True
        except redis.ConnectionError:
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern. Returns count of deleted keys."""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except redis.ConnectionError:
            return 0

    def flush_all(self) -> bool:
        """Clear all cache entries."""
        try:
            self.client.flushdb()
            return True
        except redis.ConnectionError:
            return False

    def health_check(self) -> bool:
        """Check if Redis is reachable."""
        try:
            return self.client.ping()
        except redis.ConnectionError:
            return False


# Singleton cache instance
cache = RedisCache()
