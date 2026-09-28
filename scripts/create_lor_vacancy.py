"""Группа вакансии ЛОР-врача в кампании «Вакансии»."""

from __future__ import annotations

import json
from pathlib import Path

import scripts.create_kardiolog_vacancy as kard
from scripts.create_kardiolog_vacancy import (
    build_creative,
    create_adset,
    geo_minsk,
    graph,
    upload_image,
)
from src.config import get_mrs_settings

ASSETS = Path(__file__).resolve().parents[1] / "image" / "concepts" / "lor_job"
STATE_PATH = Path(__file__).resolve().parents[1] / "tmp_refs" / "create_lor_vacancy.json"
LINK = (
    "https://kravira.by/o-companii/vacancy/"
    "?utm_source=facebook&utm_medium=cpc&utm_campaign=vacancy_lor"
)
URL_TAGS = "utm_source=facebook&utm_medium=cpc&utm_campaign=vacancy_lor"

ADS = [
    {
        "key": "1",
        "name": "ЛОР — 1",
        "sq": "sq1.png",
        "vt": "vt1.png",
        "ls": "ls1.png",
        "bodies": [
            "Вакансия ЛОР-врача: амбулаторный приём взрослых и детей. Условия и отклик – на сайте.",
            "Стабильный поток пациентов и оборудованный кабинет. Вакансия ЛОР-врача в Кравира, Минск.",
            "Достойная оплата и поддержка команды. Ищем ЛОР-врача в частную клинику.",
            "Ищем ЛОР-врача, которому важны поток и спокойный график. Подробности на сайте.",
            "Медицинский центр Кравира приглашает ЛОР-врача. Отклик – на сайте, без формы в объявлении.",
            "Если ищете работу в частной клинике Минска с достойной оплатой – откликнитесь на вакансию.",
            "Приём взрослых и детей, оборудованный кабинет, поддержка команды. Смотрите вакансию на сайте.",
            "Гибкий график, достойная оплата и клиника в Минске. Откройте вакансию и откликнитесь, если это про вас.",
            "Частная клиника, где ценят врача: оплата, график, поток пациентов. Подробности на сайте Кравира.",
            "Стабильный поток пациентов и понятная загрузка. Вакансия ЛОР-врача – на сайте.",
        ],
        "titles": [
            "Вакансия ЛОР-врача в Минске",
            "Приём взрослых и детей",
            "Стабильный поток пациентов",
            "Достойная оплата труда",
            "Оборудованный кабинет",
            "Ищем ЛОР-врача",
            "Работа в Кравира – Минск",
            "Клиника, где ценят врачей",
            "Откликнитесь на вакансию сегодня",
            "ЛОР-врач в Кравира",
        ],
        "description": (
            "Вакансия ЛОР-врача в медицинском центре Кравира, Минск. Отклик на сайте."
        ),
    },
    {
        "key": "2",
        "name": "ЛОР — 2",
        "sq": "sq2.png",
        "vt": "vt2.png",
        "ls": "ls2.png",
        "bodies": [
            "Мы в поиске оперирующего ЛОР-врача. Работа в частной клинике Кравира, Минск.",
            "Сильная команда коллег и достойная оплата. Вакансия оперирующего ЛОР-врача – на сайте.",
            "Если хотите частную клинику и операционную практику – откройте вакансию на сайте.",
            "Медицинский центр Кравира, Минск. Отклик на вакансию оперирующего ЛОР-врача – на сайте.",
            "Привлекательные условия сотрудничества и поддержка команды. Откликнитесь сегодня.",
            "Разыскивается оперирующий ЛОР-врач. Работайте в клинике с заботой о пациентах и врачах.",
            "Приглашаем оперирующего ЛОР-врача в команду Кравира. Надёжная компания с историей более 25 лет.",
            "Команда Кравира приглашает ЛОР-врача. Без формы в объявлении – условия на сайте.",
            "Надёжная компания с историей более 25 лет ищет оперирующего ЛОР-врача в Минске.",
            "Работа в частной клинике: команда, оплата, операционная практика. Подробности на сайте.",
        ],
        "titles": [
            "Ищем оперирующего ЛОР-врача",
            "Работа в частной клинике",
            "Сильная команда коллег",
            "Достойная оплата труда",
            "Вакансия ЛОР-врача в Минске",
            "Откликнитесь на вакансию на сайте",
            "В команду Кравира",
            "Оперирующий ЛОР, Минск",
            "Привлекательные условия сотрудничества",
            "Приглашаем ЛОР-врача",
        ],
        "description": (
            "Вакансия оперирующего ЛОР-врача в медицинском центре Кравира, Минск. Отклик на сайте."
        ),
    },
]


def targeting_lor() -> dict:
    return {
        "age_min": 28,
        "age_max": 55,
        "flexible_spec": [
            {
                "interests": [
                    {"id": "6003472520687", "name": "Medical school"},
                    {"id": "6003113030700", "name": "Medical education"},
                    {"id": "6003605316673", "name": "Residency (medicine)"},
                ],
            },
            {
                "education_majors": [
                    {"id": "105480999485471", "name": "Doctor of Medicine"},
                    {"id": "109247529092920", "name": "Internal medicine"},
                    {"id": "178310782214302", "name": "General Medicine (MD)"},
                ],
            },
            {
                "work_positions": [
                    {"id": "1574620286090190", "name": "Otorhinolaryngologists"},
                    {"id": "107402372623035", "name": "Doctor"},
                    {"id": "105480999485471", "name": "Doctor of Medicine"},
                    {"id": "649354901854686", "name": "Medical Doctor (MD)"},
                    {"id": "106165199414900", "name": "Attending physician"},
                    {"id": "105517002815720", "name": "General practitioner"},
                    {"id": "109247529092920", "name": "Internal medicine"},
                ],
            },
        ],
        "geo_locations": geo_minsk(),
        "locales": [17],
        "brand_safety_content_filter_levels": [
            "FACEBOOK_RELAXED",
            "AN_RELAXED",
            "FEED_RELAXED",
        ],
        "targeting_automation": {
            "advantage_audience": 0,
            "individual_setting": {"geo": 1},
        },
    }


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    mrs = get_mrs_settings()
    version = mrs.graph_api_version or "v25.0"
    state = load_state()

    if not state.get("adset_id"):
        state["adset_id"] = create_adset(mrs, "ЛОР", targeting_lor())
        save_state(state)
        print(f"[created] adset {state['adset_id']}")
    else:
        print(f"[reused] adset {state['adset_id']}")

    state.setdefault("hashes", {})
    for spec in ADS:
        for kind in ("sq", "vt", "ls"):
            key = f"{spec['key']}_{kind}"
            if key in state["hashes"]:
                continue
            path = ASSETS / spec[kind]
            if not path.is_file():
                raise FileNotFoundError(path)
            state["hashes"][key] = upload_image(mrs, path)
            save_state(state)
            print(f"[uploaded] {path.name} → {state['hashes'][key]}")

    old_link, old_tags = kard.LINK, kard.URL_TAGS
    kard.LINK, kard.URL_TAGS = LINK, URL_TAGS
    try:
        state.setdefault("creatives", {})
        for spec in ADS:
            if spec["key"] in state["creatives"]:
                print(f"[reused] creative {spec['name']}")
                continue
            hashes = {
                "sq": state["hashes"][f"{spec['key']}_sq"],
                "ls": state["hashes"][f"{spec['key']}_ls"],
                "vt": state["hashes"][f"{spec['key']}_vt"],
            }
            payload = build_creative(spec, hashes)
            created = graph(
                mrs.access_token,
                version,
                "POST",
                f"{mrs.ad_account_ref}/adcreatives",
                data={
                    k: json.dumps(v) if isinstance(v, (dict, list)) else v
                    for k, v in payload.items()
                },
            )
            state["creatives"][spec["key"]] = created["id"]
            save_state(state)
            print(f"[created] creative {spec['name']} → {created['id']}")
    finally:
        kard.LINK, kard.URL_TAGS = old_link, old_tags

    state.setdefault("ads", {})
    for spec in ADS:
        if spec["key"] in state["ads"]:
            print(f"[reused] ad {spec['name']}")
            continue
        ad = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/ads",
            data={
                "name": spec["name"],
                "adset_id": state["adset_id"],
                "creative": json.dumps({"creative_id": state["creatives"][spec["key"]]}),
                "status": "ACTIVE",
            },
        )
        state["ads"][spec["key"]] = ad["id"]
        save_state(state)
        print(f"[created] ad {spec['name']} → {ad['id']}")

    print("[complete] ЛОР ACTIVE")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
