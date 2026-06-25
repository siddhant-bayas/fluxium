# Fluxium

**A fast, modern HTTP client for Python.**

[![PyPI version](https://img.shields.io/pypi/v/fluxium)](https://pypi.org/project/fluxium/)
[![Python](https://img.shields.io/pypi/pyversions/fluxium)](https://pypi.org/project/fluxium/)
[![CI](https://github.com/siddhant-bayas/fluxium/actions/workflows/ci.yml/badge.svg)](https://github.com/siddhant-bayas/fluxium/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage](https://img.shields.io/badge/coverage-90%25+-brightgreen)]()

Fluxium provides a clean, `requests`-like API with HTTP/2 multiplexing, automatic retries, connection pooling, streaming, SSE, middleware hooks, built-in caching, and full async support — with zero blocking calls on the asyncio event loop.

```python
import fluxium

r = fluxium.get("https://api.example.com")
print(r.json())
```

Verify installation:
```bash
python -c "import fluxium; print(fluxium.__version__)"
```

## Installation

```bash
pip install fluxium
```

Optional extras:

```bash
pip install "fluxium[socks]"     # SOCKS proxy support
pip install "fluxium[uvloop]"    # 20-40% faster async
pip install "fluxium[cache]"     # Hishel RFC 7234 cache backend
pip install "fluxium[all]"       # Everything
```

## Features

| Feature | Description |
|---|---|
| **HTTP/2** | Multiplexed connections, header compression (default enabled) |
| **Connection Pooling** | Up to 200 connections, 100 keep-alive, with optional pre-warming |
| **Automatic Retries** | Exponential backoff for 5xx and timeouts |
| **Streaming & SSE** | `iter_content()`, `iter_lines()`, `iter_sse()` |
| **Built-in Caching** | In-memory, disk-based, or RFC 7234 (hishel) with TTL |
| **Middleware** | Hooks for logging, auth refresh, rate limiting |
| **OAuth2 / Bearer** | Automatic token management and refresh |
| **Async** | Full `asyncio` support via `AsyncSession` |
| **uvloop** | Auto-used when installed for 20-40% async throughput |

## Quick Start

### Basic Requests

```python
import fluxium

r = fluxium.get("https://api.example.com", timeout=10)
print(r.status_code, r.json())

r = fluxium.post("https://api.example.com/items", json={"name": "widget"})
```

### Sessions (Connection Pooling)

```python
with fluxium.Session() as s:
    r1 = s.get("https://api.example.com/users")
    r2 = s.post("https://api.example.com/items", json={"name": "x"})
    # Cookies from r1 are automatically sent with r2
```

### Pre-warming Connections

```python
with fluxium.Session() as s:
    s.prewarm("https://api.example.com")  # Opens connection now
    r = s.get("https://api.example.com")  # Uses pooled connection
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

## Streaming & SSE

```python
with fluxium.Session() as s:
    r = s.get("https://api.example.com/stream", stream=True)
    for line in r.iter_lines():
        print(line)

    r = s.get("https://api.example.com/events", stream=True)
    for event in fluxium.iter_sse(r):
        print(event.event, event.json())
```

## Timeouts

```python
from fluxium import Timeout

# All components same timeout
fluxium.get("https://api.example.com", timeout=30.0)

# Structured timeout
fluxium.get("https://api.example.com", timeout=Timeout(connect=5.0, read=30.0))

# Or use tuple shorthand (connect, read)
fluxium.get("https://api.example.com", timeout=(5.0, 30.0))
```

## Rate Limiting

```python
from fluxium import Session, RateLimitMiddleware

s = Session()
s.add_middleware(RateLimitMiddleware(calls=100, period=60))  # 100 req/min
```

## Per-Request Hooks

```python
s = Session()
s.add_hook("response", lambda response, request: log(response))
s.add_hook("error", lambda error, request: notify(error))
```

## Performance

**Cached workloads: fluxium is 4.3x faster than httpx.** On unique requests, performance is comparable.

| Scenario | vs httpx |
|---|---|
| Repeated GET with MemoryCache | **~4.3x faster** |
| Session GET (pooled) | ~1.6x slower (per-request overhead) |
| One-shot GET | ~1.03x (negligible) |
| Async concurrent | ~1.5x slower |
| Body encoding / CookieJar | ~1.0x (identical) |

**Key takeaway:** fluxium wins on repeated requests (caching) and is competitive on unique requests. Install `uvloop` for 20-40% async throughput improvement.

## Documentation

- [Getting Started](docs/getting-started/index.md) — install, first request, compatibility
- [Guides](docs/guides/index.md) — step-by-step tutorials for every feature
- [API Reference](docs/api-reference/index.md) — complete class and method signatures
- [Advanced](docs/advanced/index.md) — custom middleware, performance, SSE deep-dive
- [Changelog](docs/changelog/index.md) — version history and migration guide

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — © 2026 Siddhant Bayas
