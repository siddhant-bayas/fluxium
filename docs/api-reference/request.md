# Request

`fluxium/models.py`

## Signature

```python
class Request:
    def __init__(
        self,
        method: str,
        url: str,
        headers: dict | None = None,
        data: Any = None,
        json: Any = None,
        params: dict | None = None,
        auth: AuthBase | None = None,
        cookies: CookieJar | None = None,
    )
```

## Attributes

| Attribute | Type | Description |
|---|---|---|
| `method` | `str` | Uppercased HTTP method |
| `url` | `str` | Full URL |
| `headers` | `dict` | Request headers |
| `data` | `Any` | Request body |
| `json` | `Any` | JSON body |
| `params` | `dict \| None` | Query parameters |
| `auth` | `AuthBase \| None` | Auth handler |
| `cookies` | `CookieJar` | Request cookies |

## Slots

```python
__slots__ = ("method", "url", "headers", "data", "json", "params", "auth", "cookies")
```

## Note

`Request` is primarily internal — used by auth handlers and middleware. You typically don't create it directly.
