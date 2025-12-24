"""
Redis connection and utility functions for caching and session management.
"""
from typing import Optional
import redis
from app.core.config import settings
from loguru import logger


class RedisClient:
    """Redis client wrapper with connection pooling"""

    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.pool: Optional[redis.ConnectionPool] = None

    def connect(self):
        """Initialize Redis connection pool"""
        try:
            # Parse Redis URL from settings or use default
            redis_url = getattr(settings, 'REDIS_URL', 'redis://redis:6379/0')

            self.pool = redis.ConnectionPool.from_url(
                redis_url,
                decode_responses=True,
                max_connections=10
            )

            self.client = redis.Redis(connection_pool=self.pool)

            # Test connection
            self.client.ping()
            logger.info(f"✓ Redis connected: {redis_url}")

        except Exception as e:
            logger.error(f"✗ Redis connection failed: {e}")
            self.client = None

    def disconnect(self):
        """Close Redis connection pool"""
        if self.pool:
            self.pool.disconnect()
            logger.info("Redis disconnected")

    def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        if not self.client:
            return None
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    def set(self, key: str, value: str, ex: int = None) -> bool:
        """
        Set value in Redis

        Args:
            key: Redis key
            value: Value to store
            ex: Expiration time in seconds
        """
        if not self.client:
            return False
        try:
            return self.client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.client:
            return False
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.client:
            return False
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False

    def setex(self, key: str, seconds: int, value: str) -> bool:
        """Set key with expiration"""
        if not self.client:
            return False
        try:
            return self.client.setex(key, seconds, value)
        except Exception as e:
            logger.error(f"Redis SETEX error: {e}")
            return False

    def incr(self, key: str) -> Optional[int]:
        """Increment value"""
        if not self.client:
            return None
        try:
            return self.client.incr(key)
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
            return None

    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        if not self.client:
            return False
        try:
            return self.client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis EXPIRE error: {e}")
            return False


# Global Redis client instance
redis_client = RedisClient()


def get_redis() -> RedisClient:
    """Dependency to get Redis client"""
    return redis_client
