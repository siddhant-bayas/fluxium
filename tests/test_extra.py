"""Additional tests for fluxium 2.0.0 - reaching 250+ total."""

from __future__ import annotations

import json
import warnings

import pytest
import respx

import fluxium
from fluxium import (
    LoggingMiddleware,
    RateLimitMiddleware,
    RetryMiddleware,
    Session,
    Timeout,
)
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
# 18. ADDITIONAL TESTS (50 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestResponseModel:
    def test_response_ok_true(self):
        resp = fluxium.Response()
        resp.status_code = 200
        assert resp.ok is True

    def test_response_ok_false(self):
        resp = fluxium.Response()
        resp.status_code = 400
        assert resp.ok is False

    def test_response_ok_boundary_399(self):
        resp = fluxium.Response()
        resp.status_code = 399
        assert resp.ok is True

    def test_response_ok_boundary_400(self):
        resp = fluxium.Response()
        resp.status_code = 400
        assert resp.ok is False

    def test_response_content(self):
        resp = fluxium.Response()
        resp._content = b"hello"
        assert resp.content == b"hello"

    def test_response_text_utf8(self):
        resp = fluxium.Response()
        resp._content = b"hello"
        assert resp.text == "hello"

    def test_response_text_empty(self):
        resp = fluxium.Response()
        assert resp.text == ""

    def test_response_json_parse(self):
        resp = fluxium.Response()
        resp._content = b'{"key": "value"}'
        assert resp.json() == {"key": "value"}

    def test_response_json_empty_raises(self):
        resp = fluxium.Response()
        with pytest.raises(json.JSONDecodeError):
            resp.json()

    def test_response_is_redirect_301(self):
        resp = fluxium.Response()
        resp.status_code = 301
        assert resp.is_redirect

    def test_response_is_redirect_302(self):
        resp = fluxium.Response()
        resp.status_code = 302
        assert resp.is_redirect

    def test_response_is_redirect_303(self):
        resp = fluxium.Response()
        resp.status_code = 303
        assert resp.is_redirect

    def test_response_is_redirect_307(self):
        resp = fluxium.Response()
        resp.status_code = 307
        assert resp.is_redirect

    def test_response_is_redirect_308(self):
        resp = fluxium.Response()
        resp.status_code = 308
        assert resp.is_redirect

    def test_response_is_not_redirect_200(self):
        resp = fluxium.Response()
        resp.status_code = 200
        assert not resp.is_redirect

    def test_response_is_not_redirect_500(self):
        resp = fluxium.Response()
        resp.status_code = 500
        assert not resp.is_redirect

    def test_response_bool_true(self):
        resp = fluxium.Response()
        resp.status_code = 200
        assert bool(resp) is True

    def test_response_bool_false(self):
        resp = fluxium.Response()
        resp.status_code = 500
        assert bool(resp) is False

    def test_response_iter_content(self):
        resp = fluxium.Response()
        resp._content = b"abcdefghij"
        chunks = list(resp.iter_content(chunk_size=3))
        assert b"".join(chunks) == b"abcdefghij"

    def test_response_iter_content_empty(self):
        resp = fluxium.Response()
        chunks = list(resp.iter_content())
        assert chunks == []

    def test_response_iter_lines(self):
        resp = fluxium.Response()
        resp._content = b"a\nb\nc"
        lines = list(resp.iter_lines())
        assert lines == ["a", "b", "c"]

    def test_response_iter_lines_empty(self):
        resp = fluxium.Response()
        lines = list(resp.iter_lines())
        assert lines == []

    def test_response_repr(self):
        resp = fluxium.Response()
        resp.status_code = 200
        assert "200" in repr(resp)

    def test_response_history(self):
        resp = fluxium.Response()
        assert resp.history == []

    def test_response_elapsed_initially_none(self):
        resp = fluxium.Response()
        assert resp.elapsed is None


class TestTimeoutClass:
    def test_timeout_all_components(self):
        t = Timeout(10.0)
        assert t.connect == 10.0
        assert t.read == 10.0
        assert t.write == 10.0
        assert t.pool == 10.0

    def test_timeout_connect_only(self):
        t = Timeout(connect=5.0)
        assert t.connect == 5.0
        assert t.read == 5.0

    def test_timeout_read_only(self):
        t = Timeout(read=30.0)
        assert t.read == 30.0

    def test_timeout_tuple_two_elements(self):
        t = Timeout((5.0, 30.0))
        assert t.connect == 5.0
        assert t.read == 30.0

    def test_timeout_tuple_four_elements(self):
        t = Timeout((1.0, 2.0, 3.0, 4.0))
        assert t.connect == 1.0
        assert t.read == 2.0
        assert t.write == 3.0
        assert t.pool == 4.0

    def test_timeout_none(self):
        t = Timeout(None)
        assert t.connect is None
        assert t.read is None

    def test_timeout_to_httpx_preserves_values(self):
        t = Timeout(connect=1.0, read=2.0, write=3.0, pool=4.0)
        ht = t.to_httpx()
        assert ht.connect == 1.0
        assert ht.read == 2.0
        assert ht.write == 3.0
        assert ht.pool == 4.0

    def test_timeout_repr_connect_only(self):
        t = Timeout(connect=5.0)
        assert "connect=5.0" in repr(t)

    def test_timeout_repr_all(self):
        t = Timeout(connect=1.0, read=2.0, write=3.0, pool=4.0)
        r = repr(t)
        assert "connect=1.0" in r
        assert "pool=4.0" in r

    def test_timeout_default(self):
        t = Timeout()
        assert t.connect == 30.0


class TestMiddlewareStack:
    def test_middleware_stack_empty(self):
        s = Session()
        assert len(s._middleware) == 0
        s.close()

    def test_middleware_stack_add(self):
        s = Session()
        s.add_middleware(LoggingMiddleware())
        assert len(s._middleware) == 1
        s.close()

    def test_middleware_stack_add_retry(self):
        s = Session()
        s.add_middleware(RetryMiddleware())
        assert len(s._middleware) == 1
        s.close()

    def test_middleware_stack_add_rate_limit(self):
        s = Session()
        s.add_middleware(RateLimitMiddleware())
        assert len(s._middleware) == 1
        s.close()

    def test_middleware_stack_multiple(self):
        s = Session()
        s.add_middleware(LoggingMiddleware())
        s.add_middleware(RetryMiddleware())
        s.add_middleware(RateLimitMiddleware())
        assert len(s._middleware) == 3
        s.close()

    def test_middleware_stack_bool_empty(self):
        s = Session()
        assert not s._middleware
        s.close()

    def test_middleware_stack_bool_nonempty(self):
        s = Session()
        s.add_middleware(LoggingMiddleware())
        assert s._middleware
        s.close()


class TestCookieJarExtended:
    def test_cookiejar_from_cookiejar_instance(self):
        jar1 = CookieJar({"a": "1"})
        jar2 = CookieJar(jar1)
        assert jar2["a"] == "1"

    def test_cookiejar_update_with_cookiejar(self):
        jar1 = CookieJar({"a": "1"})
        jar2 = CookieJar({"b": "2"})
        jar1.update(jar2)
        assert jar1["a"] == "1"
        assert jar1["b"] == "2"

    def test_cookiejar_to_header_single(self):
        jar = CookieJar({"session": "abc"})
        assert jar.to_header() == "session=abc"

    def test_cookiejar_to_header_multiple(self):
        jar = CookieJar({"a": "1", "b": "2"})
        header = jar.to_header()
        assert "a=1" in header
        assert "b=2" in header

    def test_cookiejar_keys_when_empty(self):
        jar = CookieJar()
        assert jar.keys() == []

    def test_cookiejar_values_when_empty(self):
        jar = CookieJar()
        assert jar.values() == []

    def test_cookiejar_items_when_empty(self):
        jar = CookieJar()
        assert jar.items() == []

    def test_cookiejar_get_existing(self):
        jar = CookieJar({"a": "1"})
        assert jar.get("a") == "1"

    def test_cookiejar_get_missing_default(self):
        jar = CookieJar()
        assert jar.get("x", "default") == "default"

    def test_cookiejar_contains_existing(self):
        jar = CookieJar({"a": "1"})
        assert "a" in jar

    def test_cookiejar_contains_missing(self):
        jar = CookieJar()
        assert "x" not in jar


class TestExceptionHierarchy:
    def test_all_exceptions_catchable_as_fluxium_error(self):
        exceptions = [
            ConnectionError("test"),
            TimeoutError("test"),
            HTTPError("test"),
            TooManyRedirects("test"),
            SSLError("test"),
            ProxyError("test"),
        ]
        for exc in exceptions:
            try:
                raise exc
            except FluxiumError:
                pass

    def test_ssl_error_is_connection_error(self):
        assert issubclass(SSLError, ConnectionError)

    def test_proxy_error_is_connection_error(self):
        assert issubclass(ProxyError, ConnectionError)

    def test_http_error_response_attribute(self):
        resp = fluxium.Response()
        resp.status_code = 500
        err = HTTPError("server error", response=resp)
        assert err.response.status_code == 500

    def test_http_error_str(self):
        err = HTTPError("test message")
        assert "test message" in str(err)

    def test_too_many_redirects_str(self):
        err = TooManyRedirects("too many")
        assert "too many" in str(err)

    def test_fluxium_error_is_exception(self):
        assert issubclass(FluxiumError, Exception)


class TestWarningsExtended:
    def test_insecure_ssl_warning_is_fluxium_warning(self):
        assert issubclass(InsecureSSLWarning, FluxiumWarning)

    def test_retry_warning_is_fluxium_warning(self):
        assert issubclass(RetryWarning, FluxiumWarning)

    def test_fluxium_warning_is_user_warning(self):
        assert issubclass(FluxiumWarning, UserWarning)

    def test_retry_warning_attributes(self):
        w = RetryWarning(1, 3, "https://example.com", "timeout")
        assert w.attempt == 1
        assert w.max_retries == 3
        assert w.url == "https://example.com"
        assert w.reason == "timeout"
        assert "timeout" in str(w)

    def test_warning_can_be_filtered(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("error", InsecureSSLWarning)
            with pytest.raises(InsecureSSLWarning):
                Session(verify=False)


class TestPublicAPI:
    def test_all_exports_present(self):
        expected = [
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "head",
            "options",
            "request",
            "aget",
            "apost",
            "aput",
            "apatch",
            "adelete",
            "ahead",
            "aoptions",
            "arequest",
            "Session",
            "AsyncSession",
            "Response",
            "Request",
            "BasicAuth",
            "DigestAuth",
            "BearerAuth",
            "OAuth2Auth",
            "CookieJar",
            "MemoryCache",
            "DiskCache",
            "HishelCache",
            "Middleware",
            "LoggingMiddleware",
            "RetryMiddleware",
            "RateLimitMiddleware",
            "SSEEvent",
            "StreamReader",
            "iter_sse",
            "aiter_sse",
            "FluxiumError",
            "ConnectionError",
            "TimeoutError",
            "HTTPError",
            "SSLError",
            "ProxyError",
            "TooManyRedirects",
            "FluxiumWarning",
            "InsecureSSLWarning",
            "RetryWarning",
            "Timeout",
            "__version__",
            "__author__",
        ]
        for name in expected:
            assert hasattr(fluxium, name), f"Missing export: {name}"

    def test_version_is_string(self):
        assert isinstance(fluxium.__version__, str)

    def test_author_is_string(self):
        assert isinstance(fluxium.__author__, str)
