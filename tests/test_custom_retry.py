import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from http_wizz import WizzClient

class TestCustomRetry(unittest.TestCase):
    def test_should_retry_callback(self):
        """
        Verify that should_retry callback triggers retries even on 200 OK.
        """
        # Scenario: API returns 200 but content says {"error": "Try again"}
        # Then eventually returns {"status": "ok"}
        
        fail_content = {"error": "Try again"}
        success_content = {"status": "ok"}
        
        # Mock response sequence
        # Call 1: 200 OK, but fail_content
        # Call 2: 200 OK, success_content
        
        resp1 = MagicMock()
        resp1.status = 200
        resp1.json = AsyncMock(return_value=fail_content)
        resp1.content_type = "application/json"
        resp1.__aenter__ = AsyncMock(return_value=resp1)
        resp1.__aexit__ = AsyncMock(return_value=None)
        
        resp2 = MagicMock()
        resp2.status = 200
        resp2.json = AsyncMock(return_value=success_content)
        resp2.content_type = "application/json"
        resp2.__aenter__ = AsyncMock(return_value=resp2)
        resp2.__aexit__ = AsyncMock(return_value=None)
        
        # Define callback
        def my_retry_check(response, content):
            return "error" in content
            
        client = WizzClient(
            requests_per_second=100,
            max_retries=3,
            should_retry=my_retry_check
        )
        
        mock_session = MagicMock()
        # side_effect for request(): first call returns resp1, second call returns resp2
        mock_session.request.side_effect = [resp1, resp2]
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('http_wiz.client.RateLimiter.wait', new_callable=AsyncMock):
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    results = asyncio.run(client.fetch_all(["http://api.com/status"]))
                    
                    self.assertEqual(results, [success_content])
                    self.assertEqual(mock_session.request.call_count, 2)

if __name__ == '__main__':
    unittest.main()
