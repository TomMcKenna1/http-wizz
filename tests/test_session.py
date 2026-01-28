import unittest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch
from http_wizz import RateLimitedSession
import aiohttp

class TestRateLimitedSession(unittest.TestCase):
    def test_session_rate_limiting(self):
        """Verify that RateLimitedSession respects the rate limit."""
        rps = 10
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        
        mock_inner_session = MagicMock()
        mock_inner_session.request.return_value = mock_response
        mock_inner_session.__aenter__.return_value = mock_inner_session
        mock_inner_session.__aexit__.return_value = None
        
        with patch('aiohttp.ClientSession', return_value=mock_inner_session):
            async def run_test():
                async with RateLimitedSession(requests_per_second=rps) as session:
                    start = time.monotonic()
                    for _ in range(5):
                        async with session.get("http://example.com"):
                            pass
                    end = time.monotonic()
                    return end - start
            
            duration = asyncio.run(run_test())
            self.assertGreaterEqual(duration, 0.35, "Requests were too fast!")

    def test_session_methods(self):
        """Verify that wrapper methods call the underlying session."""
        mock_inner_session = MagicMock()
        mock_inner_session.__aenter__.return_value = mock_inner_session
        mock_inner_session.__aexit__.return_value = None

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = MagicMock()
        mock_ctx.__aexit__.return_value = None
        
        mock_inner_session.request.return_value = mock_ctx
        
        with patch('aiohttp.ClientSession', return_value=mock_inner_session):
             async def run_test():
                async with RateLimitedSession() as session:
                    async with session.get("http://url"):
                        pass
                    
                    mock_inner_session.request.assert_called_with('GET', "http://url")

             asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()