"""
TELOS — Sliding-window rate limiter for task submission.

Limits POST /task to a configurable number of requests per window
per client IP. Uses an in-memory deque per client.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request, HTTPException


class RateLimiter:
    """Sliding-window rate limiter keyed by client IP."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, client_ip: str) -> None:
        """Raise HTTPException(429) if the client has exceeded the limit."""
        now = time.monotonic()
        window = self._hits[client_ip]

        # Evict entries older than the window
        while window and window[0] <= now - self.window_seconds:
            window.popleft()

        if len(window) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded — max {self.max_requests} requests per {self.window_seconds}s",
            )
        window.append(now)


# Singleton — 10 requests per 60 seconds
_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


def get_rate_limiter() -> RateLimiter:
    return _rate_limiter


async def rate_limit_dependency(request: Request) -> None:
    """FastAPI dependency that enforces rate limiting on the caller's IP."""
    client_ip = request.client.host if request.client else "unknown"
    get_rate_limiter().check(client_ip)
