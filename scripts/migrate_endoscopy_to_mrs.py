"""Перенос кампании Эндоскопия (активная ad set + active ads) OLD → NEW.

1. Загружает custom audience из CSV (PHONE, FN, LN).
2. Создаёт PAUSED campaign / ad set / ads в MRS ad account.
3. Копирует креативы (скачивает изображения из OLD, заливает в NEW).

Запуск:
    python -m scripts.migrate_endoscopy_to_mrs --check
    python -m scripts.migrate_endoscopy_to_mrs --apply
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import re
import sys
import time
from copy import deepcopy
from pathlib import Path

import requests

from src.config import ConfigError, get_mrs_settings

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "tmp_refs" / "migrate_endoscopy_mrs.json"

CSV_PATH = Path("/Users/pavelkuzauka/Jupyter_2/PL/fgds_26.csv")
AUDIENCE_NAME = "fgds_26.csv"

OLD_CAMPAIGN_ID = "120239073773890770"
OLD_ADSET_ID = "120250631214700770"
OLD_AD_IDS = [
    "120250718804500770",
    "120250718861560770",
    "120250718878370770",
    "120250718870010770",
]

NEW_PIXEL = "1064023126171171"
PAGE_ID = "265643990153763"
IG_ID = "17841404399569974"

CAMPAIGN_NAME = "MRS_Эндоскопия"
ADSET_NAME = "MRS_ФГДС_Сайт__FORMAT_FIX_2026-08-10"

BATCH_SIZE = 10_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    return parser.parse_args()


def load_env_old() -> dict[str, str]:
    from dotenv import dotenv_values

    env = dotenv_values(ROOT / ".env")
    return {
        "token": env["META_ACCESS_TOKEN_OLD"],
        "account": env["META_AD_ACCOUNT_ID_OLD"],
        "version": env.get("META_GRAPH_API_VERSION") or "v25.0",
    }


def graph(token: str, version: str, method: str, path: str, **kwargs) -> dict:
    url = f"https://graph.facebook.com/{version}/{path.lstrip('/')}"
    if method == "GET":
        kwargs.setdefault("params", {})["access_token"] = token
    else:
        kwargs.setdefault("data", {})["access_token"] = token
        if "json" in kwargs:
            kwargs["params"] = {"access_token": token}
    response = requests.request(method, url, timeout=120, **kwargs)
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"Meta non-JSON {path}: {response.text[:400]}") from exc
    if response.status_code != 200:
        err = payload.get("error", {})
        raise RuntimeError(err.get("error_user_msg") or err.get("message") or str(payload))
    return payload


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_phone(raw: str) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return None
    if digits.startswith("80") and len(digits) >= 11:
        digits = "375" + digits[2:]
    if not digits.startswith("375"):
        return None
    return digits


def normalize_name(value: str) -> str | None:
    if not value:
        return None
    cleaned = value.strip().lower()
    return cleaned or None


def read_audience_rows(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            phone = normalize_phone(row.get("phone", ""))
            fn = normalize_name(row.get("fn", ""))
            ln = normalize_name(row.get("ln", ""))
            if not phone:
                continue
            rows.append(
                [
                    sha256_text(phone),
                    sha256_text(fn) if fn else "",
                    sha256_text(ln) if ln else "",
                ]
            )
    return rows


def strip_ids(obj):
    if isinstance(obj, dict):
        out = {}
        for key, value in obj.items():
            if key == "id":
                continue
            out[key] = strip_ids(value)
        return out
    if isinstance(obj, list):
        return [strip_ids(item) for item in obj]
    return obj


def clean_link(url: str) -> str:
    return url.split("?", 1)[0] if url else url


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def find_audience_by_name(mrs, name: str) -> str | None:
    version = mrs.graph_api_version or "v25.0"
    payload = graph(
        mrs.access_token,
        version,
        "GET",
        f"{mrs.ad_account_ref}/customaudiences",
        params={"fields": "id,name", "limit": 200},
    )
    for item in payload.get("data", []):
        if item.get("name") == name:
            return item["id"]
    return None


def upload_audience(mrs, rows: list[list[str]]) -> str:
    state = load_state()
    if state.get("audience_id"):
        print(f"[reused] audience {state['audience_id']}")
    else:
        audience_id = find_audience_by_name(mrs, AUDIENCE_NAME)
        if audience_id:
            print(f"[reused] existing audience {audience_id} ({AUDIENCE_NAME})")
            state["audience_id"] = audience_id
            save_state(state)
        else:
            created = graph(
                mrs.access_token,
                mrs.graph_api_version or "v25.0",
                "POST",
                f"{mrs.ad_account_ref}/customaudiences",
                data={
                    "name": AUDIENCE_NAME,
                    "subtype": "CUSTOM",
                    "customer_file_source": "USER_PROVIDED_ONLY",
                    "description": "FGDS/endoscopy list migrated from OLD endoskop_26.csv",
                },
            )
            audience_id = created["id"]
            print(f"[created] audience {audience_id} ({AUDIENCE_NAME})")
            state["audience_id"] = audience_id
            save_state(state)

    audience_id = state["audience_id"]
    if state.get("audience_uploaded"):
        print(f"[reused] audience users already uploaded")
        return audience_id

    version = mrs.graph_api_version or "v25.0"
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        result = graph(
            mrs.access_token,
            version,
            "POST",
            f"{audience_id}/users",
            data={
                "payload": json.dumps(
                    {
                        "schema": ["PHONE", "FN", "LN"],
                        "data": batch,
                    }
                ),
            },
        )
        print(f"[uploaded] users batch {i // BATCH_SIZE + 1}: {result.get('num_received', len(batch))}")

    state["audience_uploaded"] = True
    save_state(state)
    return audience_id


def fetch_old_adset(old: dict) -> dict:
    return graph(
        old["token"],
        old["version"],
        "GET",
        OLD_ADSET_ID,
        params={
            "fields": "id,name,campaign_id,daily_budget,lifetime_budget,billing_event,optimization_goal,bid_strategy,bid_amount,promoted_object,targeting,destination_type,attribution_spec,is_dynamic_creative,pacing_type",
        },
    )


def fetch_old_creative(old: dict, ad_id: str) -> tuple[str, dict]:
    ad = graph(
        old["token"],
        old["version"],
        "GET",
        ad_id,
        params={"fields": "id,name,creative"},
    )
    creative_id = ad["creative"]["id"]
    creative = graph(
        old["token"],
        old["version"],
        "GET",
        creative_id,
        params={
            "fields": "name,object_story_spec,asset_feed_spec,degrees_of_freedom_spec,call_to_action_type",
        },
    )
    return ad["name"], creative


def collect_hashes(creative: dict) -> set[str]:
    afs = creative.get("asset_feed_spec") or {}
    return {img["hash"] for img in afs.get("images", []) if img.get("hash")}


def resolve_image_urls(old: dict, hashes: set[str]) -> dict[str, str]:
    payload = graph(
        old["token"],
        old["version"],
        "GET",
        f"act_{old['account']}/adimages",
        params={"hashes": json.dumps(list(hashes)), "fields": "hash,url,name"},
    )
    return {item["hash"]: item["url"] for item in payload.get("data", []) if item.get("url")}


def upload_images(mrs, hash_urls: dict[str, str], state: dict) -> dict[str, str]:
    mapping = dict(state.get("image_hash_map", {}))
    version = mrs.graph_api_version or "v25.0"
    for old_hash, url in hash_urls.items():
        if old_hash in mapping:
            continue
        content = requests.get(url, timeout=120).content
        encoded = base64.b64encode(content).decode("ascii")
        uploaded = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/adimages",
            data={"bytes": encoded},
        )
        images = uploaded.get("images") or {}
        new_hash = next(iter(images.values())).get("hash") if images else uploaded.get("hash")
        if not new_hash and isinstance(uploaded, dict):
            # sometimes { "images": { "bytes": {"hash": "..."}}}
            for val in uploaded.values():
                if isinstance(val, dict) and val.get("hash"):
                    new_hash = val["hash"]
                    break
        if not new_hash:
            raise RuntimeError(f"Could not upload image for hash {old_hash}: {uploaded}")
        mapping[old_hash] = new_hash
        print(f"[uploaded] image {old_hash[:8]}… → {new_hash[:8]}…")
    state["image_hash_map"] = mapping
    save_state(state)
    return mapping


def remap_creative(creative: dict, hash_map: dict[str, str]) -> dict:
    spec = {
        "name": creative.get("name", "Creative"),
        "object_story_spec": {
            "page_id": PAGE_ID,
            "instagram_user_id": IG_ID,
        },
        "degrees_of_freedom_spec": creative.get("degrees_of_freedom_spec"),
    }
    afs = deepcopy(creative.get("asset_feed_spec") or {})
    for img in afs.get("images", []):
        old = img.get("hash")
        if old and old in hash_map:
            img["hash"] = hash_map[old]
    for link in afs.get("link_urls", []):
        if link.get("website_url"):
            link["website_url"] = clean_link(link["website_url"])
    spec["asset_feed_spec"] = strip_ids(afs)
    return strip_ids(spec)


def build_adset_params(source: dict, campaign_id: str, audience_id: str) -> dict:
    targeting = deepcopy(source["targeting"])
    targeting["custom_audiences"] = [{"id": audience_id}]
    return {
        "name": ADSET_NAME,
        "campaign_id": campaign_id,
        "daily_budget": source["daily_budget"],
        "billing_event": source["billing_event"],
        "optimization_goal": source["optimization_goal"],
        "bid_strategy": source["bid_strategy"],
        "bid_amount": source["bid_amount"],
        "destination_type": source["destination_type"],
        "promoted_object": {
            "pixel_id": NEW_PIXEL,
            "custom_event_type": "OTHER",
            "custom_event_str": "MRS_FB_onlineBooking",
        },
        "targeting": targeting,
        "attribution_spec": source["attribution_spec"],
        "is_dynamic_creative": source.get("is_dynamic_creative", False),
        "pacing_type": source.get("pacing_type"),
        "status": "PAUSED",
    }


def check(mrs, old: dict) -> int:
    rows = read_audience_rows(CSV_PATH)
    adset = fetch_old_adset(old)
    print(f"[csv] {CSV_PATH.name}: {len(rows)} rows with phone")
    print(f"[old adset] {adset['name']} budget={adset.get('daily_budget')} bid={adset.get('bid_amount')} {adset.get('bid_strategy')}")
    print(f"[old audience] {(adset.get('targeting') or {}).get('custom_audiences')}")
    print(f"[active ads] {len(OLD_AD_IDS)}")
    for ad_id in OLD_AD_IDS:
        name, creative = fetch_old_creative(old, ad_id)
        print(f"  - {name}: {len(collect_hashes(creative))} images")
    state = load_state()
    print(f"[state] {STATE_PATH}: {json.dumps(state, ensure_ascii=False)}")
    return 0


def apply(mrs, old: dict) -> int:
    state = load_state()
    rows = read_audience_rows(CSV_PATH)
    if not rows:
        raise RuntimeError("CSV audience is empty after normalization")

    audience_id = upload_audience(mrs, rows)
    source_adset = fetch_old_adset(old)
    version = mrs.graph_api_version or "v25.0"

    if "campaign_id" not in state:
        old_campaign = graph(
            old["token"],
            old["version"],
            "GET",
            OLD_CAMPAIGN_ID,
            params={"fields": "objective,buying_type,special_ad_categories"},
        )
        campaign = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/campaigns",
            data={
                "name": CAMPAIGN_NAME,
                "objective": old_campaign["objective"],
                "buying_type": old_campaign.get("buying_type", "AUCTION"),
                "special_ad_categories": json.dumps(old_campaign.get("special_ad_categories") or []),
                "status": "PAUSED",
                "is_adset_budget_sharing_enabled": "false",
            },
        )
        state["campaign_id"] = campaign["id"]
        save_state(state)
        print(f"[created] campaign {state['campaign_id']}")

    if "adset_id" not in state:
        params = build_adset_params(source_adset, state["campaign_id"], audience_id)
        adset = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/adsets",
            data={k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in params.items()},
        )
        state["adset_id"] = adset["id"]
        save_state(state)
        print(f"[created] ad set {state['adset_id']}")

    all_hashes: set[str] = set()
    ad_creatives: list[tuple[str, dict]] = []
    for ad_id in OLD_AD_IDS:
        name, creative = fetch_old_creative(old, ad_id)
        all_hashes |= collect_hashes(creative)
        ad_creatives.append((name, creative))

    hash_urls = resolve_image_urls(old, all_hashes)
    hash_map = upload_images(mrs, hash_urls, state)

    state.setdefault("ads", {})
    for name, creative in ad_creatives:
        if name in state["ads"] and state["ads"][name].get("ad_id"):
            print(f"[reused] ad {name}")
            continue
        creative_params = remap_creative(creative, hash_map)
        creative_params["name"] = f"{name} | MRS migrate"
        created_creative = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/adcreatives",
            data={
                k: json.dumps(v) if isinstance(v, (dict, list)) else v
                for k, v in creative_params.items()
            },
        )
        ad = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/ads",
            data={
                "name": name,
                "adset_id": state["adset_id"],
                "creative": json.dumps({"creative_id": created_creative["id"]}),
                "status": "PAUSED",
            },
        )
        state["ads"][name] = {
            "creative_id": created_creative["id"],
            "ad_id": ad["id"],
        }
        save_state(state)
        print(f"[created] ad {name} → {ad['id']}")

    print("[complete] MRS_Эндоскопия migrated PAUSED")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    args = parse_args()
    try:
        mrs = get_mrs_settings()
        old = load_env_old()
    except ConfigError as exc:
        print(f"[config] {exc}")
        return 2

    if not CSV_PATH.exists():
        print(f"[error] CSV not found: {CSV_PATH}")
        return 2

    try:
        if args.check:
            return check(mrs, old)
        return apply(mrs, old)
    except (RuntimeError, requests.RequestException) as exc:
        message = str(exc)
        if "development mode" in message.lower():
            print("[error] Meta app MRS_Web_Kravira (2042743246376012) в Development mode.")
            print("        Переведите приложение в Live: developers.facebook.com → MRS_Web_Kravira → App mode → Live.")
            print("        Затем повторите: python -m scripts.migrate_endoscopy_to_mrs --apply")
        print(f"[error] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
