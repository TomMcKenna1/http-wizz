import asyncio
import time
import aiohttp
from http_wizz import WizzClient

# Goal: Compare http-wizz vs Naive asyncio.gather vs Sequential
# Note: Use a local server or highly tolerant API for the 'Naive' test to avoid bans.
# We will use httpbin.org but with a small number of requests to be safe.

URLS = [f"https://httpbin.org/get?i={i}" for i in range(20)]

async def run_naive():
    start = time.monotonic()
    async with aiohttp.ClientSession() as session:
        tasks = [session.get(u) for u in URLS]
        responses = await asyncio.gather(*tasks)
        for r in responses:
            await r.read()
    return time.monotonic() - start

async def run_sequential():
    start = time.monotonic()
    async with aiohttp.ClientSession() as session:
        for u in URLS:
            async with session.get(u) as resp:
                await resp.read()
    return time.monotonic() - start

async def run_http_wizz():
    start = time.monotonic()
    # Limit to 5 RPS to show control
    async with WizzClient(requests_per_second=5) as client:
        await client.fetch_all(URLS)
    return time.monotonic() - start

async def main():
    print(f"Benchmarking {len(URLS)} requests...")
    
    print("1. Running Naive (All at once)...")
    naive_time = await run_naive()
    print(f"   -> {naive_time:.2f}s (Risk: High - likely to get 429s on real sites)")

    print("2. Running Sequential (One by one)...")
    seq_time = await run_sequential()
    print(f"   -> {seq_time:.2f}s (Risk: Low - but very slow)")

    print("3. Running HTTP Wizz (Controlled 5 RPS)...")
    wizz_time = await run_http_wizz()
    print(f"   -> {wizz_time:.2f}s (Risk: Low - controlled speed)")

    print("\nSummary:")
    print(f"HTTP Wizz was {seq_time / wizz_time:.1f}x faster than sequential loop.")
    print("HTTP Wizz provides the safety of sequential with the speed of async.")

if __name__ == "__main__":
    asyncio.run(main())
