import asyncio
from http_wizz import RateLimitedSession

# Goal: Use a rotating proxy service to distribute requests.
# Note: You need a real proxy URL for this to work.

PROXY_URL = "http://user:pass@proxy-service.com:8000"

async def fetch_with_proxy():
    # RateLimitedSession wraps aiohttp.ClientSession, so we can pass
    # standard aiohttp arguments like 'proxy' or 'connector'.
    
    # We can also set the proxy per-request.
    
    print("Initializing Proxy Session...")
    async with RateLimitedSession(requests_per_second=5) as session:
        
        # Example 1: Passing proxy to the request directly
        try:
            async with session.get("https://httpbin.org/ip", proxy=PROXY_URL) as resp:
                print("My IP via proxy:", await resp.json())
        except Exception as e:
            print(f"Proxy request failed (expected if no real proxy): {e}")

        # Example 2: Rotating proxies manually (conceptual)
        proxies = [PROXY_URL, PROXY_URL] # Add your list here
        
        for i, proxy in enumerate(proxies):
            try:
                async with session.get("https://httpbin.org/ip", proxy=proxy) as resp:
                    print(f"Request {i} IP:", await resp.json())
            except:
                pass

if __name__ == "__main__":
    asyncio.run(fetch_with_proxy())
