"""Копия активной группы Проктолог (OLD → NEW / MRS).

Аудитория: та же fl_pr_26.csv (как у Флеболог).
Конверсия: MRS_OnlineBooking_Spec. Search → квадрат.
Расширенные заголовки/тексты. Всё PAUSED.

    python -m scripts.create_prokt_mrs --check
    python -m scripts.create_prokt_mrs --apply
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import re
import sys
from copy import deepcopy
from pathlib import Path

import requests

from src.config import ConfigError, get_mrs_settings

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "tmp_refs" / "create_prokt_mrs.json"
CSV_PATH = Path("/Users/pavelkuzauka/Jupyter_2/PL/fl_pr_26.csv")

AUDIENCE_NAME = "fl_pr_26.csv"
CC_BOOKING = "1465168982095234"
PAGE_ID = "265643990153763"
IG_ID = "17841404399569974"

CAMPAIGN_NAME = "Проктолог"
ADSET_NAME = "Проктолог — сайт"

OLD_AD_IDS = [
    "120250631279100770",  # Мытник_1
    "120250631276680770",  # Мытник_2
    "120250631286410770",  # Мытник_3
    "120250631275150770",  # Тихон_1
    "120250631293140770",  # Тихон_3
]

SHORT_NAMES = {
    "120250631279100770": "Мытник 1",
    "120250631276680770": "Мытник 2",
    "120250631286410770": "Мытник 3",
    "120250631275150770": "Тихон 1",
    "120250631293140770": "Тихон 3",
}

EXPANDED = {
    "120250631279100770": {
        "titles": [
            "Когда мази дают «на денёк», нужен план у проктолога",
            "Ваше кресло стало главным врагом",
            "Лечение геморроя — чтобы жить без дискомфорта",
            "Проктолог Мытник — диагностика и план лечения",
            "Боль, зуд, кровь — не повод терпеть",
            "От процедур до операции — по показаниям",
            "Запишитесь к проктологу в Минске",
            "Геморрой лечится — не ждите осложнений",
        ],
        "bodies": [
            "Подбор метода лечения геморроя по показаниям",
            "Варианты лечения: от процедур до операции",
            "Лечение геморроя у опытного проктолога",
            "Диагностика и понятный план лечения",
            "Мази не решают проблему надолго",
            "Чем раньше визит — тем проще лечение",
            "Консультация проктолога в Кравира",
            "Запись онлайн или по телефону",
        ],
        "descriptions": [
            "Боль, зуд, кровь — не повод терпеть. Диагностика и лечение по стадии. Запишитесь к проктологу",
        ],
    },
    "120250631276680770": {
        "titles": [
            "Проктолог: осмотр и рекомендации",
            "Профилактика и лечение трещин, свищей, геморроя",
            "Чем раньше диагностика — тем проще лечение",
            "Симптомы геморроя — повод к врачу, не к отсрочке",
            "Современные методы лечения геморроя",
            "Проктолог Мытник в Кравира",
            "Не терпите кровь, жжение и зуд",
            "Получите понятный план лечения",
        ],
        "bodies": [
            "Мази не держат результат?",
            "Современные методы лечения геморроя",
            "Симптомы чаще с возрастом — но терпеть не нужно",
            "Если есть кровь, жжение, зуд или шишка — к проктологу",
            "Осмотр, диагностика, рекомендации",
            "При необходимости — операции",
            "Запишитесь до обострения",
            "Консультация проктолога в Минске",
        ],
        "descriptions": [
            "Если есть кровь, жжение, зуд, боль или шишка — не терпите. Запишитесь к проктологу и получите план лечения",
        ],
    },
    "120250631286410770": {
        "titles": [
            "Лечим геморрой современными методами",
            "Геморрой возвращается снова?",
            "Геморрой не пройдёт от ожидания",
            "Кровь после туалета — сигнал к проктологу",
            "Шишка, кровь, жжение — не откладывайте",
            "Перед поездкой — консультация проктолога",
            "Современное лечение без долгого ожидания",
            "Проктолог Мытник — запись в Кравира",
        ],
        "bodies": [
            "Заметили кровь после туалета?",
            "Шишка, кровь, жжение?",
            "Геморрой не лечится молчанием",
            "Долгий перелёт и сидение могут усилить симптомы",
            "Запишитесь до поездки, если есть боль или кровь",
            "Диагностика и лечение по стадии",
            "Не ждите, пока станет хуже",
            "Онлайн-запись или звонок",
        ],
        "descriptions": [
            "Длительный перелёт и много часов сидя могут спровоцировать обострение. При боли, жжении, крови или шишке — к проктологу",
        ],
    },
    "120250631275150770": {
        "titles": [
            "Терпите «там», потому что неловко?",
            "Запись к проктологу тут",
            "Лечение геморроя — это медицина, а не повод молчать",
            "Проктолог Тихон — консультация в Минске",
            "Когда мази не держат — нужен план лечения",
            "От процедур до операции — по показаниям",
            "Не ждите, что станет хуже само",
            "Комфортный приём у проктолога",
        ],
        "bodies": [
            "Когда мази дают «на денёк», нужен план у проктолога",
            "Лечим геморрой по показаниям: от процедур до операции",
            "Лечение геморроя — чтобы жить без дискомфорта",
            "Самое неприятное — ждать, что станет хуже",
            "Оперативное лечение — когда это действительно показано",
            "Диагностика без лишнего стресса",
            "Запишитесь к Тихону В. К. в Кравира",
            "Запись онлайн или по телефону",
        ],
        "descriptions": [
            "Самое неприятное — не боль, а ждать, что станет хуже. Лечение геморроя — когда это действительно показано",
        ],
    },
    "120250631293140770": {
        "titles": [
            "Перед длительным перелётом не игнорируйте симптомы",
            "У геморроя не должно быть посадочного талона",
            "Много часов сидя могут спровоцировать обострение",
            "Геморрой не должен лететь с вами",
            "Перед отпуском — консультация проктолога",
            "Перед самолётом — к проктологу",
            "Получите рекомендации до поездки",
            "Проктолог Тихон — запись в Кравира",
        ],
        "bodies": [
            "Геморрой не должен лететь с вами",
            "Перед отпуском пройдите консультацию проктолога",
            "Перед самолётом — к проктологу",
            "Недостаток воды и смена режима усиливают риск",
            "При склонности к геморрою сидение усиливает проблему",
            "Получите рекомендации проктолога заранее",
            "Не откладывайте визит до отпуска",
            "Запись онлайн или по звонку",
        ],
        "descriptions": [
            "При склонности к геморрою многочасовое сидение может усилить проблему. Перед отпуском получите рекомендации проктолога",
        ],
    },
}

DAILY_BUDGET_CENTS = 2500
COST_CAP_CENTS = 100
BATCH_SIZE = 10_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    return parser.parse_args()


def load_env_old() -> dict[str, str]:
    from dotenv import dotenv_values

    env = dotenv_values(ROOT / ".env")
    return {
        "token": env["META_ACCESS_TOKEN_OLD"],
        "account": env["META_AD_ACCOUNT_ID_OLD"],
        "version": env.get("META_GRAPH_API_VERSION") or "v25.0",
    }


def graph(token: str, version: str, method: str, path: str, **kwargs) -> dict:
    url = f"https://graph.facebook.com/{version}/{path.lstrip('/')}"
    if method == "GET":
        kwargs.setdefault("params", {})["access_token"] = token
    else:
        kwargs.setdefault("data", {})["access_token"] = token
    response = requests.request(method, url, timeout=180, **kwargs)
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"Meta non-JSON {path}: {response.text[:400]}") from exc
    if response.status_code != 200:
        err = payload.get("error", {})
        raise RuntimeError(err.get("error_user_msg") or err.get("message") or str(payload))
    return payload


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_phone(raw: str) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return None
    if digits.startswith("80") and len(digits) >= 11:
        digits = "375" + digits[2:]
    if not digits.startswith("375"):
        return None
    return digits


def normalize_name(value: str) -> str | None:
    if not value:
        return None
    cleaned = value.strip().lower()
    if cleaned in {"---", "-", "null", "none"}:
        return None
    return cleaned or None


def read_audience_rows(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            phone = normalize_phone(row.get("phone", ""))
            fn = normalize_name(row.get("fn", ""))
            ln = normalize_name(row.get("ln", ""))
            if not phone:
                continue
            rows.append(
                [
                    sha256_text(phone),
                    sha256_text(fn) if fn else "",
                    sha256_text(ln) if ln else "",
                ]
            )
    return rows


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


def resolve_audience(mrs, rows: list[list[str]]) -> str:
    """Reuse fl_pr_26.csv already uploaded for fleb; do not re-upload users."""
    state = load_state()
    if state.get("audience_id"):
        print(f"[reused] audience {state['audience_id']}")
        return state["audience_id"]

    audience_id = find_audience_by_name(mrs, AUDIENCE_NAME)
    if audience_id:
        print(f"[reused] existing audience {audience_id} ({AUDIENCE_NAME})")
        state["audience_id"] = audience_id
        state["audience_uploaded"] = True
        save_state(state)
        return audience_id

    # Fallback create+upload if somehow missing
    version = mrs.graph_api_version or "v25.0"
    created = graph(
        mrs.access_token,
        version,
        "POST",
        f"{mrs.ad_account_ref}/customaudiences",
        data={
            "name": AUDIENCE_NAME,
            "subtype": "CUSTOM",
            "customer_file_source": "USER_PROVIDED_ONLY",
            "description": "Shared fleb/proct list fl_pr_26.csv",
        },
    )
    audience_id = created["id"]
    print(f"[created] audience {audience_id}")
    state["audience_id"] = audience_id
    save_state(state)
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        result = graph(
            mrs.access_token,
            version,
            "POST",
            f"{audience_id}/users",
            data={
                "payload": json.dumps(
                    {"schema": ["PHONE", "FN", "LN"], "data": batch}
                ),
            },
        )
        print(f"[uploaded] batch {i // BATCH_SIZE + 1}: {result.get('num_received', len(batch))}")
    state["audience_uploaded"] = True
    save_state(state)
    return audience_id


def fetch_old_assets(old: dict):
    creatives: dict[str, dict] = {}
    hashes: set[str] = set()
    for ad_id in OLD_AD_IDS:
        ad = graph(
            old["token"],
            old["version"],
            "GET",
            ad_id,
            params={
                "fields": "id,name,creative{id,object_story_spec,asset_feed_spec,degrees_of_freedom_spec}",
            },
        )
        creatives[ad_id] = ad
        for img in (ad["creative"].get("asset_feed_spec") or {}).get("images", []):
            if img.get("hash"):
                hashes.add(img["hash"])

    imgs = graph(
        old["token"],
        old["version"],
        "GET",
        f"act_{old['account']}/adimages",
        params={"hashes": json.dumps(list(hashes)), "fields": "hash,url,width,height,name"},
    )
    urls = {i["hash"]: i["url"] for i in imgs.get("data", []) if i.get("url")}
    dims = {i["hash"]: (i.get("width"), i.get("height")) for i in imgs.get("data", [])}
    return creatives, urls, dims


def upload_images(mrs, urls: dict[str, str], state: dict) -> dict[str, str]:
    mapping = dict(state.get("image_hash_map", {}))
    version = mrs.graph_api_version or "v25.0"
    for old_hash, url in urls.items():
        if old_hash in mapping:
            continue
        content = requests.get(url, timeout=120).content
        encoded = base64.b64encode(content).decode("ascii")
        uploaded = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/adimages",
            data={"bytes": encoded},
        )
        images = uploaded.get("images") or {}
        new_hash = None
        for val in images.values():
            if isinstance(val, dict) and val.get("hash"):
                new_hash = val["hash"]
                break
        if not new_hash:
            raise RuntimeError(f"upload failed {old_hash}: {uploaded}")
        mapping[old_hash] = new_hash
        print(f"[uploaded] image {old_hash[:10]}… → {new_hash[:10]}…")
    state["image_hash_map"] = mapping
    save_state(state)
    return mapping


def strip_ids(obj):
    if isinstance(obj, dict):
        return {k: strip_ids(v) for k, v in obj.items() if k != "id"}
    if isinstance(obj, list):
        return [strip_ids(x) for x in obj]
    return obj


def pick_square_vertical(old_images, hash_map, dims):
    square_hash = None
    vertical_hash = None
    for img in old_images:
        h = img.get("hash")
        if not h or h not in hash_map:
            continue
        w, ht = dims.get(h) or (0, 0)
        new_h = hash_map[h]
        if w and ht and abs(w / ht - 1) < 0.08:
            square_hash = new_h
        elif w and ht and ht > w * 1.4:
            vertical_hash = new_h
    if not square_hash:
        for img in old_images:
            if img.get("hash") in hash_map:
                square_hash = hash_map[img["hash"]]
                break
    if not vertical_hash:
        vertical_hash = square_hash
    return square_hash, vertical_hash


def remap_creative(creative, hash_map, dims, short_name, old_ad_id):
    afs = deepcopy(creative.get("asset_feed_spec") or {})
    square_hash, vertical_hash = pick_square_vertical(
        afs.get("images") or [], hash_map, dims
    )
    if not square_hash:
        raise RuntimeError(f"No square for {short_name}")

    copy = EXPANDED[old_ad_id]
    prefix = re.sub(r"[^a-zA-Z0-9а-яА-Я]+", "_", short_name)[:24]
    labels = {
        "square": f"{prefix}_square",
        "vertical": f"{prefix}_vertical",
        "body": f"{prefix}_body",
        "title": f"{prefix}_title",
        "url": f"{prefix}_url",
    }

    link_urls = []
    for link in afs.get("link_urls") or []:
        link_urls.append(
            {
                "website_url": (link.get("website_url") or "").split("?", 1)[0],
                "display_url": link.get("display_url") or "https://kravira.by",
                "adlabels": [{"name": labels["url"]}],
            }
        )

    base_age = {"age_min": 13, "age_max": 65}
    rules = [
        {
            "priority": 1,
            "image_label": {"name": labels["square"]},
            "body_label": {"name": labels["body"]},
            "title_label": {"name": labels["title"]},
            "link_url_label": {"name": labels["url"]},
            "customization_spec": {
                **base_age,
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
        },
        {
            "priority": 2,
            "image_label": {"name": labels["square"]},
            "body_label": {"name": labels["body"]},
            "title_label": {"name": labels["title"]},
            "link_url_label": {"name": labels["url"]},
            "customization_spec": {
                **base_age,
                "publisher_platforms": ["facebook"],
                "facebook_positions": ["search"],
            },
        },
        {
            "priority": 3,
            "image_label": {"name": labels["square"]},
            "body_label": {"name": labels["body"]},
            "title_label": {"name": labels["title"]},
            "link_url_label": {"name": labels["url"]},
            "customization_spec": {
                **base_age,
                "publisher_platforms": [
                    "facebook",
                    "audience_network",
                    "messenger",
                ],
                "facebook_positions": ["right_hand_column"],
                "messenger_positions": ["messenger_home"],
                "audience_network_positions": ["classic"],
            },
        },
        {
            "priority": 4,
            "image_label": {"name": labels["vertical"]},
            "body_label": {"name": labels["body"]},
            "title_label": {"name": labels["title"]},
            "link_url_label": {"name": labels["url"]},
            "customization_spec": base_age,
        },
    ]

    dof = creative.get("degrees_of_freedom_spec") or {
        "creative_features_spec": {
            "adapt_to_placement": {"enroll_status": "OPT_OUT"},
            "advantage_plus_creative": {"enroll_status": "OPT_OUT"},
            "text_optimizations": {"enroll_status": "OPT_OUT"},
            "enhance_cta": {"enroll_status": "OPT_OUT"},
            "image_touchups": {"enroll_status": "OPT_OUT"},
        }
    }

    return strip_ids(
        {
            "name": f"{short_name} | creative",
            "object_story_spec": {
                "page_id": PAGE_ID,
                "instagram_user_id": IG_ID,
            },
            "asset_feed_spec": {
                "images": [
                    {"hash": square_hash, "adlabels": [{"name": labels["square"]}]},
                    {"hash": vertical_hash, "adlabels": [{"name": labels["vertical"]}]},
                ],
                "bodies": [
                    {"text": t, "adlabels": [{"name": labels["body"]}]}
                    for t in copy["bodies"]
                ],
                "titles": [
                    {"text": t, "adlabels": [{"name": labels["title"]}]}
                    for t in copy["titles"]
                ],
                "descriptions": [{"text": copy["descriptions"][0]}],
                "call_to_action_types": afs.get("call_to_action_types") or ["LEARN_MORE"],
                "link_urls": link_urls,
                "ad_formats": ["AUTOMATIC_FORMAT"],
                "optimization_type": "PLACEMENT",
                "asset_customization_rules": rules,
            },
            "degrees_of_freedom_spec": dof,
        }
    )


def build_targeting(audience_id: str) -> dict:
    return {
        "age_min": 18,
        "age_max": 65,
        "custom_audiences": [{"id": audience_id}],
        "geo_locations": {
            "cities": [
                {
                    "key": "283241",
                    "radius": 40,
                    "distance_unit": "kilometer",
                }
            ],
            "location_types": ["home", "recent", "frequently_in"],
        },
        "locales": [17],
        "brand_safety_content_filter_levels": [
            "FACEBOOK_RELAXED",
            "AN_RELAXED",
            "FEED_RELAXED",
        ],
        "targeting_automation": {
            "advantage_audience": 1,
            "individual_setting": {"geo": 1},
        },
    }


def check(mrs, old: dict) -> int:
    rows = read_audience_rows(CSV_PATH)
    creatives, urls, dims = fetch_old_assets(old)
    existing = find_audience_by_name(mrs, AUDIENCE_NAME)
    print(f"[csv] {CSV_PATH.name}: {len(rows)} phones (reuse audience={existing})")
    print(f"[old ads] {len(creatives)} | images {len(urls)}")
    for ad_id, ad in creatives.items():
        exp = EXPANDED[ad_id]
        print(
            f"  - {SHORT_NAMES[ad_id]}: "
            f"{len(exp['titles'])}t/{len(exp['bodies'])}b "
            f"(was {len(ad['creative']['asset_feed_spec'].get('titles', []))}/"
            f"{len(ad['creative']['asset_feed_spec'].get('bodies', []))})"
        )
    print(f"[conversion] MRS_OnlineBooking_Spec | ${DAILY_BUDGET_CENTS/100:.0f}/day | cap ${COST_CAP_CENTS/100:.2f}")
    print("[search] square 1:1")
    return 0


def apply(mrs, old: dict) -> int:
    state = load_state()
    version = mrs.graph_api_version or "v25.0"
    rows = read_audience_rows(CSV_PATH)
    audience_id = resolve_audience(mrs, rows)
    creatives, urls, dims = fetch_old_assets(old)
    hash_map = upload_images(mrs, urls, state)

    if "campaign_id" not in state:
        campaign = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/campaigns",
            data={
                "name": CAMPAIGN_NAME,
                "objective": "OUTCOME_LEADS",
                "buying_type": "AUCTION",
                "special_ad_categories": json.dumps([]),
                "status": "PAUSED",
                "is_adset_budget_sharing_enabled": "false",
            },
        )
        state["campaign_id"] = campaign["id"]
        save_state(state)
        print(f"[created] campaign {state['campaign_id']}")
    else:
        print(f"[reused] campaign {state['campaign_id']}")

    if "adset_id" not in state:
        adset = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/adsets",
            data={
                "name": ADSET_NAME,
                "campaign_id": state["campaign_id"],
                "daily_budget": DAILY_BUDGET_CENTS,
                "billing_event": "IMPRESSIONS",
                "optimization_goal": "OFFSITE_CONVERSIONS",
                "bid_strategy": "COST_CAP",
                "bid_amount": COST_CAP_CENTS,
                "destination_type": "WEBSITE",
                "promoted_object": json.dumps({"custom_conversion_id": CC_BOOKING}),
                "targeting": json.dumps(build_targeting(audience_id)),
                "attribution_spec": json.dumps(
                    [
                        {"event_type": "CLICK_THROUGH", "window_days": 7},
                        {"event_type": "VIEW_THROUGH", "window_days": 1},
                    ]
                ),
                "status": "PAUSED",
            },
        )
        state["adset_id"] = adset["id"]
        save_state(state)
        print(f"[created] ad set {state['adset_id']}")
    else:
        print(f"[reused] ad set {state['adset_id']}")

    state.setdefault("ads", {})
    for ad_id in OLD_AD_IDS:
        short = SHORT_NAMES[ad_id]
        if state["ads"].get(short, {}).get("ad_id"):
            print(f"[reused] ad {short}")
            continue
        params = remap_creative(
            creatives[ad_id]["creative"], hash_map, dims, short, ad_id
        )
        creative = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/adcreatives",
            data={
                k: json.dumps(v) if isinstance(v, (dict, list)) else v
                for k, v in params.items()
            },
        )
        ad = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/ads",
            data={
                "name": short,
                "adset_id": state["adset_id"],
                "creative": json.dumps({"creative_id": creative["id"]}),
                "status": "PAUSED",
            },
        )
        state["ads"][short] = {"ad_id": ad["id"], "creative_id": creative["id"]}
        save_state(state)
        print(f"[created] ad {short} → {ad['id']}")

    print("[complete] Проктолог PAUSED")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    args = parse_args()
    try:
        mrs = get_mrs_settings()
        old = load_env_old()
    except ConfigError as exc:
        print(f"[config] {exc}")
        return 2
    if not CSV_PATH.exists():
        print(f"[error] CSV missing: {CSV_PATH}")
        return 2
    try:
        if args.check:
            return check(mrs, old)
        return apply(mrs, old)
    except (RuntimeError, requests.RequestException) as exc:
        print(f"[error] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
