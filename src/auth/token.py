"""Работа с токенами доступа: обмен и диагностика.

Полезно на старте, чтобы:
  * обменять короткоживущий user-токен на долгоживущий;
  * проверить срок жизни и набор прав (scopes) текущего токена.

Для боевой автоматизации используйте долгоживущий токен System User из
Business Manager — он не привязан к сроку жизни личной сессии.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import requests

from src.config import get_settings

_GRAPH = "https://graph.facebook.com"


def _base_url() -> str:
    version = get_settings().graph_api_version
    return f"{_GRAPH}/{version}" if version else _GRAPH


def exchange_for_long_lived(short_lived_token: str) -> str:
    """Меняет короткоживущий user-токен на долгоживущий (~60 дней)."""
    settings = get_settings()
    resp = requests.get(
        f"{_base_url()}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": settings.app_id,
            "client_secret": settings.app_secret,
            "fb_exchange_token": short_lived_token,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


@dataclass
class TokenInfo:
    is_valid: bool
    app_id: str | None
    type: str | None
    expires_at: datetime | None
    scopes: list[str]
    raw: dict

    @property
    def never_expires(self) -> bool:
        return self.expires_at is None

    def summary(self) -> str:
        exp = "не истекает (System User)" if self.never_expires else self.expires_at.isoformat()
        return (
            f"valid={self.is_valid} type={self.type} app_id={self.app_id}\n"
            f"expires_at={exp}\n"
            f"scopes={', '.join(self.scopes) or '—'}"
        )


def debug_token(token: str | None = None) -> TokenInfo:
    """Диагностика токена через /debug_token (app access token = app_id|app_secret)."""
    settings = get_settings()
    input_token = token or settings.access_token
    resp = requests.get(
        f"{_base_url()}/debug_token",
        params={
            "input_token": input_token,
            "access_token": f"{settings.app_id}|{settings.app_secret}",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json().get("data", {})

    expires_raw = data.get("expires_at")
    expires_at = (
        datetime.fromtimestamp(expires_raw, tz=timezone.utc)
        if expires_raw and expires_raw > 0
        else None
    )
    return TokenInfo(
        is_valid=bool(data.get("is_valid")),
        app_id=data.get("app_id"),
        type=data.get("type"),
        expires_at=expires_at,
        scopes=data.get("scopes", []),
        raw=data,
    )


REQUIRED_SCOPES = {
    "ads_management",
    "ads_read",
    "business_management",
    "leads_retrieval",
}


def missing_scopes(info: TokenInfo) -> set[str]:
    """Каких прав из рекомендованного набора не хватает токену."""
    return REQUIRED_SCOPES - set(info.scopes)
