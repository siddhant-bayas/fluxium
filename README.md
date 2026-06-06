# Fluxium

**A fast, modern HTTP client for Python.**

Fluxium provides a clean, `requests`-like API with HTTP/2 multiplexing, automatic retries, connection pooling, streaming, SSE, middleware hooks, built-in caching, and full async support — all with zero blocking calls on the asyncio event loop.

```python
import fluxium

r = fluxium.get("https://api.example.com")
print(r.json())
```

## Installation

```bash
pip install fluxium
```

With SOCKS proxy support:

```bash
pip install "fluxium[socks]"
```

## Features

| Feature | Description |
|---|---|
| **HTTP/2 & HTTP/3** | Multiplexed connections, header compression |
| **Connection Pooling** | Up to 200 connections, 100 keep-alive |
| **Automatic Retries** | Exponential backoff for 5xx and timeouts |
| **Streaming & SSE** | `iter_content()`, `iter_lines()`, `iter_sse()` |
| **Built-in Caching** | In-memory or disk-based with TTL |
| **Middleware** | Hooks for logging, auth refresh, rate limiting |
| **OAuth2 / Bearer** | Automatic token management and refresh |
| **Async** | Full `asyncio` support via `AsyncSession` |
| **Zero Blocking** | No blocking calls on the event loop |

## Quick Start

### Basic Requests

```python
import fluxium

# GET
r = fluxium.get("https://api.example.com", timeout=10)
print(r.status_code, r.json())

# POST JSON
r = fluxium.post("https://api.example.com/items", json={"name": "widget"})

# Query params
r = fluxium.get("https://api.example.com/search", params={"q": "python"})

# Custom headers
r = fluxium.get("https://api.example.com", headers={"X-Custom": "value"})
```

### Sessions (Connection Pooling)

```python
with fluxium.Session() as s:
    r1 = s.get("https://api.example.com/users")
    r2 = s.post("https://api.example.com/items", json={"name": "x"})
    # Cookies from r1 are automatically sent with r2
```

### Async

```python
import asyncio, fluxium

async def main():
    async with fluxium.AsyncSession() as s:
        tasks = [s.get(f"https://api.example.com/item/{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)

asyncio.run(main())
```

### Retries & Caching

```python
from fluxium import Session, MemoryCache

with Session(max_retries=3, cache=MemoryCache()) as s:
    r = s.get("https://api.example.com")  # retried on failure, cached on success
```

### Streaming & SSE

```python
with fluxium.Session() as s:
    r = s.get("https://api.example.com/stream", stream=True)
    for line in r.iter_lines():
        print(line)

    # Server-Sent Events
    r = s.get("https://api.example.com/events", stream=True)
    for event in fluxium.iter_sse(r):
        print(event.event, event.json())
```

### OAuth2

```python
from fluxium import OAuth2Auth

auth = OAuth2Auth(
    token_url="https://auth.example.com/token",
    client_id="my-client",
    client_secret="my-secret",
)
r = fluxium.get("https://api.example.com", auth=auth)
```

## Documentation

See the [docs/](docs/) directory for full API reference and guides.

## Benchmarks

On a local HTTP server (200 requests, connection pooling):

| Library | Per-request |
|---|---|
| **fluxium** | **0.59 ms** |
| requests | 0.65 ms |
| httpx | 0.54 ms |

## License

MIT — © 2025 Siddhant Bayas
