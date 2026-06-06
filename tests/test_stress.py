import asyncio
import concurrent.futures
import gc
import io
import os

import psutil
import pytest

import fluxium
from fluxium import (
    AsyncSession,
    Session,
    TimeoutError,
)

HTTPBIN = "https://httpbin.org"
HTTP2BIN = "https://nghttp2.org/httpbin"


# ============================================================
# BASIC REQUESTS
# ============================================================

def test_get():
    r = fluxium.get(f"{HTTPBIN}/get", timeout=15)

    assert r.status_code == 200
    assert r.ok is True


def test_post_json():
    payload = {"name": "fluxium"}

    r = fluxium.post(
        f"{HTTPBIN}/post",
        json=payload,
        timeout=15,
    )

    assert r.status_code == 200
    assert r.json()["json"] == payload


def test_query_params():
    r = fluxium.get(
        f"{HTTPBIN}/get",
        params={"q": "fluxium"},
        timeout=15,
    )

    assert r.status_code == 200
    assert r.json()["args"]["q"] == "fluxium"


# ============================================================
# COOKIES
# ============================================================

def test_cookies():
    jar = fluxium.CookieJar({"testcookie": "fluxval"})

    r = fluxium.get(
        f"{HTTPBIN}/cookies",
        cookies=jar,
        timeout=15,
    )

    assert r.json()["cookies"]["testcookie"] == "fluxval"


def test_session_cookie_persistence():
    with Session() as s:
        s.get(
            f"{HTTPBIN}/cookies/set?fluxium=1",
            timeout=15,
        )

        r = s.get(
            f"{HTTPBIN}/cookies",
            timeout=15,
        )

        assert r.json()["cookies"]["fluxium"] == "1"


# ============================================================
# REDIRECTS
# ============================================================

def test_redirect_chain():
    r = fluxium.get(
        f"{HTTPBIN}/redirect/5",
        timeout=15,
    )

    assert r.status_code == 200
    assert len(r.history) == 5


# ============================================================
# TIMEOUTS
# ============================================================

def test_timeout():
    with pytest.raises(TimeoutError):
        fluxium.get(
            f"{HTTPBIN}/delay/10",
            timeout=1,
        )


# ============================================================
# FILE UPLOADS
# ============================================================

def test_file_upload():
    f = io.BytesIO(b"hello fluxium")

    r = fluxium.post(
        f"{HTTPBIN}/post",
        files={
            "file": (
                "test.txt",
                f,
                "text/plain",
            )
        },
        timeout=30,
    )

    assert r.status_code == 200


# ============================================================
# CHUNKED UPLOADS
# ============================================================

def chunk_generator():
    for _ in range(1024):
        yield b"x" * 1024


def test_chunked_upload():
    r = fluxium.post(
        f"{HTTPBIN}/post",
        data=chunk_generator(),
        chunked=True,
        timeout=60,
    )

    assert r.status_code == 200


# ============================================================
# STREAMING
# ============================================================

def test_stream_lines():
    r = fluxium.get(
        f"{HTTPBIN}/stream/100",
        stream=True,
        timeout=60,
    )

    count = 0

    for _ in r.iter_lines():
        count += 1

    assert count == 100


# ============================================================
# CONNECTION REUSE
# ============================================================

def test_connection_reuse():
    with Session() as s:
        for _ in range(10):
            r = s.get(
                f"{HTTPBIN}/get",
                timeout=15,
            )

            assert r.status_code == 200


# ============================================================
# MULTITHREAD
# ============================================================

def _thread_worker():
    with Session() as s:
        for _ in range(50):
            r = s.get(
                f"{HTTPBIN}/get",
                timeout=15,
            )

            assert r.status_code == 200


def test_thread_stress():
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=20
    ) as executor:

        futures = [
            executor.submit(_thread_worker)
            for _ in range(20)
        ]

        for future in futures:
            future.result()


# ============================================================
# MEMORY LEAK CHECK
# ============================================================

def test_memory_stability():
    process = psutil.Process(os.getpid())

    before = process.memory_info().rss

    with Session() as s:
        for _ in range(3000):
            r = s.get(
                f"{HTTPBIN}/get",
                timeout=15,
            )

            assert r.status_code == 200

    gc.collect()

    after = process.memory_info().rss

    growth = after - before

    assert growth < 50 * 1024 * 1024


# ============================================================
# INVALID URLS
# ============================================================

@pytest.mark.parametrize(
    "url",
    [
        "http://",
        "://broken",
        "not-a-url",
        "",
    ],
)
def test_invalid_urls(url):
    with pytest.raises(Exception):
        fluxium.get(url)


# ============================================================
# IDNA / UNICODE DOMAINS
# ============================================================

@pytest.mark.parametrize(
    "url",
    [
        "https://münchen.de",
        "https://пример.испытание",
        "https://中文.com",
    ],
)
def test_idna_domains(url):
    try:
        fluxium.get(
            url,
            timeout=10,
        )
    except Exception:
        pass


# ============================================================
# ASYNC TESTS
# ============================================================

@pytest.mark.asyncio
async def test_async_get():
    async with AsyncSession() as s:
        r = await s.get(
            f"{HTTPBIN}/get",
            timeout=15,
        )

        assert r.status_code == 200


@pytest.mark.asyncio
async def test_500_concurrent_requests():
    async with AsyncSession() as s:
        tasks = [
            s.get(
                f"{HTTPBIN}/get",
                timeout=30,
            )
            for _ in range(500)
        ]

        responses = await asyncio.gather(*tasks)

    assert all(
        r.status_code == 200
        for r in responses
    )


@pytest.mark.asyncio
async def test_2000_concurrent_requests():
    async with AsyncSession() as s:
        tasks = [
            s.get(
                f"{HTTPBIN}/get",
                timeout=60,
            )
            for _ in range(2000)
        ]

        responses = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

    failures = [
        r
        for r in responses
        if isinstance(r, Exception)
    ]

    assert len(failures) < 20


# ============================================================
# HTTP/2
# ============================================================

@pytest.mark.asyncio
async def test_http2_multiplex():
    async with AsyncSession(
        http2=True
    ) as s:

        tasks = [
            s.get(
                f"{HTTP2BIN}/get",
                timeout=30,
            )
            for _ in range(200)
        ]

        responses = await asyncio.gather(*tasks)

    assert all(
        r.status_code == 200
        for r in responses
    )


# ============================================================
# LARGE DOWNLOAD
# ============================================================

def test_large_download():
    r = fluxium.get(
        "https://speed.hetzner.de/100MB.bin",
        timeout=300,
    )

    assert len(r.content) > 100_000_000


# ============================================================
# REAL STRESS TEST
# ============================================================

@pytest.mark.asyncio
async def test_10000_requests():
    async with AsyncSession() as s:

        tasks = [
            s.get(
                f"{HTTPBIN}/get",
                timeout=120,
            )
            for _ in range(10000)
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

    failures = [
        x
        for x in results
        if isinstance(x, Exception)
    ]

    success = len(results) - len(failures)

    print(
        f"success={success}, "
        f"failures={len(failures)}"
    )

    assert success >= 9900