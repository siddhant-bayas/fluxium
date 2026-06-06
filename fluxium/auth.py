"""Authentication handlers."""
import base64
import hashlib
import os
import re
from urllib.parse import urlparse


class AuthBase:
    """Base class for authentication handlers."""

    def __call__(self, r):
        raise NotImplementedError


class BasicAuth(AuthBase):
    """HTTP Basic authentication (RFC 7617)."""

    __slots__ = ("username", "password")

    def __init__(self, username: str, password: str = ""):
        self.username = username
        self.password = password

    def __call__(self, r):
        token = base64.b64encode(
            f"{self.username}:{self.password}".encode()
        ).decode()
        r.headers["Authorization"] = f"Basic {token}"
        return r

    def __repr__(self) -> str:
        return f"<BasicAuth user={self.username!r}>"


class DigestAuth(AuthBase):
    """HTTP Digest authentication (RFC 7616).

    Handles the full challenge-response handshake automatically.
    Supports MD5, MD5-sess algorithms and auth/auth-int QoP.
    """

    __slots__ = ("username", "password", "_last_nonce", "_nc", "_cnonce")

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self._last_nonce = None
        self._nc = 0
        self._cnonce = None

    def _parse_challenge(self, header: str) -> dict[str, str]:
        parts = {}
        header = header[len("Digest "):].strip()
        for m in re.finditer(r'(\w+)=["\']?([^\"\'`,]+)["\']?', header):
            parts[m.group(1)] = m.group(2).strip()
        return parts

    def _ha1(self, realm: str, algorithm: str) -> str:
        h = f"{self.username}:{realm}:{self.password}"
        if algorithm and "MD5-sess" in algorithm.upper():
            return hashlib.md5(
                f"{hashlib.md5(h.encode()).hexdigest()}:{self._last_nonce}:{self._cnonce}".encode()
            ).hexdigest()
        return hashlib.md5(h.encode()).hexdigest()

    def _ha2(self, method: str, uri: str) -> str:
        return hashlib.md5(f"{method}:{uri}".encode()).hexdigest()

    def build_header(self, method: str, url: str, challenge_header: str) -> str:
        ch = self._parse_challenge(challenge_header)
        realm = ch.get("realm", "")
        nonce = ch.get("nonce", "")
        qop = ch.get("qop", "")
        algorithm = ch.get("algorithm", "MD5")
        opaque = ch.get("opaque", "")
        self._last_nonce = nonce
        self._cnonce = hashlib.md5(os.urandom(8)).hexdigest()[:8]
        self._nc += 1
        nc_str = f"{self._nc:08x}"
        uri = urlparse(url).path or "/"
        ha1 = self._ha1(realm, algorithm)
        ha2 = self._ha2(method, uri)
        if qop in ("auth", "auth-int"):
            resp = hashlib.md5(
                f"{ha1}:{nonce}:{nc_str}:{self._cnonce}:{qop}:{ha2}".encode()
            ).hexdigest()
            hdr = (
                f'Digest username="{self.username}", realm="{realm}", '
                f'nonce="{nonce}", uri="{uri}", qop={qop}, '
                f'nc={nc_str}, cnonce="{self._cnonce}", response="{resp}"'
            )
        else:
            resp = hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()
            hdr = (
                f'Digest username="{self.username}", realm="{realm}", '
                f'nonce="{nonce}", uri="{uri}", response="{resp}"'
            )
        if opaque:
            hdr += f', opaque="{opaque}"'
        return hdr

    def __call__(self, r):
        # Digest auth is handled by Session on 401 responses
        return r

    def __repr__(self) -> str:
        return f"<DigestAuth user={self.username!r}>"
