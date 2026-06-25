# Proxies

## Single Proxy

```python
s = fluxium.Session(proxies="http://proxy.example.com:8080")
```

## Per-Scheme Proxies

```python
s = fluxium.Session(proxies={
    "http://": "http://proxy.example.com:8080",
    "https://": "https://proxy.example.com:8443",
})
```

## SOCKS Proxy

Requires `httpx-socks`:

```bash
pip install "fluxium[socks]"
```

```python
s = fluxium.Session(proxies="socks5://localhost:1080")
s = fluxium.Session(proxies="socks4://localhost:1080")
```

## Environment Variables

Fluxium reads proxy settings from environment variables:

```bash
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="https://proxy.example.com:8443"
export NO_PROXY="localhost,127.0.0.1"
```

Disable with:

```python
s = fluxium.Session(trust_env=False)
```

## Per-Request Proxy

```python
s = Session()
s.get("https://api.example.com", proxies="http://other-proxy:8080")
```
