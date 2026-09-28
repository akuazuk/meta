"""Download source creatives for active ads that lack placement-safe formats."""

from __future__ import annotations

import json
from pathlib import Path

import requests

from scripts.migrate_other_active_formats import active_ads, collect_hashes
from scripts.create_laser_format_replacements import ACCOUNT, get


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tmp_refs" / "all_format_fix" / "design_sources"
IDS = {
    "120250487601200770",
    "120250486829330770",
    "120250486844340770",
    "120250486838780770",
    "120250486834710770",
    "120250487253590770",
    "120250487246110770",
    "120250486759170770",
    "120250486709060770",
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ads = [ad for ad in active_ads() if ad["id"] in IDS]
    hashes = sorted({image_hash for ad in ads for image_hash in collect_hashes(ad)})
    payload = get(
        f"{ACCOUNT}/adimages",
        {
            "hashes": json.dumps(hashes),
            "fields": "hash,width,height,name,url,url_128",
            "limit": 100,
        },
    )
    metadata = {item["hash"]: item for item in payload.get("data", [])}
    manifest = []
    for ad in ads:
        entry = {
            "id": ad["id"],
            "name": ad["name"],
            "campaign": ad.get("campaign", {}).get("name", ""),
            "adset": ad.get("adset", {}).get("name", ""),
            "creative": ad.get("creative", {}),
            "images": [],
        }
        for index, image_hash in enumerate(collect_hashes(ad), start=1):
            item = metadata.get(image_hash)
            if not item:
                continue
            extension = ".png" if str(item.get("name", "")).lower().endswith(".png") else ".jpg"
            path = OUT / f"{ad['id']}_{index}_{item['width']}x{item['height']}{extension}"
            response = requests.get(item["url"], timeout=120)
            response.raise_for_status()
            path.write_bytes(response.content)
            entry["images"].append({**item, "path": str(path)})
            print(path)
        manifest.append(entry)
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(OUT / "manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
