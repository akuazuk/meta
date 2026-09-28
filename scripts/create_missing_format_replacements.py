"""Upload rebuilt media and create PAUSED replacements for nine single-format ads."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts.create_laser_format_replacements import ACCOUNT, request
from scripts.migrate_other_active_formats import create_replacement


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "tmp_refs" / "all_format_fix" / "design_sources"
ASSET_DIR = ROOT / "image" / "concepts" / "all_format_fix"
STATE_FILE = ROOT / "tmp_refs" / "all_format_fix" / "design_state.json"
TARGET_ADSETS = {
    "ЛОР_серия_Сайт": "120250631198310770",
    "Гинекология_Операции_2_Сайт": "120250631255310770",
    "Гинекология_серия_Сайт": "120250631293900770",
    "Справки_Серия_Сайт": "120250631312470770",
}
VERTICAL_SOURCES = {
    "120250487253590770",
    "120250487246110770",
    "120250487601200770",
    "120250486759170770",
    "120250486829330770",
}
PORTRAIT_FEED_SOURCE = "120250486709060770"


def upload(path: Path) -> str:
    with path.open("rb") as handle:
        result = request(
            "POST",
            f"{ACCOUNT}/adimages",
            files={"filename": (path.name, handle, "image/jpeg")},
        )
    return next(iter(result["images"].values()))["hash"]


def dynamic_source(entry: dict) -> dict:
    ad = {
        "id": entry["id"],
        "name": entry["name"],
        "creative": copy.deepcopy(entry["creative"]),
    }
    story = ad["creative"].get("object_story_spec", {})
    link = story.get("link_data", {})
    clean_name = entry["name"].replace("_", " ")
    feed = {
        "bodies": [{"text": link.get("message") or "Позаботьтесь о здоровье вовремя - запишитесь в медицинский центр Кравира."}],
        "titles": [{"text": link.get("name") or clean_name}],
        "link_urls": [{"website_url": link.get("link", "https://kravira.by/")}],
        "call_to_action_types": [link.get("call_to_action", {}).get("type", "LEARN_MORE")],
        "descriptions": [{"text": link.get("description") or "Запись по телефону 403"}],
    }
    ad["creative"]["object_story_spec"] = {
        key: story[key]
        for key in ("page_id", "instagram_user_id")
        if story.get(key)
    }
    ad["creative"]["asset_feed_spec"] = feed
    return ad


def main() -> int:
    manifest = json.loads((SOURCE_DIR / "manifest.json").read_text(encoding="utf-8"))
    state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {}
    for entry in manifest:
        ad_id = entry["id"]
        if state.get(ad_id, {}).get("replacement_ad_id"):
            continue
        item = state.setdefault(ad_id, {"uploads": {}})
        uploads = item["uploads"]
        square_path = ASSET_DIR / f"{ad_id}_square.jpg"
        if "square" not in uploads:
            uploads["square"] = upload(square_path)
            STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"uploaded square {ad_id} {uploads['square']}")
        if (ASSET_DIR / f"{ad_id}_vertical.jpg").exists() and "vertical" not in uploads:
            uploads["vertical"] = upload(ASSET_DIR / f"{ad_id}_vertical.jpg")
            STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"uploaded vertical {ad_id} {uploads['vertical']}")

        original = entry["images"][0]
        if ad_id in VERTICAL_SOURCES:
            feed_hash = compact_hash = uploads["square"]
            vertical_hash = original["hash"]
            dims = {"feed": "1080x1080", "compact": "1080x1080", "vertical": "1080x1920"}
        elif ad_id == PORTRAIT_FEED_SOURCE:
            feed_hash = original["hash"]
            compact_hash = uploads["square"]
            vertical_hash = uploads["vertical"]
            dims = {"feed": "1080x1440", "compact": "1080x1080", "vertical": "1080x1920"}
        else:
            feed_hash = compact_hash = uploads["square"]
            vertical_hash = uploads["vertical"]
            dims = {"feed": "1080x1080", "compact": "1080x1080", "vertical": "1080x1920"}
        selected = {
            "feed": feed_hash,
            "compact": compact_hash,
            "vertical": vertical_hash,
            "dimensions": dims,
        }
        replacement = create_replacement(
            dynamic_source(entry), selected, TARGET_ADSETS[entry["adset"]]
        )
        item.update(
            {
                "source_name": entry["name"],
                "target_adset_id": TARGET_ADSETS[entry["adset"]],
                "replacement_ad_id": replacement,
                "status": "PAUSED",
                "dimensions": dims,
            }
        )
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"created {replacement} <- {ad_id} {entry['name']}")
    print(json.dumps({"complete": len([x for x in state.values() if x.get('replacement_ad_id')])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
