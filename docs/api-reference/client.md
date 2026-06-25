# Client (Session)

`fluxium/session.py`

## Signature

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

## Methods

```python
def request(method: str, url: str, **kwargs) -> Response
def get(url: str, **kwargs) -> Response
def post(url: str, **kwargs) -> Response
def put(url: str, **kwargs) -> Response
def patch(url: str, **kwargs) -> Response
def delete(url: str, **kwargs) -> Response
def head(url: str, **kwargs) -> Response
def options(url: str, **kwargs) -> Response
def close() -> None
def prewarm(url: str) -> None
def add_middleware(mw: Middleware) -> None
def __enter__() -> Session
def __exit__(exc_type, exc_val, exc_tb) -> None
```

## Request Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `params` | `dict \| None` | `None` | Query string |
| `data` | `dict \| bytes \| str \| Generator \| None` | `None` | Request body |
| `json` | `Any \| None` | `None` | JSON body |
| `files` | `dict \| None` | `None` | Multipart upload |
| `headers` | `dict \| None` | `None` | Additional headers |
| `cookies` | `dict \| CookieJar \| None` | `None` | Per-request cookies |
| `auth` | `AuthBase \| None` | `None` | Per-request auth |
| `timeout` | `float \| tuple \| None` | `None` | Override session timeout |
| `allow_redirects` | `bool` | `True` | Follow redirects |
| `stream` | `bool` | `False` | Stream response body |
| `chunked` | `bool` | `False` | Chunked transfer |
| `cache_ttl` | `int` | `300` | Cache TTL in seconds |

## Example

```python
from fluxium import Session

with Session(
    headers={"Authorization": "Bearer xxx"},
    timeout=30.0,
    http2=True,
    max_retries=3,
    cache=MemoryCache(),
) as s:
    r = s.get("https://api.example.com")
    print(r.json())
```
