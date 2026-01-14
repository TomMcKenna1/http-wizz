import unittest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch, call
from http_wizz import WizzClient

class TestRateLimitedFetcher(unittest.TestCase):
    def setUp(self):
        # Helper to create a proper mock response
        self.mock_response = MagicMock()
        self.mock_response.status = 200
        self.mock_response.json = AsyncMock(return_value={"id": 1})
        self.mock_response.text = AsyncMock(return_value="ok")
        self.mock_response.content_type = 'application/json'
        # Context manager protocol
        self.mock_response.__aenter__ = AsyncMock(return_value=self.mock_response)
        self.mock_response.__aexit__ = AsyncMock(return_value=None)

    def test_rate_limiting(self):
        """
        Verify that requests are spaced out correctly.
        """
        rps = 10
        client = WizzClient(requests_per_second=rps)
        
        mock_session_inst = MagicMock()
        mock_session_inst.get.return_value = self.mock_response
        mock_session_inst.request.return_value = self.mock_response
        mock_session_inst.__aenter__ = AsyncMock(return_value=mock_session_inst)
        mock_session_inst.__aexit__ = AsyncMock(return_value=None)
        
        # We need to patch RateLimitedSession to return our mock session or patch aiohttp.ClientSession
        # Since WizzClient creates RateLimitedSession, and RateLimitedSession creates aiohttp.ClientSession
        # It's easiest to patch aiohttp.ClientSession
        
        with patch('aiohttp.ClientSession', return_value=mock_session_inst):
            start = time.monotonic()
            urls = ["http://example.com" for _ in range(5)]
            asyncio.run(client.fetch_all(urls))
            end = time.monotonic()
            duration = end - start
            
            # 5 requests at 10 RPS -> 0, 0.1, 0.2, 0.3, 0.4. Total ~0.4s
            self.assertGreaterEqual(duration, 0.35, "Requests were too fast!")

    def test_backoff_disabled(self):
        client = WizzClient(
            requests_per_second=1000,
            max_retries=2, 
            initial_retry_delay=0.1, 
            exponential_backoff=False
        )
        
        # Fail response
        fail_response = MagicMock()
        fail_response.status = 500
        fail_response.__aenter__ = AsyncMock(return_value=fail_response)
        fail_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session_inst = MagicMock()
        mock_session_inst.get.return_value = fail_response
        mock_session_inst.__aenter__ = AsyncMock(return_value=mock_session_inst)
        mock_session_inst.__aexit__ = AsyncMock(return_value=None)

        with patch('aiohttp.ClientSession', return_value=mock_session_inst):
            # We patch asyncio.sleep to verify delays
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                # We also need to patch RateLimiter.wait to avoid rate limit sleeps interfering (though RPS=1000 is fast)
                with patch('http_wiz.client.RateLimiter.wait', new_callable=AsyncMock):
                    asyncio.run(client.fetch_all(["http://fail.com"]))
                    
                    # Sleeps for retries: 0.1, 0.1
                    # Filter for 0.1 calls only
                    relevant_calls = [c.args[0] for c in mock_sleep.call_args_list if c.args and c.args[0] == 0.1]
                    self.assertEqual(len(relevant_calls), 2)

    def test_backoff_enabled(self):
        client = WizzClient(
            requests_per_second=1000, 
            max_retries=2, 
            initial_retry_delay=0.1, 
            exponential_backoff=True
        )
        
        fail_response = MagicMock()
        fail_response.status = 500
        fail_response.__aenter__ = AsyncMock(return_value=fail_response)
        fail_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session_inst = MagicMock()
        mock_session_inst.get.return_value = fail_response
        mock_session_inst.__aenter__ = AsyncMock(return_value=mock_session_inst)
        mock_session_inst.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session_inst):
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                with patch('http_wiz.client.RateLimiter.wait', new_callable=AsyncMock):
                    asyncio.run(client.fetch_all(["http://fail.com"]))
                    
                    # Sleeps: 0.1, 0.2
                    calls_args = [c.args[0] for c in mock_sleep.call_args_list if c.args and c.args[0] in [0.1, 0.2]]
                    self.assertEqual(calls_args, [0.1, 0.2])

if __name__ == '__main__':
    unittest.main()
