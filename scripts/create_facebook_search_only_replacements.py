"""Create PAUSED ads that replace only Facebook Search artwork.

Every other placement keeps the source ad's existing assets and mappings.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts.create_laser_format_replacements import ACCOUNT, get, request
from scripts.migrate_other_active_formats import normalize_dashes


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "image" / "concepts" / "facebook_search_only_2026-08-12"
STATE_FILE = ROOT / "tmp_refs" / "facebook_search_only_2026-08-12" / "meta_state.json"
SOURCE_IDS = [
    "120250661689710770",  # Lugovskaya
    "120250631220810770",  # Yarovoy
    "120250631218260770",  # Bogdashich
    "120250631222800770",  # Kazak
]
UNUSED_MULTI_FORMAT_ADS = [
    "120250690214300770", "120250690218050770", "120250690220240770",
    "120250690223100770", "120250690226250770", "120250690233670770",
    "120250690238070770",
]


def save(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def upload(path: Path) -> str:
    with path.open("rb") as handle:
        result = request(
            "POST", f"{ACCOUNT}/adimages",
            files={"filename": (path.name, handle, "image/jpeg")},
        )
    return next(iter(result["images"].values()))["hash"]


def clean_label(label: dict) -> dict:
    return {"name": label["name"]}


def clean_labeled_items(items: list[dict], allowed: tuple[str, ...]) -> list[dict]:
    output = []
    for source in items:
        item = {key: copy.deepcopy(source[key]) for key in allowed if key in source}
        if source.get("adlabels"):
            item["adlabels"] = [clean_label(label) for label in source["adlabels"]]
        output.append(item)
    return output


def clean_rule(rule: dict) -> dict:
    output = copy.deepcopy(rule)
    for key in ("image_label", "video_label", "body_label", "title_label", "description_label", "link_url_label"):
        if output.get(key):
            output[key] = clean_label(output[key])
    return output


def rule_has_search(rule: dict) -> bool:
    return "search" in rule.get("customization_spec", {}).get("facebook_positions", [])


def without_facebook_search(rule: dict) -> dict | None:
    output = clean_rule(rule)
    spec = output.setdefault("customization_spec", {})
    positions = [position for position in spec.get("facebook_positions", []) if position != "search"]
    if positions:
        spec["facebook_positions"] = positions
    else:
        spec.pop("facebook_positions", None)
        publishers = [publisher for publisher in spec.get("publisher_platforms", []) if publisher != "facebook"]
        if publishers:
            spec["publisher_platforms"] = publishers
        else:
            return None
    return output


def build_creative(ad: dict, search_hash: str) -> dict:
    source = ad["creative"]
    old = source["asset_feed_spec"]
    search_label = f"facebook_search_20260812_{ad['id'][-8:]}"
    images = clean_labeled_items(old.get("images", []), ("hash",))
    images.append({"hash": search_hash, "adlabels": [{"name": search_label}]})

    rules = []
    found_search = False
    for original in old.get("asset_customization_rules", []):
        if not rule_has_search(original):
            rules.append(clean_rule(original))
            continue
        found_search = True
        search_rule = clean_rule(original)
        search_rule["image_label"] = {"name": search_label}
        search_rule["customization_spec"] = {
            "age_min": original.get("customization_spec", {}).get("age_min", 13),
            "age_max": original.get("customization_spec", {}).get("age_max", 65),
            "publisher_platforms": ["facebook"],
            "facebook_positions": ["search"],
        }
        rules.append(search_rule)
        remainder = without_facebook_search(original)
        if remainder:
            rules.append(remainder)

    if not found_search:
        # Use labels from the broadest existing rule, while changing its image only.
        base = clean_rule(old.get("asset_customization_rules", [{}])[-1])
        base["image_label"] = {"name": search_label}
        base["customization_spec"] = {
            "age_min": 13, "age_max": 65,
            "publisher_platforms": ["facebook"], "facebook_positions": ["search"],
        }
        rules.insert(0, base)
    for priority, rule in enumerate(rules, 1):
        rule["priority"] = priority

    feed = {
        "images": images,
        "bodies": clean_labeled_items(old.get("bodies", []), ("text",)),
        "titles": clean_labeled_items(old.get("titles", []), ("text",)),
        "descriptions": clean_labeled_items(old.get("descriptions", []), ("text",)),
        "link_urls": clean_labeled_items(old.get("link_urls", []), ("website_url", "display_url", "deeplink_url")),
        "call_to_action_types": copy.deepcopy(old.get("call_to_action_types", ["LEARN_MORE"])),
        "ad_formats": copy.deepcopy(old.get("ad_formats", ["AUTOMATIC_FORMAT"])),
        "optimization_type": old.get("optimization_type", "PLACEMENT"),
        "asset_customization_rules": rules,
    }
    creative = {
        "name": f"{ad['name']}__FACEBOOK_SEARCH_ONLY_2026-08-12 | Creative",
        "object_story_spec": copy.deepcopy(source["object_story_spec"]),
        "asset_feed_spec": feed,
    }
    if source.get("degrees_of_freedom_spec"):
        creative["degrees_of_freedom_spec"] = copy.deepcopy(source["degrees_of_freedom_spec"])
    return normalize_dashes(creative)


def mark_old_package_unused(state: dict) -> None:
    done = state.setdefault("unused_multi_format_ads", {})
    for ad_id in UNUSED_MULTI_FORMAT_ADS:
        if done.get(ad_id):
            continue
        ad = get(ad_id, {"fields": "id,name,status,effective_status"})
        name = ad["name"]
        if not name.startswith("UNUSED_MULTI_FORMAT__"):
            name = f"UNUSED_MULTI_FORMAT__{name}"
        request("POST", ad_id, data={"name": name, "status": "PAUSED"})
        done[ad_id] = True
        save(state)


def main() -> int:
    state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {}
    for ad_id in SOURCE_IDS:
        item = state.setdefault(ad_id, {})
        ad = get(ad_id, {"fields": (
            "id,name,status,effective_status,adset{id,name},"
            "creative{id,name,object_story_spec,asset_feed_spec,degrees_of_freedom_spec}"
        )})
        if not item.get("search_hash"):
            item["search_hash"] = upload(ASSETS / f"{ad_id}_search.jpg")
            save(state)
            print(f"uploaded {ad_id} {item['search_hash']}")
        if not item.get("replacement_ad_id"):
            item["replacement_ad_id"] = request("POST", f"{ACCOUNT}/ads", data={
                "name": f"{ad['name']}__FACEBOOK_SEARCH_ONLY_2026-08-12",
                "adset_id": ad["adset"]["id"],
                "creative": json.dumps(build_creative(ad, item["search_hash"]), ensure_ascii=False),
                "status": "PAUSED",
            })["id"]
            item.update({"source_ad_id": ad_id, "adset_id": ad["adset"]["id"], "status": "PAUSED"})
            save(state)
            print(f"created {item['replacement_ad_id']} <- {ad_id}")
        item["verification"] = get(item["replacement_ad_id"], {"fields": (
            "id,name,status,effective_status,adset{id,name},"
            "creative{id,name,asset_feed_spec}"
        )})
        save(state)
    mark_old_package_unused(state)
    print(json.dumps({key: value.get("replacement_ad_id") for key, value in state.items() if key in SOURCE_IDS}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
