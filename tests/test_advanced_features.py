import unittest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch
from http_wizz import WizzClient

class TestNewFeatures(unittest.TestCase):
    def test_multi_domain_throttling(self):
        domain_limits = {
            "fast.com": 100,
            "slow.com": 1
        }
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="ok")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_inner = MagicMock()
        mock_inner.request.return_value = mock_response
        mock_inner.__aenter__ = AsyncMock(return_value=mock_inner)
        mock_inner.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_inner):
            async def run():
                async with WizzClient(requests_per_second=10, domain_limits=domain_limits) as client:
                    start = time.monotonic()
                    await client.fetch_all(["http://slow.com/1", "http://slow.com/2"])
                    mid = time.monotonic()
                    
                    await client.fetch_all(["http://fast.com/" + str(i) for i in range(5)])
                    end = time.monotonic()
                    
                    return mid - start, end - mid

            slow_duration, fast_duration = asyncio.run(run())
            
            self.assertGreaterEqual(slow_duration, 0.95, f"Slow domain too fast: {slow_duration}")
            self.assertLess(fast_duration, 0.3, f"Fast domain too slow: {fast_duration}")
            
    def test_retry_after_header(self):
        resp_429 = MagicMock()
        resp_429.status = 429
        resp_429.headers = {"Retry-After": "1.5"}
        resp_429.__aenter__ = AsyncMock(return_value=resp_429)
        resp_429.__aexit__ = AsyncMock(return_value=None)
        
        resp_200 = MagicMock()
        resp_200.status = 200
        resp_200.text = AsyncMock(return_value="ok")
        resp_200.__aenter__ = AsyncMock(return_value=resp_200)
        resp_200.__aexit__ = AsyncMock(return_value=None)
        
        mock_inner = MagicMock()
        mock_inner.request.side_effect = [resp_429, resp_200]
        mock_inner.__aenter__ = AsyncMock(return_value=mock_inner)
        mock_inner.__aexit__ = AsyncMock(return_value=None)

        with patch('aiohttp.ClientSession', return_value=mock_inner):
             with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                with patch('http_wizz.ratelimit.TokenBucket.acquire', new_callable=AsyncMock):
                    client = WizzClient()
                    asyncio.run(client.fetch_all(["http://site.com"]))
                    
                    retry_sleeps = [c.args[0] for c in mock_sleep.call_args_list if c.args and abs(c.args[0] - 1.5) < 0.01]
                    self.assertEqual(len(retry_sleeps), 1, "Did not sleep for Retry-After duration")

if __name__ == '__main__':
    unittest.main()