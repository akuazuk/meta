"""Новые группы вакансий на цель «Отправить резюме» и пауза старых.

Meta не даёт сменить конверсию у уже опубликованной группы, поэтому
обучение сбрасывается новой группой с теми же объявлениями.
"""

from __future__ import annotations

import json
from pathlib import Path

import requests
from dotenv import dotenv_values

CAMPAIGN = "120247828518660434"
ACCT = "act_2649521998797481"
CC_RESUME = "2491849758003783"
STATE_PATH = Path(__file__).resolve().parents[1] / "tmp_refs" / "restart_vacancy_learning.json"


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
        raise RuntimeError(
            f"{path}: {err.get('error_user_msg') or err.get('message') or payload}"
        )
    return payload


def slim_targeting(src: dict) -> dict:
    geo = src.get("geo_locations") or {}
    cities = []
    for city in geo.get("cities") or []:
        item = {"key": city["key"]}
        if city.get("radius") is not None:
            item["radius"] = city["radius"]
        if city.get("distance_unit"):
            item["distance_unit"] = city["distance_unit"]
        cities.append(item)
    targeting = {
        "age_min": src.get("age_min", 18),
        "age_max": src.get("age_max", 65),
        "geo_locations": {
            "cities": cities,
            "location_types": geo.get("location_types")
            or ["frequently_in", "home", "recent"],
        },
        "locales": [17],
        "brand_safety_content_filter_levels": src.get("brand_safety_content_filter_levels")
        or ["FACEBOOK_RELAXED", "AN_RELAXED", "FEED_RELAXED"],
        "targeting_automation": src.get("targeting_automation")
        or {"advantage_audience": 0, "individual_setting": {"geo": 1}},
    }
    if "user_age_unknown" in src:
        targeting["user_age_unknown"] = src["user_age_unknown"]
    flex = []
    for group in src.get("flexible_spec") or []:
        cleaned = {}
        for key, items in group.items():
            if isinstance(items, list):
                cleaned[key] = [{"id": item["id"]} for item in items if item.get("id")]
        if cleaned:
            flex.append(cleaned)
    if flex:
        targeting["flexible_spec"] = flex
    if src.get("custom_audiences"):
        targeting["custom_audiences"] = [
            {"id": item["id"]} for item in src["custom_audiences"]
        ]
    return targeting


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"adsets": {}}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    env = dotenv_values(Path(__file__).resolve().parents[1] / ".env")
    token = env["META_ACCESS_TOKEN_MRS"]
    version = env.get("META_GRAPH_API_VERSION") or "v25.0"
    state = load_state()

    sets = graph(
        token,
        version,
        "GET",
        f"{CAMPAIGN}/adsets",
        params={
            "fields": "id,name,status,daily_budget,billing_event,optimization_goal,bid_strategy,destination_type,targeting,attribution_spec",
            "limit": 50,
        },
    )["data"]
    # не трогать уже перенесённые архивы
    sources = [s for s in sets if not s["name"].endswith("— старая цель")]

    for src in sources:
        slot = state["adsets"].setdefault(src["id"], {})
        if not slot.get("new_id"):
            created = graph(
                token,
                version,
                "POST",
                f"{ACCT}/adsets",
                data={
                    "name": src["name"],
                    "campaign_id": CAMPAIGN,
                    "daily_budget": src["daily_budget"],
                    "billing_event": src.get("billing_event") or "IMPRESSIONS",
                    "optimization_goal": "OFFSITE_CONVERSIONS",
                    "bid_strategy": src.get("bid_strategy") or "LOWEST_COST_WITHOUT_CAP",
                    "destination_type": "WEBSITE",
                    "promoted_object": json.dumps({"custom_conversion_id": CC_RESUME}),
                    "targeting": json.dumps(slim_targeting(src["targeting"])),
                    "attribution_spec": json.dumps(
                        src.get("attribution_spec")
                        or [
                            {"event_type": "CLICK_THROUGH", "window_days": 7},
                            {"event_type": "VIEW_THROUGH", "window_days": 1},
                        ]
                    ),
                    "status": "PAUSED",
                },
            )
            slot["new_id"] = created["id"]
            save_state(state)
            print(f"[created] {src['name']} {slot['new_id']}")
        else:
            print(f"[reused] {src['name']} {slot['new_id']}")

        ads = graph(
            token,
            version,
            "GET",
            f"{src['id']}/ads",
            params={"fields": "id,name,status,creative{id}", "limit": 50},
        )["data"]
        slot.setdefault("ads", {})
        for ad in ads:
            if ad["id"] in slot["ads"]:
                continue
            creative_id = (ad.get("creative") or {}).get("id")
            if not creative_id:
                raise RuntimeError(f"no creative on {ad['id']}")
            created = graph(
                token,
                version,
                "POST",
                f"{ACCT}/ads",
                data={
                    "name": ad["name"],
                    "adset_id": slot["new_id"],
                    "creative": json.dumps({"creative_id": creative_id}),
                    "status": "ACTIVE" if ad.get("status") == "ACTIVE" else "PAUSED",
                },
            )
            slot["ads"][ad["id"]] = created["id"]
            save_state(state)
            print(f"  [ad] {ad['name']} → {created['id']}")

        if not slot.get("old_paused"):
            graph(
                token,
                version,
                "POST",
                src["id"],
                data={"status": "PAUSED", "name": f"{src['name']} — старая цель"},
            )
            slot["old_paused"] = True
            save_state(state)
            print(f"[paused] {src['name']} — старая цель")

        if src.get("status") == "ACTIVE" and not slot.get("new_active"):
            graph(
                token,
                version,
                "POST",
                slot["new_id"],
                data={"status": "ACTIVE"},
            )
            slot["new_active"] = True
            save_state(state)
            print(f"[active] {src['name']} {slot['new_id']}")

    print("[complete]")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
