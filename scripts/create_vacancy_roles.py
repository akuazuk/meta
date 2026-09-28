"""Вакансии эндокринолога, терапевта и медсестры в кампании «Вакансии»."""

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

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "tmp_refs" / "create_vacancy_roles.json"

MED_INTERESTS = [
    {"id": "6003472520687", "name": "Medical school"},
    {"id": "6003113030700", "name": "Medical education"},
    {"id": "6003605316673", "name": "Residency (medicine)"},
]
MD_MAJORS = [
    {"id": "105480999485471", "name": "Doctor of Medicine"},
    {"id": "109247529092920", "name": "Internal medicine"},
    {"id": "178310782214302", "name": "General Medicine (MD)"},
]
MD_POSITIONS = [
    {"id": "107402372623035", "name": "Doctor"},
    {"id": "105480999485471", "name": "Doctor of Medicine"},
    {"id": "649354901854686", "name": "Medical Doctor (MD)"},
    {"id": "106165199414900", "name": "Attending physician"},
    {"id": "105517002815720", "name": "General practitioner"},
    {"id": "109247529092920", "name": "Internal medicine"},
]


def targeting_doctor(*, extra_majors=None, extra_positions=None) -> dict:
    majors = list(MD_MAJORS)
    positions = list(MD_POSITIONS)
    for item in extra_majors or []:
        if item["id"] not in {x["id"] for x in majors}:
            majors.append(item)
    for item in extra_positions or []:
        if item["id"] not in {x["id"] for x in positions}:
            positions.append(item)
    return {
        "age_min": 28,
        "age_max": 55,
        "flexible_spec": [
            {"interests": MED_INTERESTS},
            {"education_majors": majors},
            {"work_positions": positions},
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


JOBS = [
    {
        "key": "endocrin",
        "adset_name": "Эндокринологи",
        "assets": ROOT / "image" / "concepts" / "endocrin_job",
        "link": (
            "https://kravira.by/o-companii/vacancy/"
            "?utm_source=facebook&utm_medium=cpc&utm_campaign=vacancy_endocrinolog"
        ),
        "url_tags": "utm_source=facebook&utm_medium=cpc&utm_campaign=vacancy_endocrinolog",
        "targeting": targeting_doctor(
            extra_majors=[{"id": "109375782414787", "name": "Endocrinology"}],
            extra_positions=[
                {"id": "1785326215026542", "name": "Endocrinologist"},
                {"id": "109375782414787", "name": "Endocrinology"},
            ],
        ),
        "ads": [
            {
                "key": "1",
                "name": "Эндокринолог — 1",
                "sq": "Вакант_эндокрин_1.png",
                "vt": "Вакант_ЭНДОКРИНОЛОГ1.png",
                "ls": "эндокринолог1.png",
                "bodies": [
                    "Вакансия эндокринолога: ждём именно вас в медицинском центре Кравира, Минск.",
                    "Гибкий график, достойная оплата и стабильный поток пациентов. Отклик – на сайте.",
                    "Ищем врача-эндокринолога в частную клинику. Условия и отклик – на сайте.",
                    "Стабильный поток пациентов и спокойный график. Вакансия эндокринолога в Кравира.",
                    "Медицинский центр Кравира приглашает эндокринолога. Без формы в объявлении – смотрите сайт.",
                    "Если ищете работу в частной клинике Минска с достойной оплатой – откликнитесь на вакансию.",
                    "Гибкий график и понятная загрузка. Откройте вакансию эндокринолога на сайте.",
                    "Частная клиника, где ценят врача: оплата, график, поток пациентов. Подробности на сайте.",
                    "Достойная оплата и поддержка команды. Ищем эндокринолога в Кравира, Минск.",
                    "Ждём эндокринолога в команду. Условия – на сайте, отклик без формы в объявлении.",
                ],
                "titles": [
                    "Вакансия эндокринолога в Минске",
                    "Ждём вас в Кравира",
                    "Гибкий график и достойная оплата",
                    "Стабильный поток пациентов",
                    "Ищем эндокринолога",
                    "Работа в Кравира – Минск",
                    "Клиника, где ценят врачей",
                    "Откликнитесь на вакансию сегодня",
                    "Эндокринолог в Кравира",
                    "Достойная оплата труда",
                ],
                "description": (
                    "Вакансия эндокринолога в медицинском центре Кравира, Минск. Отклик на сайте."
                ),
            },
            {
                "key": "2",
                "name": "Эндокринолог — 2",
                "sq": "Вакант_эндокрин_2.png",
                "vt": "Вакант_ЭНДОКРИНОЛОГ2.png",
                "ls": "эндокринолог2.png",
                "bodies": [
                    "Ищем эндокринолога. Пациенты, которые 25 лет выбирают Кравира, ждут своего врача.",
                    "Стабильный поток пациентов, сильная команда коллег и гибкий график. Отклик – на сайте.",
                    "Выберите пациентов, которые 25 лет выбирают нас. Вакансия эндокринолога в Минске.",
                    "Надёжная компания с историей более 25 лет ищет эндокринолога. Перейдите и откликнитесь.",
                    "Сильная команда и достойная оплата. Вакансия эндокринолога – на сайте Кравира.",
                    "Приглашаем эндокринолога в команду Кравира. Работа в клинике с заботой о пациентах и врачах.",
                    "Если важны поток, команда и спокойный график – откройте вакансию на сайте.",
                    "Команда Кравира приглашает эндокринолога. Без формы в объявлении – условия на сайте.",
                    "Привлекательные условия сотрудничества и стабильный поток. Подробности на сайте.",
                    "Работа в частной клинике: команда, оплата, пациенты. Вакансия эндокринолога в Минске.",
                ],
                "titles": [
                    "Ищем эндокринолога",
                    "Пациенты выбирают нас 25 лет",
                    "Сильная команда коллег",
                    "Стабильный поток пациентов",
                    "Вакансия эндокринолога в Минске",
                    "Откликнитесь на вакансию на сайте",
                    "В команду Кравира",
                    "Гибкий график для врача",
                    "Привлекательные условия сотрудничества",
                    "Приглашаем эндокринолога",
                ],
                "description": (
                    "Вакансия эндокринолога в медицинском центре Кравира, Минск. Отклик на сайте."
                ),
            },
        ],
    },
    {
        "key": "terapevt",
        "adset_name": "Терапевты",
        "assets": ROOT / "image" / "concepts" / "terapevt_job",
        "link": (
            "https://kravira.by/o-companii/vacancy/"
            "?utm_source=facebook&utm_medium=cpc&utm_campaign=vacancy_terapevt"
        ),
        "url_tags": "utm_source=facebook&utm_medium=cpc&utm_campaign=vacancy_terapevt",
        "targeting": targeting_doctor(
            extra_positions=[
                {"id": "616696405130729", "name": "Internist"},
                {"id": "761820927245398", "name": "Internal Medicine Physician"},
                {"id": "588508654618832", "name": "Internal Medicine Doctor"},
            ],
        ),
        "ads": [
            {
                "key": "1",
                "name": "Терапевт — 1",
                "sq": "Вакант_терап_1.png",
                "vt": "Вакант_терапевт1.png",
                "ls": "тер1.png",
                "bodies": [
                    "Вакансия врача-терапевта: комфортные условия и гибкий график. Отклик – на сайте.",
                    "Обучение за счёт клиники, достойная оплата и поддержка опытных коллег.",
                    "Заведующая терапевтическим отделением приглашает врача-терапевта в команду Кравира.",
                    "Ищем терапевта в частную клинику Минска. Условия и отклик – на сайте.",
                    "Медицинский центр Кравира приглашает врача-терапевта. Без формы в объявлении – смотрите сайт.",
                    "Если важны график, обучение и спокойная работа – откройте вакансию на сайте.",
                    "Гибкий график и поддержка коллег. Вакансия терапевта в Кравира, Минск.",
                    "Частная клиника, где ценят врача: оплата, график, обучение. Подробности на сайте.",
                    "Достойная оплата и понятная загрузка. Ищем врача-терапевта в Минске.",
                    "Комфортные условия в клинике на Захарова. Откликнитесь на вакансию терапевта.",
                ],
                "titles": [
                    "Вакансия терапевта в Минске",
                    "Комфортные условия и гибкий график",
                    "Обучение за счёт клиники",
                    "Ищем врача-терапевта",
                    "Достойная оплата труда",
                    "Работа в Кравира – Минск",
                    "Поддержка опытных коллег",
                    "Откликнитесь на вакансию сегодня",
                    "Врач-терапевт в Кравира",
                    "Клиника, где ценят врачей",
                ],
                "description": (
                    "Вакансия врача-терапевта в медицинском центре Кравира, Минск. Отклик на сайте."
                ),
            },
            {
                "key": "2",
                "name": "Терапевт — 2",
                "sq": "Вакант_терап_2.png",
                "vt": "Вакант_терапевт2.png",
                "ls": "тер2.png",
                "bodies": [
                    "Приглашаем врача-терапевта в команду Кравира. Высокий доход и поддержка продвижения.",
                    "Гибкий график и скидки на услуги клиники для сотрудников и семьи. Отклик – на сайте.",
                    "Работа в частной клинике с понятным доходом. Вакансия терапевта в Минске.",
                    "Заведующая отделением приглашает терапевта. Условия и отклик – на сайте.",
                    "Привлекательные условия сотрудничества: график, доход, скидки для семьи.",
                    "Команда Кравира приглашает врача-терапевта. Без формы в объявлении – условия на сайте.",
                    "Если важны доход и спокойный график – откройте вакансию на сайте.",
                    "Надёжная компания с историей более 25 лет ищет терапевта в Минске.",
                    "Поддержка клиники и понятная загрузка. Вакансия врача-терапевта – на сайте.",
                    "Приглашаем терапевта в команду. Работа в клинике с заботой о пациентах и врачах.",
                ],
                "titles": [
                    "Приглашаем терапевта в команду",
                    "Высокий доход для врача",
                    "Гибкий график и скидки для семьи",
                    "Вакансия терапевта в Минске",
                    "Откликнитесь на вакансию на сайте",
                    "В команду Кравира",
                    "Привлекательные условия сотрудничества",
                    "Работа в частной клинике",
                    "Врач-терапевт, Минск",
                    "Приглашаем врача-терапевта",
                ],
                "description": (
                    "Вакансия врача-терапевта в медицинском центре Кравира, Минск. Отклик на сайте."
                ),
            },
        ],
    },
    {
        "key": "medsestra",
        "adset_name": "Медсёстры",
        "assets": ROOT / "image" / "concepts" / "medsestra_job",
        "link": (
            "https://kravira.by/o-companii/vacancy/"
            "?utm_source=facebook&utm_medium=cpc&utm_campaign=vacancy_medsestra"
        ),
        "url_tags": "utm_source=facebook&utm_medium=cpc&utm_campaign=vacancy_medsestra",
        "targeting": {
            "age_min": 22,
            "age_max": 50,
            "flexible_spec": [
                {
                    "interests": [
                        {"id": "6003239593388", "name": "Nurse education"},
                        {"id": "6003113030700", "name": "Medical education"},
                    ],
                },
                {
                    "education_majors": [
                        {"id": "113599041983855", "name": "Nursing"},
                        {"id": "116035531741618", "name": "Master of Science in Nursing"},
                    ],
                },
                {
                    "work_positions": [
                        {"id": "113852765291861", "name": "Registered nurse"},
                        {"id": "115042561841194", "name": "Registered General Nurse"},
                        {"id": "113599041983855", "name": "Nursing"},
                        {"id": "149711751705712", "name": "RN Staff Nurse"},
                        {"id": "107481765941409", "name": "Clinical nurse specialist"},
                        {"id": "107708809258733", "name": "Nurse educator"},
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
        },
        "ads": [
            {
                "key": "1",
                "name": "Медсестра — 1",
                "sq": "Вакант_мед_1.png",
                "vt": "Вакант_медсестра1.png",
                "ls": "мед1.png",
                "bodies": [
                    "Без медсестры даже доктор не волшебник. Медицинский центр Кравира ищет медсестру.",
                    "Обучение за счёт клиники, комфортный график и достойная оплата. Отклик – на сайте.",
                    "Вакансия медсестры в частной клинике Минска. Условия и отклик – на сайте.",
                    "Ищем медсестру в команду Кравира. Без формы в объявлении – смотрите сайт.",
                    "Если важны график, обучение и спокойная работа – откройте вакансию на сайте.",
                    "Комфортный график и поддержка коллег. Вакансия медсестры в Кравира, Минск.",
                    "Достойная оплата и обучение за счёт клиники. Откликнитесь сегодня.",
                    "Частная клиника, где ценят команду. Подробности вакансии медсестры – на сайте.",
                    "МЦ Кравира приглашает медсестру. Гибкий график и понятная загрузка.",
                    "Работа рядом с врачами, которым нужна сильная медсестра. Отклик – на сайте.",
                ],
                "titles": [
                    "Ищем медсестру в Кравира",
                    "Обучение за счёт клиники",
                    "Комфортный график и достойная оплата",
                    "Вакансия медсестры в Минске",
                    "Без медсестры доктор не волшебник",
                    "Откликнитесь на вакансию сегодня",
                    "Работа в Кравира – Минск",
                    "Медсестра в частную клинику",
                    "Достойная оплата труда",
                    "В команду Кравира",
                ],
                "description": (
                    "Вакансия медсестры в медицинском центре Кравира, Минск. Отклик на сайте."
                ),
            },
            {
                "key": "2",
                "name": "Медсестра — 2",
                "sq": "Вакант_мед_2.png",
                "vt": "Вакант_медсестра2.png",
                "ls": "мед2.png",
                "bodies": [
                    "Доктор без медсестры – это как чай без сахара. МЦ Кравира ищет медсестру.",
                    "Поддержка команды, гибкий график и достойная оплата. Отклик – на сайте.",
                    "Приглашаем медсестру в частную клинику Минска. Условия – на сайте.",
                    "Команда Кравира ждёт медсестру. Без формы в объявлении – смотрите сайт.",
                    "Если важны коллеги, график и спокойная работа – откройте вакансию на сайте.",
                    "Гибкий график и понятная загрузка. Вакансия медсестры в Кравира, Минск.",
                    "Достойная оплата и поддержка команды. Откликнитесь сегодня.",
                    "Работа в клинике, где ценят медсестру рядом с врачом. Подробности на сайте.",
                    "Ищем медсестру, без которой приём не состоится. Отклик – на сайте.",
                    "Привлекательные условия: график, команда, оплата. Вакансия медсестры в Минске.",
                ],
                "titles": [
                    "Доктор без медсестры – как чай без сахара",
                    "Ищем медсестру в Кравира",
                    "Поддержка команды и гибкий график",
                    "Вакансия медсестры в Минске",
                    "Откликнитесь на вакансию на сайте",
                    "В команду Кравира",
                    "Достойная оплата труда",
                    "Медсестра в частную клинику",
                    "Привлекательные условия сотрудничества",
                    "Приглашаем медсестру",
                ],
                "description": (
                    "Вакансия медсестры в медицинском центре Кравира, Минск. Отклик на сайте."
                ),
            },
        ],
    },
]


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def apply_job(mrs, version: str, state: dict, job: dict) -> None:
    job_state = state.setdefault(job["key"], {})
    if not job_state.get("adset_id"):
        job_state["adset_id"] = create_adset(mrs, job["adset_name"], job["targeting"])
        save_state(state)
        print(f"[created] adset {job['adset_name']} {job_state['adset_id']}")
    else:
        print(f"[reused] adset {job['adset_name']} {job_state['adset_id']}")

    job_state.setdefault("hashes", {})
    for spec in job["ads"]:
        for kind in ("sq", "vt", "ls"):
            key = f"{spec['key']}_{kind}"
            if key in job_state["hashes"]:
                continue
            path = job["assets"] / spec[kind]
            if not path.is_file():
                raise FileNotFoundError(path)
            job_state["hashes"][key] = upload_image(mrs, path)
            save_state(state)
            print(f"[uploaded] {path.name} → {job_state['hashes'][key]}")

    old_link, old_tags = kard.LINK, kard.URL_TAGS
    kard.LINK, kard.URL_TAGS = job["link"], job["url_tags"]
    try:
        job_state.setdefault("creatives", {})
        for spec in job["ads"]:
            if spec["key"] in job_state["creatives"]:
                print(f"[reused] creative {spec['name']}")
                continue
            hashes = {
                "sq": job_state["hashes"][f"{spec['key']}_sq"],
                "ls": job_state["hashes"][f"{spec['key']}_ls"],
                "vt": job_state["hashes"][f"{spec['key']}_vt"],
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
            job_state["creatives"][spec["key"]] = created["id"]
            save_state(state)
            print(f"[created] creative {spec['name']} → {created['id']}")
    finally:
        kard.LINK, kard.URL_TAGS = old_link, old_tags

    job_state.setdefault("ads", {})
    for spec in job["ads"]:
        if spec["key"] in job_state["ads"]:
            print(f"[reused] ad {spec['name']}")
            continue
        ad = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/ads",
            data={
                "name": spec["name"],
                "adset_id": job_state["adset_id"],
                "creative": json.dumps({"creative_id": job_state["creatives"][spec["key"]]}),
                "status": "ACTIVE",
            },
        )
        job_state["ads"][spec["key"]] = ad["id"]
        save_state(state)
        print(f"[created] ad {spec['name']} → {ad['id']}")


def main() -> int:
    mrs = get_mrs_settings()
    version = mrs.graph_api_version or "v25.0"
    state = load_state()
    for job in JOBS:
        apply_job(mrs, version, state, job)
    print("[complete] эндокринолог, терапевт, медсестра ACTIVE")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
