"""Пересобрать аудиторию врачей из кандидаты.статистика.xlsx.

В прошлой заливке отвалились телефоны 029/044 (список Ларисы) и в Meta
ушли только хеши 375… из вкладки 2022-2024. Здесь: врачи из всех листов,
нормальные BY-номера, имя + страна, lookalike BY 3%.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import requests
from openpyxl import load_workbook

from src.config import get_mrs_settings

ROOT = Path(__file__).resolve().parents[1]
XLSX_PATH = ROOT / "tmp_refs" / "kandidaty_statistika.xlsx"
CSV_PATH = ROOT / "tmp_refs" / "hr_doctors_candidates.csv"
STATE_PATH = ROOT / "tmp_refs" / "rebuild_hr_doctors_audience.json"

AUDIENCE_NAME = "HR врачи — кандидаты таблицы"
LOOKALIKE_NAME = "HR врачи — похожие BY 3%"
HR_ADSET = "120248112990910434"
BATCH_SIZE = 10_000

DOC_INCLUDE = (
    "кардиолог",
    "терапевт",
    "невролог",
    "лор",
    "оторино",
    "отоларин",
    "гинеколог",
    "педиатр",
    "педнатр",
    "стоматолог",
    "офтальмолог",
    "хирург",
    "харург",
    "хнрург",
    "эндокрин",
    "уролог",
    "онколог",
    "маммолог",
    "гастро",
    "дерматолог",
    "анестезиолог",
    "анестезнолог",
    "эндоскоп",
    "травматолог",
    "ортопед",
    "флеболог",
    "пластик",
    "ревматолог",
    "аллерголог",
    "психотерапевт",
    "психотрапевт",
    "проктолог",
    "косметолог",
    "врач",
    "начмед",
    "гематолог",
    "пульмонолог",
    "нефролог",
    "инфекцион",
    "рентген",
    "узд",
    "узи",
    "акушер",
    "психиатр",
    "нарколог",
    "физиотерапевт",
    "физнотерапевт",
    "иммунолог",
    "нейрохирург",
    "патологоанатом",
    "гистолог",
    "сомнолог",
    "диетолог",
    "ортодонт",
    "маммолог",
    "реаниматолог",
    "реваниматолог",
    "мрт",
)
DOC_EXCLUDE = (
    "медсестра",
    "фельдшер",
    "санитар",
    "рецепшн",
    "колл",
    "бухгалтер",
    "администратор",
    "массажист",
    "менеджер",
    "маркетолог",
    "экономист",
    "инженер",
    "непрофиль",
    "помощник руководителя",
    "зав. хоз",
)


def graph(token: str, version: str, method: str, path: str, **kwargs) -> dict:
    url = f"https://graph.facebook.com/{version}/{path.lstrip('/')}"
    if method == "GET":
        kwargs.setdefault("params", {})["access_token"] = token
    else:
        kwargs.setdefault("data", {})["access_token"] = token
    response = requests.request(method, url, timeout=180, **kwargs)
    payload = response.json()
    if response.status_code != 200:
        err = payload.get("error", {})
        raise RuntimeError(err.get("error_user_msg") or err.get("message") or str(payload))
    return payload


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.0f}"
    return str(value).replace("\xa0", " ").strip()


def normalize_name(value: str) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"\s+", " ", value).strip().lower().replace("ё", "е")
    cleaned = re.sub(r"[^a-zа-яіў\- ]", "", cleaned)
    if cleaned in {"", "-", "---", "null", "none"}:
        return None
    return cleaned


def split_fio(fio: str) -> tuple[str | None, str | None]:
    parts = [p for p in re.split(r"\s+", fio.strip()) if p]
    if not parts:
        return None, None
    ln = normalize_name(parts[0])
    fn = normalize_name(parts[1]) if len(parts) > 1 else None
    return fn, ln


def phone_variants(raw) -> list[str]:
    if raw is None:
        return []
    digits = re.sub(r"\D", "", cell(raw))
    if not digits:
        return []
    if digits.startswith("80") and len(digits) >= 11:
        digits = "375" + digits[2:]
    elif digits.startswith("0") and len(digits) >= 10 and digits[1:3] in {"25", "29", "33", "44"}:
        digits = "375" + digits[1:]
    elif len(digits) == 9 and digits[:2] in {"25", "29", "33", "44"}:
        digits = "375" + digits
    elif digits.startswith("8") and len(digits) == 10:
        digits = "375" + digits[1:]
    if not digits.startswith("375") or len(digits) < 12:
        return []
    e164 = digits[:12]
    local = "80" + e164[3:]
    return [e164, local]


def is_doctor(vacancy: str) -> bool:
    text = (vacancy or "").strip().lower().replace("ё", "е")
    if any(x in text for x in DOC_EXCLUDE):
        return False
    return any(x in text for x in DOC_INCLUDE)


def add_row(rows: list[dict], *, source: str, vacancy: str, fio: str, phone_raw, city: str = "") -> None:
    fio_n = normalize_name(fio) or ""
    phones = phone_variants(phone_raw)
    if not phones and not fio_n:
        return
    fn, ln = split_fio(fio) if fio_n else (None, None)
    city_n = normalize_name(city) or "минск"
    rows.append(
        {
            "source": source,
            "vacancy": (vacancy or "").strip(),
            "fio": (fio or "").strip(),
            "phone": phones[0] if phones else "",
            "phone_alt": phones[1] if len(phones) > 1 else "",
            "fn": fn or "",
            "ln": ln or "",
            "city": city_n,
        }
    )


def parse_workbook() -> list[dict]:
    wb = load_workbook(XLSX_PATH, data_only=True, read_only=True)
    rows: list[dict] = []

    ws = wb["2022-2024"]
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue
        vacancy = cell(row[1])
        if not is_doctor(vacancy):
            continue
        add_row(
            rows,
            source="2022-2024",
            vacancy=vacancy,
            fio=cell(row[5]),
            phone_raw=row[6],
            city=cell(row[18]) if len(row) > 18 else "",
        )

    larisa = None
    for name in wb.sheetnames:
        if "Лариса" in name:
            larisa = wb[name]
            break
    if larisa is not None:
        for i, row in enumerate(larisa.iter_rows(values_only=True)):
            if i == 0:
                continue
            spec = cell(row[1])
            fio = cell(row[0])
            if not fio:
                continue
            if spec and not is_doctor(spec):
                continue
            if not spec:
                continue
            add_row(rows, source="Лариса_Список", vacancy=spec, fio=fio, phone_raw=row[2])

    if "кандидаты HH" in wb.sheetnames:
        ws = wb["кандидаты HH"]
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                continue
            spec = cell(row[1])
            if spec and not is_doctor(spec):
                continue
            add_row(
                rows,
                source="кандидаты HH",
                vacancy=spec,
                fio=cell(row[2]),
                phone_raw=row[3],
            )

    if "стоматологи" in wb.sheetnames:
        ws = wb["стоматологи"]
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                continue
            vals = list(row)
            if len(vals) < 2 or not cell(vals[1]):
                continue
            add_row(
                rows,
                source="стоматологи",
                vacancy="стоматолог",
                fio=cell(vals[1]),
                phone_raw=vals[5] if len(vals) > 5 else None,
            )

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


def audience_payload(rows: list[dict]) -> list[list[str]]:
    payload: list[list[str]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        fn_h = sha256_text(row["fn"]) if row["fn"] else ""
        ln_h = sha256_text(row["ln"]) if row["ln"] else ""
        country_h = sha256_text("by")
        city_h = sha256_text(row["city"]) if row["city"] else sha256_text("минск")
        phones = [p for p in (row["phone"], row["phone_alt"]) if p]
        if not phones and not (row["fn"] and row["ln"]):
            continue
        if not phones:
            key = ("", row["fn"], row["ln"])
            if key in seen:
                continue
            seen.add(key)
            payload.append(["", fn_h, ln_h, country_h, city_h])
            continue
        for phone in phones:
            key = (phone, row["fn"], row["ln"])
            if key in seen:
                continue
            seen.add(key)
            payload.append([sha256_text(phone), fn_h, ln_h, country_h, city_h])
    return payload


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def find_audience(mrs, name: str) -> str | None:
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


def geo_minsk() -> dict:
    return {
        "cities": [{"key": "283241", "radius": 40, "distance_unit": "kilometer"}],
        "location_types": ["frequently_in", "home", "recent"],
    }


def main() -> int:
    mrs = get_mrs_settings()
    version = mrs.graph_api_version or "v25.0"
    state = load_state()

    people = parse_workbook()
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["source", "vacancy", "fio", "phone", "phone_alt", "fn", "ln", "city"],
        )
        writer.writeheader()
        writer.writerows(people)

    sources = Counter(r["source"] for r in people)
    vacs = Counter(r["vacancy"].lower() for r in people)
    phones = {r["phone"] for r in people if r["phone"]}
    print(f"[list] врачи {len(people)} | уникальные 375-телефоны {len(phones)}")
    print("[list] источники:", dict(sources))
    print("[list] топ вакансий:")
    for name, n in vacs.most_common(15):
        print(f"   {n:4d}  {name}")
    print(f"[list] csv {CSV_PATH}")

    hashed = audience_payload(people)
    print(f"[list] строк в заливку Meta {len(hashed)}")

    audience_id = state.get("audience_id") or find_audience(mrs, AUDIENCE_NAME)
    if not audience_id:
        created = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/customaudiences",
            data={
                "name": AUDIENCE_NAME,
                "subtype": "CUSTOM",
                "customer_file_source": "USER_PROVIDED_ONLY",
                "description": "Врачи из HR-таблицы кандидатов: 2022-2024 + Лариса + HH",
            },
        )
        audience_id = created["id"]
        print(f"[created] audience {audience_id}")
    else:
        print(f"[reused] audience {audience_id}")
    state["audience_id"] = audience_id
    save_state(state)

    if not state.get("audience_uploaded"):
        for i in range(0, len(hashed), BATCH_SIZE):
            batch = hashed[i : i + BATCH_SIZE]
            result = graph(
                mrs.access_token,
                version,
                "POST",
                f"{audience_id}/users",
                data={
                    "payload": json.dumps(
                        {
                            "schema": ["PHONE", "FN", "LN", "COUNTRY", "CT"],
                            "data": batch,
                        }
                    )
                },
            )
            print(f"[uploaded] batch {i // BATCH_SIZE + 1}: {result.get('num_received', len(batch))}")
        state["audience_uploaded"] = True
        save_state(state)

    lookalike_id = state.get("lookalike_id") or find_audience(mrs, LOOKALIKE_NAME)
    if not lookalike_id:
        try:
            created = graph(
                mrs.access_token,
                version,
                "POST",
                f"{mrs.ad_account_ref}/customaudiences",
                data={
                    "name": LOOKALIKE_NAME,
                    "subtype": "LOOKALIKE",
                    "origin_audience_id": audience_id,
                    "lookalike_spec": json.dumps(
                        {"type": "similarity", "country": "BY", "ratio": 0.03}
                    ),
                },
            )
            lookalike_id = created["id"]
            print(f"[created] lookalike {lookalike_id}")
        except RuntimeError as exc:
            print(f"[lookalike] не создался: {exc}")
            lookalike_id = None
    else:
        print(f"[reused] lookalike {lookalike_id}")
    if lookalike_id:
        state["lookalike_id"] = lookalike_id
        save_state(state)

    custom = [{"id": audience_id}]
    if lookalike_id:
        custom.append({"id": lookalike_id})
    targeting = {
        "age_min": 25,
        "age_max": 55,
        "custom_audiences": custom,
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
    graph(
        mrs.access_token,
        version,
        "POST",
        HR_ADSET,
        data={"targeting": json.dumps(targeting)},
    )
    print(f"[updated] adset {HR_ADSET} custom={ [c['id'] for c in custom] }")

    info = graph(
        mrs.access_token,
        version,
        "GET",
        audience_id,
        params={
            "fields": "id,name,approximate_count_lower_bound,approximate_count_upper_bound,delivery_status,operation_status"
        },
    )
    print("[audience]", json.dumps(info, ensure_ascii=False))
    print("[complete]", json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
