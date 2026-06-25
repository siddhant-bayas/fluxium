# File Uploads

## Single File

```python
import fluxium

with open("photo.jpg", "rb") as f:
    r = fluxium.post("https://api.example.com/upload", files={"file": ("photo.jpg", f, "image/jpeg")})
```

## Multiple Files

```python
with open("photo1.jpg", "rb") as f1, open("photo2.jpg", "rb") as f2:
    r = fluxium.post("https://api.example.com/upload", files={
        "photo1": ("photo1.jpg", f1, "image/jpeg"),
        "photo2": ("photo2.jpg", f2, "image/jpeg"),
    })
```

## With Form Fields

```python
with open("document.pdf", "rb") as f:
    r = fluxium.post("https://api.example.com/upload", data={
        "title": "My Document",
        "category": "reports",
    }, files={"file": ("document.pdf", f, "application/pdf")})
```

## BytesIO (In-Memory)

```python
import io

fake_file = io.BytesIO(b"Hello fluxium file upload!")
r = fluxium.post("https://api.example.com/upload", files={"file": ("hello.txt", fake_file, "text/plain")})
```

## Content-Type Auto-Detect

If you omit the content type, fluxium guesses from the filename:

```python
files = {"file": ("report.pdf", fileobj)}  # Guesses application/pdf
files = {"file": ("data.json", fileobj)}   # Guesses application/json
files = {"file": ("image", fileobj)}       # Falls back to application/octet-stream
```
