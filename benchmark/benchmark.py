"""
Benchmark: fluxium vs requests vs httpx vs aiohttp.

Uses a local HTTP server for consistent, network-independent results.

Run:
  python benchmark/benchmark.py              # all tests
  python benchmark/benchmark.py --local-only
  python benchmark/benchmark.py --network-only -n 20
"""
import asyncio
import io
import threading
import time
import timeit
from http.server import HTTPServer, BaseHTTPRequestHandler

import fluxium
import httpx
import requests
import aiohttp

ITERATIONS = 50
ASYNC_CONCURRENT = 20
WARMUP = 5
SEP = "=" * 64
SUBSEP = "-" * 48


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


def abench_concurrent(name, fn, concurrency=ASYNC_CONCURRENT, warmup=WARMUP):
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
    print(f"\n{'Library':<25} {'Total (s)':>10} {'Per op (ms)':>12} {'vs best':>10}")
    print(SUBSEP)
    for name, total, per_op in results:
        ratio = per_op / best if best > 0 else 0
        bar = "█" * max(1, int(20 / ratio)) if ratio > 0 else ""
        print(f"  {name:<23} {total:>10.3f} {per_op:>12.3f} {ratio:>9.2f}x  {bar}")
    print()


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
    payload = {"name": "fluxium", "version": "1.0"}

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


def bench_async_concurrent(base_url):
    results = []
    url = base_url + "/get"

    async def _fluxium():
        async with fluxium.AsyncSession() as s:
            await asyncio.gather(*[s.get(url, timeout=15) for _ in range(ASYNC_CONCURRENT)])

    try:
        results.append(aben_concurrent("fluxium (async)", _fluxium))
    except Exception as e:
        results.append(("fluxium (async)", 0, float("inf")))
        print(f"  fluxium (async) skipped: {e}")

    async def _httpx():
        async with httpx.AsyncClient() as c:
            await asyncio.gather(*[c.get(url, timeout=15) for _ in range(ASYNC_CONCURRENT)])

    try:
        results.append(aben_concurrent("httpx (async)", _httpx))
    except Exception as e:
        results.append(("httpx (async)", 0, float("inf")))
        print(f"  httpx (async) skipped: {e}")

    async def _aiohttp():
        async with aiohttp.ClientSession() as s:
            await asyncio.gather(*[s.get(url) for _ in range(ASYNC_CONCURRENT)])

    try:
        results.append(aben_concurrent("aiohttp (async)", _aiohttp))
    except Exception as e:
        results.append(("aiohttp (async)", 0, float("inf")))
        print(f"  aiohttp (async) skipped: {e}")

    print(f"\n{SEP}")
    print(f"  Async concurrent GET ({ASYNC_CONCURRENT} concurrent)")
    print(SEP)
    print_results(results)


def bench_cookiejar_local():
    results = []
    from fluxium.cookies import CookieJar

    results.append(bench("CookieJar __contains__",
        lambda: "a" in CookieJar({"a": "1", "b": "2", "c": "3"}), iterations=200000))
    results.append(bench("CookieJar __getitem__",
        lambda: CookieJar({"a": "1", "b": "2", "c": "3"})["a"], iterations=200000))
    results.append(bench("CookieJar to_header",
        lambda: CookieJar({"a": "1", "b": "2", "c": "3"}).to_header(), iterations=200000))

    print(f"\n{SEP}")
    print("  CookieJar operations (local, 200k iters)")
    print(SEP)
    print_results(results)


def bench_json_encoding():
    results = []
    payload = {"name": "fluxium", "version": "1.0"}
    from fluxium.session import _prepare_body

    results.append(bench("_prepare_body (json)",
        lambda: _prepare_body(None, payload, None, False), iterations=200000))

    import json as _json
    results.append(bench("stdlib json.dumps",
        lambda: _json.dumps(payload, separators=(",", ":")).encode(), iterations=200000))

    print(f"\n{SEP}")
    print("  JSON body encoding (local, 200k iters)")
    print(SEP)
    print_results(results)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fluxium benchmark suite")
    parser.add_argument("--local-only", action="store_true")
    parser.add_argument("--network-only", action="store_true")
    parser.add_argument("-n", "--iterations", type=int, default=None)
    args = parser.parse_args()

    global ITERATIONS
    if args.iterations:
        ITERATIONS = args.iterations

    print("\n" + "█" * 64)
    print("  FLUXIUM BENCHMARK SUITE")
    print("█" * 64)

    if not args.network_only:
        bench_cookiejar_local()
        bench_json_encoding()

    if not args.local_only:
        print("\n" + "!" * 64)
        print("  NETWORK BENCHMARKS — local HTTP server")
        print("!" * 64)
        server, base_url = start_test_server()
        try:
            bench_session_get(base_url)
            bench_oneshot_get(base_url)
            bench_post_json(base_url)
            bench_async_concurrent(base_url)
        finally:
            server.shutdown()

    print("\n" + "█" * 64)
    print("  Done!")
    print("█" * 64 + "\n")


if __name__ == "__main__":
    main()
