"""Activate approved Facebook Search replacements and pause their sources."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.create_laser_format_replacements import get, request


ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "tmp_refs" / "facebook_search_only_2026-08-12" / "meta_state.json"
SOURCE_IDS = [
    "120250661689710770",
    "120250631220810770",
    "120250631218260770",
    "120250631222800770",
]


def save(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    for source_id in SOURCE_IDS:
        item = state[source_id]
        replacement_id = item["replacement_ad_id"]
        request("POST", replacement_id, data={"status": "ACTIVE"})
        request("POST", source_id, data={"status": "PAUSED"})
        item["activated"] = True
        save(state)
        print(f"switched {source_id} -> {replacement_id}")

    for source_id in SOURCE_IDS:
        replacement_id = state[source_id]["replacement_ad_id"]
        old = get(source_id, {"fields": "id,name,status,effective_status"})
        new = get(replacement_id, {"fields": "id,name,status,effective_status,issues_info"})
        state[source_id]["post_activation"] = {"source": old, "replacement": new}
        save(state)
        print(json.dumps({"source": old, "replacement": new}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
