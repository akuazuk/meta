"""Группа вакансии врача-ортопеда в кампании «Вакансии».

По образцу «ЛОР» / «Кардиологи»: сайт, $5/день, placement-креативы,
locales 17, advantage_audience 0. Оптимизация – пиксель + событие
MRS_FB_hr (доходит до Meta; клик резюме + звонок HR + отправка формы).
"""

from __future__ import annotations

import json
from pathlib import Path

import scripts.create_kardiolog_vacancy as kard
from scripts.create_kardiolog_vacancy import (
    build_creative,
    geo_minsk,
    graph,
    upload_image,
)
from src.config import get_mrs_settings

ASSETS = Path(__file__).resolve().parents[1] / "image" / "concepts" / "ortho_job"
STATE_PATH = Path(__file__).resolve().parents[1] / "tmp_refs" / "create_ortho_vacancy.json"
CAMPAIGN_ID = "120247828518660434"
PIXEL_ID = "1064023126171171"
EVENT_CLICK = "MRS_FB_hr"
DAILY_BUDGET_CENTS = 500
LINK = (
    "https://kravira.by/o-companii/vacancy/"
    "?utm_source=facebook&utm_medium=cpc&utm_campaign=vacancy_ortoped"
)
URL_TAGS = "utm_source=facebook&utm_medium=cpc&utm_campaign=vacancy_ortoped"

ADS = [
    {
        "key": "ortho",
        "name": "Ортопед — 1",
        "sq": "Вакант_орто.png",
        "vt": "Вакант_ортопед.png",
        "ls": "орто.png",
        "bodies": [
            "Вакансия врача-ортопеда: стабильная полная запись и высокий доход. Условия и отклик – на сайте.",
            "Можно совмещать приём с основной работой. Ищем ортопеда в клинику, где ценят врачей.",
            "Гибкий график и стабильный поток пациентов. Вакансия ортопеда в Кравира, Минск.",
            "Медицинский центр Кравира приглашает врача-ортопеда. Отклик – на сайте, без формы в объявлении.",
            "Полная запись и понятная загрузка. Если это про вас – откройте вакансию на сайте.",
            "Достойная оплата и возможность совмещать с основной работой. Подробности на сайте.",
            "Частная клиника в Минске, где ценят врача. Вакансия ортопеда – отклик на сайте.",
            "Ищем врача-ортопеда. Полная запись, высокий доход, гибкий график.",
            "Если важны поток пациентов и спокойный график – откликнитесь на вакансию ортопеда.",
            "Команда Кравира приглашает врача-ортопеда. Без формы в объявлении – условия на сайте.",
        ],
        "titles": [
            "Вакансия ортопеда в Минске",
            "Клиника, где ценят врачей",
            "Стабильная полная запись",
            "Высокий доход для врача",
            "Можно совмещать с работой",
            "Гибкий график и поток",
            "Ищем врача-ортопеда",
            "Откликнитесь на вакансию сегодня",
            "Врач-ортопед в Кравира",
            "Достойная оплата труда",
        ],
        "description": (
            "Вакансия врача-ортопеда в медицинском центре Кравира, Минск. Отклик на сайте."
        ),
    },
]


def targeting_ortho() -> dict:
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
                    {"id": "724868487631614", "name": "Orthopedic Surgeon"},
                    {"id": "771291242957242", "name": "Orthopaedic Doctor"},
                    {
                        "id": "1423257317968087",
                        "name": "Medical Doctor/Orthopaedic Surgery and Sports Medicine",
                    },
                    {"id": "103115629729245", "name": "Traumatología y Ortopedia"},
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


def create_adset(mrs, name: str, targeting: dict) -> str:
    version = mrs.graph_api_version or "v25.0"
    created = graph(
        mrs.access_token,
        version,
        "POST",
        f"{mrs.ad_account_ref}/adsets",
        data={
            "name": name,
            "campaign_id": CAMPAIGN_ID,
            "daily_budget": DAILY_BUDGET_CENTS,
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "OFFSITE_CONVERSIONS",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "destination_type": "WEBSITE",
            "promoted_object": json.dumps(
                {
                    "pixel_id": PIXEL_ID,
                    "custom_event_type": "OTHER",
                    "custom_event_str": EVENT_CLICK,
                }
            ),
            "targeting": json.dumps(targeting),
            "attribution_spec": json.dumps(
                [
                    {"event_type": "CLICK_THROUGH", "window_days": 7},
                    {"event_type": "VIEW_THROUGH", "window_days": 1},
                ]
            ),
            "status": "ACTIVE",
        },
    )
    return created["id"]


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
        state["adset_id"] = create_adset(mrs, "Ортопеды", targeting_ortho())
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

    print("[complete] Ортопеды ACTIVE")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
