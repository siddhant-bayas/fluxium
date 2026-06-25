# Cookies

`fluxium/cookies.py`

## CookieJar

```python
class CookieJar(http.cookiejar.CookieJar):
    def __init__(self, cookies: dict | CookieJar | None = None)
```

Dict-like cookie jar backed by Python's `http.cookiejar.CookieJar`.

## Dict Interface

| Operation | Example |
|---|---|
| Set | `jar["session"] = "abc"` |
| Get | `value = jar["session"]` |
| Delete | `del jar["session"]` |
| Contains | `"session" in jar` |
| Get with default | `jar.get("missing", "default")` |

## Methods

| Method | Returns | Description |
|---|---|---|
| `set(name, value, domain="", path="/")` | `None` | Set a cookie |
| `to_dict()` | `dict[str, str]` | `{name: value}` mapping |
| `to_header()` | `str` | Cookie header value |
| `items()` | `list[tuple[str, str]]` | `(name, value)` pairs |
| `keys()` | `list[str]` | Cookie names |
| `values()` | `list[str]` | Cookie values |
| `update(cookies)` | `None` | Merge from dict or CookieJar |
| `get(name, default=None)` | `str \| None` | Get with fallback |
