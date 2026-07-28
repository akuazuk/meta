"""Идемпотентное создание тестовой кампании Кравиры в Meta Ads.

Все создаваемые объекты всегда получают статус PAUSED. Скрипт сохраняет
идентификаторы в игнорируемом Git файле tmp_refs/campaign_create_state.json,
поэтому повторный запуск продолжает незавершённую операцию без дубликатов.

Запуск:
    python -m scripts.create_test_campaign --check
    python -m scripts.create_test_campaign --create
    python -m scripts.create_test_campaign --verify
"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

import requests
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.campaign import Campaign
from facebook_business.exceptions import FacebookRequestError

from src.auth.token import debug_token, missing_scopes
from src.config import get_settings, init_api

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "tmp_refs" / "campaign_create_state.json"

CAMPAIGN_NAME = "Kravira | Website Sales | Minsk | 2026-07 | Test"
ADSET_NAME = "Minsk | MRS_Try_180_days | Online Booking | 50 PLN"
LANDING_URL = "https://kravira.by/"
PIXEL_ID = "1524169318700997"
EVENT_NAME = "MRS_FB_onlineBooking"
AUDIENCE_NAME = "MRS_Try_180_days"
CITY_KEY = "283241"

ADS = [
    {
        "name": "01 | Individual approach",
        "image": ROOT / "image" / "concepts" / "final_1_unique.jpg",
        "message": (
            "Каждый пациент – единственный.\n"
            "В Кравире нет «среднего случая»: мы слушаем, разбираемся "
            "и ведём к здоровью бережно и по делу."
        ),
        "headline": "Каждый пациент – единственный",
        "description": "Минск – запись онлайн",
    },
    {
        "name": "02 | Health first",
        "image": ROOT / "image" / "concepts" / "final_2_health.jpg",
        "message": (
            "Здоровье – без шаблонов.\n"
            "25 лет рядом с семьями Минска: когда важно не просто "
            "«принять», а помочь именно вам."
        ),
        "headline": "Ваше здоровье – наша главная цель",
        "description": "3 филиала – 120+ врачей",
    },
    {
        "name": "03 | We hear everyone",
        "image": ROOT / "image" / "concepts" / "final_3_hear.jpg",
        "message": (
            "Мы слышим каждого – потому что путь к здоровью у всех свой.\n"
            "Запишитесь онлайн и начните с главного."
        ),
        "headline": "Мы слышим каждого",
        "description": "Главное – ваше здоровье",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--check",
        action="store_true",
        help="read-only проверка токена, ассетов и delivery estimate",
    )
    action.add_argument(
        "--create",
        action="store_true",
        help="создать или продолжить PAUSED-кампанию",
    )
    action.add_argument(
        "--verify",
        action="store_true",
        help="read-only проверка уже созданных объектов из state-файла",
    )
    return parser.parse_args()


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"ads": {}}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def graph_get(path: str, params: dict | None = None) -> dict:
    settings = get_settings()
    version = getattr(init_api(), "_api_version", "v25.0")
    response = requests.get(
        f"https://graph.facebook.com/{version}/{path.lstrip('/')}",
        headers={"Authorization": f"Bearer {settings.access_token}"},
        params=params or {},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def resolve_assets(account: AdAccount) -> tuple[str, str, str]:
    pages = list(account.get_promote_pages(fields=["id", "name"]))
    if len(pages) != 1:
        raise RuntimeError(f"Expected one promoted Page, found {len(pages)}")
    page_id = pages[0]["id"]

    page_data = graph_get(page_id, {"fields": "instagram_business_account"})
    instagram_id = (page_data.get("instagram_business_account") or {}).get("id")
    if not instagram_id:
        raise RuntimeError("Page has no connected Instagram business account")

    audiences = [
        item
        for item in account.get_custom_audiences(
            fields=["id", "name", "delivery_status"]
        )
        if item.get("name") == AUDIENCE_NAME
    ]
    if len(audiences) != 1:
        raise RuntimeError(
            f"Expected one {AUDIENCE_NAME} audience, found {len(audiences)}"
        )
    delivery = audiences[0].get("delivery_status") or {}
    if delivery.get("code") != 200:
        raise RuntimeError(f"Target audience is not ready: {delivery}")

    return page_id, instagram_id, audiences[0]["id"]


def campaign_params() -> dict:
    return {
        "name": CAMPAIGN_NAME,
        "objective": "OUTCOME_SALES",
        "buying_type": "AUCTION",
        "special_ad_categories": [],
        "is_adset_budget_sharing_enabled": False,
        "status": "PAUSED",
    }


def adset_params(campaign_id: str, audience_id: str) -> dict:
    return {
        "name": ADSET_NAME,
        "campaign_id": campaign_id,
        "daily_budget": 5000,
        "billing_event": "IMPRESSIONS",
        "optimization_goal": "OFFSITE_CONVERSIONS",
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "destination_type": "WEBSITE",
        "promoted_object": {
            "pixel_id": PIXEL_ID,
            "custom_event_type": "OTHER",
            "custom_event_str": EVENT_NAME,
        },
        "targeting": {
            "geo_locations": {"cities": [{"key": CITY_KEY}]},
            "custom_audiences": [{"id": audience_id}],
            "age_min": 18,
            "age_max": 65,
        },
        "attribution_spec": [
            {"event_type": "CLICK_THROUGH", "window_days": 7},
            {"event_type": "VIEW_THROUGH", "window_days": 1},
        ],
        "is_dynamic_creative": False,
        "status": "PAUSED",
    }


def story_spec(spec: dict, image_hash: str, page_id: str, instagram_id: str) -> dict:
    return {
        "page_id": page_id,
        "instagram_user_id": instagram_id,
        "link_data": {
            "image_hash": image_hash,
            "link": LANDING_URL,
            "message": spec["message"],
            "name": spec["headline"],
            "description": spec["description"],
            "call_to_action": {
                "type": "LEARN_MORE",
                "value": {"link": LANDING_URL},
            },
        },
    }


def creative_params(
    spec: dict, image_hash: str, page_id: str, instagram_id: str
) -> dict:
    return {
        "name": f"{spec['name']} | Creative",
        "object_story_spec": story_spec(
            spec, image_hash, page_id, instagram_id
        ),
        "degrees_of_freedom_spec": {
            "creative_features_spec": {
                "standard_enhancements": {"enroll_status": "OPT_OUT"}
            }
        },
    }


def check(account: AdAccount) -> int:
    settings = get_settings()
    info = debug_token()
    if not info.is_valid:
        raise RuntimeError("Access token is invalid")
    gaps = missing_scopes(info)
    if gaps:
        raise RuntimeError(f"Missing scopes: {', '.join(sorted(gaps))}")
    if settings.dataset_id != PIXEL_ID:
        raise RuntimeError("Configured Pixel/Dataset differs from approved ID")

    _, _, audience_id = resolve_assets(account)
    targeting = adset_params("validation-placeholder", audience_id)["targeting"]
    promoted = adset_params("validation-placeholder", audience_id)[
        "promoted_object"
    ]
    estimate = list(
        account.get_delivery_estimate(
            params={
                "optimization_goal": "OFFSITE_CONVERSIONS",
                "promoted_object": promoted,
                "targeting_spec": targeting,
            }
        )
    )
    if not estimate:
        raise RuntimeError("Meta returned no delivery estimate")

    print("[ok] token, Page, Instagram, Pixel, audience, geo and event")
    print("[ok] delivery estimate accepted by Meta")
    print("[info] creative validation happens during --create")
    return 0


def create(account: AdAccount) -> int:
    settings = get_settings()
    if settings.dataset_id != PIXEL_ID:
        raise RuntimeError("Configured Pixel/Dataset differs from approved ID")

    page_id, instagram_id, audience_id = resolve_assets(account)
    state = load_state()

    if "campaign_id" not in state:
        validated = account.create_campaign(
            params={
                **campaign_params(),
                "execution_options": ["validate_only"],
            }
        )
        print(f"[validated] campaign: {dict(validated) or 'ok'}")

        existing = [
            item
            for item in account.get_campaigns(fields=["id", "name", "status"])
            if item.get("name") == CAMPAIGN_NAME
        ]
        if len(existing) > 1:
            raise RuntimeError("Duplicate campaign names found")
        if existing:
            if existing[0].get("status") != "PAUSED":
                raise RuntimeError("Existing campaign is not PAUSED")
            state["campaign_id"] = existing[0]["id"]
            print("[reused] campaign")
        else:
            campaign = account.create_campaign(params=campaign_params())
            state["campaign_id"] = campaign["id"]
            print("[created] campaign")
        save_state(state)

    if "adset_id" not in state:
        params = adset_params(state["campaign_id"], audience_id)
        validated = account.create_ad_set(
            params={**params, "execution_options": ["validate_only"]}
        )
        print(f"[validated] ad set: {dict(validated) or 'ok'}")

        existing = [
            item
            for item in Campaign(state["campaign_id"]).get_ad_sets(
                fields=["id", "name", "status"]
            )
            if item.get("name") == ADSET_NAME
        ]
        if len(existing) > 1:
            raise RuntimeError("Duplicate ad set names found")
        if existing:
            if existing[0].get("status") != "PAUSED":
                raise RuntimeError("Existing ad set is not PAUSED")
            state["adset_id"] = existing[0]["id"]
            print("[reused] ad set")
        else:
            adset = account.create_ad_set(params=params)
            state["adset_id"] = adset["id"]
            print("[created] ad set")
        save_state(state)

    for spec in ADS:
        ad_state = state.setdefault("ads", {}).setdefault(spec["name"], {})

        if "image_hash" not in ad_state:
            encoded = base64.b64encode(spec["image"].read_bytes()).decode("ascii")
            image = account.create_ad_image(params={"bytes": encoded})
            ad_state["image_hash"] = image["hash"]
            save_state(state)
            print(f"[uploaded] {spec['name']} image")

        creative = creative_params(
            spec,
            ad_state["image_hash"],
            page_id,
            instagram_id,
        )
        if "creative_id" not in ad_state:
            validated = account.create_ad_creative(
                params={
                    **creative,
                    "execution_options": ["validate_only"],
                }
            )
            print(f"[validated] {spec['name']} creative: {dict(validated) or 'ok'}")
            result = account.create_ad_creative(params=creative)
            ad_state["creative_id"] = result["id"]
            save_state(state)
            print(f"[created] {spec['name']} creative")

        ad = {
            "name": spec["name"],
            "adset_id": state["adset_id"],
            "creative": {"creative_id": ad_state["creative_id"]},
            "status": "PAUSED",
        }
        if "ad_id" not in ad_state:
            validated = account.create_ad(
                params={**ad, "execution_options": ["validate_only"]}
            )
            print(f"[validated] {spec['name']} ad: {dict(validated) or 'ok'}")
            result = account.create_ad(params=ad)
            ad_state["ad_id"] = result["id"]
            save_state(state)
            print(f"[created] {spec['name']} ad")

    print("[complete] campaign, ad set and three ads are PAUSED")
    return 0


def verify() -> int:
    state = load_state()
    if not state.get("campaign_id") or not state.get("adset_id"):
        raise RuntimeError("State does not contain campaign and ad set IDs")

    campaign = Campaign(state["campaign_id"]).api_get(
        fields=["name", "objective", "status", "effective_status"]
    )
    adset = AdSet(state["adset_id"]).api_get(
        fields=[
            "name",
            "status",
            "effective_status",
            "daily_budget",
            "billing_event",
            "optimization_goal",
            "bid_strategy",
            "destination_type",
            "promoted_object",
            "targeting",
            "attribution_spec",
            "is_dynamic_creative",
        ]
    )
    ads = list(
        AdSet(state["adset_id"]).get_ads(
            fields=["id", "name", "status", "effective_status"]
        )
    )

    if campaign.get("status") != "PAUSED":
        raise RuntimeError("Campaign is not PAUSED")
    if adset.get("status") != "PAUSED":
        raise RuntimeError("Ad set is not PAUSED")
    if len(ads) != len(ADS):
        raise RuntimeError(f"Expected {len(ADS)} ads, found {len(ads)}")
    if any(item.get("status") != "PAUSED" for item in ads):
        raise RuntimeError("At least one ad is not PAUSED")

    print(
        "[campaign]",
        {
            "name": campaign.get("name"),
            "objective": campaign.get("objective"),
            "status": campaign.get("status"),
        },
    )
    print(
        "[ad set]",
        {
            "name": adset.get("name"),
            "status": adset.get("status"),
            "daily_budget": adset.get("daily_budget"),
            "optimization_goal": adset.get("optimization_goal"),
            "destination_type": adset.get("destination_type"),
            "promoted_object": dict(adset.get("promoted_object") or {}),
        },
    )
    print("[ads]", [{"name": item.get("name"), "status": item.get("status")} for item in ads])
    return 0


def main() -> int:
    args = parse_args()
    init_api()
    account = AdAccount(get_settings().ad_account_ref)
    if args.check:
        return check(account)
    if args.create:
        return create(account)
    return verify()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FacebookRequestError as exc:
        error = (exc.body() or {}).get("error", {})
        print(
            "[meta-error]",
            {
                "code": exc.api_error_code(),
                "subcode": exc.api_error_subcode(),
                "title": error.get("error_user_title"),
                "message": error.get("error_user_msg")
                or exc.api_error_message(),
            },
        )
        raise SystemExit(1)
    except (RuntimeError, requests.RequestException) as exc:
        print(f"[error] {exc}")
        raise SystemExit(1)
