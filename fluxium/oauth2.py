"""
Advanced authentication: OAuth2, Bearer tokens, and auto-refresh.
"""
from __future__ import annotations

import time
from typing import Any, Callable

from .auth import AuthBase
from .models import Request


class BearerAuth(AuthBase):
    """Bearer token authentication with optional auto-refresh."""

    def __init__(
        self,
        token: str,
        *,
        refresh_token: str | None = None,
        refresh_url: str | None = None,
        refresh_callback: Callable[[], str] | None = None,
        token_type: str = "Bearer",
    ):
        self._token = token
        self._refresh_token = refresh_token
        self._refresh_url = refresh_url
        self._refresh_callback = refresh_callback
        self._token_type = token_type

    @property
    def token(self) -> str:
        return self._token

    def __call__(self, r: Request) -> Request:
        r.headers["Authorization"] = f"{self._token_type} {self._token}"
        return r

    def refresh(self, client=None) -> str:
        """Refresh the access token. Returns the new token."""
        if self._refresh_callback:
            self._token = self._refresh_callback()
        elif self._refresh_url and client:
            import fluxium
            resp = fluxium.post(
                self._refresh_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                },
            )
            data = resp.json()
            self._token = data["access_token"]
            if "refresh_token" in data:
                self._refresh_token = data["refresh_token"]
        return self._token


class OAuth2Auth(AuthBase):
    """OAuth2 client credentials flow with automatic token management."""

    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        *,
        scope: str | None = None,
        audience: str | None = None,
    ):
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope
        self._audience = audience
        self._access_token: str | None = None
        self._token_expires: float = 0
        self._refresh_token: str | None = None

    def _fetch_token(self) -> None:
        import fluxium

        data = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        if self._scope:
            data["scope"] = self._scope
        if self._audience:
            data["audience"] = self._audience

        resp = fluxium.post(self._token_url, data=data)
        token_data = resp.json()
        self._access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self._token_expires = time.time() + expires_in - 60  # 60s buffer
        self._refresh_token = token_data.get("refresh_token")

    def _ensure_token(self) -> None:
        if not self._access_token or time.time() >= self._token_expires:
            if self._refresh_token:
                self._refresh()
            else:
                self._fetch_token()

    def _refresh(self) -> None:
        import fluxium

        resp = fluxium.post(
            self._token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        token_data = resp.json()
        self._access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self._token_expires = time.time() + expires_in - 60

    def __call__(self, r: Request) -> Request:
        self._ensure_token()
        r.headers["Authorization"] = f"Bearer {self._access_token}"
        return r
