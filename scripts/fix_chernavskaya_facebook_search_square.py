"""Replace the Chernavskaya ad with a square-only Facebook Search variant."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.create_facebook_search_only_replacements import build_creative
from scripts.create_laser_format_replacements import ACCOUNT, get, request


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "image" / "concepts" / "cher" / "Чернявская_ФГДС_search_1x1.png"
STATE_FILE = ROOT / "tmp_refs" / "cher" / "facebook_search_square_state.json"
SOURCE_AD_ID = "120250718539290770"
SUFFIX = "__FACEBOOK_SEARCH_SQUARE_2026-08-13"


def save(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def upload() -> str:
    with ASSET.open("rb") as handle:
        result = request(
            "POST",
            f"{ACCOUNT}/adimages",
            files={"filename": (ASSET.name, handle, "image/png")},
        )
    return next(iter(result["images"].values()))["hash"]


def main() -> int:
    if not ASSET.is_file():
        raise FileNotFoundError(ASSET)
    state = (
        json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if STATE_FILE.exists()
        else {}
    )
    source = get(
        SOURCE_AD_ID,
        {
            "fields": (
                "id,name,status,effective_status,adset{id,name},"
                "creative{id,name,object_story_spec,asset_feed_spec,degrees_of_freedom_spec}"
            )
        },
    )

    if not state.get("square_hash"):
        state["square_hash"] = upload()
        state["square_path"] = str(ASSET)
        save(state)
        print(f"uploaded square {state['square_hash']}")

    if not state.get("replacement_ad_id"):
        replacement = request(
            "POST",
            f"{ACCOUNT}/ads",
            data={
                "name": f"{source['name']}{SUFFIX}",
                "adset_id": source["adset"]["id"],
                "creative": json.dumps(
                    build_creative(source, state["square_hash"]),
                    ensure_ascii=False,
                ),
                "status": "ACTIVE",
            },
        )
        state.update(
            {
                "replacement_ad_id": replacement["id"],
                "source_ad_id": SOURCE_AD_ID,
                "adset_id": source["adset"]["id"],
                "status": "ACTIVE",
            }
        )
        save(state)

    if not state.get("source_paused"):
        request("POST", SOURCE_AD_ID, data={"status": "PAUSED"})
        state["source_paused"] = True
        save(state)

    state["verification"] = get(
        state["replacement_ad_id"],
        {
            "fields": (
                "id,name,status,effective_status,issues_info,"
                "adset{id,name,status,effective_status},"
                "creative{id,name,asset_feed_spec}"
            )
        },
    )
    save(state)
    print(json.dumps(state["verification"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
