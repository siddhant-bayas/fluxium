# Middleware

Middleware hooks into the request/response lifecycle.

## Lifecycle

```
on_request  →  send request  →  on_response  →  return to caller
                ↓ (error)
             on_error
```

## LoggingMiddleware

```python
from fluxium import Session, LoggingMiddleware

s = Session()
s.add_middleware(LoggingMiddleware())
s.get("https://api.example.com")
# DEBUG:fluxium:→ GET https://api.example.com
# DEBUG:fluxium:← 200 https://api.example.com (45.2ms)
```

## RetryMiddleware

```python
from fluxium import Session, RetryMiddleware

s = Session()
s.add_middleware(RetryMiddleware(max_retries=3, backoff_factor=0.5))
r = s.get("https://api.example.com")  # auto-retries on 5xx/timeout
```

Or use the shorthand:

```python
s = Session(max_retries=3, retry_backoff=0.5)
```

Retries on: 408, 429, 500, 502, 503, 504, TimeoutError, ConnectionError.

## Custom Middleware

```python
from fluxium import Middleware

class RequestIDMiddleware(Middleware):
    def on_request(self, request):
        request.headers["x-request-id"] = str(uuid.uuid4())
        return request

s = Session()
s.add_middleware(RequestIDMiddleware())
```

### Timing Middleware

```python
class TimingMiddleware(Middleware):
    def on_request(self, request):
        request._start = time.perf_counter()
        return request

    def on_response(self, response):
        elapsed = (time.perf_counter() - response.request._start) * 1000
        print(f"{response.url} took {elapsed:.1f}ms")
        return response
```

### Error Handler

```python
class ErrorHandler(Middleware):
    def on_error(self, error, request):
        log_error(f"{request.method} {request.url} failed: {error}")
```

## Multiple Middleware

```python
s = Session()
s.add_middleware(RequestIDMiddleware())
s.add_middleware(LoggingMiddleware())
s.add_middleware(RetryMiddleware(max_retries=3))
```

Order matters: the first middleware added wraps the others (outermost).
