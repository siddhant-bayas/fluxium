"""fluxium test suite."""
import asyncio
import io
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import fluxium
from fluxium import CookieJar, BasicAuth, DigestAuth, Session, AsyncSession
from fluxium.utils import encode_url, netrc_credentials
from fluxium.cookies import CookieJar
from fluxium.auth import BasicAuth, DigestAuth

PASS = "✅"
FAIL = "❌"


def test(name, fn):
    try:
        fn()
        print(f"  {PASS} {name}")
        return True
    except Exception as e:
        print(f"  {FAIL} {name}: {e}")
        return False


# ── Unit tests (no network) ───────────────────────────────────────────────────

def test_cookiejar():
    jar = CookieJar({"session": "abc", "lang": "en"})
    assert jar["session"] == "abc"
    assert jar["lang"] == "en"
    jar["theme"] = "dark"
    assert "theme" in jar
    assert jar.get("missing", "x") == "x"
    assert set(jar.keys()) >= {"session", "lang", "theme"}
    del jar["lang"]
    assert "lang" not in jar
    assert "session=abc" in jar.to_header()

def test_basic_auth():
    import base64
    auth = BasicAuth("user", "pass")
    r = type("R", (), {"headers": {}})()
    auth(r)
    token = base64.b64decode(r.headers["Authorization"].split(" ")[1]).decode()
    assert token == "user:pass"

def test_digest_auth_init():
    auth = DigestAuth("admin", "secret")
    assert auth.username == "admin"

def test_url_encode():
    url = encode_url("https://example.com/path", {"q": "hello world", "page": 1})
    assert "q=hello+world" in url or "q=hello%20world" in url
    assert "page=1" in url

def test_url_idna():
    url = encode_url("https://münchen.de/path")
    assert "xn--mnchen-3ya" in url

def test_response_model():
    from fluxium.models import Response
    r = Response()
    r._content = b'{"ok": true}'
    r.status_code = 200
    assert r.ok
    assert r.json()["ok"] is True
    assert "ok" in r.text

def test_response_raise_for_status():
    from fluxium.models import Response
    from fluxium.exceptions import HTTPError
    r = Response()
    r.status_code = 404
    r.url = "https://example.com"
    try:
        r.raise_for_status()
        assert False, "Should have raised"
    except HTTPError as e:
        assert "404" in str(e)

def test_iter_content():
    from fluxium.models import Response
    r = Response()
    r._content = b"hello world chunked"
    chunks = list(r.iter_content(chunk_size=5))
    assert b"".join(chunks) == b"hello world chunked"

def test_session_context_manager():
    s = Session()
    with s as sess:
        assert sess is s
    # Should not raise after close

def test_multipart_encode():
    from fluxium.session import _encode_multipart
    body, headers = _encode_multipart(
        {"field": "value"},
        {"file": ("test.txt", b"file content", "text/plain")},
    )
    assert b"file content" in body
    assert b"value" in body
    assert "multipart/form-data" in headers["content-type"]

def test_chunked_body():
    from fluxium.session import _prepare_body
    def gen():
        yield b"hello"
        yield b"world"
    body, headers = _prepare_body(gen(), None, None, chunked=True)
    chunks = list(body)
    assert b"".join(chunks) == b"helloworld"

def test_json_body():
    from fluxium.session import _prepare_body
    body, headers = _prepare_body(None, {"key": "val"}, None, False)
    import json
    assert json.loads(body)["key"] == "val"
    assert headers["content-type"] == "application/json"

def test_form_body():
    from fluxium.session import _prepare_body
    body, headers = _prepare_body({"a": "1", "b": "2"}, None, None, False)
    assert b"a=1" in body
    assert headers["content-type"] == "application/x-www-form-urlencoded"

# ── Network tests ─────────────────────────────────────────────────────────────

def test_simple_get():
    r = fluxium.get("https://httpbin.org/get", timeout=15)
    assert r.status_code == 200
    assert r.ok
    data = r.json()
    assert "url" in data

def test_post_json():
    r = fluxium.post("https://httpbin.org/post", json={"name": "fluxium"}, timeout=15)
    assert r.status_code == 200
    assert r.json()["json"]["name"] == "fluxium"

def test_params():
    r = fluxium.get("https://httpbin.org/get", params={"foo": "bar"}, timeout=15)
    assert r.json()["args"]["foo"] == "bar"

def test_headers():
    r = fluxium.get(
        "https://httpbin.org/headers",
        headers={"X-Custom": "fluxium-test"},
        timeout=15,
    )
    assert r.json()["headers"].get("X-Custom") == "fluxium-test"

def test_basic_auth_network():
    r = fluxium.get(
        "https://httpbin.org/basic-auth/user/passwd",
        auth=BasicAuth("user", "passwd"),
        timeout=15,
    )
    assert r.status_code == 200

def test_cookies():
    jar = CookieJar({"testcookie": "fluxval"})
    r = fluxium.get("https://httpbin.org/cookies", cookies=jar, timeout=15)
    assert r.json()["cookies"].get("testcookie") == "fluxval"

def test_session_cookie_persistence():
    with Session() as s:
        s.get("https://httpbin.org/cookies/set?flux=1", timeout=15)
        r = s.get("https://httpbin.org/cookies", timeout=15)
        assert "flux" in r.json()["cookies"]

def test_redirects():
    r = fluxium.get("https://httpbin.org/redirect/3", timeout=15)
    assert r.status_code == 200
    assert len(r.history) == 3

def test_no_redirect():
    r = fluxium.get("https://httpbin.org/redirect/1", allow_redirects=False, timeout=15)
    assert r.status_code in (301, 302)

def test_timeout():
    from fluxium.exceptions import TimeoutError
    try:
        fluxium.get("https://httpbin.org/delay/10", timeout=1)
        assert False, "Should have timed out"
    except TimeoutError:
        pass

def test_ssl():
    r = fluxium.get("https://httpbin.org/get", verify=True, timeout=15)
    assert r.status_code == 200

def test_streaming():
    with Session() as s:
        r = s.get("https://httpbin.org/stream-bytes/1024", stream=True, timeout=15)
        data = b"".join(r.iter_content(chunk_size=256))
        assert len(data) == 1024

def test_file_upload():
    fake_file = io.BytesIO(b"Hello fluxium file upload!")
    r = fluxium.post(
        "https://httpbin.org/post",
        files={"upload": ("hello.txt", fake_file, "text/plain")},
        timeout=15,
    )
    assert r.status_code == 200
    assert "Hello fluxium file upload!" in r.text

def test_gzip_decompression():
    r = fluxium.get("https://httpbin.org/gzip", timeout=15)
    assert r.json()["gzipped"] is True

def test_deflate_decompression():
    r = fluxium.get("https://httpbin.org/deflate", timeout=15)
    assert r.json()["deflated"] is True

def test_put():
    r = fluxium.put("https://httpbin.org/put", json={"x": 1}, timeout=15)
    assert r.status_code == 200

def test_delete():
    r = fluxium.delete("https://httpbin.org/delete", timeout=15)
    assert r.status_code == 200

def test_patch():
    r = fluxium.patch("https://httpbin.org/patch", json={"y": 2}, timeout=15)
    assert r.status_code == 200

def test_head():
    r = fluxium.head("https://httpbin.org/get", timeout=15)
    assert r.status_code == 200
    assert r.content == b""

def test_async_get():
    async def _run():
        r = await fluxium.aget("https://httpbin.org/get", timeout=15)
        assert r.status_code == 200
        return r.json()
    data = asyncio.run(_run())
    assert "url" in data

def test_async_session():
    async def _run():
        async with AsyncSession() as s:
            tasks = [s.get("https://httpbin.org/get", timeout=15) for _ in range(5)]
            results = await asyncio.gather(*tasks)
            return [r.status_code for r in results]
    codes = asyncio.run(_run())
    assert all(c == 200 for c in codes)

def test_chunked_upload():
    def body_gen():
        for chunk in [b"chunk1-", b"chunk2-", b"chunk3"]:
            yield chunk
    r = fluxium.post("https://httpbin.org/post", data=body_gen(), timeout=15)
    assert r.status_code == 200


# ── Runner ────────────────────────────────────────────────────────────────────

def main():
    print("\n⚡ Fluxium Test Suite\n")

    unit_tests = [
        ("CookieJar dict interface", test_cookiejar),
        ("BasicAuth header", test_basic_auth),
        ("DigestAuth init", test_digest_auth_init),
        ("URL param encoding", test_url_encode),
        ("IDNA international domain", test_url_idna),
        ("Response model", test_response_model),
        ("Response raise_for_status", test_response_raise_for_status),
        ("iter_content", test_iter_content),
        ("Session context manager", test_session_context_manager),
        ("Multipart encode", test_multipart_encode),
        ("Chunked body generator", test_chunked_body),
        ("JSON body prepare", test_json_body),
        ("Form body prepare", test_form_body),
    ]

    network_tests = [
        ("GET", test_simple_get),
        ("POST JSON", test_post_json),
        ("Query params", test_params),
        ("Custom headers", test_headers),
        ("Basic auth", test_basic_auth_network),
        ("Cookies in request", test_cookies),
        ("Session cookie persistence", test_session_cookie_persistence),
        ("Redirects", test_redirects),
        ("No redirects", test_no_redirect),
        ("Timeout", test_timeout),
        ("TLS verification", test_ssl),
        ("Streaming download", test_streaming),
        ("File upload (multipart)", test_file_upload),
        ("Gzip decompression", test_gzip_decompression),
        ("Deflate decompression", test_deflate_decompression),
        ("PUT", test_put),
        ("DELETE", test_delete),
        ("PATCH", test_patch),
        ("HEAD", test_head),
        ("Async GET", test_async_get),
        ("Async Session (concurrent)", test_async_session),
        ("Chunked upload", test_chunked_upload),
    ]

    print("── Unit Tests ─────────────────────────────────")
    u_pass = sum(test(n, f) for n, f in unit_tests)

    print(f"\n── Network Tests ──────────────────────────────")
    n_pass = sum(test(n, f) for n, f in network_tests)

    total = len(unit_tests) + len(network_tests)
    passed = u_pass + n_pass
    print(f"\n{'='*48}")
    print(f"  Result: {passed}/{total} tests passed")
    print(f"  Unit:    {u_pass}/{len(unit_tests)}")
    print(f"  Network: {n_pass}/{len(network_tests)}")
    return passed == total


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
