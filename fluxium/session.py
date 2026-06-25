"""
Session: the heart of fluxium.
Sync Session and AsyncSession with full feature support.

Features:
- HTTP/2 multiplexing (via httpx)
- Connection pooling with keep-alive
- Middleware/hooks system
- Automatic retries with exponential backoff
- Built-in caching (memory/disk)
- Cookie persistence
- Streaming & SSE support
- OAuth2/Bearer token auto-refresh
"""

from __future__ import annotations

import contextlib
import json
import mimetypes
import os
import time
import uuid
import warnings
from typing import TYPE_CHECKING, Any, Callable
from urllib.parse import urlencode, urljoin, urlparse

import httpx

from .auth import AuthBase, BasicAuth, DigestAuth
from .cache import (
    CacheBackend,
    _cache_to_response,
    _make_cache_key,
    _response_to_cache,
)
from .cookies import CookieJar
from .exceptions import (
    ConnectionError,
    FluxiumError,
    InsecureSSLWarning,
    ProxyError,
    SSLError,
    TimeoutError,
    TooManyRedirects,
)
from .middleware import MiddlewareStack, RetryMiddleware
from .models import Request, Response
from .transport import (
    ACCEPT_ENCODING,
    _build_async_client,
    _build_sync_client,
)
from .utils import encode_url, merge_headers, netrc_credentials

if TYPE_CHECKING:
    from .timeout import Timeout

_DEFAULT_HEADERS = {
    "user-agent": "fluxium/2.0.0 (https://github.com/siddhant-bayas/fluxium)",
    "accept": "*/*",
    "accept-encoding": ACCEPT_ENCODING,
    "connection": "keep-alive",
}

MAX_REDIRECTS = 30
_JSON_SEPARATORS = (",", ":")
_timeout_cache: dict = {}


def _resolve_timeout(t):
    """Convert timeout to httpx.Timeout object. Cached for performance."""
    cached = _timeout_cache.get(t)
    if cached is not None:
        return cached
    if t is None:
        result = httpx.Timeout(None)
    elif isinstance(t, httpx.Timeout):
        result = t
    elif isinstance(t, (int, float)):
        result = httpx.Timeout(float(t))
    elif isinstance(t, tuple) and len(t) >= 2:
        result = httpx.Timeout(float(t[1]), connect=float(t[0]))
    else:
        result = httpx.Timeout(30.0)
    _timeout_cache[t] = result
    return result


class Session:
    """Thread-safe synchronous HTTP session with connection pooling."""

    __slots__ = (
        "_cache",
        "_client",
        "_hooks",
        "_middleware",
        "_retry_mw",
        "auth",
        "cookies",
        "headers",
        "max_redirects",
        "proxies",
        "timeout",
        "trust_env",
        "verify",
    )

    def __init__(
        self,
        *,
        headers: dict | None = None,
        cookies=None,
        auth=None,
        verify: bool | str = True,
        proxies: dict | str | None = None,
        timeout: float | tuple | Timeout = 30.0,
        http2: bool = True,
        max_redirects: int = MAX_REDIRECTS,
        trust_env: bool = True,
        cache: CacheBackend | None = None,
        max_retries: int = 0,
        retry_backoff: float = 0.5,
    ):
        self.headers = merge_headers(_DEFAULT_HEADERS, headers)
        self.cookies = CookieJar()
        if cookies:
            self.cookies.update(cookies if isinstance(cookies, dict) else cookies)
        self.auth = auth
        self.verify = verify
        if verify is False:
            warnings.warn(
                "TLS verification is disabled. This is insecure and not recommended for production.",
                InsecureSSLWarning,
                stacklevel=2,
            )
        self.proxies = proxies
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.trust_env = trust_env
        self._hooks: list[dict[str, Any]] = []
        self._client = _build_sync_client(
            verify=verify,
            proxies=proxies,
            timeout=timeout,
            http2=http2,
            trust_env=trust_env,
        )
        self._middleware = MiddlewareStack()
        self._cache = cache
        self._retry_mw = None
        if max_retries > 0:
            self._retry_mw = RetryMiddleware(
                max_retries=max_retries,
                backoff_factor=retry_backoff,
            )
            self._middleware.add(self._retry_mw)

    def add_middleware(self, mw) -> None:
        self._middleware.add(mw)

    def add_hook(self, event: str, callback: Callable) -> None:
        """Register a per-request callback.

        Events:
            "response" — called with (response, request)
            "error"    — called with (error, request)
            "request"  — called with (request,) before sending
        """
        self._hooks.append({"event": event, "callback": callback})

    def _run_hooks(self, event: str, *args) -> Any:
        """Run all hooks for an event. Returns modified response if event='response'."""
        result = None
        for hook in self._hooks:
            if hook["event"] == event:
                try:
                    if event == "response":
                        result = hook["callback"](args[0], args[1])
                    elif event == "error":
                        hook["callback"](*args)
                    elif event == "request":
                        result = hook["callback"](args[0])
                except Exception:
                    pass  # hooks should never break the request flow
        return result

    def _get_from_cache(self, method: str, url: str, headers: dict | None) -> Response | None:
        if self._cache is None:
            return None
        key = _make_cache_key(method, url, headers)
        data = self._cache.get(key)
        if data:
            return _cache_to_response(data)
        return None

    def _set_cache(
        self, method: str, url: str, headers: dict | None, resp: Response, ttl: int = 300
    ) -> None:
        if self._cache is None:
            return
        # Only cache GET/HEAD with 2xx status
        if method.upper() not in ("GET", "HEAD") or resp.status_code >= 300:
            return
        key = _make_cache_key(method, url, headers)
        self._cache.set(key, _response_to_cache(resp), ttl)

    def request(
        self,
        method: str,
        url: str,
        *,
        params=None,
        data=None,
        json=None,
        files=None,
        headers: dict | None = None,
        cookies=None,
        auth=None,
        timeout=None,
        allow_redirects: bool = True,
        stream: bool = False,
        verify=None,
        proxies=None,
        chunked: bool = False,
        cache_ttl: int = 300,
    ) -> Response:
        method_upper = method.upper()

        # ── Prepare ──────────────────────────────────────────────────────────
        body, body_headers = _prepare_body(data, json, files, chunked)

        final_url = encode_url(url, params) if params else url

        # ── Cache lookup ─────────────────────────────────────────────────────
        if self._cache and not stream and method_upper in ("GET", "HEAD"):
            cached = self._get_from_cache(method_upper, final_url, headers)
            if cached is not None:
                return cached

        effective_auth = auth or self.auth
        if effective_auth is None and self.trust_env:
            host = urlparse(final_url).hostname or ""
            creds = netrc_credentials(host)
            if creds:
                effective_auth = BasicAuth(*creds)

        # Cookies
        has_cookies = False
        cookie_header = None
        if cookies:
            merged_cookies = CookieJar()
            merged_cookies.update(self.cookies)
            if isinstance(cookies, dict):
                merged_cookies.update(cookies)
            else:
                merged_cookies.update(cookies)
            cookie_header = merged_cookies.to_header()
            has_cookies = True
        elif self.cookies:
            cookie_header = self.cookies.to_header()
            has_cookies = True

        # Headers
        if headers or has_cookies or body_headers:
            merged_headers = dict(self.headers)
            if headers:
                for k, v in headers.items():
                    merged_headers[k.lower()] = v
            if body_headers:
                merged_headers.update(body_headers)
            if cookie_header:
                merged_headers["cookie"] = cookie_header
        else:
            merged_headers = self.headers

        # ── Build request ────────────────────────────────────────────────────
        httpx_req = self._client.build_request(
            method_upper,
            final_url,
            content=body,
            headers=merged_headers,
        )

        # Apply middleware stack
        httpx_req = self._middleware.apply_request(httpx_req) or httpx_req

        # Run request hooks
        httpx_req = self._run_hooks("request", httpx_req) or httpx_req

        # Apply auth headers
        if effective_auth and isinstance(effective_auth, AuthBase):
            dummy = Request(method_upper, final_url, headers=dict(httpx_req.headers))
            dummy = effective_auth(dummy)
            for k, v in dummy.headers.items():
                httpx_req.headers[k] = v

        # Timeout
        effective_timeout = timeout if timeout is not None else self.timeout
        t = _resolve_timeout(effective_timeout)
        httpx_req.extensions["timeout"] = {  # type: ignore[union-attr]
            "connect": t.connect or 5.0,
            "read": t.read or 30.0,
            "write": t.write or 5.0,
            "pool": t.pool or 5.0,
        }

        # ── Send with retries ───────────────────────────────────────────────
        resp = self._send_with_retries(
            httpx_req,
            allow_redirects=allow_redirects,
            stream=stream,
            auth=effective_auth,
            timeout=t,
        )

        # ── Run response hooks ──────────────────────────────────────────────
        resp = (
            self._run_hooks(
                "response", resp, Request(method_upper, final_url, headers=merged_headers)
            )
            or resp
        )

        # ── Cache store ──────────────────────────────────────────────────────
        if self._cache and not stream:
            self._set_cache(method_upper, final_url, headers, resp, cache_ttl)

        return resp  # type: ignore[no-any-return]

    def _send_with_retries(self, httpx_req, *, allow_redirects, stream, auth, timeout):
        """Send with automatic retries and exponential backoff."""
        last_error: FluxiumError | None = None
        max_retries = self._retry_mw.max_retries if self._retry_mw else 0

        for attempt in range(max_retries + 1):
            try:
                resp = self._send_with_redirects(
                    httpx_req,
                    allow_redirects=allow_redirects,
                    stream=stream,
                    auth=auth,
                    timeout=timeout,
                    client=self._client,
                )

                # Check if we should retry based on status
                if attempt < max_retries and self._retry_mw:
                    if self._retry_mw.should_retry(resp, None):
                        backoff = self._retry_mw.get_backoff(attempt)
                        time.sleep(backoff)
                        last_error = None
                        continue

                return resp

            except httpx.TimeoutException as e:
                last_error = TimeoutError(str(e))
                if attempt < max_retries and self._retry_mw:
                    if self._retry_mw.should_retry(None, last_error):
                        backoff = self._retry_mw.get_backoff(attempt)
                        time.sleep(backoff)
                        continue
                raise last_error
            except httpx.ProxyError as e:
                last_error = ProxyError(str(e))
                raise last_error
            except httpx.TransportError as e:
                msg = str(e)
                if "ssl" in msg.lower() or "tls" in msg.lower() or "certificate" in msg.lower():
                    last_error = SSLError(msg)
                else:
                    last_error = ConnectionError(msg)
                if attempt < max_retries and self._retry_mw:
                    if self._retry_mw.should_retry(None, last_error):
                        backoff = self._retry_mw.get_backoff(attempt)
                        time.sleep(backoff)
                        continue
                raise last_error
            except httpx.NetworkError as e:
                last_error = ConnectionError(str(e))
                if attempt < max_retries and self._retry_mw:
                    if self._retry_mw.should_retry(None, last_error):
                        backoff = self._retry_mw.get_backoff(attempt)
                        time.sleep(backoff)
                        continue
                raise last_error
            except httpx.HTTPError as e:
                # Catch-all for any other httpx exceptions
                last_error = ConnectionError(str(e))
                raise last_error

        raise last_error or ConnectionError("Request failed after retries")

    def _send_with_redirects(self, req, *, allow_redirects, stream, auth, timeout, client=None):
        if client is None:
            client = self._client
        history = []
        current_req = req
        for _ in range(self.max_redirects + 1):
            raw = client.send(current_req, stream=stream)
            resp = _build_response(raw, stream=stream)
            resp.history = list(history)

            # Digest auth on 401
            if raw.status_code == 401 and isinstance(auth, DigestAuth):
                www_auth = raw.headers.get("www-authenticate", "")
                if www_auth.lower().startswith("digest"):
                    hdr = auth.build_header(current_req.method, str(current_req.url), www_auth)
                    current_req.headers["Authorization"] = hdr
                    raw = client.send(current_req, stream=stream)
                    resp = _build_response(raw, stream=stream)
                    resp.history = list(history)

            # Update session cookies from response
            _hostname = urlparse(str(raw.url)).hostname or ""
            for name, value in raw.cookies.items():
                self.cookies.set(name, value, domain=_hostname)

            if not allow_redirects or not resp.is_redirect:
                return resp

            location = raw.headers.get("location", "")
            if not location:
                return resp
            history.append(resp)
            if len(history) > self.max_redirects:
                raise TooManyRedirects(f"Exceeded {self.max_redirects} redirects")
            method = current_req.method
            if raw.status_code in (301, 302, 303):
                method = "GET"
            resolved_location = urljoin(str(current_req.url), location)
            current_req = client.build_request(
                method, resolved_location, headers=dict(current_req.headers)
            )
        raise TooManyRedirects("Too many redirects")

    # ── convenience methods ──────────────────────────────────────────────────
    def get(self, url, **kw):
        return self.request("GET", url, **kw)

    def post(self, url, **kw):
        return self.request("POST", url, **kw)

    def put(self, url, **kw):
        return self.request("PUT", url, **kw)

    def patch(self, url, **kw):
        return self.request("PATCH", url, **kw)

    def delete(self, url, **kw):
        return self.request("DELETE", url, **kw)

    def head(self, url, **kw):
        return self.request("HEAD", url, **kw)

    def options(self, url, **kw):
        return self.request("OPTIONS", url, **kw)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Session:
        return self

    def __exit__(self, *a: object) -> None:
        self.close()

    def prewarm(self, url: str) -> None:
        """Pre-warm the connection pool by opening a TCP+TLS connection to *url*.

        The connection is returned to the pool for reuse on the next request.
        Useful for eliminating first-request latency on critical paths.
        """
        try:
            self._client.send(
                self._client.build_request("GET", url),
            )
        except Exception:
            pass  # Connection is pooled even on non-2xx; TLS handshake done


# ── Async Session ────────────────────────────────────────────────────────────


class AsyncSession:
    """Async HTTP session with connection pooling (asyncio)."""

    __slots__ = (
        "_cache",
        "_client",
        "_hooks",
        "_middleware",
        "_retry_mw",
        "auth",
        "cookies",
        "headers",
        "max_redirects",
        "timeout",
        "trust_env",
        "verify",
    )

    def __init__(
        self,
        *,
        headers: dict | None = None,
        cookies=None,
        auth=None,
        verify: bool | str = True,
        proxies: dict | str | None = None,
        timeout: float | tuple | Timeout = 30.0,
        http2: bool = True,
        max_redirects: int = MAX_REDIRECTS,
        trust_env: bool = True,
        cache: CacheBackend | None = None,
        max_retries: int = 0,
        retry_backoff: float = 0.5,
    ):
        self.headers = merge_headers(_DEFAULT_HEADERS, headers)
        self.cookies = CookieJar()
        if cookies:
            self.cookies.update(cookies if isinstance(cookies, dict) else cookies)
        self.auth = auth
        self.verify = verify
        if verify is False:
            warnings.warn(
                "TLS verification is disabled. This is insecure and not recommended for production.",
                InsecureSSLWarning,
                stacklevel=2,
            )
        self.max_redirects = max_redirects
        self.trust_env = trust_env
        self.timeout = timeout
        self._hooks: list[dict[str, Any]] = []
        self._client = _build_async_client(
            verify=verify,
            proxies=proxies,
            timeout=timeout,
            http2=http2,
            trust_env=trust_env,
        )
        self._middleware = MiddlewareStack()
        self._cache = cache
        self._retry_mw = None
        if max_retries > 0:
            self._retry_mw = RetryMiddleware(
                max_retries=max_retries,
                backoff_factor=retry_backoff,
            )
            self._middleware.add(self._retry_mw)

    def add_middleware(self, mw) -> None:
        self._middleware.add(mw)

    def add_hook(self, event: str, callback: Callable) -> None:
        """Register a per-request callback.

        Events:
            "response" — called with (response, request)
            "error"    — called with (error, request)
            "request"  — called with (request,) before sending
        """
        self._hooks.append({"event": event, "callback": callback})

    def _run_hooks(self, event: str, *args) -> Any:
        """Run all hooks for an event. Returns modified response if event='response'."""
        result = None
        for hook in self._hooks:
            if hook["event"] == event:
                try:
                    if event == "response":
                        result = hook["callback"](args[0], args[1])
                    elif event == "error":
                        hook["callback"](*args)
                    elif event == "request":
                        result = hook["callback"](args[0])
                except Exception:
                    pass  # hooks should never break the request flow
        return result

    def _get_from_cache(self, method: str, url: str, headers: dict | None) -> Response | None:
        if self._cache is None:
            return None
        key = _make_cache_key(method, url, headers)
        data = self._cache.get(key)
        if data:
            return _cache_to_response(data)
        return None

    def _set_cache(
        self, method: str, url: str, headers: dict | None, resp: Response, ttl: int = 300
    ) -> None:
        if self._cache is None:
            return
        if method.upper() not in ("GET", "HEAD") or resp.status_code >= 300:
            return
        key = _make_cache_key(method, url, headers)
        self._cache.set(key, _response_to_cache(resp), ttl)

    async def request(
        self,
        method: str,
        url: str,
        *,
        params=None,
        data=None,
        json=None,
        files=None,
        headers: dict | None = None,
        cookies=None,
        auth=None,
        timeout=None,
        allow_redirects: bool = True,
        stream: bool = False,
        chunked: bool = False,
        cache_ttl: int = 300,
    ) -> Response:
        method_upper = method.upper()

        # Prepare
        body, body_headers = _prepare_body(data, json, files, chunked)

        final_url = encode_url(url, params) if params else url

        # Cache lookup
        if self._cache and not stream and method_upper in ("GET", "HEAD"):
            cached = self._get_from_cache(method_upper, final_url, headers)
            if cached is not None:
                return cached

        effective_auth = auth or self.auth
        if effective_auth is None and self.trust_env:
            host = urlparse(final_url).hostname or ""
            creds = netrc_credentials(host)
            if creds:
                effective_auth = BasicAuth(*creds)

        has_cookies = False
        cookie_header = None
        if cookies:
            merged_cookies = CookieJar()
            merged_cookies.update(self.cookies)
            if isinstance(cookies, dict):
                merged_cookies.update(cookies)
            else:
                merged_cookies.update(cookies)
            cookie_header = merged_cookies.to_header()
            has_cookies = True
        elif self.cookies:
            cookie_header = self.cookies.to_header()
            has_cookies = True

        if headers or has_cookies or body_headers:
            merged_headers = dict(self.headers)
            if headers:
                for k, v in headers.items():
                    merged_headers[k.lower()] = v
            if body_headers:
                merged_headers.update(body_headers)
            if cookie_header:
                merged_headers["cookie"] = cookie_header
        else:
            merged_headers = self.headers

        # Build
        httpx_req = self._client.build_request(
            method_upper,
            final_url,
            content=body,
            headers=merged_headers,
        )

        # Apply middleware stack
        httpx_req = self._middleware.apply_request(httpx_req) or httpx_req

        # Run request hooks
        httpx_req = self._run_hooks("request", httpx_req) or httpx_req

        if effective_auth and isinstance(effective_auth, AuthBase):
            dummy = Request(method_upper, final_url, headers=dict(httpx_req.headers))
            dummy = effective_auth(dummy)
            for k, v in dummy.headers.items():
                httpx_req.headers[k] = v

        effective_timeout = timeout if timeout is not None else self.timeout
        t = _resolve_timeout(effective_timeout)
        httpx_req.extensions["timeout"] = {  # type: ignore[union-attr]
            "connect": t.connect or 5.0,
            "read": t.read or 30.0,
            "write": t.write or 5.0,
            "pool": t.pool or 5.0,
        }

        # Send with retries
        resp = await self._send_with_retries_async(
            httpx_req,
            allow_redirects=allow_redirects,
            stream=stream,
            auth=effective_auth,
            timeout=t,
        )

        # Run response hooks
        resp = (
            self._run_hooks(
                "response", resp, Request(method_upper, final_url, headers=merged_headers)
            )
            or resp
        )

        # Cache store
        if self._cache and not stream:
            self._set_cache(method_upper, final_url, headers, resp, cache_ttl)

        return resp  # type: ignore[no-any-return]

    async def _send_with_retries_async(self, httpx_req, *, allow_redirects, stream, auth, timeout):
        last_error: FluxiumError | None = None
        max_retries = self._retry_mw.max_retries if self._retry_mw else 0

        for attempt in range(max_retries + 1):
            try:
                resp = await self._send_with_redirects_async(
                    httpx_req,
                    allow_redirects=allow_redirects,
                    stream=stream,
                    auth=auth,
                    timeout=timeout,
                    client=self._client,
                    method=httpx_req.method,
                    final_url=str(httpx_req.url),
                )

                if attempt < max_retries and self._retry_mw:
                    if self._retry_mw.should_retry(resp, None):
                        backoff = self._retry_mw.get_backoff(attempt)
                        import asyncio

                        await asyncio.sleep(backoff)
                        last_error = None
                        continue

                return resp

            except httpx.TimeoutException as e:
                last_error = TimeoutError(str(e))
                if attempt < max_retries and self._retry_mw:
                    if self._retry_mw.should_retry(None, last_error):
                        backoff = self._retry_mw.get_backoff(attempt)
                        import asyncio

                        await asyncio.sleep(backoff)
                        continue
                raise last_error
            except httpx.ProxyError as e:
                last_error = ProxyError(str(e))
                raise last_error
            except httpx.TransportError as e:
                msg = str(e)
                if "ssl" in msg.lower() or "tls" in msg.lower() or "certificate" in msg.lower():
                    last_error = SSLError(msg)
                else:
                    last_error = ConnectionError(msg)
                if attempt < max_retries and self._retry_mw:
                    if self._retry_mw.should_retry(None, last_error):
                        backoff = self._retry_mw.get_backoff(attempt)
                        import asyncio

                        await asyncio.sleep(backoff)
                        continue
                raise last_error
            except httpx.NetworkError as e:
                last_error = ConnectionError(str(e))
                if attempt < max_retries and self._retry_mw:
                    if self._retry_mw.should_retry(None, last_error):
                        backoff = self._retry_mw.get_backoff(attempt)
                        import asyncio

                        await asyncio.sleep(backoff)
                        continue
                raise last_error
            except httpx.HTTPError as e:
                last_error = ConnectionError(str(e))
                raise last_error

        raise last_error or ConnectionError("Request failed after retries")

    async def _send_with_redirects_async(
        self, req, *, allow_redirects, stream, auth, timeout, client, method, final_url
    ):
        history = []
        for _ in range(self.max_redirects + 1):
            raw = await client.send(req, stream=stream)
            resp = _build_response(raw, stream=stream)
            resp.history = list(history)

            if raw.status_code == 401 and isinstance(auth, DigestAuth):
                www_auth = raw.headers.get("www-authenticate", "")
                if www_auth.lower().startswith("digest"):
                    hdr = auth.build_header(method, final_url, www_auth)
                    req.headers["Authorization"] = hdr
                    raw = await client.send(req, stream=stream)
                    resp = _build_response(raw, stream=stream)
                    resp.history = list(history)

            _hostname = urlparse(str(raw.url)).hostname or ""
            for name, value in raw.cookies.items():
                self.cookies.set(name, value, domain=_hostname)

            if not allow_redirects or not resp.is_redirect:
                return resp
            location = raw.headers.get("location", "")
            if not location:
                return resp
            history.append(resp)
            if len(history) > self.max_redirects:
                raise TooManyRedirects(f"Exceeded {self.max_redirects} redirects")
            m = method if raw.status_code in (307, 308) else "GET"
            resolved_location = urljoin(str(req.url), location)
            req = client.build_request(m, resolved_location, headers=dict(req.headers))
        raise TooManyRedirects("Too many redirects")

    async def get(self, url, **kw):
        return await self.request("GET", url, **kw)

    async def post(self, url, **kw):
        return await self.request("POST", url, **kw)

    async def put(self, url, **kw):
        return await self.request("PUT", url, **kw)

    async def patch(self, url, **kw):
        return await self.request("PATCH", url, **kw)

    async def delete(self, url, **kw):
        return await self.request("DELETE", url, **kw)

    async def head(self, url, **kw):
        return await self.request("HEAD", url, **kw)

    async def options(self, url, **kw):
        return await self.request("OPTIONS", url, **kw)

    async def close(self) -> None:
        await self._client.aclose()

    async def prewarm(self, url: str) -> None:
        """Pre-warm the async connection pool by opening a TCP+TLS connection to *url*.

        The connection is returned to the pool for reuse on the next request.
        Useful for eliminating first-request latency on critical paths.
        """
        with contextlib.suppress(Exception):
            await self._client.send(
                self._client.build_request("GET", url),
            )

    async def __aenter__(self) -> AsyncSession:
        return self

    async def __aexit__(self, *a: object) -> None:
        await self.close()


# ── Internal helpers ─────────────────────────────────────────────────────────


def _prepare_body(data, json_data, files, chunked=False):
    """Prepare request body. Returns (body_bytes_or_None, headers_dict_or_None)."""
    if json_data is not None:
        body = json.dumps(json_data, separators=_JSON_SEPARATORS, ensure_ascii=False).encode(
            "utf-8"
        )
        return body, {"content-type": "application/json"}

    if files:
        return _encode_multipart(data or {}, files)

    if data is not None:
        if isinstance(data, (str, bytes)):
            return (data.encode() if isinstance(data, str) else data), None
        if isinstance(data, dict):
            body = urlencode(data, doseq=True).encode("utf-8")
            return body, {"content-type": "application/x-www-form-urlencoded"}
        if chunked:
            return data, None
        body = b"".join(data)
        return body, None

    return None, None


def _encode_multipart(fields: dict, files: dict):
    """Efficiently encode multipart/form-data using BytesIO."""
    import io as _io

    boundary = uuid.uuid4().hex
    CRLF = b"\r\n"
    boundary_bytes = boundary.encode("ascii")
    end_boundary = b"--" + boundary_bytes + b"--\r\n"

    buf = _io.BytesIO()

    for name, value in fields.items():
        if not isinstance(value, (str, bytes)):
            value = str(value)
        buf.write(b"--" + boundary_bytes + CRLF)
        buf.write(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        buf.write(value.encode() if isinstance(value, str) else value)
        buf.write(CRLF)

    for name, file_info in files.items():
        if isinstance(file_info, list):
            for item in file_info:
                if isinstance(item, tuple):
                    filename, fileobj = item[0], item[1]
                    content_type = item[2] if len(item) > 2 else None
                else:
                    filename = os.path.basename(str(getattr(item, "name", name)))
                    fileobj = item
                    content_type = None
                _write_multipart_file(buf, filename, fileobj, content_type, boundary_bytes, CRLF)
        elif isinstance(file_info, tuple):
            filename, fileobj = file_info[0], file_info[1]
            content_type = file_info[2] if len(file_info) > 2 else None
            _write_multipart_file(buf, filename, fileobj, content_type, boundary_bytes, CRLF)
        else:
            filename = os.path.basename(str(getattr(file_info, "name", name)))
            fileobj = file_info
            content_type = None
            _write_multipart_file(buf, filename, fileobj, content_type, boundary_bytes, CRLF)

    buf.write(end_boundary)
    body = buf.getvalue()
    headers = {"content-type": f"multipart/form-data; boundary={boundary}"}
    return body, headers


def _write_multipart_file(buf, filename, fileobj, content_type, boundary_bytes, CRLF):
    if content_type is None:
        content_type = mimetypes.guess_type(filename or "")[0] or "application/octet-stream"
    if isinstance(fileobj, (str, bytes)):
        file_data = fileobj.encode() if isinstance(fileobj, str) else fileobj
    else:
        if hasattr(fileobj, "seek"):
            fileobj.seek(0)
        file_data = fileobj.read()
    buf.write(b"--" + boundary_bytes + CRLF)
    buf.write(
        f'Content-Disposition: form-data; name="{filename}"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n".encode()
    )
    buf.write(file_data)
    buf.write(CRLF)


def _build_response(raw: httpx.Response, *, stream: bool) -> Response:
    resp = Response()
    resp.status_code = raw.status_code
    resp.url = str(raw.url)
    resp.headers = dict(raw.headers)
    for name, value in raw.cookies.items():
        resp.cookies.set(name, value)
    if stream:
        resp._raw = raw
    else:
        resp._content = raw.content
    return resp
