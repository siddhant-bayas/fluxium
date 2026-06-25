# Performance

## Benchmarks

Local HTTP server, 200 iterations, connection pooling:

| Library | Per-op (ms) | vs best |
|---|---|---|
| httpx (session) | 0.276 | 1.00x |
| fluxium (session) | 0.444 | 1.61x |
| requests (session) | 0.619 | 2.24x |

One-shot GET (no session, 200 iters):

| Library | Per-op (ms) | vs best |
|---|---|---|
| requests (oneshot) | 1.276 | 1.00x |
| fluxium (oneshot) | 8.127 | 6.37x |
| httpx (oneshot) | 7.922 | 6.21x |

Cache benchmark (100 repeated GETs, same URL):

| Config | Total (ms) | Per-op (ms) |
|---|---|---|
| fluxium (no cache) | ~40 | 0.396 |
| fluxium (MemoryCache) | ~10 | 0.092 |

**Cache speedup: ~4x**

## Optimization Tips

### 1. Use Sessions

One-shot functions create a new session (and httpx client) per call. For repeated requests, use a `Session`:

```python
# Slow
for _ in range(100):
    fluxium.get("https://api.example.com")

# Fast
with Session() as s:
    for _ in range(100):
        s.get("https://api.example.com")
```

### 2. Install uvloop

```bash
pip install "fluxium[uvloop]"
```

20-40% async throughput improvement. Auto-detected on import.

### 3. Use Caching

```python
from fluxium import Session, MemoryCache

with Session(cache=MemoryCache()) as s:
    s.get("https://api.example.com")  # network
    s.get("https://api.example.com")  # cache (instant)
```

### 4. Pre-warm Connections

```python
with Session() as s:
    s.prewarm("https://api.example.com")  # TLS handshake now
    s.get("https://api.example.com")      # no handshake latency
```

### 5. Tune Pool Size

For high-concurrency workloads:
```python
s = Session()
s._client._limits = httpx.Limits(max_connections=500, max_keepalive_connections=200)
```

### 6. Use HTTP/2

Enabled by default. Ensure the server supports HTTP/2 for multiplexing.

## Profiling

```bash
python -m cProfile -s cumtime benchmark/benchmark.py --local-only
```

Or with py-spy:
```bash
py-spy record -o profile.svg -- python benchmark/benchmark.py
```
