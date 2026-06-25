# Cache

`fluxium/cache.py`

## CacheBackend

```python
class CacheBackend:
    def get(self, key: str) -> dict | None
    def set(self, key: str, value: dict, ttl: int) -> None
    def delete(self, key: str) -> None
    def clear(self) -> None
```

Abstract base for all cache backends.

## MemoryCache

```python
class MemoryCache(CacheBackend):
    def __init__(self, max_size: int = 1000)
```

In-memory LRU cache with TTL. Thread-safe.

## DiskCache

```python
class DiskCache(CacheBackend):
    def __init__(self, cache_dir: str | Path = ".fluxium_cache")
```

Disk-based cache using JSON files. Persists across restarts.

## HishelCache

```python
class HishelCache(CacheBackend):
    def __init__(self, base_url: str = "", storage: Any = None, **kwargs)
```

RFC 7234 compliant cache. Requires `pip install hishel`.

### Methods

| Method | Returns | Description |
|---|---|---|
| `is_cachable(method, url, headers, response_status)` | `bool` | Check if response is cacheable |
