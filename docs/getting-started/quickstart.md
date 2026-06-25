# Quickstart

## Your First Request

```python
import fluxium

r = fluxium.get("https://api.example.com")
print(r.status_code)  # 200
print(r.json())       # {'hello': 'world'}
```

## POST JSON

```python
r = fluxium.post("https://api.example.com/items", json={"name": "widget"})
print(r.json()["id"])  # 123
```

## With a Session (Connection Pooling)

```python
with fluxium.Session() as s:
    r1 = s.get("https://api.example.com/users")
    r2 = s.post("https://api.example.com/items", json={"name": "x"})
    # Cookies from r1 are automatically sent with r2
```

## Async

```python
import asyncio
import fluxium

async def main():
    async with fluxium.AsyncSession() as s:
        tasks = [s.get(f"https://api.example.com/item/{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)
        print(len(results))  # 10

asyncio.run(main())
```

## With Caching

```python
from fluxium import Session, MemoryCache

with Session(cache=MemoryCache()) as s:
    s.get("https://api.example.com")  # hits network
    s.get("https://api.example.com")  # hits cache (instant!)
```

## Timeouts

```python
# Simple
fluxium.get("https://api.example.com", timeout=10.0)

# Structured
from fluxium import Timeout
fluxium.get("https://api.example.com", timeout=Timeout(connect=5, read=30))
```

## Rate Limiting

```python
from fluxium import Session, RateLimitMiddleware

s = Session()
s.add_middleware(RateLimitMiddleware(calls=100, period=60))
```

## Hooks

```python
s = Session()
s.add_hook("response", lambda r, req: print(f"Got {r.status_code}"))
```

## Next Steps

- [Sessions](../guides/sessions.md) — connection pooling, cookies, headers
- [Authentication](../guides/authentication.md) — Basic, Digest, Bearer, OAuth2
- [API Reference](../api-reference/index.md) — complete signatures
