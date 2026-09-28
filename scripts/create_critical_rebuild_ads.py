"""Upload critical rebuilt assets and create PAUSED placement-safe ads."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts.create_laser_format_replacements import ACCOUNT, get, request
from scripts.migrate_other_active_formats import normalize_dashes


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "image" / "concepts" / "critical_rebuild_2026-08-12"
STATE_FILE = ROOT / "tmp_refs" / "creative_rebuild_2026-08-12" / "meta_state.json"
SOURCE_IDS = [
    "120250661689710770",  # Lugovskaya active old style
    "120250631220810770", "120250631218260770", "120250631222800770",  # endoscopy
    "120250631580830770", "120250631548710770", "120250631315520770",  # certificates
]
LOCAL_COMPACT = {
    "120250661689710770": ROOT / "image" / "concepts" / "all_format_fix" / "120250487246110770_square_batsenko_style_v3.jpg",
    "120250631220810770": ASSETS / "120250631220810770_1x1.jpg",
    "120250631218260770": ASSETS / "120250631218260770_1x1.jpg",
    "120250631222800770": ASSETS / "120250631222800770_1x1.jpg",
}


def save(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def upload(path: Path) -> str:
    with path.open("rb") as handle:
        result = request("POST", f"{ACCOUNT}/adimages", files={"filename": (path.name, handle, "image/jpeg")})
    return next(iter(result["images"].values()))["hash"]


def current_compact(ad: dict) -> str:
    feed = ad["creative"].get("asset_feed_spec", {})
    labels = {
        label["name"]: item["hash"]
        for item in feed.get("images", []) for label in item.get("adlabels", [])
        if item.get("hash") and label.get("name")
    }
    for rule in feed.get("asset_customization_rules", []):
        spec = rule.get("customization_spec", {})
        if "search" in spec.get("facebook_positions", []):
            return labels[rule["image_label"]["name"]]
    images = feed.get("images", [])
    if images:
        return images[0]["hash"]
    return ad["creative"]["object_story_spec"]["link_data"]["image_hash"]


def label_items(items: list[dict], label: str) -> list[dict]:
    out = copy.deepcopy(items)
    for item in out:
        item["adlabels"] = [{"name": label}]
    return out


def creative(ad: dict, hashes: dict[str, str]) -> dict:
    source = ad["creative"]
    old_feed = source.get("asset_feed_spec", {})
    story = copy.deepcopy(source.get("object_story_spec", {}))
    if not old_feed:
        link = story.get("link_data", {})
        old_feed = {
            "bodies": [{"text": link.get("message", "Запишитесь в медицинский центр Кравира.")}],
            "titles": [{"text": link.get("name", ad["name"])}],
            "descriptions": [{"text": link.get("description", "Запись по телефону 403")}],
            "link_urls": [{"website_url": link.get("link", "https://kravira.by/")}],
            "call_to_action_types": [link.get("call_to_action", {}).get("type", "LEARN_MORE")],
        }
        story = {key: story[key] for key in ("page_id", "instagram_user_id") if story.get(key)}
    prefix = f"rebuild_{ad['id'][-8:]}"
    labels = {key: f"{prefix}_{key}" for key in ("feed", "compact", "vertical", "body", "title", "url")}
    descriptions = copy.deepcopy(old_feed.get("descriptions", [{"text": "Запись по телефону 403"}]))[:3]
    fallbacks = ["Медицинский центр Кравира", "Запись по телефону 403", "Удобные форматы для всех плейсментов"]
    existing = {item.get("text", "") for item in descriptions}
    for text in fallbacks:
        if len(descriptions) >= 3:
            break
        if text not in existing:
            descriptions.append({"text": text})
            existing.add(text)
    desc_labels = []
    for index, item in enumerate(descriptions):
        label = f"{prefix}_description_{index+1}"
        item["adlabels"] = [{"name": label}]
        desc_labels.append(label)

    common = {
        "body_label": {"name": labels["body"]},
        "title_label": {"name": labels["title"]},
        "link_url_label": {"name": labels["url"]},
    }
    rules = [
        {
            **common, "description_label": {"name": desc_labels[0]}, "image_label": {"name": labels["feed"]}, "priority": 1,
            "customization_spec": {
                "age_min": 13, "age_max": 65, "publisher_platforms": ["facebook", "instagram", "threads"],
                "facebook_positions": ["feed", "video_feeds", "marketplace", "profile_feed"],
                "instagram_positions": ["stream", "explore", "explore_home", "profile_feed", "ig_search"],
                "threads_positions": ["threads_stream"],
            },
        },
        {
            **common, "description_label": {"name": desc_labels[1]}, "image_label": {"name": labels["vertical"]}, "priority": 2,
            "customization_spec": {
                "age_min": 13, "age_max": 65, "publisher_platforms": ["facebook", "instagram", "messenger"],
                "facebook_positions": ["story", "facebook_reels"],
                "instagram_positions": ["story", "reels"],
                "messenger_positions": ["story"],
            },
        },
        {
            **common, "description_label": {"name": desc_labels[2]}, "image_label": {"name": labels["compact"]}, "priority": 3,
            "customization_spec": {"age_min": 13, "age_max": 65},
        },
    ]
    asset_feed = {
        "images": [{"hash": hashes[key], "adlabels": [{"name": labels[key]}]} for key in ("feed", "compact", "vertical")],
        "bodies": label_items(old_feed.get("bodies", []), labels["body"]),
        "titles": label_items(old_feed.get("titles", []), labels["title"]),
        "descriptions": descriptions,
        "link_urls": label_items(old_feed.get("link_urls", []), labels["url"]),
        "call_to_action_types": old_feed.get("call_to_action_types", ["LEARN_MORE"]),
        "ad_formats": ["AUTOMATIC_FORMAT"], "optimization_type": "PLACEMENT", "asset_customization_rules": rules,
    }
    return normalize_dashes({
        "name": f"{ad['name']}__SAFE_REBUILD_2026-08-12 | Creative",
        "object_story_spec": story,
        "asset_feed_spec": asset_feed,
        "degrees_of_freedom_spec": {"creative_features_spec": {
            key: {"enroll_status": "OPT_OUT"} for key in (
                "adapt_to_placement", "enhance_cta", "image_templates", "image_touchups", "inline_comment", "text_optimizations"
            )
        }},
    })


def main() -> int:
    state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {}
    for ad_id in SOURCE_IDS:
        item = state.setdefault(ad_id, {"hashes": {}})
        ad = get(ad_id, {"fields": "id,name,status,effective_status,adset{id,name},creative{id,object_story_spec,asset_feed_spec}"})
        files = {"feed": ASSETS / f"{ad_id}_4x5.jpg", "vertical": ASSETS / f"{ad_id}_9x16.jpg"}
        if ad_id in LOCAL_COMPACT:
            files["compact"] = LOCAL_COMPACT[ad_id]
        for group, path in files.items():
            if group not in item["hashes"]:
                item["hashes"][group] = upload(path)
                save(state)
                print(f"uploaded {ad_id} {group} {item['hashes'][group]}")
        if "compact" not in item["hashes"]:
            item["hashes"]["compact"] = current_compact(ad)
            save(state)
        if not item.get("replacement_ad_id"):
            item["replacement_ad_id"] = request("POST", f"{ACCOUNT}/ads", data={
                "name": f"{ad['name']}__SAFE_REBUILD_2026-08-12",
                "adset_id": ad["adset"]["id"],
                "creative": json.dumps(creative(ad, item["hashes"]), ensure_ascii=False),
                "status": "PAUSED",
            })["id"]
            item.update({"source_ad_id": ad_id, "adset_id": ad["adset"]["id"], "status": "PAUSED"})
            save(state)
            print(f"created {item['replacement_ad_id']} <- {ad_id}")
        item["verification"] = get(item["replacement_ad_id"], {"fields": "id,name,status,effective_status,adset{id,name},creative{id,asset_feed_spec}"})
        save(state)
    print(json.dumps({key: value.get("replacement_ad_id") for key, value in state.items()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
