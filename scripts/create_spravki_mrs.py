"""Кампания «Справки» в NEW (MRS): аудитория w_18_40 + phone + картинки spravki.

Настройки с активного OLD ad «Школьник_128_руб» в Справки_2026_2.
Конверсия: MRS_Ph_Spec (Test_F_Ph). Всё создаётся PAUSED.

Запуск:
    python -m scripts.create_spravki_mrs --check
    python -m scripts.create_spravki_mrs --apply
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

import requests
from PIL import Image

from src.config import ConfigError, get_mrs_settings

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "tmp_refs" / "create_spravki_mrs.json"
CSV_PATH = Path("/Users/pavelkuzauka/Jupyter_2/PL/w_18_40.csv")
IMG_DIR = ROOT / "image" / "spravki"

AUDIENCE_NAME = "w_18_40.csv"
CC_PHONE = "1077660694742370"  # MRS_Ph_Spec
PAGE_ID = "265643990153763"
IG_ID = "17841404399569974"

CAMPAIGN_NAME = "Справки"
ADSET_NAME = "Справки — звонок"
AD_NAME = "Школьник"

LANDING = (
    "https://kravira.by/services/kompleksnye-programmy/"
    "ezhegodnyy-check-up-shkolniki-vydacha-spravki-v-shkolu/"
)
DISPLAY_URL = "https://kravira.by"

# Расширенные варианты на основе активного объявления + акцентов с баннеров
TITLES = [
    "Справка в школу за 1 день",
    "Справка в школу — не оставляйте на потом",
    "Готовитесь к учебному году? Справка тут",
    "Справка в школу за один день — в одном месте",
    "Медсправка школьнику за 1 день",
    "Школа скоро — справка уже готова?",
    "Оформите справку в школу заранее",
    "Медосмотр школьнику + справка за день",
]

BODIES = [
    "Справка в школу за 1 день",
    "Подготовка к школе без стресса",
    "Скоро школа, а справка ещё не готова?",
    "Запишитесь на удобное время — оформим за день",
    "Один визит: осмотр и справка для школы",
    "Не откладывайте справку на последний момент",
    "Врачи рядом — справка школьнику быстро",
    "Комплекс для школьников: запись онлайн или по телефону",
]

DESCRIPTIONS = [
    "Справка в школу за один день. Запишитесь на удобное время",
    "Медосмотр школьнику и выдача справки в Кравира",
    "Оформление за день — звоните или записывайтесь на сайте",
]

DAILY_BUDGET_CENTS = 2500  # $25/day (NEW = USD), как тестовый бюджет ФГДС
COST_CAP_CENTS = 100  # $1 за телефон — как на ФГДС — звонок
BATCH_SIZE = 10_000

# Маппинг файл → placement label (по размеру)
# feed 3:4, square 1:1 (Facebook Search), compact landscape, vertical 9:16
IMG_ROLE = {
    "школа (1) .png": "feed",
    "школа_search_1x1.png": "square",
    "школа_1день (1).png": "compact",
    "школа_1день.png": "vertical",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    return parser.parse_args()


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


def upload_audience(mrs, rows: list[list[str]]) -> str:
    state = load_state()
    if state.get("audience_id") and state.get("audience_uploaded"):
        print(f"[reused] audience {state['audience_id']}")
        return state["audience_id"]

    audience_id = state.get("audience_id") or find_audience_by_name(mrs, AUDIENCE_NAME)
    version = mrs.graph_api_version or "v25.0"
    if audience_id:
        print(f"[reused] existing audience {audience_id}")
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
                "description": "Women 18-40 list for spravki campaign",
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
                "payload": json.dumps(
                    {"schema": ["PHONE", "FN", "LN"], "data": batch}
                ),
            },
        )
        print(
            f"[uploaded] users batch {i // BATCH_SIZE + 1}: "
            f"{result.get('num_received', len(batch))}"
        )
    state["audience_uploaded"] = True
    save_state(state)
    return audience_id


def ensure_square_from_feed(feed_path: Path) -> Path:
    """Facebook Search — только 1:1. Делаем center-crop с feed, если файла ещё нет."""
    out = IMG_DIR / "школа_search_1x1.png"
    if out.exists():
        return out
    im = Image.open(feed_path).convert("RGB")
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    sq = im.crop((left, top, left + side, top + side)).resize(
        (1080, 1080), Image.Resampling.LANCZOS
    )
    sq.save(out, "PNG", optimize=True)
    print(f"[image] generated square {out.name}")
    return out


def discover_images() -> dict[str, Path]:
    found: dict[str, Path] = {}
    for path in sorted(IMG_DIR.iterdir()):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        role = IMG_ROLE.get(path.name)
        if not role:
            w, h = Image.open(path).size
            ratio = w / h
            if 0.95 <= ratio <= 1.05:
                role = "square"
            elif ratio > 1.5:
                role = "compact"
            elif ratio < 0.7:
                role = "vertical"
            else:
                role = "feed"
        found[role] = path
        print(
            f"[image] {role}: {path.name} "
            f"({Image.open(path).size[0]}x{Image.open(path).size[1]})"
        )
    if "feed" in found and "square" not in found:
        found["square"] = ensure_square_from_feed(found["feed"])
        print(f"[image] square: {found['square'].name} (1080x1080)")
    for need in ("feed", "square", "compact", "vertical"):
        if need not in found:
            raise RuntimeError(f"Missing {need} image in {IMG_DIR}")
    return found


def upload_images(mrs, images: dict[str, Path], state: dict) -> dict[str, str]:
    mapping = dict(state.get("image_hashes", {}))
    version = mrs.graph_api_version or "v25.0"
    for role, path in images.items():
        if role in mapping:
            continue
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        uploaded = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/adimages",
            data={"bytes": encoded, "name": f"spravki_{role}"},
        )
        images_block = uploaded.get("images") or {}
        new_hash = None
        for val in images_block.values():
            if isinstance(val, dict) and val.get("hash"):
                new_hash = val["hash"]
                break
        if not new_hash:
            raise RuntimeError(f"Upload failed for {path.name}: {uploaded}")
        mapping[role] = new_hash
        print(f"[uploaded] {role} → {new_hash[:12]}…")
    state["image_hashes"] = mapping
    save_state(state)
    return mapping


def build_dof() -> dict:
    # Как в активном креативе — почти всё OPT_OUT
    features = [
        "adapt_to_placement",
        "add_text_overlay",
        "ads_with_benefits",
        "advantage_plus_creative",
        "description_automation",
        "enhance_cta",
        "image_background_gen",
        "image_touchups",
        "inline_comment",
        "media_type_automation",
        "product_extensions",
        "profile_card",
        "standard_enhancements_catalog",
        "text_optimizations",
        "text_translation",
        "video_auto_crop",
    ]
    return {
        "creative_features_spec": {
            name: {"enroll_status": "OPT_OUT"} for name in features
        }
    }


def build_asset_feed(hashes: dict[str, str]) -> dict:
    labels = {
        "feed": "spravki_feed",
        "square": "spravki_square",
        "compact": "spravki_compact",
        "vertical": "spravki_vertical",
        "body": "spravki_body",
        "title": "spravki_title",
        "url": "spravki_url",
    }
    base_age = {"age_max": 65, "age_min": 13}
    return {
        "images": [
            {"hash": hashes["feed"], "adlabels": [{"name": labels["feed"]}]},
            {"hash": hashes["square"], "adlabels": [{"name": labels["square"]}]},
            {"hash": hashes["compact"], "adlabels": [{"name": labels["compact"]}]},
            {"hash": hashes["vertical"], "adlabels": [{"name": labels["vertical"]}]},
        ],
        "bodies": [{"text": t, "adlabels": [{"name": labels["body"]}]} for t in BODIES],
        "titles": [{"text": t, "adlabels": [{"name": labels["title"]}]} for t in TITLES],
        # Одна description — иначе Meta ругается на placement rules
        "descriptions": [{"text": DESCRIPTIONS[0]}],
        "call_to_action_types": ["LEARN_MORE"],
        "link_urls": [
            {
                "website_url": LANDING,
                "display_url": DISPLAY_URL,
                "adlabels": [{"name": labels["url"]}],
            }
        ],
        "ad_formats": ["AUTOMATIC_FORMAT"],
        "optimization_type": "PLACEMENT",
        "asset_customization_rules": [
            {
                "priority": 1,
                "image_label": {"name": labels["feed"]},
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
                "image_label": {"name": labels["compact"]},
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
        ],
    }


def build_targeting(audience_id: str) -> dict:
    # Как в активном OLD ad set: Минск, 18–65, Advantage Audience, custom audience
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
        "brand_safety_content_filter_levels": [
            "FACEBOOK_RELAXED",
            "AN_RELAXED",
            "FEED_RELAXED",
        ],
        "locales": [17],  # русский, не 6 (English US)
        "targeting_automation": {
            "advantage_audience": 1,
            "individual_setting": {"geo": 1},
        },
    }


def check(mrs) -> int:
    rows = read_audience_rows(CSV_PATH)
    images = discover_images()
    print(f"[csv] {CSV_PATH.name}: {len(rows)} rows with phone")
    print(f"[images] {len(images)} roles ready")
    print(f"[titles] {len(TITLES)} | [bodies] {len(BODIES)} | [descriptions] {len(DESCRIPTIONS)}")
    print(f"[landing] {LANDING}")
    print(f"[conversion] MRS_Ph_Spec ({CC_PHONE})")
    print(f"[budget] ${DAILY_BUDGET_CENTS/100:.0f}/day | cost cap ${COST_CAP_CENTS/100:.2f}")
    print(f"[state] {STATE_PATH}: {json.dumps(load_state(), ensure_ascii=False)}")
    return 0


def apply(mrs) -> int:
    state = load_state()
    version = mrs.graph_api_version or "v25.0"
    rows = read_audience_rows(CSV_PATH)
    if not rows:
        raise RuntimeError("CSV audience empty after normalization")

    audience_id = upload_audience(mrs, rows)
    images = discover_images()
    hashes = upload_images(mrs, images, state)

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
                "promoted_object": json.dumps({"custom_conversion_id": CC_PHONE}),
                "targeting": json.dumps(build_targeting(audience_id)),
                "attribution_spec": json.dumps(
                    [
                        {"event_type": "CLICK_THROUGH", "window_days": 7},
                        {"event_type": "VIEW_THROUGH", "window_days": 1},
                        {"event_type": "ENGAGED_VIDEO_VIEW", "window_days": 1},
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

    if state.get("ad_id"):
        print(f"[reused] ad {state['ad_id']}")
    else:
        creative = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/adcreatives",
            data={
                "name": f"{AD_NAME} | creative",
                "object_story_spec": json.dumps(
                    {"page_id": PAGE_ID, "instagram_user_id": IG_ID}
                ),
                "asset_feed_spec": json.dumps(build_asset_feed(hashes)),
                "degrees_of_freedom_spec": json.dumps(build_dof()),
            },
        )
        ad = graph(
            mrs.access_token,
            version,
            "POST",
            f"{mrs.ad_account_ref}/ads",
            data={
                "name": AD_NAME,
                "adset_id": state["adset_id"],
                "creative": json.dumps({"creative_id": creative["id"]}),
                "status": "PAUSED",
            },
        )
        state["creative_id"] = creative["id"]
        state["ad_id"] = ad["id"]
        save_state(state)
        print(f"[created] ad {state['ad_id']} creative {state['creative_id']}")

    print("[complete] Справки PAUSED")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    args = parse_args()
    try:
        mrs = get_mrs_settings()
    except ConfigError as exc:
        print(f"[config] {exc}")
        return 2
    if not CSV_PATH.exists():
        print(f"[error] CSV not found: {CSV_PATH}")
        return 2
    if not IMG_DIR.exists():
        print(f"[error] images not found: {IMG_DIR}")
        return 2
    try:
        if args.check:
            return check(mrs)
        return apply(mrs)
    except (RuntimeError, requests.RequestException) as exc:
        print(f"[error] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
