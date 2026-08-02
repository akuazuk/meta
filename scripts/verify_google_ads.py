"""Read-only проверка доступа Google Ads API.

Запуск:
    source .venv/bin/activate
    python -m scripts.verify_google_ads
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

REQUIRED = [
    "GOOGLE_ADS_DEVELOPER_TOKEN",
    "GOOGLE_ADS_CLIENT_ID",
    "GOOGLE_ADS_CLIENT_SECRET",
    "GOOGLE_ADS_REFRESH_TOKEN",
    "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
    "GOOGLE_ADS_CUSTOMER_ID",
]


def main() -> int:
    missing = [k for k in REQUIRED if not (os.getenv(k) or "").strip()]
    if missing:
        print("[error] Не хватает в .env:", ", ".join(missing))
        print("Инструкция: docs/GOOGLE_ADS_SETUP.md")
        return 1

    customer_id = os.environ["GOOGLE_ADS_CUSTOMER_ID"].strip().replace("-", "")
    login_id = os.environ["GOOGLE_ADS_LOGIN_CUSTOMER_ID"].strip().replace("-", "")
    client = GoogleAdsClient.load_from_dict(
        {
            "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"].strip(),
            "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"].strip(),
            "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"].strip(),
            "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"].strip(),
            "login_customer_id": login_id,
            "use_proto_plus": True,
        }
    )
    ga = client.get_service("GoogleAdsService")

    print("Проверка Google Ads API (только чтение)\n")
    try:
        for batch in ga.search_stream(
            customer_id=customer_id,
            query="""
              SELECT customer.id, customer.descriptive_name, customer.currency_code,
                     customer.time_zone, customer.manager, customer.status
              FROM customer
              LIMIT 1
            """,
        ):
            for row in batch.results:
                c = row.customer
                print(
                    "[ok] customer",
                    {
                        "id": c.id,
                        "name": c.descriptive_name,
                        "currency": c.currency_code,
                        "tz": c.time_zone,
                        "manager": c.manager,
                        "status": c.status.name,
                    },
                )

        names = (
            client.get_service("CustomerService")
            .list_accessible_customers()
            .resource_names
        )
        ids = [n.split("/")[-1] for n in names]
        print("[ok] accessible_customers", len(ids))
        print("[ok] target_in_list", customer_id in ids)
        print("[ok] mcc_in_list", login_id in ids)

        n = 0
        for batch in ga.search_stream(
            customer_id=customer_id,
            query="""
              SELECT campaign.id, campaign.name, campaign.status
              FROM campaign
              ORDER BY campaign.id DESC
              LIMIT 5
            """,
        ):
            for row in batch.results:
                n += 1
                print(
                    "[campaign]",
                    row.campaign.id,
                    row.campaign.status.name,
                    row.campaign.name,
                )
        print(f"[ok] campaigns_shown={n}")
    except GoogleAdsException as ex:
        print("[error] Google Ads API")
        for err in ex.failure.errors:
            print(" ", err.message)
        print("\nСм. docs/GOOGLE_ADS_SETUP.md")
        return 2

    print("\nДоступ на чтение OK. Создание/правка – через будущий контур mutate;")
    print("права агентства на create/edit уже подтверждены ранее (validate_only).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
