"""Create PAUSED placement-safe replacements for campaign Лазерные_Хирурги.

The script is intentionally idempotent and never changes existing ads. Without
``--apply`` it only writes a fresh backup and prints the planned operations.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
ACCOUNT = "act_723170300839405"
CAMPAIGN_ID = "120240244020070770"
TARGET_NAMES = {
    "Орловский_прятать",
    "Орловский_лазер",
    "Орловский_один_приём",
    "Коротин",
    "Ерохов",
}
STAMP = "2026-08-10"
SUFFIX = f"__FORMAT_FIX_{STAMP}"
STATE_DIR = ROOT / "tmp_refs" / "laser_format_fix"
STATE_FILE = STATE_DIR / "created_replacements.json"
TARGET_ADSET_NAME = f"Онкологи_Серия_Сайт{SUFFIX}"

ORLOVSKI_FILES = {
    "Орловский_прятать": "orlovski_1_hide",
    "Орловский_лазер": "orlovski_2_laser",
    "Орловский_один_приём": "orlovski_3_once",
}


def load_env() -> dict[str, str]:
    values = dict(os.environ)
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values.setdefault(key.strip(), value.strip().strip("'\""))
    return values


ENV = load_env()
TOKEN = ENV["META_ACCESS_TOKEN"]
VERSION = ENV.get("META_GRAPH_API_VERSION", "v23.0")
BASE = f"https://graph.facebook.com/{VERSION}"


def request(method: str, path: str, *, data: dict | None = None, files=None) -> dict:
    payload = dict(data or {})
    payload["access_token"] = TOKEN
    response = requests.request(
        method,
        f"{BASE}/{path.lstrip('/')}",
        data=payload,
        files=files,
        timeout=120,
    )
    try:
        body = response.json()
    except ValueError as exc:
        raise RuntimeError(f"Meta returned HTTP {response.status_code}: {response.text[:500]}") from exc
    if not response.ok or "error" in body:
        raise RuntimeError(json.dumps(body, ensure_ascii=False, indent=2))
    return body


def get(path: str, params: dict) -> dict:
    query = dict(params)
    query["access_token"] = TOKEN
    response = requests.get(f"{BASE}/{path.lstrip('/')}", params=query, timeout=120)
    body = response.json()
    if not response.ok or "error" in body:
        raise RuntimeError(json.dumps(body, ensure_ascii=False, indent=2))
    return body


def active_ads() -> list[dict]:
    fields = (
        "id,name,status,effective_status,adset{id,name},"
        "creative{id,name,object_story_spec,asset_feed_spec,degrees_of_freedom_spec}"
    )
    payload = get(
        f"{ACCOUNT}/ads",
        {
            "filtering": json.dumps(
                [
                    {"field": "campaign.id", "operator": "EQUAL", "value": CAMPAIGN_ID},
                    {
                        "field": "effective_status",
                        "operator": "IN",
                        "value": ["ACTIVE"],
                    },
                ]
            ),
            "fields": fields,
            "limit": 100,
        },
    )
    return [ad for ad in payload.get("data", []) if ad.get("name") in TARGET_NAMES]


def all_ads() -> list[dict]:
    payload = get(
        f"{ACCOUNT}/ads",
        {
            "filtering": json.dumps(
                [{"field": "campaign.id", "operator": "EQUAL", "value": CAMPAIGN_ID}]
            ),
            "fields": "id,name,status,effective_status,adset{id,name},creative{id,name}",
            "limit": 500,
        },
    )
    return payload.get("data", [])


def ensure_target_adset() -> str:
    payload = get(
        f"{ACCOUNT}/adsets",
        {
            "filtering": json.dumps(
                [{"field": "campaign.id", "operator": "EQUAL", "value": CAMPAIGN_ID}]
            ),
            "fields": "id,name,status,effective_status,is_dynamic_creative",
            "limit": 200,
        },
    )
    for item in payload.get("data", []):
        if item.get("name") == TARGET_ADSET_NAME:
            return item["id"]

    source = get(
        "120250487339540770",
        {
            "fields": (
                "campaign_id,billing_event,optimization_goal,bid_strategy,bid_amount,"
                "promoted_object,targeting,attribution_spec,destination_type,daily_budget,"
                "pacing_type"
            )
        },
    )
    params = {
        "name": TARGET_ADSET_NAME,
        "campaign_id": source["campaign_id"],
        "billing_event": source["billing_event"],
        "optimization_goal": source["optimization_goal"],
        "bid_strategy": source["bid_strategy"],
        "bid_amount": source["bid_amount"],
        "promoted_object": json.dumps(source["promoted_object"], ensure_ascii=False),
        "targeting": json.dumps(source["targeting"], ensure_ascii=False),
        "attribution_spec": json.dumps(source["attribution_spec"], ensure_ascii=False),
        "destination_type": source["destination_type"],
        "daily_budget": source["daily_budget"],
        "pacing_type": json.dumps(source.get("pacing_type", ["standard"])),
        "is_dynamic_creative": "false",
        "status": "PAUSED",
    }
    adset_id = request("POST", f"{ACCOUNT}/adsets", data=params)["id"]
    print(f"created ad set: {TARGET_ADSET_NAME} id={adset_id} status=PAUSED")
    return adset_id


def save_backup(ads: list[dict]) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = STATE_DIR / f"active_ads_before_{now}.json"
    path.write_text(json.dumps(ads, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def normalize_dashes(value):
    if isinstance(value, str):
        return value.replace("—", "-").replace("–", "-").replace("−", "-")
    if isinstance(value, list):
        return [normalize_dashes(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_dashes(item) for key, item in value.items()}
    return value


def upload_image(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("rb") as handle:
        body = request("POST", f"{ACCOUNT}/adimages", files={"filename": handle})
    images = body.get("images", {})
    if not images:
        raise RuntimeError(f"Meta did not return an image hash for {path}")
    return next(iter(images.values()))["hash"]


def image_item(image_hash: str, label: str) -> dict:
    return {"hash": image_hash, "adlabels": [{"name": label}]}


def rules(
    feed_label: str,
    compact_label: str,
    vertical_label: str,
    body_label: str,
    title_label: str,
    url_label: str,
    description_labels: list[str],
) -> list[dict]:
    result = [
        {
            "customization_spec": {
                "age_min": 13,
                "age_max": 65,
                "publisher_platforms": ["facebook", "instagram", "threads"],
                "facebook_positions": ["feed", "marketplace", "video_feeds", "profile_feed"],
                "instagram_positions": [
                    "stream",
                    "explore",
                    "explore_home",
                    "profile_feed",
                    "ig_search",
                ],
                "threads_positions": ["threads_stream"],
            },
            "image_label": {"name": feed_label},
            "body_label": {"name": body_label},
            "title_label": {"name": title_label},
            "link_url_label": {"name": url_label},
            "description_label": {"name": description_labels[0]},
            "priority": 1,
        },
        {
            "customization_spec": {
                "age_min": 13,
                "age_max": 65,
                "publisher_platforms": ["facebook", "messenger", "audience_network"],
                "facebook_positions": ["right_hand_column", "search"],
                "messenger_positions": ["messenger_home"],
                "audience_network_positions": ["classic"],
            },
            "image_label": {"name": compact_label},
            "body_label": {"name": body_label},
            "title_label": {"name": title_label},
            "link_url_label": {"name": url_label},
            "description_label": {"name": description_labels[1]},
            "priority": 2,
        },
        {
            "customization_spec": {"age_min": 13, "age_max": 65},
            "image_label": {"name": vertical_label},
            "body_label": {"name": body_label},
            "title_label": {"name": title_label},
            "link_url_label": {"name": url_label},
            "description_label": {"name": description_labels[2]},
            "priority": 3,
        },
    ]
    return result


def shared_feed_fields(source: dict) -> dict:
    keys = (
        "bodies",
        "call_to_action_types",
        "descriptions",
        "link_urls",
        "titles",
        "additional_data",
    )
    result = {key: copy.deepcopy(source[key]) for key in keys if key in source}
    return normalize_dashes(result)


def apply_shared_label(items: list[dict], label: str) -> None:
    for item in items:
        item["adlabels"] = [{"name": label}]


def existing_hashes(ad: dict) -> tuple[str, str]:
    images = ad["creative"]["asset_feed_spec"].get("images", [])
    hashes = [item["hash"] for item in images]
    if len(hashes) < 2:
        raise RuntimeError(f"Expected multiple images for {ad['name']}")
    image_meta = get(
        f"{ACCOUNT}/adimages",
        {"hashes": json.dumps(hashes), "fields": "hash,width,height", "limit": 100},
    )
    dimensions = {
        item["hash"]: (int(item["width"]), int(item["height"]))
        for item in image_meta.get("data", [])
    }
    square = next((h for h in hashes if 0.94 <= dimensions[h][0] / dimensions[h][1] <= 1.06), None)
    vertical = next((h for h in hashes if 0.52 <= dimensions[h][0] / dimensions[h][1] <= 0.60), None)
    if not square or not vertical:
        raise RuntimeError(f"Could not resolve square/vertical assets for {ad['name']}: {dimensions}")
    return square, vertical


def build_asset_feed(ad: dict, uploaded: dict[str, str]) -> dict:
    source = ad["creative"]["asset_feed_spec"]
    name = ad["name"]
    if name in ORLOVSKI_FILES:
        base = ORLOVSKI_FILES[name]
        feed_hash = uploaded[f"{base}_4x5"]
        compact_hash = uploaded[f"{base}_1x1"]
        vertical_hash = uploaded[f"{base}_9x16"]
    else:
        compact_hash, vertical_hash = existing_hashes(ad)
        feed_hash = compact_hash

    prefix = f"fmt_{ad['id'][-8:]}"
    feed_label = f"{prefix}_feed"
    compact_label = f"{prefix}_compact"
    vertical_label = f"{prefix}_vertical"
    body_label = f"{prefix}_body"
    title_label = f"{prefix}_title"
    url_label = f"{prefix}_url"
    images = [image_item(feed_hash, feed_label)]
    if compact_hash == feed_hash:
        compact_label = feed_label
    else:
        images.append(image_item(compact_hash, compact_label))
    images.append(image_item(vertical_hash, vertical_label))
    result = shared_feed_fields(source)
    apply_shared_label(result.get("bodies", []), body_label)
    apply_shared_label(result.get("titles", []), title_label)
    apply_shared_label(result.get("link_urls", []), url_label)
    descriptions = result.get("descriptions", [])[:3]
    if not descriptions:
        descriptions = [{"text": "Консультация специалиста в Кравире"}]
    description_labels: list[str] = []
    for index, item in enumerate(descriptions):
        label = f"{prefix}_description_{index + 1}"
        item["adlabels"] = [{"name": label}]
        description_labels.append(label)
    while len(description_labels) < 3:
        description_labels.append(description_labels[-1])
    result["descriptions"] = descriptions
    result.update(
        {
            "images": images,
            "ad_formats": ["AUTOMATIC_FORMAT"],
            "optimization_type": "PLACEMENT",
            "asset_customization_rules": rules(
                feed_label,
                compact_label,
                vertical_label,
                body_label,
                title_label,
                url_label,
                description_labels,
            ),
        }
    )
    return result


def upload_orlovski() -> dict[str, str]:
    result: dict[str, str] = {}
    folder = ROOT / "image" / "concepts" / "orlovski_laser"
    for base in ORLOVSKI_FILES.values():
        for suffix in ("1x1", "4x5", "9x16"):
            key = f"{base}_{suffix}"
            result[key] = upload_image(folder / f"{key}.jpg")
            print(f"uploaded {key}: {result[key]}")
    return result


def creative_spec(ad: dict, uploaded: dict[str, str]) -> dict:
    source_creative = ad["creative"]
    object_story_spec = copy.deepcopy(source_creative["object_story_spec"])
    return {
        "name": f"{ad['name']}{SUFFIX} | Creative",
        "object_story_spec": object_story_spec,
        "asset_feed_spec": build_asset_feed(ad, uploaded),
        "degrees_of_freedom_spec": {
            "creative_features_spec": {
                "adapt_to_placement": {"enroll_status": "OPT_OUT"},
                "enhance_cta": {"enroll_status": "OPT_OUT"},
                "image_templates": {"enroll_status": "OPT_OUT"},
                "image_touchups": {"enroll_status": "OPT_OUT"},
                "inline_comment": {"enroll_status": "OPT_OUT"},
                "text_optimizations": {"enroll_status": "OPT_OUT"},
            }
        },
    }


def create_dynamic_creative(ad: dict, uploaded: dict[str, str]) -> str:
    spec = creative_spec(ad, uploaded)
    params = {
        "name": spec["name"],
        "object_story_spec": json.dumps(spec["object_story_spec"], ensure_ascii=False),
        "asset_feed_spec": json.dumps(spec["asset_feed_spec"], ensure_ascii=False),
        "degrees_of_freedom_spec": json.dumps(
            spec["degrees_of_freedom_spec"], ensure_ascii=False
        ),
        # Required when the destination ad set has is_dynamic_creative=true.
        "is_dco_internal": "true",
    }
    return request("POST", f"{ACCOUNT}/adcreatives", data=params)["id"]


def create_ad(ad: dict, uploaded: dict[str, str]) -> str:
    inline_creative = creative_spec(ad, uploaded)
    body = request(
        "POST",
        f"{ad['id']}/copies",
        data={
            "adset_id": ad["adset"]["id"],
            "creative_parameters": json.dumps(inline_creative, ensure_ascii=False),
            "status_option": "PAUSED",
        },
    )
    ad_id = body.get("copied_ad_id") or body.get("id")
    if not ad_id:
        raise RuntimeError(f"Meta copy endpoint did not return an ad id: {body}")
    request(
        "POST",
        ad_id,
        data={
            "name": f"{ad['name']}{SUFFIX}",
            "status": "PAUSED",
        },
    )
    return ad_id


def legacy_create_ad(ad: dict, uploaded: dict[str, str]) -> str:
    """Kept only as API-shape reference; dynamic ad sets use create_ad above."""
    inline_creative = creative_spec(ad, uploaded)
    params = {
        "name": f"{ad['name']}{SUFFIX}",
        "adset_id": ad["adset"]["id"],
        "source_ad_id": ad["id"],
        "creative": json.dumps(inline_creative, ensure_ascii=False),
        "status": "PAUSED",
    }
    return request("POST", f"{ACCOUNT}/ads", data=params)["id"]


def create_ad_in_new_adset(ad: dict, uploaded: dict[str, str], adset_id: str) -> str:
    params = {
        "name": f"{ad['name']}{SUFFIX}",
        "adset_id": adset_id,
        "creative": json.dumps(creative_spec(ad, uploaded), ensure_ascii=False),
        "status": "PAUSED",
    }
    return request("POST", f"{ACCOUNT}/ads", data=params)["id"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    ads = active_ads()
    if {ad["name"] for ad in ads} != TARGET_NAMES:
        raise RuntimeError(
            f"Expected {sorted(TARGET_NAMES)}, got {sorted(ad['name'] for ad in ads)}"
        )
    backup = save_backup(ads)
    print(f"backup: {backup}")

    existing = {ad["name"]: ad for ad in all_ads()}
    duplicate_names = [f"{name}{SUFFIX}" for name in TARGET_NAMES if f"{name}{SUFFIX}" in existing]
    if duplicate_names:
        print("already exist:", ", ".join(sorted(duplicate_names)))

    if not args.apply:
        for ad in sorted(ads, key=lambda item: item["name"]):
            print(f"PLAN: {ad['name']} -> {ad['name']}{SUFFIX} (PAUSED)")
        return 0

    adset_id = ensure_target_adset()
    uploaded = upload_orlovski()
    created: dict[str, dict] = {}
    if STATE_FILE.exists():
        created = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    for ad in sorted(ads, key=lambda item: item["name"]):
        replacement_name = f"{ad['name']}{SUFFIX}"
        if replacement_name in existing:
            print(f"skip existing: {replacement_name}")
            continue
        ad_id = create_ad_in_new_adset(ad, uploaded, adset_id)
        new_ad = get(ad_id, {"fields": "id,name,status,effective_status,creative{id,name}"})
        creative_id = new_ad["creative"]["id"]
        created[ad["name"]] = {
            "source_ad_id": ad["id"],
            "replacement_ad_id": ad_id,
            "creative_id": creative_id,
            "adset_id": adset_id,
            "status": "PAUSED",
        }
        STATE_FILE.write_text(json.dumps(created, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"created {ad['name']}: ad={ad_id} creative={creative_id} status=PAUSED")

    STATE_FILE.write_text(json.dumps(created, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"state: {STATE_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
