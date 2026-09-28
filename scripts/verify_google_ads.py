"""Read-only проверка доступа Google Ads API.

Запуск:
    source .venv/bin/activate
    python -m scripts.verify_google_ads
"""

from __future__ import annotations

import importlib.metadata

from google.ads.googleads.errors import GoogleAdsException

from scripts.google_ads_client import (
    cloud_project_number,
    customer_id as env_customer_id,
    load_client,
    login_customer_id as env_login_id,
    missing_env,
)


def main() -> int:
    if missing_env():
        print("[error] Не хватает в .env:", ", ".join(missing_env()))
        print("Инструкция: docs/GOOGLE_ADS_SETUP.md")
        return 1

    customer_id = env_customer_id()
    login_id = env_login_id()
    client = load_client()
    ga = client.get_service("GoogleAdsService")
    lib_ver = importlib.metadata.version("google-ads")
    project = cloud_project_number()

    print("Проверка Google Ads API (только чтение)\n")
    print(f"[info] google-ads {lib_ver}, developer-token header не отправляем")
    print(f"[info] Cloud project number {project} (BASIC с 09.09.2026)")
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
            print(" ", err.error_code, err.message)
        print("\nСм. docs/GOOGLE_ADS_SETUP.md")
        return 2

    print("\nДоступ на чтение OK. Production-аккаунт отвечает – уровень не Test.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
