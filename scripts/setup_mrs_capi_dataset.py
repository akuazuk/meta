"""Идемпотентная настройка NEW dataset Kravira_MRS_CAPI через API.

Делает то, что обычно предлагают в Events Manager вручную:
  * automatic advanced matching на dataset;
  * тестовая отправка всех ключевых CAPI-событий;
  * custom conversions MRS_Ph_Spec / MRS_Try_Spec;
  * website-аудитории MRS_*_180_days и Yackevich.

Запуск:
    python -m scripts.setup_mrs_capi_dataset --check
    python -m scripts.setup_mrs_capi_dataset --apply
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

import requests

from src.config import ConfigError, get_mrs_settings

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "tmp_refs" / "mrs_capi_dataset_state.json"

WEB_EVENTS = [
    "PageView",
    "MRS_FB_onlineBooking",
    "Test_F_Ph",
    "Test_F_try",
    "Test_F_online",
    "MRS_FB_hr",
    "Test_F_Yackevich",
]

AUDIENCES: dict[str, dict] = {
    "MRS_Try_180_days": {
        "event": "Test_F_try",
    },
    "MRS_Ph_180_days": {
        "event": "Test_F_online",
    },
    "MRS_hr_180_days": {
        "event": "MRS_FB_hr",
    },
    "Yackevich": {
        "url_contains": "https://kravira.by/staff/hirurgi-vrachi/yatskevich-oleg-stepanovich/",
    },
}

CUSTOM_CONVERSIONS: dict[str, str] = {
    "MRS_Ph_Spec": '{"and":[{"event":{"eq":"Test_F_Ph"}},{"or":[{"URL":{"i_contains":"kravira.by"}}]}]}',
    "MRS_Try_Spec": '{"and":[{"event":{"eq":"Test_F_try"}},{"or":[{"URL":{"i_contains":"kravira.by"}}]}]}',
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    return parser.parse_args()


def graph(settings, method: str, path: str, **kwargs) -> dict:
    url = f"https://graph.facebook.com/{settings.graph_api_version or 'v25.0'}/{path.lstrip('/')}"
    kwargs.setdefault("params" if method == "GET" else "data", {})["access_token"] = settings.access_token
    response = requests.request(method, url, timeout=60, **kwargs)
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"Meta вернула не-JSON для {path}: {response.text[:300]}") from exc
    if response.status_code != 200:
        err = payload.get("error", {})
        raise RuntimeError(err.get("error_user_msg") or err.get("message") or str(payload))
    return payload


def audience_rule(pixel_id: str, spec: dict) -> dict:
    if "event" in spec:
        filt = {
            "operator": "and",
            "filters": [{"field": "event", "operator": "eq", "value": spec["event"]}],
        }
    else:
        filt = {
            "operator": "and",
            "filters": [
                {
                    "operator": "or",
                    "filters": [
                        {
                            "field": "url",
                            "operator": "i_contains",
                            "value": spec["url_contains"],
                        }
                    ],
                }
            ],
        }
    rule = {
        "inclusions": {
            "operator": "or",
            "rules": [
                {
                    "event_sources": [{"type": "pixel", "id": pixel_id}],
                    "retention_seconds": 15_552_000,
                    "filter": filt,
                }
            ],
        }
    }
    if "url_contains" in spec:
        rule["inclusions"]["rules"][0]["template"] = "VISITORS_BY_URL"
    return rule


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def check(settings) -> int:
    pixel = graph(
        settings,
        "GET",
        settings.dataset_id,
        params={"fields": "id,name,enable_automatic_matching,automatic_matching_fields,last_fired_time"},
    )
    pixels = graph(
        settings,
        "GET",
        f"{settings.ad_account_ref}/adspixels",
        params={"fields": "id,name"},
    )
    audiences = graph(
        settings,
        "GET",
        f"{settings.ad_account_ref}/customaudiences",
        params={"fields": "id,name,delivery_status", "limit": 50},
    )
    conversions = graph(
        settings,
        "GET",
        f"{settings.ad_account_ref}/customconversions",
        params={"fields": "id,name", "limit": 20},
    )

    print("[dataset]", pixel)
    print("[ad account pixels]", pixels.get("data"))
    print("[audiences]", [(a["name"], a["id"]) for a in audiences.get("data", [])])
    print("[custom conversions]", [(c["name"], c["id"]) for c in conversions.get("data", [])])
    return 0


def apply(settings) -> int:
    state = load_state()
    pixel_id = settings.dataset_id
    if not pixel_id:
        raise RuntimeError("META_DATASET_ID_MRS не задан")

    graph(
        settings,
        "POST",
        pixel_id,
        data={
            "enable_automatic_matching": "true",
            "automatic_matching_fields": json.dumps(["em", "ph", "fn", "ln", "ct", "country"]),
        },
    )
    print("[ok] automatic advanced matching enabled")

    existing_conversions = {
        item["name"]: item["id"]
        for item in graph(
            settings,
            "GET",
            f"{settings.ad_account_ref}/customconversions",
            params={"fields": "name", "limit": 50},
        ).get("data", [])
    }
    state.setdefault("custom_conversions", {})
    for name, rule in CUSTOM_CONVERSIONS.items():
        if name in existing_conversions:
            state["custom_conversions"][name] = existing_conversions[name]
            print(f"[reused] custom conversion {name}")
            continue
        created = graph(
            settings,
            "POST",
            f"{settings.ad_account_ref}/customconversions",
            data={
                "name": name,
                "event_source_id": pixel_id,
                "custom_event_type": "OTHER",
                "rule": rule,
            },
        )
        state["custom_conversions"][name] = created["id"]
        print(f"[created] custom conversion {name}")

    existing_audiences = {
        item["name"]: item["id"]
        for item in graph(
            settings,
            "GET",
            f"{settings.ad_account_ref}/customaudiences",
            params={"fields": "name", "limit": 100},
        ).get("data", [])
    }
    state.setdefault("audiences", {})
    for name, spec in AUDIENCES.items():
        if name in existing_audiences:
            state["audiences"][name] = existing_audiences[name]
            print(f"[reused] audience {name}")
            continue
        created = graph(
            settings,
            "POST",
            f"{settings.ad_account_ref}/customaudiences",
            data={
                "name": name,
                "rule": json.dumps(audience_rule(pixel_id, spec)),
                "prefill": "1",
                "retention_days": "180",
            },
        )
        state["audiences"][name] = created["id"]
        print(f"[created] audience {name}")

    if not state.get("capi_bootstrap_sent"):
        now = int(time.time())
        batch = []
        for index, event_name in enumerate(WEB_EVENTS):
            batch.append(
                {
                    "event_name": event_name,
                    "event_time": now - index,
                    "event_id": f"bootstrap_{event_name}_{uuid.uuid4().hex[:8]}",
                    "action_source": "website",
                    "event_source_url": "https://kravira.by/",
                    "user_data": {
                        "client_ip_address": "203.0.113.10",
                        "client_user_agent": "Mozilla/5.0 (setup-mrs-capi-dataset)",
                        "fbp": "fb.1.1700000000000.9876543210",
                        "em": "setup.test@kravira.by",
                    },
                }
            )
        result = graph(
            settings,
            "POST",
            f"{pixel_id}/events",
            json={"data": batch},
        )
        state["capi_bootstrap_sent"] = True
        print(f"[ok] CAPI bootstrap events: {result.get('events_received')}")

    save_state(state)
    print(f"[complete] state saved to {STATE_PATH}")
    return 0


def main() -> int:
    try:
        settings = get_mrs_settings()
    except ConfigError as exc:
        print(f"[config] {exc}")
        return 2

    args = parse_args()
    try:
        if args.check:
            return check(settings)
        return apply(settings)
    except (RuntimeError, requests.RequestException) as exc:
        print(f"[error] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
