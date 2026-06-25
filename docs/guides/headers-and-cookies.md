# Headers and Cookies

## Headers

Headers are lowercased by default. Duplicates are overwritten (last wins).

```python
from fluxium import Session

# Session headers (sent with every request)
s = Session(headers={"Authorization": "Bearer xxx", "Accept": "application/json"})

# Per-request headers (merged with session headers)
s.get("https://api.example.com", headers={"X-Request-ID": "abc123"})
```

## CookieJar

Fluxium's `CookieJar` wraps Python's `http.cookiejar.CookieJar` with a dict-like interface.

```python
from fluxium import CookieJar

# Create from dict
jar = CookieJar({"session": "abc", "lang": "en"})

# Dict operations
jar["theme"] = "dark"       # set
value = jar["theme"]        # get
del jar["theme"]            # delete
"session" in jar            # contains

# Utility methods
jar.to_dict()     # {"session": "abc", "lang": "en"}
jar.to_header()  # "session=abc; lang=en"
jar.keys()        # ["session", "lang"]
jar.values()      # ["abc", "en"]
jar.items()       # [("session", "abc"), ("lang", "en")]
```

## Cookie Domain

```python
from fluxium.cookies import CookieJar

jar = CookieJar()
jar.set("session", "abc", domain="example.com", path="/")
```

## Session Cookies

```python
from fluxium import Session, CookieJar

# Method 1: Session with cookie dict
s = Session(cookies={"session": "abc"})

# Method 2: Session with CookieJar
jar = CookieJar({"session": "abc"})
s = Session(cookies=jar)

# Method 3: Per-request cookies
s.get("https://api.example.com", cookies={"extra": "value"})
```

## Automatic Cookie Persistence

```python
with Session() as s:
    s.get("https://api.example.com/login")    # Set-Cookie: session=abc
    s.get("https://api.example.com/profile")  # Cookie: session=abc (auto)
```
