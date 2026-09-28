"""Read-only export of the image mapped to Facebook Search for active ads."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from scripts.audit_active_ad_formats import ACCOUNT, graph_all, graph_get


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tmp_refs" / "active_search_audit_2026-08-12"


def hashes(ad: dict) -> tuple[dict[str, str], list[str]]:
    feed = ad.get("creative", {}).get("asset_feed_spec", {})
    labels = {
        label["name"]: item["hash"]
        for item in feed.get("images", [])
        if item.get("hash")
        for label in item.get("adlabels", [])
        if label.get("name")
    }
    all_hashes = [item["hash"] for item in feed.get("images", []) if item.get("hash")]
    link_hash = ad.get("creative", {}).get("object_story_spec", {}).get("link_data", {}).get("image_hash")
    if link_hash:
        all_hashes.append(link_hash)
    return labels, list(dict.fromkeys(all_hashes))


def search_hash(ad: dict) -> tuple[str | None, str]:
    feed = ad.get("creative", {}).get("asset_feed_spec", {})
    labels, all_hashes = hashes(ad)
    for rule in feed.get("asset_customization_rules", []):
        spec = rule.get("customization_spec", {})
        if "search" in spec.get("facebook_positions", []):
            label = rule.get("image_label", {}).get("name")
            return labels.get(label), "explicit"
    return (all_hashes[0] if len(all_hashes) == 1 else None), "automatic"


def font(size: int):
    candidates = [
        ROOT / "assets" / "Montserrat-SemiBold.ttf",
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ads = graph_all(
        f"{ACCOUNT}/ads",
        {
            "filtering": json.dumps([{"field": "effective_status", "operator": "IN", "value": ["ACTIVE"]}]),
            "fields": "id,name,status,effective_status,campaign{id,name,status,effective_status},adset{id,name,status,effective_status},creative{id,name,object_story_spec,asset_feed_spec}",
            "limit": 500,
        },
    )
    all_needed = sorted({image_hash for ad in ads for image_hash in hashes(ad)[1]})
    selected = []
    needed = set()
    for ad in ads:
        image_hash, mode = search_hash(ad)
        selected.append({"ad": ad, "hash": image_hash, "mode": mode})
        if image_hash:
            needed.add(image_hash)
    metadata = {}
    for offset in range(0, len(all_needed), 40):
        part = all_needed[offset:offset + 40]
        payload = graph_get(f"{ACCOUNT}/adimages", {"hashes": json.dumps(part), "fields": "hash,name,width,height,url", "limit": 100})
        for item in payload.get("data", []):
            metadata[item["hash"]] = item

    rows = []
    for item in selected:
        ad, image_hash = item["ad"], item["hash"]
        row = {
            "campaign": ad.get("campaign", {}).get("name", ""),
            "campaign_status": ad.get("campaign", {}).get("effective_status", ""),
            "adset": ad.get("adset", {}).get("name", ""),
            "adset_status": ad.get("adset", {}).get("effective_status", ""),
            "ad": ad.get("name", ""), "id": ad["id"], "mode": item["mode"], "hash": image_hash,
        }
        meta = metadata.get(image_hash or "", {})
        row.update({key: meta.get(key) for key in ("width", "height", "url")})
        if meta.get("url"):
            path = OUT / f"{ad['id']}_{image_hash[:8]}.jpg"
            urllib.request.urlretrieve(meta["url"], path)
            row["path"] = str(path)
        rows.append(row)
    (OUT / "search_assets.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    card_w, card_h, thumb_h = 420, 480, 350
    per_sheet = 12
    title_font, sub_font = font(22), font(16)
    for sheet_i in range(0, len(rows), per_sheet):
        subset = rows[sheet_i:sheet_i + per_sheet]
        sheet = Image.new("RGB", (card_w * 3, card_h * 4), "white")
        draw = ImageDraw.Draw(sheet)
        for idx, row in enumerate(subset):
            x, y = (idx % 3) * card_w, (idx // 3) * card_h
            if row.get("path"):
                source = Image.open(row["path"]).convert("RGB")
                source.thumbnail((card_w, thumb_h))
                px = x + (card_w - source.width) // 2
                py = y + (thumb_h - source.height) // 2
                sheet.paste(source, (px, py))
            draw.rectangle((x, y, x + card_w - 1, y + card_h - 1), outline="#777", width=2)
            name = row["ad"][:40]
            campaign = row["campaign"][:30]
            draw.text((x + 10, y + 358), campaign, fill="#006457", font=sub_font)
            draw.text((x + 10, y + 382), name, fill="black", font=title_font)
            draw.text((x + 10, y + 414), f"ID {row['id']} | {row.get('width')}x{row.get('height')} | {row['mode']}", fill="#333", font=sub_font)
        sheet.save(OUT / f"contact_{sheet_i // per_sheet + 1}.jpg", quality=92)

    all_rows = []
    seen = set()
    for ad in ads:
        for image_hash in hashes(ad)[1]:
            if image_hash in seen:
                continue
            seen.add(image_hash)
            meta = metadata.get(image_hash, {})
            row = {
                "campaign": ad.get("campaign", {}).get("name", ""),
                "ad": ad.get("name", ""), "id": ad["id"], "hash": image_hash,
                "width": meta.get("width"), "height": meta.get("height"),
            }
            if meta.get("url"):
                path = OUT / f"all_{ad['id']}_{image_hash[:8]}.jpg"
                urllib.request.urlretrieve(meta["url"], path)
                row["path"] = str(path)
            all_rows.append(row)
    (OUT / "all_assets.json").write_text(json.dumps(all_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    all_per_sheet = 12
    for sheet_i in range(0, len(all_rows), all_per_sheet):
        subset = all_rows[sheet_i:sheet_i + all_per_sheet]
        sheet = Image.new("RGB", (card_w * 3, card_h * 4), "white")
        draw = ImageDraw.Draw(sheet)
        for idx, row in enumerate(subset):
            x, y = (idx % 3) * card_w, (idx // 3) * card_h
            if row.get("path"):
                source = Image.open(row["path"]).convert("RGB")
                source.thumbnail((card_w, thumb_h))
                px = x + (card_w - source.width) // 2
                py = y + (thumb_h - source.height) // 2
                sheet.paste(source, (px, py))
            draw.rectangle((x, y, x + card_w - 1, y + card_h - 1), outline="#777", width=2)
            draw.text((x + 10, y + 358), row["campaign"][:30], fill="#006457", font=sub_font)
            draw.text((x + 10, y + 382), row["ad"][:40], fill="black", font=title_font)
            draw.text((x + 10, y + 414), f"{row.get('width')}x{row.get('height')} | {row['hash'][:8]}", fill="#333", font=sub_font)
        sheet.save(OUT / f"all_contact_{sheet_i // all_per_sheet + 1}.jpg", quality=92)
    print(json.dumps({"ads": len(rows), "mapped": sum(bool(r.get('path')) for r in rows), "search_sheets": (len(rows)+per_sheet-1)//per_sheet, "unique_assets": len(all_rows), "all_sheets": (len(all_rows)+all_per_sheet-1)//all_per_sheet}, ensure_ascii=False))
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
