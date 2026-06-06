"""Transport layer: builds httpx clients with connection pooling and TLS."""
from __future__ import annotations

import ssl

import httpx

try:
    import brotli as _brotli  # noqa: F401
    _HAS_BROTLI = True
except ImportError:
    _HAS_BROTLI = False

ACCEPT_ENCODING = "gzip, deflate" + (", br" if _HAS_BROTLI else "")


def _make_ssl_ctx(verify):
    if verify is True:
        return True
    if verify is False:
        return False
    return ssl.create_default_context(cafile=verify)


def _parse_timeout(t):
    if t is None:
        return httpx.Timeout(None)
    if isinstance(t, httpx.Timeout):
        return t
    if isinstance(t, (int, float)):
        return httpx.Timeout(float(t))
    if isinstance(t, tuple):
        connect, read = float(t[0]), float(t[1])
        return httpx.Timeout(read, connect=connect)
    return httpx.Timeout(30.0)


def _build_mounts(proxies, *, verify, sync: bool):
    if not proxies:
        return {}
    if isinstance(proxies, str):
        proxies = {"all://": proxies}
    mounts = {}
    for scheme, url in proxies.items():
        if not url:
            continue
        mounts[scheme] = _make_transport(url, verify=verify, sync=sync)
    return mounts


def _make_transport(proxy_url: str, *, verify, sync: bool):
    lower = proxy_url.lower()
    if lower.startswith("socks5://") or lower.startswith("socks4://"):
        try:
            import httpx_socks
            cls = httpx_socks.SyncProxyTransport if sync else httpx_socks.AsyncProxyTransport
            return cls.from_url(proxy_url, verify=verify)
        except ImportError:
            raise ImportError("SOCKS proxy requires 'httpx-socks': pip install httpx-socks")
    if sync:
        return httpx.HTTPTransport(proxy=httpx.Proxy(proxy_url), verify=verify)
    return httpx.AsyncHTTPTransport(proxy=httpx.Proxy(proxy_url), verify=verify)


def _build_sync_client(
    *,
    verify: bool | str = True,
    proxies: dict | str | None = None,
    timeout: float | tuple | None = 30.0,
    http2: bool = True,
    trust_env: bool = True,
) -> httpx.Client:
    ssl_ctx = _make_ssl_ctx(verify)
    mounts = _build_mounts(proxies, verify=ssl_ctx, sync=True)
    t = _parse_timeout(timeout)
    return httpx.Client(
        http2=http2,
        verify=ssl_ctx,
        limits=httpx.Limits(max_connections=200, max_keepalive_connections=100, keepalive_expiry=30),
        timeout=t,
        follow_redirects=False,
        trust_env=trust_env,
        mounts=mounts or None,
    )


def _build_async_client(
    *,
    verify: bool | str = True,
    proxies: dict | str | None = None,
    timeout: float | tuple | None = 30.0,
    http2: bool = True,
    trust_env: bool = True,
) -> httpx.AsyncClient:
    ssl_ctx = _make_ssl_ctx(verify)
    mounts = _build_mounts(proxies, verify=ssl_ctx, sync=False)
    t = _parse_timeout(timeout)
    return httpx.AsyncClient(
        http2=http2,
        verify=ssl_ctx,
        limits=httpx.Limits(max_connections=200, max_keepalive_connections=100, keepalive_expiry=30),
        timeout=t,
        follow_redirects=False,
        trust_env=trust_env,
        mounts=mounts or None,
    )
