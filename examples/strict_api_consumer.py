import asyncio
from http_wizz import WizzClient

# Goal: Interact with an API that has a strict limit (e.g., 2 requests per second)
# and sends "Retry-After" headers if you go too fast.

async def strict_api_consumer():
    # Imagine this is a strict API
    urls = [f"https://httpbin.org/get?id={i}" for i in range(10)]
    
    print("Starting strict fetching (2 RPS)...")
    
    # We set burst_size=1 to ensure we don't spike traffic even at start
    async with WizzClient(
        requests_per_second=2,
        burst_size=1, 
        max_retries=5,
        exponential_backoff=True
    ) as client:
        results = await client.fetch_all(urls, show_progress=True)
        
    print(f"Successfully fetched {len(results)} items.")

if __name__ == "__main__":
    asyncio.run(strict_api_consumer())
