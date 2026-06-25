# Connection Pooling

## Default Pool

```python
httpx.Limits(
    max_connections=200,
    max_keepalive_connections=100,
    keepalive_expiry=30,
)
```

## Tuning

### High-Concurrency

```python
from fluxium import Session

s = Session()
# Access the underlying httpx client
s._client = s._client.with_limits(
    httpx.Limits(max_connections=500, max_keepalive_connections=200)
)
```

### Low-Resource

```python
s = Session()
s._client._limits = httpx.Limits(max_connections=50, max_keepalive_connections=20)
```

### Keep-Alive

`keepalive_expiry=30` means idle connections are closed after 30 seconds. Increase for APIs with long gaps between requests:

```python
s._client._limits = httpx.Limits(
    max_connections=200,
    max_keepalive_connections=100,
    keepalive_expiry=120,  # 2 minutes
)
```

## Pre-warming

Open a connection before the first real request:

```python
with Session() as s:
    s.prewarm("https://api.example.com")
    # TCP+TLS handshake done
    s.get("https://api.example.com")  # uses pooled connection
```

## HTTP/2 Multiplexing

With `http2=True` (default), multiple requests share a single TCP connection. This is especially effective with connection pooling — concurrent requests to the same host all multiplex over one connection.

```python
with Session(http2=True) as s:
    # All requests to same host share one TCP connection
    tasks = [s.get(f"https://api.example.com/item/{i}") for i in range(100)]
    results = await asyncio.gather(*tasks)
```
