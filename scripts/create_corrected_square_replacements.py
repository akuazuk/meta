"""Replace seven PAUSED off-style square creatives with corrected STYLE_V2 ads."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.create_laser_format_replacements import ACCOUNT, get, request
from scripts.create_missing_format_replacements import dynamic_source
from scripts.migrate_other_active_formats import create_replacement


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "image" / "concepts" / "all_format_fix"
MANIFEST = ROOT / "tmp_refs" / "all_format_fix" / "design_sources" / "manifest.json"
OLD_STATE = ROOT / "tmp_refs" / "all_format_fix" / "design_state.json"
STATE_FILE = ROOT / "tmp_refs" / "all_format_fix" / "corrected_square_state.json"
TARGET_IDS = {
    "120250487253590770",
    "120250487246110770",
    "120250487601200770",
    "120250486829330770",
    "120250486844340770",
    "120250486834710770",
    "120250486838780770",
}
VERTICAL_SOURCES = {
    "120250487253590770",
    "120250487246110770",
    "120250487601200770",
    "120250486829330770",
}


def save(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def upload(path: Path) -> str:
    with path.open("rb") as handle:
        result = request(
            "POST",
            f"{ACCOUNT}/adimages",
            files={"filename": (path.name, handle, "image/jpeg")},
        )
    return next(iter(result["images"].values()))["hash"]


def main() -> int:
    manifest = {item["id"]: item for item in json.loads(MANIFEST.read_text(encoding="utf-8"))}
    old = json.loads(OLD_STATE.read_text(encoding="utf-8"))
    state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {}
    for source_id in sorted(TARGET_IDS):
        if state.get(source_id, {}).get("replacement_ad_id"):
            continue
        item = state.setdefault(source_id, {})
        if not item.get("square_hash"):
            item["square_hash"] = upload(ASSETS / f"{source_id}_square.jpg")
            save(state)
            print(f"uploaded corrected square {source_id} {item['square_hash']}")
        source_entry = manifest[source_id]
        if source_id in VERTICAL_SOURCES:
            vertical_hash = source_entry["images"][0]["hash"]
        else:
            vertical_hash = old[source_id]["uploads"]["vertical"]
        ad = dynamic_source(source_entry)
        ad["name"] = f"{ad['name']}__STYLE_V2"
        selected = {
            "feed": item["square_hash"],
            "compact": item["square_hash"],
            "vertical": vertical_hash,
            "dimensions": {
                "feed": "1080x1080",
                "compact": "1080x1080",
                "vertical": "1080x1920",
            },
        }
        replacement_id = create_replacement(
            ad, selected, old[source_id]["target_adset_id"]
        )
        old_id = old[source_id]["replacement_ad_id"]
        current_old = get(old_id, {"fields": "id,name,status,effective_status"})
        if "OLD_OFFSTYLE" not in current_old.get("name", ""):
            request(
                "POST",
                old_id,
                data={"name": f"{current_old['name']}__OLD_OFFSTYLE", "status": "PAUSED"},
            )
        item.update(
            {
                "source_name": source_entry["name"],
                "old_ad_id": old_id,
                "replacement_ad_id": replacement_id,
                "target_adset_id": old[source_id]["target_adset_id"],
                "status": "PAUSED",
            }
        )
        save(state)
        verified = get(replacement_id, {"fields": "id,name,status,effective_status,adset{id,name}"})
        print(json.dumps(verified, ensure_ascii=False))
    print(json.dumps({"corrected": len([v for v in state.values() if v.get('replacement_ad_id')])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
