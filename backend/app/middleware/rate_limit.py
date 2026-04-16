"""
Rate Limiting Middleware

Implements rate limiting to prevent:
- Brute force attacks
- API abuse
- DoS attacks

Uses Redis for distributed rate limiting support.
"""

import time
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
import redis.asyncio as redis
from loguru import logger

from app.core.config import settings
from app.core.exceptions import RateLimitExceededError


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm

    Features:
    - Per-IP rate limiting
    - Per-user rate limiting (when authenticated)
    - Different limits for different endpoints
    - Distributed support via Redis
    """

    def __init__(
        self,
        app,
        redis_client: Optional[redis.Redis] = None,
        requests_per_minute: int = 60,
        auth_requests_per_minute: int = 5,
    ):
        super().__init__(app)
        self.redis_client = redis_client
        self.requests_per_minute = requests_per_minute
        self.auth_requests_per_minute = auth_requests_per_minute

        # Endpoints that need stricter rate limiting
        self.strict_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
        ]

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process request with rate limiting

        Args:
            request: FastAPI request
            call_next: Next middleware in chain

        Returns:
            Response

        Raises:
            RateLimitExceededError: If rate limit exceeded
        """
        # Skip rate limiting if disabled
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Determine rate limit based on endpoint
        is_auth_endpoint = any(
            request.url.path.startswith(endpoint)
            for endpoint in self.strict_endpoints
        )

        if is_auth_endpoint:
            max_requests = self.auth_requests_per_minute
            window = 60  # seconds
        else:
            max_requests = self.requests_per_minute
            window = 60

        # Get client identifier (IP or user ID)
        client_id = self._get_client_identifier(request)

        # Check rate limit
        is_allowed, remaining = await self._check_rate_limit(
            client_id=client_id,
            max_requests=max_requests,
            window=window
        )

        # Add rate limit headers
        response = None
        if is_allowed:
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window)
        else:
            # Rate limit exceeded
            logger.warning(
                f"Rate limit exceeded for {client_id}",
                extra={
                    "client_id": client_id,
                    "path": request.url.path,
                    "limit": max_requests
                }
            )
            raise RateLimitExceededError(limit=max_requests, window=window)

        return response

    def _get_client_identifier(self, request: Request) -> str:
        """
        Get unique client identifier

        Uses user ID if authenticated, otherwise IP address

        Args:
            request: FastAPI request

        Returns:
            Client identifier string
        """
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    async def _check_rate_limit(
        self,
        client_id: str,
        max_requests: int,
        window: int
    ) -> tuple[bool, int]:
        """
        Check if request is within rate limit

        Uses sliding window algorithm with Redis

        Args:
            client_id: Unique client identifier
            max_requests: Maximum requests allowed
            window: Time window in seconds

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        if not self.redis_client:
            # Rate limiting not available without Redis
            return True, max_requests

        try:
            # Use Redis sorted set for sliding window
            current_time = time.time()
            window_start = current_time - window

            # Redis key for this client
            key = f"rate_limit:{client_id}"

            # Remove old entries outside the window
            await self.redis_client.zremrangebyscore(
                key,
                0,
                window_start
            )

            # Count requests in current window
            request_count = await self.redis_client.zcard(key)

            # Check if limit exceeded
            if request_count >= max_requests:
                return False, 0

            # Add current request
            await self.redis_client.zadd(
                key,
                {str(current_time): current_time}
            )

            # Set expiration on key
            await self.redis_client.expire(key, window)

            # Calculate remaining requests
            remaining = max_requests - request_count - 1

            return True, remaining

        except Exception as e:
            # Log error but don't block request if Redis fails
            logger.error(f"Rate limit check failed: {str(e)}")
            return True, max_requests


# Decorator for endpoint-specific rate limiting


def rate_limit(
    requests: int,
    window: int = 60,
    key_func: Optional[Callable] = None
):
    """
    Decorator for endpoint-specific rate limiting

    Usage:
        @app.get("/api/expensive")
        @rate_limit(requests=10, window=60)
        async def expensive_endpoint():
            return {"status": "ok"}

    Args:
        requests: Maximum requests allowed
        window: Time window in seconds
        key_func: Custom function to generate rate limit key
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Implementation would go here
            # This is a placeholder for future enhancement
            return await func(*args, **kwargs)
        return wrapper
    return decorator
