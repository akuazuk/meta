"""Create the Chernavskaya multi-placement ad in the active Endoscopy ad set.

The operation is idempotent: uploaded hashes and the created ad ID are kept in
``tmp_refs/cher/meta_state.json`` so an interrupted run can safely continue.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts.create_laser_format_replacements import ACCOUNT, get, request


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "image" / "concepts" / "cher"
STATE_FILE = ROOT / "tmp_refs" / "cher" / "meta_state.json"
ADSET_ID = "120250631214700770"
SOURCE_AD_ID = "120250690506760770"
AD_NAME = "Чернявская_ФГДС_86__FORMAT_SAFE_2026-08-13"
URL = "https://kravira.by/staff/chernavskaya/"

FILES = {
    "feed": ASSETS / "ФГДС_Чернявская  (1).png",
    "compact": ASSETS / "Чернявская_ФГДС (1).png",
    "vertical": ASSETS / "ФГДС _скидка_Чернявская_дети (1).png",
}

BODIES = [
    "ФГДС для взрослых и детей от 7 лет у врача-эндоскописта Инны Чернявской. Во второй половине дня - 86 руб.",
    "Нужно пройти гастроскопию? Запишитесь к Инне Николаевне Чернявской: ФГДС после 14:30 - 86 руб.",
    "ФГДС во второй половине дня по специальной цене 86 руб. Приём взрослых и детей от 7 лет.",
]
TITLES = [
    "ФГДС у Инны Чернявской - 86 руб.",
    "Гастроскопия для взрослых и детей",
    "ФГДС после 14:30 - 86 руб.",
]
DESCRIPTION = (
    "Врач-эндоскопист. Приём взрослых и детей от 7 лет. Запись по телефону 403."
)


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
            files={"filename": (path.name, handle, "image/png")},
        )
    return next(iter(result["images"].values()))["hash"]


def labeled_text(values: list[str], label: str) -> list[dict]:
    return [{"text": value, "adlabels": [{"name": label}]} for value in values]


def creative(hashes: dict[str, str], source: dict) -> dict:
    labels = {
        "feed": "chernavskaya_fgds_feed",
        "compact": "chernavskaya_fgds_compact",
        "vertical": "chernavskaya_fgds_vertical",
        "body": "chernavskaya_fgds_body",
        "title": "chernavskaya_fgds_title",
        "url": "chernavskaya_fgds_url",
    }
    base = {
        "age_min": 13,
        "age_max": 65,
    }
    specs = [
        {
            **base,
            "publisher_platforms": ["facebook", "instagram", "threads"],
            "facebook_positions": [
                "feed",
                "video_feeds",
                "marketplace",
                "profile_feed",
            ],
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
            **base,
            "publisher_platforms": ["facebook"],
            "facebook_positions": ["search"],
        },
        {
            **base,
            "publisher_platforms": ["facebook", "audience_network", "messenger"],
            "facebook_positions": ["right_hand_column"],
            "messenger_positions": ["messenger_home"],
            "audience_network_positions": ["classic"],
        },
        base,
    ]
    image_groups = ("feed", "compact", "compact", "vertical")
    rules = []
    for priority, (spec, group) in enumerate(zip(specs, image_groups), start=1):
        rules.append(
            {
                "customization_spec": spec,
                "image_label": {"name": labels[group]},
                "body_label": {"name": labels["body"]},
                "link_url_label": {"name": labels["url"]},
                "title_label": {"name": labels["title"]},
                "priority": priority,
            }
        )

    result = {
        "name": f"{AD_NAME} | Creative",
        "object_story_spec": copy.deepcopy(source["creative"]["object_story_spec"]),
        "asset_feed_spec": {
            "images": [
                {"hash": hashes[group], "adlabels": [{"name": labels[group]}]}
                for group in ("feed", "compact", "vertical")
            ],
            "bodies": labeled_text(BODIES, labels["body"]),
            "titles": labeled_text(TITLES, labels["title"]),
            "descriptions": [{"text": DESCRIPTION}],
            "link_urls": [
                {
                    "website_url": URL,
                    "display_url": "https://kravira.by",
                    "adlabels": [{"name": labels["url"]}],
                }
            ],
            "call_to_action_types": ["LEARN_MORE"],
            "ad_formats": ["AUTOMATIC_FORMAT"],
            "optimization_type": "PLACEMENT",
            "asset_customization_rules": rules,
        },
    }
    if source["creative"].get("degrees_of_freedom_spec"):
        result["degrees_of_freedom_spec"] = copy.deepcopy(
            source["creative"]["degrees_of_freedom_spec"]
        )
    return result


def main() -> int:
    for path in FILES.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    state = (
        json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if STATE_FILE.exists()
        else {"hashes": {}}
    )
    source = get(
        SOURCE_AD_ID,
        {
            "fields": (
                "id,name,status,effective_status,adset{id,name},"
                "creative{id,name,object_story_spec,degrees_of_freedom_spec}"
            )
        },
    )
    if source.get("effective_status") != "ACTIVE" or source["adset"]["id"] != ADSET_ID:
        raise RuntimeError("Reference ad is no longer active in the target ad set")

    for group, path in FILES.items():
        if group not in state["hashes"]:
            state["hashes"][group] = upload(path)
            save(state)
            print(f"uploaded {group} {state['hashes'][group]}")

    if not state.get("ad_id"):
        result = request(
            "POST",
            f"{ACCOUNT}/ads",
            data={
                "name": AD_NAME,
                "adset_id": ADSET_ID,
                "creative": json.dumps(
                    creative(state["hashes"], source), ensure_ascii=False
                ),
                "status": "ACTIVE",
            },
        )
        state.update(
            {
                "ad_id": result["id"],
                "status": "ACTIVE",
                "adset_id": ADSET_ID,
                "source_ad_id": SOURCE_AD_ID,
                "url": URL,
            }
        )
        save(state)

    state["verification"] = get(
        state["ad_id"],
        {
            "fields": (
                "id,name,status,effective_status,adset{id,name,status,effective_status},"
                "creative{id,name,object_story_spec,asset_feed_spec}"
            )
        },
    )
    save(state)
    print(json.dumps(state["verification"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
