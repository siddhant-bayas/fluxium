"""Middleware / hooks system for Fluxium."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .models import Request, Response

HookFunc = Callable[..., Any]


class Middleware:
    """Base middleware class. Subclass and override methods."""

    def on_request(self, request: Request) -> Request:
        return request

    def on_response(self, response: Response) -> Response:
        return response

    def on_error(self, error: Exception, request: Request) -> None:
        pass


class MiddlewareStack:
    """Manages a stack of middleware."""

    def __init__(self):
        self._middleware: list[Middleware] = []

    def add(self, mw: Middleware) -> None:
        self._middleware.append(mw)

    def remove(self, mw: Middleware) -> None:
        self._middleware.remove(mw)

    def apply_request(self, request: Request) -> Request:
        for mw in self._middleware:
            request = mw.on_request(request)
        return request

    def apply_response(self, response: Response) -> Response:
        for mw in self._middleware:
            response = mw.on_response(response)
        return response

    def apply_error(self, error: Exception, request: Request) -> None:
        for mw in self._middleware:
            mw.on_error(error, request)

    def __len__(self) -> int:
        return len(self._middleware)

    def __bool__(self) -> bool:
        return bool(self._middleware)


class LoggingMiddleware(Middleware):
    """Logs all requests and responses."""

    def __init__(self, logger=None):
        import logging

        self.logger = logger or logging.getLogger("fluxium")

    def on_request(self, request: Request) -> Request:
        request._start_time = time.perf_counter()  # type: ignore[attr-defined]
        self.logger.debug(f"→ {request.method} {request.url}")
        return request

    def on_response(self, response: Response) -> Response:
        elapsed = getattr(response.request, "_start_time", None)
        if elapsed:
            elapsed = (time.perf_counter() - elapsed) * 1000
        self.logger.debug(
            f"← {response.status_code} {response.url} ({elapsed:.1f}ms)"
            if elapsed
            else f"← {response.status_code} {response.url}"
        )
        return response


class RetryMiddleware(Middleware):
    """Automatic retries with exponential backoff for transient errors."""

    RETRYABLE_STATUS: frozenset[int] = frozenset({408, 429, 500, 502, 503, 504})
    RETRYABLE_EXCEPTIONS: tuple[str, ...] = ("TimeoutError", "ConnectionError")

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        max_backoff: float = 30.0,
        retry_on_status: set[int] | None = None,
    ):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.max_backoff = max_backoff
        self.retry_on_status = retry_on_status or self.RETRYABLE_STATUS

    def should_retry(self, response: Response | None, error: Exception | None) -> bool:
        if error:
            return type(error).__name__ in self.RETRYABLE_EXCEPTIONS
        if response is not None:
            return response.status_code in self.retry_on_status
        return False

    def get_backoff(self, attempt: int) -> float:
        import random

        backoff: float = self.backoff_factor * (2**attempt)
        return min(backoff + random.uniform(0, 0.1), self.max_backoff)


class RateLimitMiddleware(Middleware):
    """Rate limiting middleware using a token bucket.

    Limits requests to `calls` per `period` seconds.

    Example:
        # Max 100 requests per 60 seconds
        session.add_middleware(RateLimitMiddleware(calls=100, period=60))
    """

    def __init__(self, calls: int = 100, period: float = 60.0):
        self._calls = calls
        self._period = period
        self._tokens = float(calls)
        self._max_tokens = float(calls)
        self._refill_rate = calls / period
        import time

        self._time = time
        self._last_refill = time.monotonic()

    def on_request(self, request: Request) -> Request:
        now = self._time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._max_tokens, self._tokens + elapsed * self._refill_rate)
        self._last_refill = now

        if self._tokens < 1.0:
            wait = (1.0 - self._tokens) / self._refill_rate
            self._time.sleep(wait)
            self._tokens = 0.0
            self._last_refill = self._time.monotonic()
        else:
            self._tokens -= 1.0

        return request
