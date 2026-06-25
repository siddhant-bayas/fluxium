# Exceptions

`fluxium/exceptions.py`

## Hierarchy

```
FluxiumError
├── ConnectionError
│   ├── SSLError
│   └── ProxyError
├── TimeoutError
├── HTTPError
└── TooManyRedirects
```

## FluxiumError

Base exception for all fluxium errors.

## ConnectionError

Failed to establish a connection.

### SSLError

SSL/TLS handshake or certificate verification failed.

### ProxyError

Proxy connection failed.

## TimeoutError

Request timed out.

## HTTPError

HTTP response with 4xx or 5xx status code.

```python
class HTTPError(FluxiumError):
    def __init__(self, msg: str = "", response: Response | None = None)
```

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `response` | `Response \| None` | The error response |

## TooManyRedirects

Exceeded the maximum number of redirects (default 30).
