# Request Body

## JSON

```python
import fluxium

r = fluxium.post("https://api.example.com", json={"name": "widget", "price": 9.99})
# Content-Type: application/json (auto-set)
```

## Form Data

```python
r = fluxium.post("https://api.example.com", data={"username": "alice", "age": "30"})
# Content-Type: application/x-www-form-urlencoded (auto-set)
```

## Raw Bytes

```python
r = fluxium.post("https://api.example.com", data=b"raw binary content")
```

## String

```python
r = fluxium.post("https://api.example.com", data="plain text content")
# Encoded to bytes, no Content-Type set
```

## Generators (Chunked Transfer)

```python
def body_gen():
    yield b"chunk1-"
    yield b"chunk2-"
    yield b"chunk3"

r = fluxium.post("https://api.example.com", data=body_gen(), chunked=True)
# Transfer-Encoding: chunked (auto-set)
```

## No Body

```python
r = fluxium.get("https://api.example.com")  # No body
r = fluxium.head("https://api.example.com")  # No body
```
