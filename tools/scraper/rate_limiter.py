"""
Rate limiter for respectful web scraping.
"""

import asyncio
import time
from typing import Optional


class RateLimiter:
    """Token bucket rate limiter for async operations."""

    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.interval = 60.0 / requests_per_minute
        self.last_request: Optional[float] = None
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Wait until a request can be made."""
        async with self._lock:
            now = time.monotonic()

            if self.last_request is not None:
                elapsed = now - self.last_request
                if elapsed < self.interval:
                    await asyncio.sleep(self.interval - elapsed)

            self.last_request = time.monotonic()

    def reset(self):
        """Reset the rate limiter."""
        self.last_request = None
