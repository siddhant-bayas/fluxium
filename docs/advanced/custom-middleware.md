# Custom Middleware

Build your own middleware by subclassing `Middleware`.

## Template

```python
from fluxium import Middleware

class MyMiddleware(Middleware):
    def on_request(self, request):
        # Modify request before sending
        return request

    def on_response(self, response):
        # Modify or log response after receiving
        return response

    def on_error(self, error, request):
        # Handle errors
        pass
```

## Request ID Injection

```python
import uuid

class RequestIDMiddleware(Middleware):
    def on_request(self, request):
        request.headers["x-request-id"] = str(uuid.uuid4())
        return request
```

## Timing

```python
import time

class TimingMiddleware(Middleware):
    def on_request(self, request):
        request._start_time = time.perf_counter()
        return request

    def on_response(self, response):
        elapsed = (time.perf_counter() - response.request._start_time) * 1000
        response.elapsed_ms = elapsed
        return response
```

## Rate Limiting

```python
import time
import threading

class RateLimitMiddleware(Middleware):
    def __init__(self, max_per_second=10):
        self._interval = 1.0 / max_per_second
        self._lock = threading.Lock()
        self._last = 0

    def on_request(self, request):
        with self._lock:
            now = time.monotonic()
            wait = self._last + self._interval - now
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
        return request
```

## Circuit Breaker

```python
import time

class CircuitBreaker(Middleware):
    def __init__(self, failure_threshold=5, reset_timeout=30):
        self._failures = 0
        self._threshold = failure_threshold
        self._reset_timeout = reset_timeout
        self._last_failure = 0

    def on_response(self, response):
        if response.status_code >= 500:
            self._failures += 1
            self._last_failure = time.time()
        else:
            self._failures = 0
        return response

    def on_request(self, request):
        if self._failures >= self._threshold:
            if time.time() - self._last_failure > self._reset_timeout:
                self._failures = 0  # half-open
            else:
                raise Exception("Circuit open")
        return request
```

## Error Handler

```python
class ErrorHandler(Middleware):
    def __init__(self, logger):
        self.logger = logger

    def on_error(self, error, request):
        self.logger.error(f"{request.method} {request.url} failed: {error}")
```

## Registering

```python
s = Session()
s.add_middleware(MyMiddleware())
```

## Order

Middleware order matters. The first added is outermost:

```python
s.add_middleware(RequestIDMiddleware())   # outermost
s.add_middleware(LoggingMiddleware())
s.add_middleware(RetryMiddleware())       # innermost
```
