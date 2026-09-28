"""Группа вакансии врача-кардиолога в кампании «Вакансии» (MRS).

По образцу «Стоматологи»: конверсия MRS_FB_hr, сайт, $10/день, placement-креативы.
Список медкандидатов из кандидаты.статистика.xlsx + доп. аудитория по должностям/интересам.

    python -m scripts.create_kardiolog_vacancy --apply
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import requests

from src.config import ConfigError, get_mrs_settings

ROOT = Path(__file__).resolve().parents[1]
XLSX_PATH = ROOT / "tmp_refs" / "kandidaty_statistika.xlsx"
CSV_PATH = ROOT / "tmp_refs" / "hr_medical_candidates.csv"
STATE_PATH = ROOT / "tmp_refs" / "create_kardiolog_vacancy.json"
ASSETS = ROOT / "image" / "concepts" / "kardiplog_job"

ACCOUNT = "act_2649521998797481"
CAMPAIGN_ID = "120247828518660434"
PAGE_ID = "265643990153763"
IG_ID = "17841404399569974"
CC_HR = "1036667668966757"
AUDIENCE_NAME = "HR медкандидаты — вакансии + ФИО"
DAILY_BUDGET_CENTS = 1000
BATCH_SIZE = 10_000
LINK = (
    "https://kravira.by/o-companii/vacancy/"
    "?utm_source=facebook&utm_medium=cpc&utm_campaign=vacancy_kardiolog"
)
URL_TAGS = "utm_source=facebook&utm_medium=cpc&utm_campaign=vacancy_kardiolog"

MED_INCLUDE = (
    "кардиолог",
    "терапевт",
    "невролог",
    "узд",
    "узи",
    "оторино",
    "лор",
    "гинеколог",
    "педиатр",
    "стоматолог",
    "офтальмолог",
    "хирург",
    "эндокрин",
    "уролог",
    "онколог",
    "маммолог",
    "гастро",
    "дерматолог",
    "анестезиолог",
    "эндоскоп",
    "травматолог",
    "ортопед",
    "флеболог",
    "пластик",
    "ревматолог",
    "аллерголог",
    "психотерапевт",
    "проктолог",
    "косметолог",
    "врач фд",
    "начмед",
    "медсестра",
    "фельдшер",
    "массажист",
    "логопед",
    "психолог",
    "акушер",
    "врач",
)
MED_EXCLUDE = (
    "рецепшн",
    "колл",
    "бухгалтер",
    "экономист",
    "маркетолог",
    "непрофиль",
    "менеджер",
    "инженер",
    "санитар",
)

ADS = [
    {
        "key": "1",
        "name": "Кардиолог — 1",
        "sq": "Вакант_кард_1.png",
        "vt": "Вакант_кардио.png",
        "ls": "кард1.png",
        "bodies": [
            "Ищем врача, которому важны поток и спокойный график. Вакансия врача-кардиолога – на сайте.",
            "Откликнитесь сегодня: вакансия врача-кардиолога в медицинском центре Кравира, Минск.",
            "Достойный уровень оплаты труда, гибкий график и стабильный поток пациентов.",
            "Ищем врача-кардиолога в клинику, где ценят врачей. Подробности на сайте.",
            "Гибкий график и понятная загрузка: стабильный поток пациентов, без ночных дежурств стационара.",
            "Медицинский центр Кравира приглашает врача-кардиолога. Условия и отклик – на сайте, без формы в объявлении.",
            "Если ищете работу в частной клинике Минска с достойной оплатой – откликнитесь на вакансию.",
            "Стабильный поток пациентов и поддержка команды. Смотрите вакансию врача-кардиолога на сайте Кравира.",
            "Гибкий график, достойная оплата и клиника в Минске. Откройте вакансию и откликнитесь, если это про вас.",
            "Частная клиника, где ценят врача: оплата, график, поток пациентов. Подробности на сайте Кравира.",
        ],
        "titles": [
            "Откликнитесь на вакансию сегодня",
            "Ищем врача-кардиолога",
            "Достойная оплата труда",
            "Гибкий график и стабильный поток",
            "Вакансия кардиолога в Минске",
            "Клиника, где ценят врачей",
            "Работа в Кравира – Минск",
            "Стабильный поток пациентов",
            "Гибкий график для врача",
            "Врач-кардиолог в Кравира",
        ],
        "description": (
            "Вакансия врача-кардиолога в медицинском центре Кравира, Минск. Отклик на сайте."
        ),
    },
    {
        "key": "2",
        "name": "Кардиолог — 2",
        "sq": "Вакант_кард_2.png",
        "vt": "Вакант_кардио2.png",
        "ls": "кард2.png",
        "bodies": [
            "Если хотите частную клинику, где считают и пациента, и врача – откройте вакансию Кравира на сайте.",
            "Более 25 лет на рынке. Ищем врача-кардиолога, которому важны команда и спокойная работа с пациентами.",
            "Медицинский центр Кравира, Минск. Отклик на вакансию врача-кардиолога – на сайте.",
            "Гибкий график, достойная оплата и поддержка команды. Откликнитесь сегодня.",
            "Привлекательные условия сотрудничества и стабильный поток пациентов. Подробности на сайте.",
            "Разыскивается врач-кардиолог. Работайте в клинике с заботой о пациентах и врачах.",
            "Приглашаем врача-кардиолога в команду Кравира. Работа в надёжной компании с историей более 25 лет.",
            "Команда Кравира приглашает врача-кардиолога. Без формы в объявлении – условия на сайте.",
            "Надёжная компания с историей более 25 лет ищет врача-кардиолога в Минске. Перейдите и откликнитесь.",
            "Привлекательные условия сотрудничества: график, поток, поддержка. Вакансия врача-кардиолога в Минске.",
        ],
        "titles": [
            "Забота о пациентах и врачах",
            "Надёжная клиника, 25 лет",
            "Откликнитесь на вакансию на сайте",
            "Врач-кардиолог, Минск",
            "Привлекательные условия сотрудничества",
            "Работа в клинике с заботой о врачах",
            "Разыскивается врач-кардиолог",
            "Компания с историей 25 лет",
            "В команду Кравира",
            "Приглашаем врача-кардиолога",
        ],
        "description": (
            "Вакансия врача-кардиолога в медицинском центре Кравира, Минск. Отклик на сайте."
        ),
    },
    {
        "key": "3",
        "name": "Кардиолог — 3",
        "sq": "Вакант_кард_3.png",
        "vt": "Вакант_кардио3.png",
        "ls": "кард3.png",
        "bodies": [
            "Ищем кардиолога, у которого сердце на месте. Вакансия в медицинском центре Кравира, Минск.",
            "Зарплата, которая не вызывает аритмию. Условия и отклик – на сайте.",
            "Заместитель директора по медицинской части приглашает врача-кардиолога в команду.",
            "Если вам важны пациенты и спокойная работа – откройте вакансию на сайте.",
            "Медицинский центр Кравира, Минск. Отклик на вакансию врача-кардиолога – на сайте.",
            "Гибкий график, достойная оплата и поддержка команды. Откликнитесь сегодня.",
            "Привлекательные условия сотрудничества и стабильный поток пациентов. Подробности на сайте.",
            "Разыскивается врач-кардиолог. Работайте в клинике с заботой о пациентах и врачах.",
            "Приглашаем врача-кардиолога в команду Кравира. Работа в надёжной компании с историей более 25 лет.",
            "Команда Кравира приглашает врача-кардиолога. Без формы в объявлении – условия на сайте.",
        ],
        "titles": [
            "Сердце на месте",
            "Зарплата без аритмии",
            "Ищем кардиолога",
            "Вакансия кардиолога в Минске",
            "Откликнитесь на вакансию на сайте",
            "Врач-кардиолог, Минск",
            "Привлекательные условия сотрудничества",
            "В команду Кравира",
            "Разыскивается врач-кардиолог",
            "Приглашаем врача-кардиолога",
        ],
        "description": (
            "Вакансия врача-кардиолога в медицинском центре Кравира, Минск. Отклик на сайте."
        ),
    },
    {
        "key": "4",
        "name": "Кардиолог — 4",
        "sq": "Вакант_кард_4.png",
        "vt": "Вакант_кардио4.png",
        "ls": "кард4.png",
        "bodies": [
            "Работайте в клинике с заботой о пациентах и врачах. Вакансия кардиолога – на сайте.",
            "Если хотите частную клинику, где считают и пациента, и врача – откройте вакансию Кравира на сайте.",
            "Более 25 лет на рынке. Ищем врача-кардиолога, которому важны команда и спокойная работа с пациентами.",
            "Медицинский центр Кравира, Минск. Отклик на вакансию врача-кардиолога – на сайте.",
            "Гибкий график, достойная оплата и поддержка команды. Откликнитесь сегодня.",
            "Привлекательные условия сотрудничества и стабильный поток пациентов. Подробности на сайте.",
            "Надёжная компания с историей более 25 лет ищет врача-кардиолога в Минске. Перейдите и откликнитесь.",
            "Команда Кравира приглашает врача-кардиолога. Без формы в объявлении – условия на сайте.",
            "Приглашаем врача-кардиолога в команду Кравира. Работа в надёжной компании с историей более 25 лет.",
            "Привлекательные условия сотрудничества: график, поток, поддержка. Вакансия врача-кардиолога в Минске.",
        ],
        "titles": [
            "Забота о пациентах и врачах",
            "Вакансия кардиолога",
            "Работайте в клинике",
            "Врач-кардиолог, Минск",
            "Откликнитесь на вакансию на сайте",
            "Надёжная клиника, 25 лет",
            "Привлекательные условия сотрудничества",
            "В команду Кравира",
            "Приглашаем врача-кардиолога",
            "Компания с историей 25 лет",
        ],
        "description": (
            "Вакансия врача-кардиолога в медицинском центре Кравира, Минск. Отклик на сайте."
        ),
    },
]

DOF = {
    "creative_features_spec": {
        "adapt_to_placement": {"enroll_status": "OPT_OUT"},
        "advantage_plus_creative": {"enroll_status": "OPT_OUT"},
        "text_optimizations": {"enroll_status": "OPT_OUT"},
        "enhance_cta": {"enroll_status": "OPT_OUT"},
        "image_touchups": {"enroll_status": "OPT_OUT"},
        "image_auto_crop": {"enroll_status": "OPT_OUT"},
        "image_animation": {"enroll_status": "OPT_OUT"},
        "add_text_overlay": {"enroll_status": "OPT_OUT"},
        "inline_comment": {"enroll_status": "OPT_OUT"},
        "video_auto_crop": {"enroll_status": "OPT_OUT"},
        "standard_enhancements_catalog": {"enroll_status": "OPT_OUT"},
    }
}


def graph(token: str, version: str, method: str, path: str, **kwargs) -> dict:
    url = f"https://graph.facebook.com/{version}/{path.lstrip('/')}"
    if method == "GET":
        kwargs.setdefault("params", {})["access_token"] = token
    elif "files" not in kwargs:
        kwargs.setdefault("data", {})["access_token"] = token
    else:
        kwargs.setdefault("params", {})["access_token"] = token
    response = requests.request(method, url, timeout=180, **kwargs)
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"Meta non-JSON {path}: {response.text[:400]}") from exc
    if response.status_code != 200:
        err = payload.get("error", {})
        raise RuntimeError(
            err.get("error_user_msg") or err.get("message") or str(payload)
        )
    return payload


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_phone(raw) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, float):
        raw = f"{raw:.0f}"
    digits = re.sub(r"\D", "", str(raw))
    if not digits:
        return None
    if digits.startswith("80") and len(digits) >= 11:
        digits = "375" + digits[2:]
    if digits.startswith("8") and len(digits) == 10:
        digits = "375" + digits[1:]
    if len(digits) == 9 and digits[:2] in {"25", "29", "33", "44"}:
        digits = "375" + digits
    if not digits.startswith("375") or len(digits) < 12:
        return None
    return digits[:12]


def normalize_name(value: str) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"\s+", " ", str(value)).strip().lower()
    if cleaned in {"---", "-", "null", "none"}:
        return None
    return cleaned or None


def split_fio(fio: str) -> tuple[str | None, str | None]:
    parts = [p for p in re.split(r"\s+", fio.strip()) if p]
    if not parts:
        return None, None
    ln = normalize_name(parts[0])
    fn = normalize_name(parts[1]) if len(parts) > 1 else None
    return fn, ln


def is_medical(vacancy: str) -> bool:
    text = vacancy.strip().lower()
    if any(x in text for x in MED_EXCLUDE):
        return False
    return any(x in text for x in MED_INCLUDE)


def add_row(rows: list[dict], *, source: str, vacancy: str, fio: str, phone_raw) -> None:
    phone = normalize_phone(phone_raw)
    fio_n = normalize_name(fio) or ""
    if not phone and not fio_n:
        return
    fn, ln = split_fio(fio) if fio_n else (None, None)
    rows.append(
        {
            "source": source,
            "vacancy": (vacancy or "").strip(),
            "fio": (fio or "").strip(),
            "phone": phone or "",
            "fn": fn or "",
            "ln": ln or "",
        }
    )


def parse_workbook() -> list[dict]:
    import openpyxl

    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True, read_only=True)
    rows: list[dict] = []

    ws = wb["2022-2024"]
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue
        vacancy = "" if row[1] is None else str(row[1])
        fio = "" if row[5] is None else str(row[5])
        if not is_medical(vacancy):
            continue
        add_row(rows, source="2022-2024", vacancy=vacancy, fio=fio, phone_raw=row[6])

    ws = wb["  Лариса_Список"] if "  Лариса_Список" in wb.sheetnames else None
    if ws is None:
        for name in wb.sheetnames:
            if "Лариса" in name:
                ws = wb[name]
                break
    if ws is not None:
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                continue
            fio = "" if row[0] is None else str(row[0])
            spec = "" if row[1] is None else str(row[1])
            add_row(rows, source="Лариса_Список", vacancy=spec, fio=fio, phone_raw=row[2])

    ws = wb["кандидаты HH"]
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue
        spec = "" if row[1] is None else str(row[1])
        fio = "" if row[2] is None else str(row[2])
        if spec and not is_medical(spec) and "кардио" not in spec.lower():
            continue
        add_row(rows, source="кандидаты HH", vacancy=spec, fio=fio, phone_raw=row[3])

    wb.close()

    seen: set[tuple[str, str]] = set()
    unique: list[dict] = []
    for row in rows:
        key = (row["phone"], row["fio"].lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def save_csv(rows: list[dict]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["source", "vacancy", "fio", "phone", "fn", "ln"]
        )
        writer.writeheader()
        writer.writerows(rows)


def audience_payload(rows: list[dict]) -> list[list[str]]:
    payload: list[list[str]] = []
    seen: set[str] = set()
    for row in rows:
        if not row["phone"] or row["phone"] in seen:
            continue
        seen.add(row["phone"])
        payload.append(
            [
                sha256_text(row["phone"]),
                sha256_text(row["fn"]) if row["fn"] else "",
                sha256_text(row["ln"]) if row["ln"] else "",
            ]
        )
    return payload


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def find_audience_by_name(mrs, name: str) -> str | None:
    payload = graph(
        mrs.access_token,
        mrs.graph_api_version or "v25.0",
        "GET",
        f"{mrs.ad_account_ref}/customaudiences",
        params={"fields": "id,name", "limit": 200},
    )
    for item in payload.get("data", []):
        if item.get("name") == name:
            return item["id"]
    return None


def upload_audience(mrs, rows: list[list[str]]) -> str:
    state = load_state()
    version = mrs.graph_api_version or "v25.0"
    audience_id = state.get("audience_id") or find_audience_by_name(mrs, AUDIENCE_NAME)
    if audience_id:
        print(f"[reused] audience {audience_id}")
    else:
        created = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/customaudiences",
            data={
                "name": AUDIENCE_NAME,
                "subtype": "CUSTOM",
                "customer_file_source": "USER_PROVIDED_ONLY",
                "description": "Медицинские кандидаты из HR-таблицы: вакансия + ФИО + телефон",
            },
        )
        audience_id = created["id"]
        print(f"[created] audience {audience_id}")
    state["audience_id"] = audience_id
    save_state(state)
    if state.get("audience_uploaded"):
        return audience_id
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        result = graph(
            mrs.access_token,
            version,
            "POST",
            f"{audience_id}/users",
            data={
                "payload": json.dumps({"schema": ["PHONE", "FN", "LN"], "data": batch}),
            },
        )
        print(
            f"[uploaded] users batch {i // BATCH_SIZE + 1}: "
            f"{result.get('num_received', len(batch))}"
        )
    state["audience_uploaded"] = True
    save_state(state)
    return audience_id


def geo_minsk() -> dict:
    return {
        "cities": [
            {"key": "283241", "radius": 40, "distance_unit": "kilometer"}
        ],
        "location_types": ["frequently_in", "home", "recent"],
    }


def targeting_jobs() -> dict:
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
                    {"id": "104034682965350", "name": "Cardiology"},
                    {"id": "105480999485471", "name": "Doctor of Medicine"},
                    {"id": "109247529092920", "name": "Internal medicine"},
                    {"id": "178310782214302", "name": "General Medicine (MD)"},
                ],
            },
            {
                "work_positions": [
                    {"id": "143214035704311", "name": "Consultant Cardiologist"},
                    {"id": "789368504445169", "name": "Pediatric Cardiologist"},
                    {"id": "104034682965350", "name": "Cardiology"},
                    {"id": "149919545021465", "name": "Cardiology Fellow"},
                    {"id": "107402372623035", "name": "Doctor"},
                    {"id": "105480999485471", "name": "Doctor of Medicine"},
                    {"id": "649354901854686", "name": "Medical Doctor (MD)"},
                    {"id": "616696405130729", "name": "Internist"},
                    {"id": "105517002815720", "name": "General practitioner"},
                    {"id": "761820927245398", "name": "Internal Medicine Physician"},
                    {"id": "588508654618832", "name": "Internal Medicine Doctor"},
                    {"id": "109247529092920", "name": "Internal medicine"},
                    {"id": "106165199414900", "name": "Attending physician"},
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


def targeting_list(audience_id: str) -> dict:
    return {
        "age_min": 25,
        "age_max": 55,
        "custom_audiences": [{"id": audience_id}],
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
            "promoted_object": json.dumps({"custom_conversion_id": CC_HR}),
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


def upload_image(mrs, path: Path) -> str:
    version = mrs.graph_api_version or "v25.0"
    with path.open("rb") as handle:
        result = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/adimages",
            files={"filename": (path.name, handle, "image/png")},
        )
    return next(iter(result["images"].values()))["hash"]


def build_creative(spec: dict, hashes: dict[str, str]) -> dict:
    prefix = f"kardiolog_{spec['key']}"
    labels = {
        "sq": f"{prefix}_sq",
        "ls": f"{prefix}_ls",
        "vt": f"{prefix}_vt",
        "body": f"{prefix}_body",
        "title": f"{prefix}_title",
        "url": f"{prefix}_url",
    }
    base_age = {"age_min": 13, "age_max": 65}
    rules = [
        {
            "priority": 1,
            "body_label": {"name": labels["body"]},
            "title_label": {"name": labels["title"]},
            "link_url_label": {"name": labels["url"]},
            "image_label": {"name": labels["sq"]},
            "customization_spec": {
                **base_age,
                "publisher_platforms": ["facebook", "instagram", "threads"],
                "instagram_positions": [
                    "stream",
                    "explore",
                    "explore_home",
                    "profile_feed",
                    "ig_search",
                ],
                "facebook_positions": [
                    "feed",
                    "video_feeds",
                    "marketplace",
                    "profile_feed",
                ],
                "threads_positions": ["threads_stream"],
            },
        },
        {
            "priority": 2,
            "body_label": {"name": labels["body"]},
            "title_label": {"name": labels["title"]},
            "link_url_label": {"name": labels["url"]},
            "image_label": {"name": labels["sq"]},
            "customization_spec": {
                **base_age,
                "publisher_platforms": ["facebook"],
                "facebook_positions": ["search"],
            },
        },
        {
            "priority": 3,
            "body_label": {"name": labels["body"]},
            "title_label": {"name": labels["title"]},
            "link_url_label": {"name": labels["url"]},
            "image_label": {"name": labels["ls"]},
            "customization_spec": {
                **base_age,
                "publisher_platforms": ["facebook", "audience_network", "messenger"],
                "facebook_positions": ["right_hand_column"],
                "messenger_positions": ["messenger_home"],
                "audience_network_positions": ["classic"],
            },
        },
        {
            "priority": 4,
            "body_label": {"name": labels["body"]},
            "title_label": {"name": labels["title"]},
            "link_url_label": {"name": labels["url"]},
            "image_label": {"name": labels["vt"]},
            "customization_spec": base_age,
        },
    ]
    return {
        "name": spec["name"],
        "url_tags": URL_TAGS,
        "object_story_spec": {
            "page_id": PAGE_ID,
            "instagram_user_id": IG_ID,
        },
        "asset_feed_spec": {
            "optimization_type": "PLACEMENT",
            "call_to_action_types": ["LEARN_MORE"],
            "ad_formats": ["AUTOMATIC_FORMAT"],
            "images": [
                {"hash": hashes["sq"], "adlabels": [{"name": labels["sq"]}]},
                {"hash": hashes["ls"], "adlabels": [{"name": labels["ls"]}]},
                {"hash": hashes["vt"], "adlabels": [{"name": labels["vt"]}]},
            ],
            "bodies": [
                {"text": text, "adlabels": [{"name": labels["body"]}]}
                for text in spec["bodies"]
            ],
            "titles": [
                {"text": text, "adlabels": [{"name": labels["title"]}]}
                for text in spec["titles"]
            ],
            "descriptions": [{"text": spec["description"]}],
            "link_urls": [
                {
                    "website_url": LINK,
                    "display_url": "https://kravira.by",
                    "adlabels": [{"name": labels["url"]}],
                }
            ],
            "asset_customization_rules": rules,
        },
        "degrees_of_freedom_spec": DOF,
    }


def apply() -> int:
    mrs = get_mrs_settings()
    version = mrs.graph_api_version or "v25.0"
    state = load_state()
    if state.get("audience_id") and CSV_PATH.exists():
        print(f"[reused] audience {state['audience_id']} | csv {CSV_PATH}")
        audience_id = state["audience_id"]
    else:
        if not XLSX_PATH.exists():
            raise RuntimeError(f"xlsx missing: {XLSX_PATH}")
        people = parse_workbook()
        save_csv(people)
        phones = [r for r in people if r["phone"]]
        vac_counts = Counter(r["vacancy"].lower() for r in people)
        print(f"[list] unique rows {len(people)} | with phone {len(phones)}")
        print(f"[list] csv {CSV_PATH}")
        print("[list] top vacancies:")
        for name, n in vac_counts.most_common(15):
            print(f"   {n:4d}  {name}")
        hashed = audience_payload(people)
        print(f"[list] hashed phones for Meta {len(hashed)}")
        audience_id = upload_audience(mrs, hashed)
        state = load_state()
    if not state.get("adset_jobs"):
        state["adset_jobs"] = create_adset(mrs, "Кардиологи", targeting_jobs())
        save_state(state)
        print(f"[created] adset jobs {state['adset_jobs']}")
    else:
        print(f"[reused] adset jobs {state['adset_jobs']}")

    if not state.get("adset_list"):
        state["adset_list"] = create_adset(
            mrs, "Кардиологи — база HR", targeting_list(audience_id)
        )
        save_state(state)
        print(f"[created] adset list {state['adset_list']}")
    else:
        print(f"[reused] adset list {state['adset_list']}")

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

    state.setdefault("ads", {})
    for adset_key, adset_id in (
        ("jobs", state["adset_jobs"]),
        ("list", state["adset_list"]),
    ):
        for spec in ADS:
            ad_key = f"{adset_key}_{spec['key']}"
            if ad_key in state["ads"]:
                print(f"[reused] ad {ad_key}")
                continue
            suffix = "" if adset_key == "jobs" else " | база HR"
            ad = graph(
                mrs.access_token,
                version,
                "POST",
                f"{mrs.ad_account_ref}/ads",
                data={
                    "name": f"{spec['name']}{suffix}",
                    "adset_id": adset_id,
                    "creative": json.dumps(
                        {"creative_id": state["creatives"][spec["key"]]}
                    ),
                    "status": "ACTIVE",
                },
            )
            state["ads"][ad_key] = ad["id"]
            save_state(state)
            print(f"[created] ad {spec['name']}{suffix} → {ad['id']}")

    print("[complete] Кардиологи ACTIVE")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    try:
        return apply()
    except ConfigError as exc:
        print(f"[config] {exc}")
        return 2
    except (RuntimeError, requests.RequestException, FileNotFoundError) as exc:
        print(f"[error] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
