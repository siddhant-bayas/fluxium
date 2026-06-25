"""Timeout configuration for Fluxium."""

from __future__ import annotations

import httpx


class Timeout:
    """Structured timeout configuration.

    Examples:
        Timeout(30.0)                          # all components 30s
        Timeout(connect=5.0, read=30.0)        # connect 5s, read 30s
        Timeout((5.0, 30.0))                   # connect 5s, read 30s (tuple)
        Timeout(None)                          # no timeout
    """

    __slots__ = ("connect", "pool", "read", "write")

    def __init__(
        self,
        connect: float | tuple | None = 30.0,
        read: float | None = None,
        write: float | None = None,
        pool: float | None = None,
    ):
        if isinstance(connect, tuple):
            self.connect = float(connect[0]) if connect else None
            self.read = float(connect[1]) if len(connect) > 1 else None
            self.write = float(connect[2]) if len(connect) > 2 else None
            self.pool = float(connect[3]) if len(connect) > 3 else None
        elif read is not None or write is not None or pool is not None:
            # Per-component mode: use explicit values, default unset to connect value
            self.connect = float(connect) if connect is not None else None
            self.read = float(read) if read is not None else self.connect
            self.write = float(write) if write is not None else self.connect
            self.pool = float(pool) if pool is not None else self.connect
        else:
            # Single value: all components same
            val = float(connect) if connect is not None else None
            self.connect = val
            self.read = val
            self.write = val
            self.pool = val

    def to_httpx(self) -> httpx.Timeout:
        return httpx.Timeout(
            connect=self.connect,
            read=self.read,
            write=self.write,
            pool=self.pool,
        )

    def __repr__(self) -> str:
        parts = []
        for attr in ("connect", "read", "write", "pool"):
            val = getattr(self, attr)
            if val is not None:
                parts.append(f"{attr}={val}")
        return f"Timeout({', '.join(parts)})"
