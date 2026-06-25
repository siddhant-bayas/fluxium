# Fluxium Documentation

Welcome to the **fluxium** 2.0.0 documentation.

## Quick Links

- [Getting Started](getting-started/index.md) — install, first request, compatibility
- [Guides](guides/index.md) — step-by-step tutorials for every feature
- [API Reference](api-reference/index.md) — complete class and method signatures
- [Advanced](advanced/index.md) — custom middleware, performance, SSE deep-dive
- [Changelog](changelog/index.md) — version history and migration guide

## What is Fluxium?

Fluxium is a fast, modern HTTP client for Python with HTTP/2, connection pooling, caching, middleware, and async support.

```python
import fluxium

r = fluxium.get("https://api.example.com")
print(r.json())
```

## Installation

```bash
pip install fluxium
```

## Key Features

| Feature | Description |
|---|---|
| HTTP/2 | Multiplexing enabled by default |
| Connection Pooling | 200 connections, 100 keep-alive |
| Caching | Memory, Disk, or RFC 7234 (Hishel) |
| Middleware | Hooks for logging, retries, custom logic |
| Async | Full asyncio support with uvloop |
| Retries | Exponential backoff for transient errors |

## License

MIT
