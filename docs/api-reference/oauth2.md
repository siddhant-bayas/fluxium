# OAuth2

`fluxium/oauth2.py`

## BearerAuth

```python
class BearerAuth(AuthBase):
    def __init__(
        self,
        token: str,
        *,
        refresh_token: str | None = None,
        refresh_url: str | None = None,
        refresh_callback: Callable[[], str] | None = None,
        token_type: str = "Bearer",
    )
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `token` | `str` | Access token |
| `refresh_token` | `str \| None` | Refresh token |
| `refresh_url` | `str \| None` | URL to refresh the token |
| `refresh_callback` | `Callable \| None` | Called to get a new token |
| `token_type` | `str` | Token type (default "Bearer") |

### Methods

| Method | Returns | Description |
|---|---|---|
| `token` (property) | `str` | Current token |
| `refresh(client=None)` | `str` | Refresh the access token |

## OAuth2Auth

```python
class OAuth2Auth(AuthBase):
    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        *,
        scope: str | None = None,
        audience: str | None = None,
    )
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `token_url` | `str` | OAuth2 token endpoint |
| `client_id` | `str` | Client ID |
| `client_secret` | `str` | Client secret |
| `scope` | `str \| None` | Requested scope |
| `audience` | `str \| None` | Token audience |

Automatically fetches and refreshes tokens. Uses 60s buffer before expiry.
