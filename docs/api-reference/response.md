# Response

`fluxium/models.py`

## Signature

```python
class Response:
    def __init__()
```

## Attributes

| Attribute | Type | Description |
|---|---|---|
| `status_code` | `int` | HTTP status code (default 0) |
| `url` | `str` | Final URL after redirects |
| `headers` | `dict` | Response headers (lowercase keys) |
| `cookies` | `CookieJar` | Response cookies |
| `encoding` | `str` | Detected encoding (default "utf-8") |
| `history` | `list[Response]` | Redirect chain |
| `elapsed` | `float \| None` | Time elapsed (set by transport) |
| `request` | `Request \| None` | Originating request |

## Properties

| Property | Returns | Description |
|---|---|---|
| `content` | `bytes` | Raw response body |
| `text` | `str` | Auto-decoded body |
| `ok` | `bool` | `status_code < 400` |
| `is_redirect` | `bool` | status in (301, 302, 303, 307, 308) |

## Methods

| Method | Returns | Description |
|---|---|---|
| `json(**kwargs)` | `Any` | Parse body as JSON |
| `raise_for_status()` | `None` | Raise `HTTPError` on 4xx/5xx |
| `iter_content(chunk_size=8192)` | `Iterator[bytes]` | Stream body in chunks |
| `iter_lines()` | `Iterator[str]` | Iterate line by line |
| `__bool__()` | `bool` | Same as `ok` |

## Slots

```python
__slots__ = (
    "status_code", "url", "headers", "cookies", "_content",
    "encoding", "history", "elapsed", "request", "_raw",
    "_text", "_enc",
)
```

## Note

`__bool__` returns `self.ok`, so `if response:` evaluates to `False` for 4xx/5xx. Use `if response is not None:` for null checks.
