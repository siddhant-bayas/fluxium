# Rate Limiting

`fluxium/middleware.py`

## RateLimitMiddleware

```python
class RateLimitMiddleware(Middleware):
    def __init__(self, calls: int = 100, period: float = 60.0)
```

Token bucket rate limiter.

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|
| `calls` | `int` | `100` | Max requests per period |
| `period` | `float` | `60.0` | Period in seconds |

## Examples

```python
from fluxium import Session, RateLimitMiddleware

s = Session()
s.add_middleware(RateLimitMiddleware(calls=100, period=60))  # 100 req/min
```

## With AsyncSession

```python
async with AsyncSession() as s:
    s.add_middleware(RateLimitMiddleware(calls=10, period=1))  # 10 req/s
    results = await asyncio.gather(*[s.get(url) for _ in range(100)])
```

## Token Bucket

The middleware uses a token bucket algorithm:
- Starts with `calls` tokens
- Refills at `calls/period` tokens per second
- Sleeps when tokens are exhausted
