import asyncio
from http_wizz import WizzClient

# Goal: Process a large batch of addresses for geocoding.
# Services like Google Maps or OpenStreetMap have strict RPS limits.
# We want to process 100 addresses at exactly 50 requests per second.

async def geocode_pipeline():
    # Mock list of addresses
    addresses = [f"{i} Main St, Springfield, USA" for i in range(100)]
    
    # Base URL for a geocoding service (e.g., Nominatim or Google)
    base_url = "https://httpbin.org/get" # Using httpbin for demonstration
    
    urls = [f"{base_url}?address={addr}" for addr in addresses]
    
    print(f"🚀 Starting data pipeline: Processing {len(urls)} addresses...")
    
    # 50 RPS limit ensures we stay within the 'Bronze Tier' of our mock API
    async with WizzClient(
        requests_per_second=50, 
        burst_size=10,
    ) as client:
        results = await client.fetch_all(urls)
    
    # Process results (e.g., extracting 'lat' and 'lon')
    successful = [r for r in results if r is not None]
    print(f"✅ Pipeline Complete. Processed {len(successful)} addresses successfully.")

if __name__ == "__main__":
    # In a real pipeline, you might pipe this data into a database or CSV
    asyncio.run(geocode_pipeline())
