"""Общий клиент Google Ads API без developer token.

С 09.09.2026 уровень доступа (у нас BASIC) висит на Cloud-проекте
OAuth-клиента, не на токене. Заголовок developer-token больше не шлём:
в первой половине 2027 API его перестанет принимать.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=True)

REQUIRED = (
    "GOOGLE_ADS_CLIENT_ID",
    "GOOGLE_ADS_CLIENT_SECRET",
    "GOOGLE_ADS_REFRESH_TOKEN",
    "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
    "GOOGLE_ADS_CUSTOMER_ID",
)


def missing_env() -> list[str]:
    return [k for k in REQUIRED if not (os.getenv(k) or "").strip()]


def customer_id() -> str:
    return os.environ["GOOGLE_ADS_CUSTOMER_ID"].strip().replace("-", "")


def login_customer_id() -> str:
    return os.environ["GOOGLE_ADS_LOGIN_CUSTOMER_ID"].strip().replace("-", "")


def cloud_project_number() -> str:
    """Номер проекта из OAuth Client ID (xxxx-....apps.googleusercontent.com)."""
    cid = (os.getenv("GOOGLE_ADS_CLIENT_ID") or "").strip()
    return cid.split("-", 1)[0] if cid else ""


def load_client() -> GoogleAdsClient:
    missing = missing_env()
    if missing:
        raise SystemExit(
            "[error] Не хватает в .env: "
            + ", ".join(missing)
            + "\nИнструкция: docs/GOOGLE_ADS_SETUP.md"
        )
    return GoogleAdsClient.load_from_dict(
        {
            "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"].strip(),
            "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"].strip(),
            "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"].strip(),
            "login_customer_id": login_customer_id(),
            "use_proto_plus": True,
        }
    )
