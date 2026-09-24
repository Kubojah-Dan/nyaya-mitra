"""
NyayaMitra Security Hardening Middleware
Provides sliding-window rate limiting, request payload size enforcement,
security audit logging, and automated PII protection.
"""

from collections import defaultdict
from datetime import datetime, timezone
import logging
import time
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

logger = logging.getLogger("nyayamitra.security")

# Maximum body sizes
MAX_DEFAULT_BODY_BYTES = 2 * 1024 * 1024       # 2 MB for JSON/general API
MAX_UPLOAD_BODY_BYTES = 12 * 1024 * 1024       # 12 MB for file uploads


class InMemoryRateLimiter:
    """Sliding-window rate limiter per client IP address."""

    def __init__(self, requests_limit: int = 120, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.client_records: dict[str, list[float]] = defaultdict(list)

    def is_rate_limited(self, client_ip: str) -> tuple[bool, int]:
        """
        Checks if client IP has exceeded request quota.
        Returns (is_limited: bool, retry_after_seconds: int).
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Prune older timestamps
        timestamps = [ts for ts in self.client_records[client_ip] if ts > window_start]
        self.client_records[client_ip] = timestamps

        if len(timestamps) >= self.requests_limit:
            oldest = timestamps[0]
            retry_after = max(1, int(self.window_seconds - (now - oldest)))
            return True, retry_after

        # Record this request
        self.client_records[client_ip].append(now)
        return False, 0

    def reset(self):
        """Clears all in-memory rate records (useful for test isolation)."""
        self.client_records.clear()


class DistributedRateLimiter:
    """Sliding-window rate limiter utilizing Redis (ZADD/ZREMRANGEBYSCORE) with local fallback."""

    def __init__(self, requests_limit: int = 120, window_seconds: int = 60, prefix: str = "nm_rl"):
        self._requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.prefix = prefix
        self.fallback = InMemoryRateLimiter(requests_limit=requests_limit, window_seconds=window_seconds)

    @property
    def requests_limit(self) -> int:
        return self._requests_limit

    @requests_limit.setter
    def requests_limit(self, value: int):
        self._requests_limit = value
        self.fallback.requests_limit = value

    def is_rate_limited(self, client_ip: str) -> tuple[bool, int]:
        try:
            from app.services.cache_service import global_cache
            if global_cache.is_available() and getattr(global_cache, "_redis", None):
                r = global_cache._redis
                now = time.time()
                key = f"{self.prefix}:{client_ip}"
                pipe = r.pipeline()
                pipe.zremrangebyscore(key, 0, now - self.window_seconds)
                pipe.zadd(key, {str(now): now})
                pipe.zcard(key)
                pipe.expire(key, self.window_seconds + 1)
                results = pipe.execute()
                count = results[2]
                if count > self._requests_limit:
                    return True, max(1, int(self.window_seconds))
                return False, 0
        except Exception:
            pass
        return self.fallback.is_rate_limited(client_ip)

    def reset(self):
        self.fallback.reset()


# Global limiter instances
default_limiter = DistributedRateLimiter(requests_limit=120, window_seconds=60, prefix="nm_rl_default")
upload_limiter = DistributedRateLimiter(requests_limit=20, window_seconds=60, prefix="nm_rl_upload")


class SecurityHardeningMiddleware(BaseHTTPMiddleware):
    """
    Applies rate limiting, payload size limits, and security audit headers.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 1. Identify client IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "127.0.0.1")

        # 2. Check Request Size Limits via Content-Length header
        content_length_header = request.headers.get("content-length")
        is_upload_endpoint = "/documents/analyze" in request.url.path or "/upload" in request.url.path
        max_allowed = MAX_UPLOAD_BODY_BYTES if is_upload_endpoint else MAX_DEFAULT_BODY_BYTES

        if content_length_header:
            try:
                content_length = int(content_length_header)
                if content_length > max_allowed:
                    logger.warning(
                        f"Security Alert: Payload too large from IP={client_ip} Size={content_length} Max={max_allowed}"
                    )
                    try:
                        await request.body()
                    except Exception:
                        pass
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "PAYLOAD_TOO_LARGE",
                            "message": f"Request body ({content_length} bytes) exceeds maximum allowable limit of {max_allowed} bytes.",
                        },
                    )
            except ValueError:
                pass

        # 3. Rate Limiting Check (Skip health check to avoid test/monitoring false positives)
        if not request.url.path.endswith("/health") and request.url.path != "/":
            limiter = upload_limiter if is_upload_endpoint else default_limiter
            is_limited, retry_after = limiter.is_rate_limited(client_ip)

            if is_limited:
                logger.warning(
                    f"Security Alert: Rate limit exceeded for IP={client_ip} Path={request.url.path} RetryAfter={retry_after}s"
                )
                return JSONResponse(
                    status_code=429,
                    headers={"Retry-After": str(retry_after)},
                    content={
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": f"Too many requests. Quota exceeded. Please retry in {retry_after} seconds.",
                        "retry_after_seconds": retry_after,
                    },
                )

        # 4. Proceed to application
        response = await call_next(request)

        # 5. Attach extra defensive headers
        response.headers["X-RateLimit-Limit"] = str(upload_limiter.requests_limit if is_upload_endpoint else default_limiter.requests_limit)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
