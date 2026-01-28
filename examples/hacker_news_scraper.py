import asyncio
from http_wizz import WizzClient

# Goal: Fetch top 30 Hacker News stories without getting rate-limited.
# Hacker News API is fast, but let's be polite citizens (5 RPS).

async def fetch_hn_stories():
    base_url = "https://hacker-news.firebaseio.com/v0"
    
    # 1. Get Top Story IDs
    async with WizzClient(requests_per_second=10) as client:
        print("Fetching Top Stories IDs...")
        top_ids = await client.fetch_all([f"{base_url}/topstories.json"])
        top_ids = top_ids[0][:30] # Just the top 30
    
    story_urls = [f"{base_url}/item/{id}.json" for id in top_ids]
    
    # 2. Fetch Story Details with politeness
    print(f"Fetching {len(story_urls)} stories at 5 RPS...")
    async with WizzClient(requests_per_second=5) as client:
        stories = await client.fetch_all(story_urls)
        
    for story in stories:
        if story and 'title' in story:
            print(f"- {story['title']}")

if __name__ == "__main__":
    asyncio.run(fetch_hn_stories())
