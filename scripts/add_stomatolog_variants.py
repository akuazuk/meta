"""Доставить комплекты 2 и 4 в группу «Стоматологи» (вторая Касацкая и вторая Михневич)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.create_kardiolog_vacancy import build_creative, graph, upload_image
from src.config import get_mrs_settings

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "image" / "concepts" / "stomatolog"
STATE_PATH = ROOT / "tmp_refs" / "add_stomatolog_variants.json"
ADSET_ID = "120248094786100434"
LINK = (
    "https://kravira.by/o-companii/vacancy/"
    "?utm_source=facebook&utm_medium=cpc&utm_campaign=vacancy_stomatolog"
)
URL_TAGS = "utm_source=facebook&utm_medium=cpc&utm_campaign=vacancy_stomatolog"

ADS = [
    {
        "key": "3",
        "name": "Стоматолог — 3",
        "sq": "Вакант_стом_2.png",
        "vt": "Вакант_стом2.png",
        "ls": "стом2.png",
        "bodies": [
            "Ищем врача, которому важны поток и спокойный график. Вакансия стоматолога-терапевта – на сайте.",
            "Откликнитесь сегодня: вакансия стоматолога-терапевта в медицинском центре Кравира, Минск.",
            "Достойный уровень оплаты труда, гибкий график и стабильный поток пациентов.",
            "Ищем стоматолога-терапевта в клинику, где ценят врачей. Подробности на сайте.",
            "Гибкий график и понятная загрузка: стабильный поток пациентов, без ночных дежурств стационара.",
            "Медицинский центр Кравира приглашает стоматолога-терапевта. Условия и отклик – на сайте, без формы в объявлении.",
            "Если ищете работу в частной клинике Минска с достойной оплатой – откликнитесь на вакансию.",
            "Стабильный поток пациентов и поддержка команды. Смотрите вакансию стоматолога-терапевта на сайте Кравира.",
            "Гибкий график, достойная оплата и клиника в Минске. Откройте вакансию и откликнитесь, если это про вас.",
            "Частная клиника, где ценят врача: оплата, график, поток пациентов. Подробности на сайте Кравира.",
        ],
        "titles": [
            "Откликнитесь на вакансию сегодня",
            "Ищем стоматолога-терапевта",
            "Достойная оплата труда",
            "Гибкий график и стабильный поток",
            "Вакансия стоматолога в Минске",
            "Клиника, где ценят врачей",
            "Работа в Кравира – Минск",
            "Стабильный поток пациентов",
            "Гибкий график для врача",
            "Стоматолог-терапевт в Кравира",
        ],
        "description": (
            "Вакансия стоматолога-терапевта в медицинском центре Кравира, Минск. Отклик на сайте."
        ),
    },
    {
        "key": "4",
        "name": "Стоматолог — 4",
        "sq": "Вакант_стом_4.png",
        "vt": "Вакант_стом4.png",
        "ls": "стом4.png",
        "bodies": [
            "Разыскивается стоматолог-терапевт. Работайте в клинике с заботой о пациентах и врачах.",
            "Если хотите частную клинику, где считают и пациента, и врача – откройте вакансию Кравира на сайте.",
            "Более 25 лет на рынке. Ищем стоматолога-терапевта, которому важны команда и спокойная работа с пациентами.",
            "Медицинский центр Кравира, Минск. Отклик на вакансию стоматолога-терапевта – на сайте.",
            "Гибкий график, достойная оплата и поддержка команды. Откликнитесь сегодня.",
            "Привлекательные условия сотрудничества и стабильный поток пациентов. Подробности на сайте.",
            "Приглашаем стоматолога-терапевта в команду Кравира. Работа в надёжной компании с историей более 25 лет.",
            "Команда Кравира приглашает стоматолога-терапевта. Без формы в объявлении – условия на сайте.",
            "Надёжная компания с историей более 25 лет ищет стоматолога-терапевта в Минске. Перейдите и откликнитесь.",
            "Привлекательные условия сотрудничества: график, поток, поддержка. Вакансия стоматолога-терапевта в Минске.",
        ],
        "titles": [
            "Разыскивается стоматолог-терапевт",
            "Забота о пациентах и врачах",
            "Надёжная клиника, 25 лет",
            "Откликнитесь на вакансию на сайте",
            "Стоматолог-терапевт, Минск",
            "Привлекательные условия сотрудничества",
            "Работа в клинике с заботой о врачах",
            "Компания с историей 25 лет",
            "В команду Кравира",
            "Приглашаем стоматолога-терапевта",
        ],
        "description": (
            "Вакансия стоматолога-терапевта в медицинском центре Кравира, Минск. Отклик на сайте."
        ),
    },
]


def local_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {}


def save_local(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    mrs = get_mrs_settings()
    version = mrs.graph_api_version or "v25.0"
    state = local_state()
    state.setdefault("hashes", {})
    state.setdefault("creatives", {})
    state.setdefault("ads", {})

    for spec in ADS:
        for kind in ("sq", "vt", "ls"):
            key = f"{spec['key']}_{kind}"
            if key in state["hashes"]:
                continue
            path = ASSETS / spec[kind]
            if not path.is_file():
                raise FileNotFoundError(path)
            state["hashes"][key] = upload_image(mrs, path)
            save_local(state)
            print(f"[uploaded] {path.name} → {state['hashes'][key]}")

    # build_creative uses kardiolog URL/tags from that module; override after.
    import scripts.create_kardiolog_vacancy as kard

    old_link, old_tags = kard.LINK, kard.URL_TAGS
    kard.LINK, kard.URL_TAGS = LINK, URL_TAGS
    try:
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
            payload["name"] = spec["name"]
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
            save_local(state)
            print(f"[created] creative {spec['name']} → {created['id']}")
    finally:
        kard.LINK, kard.URL_TAGS = old_link, old_tags

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
                "adset_id": ADSET_ID,
                "creative": json.dumps({"creative_id": state["creatives"][spec["key"]]}),
                "status": "ACTIVE",
            },
        )
        state["ads"][spec["key"]] = ad["id"]
        save_local(state)
        print(f"[created] ad {spec['name']} → {ad['id']}")

    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
