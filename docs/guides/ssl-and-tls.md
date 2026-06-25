# SSL and TLS

## Default Verification

```python
# Default: verify=True
s = Session()  # TLS verification enabled
s = Session(verify=True)  # explicit
```

## Disable Verification

Not recommended for production.

```python
s = Session(verify=False)
```

## Custom CA Bundle

```python
s = Session(verify="/path/to/ca-bundle.crt")
```

## Client Certificates

```python
import ssl

# Via httpx's SSL context
ctx = ssl.create_default_context()
ctx.load_cert_chain("client.crt", "client.key")
s = Session(verify=ctx)
```

## TLS Minimum Version

```python
import ssl

ctx = ssl.create_default_context()
ctx.minimum_version = ssl.TLSVersion.TLSv1_2
s = Session(verify=ctx)
```

## Checking TLS Status

```python
r = fluxium.get("https://api.example.com")
# httpx stores SSL info on the raw response
```
