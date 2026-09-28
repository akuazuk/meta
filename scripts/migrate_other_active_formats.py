"""Create PAUSED format-safe replacements for active Meta ads outside Laser Surgeons.

Existing image assets are reused. Ads without both a feed-safe and a 9:16
asset are reported for a later design pass and are not changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from scripts.create_laser_format_replacements import ACCOUNT, request, get


ROOT = Path(__file__).resolve().parents[1]
LASER_CAMPAIGN_ID = "120240244020070770"
SUFFIX = "__FORMAT_FIX_2026-08-10"
STATE_DIR = ROOT / "tmp_refs" / "all_format_fix"
STATE_FILE = STATE_DIR / "state.json"
PLAN_FILE = ROOT / "docs" / "META_OTHER_FORMAT_FIX_PLAN.md"


def all_pages(path: str, params: dict) -> list[dict]:
    result: list[dict] = []
    payload = get(path, params)
    while True:
        result.extend(payload.get("data", []))
        next_url = payload.get("paging", {}).get("next")
        if not next_url:
            return result
        import requests

        response = requests.get(next_url, timeout=120)
        body = response.json()
        if not response.ok or "error" in body:
            raise RuntimeError(json.dumps(body, ensure_ascii=False, indent=2))
        payload = body


def active_ads() -> list[dict]:
    fields = (
        "id,name,status,effective_status,campaign{id,name},adset{id,name},"
        "creative{id,name,object_story_spec,asset_feed_spec,degrees_of_freedom_spec}"
    )
    ads = all_pages(
        f"{ACCOUNT}/ads",
        {
            "filtering": json.dumps(
                [{"field": "effective_status", "operator": "IN", "value": ["ACTIVE"]}]
            ),
            "fields": fields,
            "limit": 500,
        },
    )
    return [
        ad
        for ad in ads
        if ad.get("campaign", {}).get("id") != LASER_CAMPAIGN_ID
        and SUFFIX not in ad.get("name", "")
    ]


def collect_hashes(ad: dict) -> list[str]:
    creative = ad.get("creative", {})
    feed = creative.get("asset_feed_spec", {})
    hashes = [item.get("hash") for item in feed.get("images", []) if item.get("hash")]
    link_hash = creative.get("object_story_spec", {}).get("link_data", {}).get("image_hash")
    if link_hash:
        hashes.append(link_hash)
    return list(dict.fromkeys(hashes))


def image_metadata(ads: list[dict]) -> dict[str, dict]:
    hashes = sorted({image_hash for ad in ads for image_hash in collect_hashes(ad)})
    result: dict[str, dict] = {}
    for offset in range(0, len(hashes), 40):
        payload = get(
            f"{ACCOUNT}/adimages",
            {
                "hashes": json.dumps(hashes[offset : offset + 40]),
                "fields": "hash,width,height,name",
                "limit": 100,
            },
        )
        for item in payload.get("data", []):
            result[item["hash"]] = item
    return result


def ratio(item: dict) -> float:
    return int(item["width"]) / int(item["height"])


def choose_assets(ad: dict, metadata: dict[str, dict]) -> dict | None:
    hashes = [h for h in collect_hashes(ad) if h in metadata]
    if not hashes:
        return None
    vertical = [h for h in hashes if 0.52 <= ratio(metadata[h]) <= 0.60]
    feed = [h for h in hashes if 0.70 <= ratio(metadata[h]) <= 1.06]
    compact_square = [h for h in hashes if 0.94 <= ratio(metadata[h]) <= 1.06]
    compact_wide = [h for h in hashes if ratio(metadata[h]) >= 1.45]
    if not vertical or not feed:
        return None

    def feed_score(image_hash: str) -> tuple[float, float]:
        value = ratio(metadata[image_hash])
        return (abs(value - 0.8), abs(value - 1.0))

    feed_hash = sorted(feed, key=feed_score)[0]
    compact_hash = (
        compact_square[0]
        if compact_square
        else compact_wide[0]
        if compact_wide
        else feed_hash
        if 0.94 <= ratio(metadata[feed_hash]) <= 1.06
        else None
    )
    if compact_hash is None:
        return None
    vertical_hash = vertical[0]
    return {
        "feed": feed_hash,
        "compact": compact_hash,
        "vertical": vertical_hash,
        "dimensions": {
            key: f"{metadata[value]['width']}x{metadata[value]['height']}"
            for key, value in {
                "feed": feed_hash,
                "compact": compact_hash,
                "vertical": vertical_hash,
            }.items()
        },
    }


def normalize_dashes(value):
    if isinstance(value, str):
        return value.replace("—", "-").replace("–", "-").replace("−", "-")
    if isinstance(value, list):
        return [normalize_dashes(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_dashes(item) for key, item in value.items()}
    return value


def label_items(items: list[dict], label: str) -> None:
    for item in items:
        item.pop("adlabels", None)
        item["adlabels"] = [{"name": label}]


def build_rules(labels: dict, description_labels: list[str] | None) -> list[dict]:
    specs = [
        {
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
        {
            "age_min": 13,
            "age_max": 65,
            "publisher_platforms": ["facebook", "messenger", "audience_network"],
            "facebook_positions": ["right_hand_column", "search"],
            "messenger_positions": ["messenger_home"],
            "audience_network_positions": ["classic"],
        },
        {"age_min": 13, "age_max": 65},
    ]
    image_labels = [labels["feed"], labels["compact"], labels["vertical"]]
    result: list[dict] = []
    for index, (spec, image_label) in enumerate(zip(specs, image_labels)):
        rule = {
            "customization_spec": spec,
            "image_label": {"name": image_label},
            "body_label": {"name": labels["body"]},
            "title_label": {"name": labels["title"]},
            "link_url_label": {"name": labels["url"]},
            "priority": index + 1,
        }
        if description_labels:
            rule["description_label"] = {"name": description_labels[index]}
        result.append(rule)
    return result


def build_asset_feed(ad: dict, selected: dict) -> dict:
    source = ad["creative"].get("asset_feed_spec", {})
    keys = (
        "bodies",
        "call_to_action_types",
        "descriptions",
        "link_urls",
        "titles",
        "additional_data",
    )
    result = normalize_dashes(
        {key: copy.deepcopy(source[key]) for key in keys if key in source}
    )
    prefix = f"allfmt_{ad['id'][-8:]}"
    labels = {
        "feed": f"{prefix}_feed",
        "compact": f"{prefix}_compact",
        "vertical": f"{prefix}_vertical",
        "body": f"{prefix}_body",
        "title": f"{prefix}_title",
        "url": f"{prefix}_url",
    }
    label_items(result.get("bodies", []), labels["body"])
    label_items(result.get("titles", []), labels["title"])
    label_items(result.get("link_urls", []), labels["url"])

    description_labels: list[str] | None = None
    descriptions = result.get("descriptions", [])
    if len(descriptions) > 1:
        descriptions = descriptions[:3]
        description_labels = []
        for index, item in enumerate(descriptions):
            label = f"{prefix}_description_{index + 1}"
            item.pop("adlabels", None)
            item["adlabels"] = [{"name": label}]
            description_labels.append(label)
        while len(description_labels) < 3:
            description_labels.append(description_labels[-1])
        result["descriptions"] = descriptions

    image_items: list[dict] = []
    hash_to_label: dict[str, str] = {}
    for group in ("feed", "compact", "vertical"):
        image_hash = selected[group]
        if image_hash in hash_to_label:
            labels[group] = hash_to_label[image_hash]
            continue
        hash_to_label[image_hash] = labels[group]
        image_items.append(
            {"hash": image_hash, "adlabels": [{"name": labels[group]}]}
        )

    result.update(
        {
            "images": image_items,
            "ad_formats": ["AUTOMATIC_FORMAT"],
            "optimization_type": "PLACEMENT",
            "asset_customization_rules": build_rules(labels, description_labels),
        }
    )
    return result


def creative_spec(ad: dict, selected: dict) -> dict:
    return {
        "name": f"{ad['name']}{SUFFIX} | Creative",
        "object_story_spec": copy.deepcopy(ad["creative"]["object_story_spec"]),
        "asset_feed_spec": build_asset_feed(ad, selected),
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


def source_adset(adset_id: str) -> dict:
    return get(
        adset_id,
        {
            "fields": (
                "id,name,campaign_id,billing_event,optimization_goal,bid_strategy,"
                "bid_amount,bid_constraints,promoted_object,targeting,attribution_spec,"
                "destination_type,daily_budget,lifetime_budget,pacing_type,"
                "optimization_sub_event,frequency_control_specs"
            )
        },
    )


def existing_target_adsets() -> dict[tuple[str, str], str]:
    items = all_pages(
        f"{ACCOUNT}/adsets",
        {"fields": "id,name,campaign_id,status,effective_status", "limit": 500},
    )
    return {
        (item.get("campaign_id", ""), item.get("name", "")): item["id"] for item in items
    }


def create_target_adset(source: dict, existing: dict[tuple[str, str], str]) -> str:
    name = f"{source['name']}{SUFFIX}"
    key = (source["campaign_id"], name)
    if key in existing:
        return existing[key]
    params = {
        "name": name,
        "campaign_id": source["campaign_id"],
        "billing_event": source["billing_event"],
        "optimization_goal": source["optimization_goal"],
        "promoted_object": json.dumps(source["promoted_object"], ensure_ascii=False),
        "targeting": json.dumps(source["targeting"], ensure_ascii=False),
        "attribution_spec": json.dumps(source.get("attribution_spec", [])),
        "is_dynamic_creative": "false",
        "status": "PAUSED",
    }
    for key_name in (
        "bid_strategy",
        "bid_amount",
        "destination_type",
        "optimization_sub_event",
    ):
        value = source.get(key_name)
        if value not in (None, "", "NONE"):
            params[key_name] = value
    for key_name in (
        "bid_constraints",
        "pacing_type",
        "frequency_control_specs",
    ):
        value = source.get(key_name)
        if value:
            params[key_name] = json.dumps(value)
    daily = int(source.get("daily_budget") or 0)
    lifetime = int(source.get("lifetime_budget") or 0)
    if daily:
        params["daily_budget"] = daily
    elif lifetime:
        params["lifetime_budget"] = lifetime
    adset_id = request("POST", f"{ACCOUNT}/adsets", data=params)["id"]
    existing[(source["campaign_id"], name)] = adset_id
    print(f"created adset {adset_id} {name}")
    return adset_id


def create_replacement(ad: dict, selected: dict, adset_id: str) -> str:
    name = f"{ad['name']}{SUFFIX}__{ad['id'][-6:]}"
    return request(
        "POST",
        f"{ACCOUNT}/ads",
        data={
            "name": name,
            "adset_id": adset_id,
            "creative": json.dumps(creative_spec(ad, selected), ensure_ascii=False),
            "status": "PAUSED",
        },
    )["id"]


def write_plan(rows: list[dict]) -> None:
    summary = Counter(row["class"] for row in rows)
    lines = [
        "# План исправления остальных активных объявлений Meta",
        "",
        f"Дата UTC: `{datetime.now(timezone.utc).isoformat()}`.",
        "",
        f"Готовы к remap без перерисовки: **{summary['remap']}**.",
        f"Нужна пересборка медиа: **{summary['design']}**.",
        f"Уже оптимальны: **{summary['optimal']}**.",
        "",
        "| Кампания | Группа | Объявление | ID | Класс | Feed / compact / vertical |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        dimensions = row.get("dimensions", {})
        mapping = (
            f"{dimensions.get('feed', '-')} / {dimensions.get('compact', '-')} / "
            f"{dimensions.get('vertical', '-')}"
        )
        lines.append(
            f"| {row['campaign']} | {row['adset']} | {row['ad']} | `{row['id']}` | "
            f"{row['class']} | {mapping} |"
        )
    PLAN_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    ads = active_ads()
    metadata = image_metadata(ads)
    audit_rows: list[dict] = []
    fixable: list[tuple[dict, dict]] = []
    for ad in ads:
        selected = choose_assets(ad, metadata)
        source_feed = ad.get("creative", {}).get("asset_feed_spec", {})
        old_rules = source_feed.get("asset_customization_rules", [])
        # Existing correct rules have square/4:5 in feed and 9:16 as default.
        already_optimal = False
        if selected and old_rules:
            labels = {
                label.get("name"): item.get("hash")
                for item in source_feed.get("images", [])
                for label in item.get("adlabels", [])
            }
            rule_hashes = [labels.get(rule.get("image_label", {}).get("name")) for rule in old_rules]
            already_optimal = (
                len(rule_hashes) >= 3
                and rule_hashes[0] == selected["feed"]
                and rule_hashes[-1] == selected["vertical"]
            )
        row = {
            "campaign": ad.get("campaign", {}).get("name", ""),
            "adset": ad.get("adset", {}).get("name", ""),
            "ad": ad.get("name", ""),
            "id": ad["id"],
            "class": "optimal" if already_optimal else "remap" if selected else "design",
            "dimensions": selected.get("dimensions", {}) if selected else {},
        }
        audit_rows.append(row)
        if selected and not already_optimal:
            fixable.append((ad, selected))

    audit_rows.sort(key=lambda row: (row["campaign"], row["adset"], row["ad"], row["id"]))
    write_plan(audit_rows)
    print(json.dumps(Counter(row["class"] for row in audit_rows), ensure_ascii=False))
    print(PLAN_FILE)
    if not args.apply:
        return 0

    state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {}
    # Reuse target ad sets recorded after each successful creation. Fetching the
    # complete ad-set inventory on every resume is expensive and quickly hits
    # Meta's account-level API request limit.
    existing_adsets: dict[tuple[str, str], str] = {}
    target_by_source = {
        item["source_adset_id"]: item["target_adset_id"]
        for item in state.values()
        if item.get("source_adset_id") and item.get("target_adset_id")
    }
    source_cache: dict[str, dict] = {}
    created_now = 0
    for ad, selected in fixable:
        if ad["id"] in state:
            continue
        if args.limit and created_now >= args.limit:
            break
        source_id = ad["adset"]["id"]
        target_adset_id = target_by_source.get(source_id)
        if not target_adset_id:
            if source_id not in source_cache:
                source_cache[source_id] = source_adset(source_id)
            target_adset_id = create_target_adset(source_cache[source_id], existing_adsets)
            target_by_source[source_id] = target_adset_id
        try:
            replacement_id = create_replacement(ad, selected, target_adset_id)
        except RuntimeError as exc:
            if "User request limit reached" in str(exc) or '"code": 17' in str(exc):
                print("RATE_LIMIT: stopped safely")
                break
            raise
        state[ad["id"]] = {
            "source_name": ad["name"],
            "campaign": ad.get("campaign", {}).get("name", ""),
            "source_adset_id": source_id,
            "target_adset_id": target_adset_id,
            "replacement_ad_id": replacement_id,
            "status": "PAUSED",
            "dimensions": selected["dimensions"],
        }
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        created_now += 1
        print(f"created {replacement_id} <- {ad['id']} {ad['name']}")
        time.sleep(0.35)
    print(json.dumps({"created_now": created_now, "total_state": len(state)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
