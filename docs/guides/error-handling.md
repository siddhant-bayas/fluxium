# Error Handling

## Exception Hierarchy

```
FluxiumError
├── ConnectionError
│   ├── SSLError
│   └── ProxyError
├── TimeoutError
├── HTTPError
└── TooManyRedirects
```

## raise_for_status

```python
r = fluxium.get("https://api.example.com/missing")
try:
    r.raise_for_status()
except fluxium.HTTPError as e:
    print(f"HTTP {e.response.status_code}: {e.response.text}")
```

## Catching Specific Errors

```python
from fluxium.exceptions import TimeoutError, ConnectionError, HTTPError

try:
    r = fluxium.get("https://api.example.com", timeout=5)
except TimeoutError:
    print("Request timed out")
except ConnectionError:
    print("Connection failed")
except HTTPError as e:
    print(f"HTTP {e.response.status_code}")
    print(e.response.json())  # parse error body
```

## With Retries

```python
from fluxium import Session

with Session(max_retries=3, retry_backoff=0.5) as s:
    # Retries automatically on 500, 502, 503, 504, timeout, connection error
    r = s.get("https://api.example.com/flaky-endpoint")
```

## Graceful Degradation

```python
def get_with_fallback(url, fallback_url=None):
    try:
        with fluxium.Session(timeout=5) as s:
            r = s.get(url)
            r.raise_for_status()
            return r.json()
    except Exception:
        if fallback_url:
            with fluxium.Session(timeout=5) as s:
                return s.get(fallback_url).json()
        return None
```

## HTTPError Attributes

```python
try:
    r = fluxium.get("https://api.example.com/forbidden")
    r.raise_for_status()
except fluxium.HTTPError as e:
    e.response          # fluxium.Response object
    e.response.status_code  # 403
    e.response.json()       # parse error body
    e.response.headers      # response headers
```
