# Custom Transport

Fluxium wraps httpx. You can customize the underlying transport.

## Custom httpx Client

```python
import httpx
from fluxium import Session

# Create your own httpx.Client
custom_client = httpx.Client(
    http2=True,
    limits=httpx.Limits(max_connections=500),
    transport=httpx.HTTPTransport(retries=2),
)

# Use it with fluxium
s = Session()
s._client = custom_client  # replace the default client
```

## Custom Proxy Transport

```python
import httpx

proxy_transport = httpx.HTTPTransport(
    proxy=httpx.Proxy("http://proxy:8080"),
    verify=False,
)
```

## Custom SSL Context

```python
import ssl
import httpx

ctx = ssl.create_default_context()
ctx.minimum_version = ssl.TLSVersion.TLSv1_3
ctx.load_cert_chain("client.crt", "client.key")

transport = httpx.HTTPTransport(verify=ctx)
```

## Custom HTTP/2 Settings

```python
import httpx

# httpx handles HTTP/2 internally
# Just ensure http2=True (default)
s = Session(http2=True)
```

## Note

Custom transports are advanced. For most use cases, the default configuration is sufficient. The default pool is 200 connections with 100 keep-alive.
