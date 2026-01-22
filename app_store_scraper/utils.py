"""Utility functions for App Store scraper."""

import time
import random
import logging
from functools import wraps
from typing import Callable, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests

# Configure logging
logger = logging.getLogger(__name__)

# Default rate limiting settings
DEFAULT_DELAY_MIN = 1.0  # Minimum delay between requests (seconds)
DEFAULT_DELAY_MAX = 2.0  # Maximum delay between requests (seconds)
DEFAULT_REQUESTS_PER_MINUTE = 20

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
]


class RateLimiter:
    """Rate limiter to prevent exceeding API limits."""

    def __init__(
        self,
        requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE,
        delay_min: float = DEFAULT_DELAY_MIN,
        delay_max: float = DEFAULT_DELAY_MAX
    ):
        self.requests_per_minute = requests_per_minute
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.last_request_time: float = 0
        self.request_count: int = 0
        self.window_start: float = time.time()

    def wait(self) -> None:
        """Wait if necessary to respect rate limits."""
        current_time = time.time()

        # Reset window if minute has passed
        if current_time - self.window_start >= 60:
            self.window_start = current_time
            self.request_count = 0

        # Check if we've exceeded rate limit
        if self.request_count >= self.requests_per_minute:
            sleep_time = 60 - (current_time - self.window_start)
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
                self.window_start = time.time()
                self.request_count = 0

        # Add random delay between requests
        time_since_last = current_time - self.last_request_time
        min_delay = self.delay_min
        if time_since_last < min_delay:
            delay = random.uniform(self.delay_min, self.delay_max)
            time.sleep(delay)

        self.last_request_time = time.time()
        self.request_count += 1


def get_random_user_agent() -> str:
    """Get a random user agent string."""
    return random.choice(USER_AGENTS)


def get_default_headers() -> dict:
    """Get default HTTP headers for requests."""
    return {
        'User-Agent': get_random_user_agent(),
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }


# Retry decorator for network requests
retry_on_network_error = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
    )),
    before_sleep=lambda retry_state: logger.warning(
        f"Request failed, retrying in {retry_state.next_action.sleep}s..."
    )
)


def safe_request(
    url: str,
    method: str = 'GET',
    rate_limiter: Optional[RateLimiter] = None,
    **kwargs
) -> requests.Response:
    """Make a rate-limited HTTP request with retries.

    Args:
        url: URL to request
        method: HTTP method
        rate_limiter: RateLimiter instance
        **kwargs: Additional arguments for requests

    Returns:
        Response object

    Raises:
        requests.exceptions.RequestException: On request failure
    """
    if rate_limiter:
        rate_limiter.wait()

    # Set default headers if not provided
    if 'headers' not in kwargs:
        kwargs['headers'] = get_default_headers()

    # Set default timeout
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 30

    @retry_on_network_error
    def _make_request():
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    return _make_request()


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"

    units = ['B', 'KB', 'MB', 'GB']
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.1f} {units[unit_index]}"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()


def chunk_list(lst: list, chunk_size: int) -> list:
    """Split list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def parse_date(date_str: str) -> Optional[str]:
    """Parse and normalize date string to YYYY-MM-DD format."""
    if not date_str:
        return None

    # Handle ISO format (2024-01-15T10:30:00Z)
    if 'T' in date_str:
        return date_str.split('T')[0]

    return date_str


class ProgressTracker:
    """Simple progress tracker for batch operations."""

    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()

    def update(self, increment: int = 1) -> None:
        """Update progress."""
        self.current += increment

    def get_progress(self) -> float:
        """Get progress as percentage."""
        if self.total == 0:
            return 100.0
        return (self.current / self.total) * 100

    def get_eta(self) -> Optional[float]:
        """Get estimated time remaining in seconds."""
        if self.current == 0:
            return None

        elapsed = time.time() - self.start_time
        rate = self.current / elapsed
        remaining = self.total - self.current

        if rate == 0:
            return None

        return remaining / rate

    def __str__(self) -> str:
        """String representation of progress."""
        progress = self.get_progress()
        eta = self.get_eta()
        eta_str = f" ETA: {eta:.0f}s" if eta else ""
        return f"{self.description}: {self.current}/{self.total} ({progress:.1f}%){eta_str}"
