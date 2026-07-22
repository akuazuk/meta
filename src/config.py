"""Загрузка настроек и инициализация Meta Marketing API.

Все секреты берутся из переменных окружения (файл .env локально).
В код секреты не кладём.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi

load_dotenv()


class ConfigError(RuntimeError):
    """Не хватает обязательной переменной окружения."""


def _get(name: str, *, required: bool = False, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is not None:
        value = value.strip()
    if required and not value:
        raise ConfigError(
            f"Не задана обязательная переменная окружения {name}. "
            f"Скопируйте .env.example в .env и заполните значения."
        )
    return value or None


@dataclass(frozen=True)
class Settings:
    app_id: str
    app_secret: str
    access_token: str
    ad_account_id: str | None
    dataset_id: str | None
    test_event_code: str | None
    graph_api_version: str | None

    @property
    def ad_account_ref(self) -> str | None:
        """ID рекламного аккаунта в форме act_XXXX (как требует SDK)."""
        if not self.ad_account_id:
            return None
        return self.ad_account_id if self.ad_account_id.startswith("act_") else f"act_{self.ad_account_id}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_id=_get("META_APP_ID", required=True),
        app_secret=_get("META_APP_SECRET", required=True),
        access_token=_get("META_ACCESS_TOKEN", required=True),
        ad_account_id=_get("META_AD_ACCOUNT_ID"),
        dataset_id=_get("META_DATASET_ID"),
        test_event_code=_get("META_TEST_EVENT_CODE"),
        graph_api_version=_get("META_GRAPH_API_VERSION"),
    )


@lru_cache(maxsize=1)
def init_api() -> FacebookAdsApi:
    """Инициализирует и возвращает singleton FacebookAdsApi."""
    settings = get_settings()
    kwargs: dict[str, str] = {}
    if settings.graph_api_version:
        kwargs["api_version"] = settings.graph_api_version
    FacebookAdsApi.init(
        app_id=settings.app_id,
        app_secret=settings.app_secret,
        access_token=settings.access_token,
        **kwargs,
    )
    return FacebookAdsApi.get_default_api()
