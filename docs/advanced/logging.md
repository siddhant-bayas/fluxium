# Logging

## LoggingMiddleware

```python
from fluxium import Session, LoggingMiddleware

s = Session()
s.add_middleware(LoggingMiddleware())
s.get("https://api.example.com")
# DEBUG:fluxium:→ GET https://api.example.com
# DEBUG:fluxium:← 200 https://api.example.com (45.2ms)
```

## Custom Logger

```python
import logging

logger = logging.getLogger("my-app.http")
logger.setLevel(logging.DEBUG)

s = Session()
s.add_middleware(LoggingMiddleware(logger=logger))
```

## Log Levels

- **DEBUG**: request method+URL, response status+URL+elapsed time
- Errors from httpx are propagated as exceptions (not logged by middleware)

## Structured Logging

```python
import logging
import json

class StructuredLoggingMiddleware(Middleware):
    def __init__(self):
        self.logger = logging.getLogger("http")

    def on_request(self, request):
        self.logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "url": str(request.url),
        }))
        request._start = time.perf_counter()
        return request

    def on_response(self, response):
        elapsed = (time.perf_counter() - response.request._start) * 1000
        self.logger.info(json.dumps({
            "event": "response",
            "status": response.status_code,
            "url": str(response.url),
            "elapsed_ms": round(elapsed, 1),
        }))
        return response
```

## Debug Patterns

```python
import logging

# Enable all httpx + fluxium debug logs
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("httpcore").setLevel(logging.DEBUG)

# Or just fluxium
logging.getLogger("fluxium").setLevel(logging.DEBUG)
```
