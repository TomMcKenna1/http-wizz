# API Reference

## `fetch_urls(...)`

A synchronous convenience wrapper around `WizzClient.fetch_all`. This is the easiest way to get started for scripts that do not require a custom `asyncio` loop.

```python
from http_wizz import fetch_urls

results = fetch_urls(urls, requests_per_second=10, ...)
```

### Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`urls`** | `List[str]` | **Required** | A list of URL strings to fetch. |
| **`requests_per_second`** | `float` | `10` | The global maximum rate limit in requests per second (RPS). |
| **`burst_size`** | `int` | `1` | The maximum number of requests allowed to burst through immediately before throttling kicks in. Useful for responsiveness. |
| **`domain_limits`** | `Dict[str, float]` | `None` | A dictionary mapping domain names (e.g., `"google.com"`) to their specific RPS limits. Overrides the global limit for those domains. |
| **`max_retries`** | `int` | `5` | The maximum number of retry attempts for failed requests (network errors, 429s, 503s). |
| **`initial_retry_delay`** | `float` | `1.0` | The initial delay (in seconds) before the first retry. |
| **`exponential_backoff`** | `bool` | `True` | If `True`, the delay doubles after each subsequent failure (e.g., 1s, 2s, 4s...). |
| **`should_retry`** | `Callable` | `None` | A custom function `f(response, content) -> bool`. If it returns `True`, the request is retried even if the status was 200 OK. |
| **`show_progress`** | `bool` | `False` | If `True`, displays a progress bar using `tqdm`. |

### Returns
- `List[Optional[Any]]`: A list of results corresponding to the input URLs. The order is preserved. Failed requests (after all retries) return `None`.

---

## `WizzClient`

The primary asynchronous client. Handles session lifecycle, token buckets, and parallel fetching.

```python
from http_wizz import WizzClient

async with WizzClient(requests_per_second=50) as client:
    results = await client.fetch_all(urls)
```

### Constructor `__init__(...)`

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`requests_per_second`** | `float` | `10` | Global rate limit (RPS). |
| **`burst_size`** | `int` | `1` | Max concurrent burst size. |
| **`domain_limits`** | `Dict[str, float]` | `None` | Domain-specific RPS limits. |
| **`max_retries`** | `int` | `5` | Max retry attempts per URL. |
| **`initial_retry_delay`** | `float` | `1.0` | Initial wait time for retries. |
| **`exponential_backoff`** | `bool` | `True` | Enable doubling of wait time. |
| **`should_retry`** | `Callable` | `None` | Custom retry predicate `f(response, content) -> bool`. |

### Methods

#### `fetch_all(urls: List[str], show_progress: bool = False) -> List[Optional[Any]]`
Fetches all provided URLs concurrently, respecting the configured rate limits.
- **`urls`**: List of URLs to fetch.
- **`show_progress`**: Enable `tqdm` progress bar.

---

## `RateLimitedSession`

A low-level wrapper around `aiohttp.ClientSession`. Use this if you need full control over HTTP verbs (`POST`, `PUT`, `DELETE`), headers, cookies, or persistent connections.

```python
from http_wizz import RateLimitedSession

async with RateLimitedSession(requests_per_second=5) as session:
    async with session.post("https://api.com", json={...}) as resp:
        ...
```

### Constructor `__init__(...)`

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`requests_per_second`** | `float` | `10` | Global rate limit (RPS). |
| **`burst_size`** | `int` | `1` | Max concurrent burst size. |
| **`domain_limits`** | `Dict[str, float]` | `None` | Domain-specific RPS limits. |
| **`session`** | `aiohttp.ClientSession` | `None` | Optional existing session to wrap. If provided, `RateLimitedSession` will use it but won't close it automatically. |
| **`**kwargs`** | `Any` | - | Any other arguments are passed directly to `aiohttp.ClientSession` (e.g., `headers`, `cookies`, `connector`). |

### Methods

#### `request(method: str, url: str, **kwargs)`
Performs a rate-limited request.
- **`method`**: HTTP method (`"GET"`, `"POST"`, etc.).
- **`url`**: Target URL.
- **`**kwargs`**: Standard `aiohttp` request arguments (`params`, `data`, `json`, `headers`, etc.).

#### Convenience Methods
- `get(url, **kwargs)`
- `post(url, **kwargs)`
- `put(url, **kwargs)`
- `delete(url, **kwargs)`
- `patch(url, **kwargs)`
- `head(url, **kwargs)`
- `options(url, **kwargs)`

These are shortcuts for `request(method, ...)` and behave exactly like their `aiohttp` counterparts, but with automatic rate limiting.
