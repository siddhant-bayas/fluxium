# Middleware

`fluxium/middleware.py`

## Middleware

```python
class Middleware:
    def on_request(self, request: Request) -> Request
    def on_response(self, response: Response) -> Response
    def on_error(self, error: Exception, request: Request) -> None
```

Base class. Override the hooks you need.

## MiddlewareStack

```python
class MiddlewareStack:
    def add(self, mw: Middleware) -> None
    def remove(self, mw: Middleware) -> None
    def apply_request(request: Request) -> Request
    def apply_response(response: Response) -> Response
    def apply_error(error: Exception, request: Request) -> None
    def __len__() -> int
    def __bool__() -> bool
```

Internal — managed by Session. You interact via `session.add_middleware()`.

## LoggingMiddleware

```python
class LoggingMiddleware(Middleware):
    def __init__(self, logger: logging.Logger | None = None)
```

Logs `→ METHOD URL` and `← STATUS URL (XXms)` at DEBUG level.

## RetryMiddleware

```python
class RetryMiddleware(Middleware):
    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        max_backoff: float = 30.0,
        retry_on_status: set[int] | None = None,
    )
```

### Attributes

| Attribute | Type | Default | Description |
|---|---|---|
| `max_retries` | `int` | `3` | Max retry attempts |
| `backoff_factor` | `float` | `0.5` | Exponential factor |
| `max_backoff` | `float` | `30.0` | Backoff cap |
| `retry_on_status` | `set[int] \| None` | `{408, 429, 500, 502, 503, 504}` | Retryable status codes |

### Methods

| Method | Returns | Description |
|---|---|---|
| `should_retry(response, error)` | `bool` | Whether to retry |
| `get_backoff(attempt)` | `float` | Backoff duration for attempt |
