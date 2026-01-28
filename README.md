# HTTP Wizz 🧙‍♂️

**HTTP Wizz** is a Python library designed for high-performance, asynchronous, rate-limited URL fetching. Whether you're scraping data, calling third-party APIs with strict limits, or building robust microservices, HTTP Wizz provides the tools to handle "requests per second" (RPS) constraints with ease.

## Key Features

- ⏱️ **Strict Rate Limiting:** Precisely control your throughput with "requests per second" (RPS).
- 🌍 **Domain-Specific Limits:** Set different rate limits for different domains (e.g., fast for your API, slow for scraping).
- 💥 **Burst Handling:** Allow short bursts of traffic while maintaining long-term rate limits.
- 🔄 **Automatic Retries:** Built-in resilience for flaky networks and unstable APIs.
- ⏳ **Smart Backoff:** Respects standard `Retry-After` headers and supports exponential backoff.
- 🎯 **Custom Retry Logic:** Force retries based on response content, even if the status code is `200 OK`.
- 📊 **Progress Monitoring:** Built-in integration with `tqdm` for progress bars.
- 🪄 **Versatile API:** Choose between a simple sync function, a high-level async client, or a low-level `aiohttp` wrapper.

---

## Installation

```bash
pip install http-wizz
```

*(Optional) For progress bar support:*
```bash
pip install tqdm
```

---

## Usage Guide

### 1. The Simple Way (Synchronous)
Perfect for quick scripts. Use `fetch_urls` to get results immediately without `asyncio` boilerplate.

```python
from http_wizz import fetch_urls

urls = [f"https://api.example.com/data/{i}" for i in range(10)]

# Fetch at 5 requests per second with a progress bar
results = fetch_urls(urls, requests_per_second=5, show_progress=True)
```

### 2. The Wizard Way (Async Client)
Best for async applications. `WizzClient` handles rate limiting, retries, and JSON parsing automatically.

```python
import asyncio
from http_wizz import WizzClient

async def main():
    urls = ["https://api.example.com/item/1", "https://api.example.com/item/2"]
    
    # Use as a context manager for proper cleanup
    async with WizzClient(requests_per_second=10) as client:
        results = await client.fetch_all(urls)
        print(f"Fetched {len(results)} results")

asyncio.run(main())
```

### 3. The Power User Way (`RateLimitedSession`)
A drop-in replacement for `aiohttp.ClientSession`. Use this when you need full control over headers, cookies, or different HTTP methods (POST, PUT, etc.).

```python
import asyncio
from http_wizz import RateLimitedSession

async def main():
    async with RateLimitedSession(requests_per_second=2) as session:
        for i in range(5):
            # Supports .get, .post, .put, .delete, etc.
            async with session.get(f"https://httpbin.org/get?id={i}") as resp:
                data = await resp.json()
                print(f"Status {resp.status}: {data.get('args')}")

asyncio.run(main())
```

---

## Advanced Configuration

### Domain-Specific Throttling
You can set a global rate limit and specific limits for certain domains.

```python
from http_wizz import WizzClient

client = WizzClient(
    requests_per_second=10,  # Default limit for most domains
    domain_limits={
        "slow-api.com": 1,   # Very strict limit for this domain
        "fast-cdn.com": 50   # High throughput for this domain
    }
)
```

### Burst Handling
Allow small bursts of requests to go through instantly before throttling kicks in. This makes the client feel more responsive for small batches.

```python
client = WizzClient(
    requests_per_second=5,
    burst_size=10  # Allow up to 10 requests immediately
)
```

### Configuring Retries and Backoff
`WizzClient` automatically respects `Retry-After` headers (both seconds and dates). You can further customize the behavior:

```python
client = WizzClient(
    requests_per_second=5,
    max_retries=5,              # Number of retry attempts
    initial_retry_delay=1.0,    # Seconds to wait after first failure
    exponential_backoff=True    # Double the delay after each failure (1s, 2s, 4s...)
)
```

### Custom Retry Conditions
Sometimes APIs return `200 OK` but include an error message in the body. You can force a retry by providing a `should_retry` callback.

```python
def check_for_api_errors(response, content):
    # Retry if the API returned a 'try_again' flag in the JSON body
    return isinstance(content, dict) and content.get("status") == "try_again"

results = fetch_urls(
    ["https://api.example.com/job"],
    should_retry=check_for_api_errors,
    max_retries=10
)
```

---

## API Reference

### `fetch_urls(...)`
- `urls`: List of strings.
- `requests_per_second`: (float) Max requests/sec. Default `10`.
- `burst_size`: (int) Max concurrent burst. Default `1`.
- `domain_limits`: (dict) Map of domain string to RPS float.
- `max_retries`: (int) Default `5`.
- `initial_retry_delay`: (float) Default `1.0`.
- `exponential_backoff`: (bool) Default `True`.
- `should_retry`: `callable(response, content) -> bool`.
- `show_progress`: (bool) Show a tqdm progress bar. Default `False`.

### `WizzClient(...)`
- High-level async client. Same arguments as `fetch_urls` (excluding `urls` and `show_progress` in init).
- `fetch_all(urls, show_progress=False)`: Asynchronously fetches all provided URLs.

### `RateLimitedSession(...)`
- `requests_per_second`: (float) Max requests/sec.
- `burst_size`: (int) Max concurrent burst.
- `domain_limits`: (dict) Map of domain string to RPS float.
- All other arguments are passed to the underlying `aiohttp.ClientSession`.

---