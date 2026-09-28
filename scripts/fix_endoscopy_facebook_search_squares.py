"""Use square assets for Facebook Search in every active Endoscopy ad."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.create_facebook_search_only_replacements import build_creative
from scripts.create_laser_format_replacements import ACCOUNT, get, request


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "image" / "concepts" / "critical_rebuild_2026-08-12"
STATE_FILE = ROOT / "tmp_refs" / "endoscopy_search_square_2026-08-13" / "meta_state.json"
SUFFIX = "__FACEBOOK_SEARCH_SQUARE_2026-08-13"

ITEMS = {
    "120250690499260770": ASSETS / "120250631220810770_1x1.jpg",  # Яровой
    "120250690502930770": ASSETS / "120250631218260770_1x1.jpg",  # Богдашич
    "120250690506760770": ASSETS / "120250631222800770_1x1.jpg",  # Казак
}


def save(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def upload(path: Path) -> str:
    with path.open("rb") as handle:
        result = request(
            "POST",
            f"{ACCOUNT}/adimages",
            files={"filename": (path.name, handle, "image/jpeg")},
        )
    return next(iter(result["images"].values()))["hash"]


def main() -> int:
    state = (
        json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if STATE_FILE.exists()
        else {}
    )
    for source_id, path in ITEMS.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        item = state.setdefault(source_id, {})
        source = get(
            source_id,
            {
                "fields": (
                    "id,name,status,effective_status,adset{id,name},"
                    "creative{id,name,object_story_spec,asset_feed_spec,degrees_of_freedom_spec}"
                )
            },
        )

        if not item.get("square_hash"):
            item["square_hash"] = upload(path)
            item["square_path"] = str(path)
            save(state)
            print(f"uploaded {source_id} {item['square_hash']}")

        if not item.get("replacement_ad_id"):
            replacement = request(
                "POST",
                f"{ACCOUNT}/ads",
                data={
                    "name": f"{source['name']}{SUFFIX}",
                    "adset_id": source["adset"]["id"],
                    "creative": json.dumps(
                        build_creative(source, item["square_hash"]),
                        ensure_ascii=False,
                    ),
                    "status": "ACTIVE",
                },
            )
            item.update(
                {
                    "replacement_ad_id": replacement["id"],
                    "source_ad_id": source_id,
                    "adset_id": source["adset"]["id"],
                    "status": "ACTIVE",
                }
            )
            save(state)

        if not item.get("source_paused"):
            request("POST", source_id, data={"status": "PAUSED"})
            item["source_paused"] = True
            save(state)

        item["verification"] = get(
            item["replacement_ad_id"],
            {
                "fields": (
                    "id,name,status,effective_status,issues_info,"
                    "adset{id,name,status,effective_status},"
                    "creative{id,name,asset_feed_spec}"
                )
            },
        )
        save(state)

    print(
        json.dumps(
            {
                source_id: {
                    "replacement_ad_id": item["replacement_ad_id"],
                    "status": item["verification"].get("effective_status"),
                    "square_hash": item["square_hash"],
                }
                for source_id, item in state.items()
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
