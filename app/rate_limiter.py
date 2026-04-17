"""
Rate limiting module for VinFast Assistant
Sliding window algorithm with Redis support for scaling
"""

import time
from collections import defaultdict, deque
from typing import Optional
import os


class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(deque)
        # Checklist requirement: 10 requests per minute
        self.max_requests = int(os.getenv("RATE_LIMIT_MAX", "10"))
        self.window_seconds = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        self.redis_url = os.getenv("REDIS_URL", "")

    def is_allowed(self, client_key: str) -> bool:
        """
        Check if request is allowed under rate limit
        Returns False if limit exceeded, True otherwise
        """
        current_time = time.time()

        # Clean old requests outside the window
        request_queue = self.requests[client_key]
        while request_queue and request_queue[0] < current_time - self.window_seconds:
            request_queue.popleft()

        # Check if under limit
        if len(request_queue) >= self.max_requests:
            return False

        # Add current request
        request_queue.append(current_time)
        return True

    def get_remaining_requests(self, client_key: str) -> int:
        """Get remaining requests allowed in current window"""
        request_queue = self.requests[client_key]
        current_time = time.time()

        # Clean old requests
        while request_queue and request_queue[0] < current_time - self.window_seconds:
            request_queue.popleft()

        return max(0, self.max_requests - len(request_queue))

    def get_reset_time(self, client_key: str) -> int:
        """Get seconds until rate limit resets"""
        request_queue = self.requests[client_key]
        if not request_queue:
            return 0

        oldest_request = request_queue[0]
        reset_time = int((oldest_request + self.window_seconds) - time.time())
        return max(0, reset_time)

    def active_keys_count(self) -> int:
        """Return count of unique client keys currently tracked"""
        current_time = time.time()
        count = 0
        for key in list(self.requests.keys()):
            self._clean(key)
            if self.requests[key]:
                count += 1
        return count

    def _clean(self, client_key: str) -> None:
        """Remove requests outside the sliding window for a key."""
        current_time = time.time()
        queue = self.requests[client_key]
        while queue and queue[0] < current_time - self.window_seconds:
            queue.popleft()


# Global rate limiter instance
rate_limiter = RateLimiter()
