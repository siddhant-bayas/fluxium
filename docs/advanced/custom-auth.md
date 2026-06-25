# Custom Auth

Implement custom authentication by subclassing `AuthBase`.

## Template

```python
from fluxium.auth import AuthBase

class MyAuth(AuthBase):
    def __init__(self, key):
        self.key = key

    def __call__(self, request):
        request.headers["X-API-Key"] = self.key
        return request
```

## HMAC Signature

```python
import hashlib
import hmac

class HMACAuth(AuthBase):
    def __init__(self, api_key: str, secret: str):
        self._key = api_key
        self._secret = secret.encode()

    def __call__(self, request):
        body = request.data or b""
        signature = hmac.new(self._secret, body, hashlib.sha256).hexdigest()
        request.headers["X-API-Key"] = self._key
        request.headers["X-Signature"] = signature
        return request
```

## Custom Header Scheme

```python
class CustomSchemeAuth(AuthBase):
    def __init__(self, token: str):
        self._token = token

    def __call__(self, request):
        request.headers["Authorization"] = f"CustomScheme {self._token}"
        return request
```

## Conditional Auth

```python
class ConditionalAuth(AuthBase):
    def __init__(self, auth: AuthBase, condition):
        self._auth = auth
        self._condition = condition

    def __call__(self, request):
        if self._condition(request.url):
            return self._auth(request)
        return request
```

## Registering

```python
s = Session(auth=HMACAuth("my-key", "my-secret"))
s.get("https://api.example.com")  # auth applied automatically
```
