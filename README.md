# HTTP Wizz 🧙‍♂️

![PyPI - Version](https://img.shields.io/pypi/v/http-wizz)
![PyPI - License](https://img.shields.io/pypi/l/http-wizz)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/http-wizz)
![Tests](https://github.com/tommckenna1/http-wizz/actions/workflows/tests.yml/badge.svg)

**The missing rate-limit wrapper for `aiohttp` and `asyncio`.**

**HTTP Wizz** handles the hard parts of web scraping and high-volume API consumption: **Strict Rate Limiting (RPS)**, **Automatic Retries**, **429/503 Backoff**, and **Domain Throttling**. Perfect for web crawlers, data processing pipelines, and microservices.

---

## ✨ Key Features

*   **Strict Global Rate Limiting:** Enforce a precise Request Per Second (RPS) limit across all your concurrent tasks.
*   **Per-Domain Throttling:** Set different rate limits for different domains (e.g., 50 RPS for Google, 1 RPS for a small site) within the same client.
*   **Smart Retries & Backoff:** Automatically retries failed requests with exponential backoff.
*   **Respects `Retry-After`:** Automatically sleeps when a server sends a `429 Too Many Requests` or `503 Service Unavailable` with a `Retry-After` header.
*   **Custom Retry Logic:** Define your own conditions for retrying (e.g., specific JSON content or headers).
*   **Drop-in `aiohttp` Replacement:** The `RateLimitedSession` is compatible with standard `aiohttp` usage, including proxies, cookies, and all HTTP verbs.

---

## ⚡ Why HTTP Wizz?

Whether you are building a **web scraper** or a **data pipeline** (e.g., geocoding 100k addresses), hitting rate limits is the #1 cause of failure. `asyncio.gather` is too aggressive, and `requests` is too slow.

| Feature | `requests` | `aiohttp` (raw) | `http-wizz` 🧙‍♂️ |
| :--- | :---: | :---: | :---: |
| **Async / Non-blocking** | ❌ | ✅ | ✅ |
| **Strict Rate Limiting (RPS)** | ❌ | ❌ | ✅ |
| **Handle `Retry-After` Header** | ❌ | ❌ | ✅ |
| **Domain-Specific Limits** | ❌ | ❌ | ✅ |
| **Auto-Retries with Backoff** | ❌ | ❌ | ✅ |
| **Data Pipeline Friendly** | ❌ | ⚠️ | ✅ |

---

## 🚀 Installation

```bash
pip install http-wizz
```
*(Optional) For progress bars in `fetch_all` and `fetch_urls`:* `pip install tqdm`

---

## 🏃 Quick Start

**Batch Processing (The Simple Way)**
Perfect for data processing pipelines where you just want to "fire and forget" a list of tasks at a safe speed.

```python
from http_wizz import fetch_urls

urls = [f"https://api.geocoder.com/search?q={addr}" for addr in my_addresses]

# Process items at exactly 20 requests per second
results = fetch_urls(urls, requests_per_second=20, show_progress=True)
```

---

## 🛠 Advanced Usage

### 1. High-Performance Async Client
Best for modern async applications and microservices.

```python
import asyncio
from http_wizz import WizzClient

async def main():
    # 50 RPS limit for high-throughput pipelines
    async with WizzClient(requests_per_second=50, burst_size=10) as client:
        results = await client.fetch_all(["https://api.com/task/1", ...])
```

### 2. Fine-grained Control (`RateLimitedSession`)
A drop-in replacement for `aiohttp.ClientSession`. Use this for full control (headers, cookies, POST/PUT methods, proxies, etc.).

```python
from http_wizz import RateLimitedSession

async with RateLimitedSession(requests_per_second=5) as session:
    # Use proxies, headers, or any other aiohttp feature
    async with session.post(
        "https://api.com/update", 
        json={"id": 123}, 
        proxy="http://user:pass@proxy.com:8080"
    ) as resp:
        status = await resp.json()
```

### 3. Domain Throttling
Manage multiple services with different quotas simultaneously.

```python
client = WizzClient(
    requests_per_second=10, # Global Limit
    domain_limits={
        "maps.google.com": 50,  # High quota
        "legacy-service.local": 1 # Very fragile service
    }
)
```

### 4. Custom Retry Logic
Retry not just on network errors, but also on specific application-level responses (e.g., a 200 OK that actually contains an error message).

```python
def is_error_response(response, content):
    # Retry if the JSON body contains "error": true
    if isinstance(content, dict) and content.get("error"):
        return True
    return False

client = WizzClient(should_retry=is_error_response)
```

---

## 📖 Recipes & Examples

Check out the `examples/` directory for ready-to-run scripts:

- **[Data Pipeline](examples/data_pipeline_geocoding.py):** Process batches of data at a fixed speed.
- **[Hacker News Scraper](examples/hacker_news_scraper.py):** Fetch top stories politely.
- **[Strict API Consumer](examples/strict_api_consumer.py):** Handle APIs with tight limits (e.g., 2 RPS).
- **[Proxy Integration](examples/proxy_integration.py):** Use rotating proxies with rate limiting.
- **[Benchmark](examples/benchmark_comparison.py):** Compare Wizz vs Sequential vs Naive Async.

---

## 📚 API Reference

For a complete list of all parameters, flags, and advanced options, please see the [**Full API Reference**](docs/API_REFERENCE.md).

---

## 🤝 Contributing

We love pull requests! If you have a feature idea or found a bug, please open an issue.

**License:** MIT
