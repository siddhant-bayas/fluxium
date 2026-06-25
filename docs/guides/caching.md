# Caching

Fluxium offers three cache backends. Only GET and HEAD requests with 2xx status are cached.

## MemoryCache

In-memory LRU cache with TTL. Best for single-process apps.

```python
from fluxium import Session, MemoryCache

cache = MemoryCache(max_size=1000)
with Session(cache=cache) as s:
    s.get("https://api.example.com")           # hits network, caches
    s.get("https://api.example.com")           # hits cache (instant!)
    s.get("https://api.example.com")           # hits cache (instant!)
```

## DiskCache

Disk-based cache using JSON files. Persists across restarts.

```python
from fluxium import Session, DiskCache

cache = DiskCache(".fluxium_cache")
with Session(cache=cache) as s:
    s.get("https://api.example.com")  # cached to .fluxium_cache/

# Restart app — cache is still there
with Session(cache=cache) as s:
    s.get("https://api.example.com")  # hits disk cache
```

## HishelCache

RFC 7234 compliant cache. Respects `Cache-Control`, `ETag`, `Vary`.

```bash
pip install fluxium[cache]
```

```python
from fluxium import Session, HishelCache

with Session(cache=HishelCache()) as s:
    s.get("https://api.example.com")  # respects Cache-Control headers
```

## Per-Request TTL

```python
with Session(cache=MemoryCache()) as s:
    s.get("https://api.example.com/config", cache_ttl=300)    # 5 min
    s.get("https://api.example.com/static", cache_ttl=3600)   # 1 hour
    s.get("https://api.example.com/live", cache_ttl=0)        # don't cache
```

## Cache Key

Cache keys are derived from method + URL + relevant headers (excluding auth/cookie).

```python
# These have the same cache key:
s.get("https://api.example.com", headers={"Accept": "application/json"})
s.get("https://api.example.com", headers={"Accept": "text/html"})
```

## Performance

```
Cache benchmark (100 repeated GETs, same URL):
  Uncached:  ~40 ms
  Cached:    ~10 ms
  Speedup:   ~4x
```
