# Changelog

## [2.0.0] — 2026-06-24

### Added

- **MemoryCache** — in-memory LRU cache with TTL. ~4x speedup on repeated requests.
- **DiskCache** — disk-based cache using JSON files. Persists across restarts.
- **HishelCache** — RFC 7234 compliant cache backend (via `hishel`). Respects `Cache-Control`, `ETag`, `Vary`.
- **Connection pre-warming** — `session.prewarm(url)` opens a TCP+TLS connection ahead of time.
- **uvloop auto-install** — automatically uses `uvloop` for asyncio event loop when installed (20-40% throughput boost).
- **Connection pooling** — default 200 connections, 100 keep-alive.
- **HTTP/2 by default** — multiplexing enabled out of the box.
- **Middleware system** — `on_request`, `on_response`, `on_error` hooks.
- **Built-in middleware** — `LoggingMiddleware` and `RetryMiddleware`.
- **CookieJar dict interface** — `jar["key"] = "value"`, `"key" in jar`, `jar.to_dict()`.
- **IDNA support** — automatic international domain encoding.
- **Retry with exponential backoff** — configurable retries for transient errors.
- **CI pipeline** — ruff linting, mypy type checking, pytest on Python 3.9–3.13.
- **PyPI trusted publishing** — OIDC-based release workflow.
- **Documentation** — full API reference, guides, migration docs.

### Changed

- **Packaging** — `setup.py` removed. Modern `pyproject.toml` only.
- **Version** — 1.0.0 → 2.0.0

### Fixed

- **Critical: Retry never triggered** — `RetryMiddleware.should_retry()` used `if response:` which evaluates to `False` for 4xx/5xx responses (due to `Response.__bool__` → `self.ok`). Fixed to `if response is not None:`.

### Migration

See [v1-to-v2.md](migration/v1-to-v2.md) for breaking changes and upgrade steps.

---

## [1.0.0] — 2025

Initial release.
