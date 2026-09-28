"""Upload Lugovskaya Batsenko-style squares and create PAUSED Meta ads.

The vertical source images remain assigned to Stories/Reels. The new 1:1
images are assigned to feed and compact placements. Previous V2 replacements
are kept paused and renamed so the transition is recoverable.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts.create_laser_format_replacements import ACCOUNT, get, request
from scripts.create_missing_format_replacements import dynamic_source
from scripts.migrate_other_active_formats import create_replacement


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tmp_refs" / "all_format_fix" / "design_sources" / "manifest.json"
V2_STATE = ROOT / "tmp_refs" / "all_format_fix" / "corrected_square_state.json"
STATE = ROOT / "tmp_refs" / "all_format_fix" / "lugovskaya_batsenko_style_v3_state.json"
ASSETS = ROOT / "image" / "concepts" / "all_format_fix"
TARGET_ADSET = "120250631198310770"
SOURCE_IDS = ("120250487253590770", "120250487246110770")

COPY = {
    "120250487253590770": {
        "bodies": [
            "Телевизор стал громче, чем разговоры? Проверьте слух у ЛОР-врача. Запись в медицинский центр Кравира - 403.",
            "Просите повторить сказанное всё чаще? Не привыкайте к дискомфорту - проверьте слух у специалиста.",
            "Снижение слуха может развиваться постепенно. Консультация ЛОР-врача поможет разобраться в причине.",
            "Проверьте слух, если речь стала менее разборчивой, а привычная громкость - недостаточной.",
        ],
        "titles": [
            "Проверьте слух у ЛОР-врача",
            "Телевизор стал громче?",
            "Приём ЛОР-врача в Кравира",
            "Не откладывайте проверку слуха",
        ],
        "descriptions": [
            "Луговская Татьяна Евгеньевна - врач высшей категории",
            "Запись на консультацию - 403",
            "Медицинский центр Кравира",
        ],
    },
    "120250487246110770": {
        "bodies": [
            "Голос пропал без предупреждения? Причину лучше не угадывать - обратитесь к ЛОР-врачу.",
            "Осиплость и дискомфорт в горле не проходят? Запишитесь на консультацию к специалисту.",
            "Голос изменился или быстро устаёт? ЛОР-врач поможет определить причину и дальнейшие шаги.",
            "Не ждите, пока голос восстановится сам. Пройдите осмотр у ЛОР-врача в медицинском центре Кравира.",
        ],
        "titles": [
            "Голос пропал? Обратитесь к ЛОР-врачу",
            "Причину осиплости лучше проверить",
            "Приём ЛОР-врача в Кравира",
            "Запишитесь на консультацию",
        ],
        "descriptions": [
            "Луговская Татьяна Евгеньевна - врач высшей категории",
            "Запись на консультацию - 403",
            "Медицинский центр Кравира",
        ],
    },
}


def save(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def upload(path: Path) -> str:
    with path.open("rb") as handle:
        result = request(
            "POST",
            f"{ACCOUNT}/adimages",
            files={"filename": (path.name, handle, "image/jpeg")},
        )
    return next(iter(result["images"].values()))["hash"]


def source_with_copy(entry: dict) -> dict:
    ad = dynamic_source(entry)
    ad["name"] = f"{entry['name']}__BATSENKO_STYLE_V3"
    copy_set = COPY[entry["id"]]
    feed = ad["creative"]["asset_feed_spec"]
    feed["bodies"] = [{"text": text} for text in copy_set["bodies"]]
    feed["titles"] = [{"text": text} for text in copy_set["titles"]]
    feed["descriptions"] = [{"text": text} for text in copy_set["descriptions"]]
    return ad


def mark_previous_v2(ad_id: str) -> None:
    current = get(ad_id, {"fields": "id,name,status,effective_status"})
    name = current.get("name", ad_id)
    suffix = "__OLD_NOT_BATSENKO_STYLE"
    if not name.endswith(suffix):
        name += suffix
    request("POST", ad_id, data={"name": name, "status": "PAUSED"})


def main() -> int:
    manifest = {
        item["id"]: item
        for item in json.loads(MANIFEST.read_text(encoding="utf-8"))
        if item["id"] in SOURCE_IDS
    }
    v2 = json.loads(V2_STATE.read_text(encoding="utf-8"))
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}

    for source_id in SOURCE_IDS:
        entry = manifest[source_id]
        item = state.setdefault(source_id, {})
        asset = ASSETS / f"{source_id}_square_batsenko_style_v3.jpg"
        if not item.get("square_hash"):
            item["square_hash"] = upload(asset)
            item["square_path"] = str(asset)
            save(state)
            print(f"uploaded {source_id} {item['square_hash']}")

        if not item.get("replacement_ad_id"):
            original_vertical_hash = entry["images"][0]["hash"]
            selected = {
                "feed": item["square_hash"],
                "compact": item["square_hash"],
                "vertical": original_vertical_hash,
                "dimensions": {
                    "feed": "1080x1080",
                    "compact": "1080x1080",
                    "vertical": "1080x1920",
                },
            }
            item["replacement_ad_id"] = create_replacement(
                source_with_copy(copy.deepcopy(entry)), selected, TARGET_ADSET
            )
            item["target_adset_id"] = TARGET_ADSET
            item["status"] = "PAUSED"
            item["vertical_hash"] = original_vertical_hash
            save(state)
            print(f"created {item['replacement_ad_id']} <- {source_id}")

        previous_id = v2[source_id]["replacement_ad_id"]
        if not item.get("previous_v2_marked"):
            mark_previous_v2(previous_id)
            item["previous_v2_ad_id"] = previous_id
            item["previous_v2_marked"] = True
            save(state)
            print(f"marked previous V2 {previous_id}")

        item["verification"] = get(
            item["replacement_ad_id"],
            {
                "fields": (
                    "id,name,status,effective_status,adset{id,name},"
                    "creative{id,name,asset_feed_spec}"
                )
            },
        )
        save(state)

    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
