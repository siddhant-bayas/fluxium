# API Reference

## Module-Level Functions

One-shot convenience functions. Each creates a short-lived session internally.

### Sync

```python
fluxium.get(url, **kwargs) -> Response
fluxium.post(url, **kwargs) -> Response
fluxium.put(url, **kwargs) -> Response
fluxium.patch(url, **kwargs) -> Response
fluxium.delete(url, **kwargs) -> Response
fluxium.head(url, **kwargs) -> Response
fluxium.options(url, **kwargs) -> Response
fluxium.request(method, url, **kwargs) -> Response
```

### Async

```python
await fluxium.aget(url, **kwargs) -> Response
await fluxium.apost(url, **kwargs) -> Response
await fluxium.aput(url, **kwargs) -> Response
await fluxium.apatch(url, **kwargs) -> Response
await fluxium.adelete(url, **kwargs) -> Response
await fluxium.ahead(url, **kwargs) -> Response
await fluxium.aoptions(url, **kwargs) -> Response
await fluxium.arequest(method, url, **kwargs) -> Response
```

## Session

```python
class Session:
    def __init__(
        self,
        *,
        headers: dict | None = None,
        cookies: dict | CookieJar | None = None,
        auth: AuthBase | None = None,
        verify: bool | str = True,
        proxies: dict | str | None = None,
        timeout: float | tuple = 30.0,
        http2: bool = True,
        max_redirects: int = 30,
        trust_env: bool = True,
        cache: CacheBackend | None = None,
        max_retries: int = 0,
        retry_backoff: float = 0.5,
    )
```

| Parameter | Default | Description |
|---|---|---|
| `headers` | `None` | Base headers merged into every request |
| `cookies` | `None` | Cookies sent with every request |
| `auth` | `None` | Default authentication |
| `verify` | `True` | TLS verification (`False` to disable, or path to CA bundle) |
| `proxies` | `None` | Proxy URL or `{"all://": "..."}` dict |
| `timeout` | `30.0` | Default timeout in seconds |
| `http2` | `True` | Enable HTTP/2 |
| `max_redirects` | `30` | Maximum redirects before raising `TooManyRedirects` |
| `trust_env` | `True` | Read credentials from `~/.netrc` |
| `cache` | `None` | Cache backend (`MemoryCache` or `DiskCache`) |
| `max_retries` | `0` | Number of retries for transient errors |
| `retry_backoff` | `0.5` | Exponential backoff factor |

### Methods

```python
session.request(method, url, **kwargs) -> Response
session.get(url, **kwargs) -> Response
session.post(url, **kwargs) -> Response
session.put(url, **kwargs) -> Response
session.patch(url, **kwargs) -> Response
session.delete(url, **kwargs) -> Response
session.head(url, **kwargs) -> Response
session.options(url, **kwargs) -> Response
session.close()
session.add_middleware(mw)
```

### Request Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `params` | `dict` | `None` | Query string parameters |
| `data` | `dict \| bytes \| str \| Generator` | `None` | Request body |
| `json` | `Any` | `None` | JSON body (sets `Content-Type`) |
| `files` | `dict` | `None` | Multipart upload |
| `headers` | `dict` | `None` | Additional headers |
| `cookies` | `dict \| CookieJar` | `None` | Per-request cookies |
| `auth` | `AuthBase` | `None` | Per-request auth |
| `timeout` | `float \| tuple` | `None` | Override session timeout |
| `allow_redirects` | `bool` | `True` | Follow redirects |
| `stream` | `bool` | `False` | Stream response body |
| `chunked` | `bool` | `False` | Chunked transfer for generators |
| `cache_ttl` | `int` | `300` | Cache TTL in seconds |

## AsyncSession

Same API as `Session`, but all methods are `async`:

```python
async with AsyncSession() as s:
    r = await s.get("https://api.example.com")
```

## Response

```python
r.status_code    # int
r.url            # str (final URL after redirects)
r.headers        # dict (lowercase keys)
r.cookies        # CookieJar
r.content        # bytes
r.text           # str (auto-decoded)
r.json()         # Any (parsed JSON)
r.history        # list[Response] (redirect chain)
r.ok             # bool (status < 400)
r.is_redirect    # bool
r.raise_for_status()  # raises HTTPError on 4xx/5xx
r.iter_content(chunk_size=8192)  # Iterator[bytes]
r.iter_lines()   # Iterator[str]
```

## Authentication

### BasicAuth

```python
fluxium.BasicAuth("username", "password")
```

### DigestAuth

```python
fluxium.DigestAuth("username", "password")
```

### BearerAuth

```python
fluxium.BearerAuth("token", refresh_callback=lambda: get_new_token())
```

### OAuth2Auth

```python
fluxium.OAuth2Auth(
    token_url="https://auth.example.com/token",
    client_id="...",
    client_secret="...",
)
```

## CookieJar

```python
jar = fluxium.CookieJar({"session": "abc"})
jar["key"] = "value"       # set
value = jar["key"]         # get
del jar["key"]             # delete
"key" in jar               # contains
jar.to_dict()              # {"key": "value"}
jar.to_header()            # "key=value"
```

## Caching

```python
from fluxium import MemoryCache, DiskCache

# In-memory cache
with Session(cache=MemoryCache(max_size=1000)) as s:
    r = s.get("https://api.example.com")  # cached for 300s

# Disk cache
with Session(cache=DiskCache(".cache")) as s:
    r = s.get("https://api.example.com")
```

## Middleware

```python
from fluxium import Middleware, LoggingMiddleware, RetryMiddleware

class MyMiddleware(Middleware):
    def on_request(self, request):
        request.headers["X-Request-ID"] = generate_id()
        return request

    def on_response(self, response):
        log_response(response)
        return response

session = Session()
session.add_middleware(LoggingMiddleware())
session.add_middleware(RetryMiddleware(max_retries=3))
```

## Streaming & SSE

```python
# Stream download
with Session() as s:
    r = s.get("https://example.com/large.zip", stream=True)
    with open("large.zip", "wb") as f:
        for chunk in r.iter_content(chunk_size=65536):
            f.write(chunk)

# Server-Sent Events
with Session() as s:
    r = s.get("https://example.com/events", stream=True)
    for event in fluxium.iter_sse(r):
        print(event.event, event.data)
```

## Exceptions

```
FluxiumError
├── ConnectionError
│   ├── SSLError
│   └── ProxyError
├── TimeoutError
├── HTTPError
└── TooManyRedirects
```
