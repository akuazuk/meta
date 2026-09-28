"""Clone already-safe ads, verify 1:1 coverage, then swap old/new ad sets."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from scripts.create_laser_format_replacements import ACCOUNT, get, request
from scripts.migrate_other_active_formats import active_ads


ROOT = Path(__file__).resolve().parents[1]
REMAP_STATE = ROOT / "tmp_refs" / "all_format_fix" / "state.json"
DESIGN_STATE = ROOT / "tmp_refs" / "all_format_fix" / "design_state.json"
FINAL_STATE = ROOT / "tmp_refs" / "all_format_fix" / "finalize_state.json"

TARGETS = {
    "Флебологи_серия_Сайт": "120250631179730770",
    "Урологи_Серия_Сайт": "120250631182860770",
    "ЛОР_серия_Сайт": "120250631198310770",
    "ФГДС_Сайт": "120250631214700770",
    "Гинекология_Операции_Сайт": "120250631223360770",
    "Гинекология_Операции_2_Сайт": "120250631255310770",
    "Терапевты_Серия_Сайт": "120250631265910770",
    "Проктолог_серия_Сайт": "120250631271600770",
    "Гинекология_серия_Сайт": "120250631293900770",
    "Справки_Серия_Сайт": "120250631312470770",
}
CLONE_OPTIMAL = {
    "120250487259730770": "120250631198310770",  # Яровой_Аденоиды_2
    "120250486684580770": "120250631312470770",  # Абитуриент
    "120250486617440770": "120250631179730770",  # Попченко_15
}


def save(state: dict) -> None:
    FINAL_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--clone-only", action="store_true")
    args = parser.parse_args()
    ads = active_ads()
    by_id = {ad["id"]: ad for ad in ads}
    final = json.loads(FINAL_STATE.read_text(encoding="utf-8")) if FINAL_STATE.exists() else {"clones": {}, "swapped": {}}

    if args.apply or args.clone_only:
        for source_id, target_id in CLONE_OPTIMAL.items():
            if source_id in final["clones"]:
                continue
            source = by_id.get(source_id) or get(
                source_id,
                {"fields": "id,name,status,effective_status,adset{id,name},creative{id,name}"},
            )
            replacement = request(
                "POST",
                f"{ACCOUNT}/ads",
                data={
                    "name": f"{source['name']}__FORMAT_FIX_2026-08-10__CLONE",
                    "adset_id": target_id,
                    "creative": json.dumps({"creative_id": source["creative"]["id"]}),
                    "status": "PAUSED",
                },
            )["id"]
            final["clones"][source_id] = {"replacement_ad_id": replacement, "target_adset_id": target_id}
            save(final)
            print(f"cloned {replacement} <- {source_id} {source['name']}")

    remap = json.loads(REMAP_STATE.read_text(encoding="utf-8"))
    design = json.loads(DESIGN_STATE.read_text(encoding="utf-8"))
    covered = set(remap) | {key for key, value in design.items() if value.get("replacement_ad_id")} | set(final["clones"])
    source_groups: dict[str, list[dict]] = defaultdict(list)
    for ad in ads:
        name = ad.get("adset", {}).get("name", "")
        if name in TARGETS:
            source_groups[name].append(ad)

    problems = []
    for name, source_ads in source_groups.items():
        missing = [ad["id"] for ad in source_ads if ad["id"] not in covered]
        if missing:
            problems.append(f"{name}: missing {missing}")
        print(f"verified {name}: {len(source_ads)} source ads, {len(source_ads)-len(missing)} replacements")
    if problems:
        raise RuntimeError("Coverage verification failed: " + "; ".join(problems))
    if args.clone_only:
        print("clone-only verified; live ad sets unchanged")
        return 0
    if not args.apply:
        print("dry-run verified; use --apply to switch")
        return 0

    for name, source_ads in source_groups.items():
        if name in final["swapped"]:
            continue
        source_adset_id = source_ads[0]["adset"]["id"]
        target_adset_id = TARGETS[name]
        request("POST", source_adset_id, data={"status": "PAUSED"})
        request("POST", target_adset_id, data={"status": "ACTIVE"})
        final["swapped"][name] = {
            "source_adset_id": source_adset_id,
            "target_adset_id": target_adset_id,
            "source_status": "PAUSED",
            "target_status": "ACTIVE",
        }
        save(final)
        print(f"swapped {name}: {source_adset_id} -> {target_adset_id}")
    print(json.dumps({"clones": len(final["clones"]), "swapped": len(final["swapped"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
