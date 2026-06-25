# Transport

`fluxium/transport.py`

## Constants

| Constant | Type | Description |
|---|---|---|
| `ACCEPT_ENCODING` | `str` | `"gzip, deflate"` (+ `", br"` if brotli installed) |
| `_HAS_BROTLI` | `bool` | Whether brotli is available |
| `_UVLOOP_INSTALLED` | `bool` | Whether uvloop was installed |

## Functions

| Function | Returns | Description |
|---|---|---|
| `_install_uvloop()` | `bool` | Install uvloop if available |
| `_make_ssl_ctx(verify)` | `bool \| str \| ssl.SSLContext` | Create SSL context |
| `_parse_timeout(t)` | `httpx.Timeout` | Convert timeout to httpx.Timeout |
| `_build_mounts(proxies, *, verify, sync)` | `dict` | Build proxy mounts |
| `_make_transport(proxy_url, *, verify, sync)` | `httpx.HTTPTransport` | Create proxy transport |
| `_build_sync_client(*, verify, proxies, timeout, http2, trust_env)` | `httpx.Client` | Build sync client |
| `_build_async_client(*, verify, proxies, timeout, http2, trust_env)` | `httpx.AsyncClient` | Build async client |

## Default Pool Settings

```python
httpx.Limits(
    max_connections=200,
    max_keepalive_connections=100,
    keepalive_expiry=30,
)
```

## TLS Configuration

```python
# Default context
ssl.create_default_context()

# Custom CA
ssl.create_default_context(cafile="/path/to/ca-bundle.crt")

# Disable (returns False)
# verify=False
```
