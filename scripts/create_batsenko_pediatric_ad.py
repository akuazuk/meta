"""Upload the Batsenko pediatric-urology banner set and create one PAUSED Meta ad."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.create_laser_format_replacements import ACCOUNT, get, request


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "image" / "concepts" / "batsenko_pediatric"
STATE_FILE = ROOT / "tmp_refs" / "batsenko_pediatric" / "meta_state.json"
ADSET_ID = "120250631182860770"
AD_NAME = "Баценко_Детский_уролог__FORMAT_SAFE_2026-08-11"
URL = "https://kravira.by/staff/urologiya-vrachi/batsenko-aleksandr-olegovich/"

FILES = {
    "compact": ASSETS / "batsenko_pediatric_1x1.jpg",
    "feed": ASSETS / "batsenko_pediatric_4x5.jpg",
    "vertical": ASSETS / "batsenko_pediatric_9x16.jpg",
}

BODIES = [
    "Ребёнок боится сказать, что болит? Фимоз, покраснение и воспаление - повод обратиться к урологу.",
    "Боль или дискомфорт при мочеиспускании у ребёнка не стоит оставлять без внимания. Запишитесь на консультацию к врачу-урологу.",
    "Детское обрезание проводится по медицинским показаниям после консультации врача.",
    "Фимоз, повторные воспаления, покраснение или дискомфорт - обсудите симптомы с врачом-урологом.",
]
TITLES = [
    "Приём детей у уролога",
    "Фимоз у ребёнка",
    "Детское обрезание по показаниям",
    "Баценко Александр Олегович",
]
DESCRIPTIONS = [
    "Врач-уролог-андролог высшей категории",
    "Консультация и выбор тактики лечения",
    "Запись по телефону 403",
]


def save(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def upload(path: Path) -> str:
    with path.open("rb") as handle:
        result = request(
            "POST",
            f"{ACCOUNT}/adimages",
            files={"filename": (path.name, handle, "image/jpeg")},
        )
    return next(iter(result["images"].values()))["hash"]


def labeled_text(values: list[str], label: str) -> list[dict]:
    return [{"text": value, "adlabels": [{"name": label}]} for value in values]


def creative(hashes: dict[str, str]) -> dict:
    labels = {
        "feed": "batsenko_child_feed",
        "compact": "batsenko_child_compact",
        "vertical": "batsenko_child_vertical",
        "body": "batsenko_child_body",
        "title": "batsenko_child_title",
        "url": "batsenko_child_url",
    }
    description_labels = [f"batsenko_child_description_{i}" for i in range(1, 4)]
    rules = []
    specs = [
        {
            "age_min": 13,
            "age_max": 65,
            "publisher_platforms": ["facebook", "instagram", "threads"],
            "facebook_positions": ["feed", "video_feeds", "marketplace", "profile_feed"],
            "instagram_positions": ["stream", "explore", "explore_home", "profile_feed", "ig_search"],
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
    for priority, (group, spec, description_label) in enumerate(
        zip(("feed", "compact", "vertical"), specs, description_labels), start=1
    ):
        rules.append(
            {
                "customization_spec": spec,
                "image_label": {"name": labels[group]},
                "body_label": {"name": labels["body"]},
                "title_label": {"name": labels["title"]},
                "description_label": {"name": description_label},
                "link_url_label": {"name": labels["url"]},
                "priority": priority,
            }
        )
    descriptions = [
        {"text": value, "adlabels": [{"name": label}]}
        for value, label in zip(DESCRIPTIONS, description_labels)
    ]
    return {
        "name": f"{AD_NAME} | Creative",
        "object_story_spec": {
            "page_id": "265643990153763",
            "instagram_user_id": "17841404399569974",
        },
        "asset_feed_spec": {
            "images": [
                {"hash": hashes[group], "adlabels": [{"name": labels[group]}]}
                for group in ("feed", "compact", "vertical")
            ],
            "bodies": labeled_text(BODIES, labels["body"]),
            "titles": labeled_text(TITLES, labels["title"]),
            "descriptions": descriptions,
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


def main() -> int:
    state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {"hashes": {}}
    if state.get("ad_id"):
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0
    for group, path in FILES.items():
        if group not in state["hashes"]:
            state["hashes"][group] = upload(path)
            save(state)
            print(f"uploaded {group} {state['hashes'][group]}")
    result = request(
        "POST",
        f"{ACCOUNT}/ads",
        data={
            "name": AD_NAME,
            "adset_id": ADSET_ID,
            "creative": json.dumps(creative(state["hashes"]), ensure_ascii=False),
            "status": "PAUSED",
        },
    )
    state.update({"ad_id": result["id"], "status": "PAUSED", "adset_id": ADSET_ID})
    save(state)
    verified = get(
        result["id"],
        {"fields": "id,name,status,effective_status,adset{id,name},creative{id,asset_feed_spec}"},
    )
    print(json.dumps(verified, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
