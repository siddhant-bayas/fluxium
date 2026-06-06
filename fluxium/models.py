"""Request and Response models."""
from __future__ import annotations

import json as _json
from typing import Any, Iterator

from .cookies import CookieJar
from .exceptions import HTTPError


class Request:
    """Internal request object used by auth handlers."""

    __slots__ = ("method", "url", "headers", "data", "json", "params", "auth", "cookies")

    def __init__(self, method, url, headers=None, data=None,
                 json=None, params=None, auth=None, cookies=None):
        self.method = method.upper()
        self.url = url
        self.headers = headers or {}
        self.data = data
        self.json = json
        self.params = params
        self.auth = auth
        self.cookies = cookies or CookieJar()

    def __repr__(self):
        return f"<Request [{self.method}] {self.url}>"


class Response:
    """HTTP response.

    Attributes:
        status_code: HTTP status code.
        url: Final URL after redirects.
        headers: Response headers (lowercase keys).
        cookies: Response cookies.
        history: List of redirect responses.
        elapsed: Time elapsed (set by transport).
    """

    __slots__ = (
        "status_code", "url", "headers", "cookies", "_content",
        "encoding", "history", "elapsed", "request", "_raw",
        "_text", "_enc",
    )

    def __init__(self):
        self.status_code: int = 0
        self.url: str = ""
        self.headers: dict = {}
        self.cookies: CookieJar = CookieJar()
        self._content: bytes = b""
        self.encoding: str = "utf-8"
        self.history: list[Response] = []
        self.elapsed = None
        self.request: Request | None = None
        self._raw = None
        self._text: str | None = None
        self._enc: str | None = None

    @property
    def content(self) -> bytes:
        """Raw response body."""
        return self._content

    @property
    def text(self) -> str:
        """Decoded response body. Encoding is auto-detected."""
        if self._text is None:
            self._text = self._content.decode(self._detect_encoding(), errors="replace")
        return self._text

    def _detect_encoding(self) -> str:
        if self._enc is not None:
            return self._enc
        ct = self.headers.get("content-type", "")
        if "charset=" in ct:
            self._enc = ct.split("charset=")[-1].split(";")[0].strip()
            return self._enc
        try:
            self._content.decode("utf-8")
            self._enc = "utf-8"
            return "utf-8"
        except UnicodeDecodeError:
            pass
        try:
            import chardet
            detected = chardet.detect(self._content)
            self._enc = detected.get("encoding") or self.encoding
        except ImportError:
            self._enc = self.encoding
        return self._enc

    def json(self, **kwargs) -> Any:
        """Parse response body as JSON."""
        return _json.loads(self._content, **kwargs)

    def raise_for_status(self) -> None:
        """Raise :class:`HTTPError` if status is 4xx or 5xx."""
        if 400 <= self.status_code < 600:
            raise HTTPError(
                f"HTTP {self.status_code} for url: {self.url}", response=self
            )

    def iter_content(self, chunk_size: int = 8192) -> Iterator[bytes]:
        """Iterate over response body in *chunk_size* bytes at a time."""
        if self._raw is not None:
            yield from self._raw.iter_bytes(chunk_size=chunk_size)
        else:
            for i in range(0, len(self._content), chunk_size):
                yield self._content[i:i + chunk_size]

    def iter_lines(self) -> Iterator[str]:
        """Iterate over response body line by line."""
        enc = self._detect_encoding()
        buf = bytearray()
        for chunk in self.iter_content():
            buf.extend(chunk)
            while b"\n" in buf:
                idx = buf.index(b"\n")
                line = bytes(buf[:idx]).rstrip(b"\r")
                del buf[:idx + 1]
                yield line.decode(enc, errors="replace")
        if buf:
            yield bytes(buf).decode(enc, errors="replace")

    @property
    def ok(self) -> bool:
        return self.status_code < 400

    @property
    def is_redirect(self) -> bool:
        return self.status_code in (301, 302, 303, 307, 308)

    def __bool__(self) -> bool:
        return self.ok

    def __repr__(self) -> str:
        return f"<Response [{self.status_code}]>"
