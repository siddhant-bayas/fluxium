# OAuth2

Deep-dive into OAuth2 flows with `oauth2.py`.

## Client Credentials Flow

```python
from fluxium import OAuth2Auth

auth = OAuth2Auth(
    token_url="https://auth.example.com/token",
    client_id="my-client",
    client_secret="my-secret",
)
```

Fluxium automatically:
1. Fetches the access token on first request
2. Caches the token until expiry
3. Refreshes when `expires_in` is reached (60s buffer)

## Scopes and Audience

```python
auth = OAuth2Auth(
    token_url="https://auth.example.com/token",
    client_id="my-client",
    client_secret="my-secret",
    scope="read:users write:users",
    audience="https://api.example.com",
)
```

## Token Refresh

If the server returns a `refresh_token`, fluxium uses it automatically:

```python
auth = OAuth2Auth(
    token_url="https://auth.example.com/token",
    client_id="my-client",
    client_secret="my-secret",
)
# On 401, fluxium will POST grant_type=refresh_token if available
```

## BearerAuth with Manual Refresh

For custom refresh logic:

```python
from fluxium import BearerAuth

class TokenManager:
    def __init__(self):
        self.token = None

    def refresh(self):
        # custom logic to get new token
        self.token = fetch_new_token()
        return self.token

mgr = TokenManager()
auth = BearerAuth("initial-token", refresh_callback=mgr.refresh)
```

## Error Handling

```python
from fluxium.exceptions import HTTPError

try:
    r = fluxium.get("https://api.example.com", auth=OAuth2Auth(
        token_url="https://auth.example.com/token",
        client_id="my-client",
        client_secret="my-secret",
    ))
except HTTPError as e:
    if e.response.status_code == 401:
        print("Token expired or invalid")
```
