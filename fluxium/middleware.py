"""Middleware / hooks system for Fluxium."""
from __future__ import annotations

import time
from typing import Any, Callable

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
        request._start_time = time.perf_counter()
        self.logger.debug(f"→ {request.method} {request.url}")
        return request

    def on_response(self, response: Response) -> Response:
        elapsed = getattr(response.request, "_start_time", None)
        if elapsed:
            elapsed = (time.perf_counter() - elapsed) * 1000
        self.logger.debug(
            f"← {response.status_code} {response.url} ({elapsed:.1f}ms)"
            if elapsed else f"← {response.status_code} {response.url}"
        )
        return response


class RetryMiddleware(Middleware):
    """Automatic retries with exponential backoff for transient errors."""

    RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}
    RETRYABLE_EXCEPTIONS = ("TimeoutError", "ConnectionError")

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
        if response:
            return response.status_code in self.retry_on_status
        return False

    def get_backoff(self, attempt: int) -> float:
        import random
        backoff = self.backoff_factor * (2 ** attempt)
        return min(backoff + random.uniform(0, 0.1), self.max_backoff)
