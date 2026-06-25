"""
Benchmark: fluxium vs requests vs httpx vs aiohttp.

Uses a local HTTP server for consistent, network-independent results.

Run:
  python benchmark/benchmark.py              # all tests
  python benchmark/benchmark.py --local-only
  python benchmark/benchmark.py --network-only -n 200
  python benchmark/benchmark.py --cache-bench
"""

import asyncio
import io
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import aiohttp
import httpx
import requests

import fluxium

ITERATIONS = 200
ASYNC_CONCURRENT = 20
WARMUP = 5
SEP = "=" * 72
SUBSEP = "-" * 60


class TestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'{"ok": true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        body = b'{"ok": true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def start_test_server(port=0):
    server = HTTPServer(("127.0.0.1", port), TestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{port}"


def bench(name, fn, iterations=ITERATIONS, warmup=WARMUP):
    for _ in range(warmup):
        fn()
    start = time.perf_counter()
    for _ in range(iterations):
        fn()
    elapsed = time.perf_counter() - start
    return name, elapsed, (elapsed / iterations) * 1000


def bench_async_concurrent(name, fn, concurrency=ASYNC_CONCURRENT, warmup=WARMUP):
    async def _run():
        for _ in range(warmup):
            await asyncio.gather(*[fn() for _ in range(concurrency)])
        iterations = max(1, ITERATIONS // concurrency)
        start = time.perf_counter()
        for _ in range(iterations):
            await asyncio.gather(*[fn() for _ in range(concurrency)])
        elapsed = time.perf_counter() - start
        total = iterations * concurrency
        return name, elapsed, (elapsed / total) * 1000

    return asyncio.run(_run())


def print_results(results):
    results.sort(key=lambda x: x[2])
    best = results[0][2] if results else 1
    print(f"\n  {'Library':<30} {'Total (s)':>10} {'Per op (ms)':>12} {'vs best':>10}")
    print(SUBSEP)
    for name, total, per_op in results:
        ratio = per_op / best if best > 0 else 0
        bar = "█" * max(1, int(20 / ratio)) if ratio > 0 else ""
        print(f"  {name:<30} {total:>10.3f} {per_op:>12.3f} {ratio:>9.2f}x  {bar}")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# Network benchmarks (local HTTP server)
# ═══════════════════════════════════════════════════════════════════════════════


def bench_session_get(base_url):
    results = []
    url = base_url + "/get"

    fs = fluxium.Session()
    results.append(bench("fluxium (session)", lambda: fs.get(url, timeout=15)))
    fs.close()

    rs = requests.Session()
    results.append(bench("requests (session)", lambda: rs.get(url, timeout=15)))
    rs.close()

    hs = httpx.Client()
    results.append(bench("httpx (session)", lambda: hs.get(url, timeout=15)))
    hs.close()

    print(f"\n{SEP}")
    print(f"  Session GET (connection pooling, {ITERATIONS} iters)")
    print(SEP)
    print_results(results)


def bench_oneshot_get(base_url):
    results = []
    url = base_url + "/get"

    results.append(bench("fluxium (oneshot)", lambda: fluxium.get(url, timeout=15)))
    results.append(bench("requests (oneshot)", lambda: requests.get(url, timeout=15)))
    results.append(bench("httpx (oneshot)", lambda: httpx.get(url, timeout=15)))

    print(f"\n{SEP}")
    print(f"  One-shot GET (no session, {ITERATIONS} iters)")
    print(SEP)
    print_results(results)


def bench_post_json(base_url):
    results = []
    url = base_url + "/post"
    payload = {"name": "fluxium", "version": "2.0"}

    fs = fluxium.Session()
    results.append(bench("fluxium (session)", lambda: fs.post(url, json=payload, timeout=15)))
    fs.close()

    rs = requests.Session()
    results.append(bench("requests (session)", lambda: rs.post(url, json=payload, timeout=15)))
    rs.close()

    hs = httpx.Client()
    results.append(bench("httpx (session)", lambda: hs.post(url, json=payload, timeout=15)))
    hs.close()

    print(f"\n{SEP}")
    print(f"  POST JSON (session, {ITERATIONS} iters)")
    print(SEP)
    print_results(results)


def bench_multipart(base_url):
    results = []
    url = base_url + "/post"

    def _fluxium():
        f = io.BytesIO(b"file content")
        fs = fluxium.Session()
        fs.post(url, files={"file": ("test.txt", f, "text/plain")}, timeout=15)
        fs.close()

    def _requests():
        f = io.BytesIO(b"file content")
        rs = requests.Session()
        rs.post(url, files={"file": ("test.txt", f, "text/plain")}, timeout=15)
        rs.close()

    def _httpx():
        f = io.BytesIO(b"file content")
        hs = httpx.Client()
        hs.post(url, files={"file": ("test.txt", f, "text/plain")}, timeout=15)
        hs.close()

    results.append(bench("fluxium (session)", _fluxium))
    results.append(bench("requests (session)", _requests))
    results.append(bench("httpx (session)", _httpx))

    print(f"\n{SEP}")
    print(f"  Multipart file upload (session, {ITERATIONS} iters)")
    print(SEP)
    print_results(results)


def bench_async_section(base_url):
    results = []
    url = base_url + "/get"

    async def _all_benchmarks():
        # fluxium
        async def _fluxium():
            async with fluxium.AsyncSession() as s:
                await asyncio.gather(*[s.get(url, timeout=15) for _ in range(ASYNC_CONCURRENT)])

        # httpx
        async def _httpx():
            async with httpx.AsyncClient() as c:
                await asyncio.gather(*[c.get(url, timeout=15) for _ in range(ASYNC_CONCURRENT)])

        # aiohttp
        async def _aiohttp():
            async with aiohttp.ClientSession() as s:
                await asyncio.gather(*[s.get(url) for _ in range(ASYNC_CONCURRENT)])

        coros = [
            ("fluxium (async)", _fluxium),
            ("httpx (async)", _httpx),
            ("aiohttp (async)", _aiohttp),
        ]
        for name, coro in coros:
            try:
                start = time.perf_counter()
                iterations = max(1, ITERATIONS // ASYNC_CONCURRENT)
                for _ in range(iterations):
                    await coro()
                elapsed = time.perf_counter() - start
                total = iterations * ASYNC_CONCURRENT
                results.append((name, elapsed, (elapsed / total) * 1000))
            except Exception as e:
                results.append((name, 0, float("inf")))
                print(f"  {name} skipped: {e}")

    asyncio.run(_all_benchmarks())

    print(f"\n{SEP}")
    print(f"  Async concurrent GET ({ASYNC_CONCURRENT} concurrent)")
    print(SEP)
    print_results(results)


# ═══════════════════════════════════════════════════════════════════════════════
# Local benchmarks (no network)
# ═══════════════════════════════════════════════════════════════════════════════


def bench_cookiejar_local():
    results = []
    from fluxium.cookies import CookieJar

    results.append(
        bench(
            "CookieJar __contains__",
            lambda: "a" in CookieJar({"a": "1", "b": "2", "c": "3"}),
            iterations=200000,
        )
    )
    results.append(
        bench(
            "CookieJar __getitem__",
            lambda: CookieJar({"a": "1", "b": "2", "c": "3"})["a"],
            iterations=200000,
        )
    )
    results.append(
        bench(
            "CookieJar to_header",
            lambda: CookieJar({"a": "1", "b": "2", "c": "3"}).to_header(),
            iterations=200000,
        )
    )

    print(f"\n{SEP}")
    print("  CookieJar operations (local, 200k iters)")
    print(SEP)
    print_results(results)


def bench_json_encoding():
    results = []
    payload = {"name": "fluxium", "version": "2.0"}
    from fluxium.session import _prepare_body

    results.append(
        bench(
            "_prepare_body (json)",
            lambda: _prepare_body(None, payload, None, False),
            iterations=200000,
        )
    )

    import json as _json

    results.append(
        bench(
            "stdlib json.dumps",
            lambda: _json.dumps(payload, separators=(",", ":")).encode(),
            iterations=200000,
        )
    )

    print(f"\n{SEP}")
    print("  JSON body encoding (local, 200k iters)")
    print(SEP)
    print_results(results)


def bench_cache_local():
    results = []
    from fluxium import MemoryCache

    cache = MemoryCache()
    url = "https://api.example.com/data"

    def _cached():
        key = fluxium.cache._make_cache_key("GET", url, None)
        cache.get(key)

    def _uncached():
        # Simulate cache key computation without lookup
        fluxium.cache._make_cache_key("GET", url, None)

    results.append(bench("cache hit (MemoryCache.get)", _cached, iterations=200000))
    results.append(bench("cache key computation only", _uncached, iterations=200000))

    print(f"\n{SEP}")
    print("  Cache operations (local, 200k iters)")
    print(SEP)
    print_results(results)


def bench_timeout_local():
    results = []
    from fluxium import Timeout

    results.append(bench("Timeout(30.0)", lambda: Timeout(30.0), iterations=200000))
    results.append(
        bench(
            "Timeout(connect=5, read=30)",
            lambda: Timeout(connect=5.0, read=30.0),
            iterations=200000,
        )
    )
    results.append(
        bench(
            "Timeout.to_httpx()",
            lambda: Timeout(connect=5.0, read=30.0).to_httpx(),
            iterations=200000,
        )
    )

    print(f"\n{SEP}")
    print("  Timeout operations (local, 200k iters)")
    print(SEP)
    print_results(results)


def bench_idna_encoding():
    results = []
    from fluxium.utils import encode_url

    results.append(
        bench(
            "encode_url (ASCII)",
            lambda: encode_url("https://example.com/path", {"q": "hello"}),
            iterations=200000,
        )
    )
    results.append(
        bench("encode_url (IDNA)", lambda: encode_url("https://münchen.de/path"), iterations=200000)
    )

    print(f"\n{SEP}")
    print("  URL encoding (local, 200k iters)")
    print(SEP)
    print_results(results)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fluxium benchmark suite")
    parser.add_argument("--local-only", action="store_true")
    parser.add_argument("--network-only", action="store_true")
    parser.add_argument("--cache-bench", action="store_true")
    parser.add_argument("-n", "--iterations", type=int, default=None)
    args = parser.parse_args()

    global ITERATIONS
    if args.iterations:
        ITERATIONS = args.iterations

    print("\n" + "█" * 72)
    print(f"  FLUXIUM v{fluxium.__version__} BENCHMARK SUITE")
    print("█" * 72)

    if not args.network_only:
        bench_cookiejar_local()
        bench_json_encoding()
        bench_cache_local()
        bench_timeout_local()
        bench_idna_encoding()

    if args.cache_bench:
        return

    if not args.local_only:
        print("\n" + "!" * 72)
        print("  NETWORK BENCHMARKS — local HTTP server")
        print("!" * 72)
        server, base_url = start_test_server()
        try:
            bench_session_get(base_url)
            bench_oneshot_get(base_url)
            bench_post_json(base_url)
            bench_multipart(base_url)
            bench_async_section(base_url)
        finally:
            server.shutdown()

    print("\n" + "█" * 72)
    print("  Done!")
    print("█" * 72 + "\n")


if __name__ == "__main__":
    main()
