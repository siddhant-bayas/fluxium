# Timeouts and Retries

## Timeout Formats

```python
# All components same timeout
with fluxium.Session(timeout=30.0) as s:
    s.get("https://api.example.com")

# (connect, read) tuple
with fluxium.Session(timeout=(5.0, 30.0)) as s:
    s.get("https://api.example.com")

# Per-request override
s.get("https://api.example.com", timeout=10.0)
```

## Retry Configuration

```python
from fluxium import Session, RetryMiddleware

# Shorthand
s = Session(max_retries=3, retry_backoff=0.5)

# Full control
mw = RetryMiddleware(
    max_retries=5,          # max retry attempts
    backoff_factor=0.5,     # backoff = factor * 2^attempt
    max_backoff=30.0,       # cap backoff at 30s
    retry_on_status={500, 502, 503},  # custom retryable statuses
)
s = Session()
s.add_middleware(mw)
```

## Backoff Formula

```
backoff = min(backoff_factor * 2^attempt + random(0, 0.1), max_backoff)
```

| Attempt | Factor=0.5 |
|---|---|
| 0 | ~0.5s |
| 1 | ~1.0s |
| 2 | ~2.0s |
| 3 | ~4.0s |

## Retryable Conditions

- Status codes: 408, 429, 500, 502, 503, 504
- Exceptions: TimeoutError, ConnectionError

## Per-Request Retry Override

```python
# Disable retry for specific request
s = Session(max_retries=3)
s.get("https://api.example.com", max_retries=0)  # no retry
```
