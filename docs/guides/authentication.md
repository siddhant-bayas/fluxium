# Authentication

## BasicAuth

```python
from fluxium import BasicAuth

r = fluxium.get("https://api.example.com", auth=BasicAuth("user", "pass"))
```

## DigestAuth

Handles the full challenge-response handshake automatically on 401 responses.

```python
from fluxium import DigestAuth

r = fluxium.get("https://api.example.com", auth=DigestAuth("user", "pass"))
```

## BearerAuth

```python
from fluxium import BearerAuth

r = fluxium.get("https://api.example.com", auth=BearerAuth("your-token"))
```

### With Auto-Refresh

```python
def get_new_token():
    # fetch new token from auth server
    return "new-token"

auth = BearerAuth("initial-token", refresh_callback=get_new_token)
r = fluxium.get("https://api.example.com", auth=auth)
```

## OAuth2Auth

Client credentials flow with automatic token management.

```python
from fluxium import OAuth2Auth

auth = OAuth2Auth(
    token_url="https://auth.example.com/token",
    client_id="my-client",
    client_secret="my-secret",
    scope="read write",       # optional
    audience="api",           # optional
)

r = fluxium.get("https://api.example.com", auth=auth)
# Token is fetched automatically, refreshed when expired
```

### With Session

```python
from fluxium import Session, OAuth2Auth

auth = OAuth2Auth(
    token_url="https://auth.example.com/token",
    client_id="my-client",
    client_secret="my-secret",
)

with Session(auth=auth) as s:
    s.get("https://api.example.com")  # token fetched here
    s.get("https://api.example.com")  # token reused
```

## Per-Request Auth (Override Session)

```python
s = Session(auth=BasicAuth("admin", "admin"))
s.get("https://api.example.com", auth=BearerAuth("special-token"))  # overrides
```
