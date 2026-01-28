import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from http_wizz import WizzClient

class TestCustomRetry(unittest.TestCase):
    def test_should_retry_callback(self):
        """Verify that should_retry callback triggers retries even on 200 OK."""
        fail_content = {"error": "Try again"}
        success_content = {"status": "ok"}
        
        resp1 = MagicMock(status=200, content_type="application/json")
        resp1.json = AsyncMock(return_value=fail_content)
        resp1.__aenter__ = AsyncMock(return_value=resp1)
        resp1.__aexit__ = AsyncMock(return_value=None)
        
        resp2 = MagicMock(status=200, content_type="application/json")
        resp2.json = AsyncMock(return_value=success_content)
        resp2.__aenter__ = AsyncMock(return_value=resp2)
        resp2.__aexit__ = AsyncMock(return_value=None)
        
        client = WizzClient(
            requests_per_second=100,
            max_retries=3,
            should_retry=lambda r, c: "error" in c
        )
        
        mock_session = MagicMock()
        mock_session.request.side_effect = [resp1, resp2]
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('http_wizz.ratelimit.TokenBucket.acquire', new_callable=AsyncMock):
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    results = asyncio.run(client.fetch_all(["http://api.com/status"]))
                    
                    self.assertEqual(results, [success_content])
                    self.assertEqual(mock_session.request.call_count, 2)

if __name__ == '__main__':
    unittest.main()
