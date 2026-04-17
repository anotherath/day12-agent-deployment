"""Rate limiting — 10 requests per minute per user."""
import time
import logging
from collections import defaultdict, deque

from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)

# In-memory rate windows (per API key prefix)
# NOTE: For true statelessness with multiple instances, use Redis.
_rate_windows: dict[str, deque] = defaultdict(deque)


def check_rate_limit(key: str):
    """Sliding window rate limiter. Raises 429 if exceeded."""
    now = time.time()
    window = _rate_windows[key]
    # Remove timestamps older than 60 seconds
    while window and window[0] < now - 60:
        window.popleft()
    if len(window) >= settings.rate_limit_per_minute:
        logger.warning(f"Rate limit exceeded for key {key[:8]}...")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
            headers={"Retry-After": "60"},
        )
    window.append(now)
