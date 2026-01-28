import asyncio
import logging
import datetime
from typing import List, Optional, Any, Callable, Dict
from email.utils import parsedate_to_datetime

import aiohttp
from .session import RateLimitedSession

logger = logging.getLogger(__name__)

class WizzClient:
    """High-level async HTTP client with rate limiting, retries, and domain throttling."""
    
    def __init__(
        self, 
        requests_per_second: float = 10, 
        burst_size: int = 1,
        domain_limits: Optional[Dict[str, float]] = None,
        max_retries: int = 5, 
        initial_retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        should_retry: Optional[Callable[[aiohttp.ClientResponse, Any], bool]] = None
    ):
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.domain_limits = domain_limits
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.exponential_backoff = exponential_backoff
        self.should_retry = should_retry
        self._session: Optional[RateLimitedSession] = None

    async def __aenter__(self):
        self._session = RateLimitedSession(
            requests_per_second=self.requests_per_second,
            burst_size=self.burst_size,
            domain_limits=self.domain_limits
        )
        await self._session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)
            self._session = None

    def _parse_retry_after(self, header_val: str) -> Optional[float]:
        try:
            return float(header_val)
        except ValueError:
            pass
        
        try:
            dt = parsedate_to_datetime(header_val)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            now = datetime.datetime.now(datetime.timezone.utc)
            return max(0.0, (dt - now).total_seconds())
        except Exception:
            return None

    async def _fetch(self, session: RateLimitedSession, url: str) -> Optional[Any]:
        retries = 0
        delay = self.initial_retry_delay
        
        while retries <= self.max_retries:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        try:
                            content = await response.json() if response.content_type == 'application/json' else await response.text()

                            if self.should_retry and self.should_retry(response, content):
                                logger.warning(f"Custom retry condition met for {url}. Retrying...")
                            else:
                                return content
                        except Exception as e:
                             logger.error(f"Failed to parse response from {url}: {e}")
                             return None
                    
                    elif response.status in (429, 503):
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            wait_time = self._parse_retry_after(retry_after)
                            if wait_time is not None:
                                logger.info(f"Rate limited (status {response.status}). Sleeping for {wait_time:.2f}s.")
                                await asyncio.sleep(wait_time)
                                retries += 1
                                continue
                        
                        logger.warning(f"Status {response.status} for {url}. Retrying in {delay}s...")
                        
                    else:
                        logger.warning(f"Non-200 status {response.status} for {url}. Retrying in {delay}s...")
                        
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}. Retrying in {delay}s...")

            retries += 1
            if retries > self.max_retries:
                logger.error(f"Max retries reached for {url}.")
                return None
            
            await asyncio.sleep(delay)
            if self.exponential_backoff:
                delay *= 2
        return None

    async def fetch_all(self, urls: List[str], show_progress: bool = False) -> List[Optional[Any]]:
        """Concurrent fetch of multiple URLs."""
        session_created = False
        session = self._session
        
        if session is None:
            session = RateLimitedSession(
                requests_per_second=self.requests_per_second,
                burst_size=self.burst_size,
                domain_limits=self.domain_limits
            )
            await session.__aenter__()
            session_created = True

        pbar = None
        if show_progress:
            try:
                from tqdm import tqdm
                pbar = tqdm(total=len(urls), desc="Fetching URLs", unit="url")
            except ImportError:
                pass

        try:
            async def _task(u):
                res = await self._fetch(session, u)
                if pbar:
                    pbar.update(1)
                return res

            return await asyncio.gather(*[_task(url) for url in urls])
            
        finally:
            if pbar:
                pbar.close()
            if session_created:
                await session.__aexit__(None, None, None)

def fetch_urls(
    urls: List[str], 
    requests_per_second: float = 10, 
    burst_size: int = 1,
    domain_limits: Optional[Dict[str, float]] = None,
    max_retries: int = 5,
    exponential_backoff: bool = True,
    should_retry: Optional[Callable[[aiohttp.ClientResponse, Any], bool]] = None,
    show_progress: bool = False
) -> List[Optional[Any]]:
    """Synchronous convenience wrapper for fetch_all."""
    client = WizzClient(
        requests_per_second=requests_per_second, 
        burst_size=burst_size,
        domain_limits=domain_limits,
        max_retries=max_retries,
        exponential_backoff=exponential_backoff,
        should_retry=should_retry
    )
    return asyncio.run(client.fetch_all(urls, show_progress=show_progress))