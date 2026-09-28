"""locale 6 = English (US); русский = 17. Расширить детальный таргет вакансий."""

from __future__ import annotations

import json
from pathlib import Path

import requests
from dotenv import dotenv_values

VAC_CAMP = "120247828518660434"
HR_ADSET = "120248112990910434"
KARDIO_ADSET = "120248112990210434"
ACCT = "act_2649521998797481"


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


def ids_only(items: list[dict]) -> list[dict]:
    return [{"id": item["id"], "name": item.get("name")} for item in items if item.get("id")]


def broaden_flex(flex: list[dict] | None) -> list[dict] | None:
    if not flex:
        return flex
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for group in flex:
        for key in (
            "interests",
            "education_majors",
            "work_positions",
            "industries",
            "behaviors",
        ):
            items = ids_only(group.get(key) or [])
            if not items:
                continue
            fingerprint = (key, tuple(sorted(x["id"] for x in items)))
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            out.append({key: items})
    return out or flex


def slim_geo(geo: dict) -> dict:
    cities = []
    for city in geo.get("cities") or []:
        item = {"key": city["key"]}
        if "radius" in city:
            item["radius"] = city["radius"]
        if "distance_unit" in city:
            item["distance_unit"] = city["distance_unit"]
        cities.append(item)
    out = {}
    if cities:
        out["cities"] = cities
    if geo.get("countries"):
        out["countries"] = geo["countries"]
    if geo.get("location_types"):
        out["location_types"] = geo["location_types"]
    return out


def build_targeting(src: dict, *, locale: int, flex=None, drop_custom: bool = False) -> dict:
    targeting = {
        "age_min": src.get("age_min", 18),
        "age_max": src.get("age_max", 65),
        "geo_locations": slim_geo(src.get("geo_locations") or {}),
        "locales": [locale],
        "brand_safety_content_filter_levels": src.get(
            "brand_safety_content_filter_levels"
        )
        or ["FACEBOOK_RELAXED", "AN_RELAXED", "FEED_RELAXED"],
        "targeting_automation": src.get("targeting_automation")
        or {"advantage_audience": 0, "individual_setting": {"geo": 1}},
    }
    if "user_age_unknown" in src:
        targeting["user_age_unknown"] = src["user_age_unknown"]
    if flex is not None:
        targeting["flexible_spec"] = flex
    elif src.get("flexible_spec"):
        targeting["flexible_spec"] = src["flexible_spec"]
    if not drop_custom and src.get("custom_audiences"):
        targeting["custom_audiences"] = [
            {"id": item["id"]} for item in src["custom_audiences"]
        ]
    return targeting


def estimate(token: str, version: str, targeting: dict) -> str:
    try:
        payload = graph(
            token,
            version,
            "GET",
            f"{ACCT}/delivery_estimate",
            params={
                "targeting_spec": json.dumps(targeting),
                "optimization_goal": "OFFSITE_CONVERSIONS",
            },
        )
        row = (payload.get("data") or [{}])[0]
        daily = row.get("daily_outcomes_curve") or row
        return json.dumps(
            {
                "estimate_mau": row.get("estimate_mau_lower_bound")
                or row.get("estimate_mau"),
                "estimate_mau_upper": row.get("estimate_mau_upper_bound"),
                "estimate_dau": row.get("estimate_dau"),
            },
            ensure_ascii=False,
        )
    except Exception as exc:  # noqa: BLE001
        return f"n/a ({exc})"


def main() -> int:
    env = dotenv_values(Path(__file__).resolve().parents[1] / ".env")
    token = env["META_ACCESS_TOKEN_MRS"]
    version = env.get("META_GRAPH_API_VERSION") or "v25.0"
    sets = graph(
        token,
        version,
        "GET",
        f"{ACCT}/adsets",
        params={"fields": "id,name,campaign_id,targeting", "limit": 200},
    )["data"]
    by_id = {item["id"]: item for item in sets}
    kardio_flex = broaden_flex((by_id[KARDIO_ADSET].get("targeting") or {}).get("flexible_spec"))

    for item in sets:
        src = item.get("targeting") or {}
        old_locales = src.get("locales")
        is_vac = item.get("campaign_id") == VAC_CAMP
        drop_custom = item["id"] == HR_ADSET
        flex = None
        if is_vac:
            if item["id"] == HR_ADSET:
                flex = kardio_flex
            else:
                flex = broaden_flex(src.get("flexible_spec"))
        targeting = build_targeting(
            src, locale=17, flex=flex, drop_custom=drop_custom
        )
        changed_lang = old_locales != [17]
        changed_flex = is_vac
        if not changed_lang and not changed_flex:
            print(f"[skip] {item['name']} already ru")
            continue
        graph(
            token,
            version,
            "POST",
            item["id"],
            data={"targeting": json.dumps(targeting)},
        )
        bits = []
        if changed_lang:
            bits.append(f"locale {old_locales} → [17]")
        if changed_flex:
            bits.append("flex OR")
        if drop_custom:
            bits.append("убрал узкий список HR из AND")
        print(f"[ok] {item['name']} {item['id']}: {', '.join(bits)}")
        if is_vac:
            print(f"     estimate {estimate(token, version, targeting)}")

    print("[complete] русский locale 17 + расширенный таргет вакансий")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
