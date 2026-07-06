# Changelog

## [3.0.0] — 2026-07-06

### Added

- **uvloop platform marker** — `sys_platform != 'win32'` pip marker prevents installation failure on Windows.

### Changed

- **Performance overhaul** — fluxium now matches or exceeds httpx throughput (0.91× vs 1.70× baseline):
  - Lazy header merge via `dict.update()` generator; reuse `self.headers` directly when no custom headers/cookies.
  - Skip body preparation for GET/HEAD requests.
  - CookieJar `_header_cache` + `_dirty` flag eliminates repeated serialization.
  - Empty middleware/hooks early-return guards to bypass function call overhead.
  - Import hoisting — inline imports in retry loops moved to module top.
  - Single-pass request construction — auth headers applied to merged headers before `build_request`.
  - Direct transport path — `client._transport.handle_request()` bypasses httpx's `_send_handling_auth`/`_send_handling_redirects` wrappers.
  - Cookie guard — skip `raw.cookies` access when no `Set-Cookie` header present, avoiding httpx's `extract_cookies()` on every response.
  - Empty jar fix — `CookieJar()` now evaluates as not-truthy when empty, avoiding forced header dict copy.
  - Skip `list(history)` and cookie iteration loops when empty.
- **Version** — 2.0.0 → 3.0.0

### Fixed

- **CookieJar always truthy** — `CookieJar()` inherited from `http.cookiejar.CookieJar` which has no `__bool__`, causing `if self.cookies:` to force `dict(self.headers)` on every request even with an empty jar. Fixed to check `bool(cookie_header)` instead.
- **Benchmark session reuse** — multipart and async benchmarks now reuse sessions across iterations instead of creating a new `httpx.Client()` per request (~300ms overhead on Windows).

### Migration

No breaking changes. v2 users can upgrade directly. See [v2-to-v3.md](migration/v2-to-v3.md) for details.

---

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
