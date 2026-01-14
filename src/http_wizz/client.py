import asyncio
import logging
import time
from typing import List, Optional, Any, Callable
import aiohttp

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Limits the rate of execution to a specific number of calls per second.
    """
    def __init__(self, calls_per_second: float):
        if calls_per_second <= 0:
            raise ValueError("calls_per_second must be positive")
        self.interval = 1.0 / calls_per_second
        self.last_call_time = 0.0
        self._lock = asyncio.Lock()

    async def wait(self):
        """
        Waits until enough time has passed to maintain the rate limit.
        """
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_call_time
            if elapsed < self.interval:
                sleep_time = self.interval - elapsed
                await asyncio.sleep(sleep_time)
            self.last_call_time = time.monotonic()

class _RateLimitedRequestContextManager:
    """
    Wraps aiohttp's request context manager to wait for rate limit before sending request.
    """
    def __init__(self, limiter: RateLimiter, original_ctx):
        self.limiter = limiter
        self.original_ctx = original_ctx

    async def __aenter__(self):
        await self.limiter.wait()
        return await self.original_ctx.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.original_ctx.__aexit__(exc_type, exc_val, exc_tb)

class RateLimitedSession:
    """
    A wrapper around aiohttp.ClientSession that enforces a rate limit on all requests.
    """
    def __init__(self, requests_per_second: float = 10, session: Optional[aiohttp.ClientSession] = None, **kwargs):
        self.limiter = RateLimiter(requests_per_second)
        self._session = session
        self._owns_session = session is None
        self._session_kwargs = kwargs

    async def __aenter__(self):
        if self._session is None:
            self._session = aiohttp.ClientSession(**self._session_kwargs)
        if self._owns_session and self._session.closed:
             # Re-open if possible? ClientSession usually cannot be re-opened.
             # Assume new session if owned and None.
             pass
        elif not self._owns_session:
             # External session, assume managed externally.
             pass
        else:
             # We own it, enter it.
             await self._session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._owns_session and self._session:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)

    async def close(self):
        if self._owns_session and self._session:
            await self._session.close()

    def request(self, method: str, url: str, **kwargs):
        if self._session is None:
             raise RuntimeError("Session not initialized. Use 'async with RateLimitedSession(...)'.")
        return _RateLimitedRequestContextManager(self.limiter, self._session.request(method, url, **kwargs))

    def get(self, url: str, **kwargs):
        return self.request(aiohttp.hdrs.METH_GET, url, **kwargs)

    def post(self, url: str, **kwargs):
        return self.request(aiohttp.hdrs.METH_POST, url, **kwargs)
        
    def put(self, url: str, **kwargs):
        return self.request(aiohttp.hdrs.METH_PUT, url, **kwargs)

    def delete(self, url: str, **kwargs):
        return self.request(aiohttp.hdrs.METH_DELETE, url, **kwargs)

    def head(self, url: str, **kwargs):
        return self.request(aiohttp.hdrs.METH_HEAD, url, **kwargs)

    def options(self, url: str, **kwargs):
        return self.request(aiohttp.hdrs.METH_OPTIONS, url, **kwargs)

    def patch(self, url: str, **kwargs):
        return self.request(aiohttp.hdrs.METH_PATCH, url, **kwargs)

class WizzClient:
    """
    A high-level client to fetch URLs asynchronously with rate limiting and retries.
    """
    def __init__(
        self, 
        requests_per_second: float = 10, 
        max_retries: int = 5, 
        initial_retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        should_retry: Optional[Callable[[aiohttp.ClientResponse, Any], bool]] = None
    ):
        self.requests_per_second = requests_per_second
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.exponential_backoff = exponential_backoff
        self.should_retry = should_retry

    async def _fetch(self, session: RateLimitedSession, url: str) -> Optional[Any]:
        retries = 0
        current_delay = self.initial_retry_delay
        
        while retries <= self.max_retries:
            # session.get already handles waiting for the rate limiter
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        try:
                            # Try to return JSON, otherwise return text if not JSON
                            if response.content_type == 'application/json':
                                content = await response.json()
                            else:
                                content = await response.text()

                            if self.should_retry and self.should_retry(response, content):
                                logger.warning(f"Custom retry condition met for {url}. Retrying in {current_delay}s...")
                                # Fall through to retry logic
                            else:
                                return content
                        except Exception as e:
                             logger.error(f"Failed to parse response from {url}: {e}")
                             return None
                    else:
                        logger.warning(f"Non-200 status {response.status} for {url}. Retrying in {current_delay}s...")
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}. Retrying in {current_delay}s...")

            retries += 1
            if retries > self.max_retries:
                logger.error(f"Max retries reached for {url}.")
                return None
            
            await asyncio.sleep(current_delay)
            if self.exponential_backoff:
                current_delay *= 2
        return None

    async def fetch_all(self, urls: List[str]) -> List[Optional[Any]]:
        """
        Fetches all URLs respecting the rate limit.
        """
        async with RateLimitedSession(requests_per_second=self.requests_per_second) as session:
            tasks = [self._fetch(session, url) for url in urls]
            return await asyncio.gather(*tasks)

def fetch_urls(
    urls: List[str], 
    requests_per_second: float = 10, 
    max_retries: int = 5,
    exponential_backoff: bool = True,
    should_retry: Optional[Callable[[aiohttp.ClientResponse, Any], bool]] = None
) -> List[Optional[Any]]:
    """
    Convenience function to fetch a list of URLs synchronously (blocking until done).
    
    Args:
        urls: List of URLs to fetch.
        requests_per_second: Maximum requests per second.
        max_retries: Maximum number of retries per URL.
        exponential_backoff: Whether to double the delay after each retry.
        should_retry: Callable that returns True if we should retry.
        
    Returns:
        List of results (JSON dict, string, or None).
    """
    client = WizzClient(
        requests_per_second=requests_per_second, 
        max_retries=max_retries,
        exponential_backoff=exponential_backoff,
        should_retry=should_retry
    )
    return asyncio.run(client.fetch_all(urls))
