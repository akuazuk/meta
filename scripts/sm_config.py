"""Карта Secret Manager для Meta (проект protocol-home-e1).

Имена секретов – kebab-case с префиксом meta-/google-ads-/heygen-,
чтобы не пересечься с секретами Протокола.
Значения в лог и в Git не писать.
"""

from __future__ import annotations

# env var → Secret Manager id
SM_MAP: dict[str, str] = {
    "META_APP_ID": "meta-app-id",
    "META_APP_SECRET": "meta-app-secret",
    "META_ACCESS_TOKEN": "meta-access-token",
    "META_ACCESS_TOKEN_OLD": "meta-access-token-old",
    "META_ACCESS_TOKEN_MRS": "meta-access-token-mrs",
    "META_AD_ACCOUNT_ID": "meta-ad-account-id",
    "META_AD_ACCOUNT_ID_OLD": "meta-ad-account-id-old",
    "META_AD_ACCOUNT_ID_MRS": "meta-ad-account-id-mrs",
    "META_DATASET_ID": "meta-dataset-id",
    "META_DATASET_ID_MRS": "meta-dataset-id-mrs",
    "META_PAGE_ID": "meta-page-id",
    "META_INSTAGRAM_ID": "meta-instagram-id",
    "META_GRAPH_API_VERSION": "meta-graph-api-version",
    "GOOGLE_ADS_CLIENT_ID": "google-ads-client-id",
    "GOOGLE_ADS_CLIENT_SECRET": "google-ads-client-secret",
    "GOOGLE_ADS_REFRESH_TOKEN": "google-ads-refresh-token",
    "GOOGLE_ADS_LOGIN_CUSTOMER_ID": "google-ads-login-customer-id",
    "GOOGLE_ADS_CUSTOMER_ID": "google-ads-customer-id",
    "HEYGEN_API_KEY": "heygen-api-key",
}

# Для модерации комментов на GCE (собирается на VM из SM).
COMMENTS_SM_KEYS: tuple[str, ...] = (
    "META_ACCESS_TOKEN_MRS",
    "META_AD_ACCOUNT_ID_MRS",
    "META_PAGE_ID",
    "META_INSTAGRAM_ID",
    "META_GRAPH_API_VERSION",
)

COMMENTS_PUBLIC: dict[str, str] = {
    "GOOGLE_SHEETS_ID": "1LkaVoEZ7hQWR2FL0Iejjviutdte91SLq9rM7W5u80lU",
    "GOOGLE_APPLICATION_CREDENTIALS": "/opt/kravira-meta-comments/service-account.json",
    "COMMENT_SINCE": "2026-09-01",
    "TZ": "Europe/Minsk",
    "GOOGLE_CLOUD_PROJECT": "protocol-home-e1",
    "GEMINI_MODEL": "gemini-2.5-flash",
    "GEMINI_LOCATION": "europe-west1",
    "COMMENT_USE_GEMINI": "1",
}

GCP_PROJECT = "protocol-home-e1"
