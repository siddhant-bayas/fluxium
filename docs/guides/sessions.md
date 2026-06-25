# Sessions

Sessions provide connection pooling, cookie persistence, and header persistence across requests.

## Sync Session

```python
from fluxium import Session

with Session() as s:
    r1 = s.get("https://api.example.com/users")
    r2 = s.post("https://api.example.com/items", json={"name": "x"})
    r3 = s.get("https://api.example.com/items")
    # All three share the same connection pool and cookies
```

## Async Session

```python
from fluxium import AsyncSession

async with AsyncSession() as s:
    r1 = await s.get("https://api.example.com/users")
    r2 = await s.post("https://api.example.com/items", json={"name": "x"})
```

## Session Configuration

```python
s = Session(
    headers={"Authorization": "Bearer xxx"},  # sent with every request
    cookies={"session": "abc"},                 # sent with every request
    timeout=30.0,                               # default timeout
    http2=True,                                 # enable HTTP/2
    max_retries=3,                              # retry on failure
    retry_backoff=0.5,                          # exponential backoff factor
    cache=MemoryCache(),                       # cache backend
)
```

## Cookie Persistence

```python
with Session() as s:
    s.get("https://api.example.com/login")  # server sets cookies
    s.get("https://api.example.com/profile")  # cookies sent automatically
```

## Header Merging

```python
s = Session(headers={"X-Session": "abc"})
s.get("https://api.example.com", headers={"X-Request": "123"})
# Sent headers: X-Session: abc, X-Request: 123
```

## Pre-warming

Eliminate first-request TLS handshake latency:

```python
with Session() as s:
    s.prewarm("https://api.example.com")  # Opens connection now
    r = s.get("https://api.example.com")  # Uses pooled connection
```

## Context Manager

```python
# Sync — auto-closes on exit
with Session() as s:
    s.get("https://api.example.com")

# Async — auto-closes on exit
async with AsyncSession() as s:
    await s.get("https://api.example.com")
```

Without the context manager, call `s.close()` or `await s.close()` manually.
