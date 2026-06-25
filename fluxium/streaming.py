"""Streaming and Server-Sent Events (SSE) support for Fluxium."""

from __future__ import annotations

import contextlib
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from .models import Response


class SSEEvent:
    """A single Server-Sent Events event."""

    __slots__ = ("data", "event", "id", "retry")

    def __init__(
        self,
        event: str = "message",
        data: str = "",
        id: str | None = None,
        retry: int | None = None,
    ):
        self.event = event
        self.data = data
        self.id = id
        self.retry = retry

    def json(self) -> Any:
        return json.loads(self.data)

    def __repr__(self) -> str:
        return f"<SSEEvent [{self.event}] {self.data[:80]}>"


def iter_sse(response: Response) -> Iterator[SSEEvent]:
    """Parse SSE events from a streaming response (sync)."""
    event = SSEEvent()
    for line in response.iter_lines():
        if not line:
            if event.data:
                yield event
                event = SSEEvent()
            continue
        if line.startswith(":"):
            continue
        if ":" in line:
            field, value = line.split(":", 1)
            if value.startswith(" "):
                value = value[1:]
        else:
            field = line
            value = ""
        if field == "event":
            event.event = value
        elif field == "data":
            event.data += value + "\n"
        elif field == "id":
            event.id = value
        elif field == "retry":
            with contextlib.suppress(ValueError):
                event.retry = int(value)
    if event.data:
        yield event


async def aiter_sse(response: Response) -> AsyncIterator[SSEEvent]:
    """Parse SSE events from a streaming response (async)."""
    event = SSEEvent()
    raw = response._raw
    if raw is None:
        return
    async for line in raw.aiter_lines():
        if not line:
            if event.data:
                yield event
                event = SSEEvent()
            continue
        if line.startswith(":"):
            continue
        if ":" in line:
            field, value = line.split(":", 1)
            if value.startswith(" "):
                value = value[1:]
        else:
            field = line
            value = ""
        if field == "event":
            event.event = value
        elif field == "data":
            event.data += value + "\n"
        elif field == "id":
            event.id = value
        elif field == "retry":
            with contextlib.suppress(ValueError):
                event.retry = int(value)
    if event.data:
        yield event


class StreamReader:
    """High-level streaming file download with progress tracking."""

    def __init__(self, response: Response, chunk_size: int = 8192):
        self._response = response
        self._chunk_size = chunk_size
        self._bytes_read = 0
        content_length = response.headers.get("content-length")
        self._total = int(content_length) if content_length else None

    @property
    def bytes_read(self) -> int:
        return self._bytes_read

    @property
    def total(self) -> int | None:
        return self._total

    @property
    def progress(self) -> float | None:
        return self._bytes_read / self._total if self._total else None

    def iter_chunks(self) -> Iterator[bytes]:
        for chunk in self._response.iter_content(chunk_size=self._chunk_size):
            self._bytes_read += len(chunk)
            yield chunk

    def iter_text(self) -> Iterator[str]:
        encoding = self._response._detect_encoding()
        for chunk in self.iter_chunks():
            yield chunk.decode(encoding, errors="replace")

    def save_to(self, path: str | None = None) -> str:
        import os

        if path is None:
            path = self._response.url.split("/")[-1].split("?")[0] or "download"
        with open(path, "wb") as f:
            for chunk in self.iter_chunks():
                f.write(chunk)
        return os.path.abspath(path)
