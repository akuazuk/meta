"""Два объявления проктолога Гусевой в группу «Проктолог — сайт»."""

from __future__ import annotations

import json
from pathlib import Path

import scripts.create_kardiolog_vacancy as kard
from scripts.create_kardiolog_vacancy import build_creative, graph, upload_image
from src.config import get_mrs_settings

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "image" / "concepts" / "proctolog" / "Guseva"
STATE_PATH = ROOT / "tmp_refs" / "add_guseva_prokt.json"
ADSET_ID = "120247744636610434"
LINK = "https://kravira.by/staff/guseva-marina-igorevna-/?clear_cache=Y"
URL_TAGS = "utm_source=facebook&utm_medium=cpc&utm_campaign=proktolog_guseva"

ADS = [
    {
        "key": "1",
        "name": "Гусева — дискомфорт",
        "sq": "ГУСЕВА1(1).png",
        "vt": "ГУСЕВА_проктолог.png",
        "ls": "Гусева1.png",
        "bodies": [
            "Боль, жжение и зуд – повод обратиться за консультацией к проктологу.",
            "Когда каждый поход в туалет приносит дискомфорт, не откладывайте визит.",
            "Врач-проктолог Гусева Марина Игоревна. Стаж по специальности с 2016 года.",
            "Бережная консультация проктолога в медицинском центре Кравира, Минск.",
            "Дискомфорт в туалете – не норма. Запишитесь к врачу-проктологу.",
            "Консультация Гусевой Марины Игоревны: осмотр и понятные рекомендации.",
            "Стаж по специальности с 2016 года. Запись на странице врача.",
            "Если поход в туалет стал источником дискомфорта – запишитесь к проктологу.",
            "Боль, жжение, зуд. Врач-проктолог Гусева принимает в Кравира.",
            "Не терпите симптомы. Консультация проктолога – на странице врача.",
        ],
        "titles": [
            "Когда туалет приносит дискомфорт",
            "Боль, жжение, зуд",
            "Повод обратиться к проктологу",
            "Гусева Марина Игоревна",
            "Врач-проктолог, стаж с 2016 года",
            "Консультация проктолога в Кравира",
            "Не терпите дискомфорт",
            "Запишитесь к проктологу Гусевой",
            "Бережная консультация",
            "Проктолог в Минске",
        ],
        "description": (
            "Консультация врача-проктолога Гусевой М. И. в Кравира. Стаж с 2016 года."
        ),
    },
    {
        "key": "2",
        "name": "Гусева — осмотр",
        "sq": "ГУСЕВА2.png",
        "vt": "ГУСЕВА_проктолог2.png",
        "ls": "Гусева2(1).png",
        "bodies": [
            "Больно ходить в туалет? Боль и жжение после дефекации – повод к проктологу.",
            "Бережный осмотр врача-проктолога Гусевой Марины Игоревны.",
            "Стаж по специальности с 2016 года. Запись на странице врача.",
            "Не терпите боль после туалета. Консультация проктолога в Кравира.",
            "Бережный приём без лишнего стресса. Врач-проктолог в Минске.",
            "Боль и жжение после дефекации. Запишитесь к Гусевой М. И.",
            "Осмотр проктолога, если больно ходить в туалет.",
            "Врач-проктолог Гусева Марина Игоревна принимает в медицинском центре Кравира.",
            "Бережный осмотр и понятные рекомендации. Стаж с 2016 года.",
            "Если после туалета боль и жжение – не откладывайте визит к проктологу.",
        ],
        "titles": [
            "Больно ходить в туалет?",
            "Боль и жжение после дефекации",
            "Бережный осмотр проктолога",
            "Гусева Марина Игоревна",
            "Стаж по специальности с 2016 года",
            "Не терпите боль после туалета",
            "Запишитесь на осмотр",
            "Бережный приём в Кравира",
            "Врач-проктолог в Минске",
            "Консультация без лишнего стресса",
        ],
        "description": (
            "Бережный осмотр врача-проктолога Гусевой М. И. в Кравира. Стаж с 2016 года."
        ),
    },
]


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
            print(f"[uploaded] {path.name}")

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
            print(f"[created] creative {spec['name']} {created['id']}")
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
                "adset_id": ADSET_ID,
                "creative": json.dumps({"creative_id": state["creatives"][spec["key"]]}),
                "status": "ACTIVE",
            },
        )
        state["ads"][spec["key"]] = ad["id"]
        save_state(state)
        print(f"[created] ad {spec['name']} {ad['id']}")

    print("[complete]")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
