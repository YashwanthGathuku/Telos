"""Tests for the TELOS rate limiter."""

import pytest
from fastapi import HTTPException

from services.orchestrator.middleware.rate_limit import RateLimiter


def test_allows_within_limit():
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        limiter.check("127.0.0.1")  # Should not raise


def test_blocks_over_limit():
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        limiter.check("127.0.0.1")
    with pytest.raises(HTTPException) as exc_info:
        limiter.check("127.0.0.1")
    assert exc_info.value.status_code == 429


def test_separate_clients():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    for _ in range(2):
        limiter.check("10.0.0.1")
    # Different client should still be allowed
    limiter.check("10.0.0.2")
    # First client should be blocked
    with pytest.raises(HTTPException):
        limiter.check("10.0.0.1")


def test_window_expiry(monkeypatch: pytest.MonkeyPatch):
    """After the window passes, requests should be allowed again."""
    import time

    fake_time = [100.0]
    monkeypatch.setattr(time, "monotonic", lambda: fake_time[0])

    limiter = RateLimiter(max_requests=2, window_seconds=10)
    limiter.check("127.0.0.1")
    limiter.check("127.0.0.1")

    with pytest.raises(HTTPException):
        limiter.check("127.0.0.1")

    # Advance time past the window
    fake_time[0] = 111.0
    limiter.check("127.0.0.1")  # Should succeed
