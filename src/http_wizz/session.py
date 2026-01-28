import aiohttp
from typing import Optional, Dict
from urllib.parse import urlparse
from .ratelimit import TokenBucket

class _RateLimitedContext:
    def __init__(self, limiter: TokenBucket, original_ctx):
        self.limiter = limiter
        self.original_ctx = original_ctx

    async def __aenter__(self):
        await self.limiter.acquire()
        return await self.original_ctx.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.original_ctx.__aexit__(exc_type, exc_val, exc_tb)

class RateLimitedSession:
    """
    Wrapper around aiohttp.ClientSession ensuring rate limits.
    """
    def __init__(
        self, 
        requests_per_second: float = 10, 
        burst_size: int = 1,
        domain_limits: Optional[Dict[str, float]] = None,
        session: Optional[aiohttp.ClientSession] = None, 
        **kwargs
    ):
        self.default_limiter = TokenBucket(burst_size, requests_per_second)
        self.domain_limiters = {
            domain: TokenBucket(burst_size, limit) 
            for domain, limit in (domain_limits or {}).items()
        }
        
        self._session = session
        self._owns_session = session is None
        self._session_kwargs = kwargs

    def _get_limiter(self, url: str) -> TokenBucket:
        try:
            domain = urlparse(url).netloc
            return self.domain_limiters.get(domain, self.default_limiter)
        except Exception:
            return self.default_limiter

    async def __aenter__(self):
        if self._session is None:
            self._session = aiohttp.ClientSession(**self._session_kwargs)
        
        if self._owns_session and not self._session.closed:
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
        limiter = self._get_limiter(url)
        return _RateLimitedContext(limiter, self._session.request(method, url, **kwargs))

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
