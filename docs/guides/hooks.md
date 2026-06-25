# Hooks

`fluxium/session.py`

## Overview

Hooks are lightweight per-request callbacks. Unlike middleware (which is class-based and reusable), hooks are registered per-session and ideal for one-off logging or instrumentation.

## API

```python
session.add_hook(event: str, callback: Callable) -> None
```

## Events

| Event | Arguments | Description |
|---|---|---|
| `"request"` | `(request)` | Called before request is sent |
| `"response"` | `(response, request)` | Called after response is received |
| `"error"` | `(error, request)` | Called on error |

## Examples

### Response Logging

```python
s = Session()
s.add_hook("response", lambda r, req: print(f"{r.status_code} {req.url}"))
```

### Error Notification

```python
s = Session()
s.add_hook("error", lambda e, req: send_alert(f"{req.url} failed: {e}"))
```

### Request Timing

```python
import time

s = Session()

def start_timer(request):
    request._start = time.perf_counter()
    return request

def log_time(response, request):
    elapsed = (time.perf_counter() - request._start) * 1000
    print(f"{request.url}: {elapsed:.1f}ms")

s.add_hook("request", start_timer)
s.add_hook("response", log_time)
```

### Response Modification

```python
def add_header(response, request):
    response.headers["x-processed"] = "true"
    return response

s.add_hook("response", add_header)
```

## vs Middleware

| Feature | Hooks | Middleware |
|---|---|---|
| Registration | Per-session | Per-session |
| Overhead | Lower | Slightly higher |
| Use case | One-off logging | Reusable logic |
| Class required | No | Yes |
| Error handling | Separate hook | `on_error` method |
