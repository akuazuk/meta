"""Read-only audit of active Meta ads: image sizes, placement rules and crop risk."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"
REPORT = ROOT / "docs" / "META_ACTIVE_AD_FORMAT_AUDIT.md"


def load_env() -> dict[str, str]:
    values = dict(os.environ)
    for raw in ENV.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values.setdefault(key.strip(), value.strip().strip("'\""))
    return values


ENV_VALUES = load_env()
TOKEN = ENV_VALUES["META_ACCESS_TOKEN"]
VERSION = ENV_VALUES.get("META_GRAPH_API_VERSION", "v23.0")
ACCOUNT = "act_723170300839405"
BASE = f"https://graph.facebook.com/{VERSION}"


def graph_get(path: str, params: dict) -> dict:
    query = dict(params)
    query["access_token"] = TOKEN
    url = f"{BASE}/{path.lstrip('/')}?{urllib.parse.urlencode(query)}"
    with urllib.request.urlopen(url, timeout=90) as response:
        return json.load(response)


def graph_all(path: str, params: dict) -> list[dict]:
    result: list[dict] = []
    payload = graph_get(path, params)
    while True:
        result.extend(payload.get("data", []))
        next_url = payload.get("paging", {}).get("next")
        if not next_url:
            return result
        with urllib.request.urlopen(next_url, timeout=90) as response:
            payload = json.load(response)


def chunks(items: list[str], size: int):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def ratio_kind(width: int, height: int) -> tuple[str, float]:
    ratio = width / height
    if 0.94 <= ratio <= 1.06:
        return "1:1", ratio
    if 0.52 <= ratio <= 0.60:
        return "9:16", ratio
    if 0.76 <= ratio <= 0.84:
        return "4:5", ratio
    if 1.72 <= ratio <= 1.82:
        return "16:9", ratio
    if 1.85 <= ratio <= 1.98:
        return "1.91:1", ratio
    if ratio > 1.06:
        return f"гориз. {ratio:.2f}:1", ratio
    return f"верт. 1:{1 / ratio:.2f}", ratio


def placement_group(spec: dict) -> tuple[str, str]:
    values: list[str] = []
    for key in (
        "facebook_positions",
        "instagram_positions",
        "messenger_positions",
        "audience_network_positions",
        "threads_positions",
    ):
        values.extend(spec.get(key, []))
    if not values and not spec.get("publisher_platforms"):
        return "default", "остальные автоматические плейсменты"

    joined = " ".join(values)
    if any(token in joined for token in ("feed", "stream", "marketplace")):
        return "feed", "/".join(values)
    if any(token in joined for token in ("right_hand_column", "search")):
        return "compact", "/".join(values)
    if any(token in joined for token in ("story", "reels")):
        return "vertical", "/".join(values)
    return "default", "/".join(values) or "автоматические плейсменты"


def assess(group: str, kind: str, ratio: float) -> tuple[str, str]:
    if group == "all":
        if kind == "9:16":
            return "PARTIAL", "Stories/Reels без обрезки, но Feed обрежет примерно до 4:5"
        if kind in {"1:1", "4:5"} or 0.70 <= ratio <= 1.06:
            return "PARTIAL", "Feed безопасен, но Stories/Reels потребуют автокадрирование/поля"
        return "RISK", "горизонтальный файл в Stories/Reels будет сильно обрезан или уменьшен"

    if group == "feed":
        if kind in {"1:1", "4:5"}:
            return "OK", "Feed без обрезки"
        if ratio >= 1.45:
            return "OK", "Feed принимает горизонтальный формат, но он занимает меньше экрана"
        if 0.73 <= ratio < 0.76:
            return "RISK", "формат 3:4 может быть обрезан примерно до 4:5 в части Facebook Feed"
        return "RISK", "вертикальный файл в Feed будет ограничен или обрезан примерно до 4:5"

    if group == "compact":
        if kind in {"1:1", "1.91:1", "16:9"} or ratio >= 1.45:
            return "OK", "подходит для Right Column/Search"
        return "RISK", "вертикальный файл будет заметно обрезан в Right Column/Search"

    # Explicit Stories/Reels or the default rule covering all remaining placements.
    if kind == "9:16":
        return "OK", "подходит для Stories/Reels"
    if kind in {"1:1", "4:5"} or 0.70 <= ratio <= 1.06:
        return "PARTIAL", "Feed безопасен, но Stories/Reels потребуют автокадрирование/поля"
    return "RISK", "горизонтальный файл в Stories/Reels будет сильно обрезан или уменьшен"


def collect_hashes(ad: dict) -> list[str]:
    creative = ad.get("creative", {})
    feed = creative.get("asset_feed_spec", {})
    result = [item.get("hash") for item in feed.get("images", []) if item.get("hash")]
    link_hash = creative.get("object_story_spec", {}).get("link_data", {}).get("image_hash")
    if link_hash:
        result.append(link_hash)
    return list(dict.fromkeys(result))


def audit_ad(ad: dict, images: dict[str, dict]) -> dict:
    creative = ad.get("creative", {})
    feed = creative.get("asset_feed_spec", {})
    image_items = feed.get("images", [])
    rules = feed.get("asset_customization_rules", [])
    labels: dict[str, str] = {}
    for item in image_items:
        image_hash = item.get("hash")
        for label in item.get("adlabels", []):
            if label.get("name") and image_hash:
                labels[label["name"]] = image_hash

    hashes = collect_hashes(ad)
    media_lines: list[str] = []
    for image_hash in hashes:
        meta = images.get(image_hash, {})
        width, height = meta.get("width"), meta.get("height")
        if width and height:
            kind, _ = ratio_kind(width, height)
            media_lines.append(f"{width}×{height} ({kind})")
        else:
            media_lines.append(f"{image_hash[:8]}… (размер не получен)")

    evaluations: list[tuple[str, str, str]] = []
    mapping_lines: list[str] = []
    if rules:
        for rule in rules:
            label = rule.get("image_label", {}).get("name")
            image_hash = labels.get(label or "")
            spec = rule.get("customization_spec", {})
            group, placement = placement_group(spec)
            meta = images.get(image_hash or "", {})
            width, height = meta.get("width"), meta.get("height")
            if width and height:
                kind, ratio = ratio_kind(width, height)
                level, note = assess(group, kind, ratio)
                mapping_lines.append(f"{placement}: {width}×{height}")
                evaluations.append((level, note, placement))
            else:
                evaluations.append(("UNKNOWN", "нет размера файла", placement))
    elif hashes:
        for image_hash in hashes:
            meta = images.get(image_hash, {})
            width, height = meta.get("width"), meta.get("height")
            if width and height:
                kind, ratio = ratio_kind(width, height)
                level, note = assess("all", kind, ratio)
                mapping_lines.append(f"все автоматические плейсменты: {width}×{height}")
                evaluations.append((level, note, "автоплейсменты"))
            else:
                evaluations.append(("UNKNOWN", "нет размера файла", "автоплейсменты"))
    else:
        evaluations.append(("UNKNOWN", "изображение/видео не определено", ""))

    levels = {item[0] for item in evaluations}
    if "RISK" in levels:
        verdict = "Обрезается"
    elif "UNKNOWN" in levels:
        verdict = "Не проверено"
    elif "PARTIAL" in levels:
        verdict = "Частично"
    else:
        verdict = "Оптимально"

    unique_notes = list(dict.fromkeys(item[1] for item in evaluations))
    return {
        "campaign": ad.get("campaign", {}).get("name", ""),
        "adset": ad.get("adset", {}).get("name", ""),
        "ad": ad.get("name", ""),
        "id": ad.get("id", ""),
        "media": "; ".join(media_lines) or "не определено",
        "mapping": "; ".join(mapping_lines) or "не определено",
        "verdict": verdict,
        "note": "; ".join(unique_notes),
    }


def main() -> int:
    ads = graph_all(
        f"{ACCOUNT}/ads",
        {
            "filtering": json.dumps(
                [{"field": "effective_status", "operator": "IN", "value": ["ACTIVE"]}]
            ),
            "fields": (
                "id,name,status,effective_status,campaign{id,name},"
                "adset{id,name,targeting},creative{id,name,image_url,thumbnail_url,"
                "object_story_spec,asset_feed_spec}"
            ),
            "limit": 500,
        },
    )
    hashes = sorted({image_hash for ad in ads for image_hash in collect_hashes(ad)})
    images: dict[str, dict] = {}
    for part in chunks(hashes, 40):
        payload = graph_get(
            f"{ACCOUNT}/adimages",
            {
                "hashes": json.dumps(part),
                "fields": "hash,name,width,height,url",
                "limit": 100,
            },
        )
        for item in payload.get("data", []):
            images[item["hash"]] = item

    rows = [audit_ad(ad, images) for ad in ads]
    rows.sort(key=lambda row: (row["campaign"].casefold(), row["ad"].casefold()))
    summary = Counter(row["verdict"] for row in rows)
    campaign_summary: dict[str, Counter] = {}
    for row in rows:
        campaign_summary.setdefault(row["campaign"], Counter())[row["verdict"]] += 1

    lines = [
        "# Аудит размеров активных объявлений Meta",
        "",
        f"Активных объявлений: **{len(rows)}**.",
        "",
        "Критерии: Feed - безопасно 1:1 или 4:5; Stories/Reels - 9:16; "
        "Right Column/Search - квадратный или горизонтальный файл. "
        "Пустые ограничения ad set означают автоматические плейсменты.",
        "",
        "## Сводка",
        "",
        "| Вердикт | Количество |",
        "| --- | ---: |",
    ]
    for key in ("Оптимально", "Частично", "Обрезается", "Не проверено"):
        lines.append(f"| {key} | {summary.get(key, 0)} |")
    lines.extend(
        [
            "",
            "## Сводка по кампаниям",
            "",
            "| Кампания | Активных | Оптимально | Частично | Обрезается |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for campaign in sorted(campaign_summary, key=str.casefold):
        counts = campaign_summary[campaign]
        total = sum(counts.values())
        lines.append(
            f"| {campaign} | {total} | {counts.get('Оптимально', 0)} | "
            f"{counts.get('Частично', 0)} | {counts.get('Обрезается', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Все активные объявления",
            "",
            "| Кампания | Объявление | ID | Медиа | Привязка к плейсментам | Вердикт | Причина |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        values = [
            row["campaign"],
            row["ad"],
            row["id"],
            row["media"],
            row["mapping"],
            row["verdict"],
            row["note"],
        ]
        clean = [value.replace("|", "/").replace("\n", " ") for value in values]
        lines.append("| " + " | ".join(clean) + " |")

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"ads": len(rows), "images": len(images), "summary": summary}, ensure_ascii=False))
    print(REPORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
