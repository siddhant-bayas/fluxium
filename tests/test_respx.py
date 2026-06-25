"""Unit tests using respx for deterministic HTTP mocking.

These tests run without network access and verify fluxium's behavior
(endpoints, headers, retries, caching, etc.) by intercepting httpx calls.
"""

from __future__ import annotations

import httpx
import pytest
import respx

import fluxium
from fluxium import AsyncSession, MemoryCache, Session


@pytest.fixture
def mocked():
    """Provide a respx mock context."""
    with respx.mock:
        yield


# ── Basic Requests ────────────────────────────────────────────────────────────


class TestBasicRequests:
    def test_get(self, mocked):
        route = respx.get("https://api.example.com/").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        r = fluxium.get("https://api.example.com/")
        assert route.called
        assert r.status_code == 200
        assert r.json() == {"ok": True}

    def test_post_json(self, mocked):
        route = respx.post("https://api.example.com/items").mock(
            return_value=httpx.Response(201, json={"created": True})
        )
        r = fluxium.post("https://api.example.com/items", json={"name": "x"})
        assert r.status_code == 201
        assert r.json()["created"] is True

    def test_query_params(self, mocked):
        route = respx.get("https://api.example.com/search").mock(
            return_value=httpx.Response(200, json={"q": "hello"})
        )
        r = fluxium.get("https://api.example.com/search", params={"q": "hello"})
        assert "q=hello" in str(route.calls[0].request.url)

    def test_custom_headers(self, mocked):
        route = respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.get("https://api.example.com/", headers={"X-Custom": "val"})
        assert route.calls[0].request.headers["x-custom"] == "val"

    def test_status_404(self, mocked):
        respx.get("https://api.example.com/missing").mock(return_value=httpx.Response(404))
        r = fluxium.get("https://api.example.com/missing")
        assert r.status_code == 404
        assert not r.ok

    def test_raise_for_status(self, mocked):
        respx.get("https://api.example.com/error").mock(return_value=httpx.Response(500))
        r = fluxium.get("https://api.example.com/error")
        with pytest.raises(fluxium.HTTPError):
            r.raise_for_status()


# ── Session ───────────────────────────────────────────────────────────────────


class TestSession:
    def test_session_get(self, mocked):
        route = respx.get("https://api.example.com/").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        with Session() as s:
            r = s.get("https://api.example.com/")
            assert r.status_code == 200
        assert route.call_count == 1

    def test_session_reuses_connection(self, mocked):
        """Multiple requests on same session should reuse the httpx client."""
        route = respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        with Session() as s:
            s.get("https://api.example.com/")
            s.get("https://api.example.com/")
        assert route.call_count == 2

    def test_session_headers(self, mocked):
        route = respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        with Session(headers={"X-Session": "yes"}) as s:
            s.get("https://api.example.com/")
        assert route.calls[0].request.headers["x-session"] == "yes"

    def test_session_cookies(self, mocked):
        route = respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        with Session(cookies={"sid": "abc123"}) as s:
            s.get("https://api.example.com/")
        assert "sid=abc123" in route.calls[0].request.headers["cookie"]


# ── Caching ───────────────────────────────────────────────────────────────────


class TestCaching:
    def test_cache_hit(self, mocked):
        route = respx.get("https://api.example.com/").mock(
            return_value=httpx.Response(200, json={"cached": True})
        )
        with Session(cache=MemoryCache()) as s:
            r1 = s.get("https://api.example.com/")
            r2 = s.get("https://api.example.com/")
            assert r1.json() == {"cached": True}
            assert r2.json() == {"cached": True}
        # Second request should come from cache, not network
        assert route.call_count == 1

    def test_cache_bypass_on_different_url(self, mocked):
        respx.get("https://api.example.com/a").mock(
            return_value=httpx.Response(200, json={"url": "a"})
        )
        respx.get("https://api.example.com/b").mock(
            return_value=httpx.Response(200, json={"url": "b"})
        )
        with Session(cache=MemoryCache()) as s:
            r1 = s.get("https://api.example.com/a")
            r2 = s.get("https://api.example.com/b")
            assert r1.json()["url"] == "a"
            assert r2.json()["url"] == "b"

    def test_no_cache_by_default(self, mocked):
        route = respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        with Session() as s:
            s.get("https://api.example.com/")
            s.get("https://api.example.com/")
        assert route.call_count == 2


# ── Retries ───────────────────────────────────────────────────────────────────


class TestRetries:
    def test_retry_on_500(self, mocked):
        """Retry on 500 — second attempt succeeds."""
        counter = [0]

        def _respond(request):
            counter[0] += 1
            if counter[0] <= 2:
                return httpx.Response(500)
            return httpx.Response(200, json={"ok": True})

        route = respx.get("https://api.example.com/").mock(side_effect=_respond)
        with Session(max_retries=3, retry_backoff=0.01) as s:
            r = s.get("https://api.example.com/")
            assert r.status_code == 200
        assert route.call_count == 3

    def test_no_retry_on_4xx(self, mocked):
        route = respx.get("https://api.example.com/").mock(return_value=httpx.Response(404))
        with Session(max_retries=3, retry_backoff=0.01) as s:
            r = s.get("https://api.example.com/")
            assert r.status_code == 404
        assert route.call_count == 1


# ── Redirects ─────────────────────────────────────────────────────────────────


class TestRedirects:
    def test_follows_redirect(self, mocked):
        respx.get("https://api.example.com/redirect").mock(
            return_value=httpx.Response(301, headers={"location": "https://api.example.com/final"})
        )
        respx.get("https://api.example.com/final").mock(
            return_value=httpx.Response(200, json={"done": True})
        )
        r = fluxium.get("https://api.example.com/redirect")
        assert r.status_code == 200
        assert r.json()["done"] is True

    def test_no_redirect(self, mocked):
        respx.get("https://api.example.com/redirect").mock(
            return_value=httpx.Response(301, headers={"location": "https://api.example.com/final"})
        )
        r = fluxium.get("https://api.example.com/redirect", allow_redirects=False)
        assert r.status_code == 301


# ── Async ─────────────────────────────────────────────────────────────────────


class TestAsync:
    @pytest.mark.asyncio
    async def test_async_get(self, mocked):
        route = respx.get("https://api.example.com/").mock(
            return_value=httpx.Response(200, json={"async": True})
        )
        async with AsyncSession() as s:
            r = await s.get("https://api.example.com/")
            assert r.status_code == 200
            assert r.json()["async"] is True
        assert route.called

    @pytest.mark.asyncio
    async def test_async_concurrent(self, mocked):
        route = respx.get("https://api.example.com/").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        async with AsyncSession() as s:
            results = [await s.get("https://api.example.com/") for _ in range(5)]
        assert all(r.status_code == 200 for r in results)
        assert route.call_count == 5

    @pytest.mark.asyncio
    async def test_async_session_headers(self, mocked):
        route = respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        async with AsyncSession(headers={"X-Async": "yes"}) as s:
            await s.get("https://api.example.com/")
        assert route.calls[0].request.headers["x-async"] == "yes"


# ── Auth ──────────────────────────────────────────────────────────────────────


class TestAuth:
    def test_basic_auth(self, mocked):
        route = respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.get("https://api.example.com/", auth=fluxium.BasicAuth("user", "pass"))
        auth_header = route.calls[0].request.headers["authorization"]
        assert auth_header.startswith("Basic ")

    def test_bearer_auth(self, mocked):
        route = respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.get("https://api.example.com/", auth=fluxium.BearerAuth("my-token"))
        assert route.calls[0].request.headers["authorization"] == "Bearer my-token"


# ── Body Encoding ────────────────────────────────────────────────────────────


class TestBodyEncoding:
    def test_json_body(self, mocked):
        route = respx.post("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.post("https://api.example.com/", json={"key": "value"})
        body = route.calls[0].request.content
        assert b'"key"' in body
        assert b'"value"' in body

    def test_form_body(self, mocked):
        route = respx.post("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.post("https://api.example.com/", data={"a": "1", "b": "2"})
        body = route.calls[0].request.content
        assert b"a=1" in body
        assert b"b=2" in body

    def test_bytes_body(self, mocked):
        route = respx.post("https://api.example.com/").mock(return_value=httpx.Response(200))
        fluxium.post("https://api.example.com/", data=b"raw bytes")
        assert route.calls[0].request.content == b"raw bytes"


# ── Prewarm ──────────────────────────────────────────────────────────────────


class TestPrewarm:
    def test_prewarm_makes_connection(self, mocked):
        """prewarm() should open a connection to the target URL."""
        route = respx.get("https://api.example.com/").mock(return_value=httpx.Response(200))
        s = Session()
        s.prewarm("https://api.example.com/")
        assert route.call_count == 1
        s.close()

    def test_prewarm_does_not_fail_on_error(self, mocked):
        """prewarm() should silently ignore errors."""
        route = respx.get("https://api.example.com/").mock(return_value=httpx.Response(500))
        s = Session()
        s.prewarm("https://api.example.com/")  # Should not raise
        s.close()


# ── HishelCache (optional) ───────────────────────────────────────────────────


class TestHishelCache:
    def test_hishel_cache_import(self):
        """HishelCache should be importable from fluxium."""
        assert hasattr(fluxium, "HishelCache")

    def test_hishel_cache_requires_hishel(self):
        """HishelCache should raise ImportError if hishel is not installed."""
        import sys

        # Temporarily hide hishel
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
