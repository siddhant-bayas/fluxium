# Auth

`fluxium/auth.py`

## AuthBase

```python
class AuthBase:
    def __call__(self, r: Request) -> Request
```

Base class for all auth handlers. Subclass and override `__call__`.

## BasicAuth

```python
class BasicAuth(AuthBase):
    def __init__(self, username: str, password: str = "")
```

HTTP Basic authentication (RFC 7617). Sets `Authorization: Basic <base64>`.

## DigestAuth

```python
class DigestAuth(AuthBase):
    def __init__(self, username: str, password: str)
```

HTTP Digest authentication (RFC 7616). Handles full challenge-response handshake.

### Methods

| Method | Returns | Description |
|---|---|---|
| `build_header(method, url, challenge_header)` | `str` | Build the Digest Authorization header |

The Session automatically calls this on 401 responses.
