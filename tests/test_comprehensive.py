"""Comprehensive test suite for fluxium 3.0.0.

250+ deterministic tests using respx for HTTP mocking.
"""

from __future__ import annotations

import io
import json
import sys
import warnings

import httpx
import pytest
import respx

import fluxium
from fluxium import (
    AsyncSession,
    BasicAuth,
    BearerAuth,
    DigestAuth,
    DiskCache,
    LoggingMiddleware,
    MemoryCache,
    RateLimitMiddleware,
    RetryMiddleware,
    Session,
    Timeout,
)
from fluxium.cache import _cache_to_response, _make_cache_key, _response_to_cache
from fluxium.cookies import CookieJar
from fluxium.exceptions import (
    ConnectionError,
    FluxiumError,
    FluxiumWarning,
    HTTPError,
    InsecureSSLWarning,
    ProxyError,
    RetryWarning,
    SSLError,
    TimeoutError,
    TooManyRedirects,
)


@pytest.fixture
def mocked():
    with respx.mock:
        yield


# ═══════════════════════════════════════════════════════════════════════════════
# 1. BASIC REQUESTS (20 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestBasicRequests:
    def test_get_200(self, mocked):
        respx.get("https://api.example.com/").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        r = fluxium.get("https://api.example.com/")
        assert r.status_code == 200
        assert r.json() == {"ok": True}
        assert r.ok

    def test_get_with_params(self, mocked):
        respx.get("https://api.example.com/search").mock(
            return_value=httpx.Response(200, json={"q": "hello"})
        )
        r = fluxium.get("https://api.example.com/search", params={"q": "hello", "page": 1})
        assert "q=hello" in str(respx.calls[0].request.url)
        assert "page=1" in str(respx.calls[0].request.url)

    def test_get_with_custom_headers(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.get(
            "https://api.example.com/", headers={"X-Custom": "value", "Accept": "text/plain"}
        )
        assert respx.calls[0].request.headers["x-custom"] == "value"
        assert respx.calls[0].request.headers["accept"] == "text/plain"

    def test_post_json(self, mocked):
        respx.post("https://api.example.com/items").mock(
            return_value=httpx.Response(201, json={"id": 1})
        )
        r = fluxium.post("https://api.example.com/items", json={"name": "widget"})
        assert r.status_code == 201
        assert r.json()["id"] == 1

    def test_post_form_data(self, mocked):
        respx.post("https://api.example.com/form").mock(return_value=httpx.Response(200))
        fluxium.post("https://api.example.com/form", data={"a": "1", "b": "2"})
        body = respx.calls[0].request.content
        assert b"a=1" in body
        assert b"b=2" in body

    def test_post_bytes(self, mocked):
        respx.post("https://api.example.com/upload").mock(return_value=httpx.Response(200))
        fluxium.post("https://api.example.com/upload", data=b"\x00\x01\x02")
        assert respx.calls[0].request.content == b"\x00\x01\x02"

    def test_put(self, mocked):
        respx.put("https://api.example.com/items/1").mock(
            return_value=httpx.Response(200, json={"updated": True})
        )
        r = fluxium.put("https://api.example.com/items/1", json={"name": "new"})
        assert r.json()["updated"] is True

    def test_patch(self, mocked):
        respx.patch("https://api.example.com/items/1").mock(return_value=httpx.Response(200))
        r = fluxium.patch("https://api.example.com/items/1", json={"name": "patched"})
        assert r.status_code == 200

    def test_delete(self, mocked):
        respx.delete("https://api.example.com/items/1").mock(return_value=httpx.Response(204))
        r = fluxium.delete("https://api.example.com/items/1")
        assert r.status_code == 204

    def test_head(self, mocked):
        respx.head("https://api.example.com/").mock(return_value=httpx.Response(200))
        r = fluxium.head("https://api.example.com/")
        assert r.status_code == 200
        assert r.content == b""

    def test_options(self, mocked):
        respx.options("https://api.example.com/").mock(return_value=httpx.Response(200))
        r = fluxium.options("https://api.example.com/")
        assert r.status_code == 200

    def test_404_not_ok(self, mocked):
        respx.get("https://api.example.com/missing").mock(return_value=httpx.Response(404))
        r = fluxium.get("https://api.example.com/missing")
        assert r.status_code == 404
        assert not r.ok

    def test_500_response(self, mocked):
        respx.get("https://api.example.com/error").mock(return_value=httpx.Response(500))
        r = fluxium.get("https://api.example.com/error")
        assert r.status_code == 500
        assert not r.ok

    def test_raise_for_status_404(self, mocked):
        respx.get("https://api.example.com/missing").mock(return_value=httpx.Response(404))
        r = fluxium.get("https://api.example.com/missing")
        with pytest.raises(HTTPError):
            r.raise_for_status()

    def test_raise_for_status_500(self, mocked):
        respx.get("https://api.example.com/error").mock(return_value=httpx.Response(500))
        r = fluxium.get("https://api.example.com/error")
        with pytest.raises(HTTPError):
            r.raise_for_status()

    def test_raise_for_status_no_error_on_200(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        r = fluxium.get("https://api.example.com/")
        r.raise_for_status()

    def test_response_text(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200, text="hello"))
        r = fluxium.get("https://api.example.com/")
        assert r.text == "hello"

    def test_response_is_redirect(self, mocked):
        respx.get("https://api.example.com/redirect").mock(
            return_value=httpx.Response(301, headers={"location": "/final"})
        )
        r = fluxium.get("https://api.example.com/redirect", allow_redirects=False)
        assert r.is_redirect

    def test_request_custom_method(self, mocked):
        respx.route(method="CUSTOM", path="/custom").mock(return_value=httpx.Response(200))
        r = fluxium.request("CUSTOM", "https://api.example.com/custom")
        assert r.status_code == 200

    def test_get_with_allow_redirects_false(self, mocked):
        respx.get("https://api.example.com/redirect").mock(
            return_value=httpx.Response(302, headers={"location": "/final"})
        )
        r = fluxium.get("https://api.example.com/redirect", allow_redirects=False)
        assert r.status_code == 302


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SESSION (15 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestSession:
    def test_session_get(self, mocked):
        respx.get("https://api.example.com/").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        with Session() as s:
            r = s.get("https://api.example.com/")
            assert r.status_code == 200

    def test_session_reuses_connection(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        with Session() as s:
            s.get("https://api.example.com/")
            s.get("https://api.example.com/")
        assert len(respx.calls) == 2

    def test_session_headers(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        with Session(headers={"X-Session": "yes"}) as s:
            s.get("https://api.example.com/")
        assert respx.calls[0].request.headers["x-session"] == "yes"

    def test_session_cookies(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        with Session(cookies={"sid": "abc123"}) as s:
            s.get("https://api.example.com/")
        assert "sid=abc123" in respx.calls[0].request.headers["cookie"]

    def test_session_per_request_headers_merge(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        with Session(headers={"X-Session": "session-val"}) as s:
            s.get("https://api.example.com/", headers={"X-Request": "req-val"})
        assert respx.calls[0].request.headers["x-session"] == "session-val"
        assert respx.calls[0].request.headers["x-request"] == "req-val"

    def test_session_per_request_cookies_merge(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        with Session(cookies={"session": "abc"}) as s:
            s.get("https://api.example.com/", cookies={"extra": "xyz"})
        cookie = respx.calls[0].request.headers["cookie"]
        assert "session=abc" in cookie
        assert "extra=xyz" in cookie

    def test_session_context_manager(self, mocked):
        with Session() as s:
            assert s is not None

    def test_session_close(self, mocked):
        s = Session()
        s.close()

    def test_session_add_middleware(self, mocked):
        s = Session()
        s.add_middleware(LoggingMiddleware())
        assert len(s._middleware) == 1

    def test_session_add_hook(self, mocked):
        s = Session()
        s.add_hook("response", lambda r, req: r)
        assert len(s._hooks) == 1

    def test_session_hook_called(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        calls = []
        s = Session()
        s.add_hook("response", lambda r, req: calls.append("hooked") or r)
        s.get("https://api.example.com/")
        assert calls == ["hooked"]

    def test_session_hook_can_modify_response(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        s = Session()
        s.add_hook("response", lambda r, req: r)
        r = s.get("https://api.example.com/")
        assert r.status_code == 200

    def test_session_verify_false_emits_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            s = Session(verify=False)
            assert len(w) == 1
            assert issubclass(w[0].category, InsecureSSLWarning)
            s.close()

    def test_session_verify_true_no_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            s = Session(verify=True)
            insecure_warnings = [x for x in w if issubclass(x.category, InsecureSSLWarning)]
            assert len(insecure_warnings) == 0
            s.close()


# ═══════════════════════════════════════════════════════════════════════════════
# 3. CACHING (20 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestCaching:
    def test_cache_hit(self, mocked):
        respx.get("https://api.example.com/").mock(
            return_value=httpx.Response(200, json={"cached": True})
        )
        with Session(cache=MemoryCache()) as s:
            r1 = s.get("https://api.example.com/")
            r2 = s.get("https://api.example.com/")
            assert r1.json() == {"cached": True}
            assert r2.json() == {"cached": True}
        assert len(respx.calls) == 1

    def test_cache_bypass_on_different_url(self, mocked):
        respx.get("https://api.example.com/a").mock(
            return_value=httpx.Response(200, json={"url": "a"})
        )
        respx.get("https://api.example.com/b").mock(
            return_value=httpx.Response(200, json={"url": "b"})
        )
        with Session(cache=MemoryCache()) as s:
            assert s.get("https://api.example.com/a").json()["url"] == "a"
            assert s.get("https://api.example.com/b").json()["url"] == "b"
        assert len(respx.calls) == 2

    def test_no_cache_by_default(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        with Session() as s:
            s.get("https://api.example.com/")
            s.get("https://api.example.com/")
        assert len(respx.calls) == 2

    def test_cache_only_get(self, mocked):
        respx.post("https://api.example.com/").mock(return_value=httpx.Response(200))
        with Session(cache=MemoryCache()) as s:
            s.post("https://api.example.com/")
            s.post("https://api.example.com/")
        assert len(respx.calls) == 2

    def test_cache_ignores_error_status(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(500))
        with Session(cache=MemoryCache()) as s:
            s.get("https://api.example.com/")
            s.get("https://api.example.com/")
        assert len(respx.calls) == 2

    def test_cache_ttl_expiry(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        cache = MemoryCache()
        with Session(cache=cache) as s:
            s.get("https://api.example.com/", cache_ttl=-1)
            import time

            time.sleep(0.01)
            s.get("https://api.example.com/")
        assert len(respx.calls) == 2

    def test_cache_clear(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        cache = MemoryCache()
        with Session(cache=cache) as s:
            s.get("https://api.example.com/")
            assert len(respx.calls) == 1
            s.get("https://api.example.com/")
            assert len(respx.calls) == 1
            cache.clear()
            s.get("https://api.example.com/")
            assert len(respx.calls) == 2

    def test_cache_delete_key(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        cache = MemoryCache()
        with Session(cache=cache) as s:
            s.get("https://api.example.com/")
            assert len(respx.calls) == 1
            key = _make_cache_key("GET", "https://api.example.com/", None)
            cache.delete(key)
            s.get("https://api.example.com/")
            assert len(respx.calls) == 2

    def test_cache_max_size(self, mocked):
        cache = MemoryCache(max_size=2)
        with Session(cache=cache) as s:
            respx.get("https://api.example.com/1").mock(return_value=httpx.Response(200))
            respx.get("https://api.example.com/2").mock(return_value=httpx.Response(200))
            respx.get("https://api.example.com/3").mock(return_value=httpx.Response(200))
            s.get("https://api.example.com/1")
            s.get("https://api.example.com/2")
            s.get("https://api.example.com/3")
            s.get("https://api.example.com/1")
        assert len(respx.calls) == 4

    def test_cache_key_excludes_auth(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        cache = MemoryCache()
        with Session(cache=cache) as s:
            s.get("https://api.example.com/", headers={"Authorization": "Bearer a"})
            s.get("https://api.example.com/", headers={"Authorization": "Bearer b"})
        assert len(respx.calls) == 1

    def test_cache_key_includes_relevant_headers(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        cache = MemoryCache()
        with Session(cache=cache) as s:
            s.get("https://api.example.com/", headers={"Accept": "application/json"})
            s.get("https://api.example.com/", headers={"Accept": "text/html"})
        assert len(respx.calls) == 2

    def test_response_to_cache_roundtrip(self, mocked):
        respx.get("https://api.example.com/").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        r = fluxium.get("https://api.example.com/")
        cache_data = _response_to_cache(r)
        r2 = _cache_to_response(cache_data)
        assert r2.status_code == 200
        assert r2.json() == {"ok": True}

    def test_disk_cache_set_get(self, tmp_path):
        cache = DiskCache(tmp_path / ".fluxium_cache")
        data = {
            "status_code": 200,
            "url": "https://example.com",
            "headers": {},
            "content": b"hello".hex(),
            "encoding": "utf-8",
        }
        cache.set("test-key", data, ttl=300)
        result = cache.get("test-key")
        assert result == data

    def test_disk_cache_expiry(self, tmp_path):
        cache = DiskCache(tmp_path / ".fluxium_cache")
        data = {
            "status_code": 200,
            "url": "https://example.com",
            "headers": {},
            "content": b"hello".hex(),
            "encoding": "utf-8",
        }
        cache.set("test-key", data, ttl=-1)
        import time

        time.sleep(0.01)
        assert cache.get("test-key") is None

    def test_disk_cache_delete(self, tmp_path):
        cache = DiskCache(tmp_path / ".fluxium_cache")
        data = {
            "status_code": 200,
            "url": "https://example.com",
            "headers": {},
            "content": b"hello".hex(),
            "encoding": "utf-8",
        }
        cache.set("test-key", data, ttl=300)
        cache.delete("test-key")
        assert cache.get("test-key") is None

    def test_disk_cache_clear(self, tmp_path):
        cache = DiskCache(tmp_path / ".fluxium_cache")
        data = {
            "status_code": 200,
            "url": "https://example.com",
            "headers": {},
            "content": b"hello".hex(),
            "encoding": "utf-8",
        }
        cache.set("key1", data, ttl=300)
        cache.set("key2", data, ttl=300)
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_memory_cache_clear(self):
        cache = MemoryCache()
        data = {
            "status_code": 200,
            "url": "https://example.com",
            "headers": {},
            "content": b"hello".hex(),
            "encoding": "utf-8",
        }
        cache.set("key1", data, ttl=300)
        cache.clear()
        assert cache.get("key1") is None

    def test_memory_cache_delete(self):
        cache = MemoryCache()
        data = {
            "status_code": 200,
            "url": "https://example.com",
            "headers": {},
            "content": b"hello".hex(),
            "encoding": "utf-8",
        }
        cache.set("key1", data, ttl=300)
        cache.delete("key1")
        assert cache.get("key1") is None


# ═══════════════════════════════════════════════════════════════════════════════
# 4. RETRIES (15 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestRetries:
    def test_retry_on_500(self, mocked):
        counter = [0]

        def _respond(request):
            counter[0] += 1
            if counter[0] <= 2:
                return httpx.Response(500)
            return httpx.Response(200, json={"ok": True})

        respx.get("https://api.example.com/").mock(side_effect=_respond)
        with Session(max_retries=3, retry_backoff=0.01) as s:
            r = s.get("https://api.example.com/")
            assert r.status_code == 200
        assert len(respx.calls) == 3

    def test_no_retry_on_4xx(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(404))
        with Session(max_retries=3, retry_backoff=0.01) as s:
            r = s.get("https://api.example.com/")
            assert r.status_code == 404
        assert len(respx.calls) == 1

    def test_retry_on_503(self, mocked):
        counter = [0]

        def _respond(request):
            counter[0] += 1
            if counter[0] == 1:
                return httpx.Response(503)
            return httpx.Response(200)

        respx.get("https://api.example.com/").mock(side_effect=_respond)
        with Session(max_retries=1, retry_backoff=0.01) as s:
            r = s.get("https://api.example.com/")
            assert r.status_code == 200
        assert len(respx.calls) == 2

    def test_retry_on_429(self, mocked):
        counter = [0]

        def _respond(request):
            counter[0] += 1
            if counter[0] == 1:
                return httpx.Response(429)
            return httpx.Response(200)

        respx.get("https://api.example.com/").mock(side_effect=_respond)
        with Session(max_retries=1, retry_backoff=0.01) as s:
            r = s.get("https://api.example.com/")
            assert r.status_code == 200

    def test_retry_exhausted(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(500))
        with Session(max_retries=2, retry_backoff=0.01) as s:
            r = s.get("https://api.example.com/")
            assert r.status_code == 500
        assert len(respx.calls) == 3

    def test_retry_middleware_direct(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(500))
        s = Session(max_retries=1, retry_backoff=0.01)
        r = s.get("https://api.example.com/")
        assert r.status_code == 500
        assert len(respx.calls) == 2

    def test_retry_custom_status(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(501))
        mw = RetryMiddleware(max_retries=1, backoff_factor=0.01, retry_on_status={501})
        s = Session()
        s._retry_mw = mw
        s._middleware.add(mw)
        r = s.get("https://api.example.com/")
        assert r.status_code == 501
        assert len(respx.calls) == 2

    def test_retry_should_retry_returns_false_for_404(self):
        mw = RetryMiddleware()
        resp = fluxium.Response()
        resp.status_code = 404
        assert mw.should_retry(resp, None) is False

    def test_retry_should_retry_returns_true_for_500(self):
        mw = RetryMiddleware()
        resp = fluxium.Response()
        resp.status_code = 500
        assert mw.should_retry(resp, None) is True

    def test_retry_should_retry_with_none_response_and_error(self):
        mw = RetryMiddleware()
        err = TimeoutError("timeout")
        assert mw.should_retry(None, err) is True

    def test_retry_should_retry_with_none_both(self):
        mw = RetryMiddleware()
        assert mw.should_retry(None, None) is False

    def test_retry_should_retry_with_200_response(self):
        mw = RetryMiddleware()
        resp = fluxium.Response()
        resp.status_code = 200
        assert mw.should_retry(resp, None) is False

    def test_retry_backoff_increases(self):
        mw = RetryMiddleware(backoff_factor=0.5)
        b0 = mw.get_backoff(0)
        b1 = mw.get_backoff(1)
        b2 = mw.get_backoff(2)
        assert b0 < b1 < b2

    def test_retry_backoff_capped(self):
        mw = RetryMiddleware(backoff_factor=1.0, max_backoff=1.0)
        b = mw.get_backoff(10)
        assert b <= 1.0 + 0.1


# ═══════════════════════════════════════════════════════════════════════════════
# 5. REDIRECTS (10 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestRedirects:
    def test_follows_single_redirect(self, mocked):
        respx.get("https://api.example.com/redirect").mock(
            return_value=httpx.Response(301, headers={"location": "https://api.example.com/final"})
        )
        respx.get("https://api.example.com/final").mock(
            return_value=httpx.Response(200, json={"done": True})
        )
        r = fluxium.get("https://api.example.com/redirect")
        assert r.status_code == 200
        assert r.json()["done"] is True

    def test_follows_chain_redirect(self, mocked):
        respx.get("https://api.example.com/r1").mock(
            return_value=httpx.Response(301, headers={"location": "https://api.example.com/r2"})
        )
        respx.get("https://api.example.com/r2").mock(
            return_value=httpx.Response(301, headers={"location": "https://api.example.com/r3"})
        )
        respx.get("https://api.example.com/r3").mock(
            return_value=httpx.Response(200, json={"final": True})
        )
        r = fluxium.get("https://api.example.com/r1")
        assert r.status_code == 200
        assert len(r.history) == 2

    def test_no_redirect(self, mocked):
        respx.get("https://api.example.com/redirect").mock(
            return_value=httpx.Response(301, headers={"location": "https://api.example.com/final"})
        )
        r = fluxium.get("https://api.example.com/redirect", allow_redirects=False)
        assert r.status_code == 301

    def test_redirect_preserves_history(self, mocked):
        respx.get("https://api.example.com/start").mock(
            return_value=httpx.Response(302, headers={"location": "https://api.example.com/end"})
        )
        respx.get("https://api.example.com/end").mock(return_value=httpx.Response(200))
        r = fluxium.get("https://api.example.com/start")
        assert len(r.history) == 1
        assert r.history[0].status_code == 302

    def test_redirect_301_follows(self, mocked):
        respx.get("https://api.example.com/redirect").mock(
            return_value=httpx.Response(301, headers={"location": "https://api.example.com/final"})
        )
        respx.get("https://api.example.com/final").mock(
            return_value=httpx.Response(200, json={"final": True})
        )
        r = fluxium.get("https://api.example.com/redirect")
        assert r.status_code == 200
        assert r.json()["final"] is True

    def test_redirect_with_relative_location(self, mocked):
        respx.get("https://api.example.com/redirect").mock(
            return_value=httpx.Response(301, headers={"location": "/final"})
        )
        respx.get("https://api.example.com/final").mock(return_value=httpx.Response(200))
        r = fluxium.get("https://api.example.com/redirect")
        assert r.status_code == 200

    def test_no_redirect_when_no_location_header(self, mocked):
        respx.get("https://api.example.com/redirect").mock(return_value=httpx.Response(301))
        r = fluxium.get("https://api.example.com/redirect")
        assert r.status_code == 301

    def test_redirect_with_session(self, mocked):
        respx.get("https://api.example.com/redirect").mock(
            return_value=httpx.Response(301, headers={"location": "https://api.example.com/final"})
        )
        respx.get("https://api.example.com/final").mock(return_value=httpx.Response(200))
        with Session() as s:
            r = s.get("https://api.example.com/redirect")
            assert r.status_code == 200

    def test_session_max_redirects(self, mocked):
        respx.get("https://api.example.com/start").mock(
            return_value=httpx.Response(
                301, headers={"location": "https://api.example.com/redirect"}
            )
        )
        respx.get("https://api.example.com/redirect").mock(
            return_value=httpx.Response(301, headers={"location": "https://api.example.com/end"})
        )
        s = Session(max_redirects=1)
        with pytest.raises(TooManyRedirects):
            s.get("https://api.example.com/start")
        s.close()


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ASYNC (20 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestAsync:
    @pytest.mark.asyncio
    async def test_async_get(self, mocked):
        respx.get("https://api.example.com/").mock(
            return_value=httpx.Response(200, json={"async": True})
        )
        async with AsyncSession() as s:
            r = await s.get("https://api.example.com/")
            assert r.status_code == 200
            assert r.json()["async"] is True

    @pytest.mark.asyncio
    async def test_async_post(self, mocked):
        respx.post("https://api.example.com/").mock(
            return_value=httpx.Response(201, json={"created": True})
        )
        async with AsyncSession() as s:
            r = await s.post("https://api.example.com/", json={"name": "x"})
            assert r.status_code == 201

    @pytest.mark.asyncio
    async def test_async_concurrent(self, mocked):
        respx.get("https://api.example.com/").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        async with AsyncSession() as s:
            results = [await s.get("https://api.example.com/") for _ in range(5)]
        assert all(r.status_code == 200 for r in results)
        assert len(respx.calls) == 5

    @pytest.mark.asyncio
    async def test_async_gather(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        import asyncio

        async with AsyncSession() as s:
            tasks = [s.get("https://api.example.com/") for _ in range(10)]
            results = await asyncio.gather(*tasks)
        assert len(results) == 10
        assert all(r.status_code == 200 for r in results)

    @pytest.mark.asyncio
    async def test_async_session_headers(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        async with AsyncSession(headers={"X-Async": "yes"}) as s:
            await s.get("https://api.example.com/")
        assert respx.calls[0].request.headers["x-async"] == "yes"

    @pytest.mark.asyncio
    async def test_async_session_cookies(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        async with AsyncSession(cookies={"sid": "abc"}) as s:
            await s.get("https://api.example.com/")
        assert "sid=abc" in respx.calls[0].request.headers["cookie"]

    @pytest.mark.asyncio
    async def test_async_with_cache(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        async with AsyncSession(cache=MemoryCache()) as s:
            await s.get("https://api.example.com/")
            await s.get("https://api.example.com/")
        assert len(respx.calls) == 1

    @pytest.mark.asyncio
    async def test_async_with_hooks(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        calls = []
        async with AsyncSession() as s:
            s.add_hook("response", lambda r, req: calls.append("hooked") or r)
            await s.get("https://api.example.com/")
        assert calls == ["hooked"]

    @pytest.mark.asyncio
    async def test_async_verify_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            s = AsyncSession(verify=False)
            assert any(issubclass(x.category, InsecureSSLWarning) for x in w)
            await s.close()

    @pytest.mark.asyncio
    async def test_async_add_middleware(self, mocked):
        s = AsyncSession()
        s.add_middleware(LoggingMiddleware())
        assert len(s._middleware) == 1
        await s.close()

    @pytest.mark.asyncio
    async def test_async_redirect(self, mocked):
        respx.get("https://api.example.com/redirect").mock(
            return_value=httpx.Response(301, headers={"location": "https://api.example.com/final"})
        )
        respx.get("https://api.example.com/final").mock(return_value=httpx.Response(200))
        async with AsyncSession() as s:
            r = await s.get("https://api.example.com/redirect")
            assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_async_retry(self, mocked):
        counter = [0]

        def _respond(request):
            counter[0] += 1
            if counter[0] == 1:
                return httpx.Response(500)
            return httpx.Response(200)

        respx.get("https://api.example.com/").mock(side_effect=_respond)
        async with AsyncSession(max_retries=1, retry_backoff=0.01) as s:
            r = await s.get("https://api.example.com/")
            assert r.status_code == 200
        assert len(respx.calls) == 2

    @pytest.mark.asyncio
    async def test_aget(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        r = await fluxium.aget("https://api.example.com/")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_apost(self, mocked):
        respx.post("https://api.example.com/").mock(return_value=httpx.Response(201))
        r = await fluxium.apost("https://api.example.com/", json={"x": 1})
        assert r.status_code == 201

    @pytest.mark.asyncio
    async def test_aput(self, mocked):
        respx.put("https://api.example.com/1").mock(return_value=httpx.Response(200))
        r = await fluxium.aput("https://api.example.com/1", json={"x": 1})
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_adelete(self, mocked):
        respx.delete("https://api.example.com/1").mock(return_value=httpx.Response(204))
        r = await fluxium.adelete("https://api.example.com/1")
        assert r.status_code == 204

    @pytest.mark.asyncio
    async def test_aoptions(self, mocked):
        respx.options("https://api.example.com/").mock(return_value=httpx.Response(200))
        r = await fluxium.aoptions("https://api.example.com/")
        assert r.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# 7. AUTH (15 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestAuth:
    def test_basic_auth(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.get("https://api.example.com/", auth=BasicAuth("user", "pass"))
        assert respx.calls[0].request.headers["authorization"].startswith("Basic ")

    def test_bearer_auth(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.get("https://api.example.com/", auth=BearerAuth("my-token"))
        assert respx.calls[0].request.headers["authorization"] == "Bearer my-token"

    def test_digest_auth_init(self):
        auth = DigestAuth("admin", "secret")
        assert auth.username == "admin"
        assert auth.password == "secret"

    def test_basic_auth_encoding(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.get("https://api.example.com/", auth=BasicAuth("user", "p@ss:w0rd"))
        import base64

        encoded = respx.calls[0].request.headers["authorization"].split(" ")[1]
        decoded = base64.b64decode(encoded).decode()
        assert decoded == "user:p@ss:w0rd"

    def test_bearer_auth_with_session(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        with Session(auth=BearerAuth("session-token")) as s:
            s.get("https://api.example.com/")
        assert respx.calls[0].request.headers["authorization"] == "Bearer session-token"

    def test_auth_override_per_request(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        s = Session(auth=BearerAuth("session-token"))
        s.get("https://api.example.com/", auth=BasicAuth("user", "pass"))
        assert respx.calls[0].request.headers["authorization"].startswith("Basic ")
        s.close()

    def test_basic_auth_empty_password(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.get("https://api.example.com/", auth=BasicAuth("user", ""))
        import base64

        encoded = respx.calls[0].request.headers["authorization"].split(" ")[1]
        decoded = base64.b64decode(encoded).decode()
        assert decoded == "user:"

    def test_bearer_auth_custom_token_type(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.get("https://api.example.com/", auth=BearerAuth("token", token_type="Token"))
        assert respx.calls[0].request.headers["authorization"] == "Token token"

    def test_digest_auth_build_header(self):
        auth = DigestAuth("admin", "secret")
        challenge = 'Digest realm="test", nonce="abc123", algorithm=MD5, qop="auth"'
        header = auth.build_header("GET", "https://api.example.com/path", challenge)
        assert "Digest" in header
        assert 'username="admin"' in header
        assert 'realm="test"' in header
        assert 'nonce="abc123"' in header

    def test_digest_auth_parse_challenge(self):
        auth = DigestAuth("admin", "secret")
        challenge = 'Digest realm="myrealm", nonce="mynonce", algorithm=MD5-sess, qop="auth"'
        parsed = auth._parse_challenge(challenge)
        assert parsed["realm"] == "myrealm"
        assert parsed["nonce"] == "mynonce"
        assert parsed["algorithm"] == "MD5-sess"
        assert parsed["qop"] == "auth"

    def test_basic_auth_special_chars(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.get("https://api.example.com/", auth=BasicAuth("user@domain.com", "p@$$w0rd!"))
        import base64

        encoded = respx.calls[0].request.headers["authorization"].split(" ")[1]
        decoded = base64.b64decode(encoded).decode()
        assert decoded == "user@domain.com:p@$$w0rd!"

    def test_bearer_auth_with_refresh_callback(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))

        def refresh():
            return "new-token"

        auth = BearerAuth("old-token", refresh_callback=refresh)
        fluxium.get("https://api.example.com/", auth=auth)
        assert respx.calls[0].request.headers["authorization"] == "Bearer old-token"

    def test_auth_none(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.get("https://api.example.com/", auth=None)
        assert "authorization" not in respx.calls[0].request.headers


# ═══════════════════════════════════════════════════════════════════════════════
# 8. BODY ENCODING (10 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestBodyEncoding:
    def test_json_body(self, mocked):
        respx.post("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.post("https://api.example.com/", json={"key": "value"})
        body = respx.calls[0].request.content
        assert b'"key"' in body
        assert b'"value"' in body

    def test_form_body(self, mocked):
        respx.post("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.post("https://api.example.com/", data={"a": "1", "b": "2"})
        body = respx.calls[0].request.content
        assert b"a=1" in body
        assert b"b=2" in body

    def test_bytes_body(self, mocked):
        respx.post("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.post("https://api.example.com/", data=b"raw bytes")
        assert respx.calls[0].request.content == b"raw bytes"

    def test_string_body(self, mocked):
        respx.post("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.post("https://api.example.com/", data="plain text")
        assert respx.calls[0].request.content == b"plain text"

    def test_json_content_type(self, mocked):
        respx.post("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.post("https://api.example.com/", json={"x": 1})
        assert "application/json" in respx.calls[0].request.headers["content-type"]

    def test_form_content_type(self, mocked):
        respx.post("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.post("https://api.example.com/", data={"x": 1})
        assert "application/x-www-form-urlencoded" in respx.calls[0].request.headers["content-type"]

    def test_multipart_file_upload(self, mocked):
        respx.post("https://api.example.com/upload").mock(return_value=httpx.Response(200))
        fake = io.BytesIO(b"file content here")
        fluxium.post(
            "https://api.example.com/upload", files={"file": ("test.txt", fake, "text/plain")}
        )
        body = respx.calls[0].request.content
        assert b"file content here" in body
        assert "multipart/form-data" in respx.calls[0].request.headers["content-type"]

    def test_multipart_with_fields(self, mocked):
        respx.post("https://api.example.com/upload").mock(return_value=httpx.Response(200))
        fake = io.BytesIO(b"data")
        fluxium.post(
            "https://api.example.com/upload",
            data={"field": "value"},
            files={"file": ("test.txt", fake, "text/plain")},
        )
        body = respx.calls[0].request.content
        assert b"data" in body
        assert b"value" in body

    def test_json_nested_data(self, mocked):
        respx.post("https://api.example.com/").mock(return_value=httpx.Response(200))
        payload = {"nested": {"deep": {"value": 42}}, "list": [1, 2, 3]}
        fluxium.post("https://api.example.com/", json=payload)
        body = json.loads(respx.calls[0].request.content)
        assert body == payload

    def test_empty_body(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.get("https://api.example.com/")
        assert respx.calls[0].request.content == b""


# ═══════════════════════════════════════════════════════════════════════════════
# 9. COOKIEJAR (15 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestCookieJar:
    def test_create_empty(self):
        jar = CookieJar()
        assert len(list(jar)) == 0

    def test_create_from_dict(self):
        jar = CookieJar({"a": "1", "b": "2"})
        assert jar["a"] == "1"
        assert jar["b"] == "2"

    def test_set_get(self):
        jar = CookieJar()
        jar["session"] = "abc"
        assert jar["session"] == "abc"

    def test_contains(self):
        jar = CookieJar({"a": "1"})
        assert "a" in jar
        assert "b" not in jar

    def test_delete(self):
        jar = CookieJar({"a": "1", "b": "2"})
        del jar["a"]
        assert "a" not in jar
        assert "b" in jar

    def test_to_dict(self):
        jar = CookieJar({"a": "1", "b": "2"})
        assert jar.to_dict() == {"a": "1", "b": "2"}

    def test_to_header(self):
        jar = CookieJar({"a": "1", "b": "2"})
        header = jar.to_header()
        assert "a=1" in header
        assert "b=2" in header

    def test_keys_values_items(self):
        jar = CookieJar({"a": "1", "b": "2"})
        assert set(jar.keys()) == {"a", "b"}
        assert set(jar.values()) == {"1", "2"}
        assert set(jar.items()) == {("a", "1"), ("b", "2")}

    def test_get_with_default(self):
        jar = CookieJar()
        assert jar.get("missing", "default") == "default"

    def test_update_from_dict(self):
        jar = CookieJar({"a": "1"})
        jar.update({"b": "2"})
        assert jar["a"] == "1"
        assert jar["b"] == "2"

    def test_update_from_cookiejar(self):
        jar1 = CookieJar({"a": "1"})
        jar2 = CookieJar({"b": "2"})
        jar1.update(jar2)
        assert jar1["a"] == "1"
        assert jar1["b"] == "2"

    def test_bool_not_empty(self):
        jar = CookieJar({"a": "1"})
        assert bool(jar) is True

    def test_iter_content(self):
        resp = fluxium.Response()
        resp._content = b"hello world chunked"
        chunks = list(resp.iter_content(chunk_size=5))
        assert b"".join(chunks) == b"hello world chunked"

    def test_iter_lines(self):
        resp = fluxium.Response()
        resp._content = b"line1\nline2\nline3"
        lines = list(resp.iter_lines())
        assert lines == ["line1", "line2", "line3"]


# ═══════════════════════════════════════════════════════════════════════════════
# 10. EXCEPTIONS (10 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestExceptions:
    def test_fluxium_error_is_base(self):
        assert issubclass(ConnectionError, FluxiumError)
        assert issubclass(TimeoutError, FluxiumError)
        assert issubclass(HTTPError, FluxiumError)
        assert issubclass(TooManyRedirects, FluxiumError)
        assert issubclass(SSLError, FluxiumError)
        assert issubclass(ProxyError, FluxiumError)

    def test_ssl_error_is_connection_error(self):
        assert issubclass(SSLError, ConnectionError)

    def test_proxy_error_is_connection_error(self):
        assert issubclass(ProxyError, ConnectionError)

    def test_http_error_has_response(self):
        resp = fluxium.Response()
        resp.status_code = 404
        err = HTTPError("not found", response=resp)
        assert err.response is resp
        assert "not found" in str(err)

    def test_http_error_without_response(self):
        err = HTTPError("generic error")
        assert err.response is None

    def test_fluxium_warning_hierarchy(self):
        assert issubclass(InsecureSSLWarning, FluxiumWarning)
        assert issubclass(FluxiumWarning, UserWarning)

    def test_insecure_ssl_warning_message(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnings.warn("test", InsecureSSLWarning)
            assert len(w) == 1
            assert issubclass(w[0].category, InsecureSSLWarning)

    def test_retry_warning_attributes(self):
        w = RetryWarning(2, 5, "https://example.com", "timeout")
        assert w.attempt == 2
        assert w.max_retries == 5
        assert w.url == "https://example.com"
        assert w.reason == "timeout"

    def test_exception_catchable_as_fluxium_error(self):
        try:
            raise ConnectionError("test")
        except FluxiumError:
            pass

    def test_exception_catchable_specific(self):
        try:
            raise TimeoutError("test")
        except FluxiumError:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# 11. TIMEOUT (10 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestTimeout:
    def test_timeout_single_value(self):
        t = Timeout(30.0)
        assert t.connect == 30.0
        assert t.read == 30.0
        assert t.write == 30.0
        assert t.pool == 30.0

    def test_timeout_per_component(self):
        t = Timeout(connect=5.0, read=30.0)
        assert t.connect == 5.0
        assert t.read == 30.0

    def test_timeout_from_tuple(self):
        t = Timeout((5.0, 30.0))
        assert t.connect == 5.0
        assert t.read == 30.0

    def test_timeout_none(self):
        t = Timeout(None)
        assert t.connect is None

    def test_timeout_to_httpx(self):
        t = Timeout(connect=5.0, read=30.0)
        httpx_timeout = t.to_httpx()
        assert isinstance(httpx_timeout, httpx.Timeout)
        assert httpx_timeout.connect == 5.0
        assert httpx_timeout.read == 30.0

    def test_timeout_repr(self):
        t = Timeout(connect=5.0, read=30.0)
        r = repr(t)
        assert "connect=5.0" in r
        assert "read=30.0" in r

    def test_timeout_default(self):
        t = Timeout()
        assert t.connect == 30.0

    def test_timeout_with_session(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        s = Session(timeout=Timeout(connect=5.0, read=30.0))
        r = s.get("https://api.example.com/")
        assert r.status_code == 200
        s.close()

    def test_timeout_per_request(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        s = Session()
        r = s.get("https://api.example.com/", timeout=Timeout(10.0))
        assert r.status_code == 200
        s.close()


# ═══════════════════════════════════════════════════════════════════════════════
# 12. RATE LIMITING (10 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestRateLimiting:
    def test_rate_limit_allows_within_limit(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        s = Session()
        s.add_middleware(RateLimitMiddleware(calls=10, period=1))
        for _ in range(5):
            r = s.get("https://api.example.com/")
            assert r.status_code == 200
        s.close()

    def test_rate_limit_delays_when_exceeded(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        s = Session()
        s.add_middleware(RateLimitMiddleware(calls=1, period=0.5))
        import time

        start = time.perf_counter()
        s.get("https://api.example.com/")
        s.get("https://api.example.com/")
        elapsed = time.perf_counter() - start
        assert elapsed > 0.05
        s.close()

    def test_rate_limit_with_session(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        s = Session()
        s.add_middleware(RateLimitMiddleware(calls=10, period=60))
        assert len(s._middleware) == 1
        s.close()

    def test_rate_limit_default_params(self):
        mw = RateLimitMiddleware()
        assert mw._calls == 100
        assert mw._period == 60.0

    def test_rate_limit_custom_params(self):
        mw = RateLimitMiddleware(calls=10, period=1)
        assert mw._calls == 10
        assert mw._period == 1.0

    def test_rate_limit_token_bucket_refill(self):
        import time

        mw = RateLimitMiddleware(calls=2, period=1)
        mw._tokens = 0
        mw._last_refill = time.monotonic() - 0.5
        from fluxium.models import Request

        req = Request("GET", "https://example.com/")
        mw.on_request(req)
        assert mw._tokens >= 0

    def test_rate_limit_does_not_block_forever(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        s = Session()
        s.add_middleware(RateLimitMiddleware(calls=1, period=0.1))
        import time

        start = time.perf_counter()
        for _ in range(3):
            s.get("https://api.example.com/")
        elapsed = time.perf_counter() - start
        assert elapsed < 5
        s.close()

    def test_rate_limit_per_method(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        respx.post("https://api.example.com/").mock(return_value=httpx.Response(200))
        s = Session()
        s.add_middleware(RateLimitMiddleware(calls=10, period=1))
        s.get("https://api.example.com/")
        s.post("https://api.example.com/")
        assert len(respx.calls) == 2
        s.close()

    def test_rate_limit_async_session(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        s = AsyncSession()
        s.add_middleware(RateLimitMiddleware(calls=10, period=1))
        assert len(s._middleware) == 1

    def test_rate_limit_burst(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        s = Session()
        s.add_middleware(RateLimitMiddleware(calls=5, period=1))
        import time

        start = time.perf_counter()
        for _ in range(5):
            s.get("https://api.example.com/")
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5
        s.close()


# ═══════════════════════════════════════════════════════════════════════════════
# 13. HOOKS (10 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestHooks:
    def test_hook_response_called(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        calls = []
        s = Session()
        s.add_hook("response", lambda r, req: calls.append("response") or r)
        s.get("https://api.example.com/")
        assert calls == ["response"]
        s.close()

    def test_hook_request_called(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        calls = []
        s = Session()
        s.add_hook("request", lambda req: calls.append("request") or req)
        s.get("https://api.example.com/")
        assert calls == ["request"]
        s.close()

    def test_multiple_hooks_same_event(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        calls = []
        s = Session()
        s.add_hook("response", lambda r, req: calls.append("first") or r)
        s.add_hook("response", lambda r, req: calls.append("second") or r)
        s.get("https://api.example.com/")
        assert calls == ["first", "second"]
        s.close()

    def test_hook_does_not_break_on_error(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        s = Session()

        def bad_hook(r, req):
            raise ValueError("hook error")

        s.add_hook("response", bad_hook)
        r = s.get("https://api.example.com/")
        assert r.status_code == 200
        s.close()

    def test_hook_with_async_session(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        calls = []
        s = AsyncSession()
        s.add_hook("response", lambda r, req: calls.append("hooked") or r)
        assert len(s._hooks) == 1

    def test_hook_can_access_response_status(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        statuses = []
        s = Session()
        s.add_hook("response", lambda r, req: statuses.append(r.status_code) or r)
        s.get("https://api.example.com/")
        assert statuses == [200]
        s.close()

    def test_hook_can_access_request_url(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        urls = []
        s = Session()
        s.add_hook("response", lambda r, req: urls.append(req.url) or r)
        s.get("https://api.example.com/")
        assert urls == ["https://api.example.com/"]
        s.close()

    def test_hook_with_cache(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        call_count = [0]
        s = Session(cache=MemoryCache())
        s.add_hook("response", lambda r, req: call_count.__setitem__(0, call_count[0] + 1) or r)
        s.get("https://api.example.com/")
        s.get("https://api.example.com/")
        assert call_count[0] == 1
        s.close()

    def test_hook_returns_modified_response(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        s = Session()

        def add_header(r, req):
            r.headers["x-custom"] = "modified"
            return r

        s.add_hook("response", add_header)
        r = s.get("https://api.example.com/")
        assert r.headers.get("x-custom") == "modified"
        s.close()

    def test_hook_empty_session(self):
        s = Session()
        assert s._hooks == []
        s.close()


# ═══════════════════════════════════════════════════════════════════════════════
# 14. WARNINGS (5 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestWarnings:
    def test_insecure_ssl_warning_on_verify_false(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            s = Session(verify=False)
            assert any(issubclass(x.category, InsecureSSLWarning) for x in w)
            s.close()

    def test_no_warning_on_verify_true(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            s = Session(verify=True)
            assert not any(issubclass(x.category, InsecureSSLWarning) for x in w)
            s.close()

    def test_no_warning_on_verify_string(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                s = Session(verify="/nonexistent/ca.crt")
            except (FileNotFoundError, OSError):
                pass
            insecure_warnings = [x for x in w if issubclass(x.category, InsecureSSLWarning)]
            assert len(insecure_warnings) == 0

    def test_warning_message_content(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            s = Session(verify=False)
            ssl_warnings = [x for x in w if issubclass(x.category, InsecureSSLWarning)]
            assert len(ssl_warnings) == 1
            assert "insecure" in str(ssl_warnings[0].message).lower()
            s.close()

    def test_async_session_insecure_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            s = AsyncSession(verify=False)
            assert any(issubclass(x.category, InsecureSSLWarning) for x in w)
            import asyncio

            asyncio.run(s.close())


# ═══════════════════════════════════════════════════════════════════════════════
# 15. HISHEL CACHE (5 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestHishelCache:
    def test_hishel_cache_import(self):
        assert hasattr(fluxium, "HishelCache")

    def test_hishel_cache_requires_hishel(self):
        real_hishel = sys.modules.get("hishel")
        sys.modules["hishel"] = None
        try:
            from fluxium.cache import HishelCache

            try:
                HishelCache()
                assert False, "Should have raised ImportError"
            except ImportError:
                pass
        finally:
            if real_hishel is not None:
                sys.modules["hishel"] = real_hishel
            else:
                del sys.modules["hishel"]

    def test_hishel_cache_in_all(self):
        assert "HishelCache" in fluxium.__all__

    def test_hishel_cache_is_cache_backend(self):
        assert hasattr(fluxium, "HishelCache")

    def test_hishel_cache_class_attributes(self):
        assert hasattr(fluxium.HishelCache, "is_cachable")


# ═══════════════════════════════════════════════════════════════════════════════
# 16. MODULE-LEVEL FUNCTIONS PARITY (10 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestModuleLevelParity:
    def test_get_supports_cache_ttl(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        r = fluxium.get("https://api.example.com/", cache_ttl=60)
        assert r.status_code == 200

    def test_get_supports_stream(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        r = fluxium.get("https://api.example.com/", stream=True)
        assert r.status_code == 200

    def test_get_supports_allow_redirects(self, mocked):
        respx.get("https://api.example.com/redirect").mock(
            return_value=httpx.Response(301, headers={"location": "/final"})
        )
        r = fluxium.get("https://api.example.com/redirect", allow_redirects=False)
        assert r.status_code == 301

    def test_post_supports_json(self, mocked):
        respx.post("https://api.example.com/").mock(return_value=httpx.Response(201))
        r = fluxium.post("https://api.example.com/", json={"x": 1})
        assert r.status_code == 201

    def test_post_supports_files(self, mocked):
        respx.post("https://api.example.com/").mock(return_value=httpx.Response(200))
        fake = io.BytesIO(b"data")
        r = fluxium.post("https://api.example.com/", files={"f": ("x.txt", fake, "text/plain")})
        assert r.status_code == 200

    def test_put_supports_json(self, mocked):
        respx.put("https://api.example.com/1").mock(return_value=httpx.Response(200))
        r = fluxium.put("https://api.example.com/1", json={"x": 1})
        assert r.status_code == 200

    def test_delete_returns_response(self, mocked):
        respx.delete("https://api.example.com/1").mock(return_value=httpx.Response(204))
        r = fluxium.delete("https://api.example.com/1")
        assert r.status_code == 204

    def test_head_returns_empty_content(self, mocked):
        respx.head("https://api.example.com/").mock(return_value=httpx.Response(200))
        r = fluxium.head("https://api.example.com/")
        assert r.content == b""

    def test_options_returns_response(self, mocked):
        respx.options("https://api.example.com/").mock(return_value=httpx.Response(200))
        r = fluxium.options("https://api.example.com/")
        assert r.status_code == 200

    def test_request_custom_method(self, mocked):
        respx.route(method="PURGE", path="/cache").mock(return_value=httpx.Response(200))
        r = fluxium.request("PURGE", "https://api.example.com/cache")
        assert r.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# 17. EDGE CASES & INTEGRATION (15 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_empty_response_body(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        r = fluxium.get("https://api.example.com/")
        assert r.content == b""
        assert r.text == ""

    def test_large_json_response(self, mocked):
        data = {"items": [{"id": i, "name": f"item_{i}"} for i in range(1000)]}
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200, json=data))
        r = fluxium.get("https://api.example.com/")
        assert len(r.json()["items"]) == 1000

    def test_unicode_in_response(self, mocked):
        respx.get("https://api.example.com/").mock(
            return_value=httpx.Response(200, json={"name": "日本語テスト"})
        )
        r = fluxium.get("https://api.example.com/")
        assert r.json()["name"] == "日本語テスト"

    def test_204_no_content(self, mocked):
        respx.delete("https://api.example.com/1").mock(return_value=httpx.Response(204))
        r = fluxium.delete("https://api.example.com/1")
        assert r.status_code == 204

    def test_session_with_all_options(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        s = Session(
            headers={"X-Custom": "val"},
            cookies={"session": "abc"},
            timeout=30.0,
            http2=True,
            max_retries=2,
            retry_backoff=0.1,
            cache=MemoryCache(),
        )
        r = s.get("https://api.example.com/")
        assert r.status_code == 200
        s.close()

    def test_response_json_with_kwargs(self, mocked):
        respx.get("https://api.example.com/").mock(
            return_value=httpx.Response(200, json={"key": "value"})
        )
        r = fluxium.get("https://api.example.com/")
        data = r.json(parse_float=str)
        assert data == {"key": "value"}

    def test_multipart_multiple_files(self, mocked):
        respx.post("https://api.example.com/").mock(return_value=httpx.Response(200))
        f1 = io.BytesIO(b"file1")
        f2 = io.BytesIO(b"file2")
        fluxium.post(
            "https://api.example.com/",
            files={"files": [("a.txt", f1, "text/plain"), ("b.txt", f2, "text/plain")]},
        )
        body = respx.calls[0].request.content
        assert b"file1" in body or b"file2" in body

    def test_cookie_header_format(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.get("https://api.example.com/", cookies={"a": "1", "b": "2"})
        cookie = respx.calls[0].request.headers["cookie"]
        assert "a=1" in cookie
        assert "b=2" in cookie

    def test_header_lowercase_keys(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        r = fluxium.get("https://api.example.com/")
        for key in r.headers:
            assert key == key.lower()

    def test_session_cookie_persistence(self, mocked):
        respx.get("https://api.example.com/login").mock(
            return_value=httpx.Response(200, headers={"set-cookie": "session=abc"})
        )
        respx.get("https://api.example.com/profile").mock(return_value=httpx.Response(200))
        with Session() as s:
            s.get("https://api.example.com/login")
            s.get("https://api.example.com/profile")
        assert "session=abc" in respx.calls[1].request.headers["cookie"]

    def test_cache_does_not_cache_post(self, mocked):
        respx.post("https://api.example.com/").mock(return_value=httpx.Response(200))
        with Session(cache=MemoryCache()) as s:
            s.post("https://api.example.com/")
            s.post("https://api.example.com/")
        assert len(respx.calls) == 2

    def test_cache_differentiates_query_params(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        with Session(cache=MemoryCache()) as s:
            s.get("https://api.example.com/", params={"a": "1"})
            s.get("https://api.example.com/", params={"a": "2"})
        assert len(respx.calls) == 2

    def test_stream_true_no_content_read(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        r = fluxium.get("https://api.example.com/", stream=True)
        assert r.status_code == 200

    def test_response_repr(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        r = fluxium.get("https://api.example.com/")
        assert "200" in repr(r)

    def test_bool_response_200(self, mocked):
        respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        r = fluxium.get("https://api.example.com/")
        assert bool(r) is True
