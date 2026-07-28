"""Сборка финальных баннеров из эталона v2-стиля.

Берёт AI-эталоны стиля, убирает нарисованное лого, ставит прозрачный
`image/brand/logo_transparent.png`, заменяет длинное тире на короткое `–`.

Запуск:
    source .venv/bin/activate
    python -m scripts.build_ad_banners
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path.home() / ".cursor/projects/Users-pavelkuzauka-Cursor-Folders-Meta/assets"
OUT = ROOT / "image" / "concepts"
BRAND = ROOT / "image" / "brand"
FONTS = ROOT / "assets" / "fonts"
LOGO = BRAND / "logo_transparent.png"

# Локальные копии эталонов (если assets недоступны, кладём источники в image/brand/sources)
SOURCES = {
    "final_1_unique.jpg": [
        ASSETS / "kravira_v2_concept_1_unique.jpg",
        BRAND / "sources" / "kravira_v2_concept_1_unique.jpg",
    ],
    "final_2_health.jpg": [
        ASSETS / "kravira_v2_concept_2_health.jpg",
        BRAND / "sources" / "kravira_v2_concept_2_health.jpg",
    ],
    "final_3_hear.jpg": [
        ASSETS / "kravira_v2_concept_3_hear.jpg",
        BRAND / "sources" / "kravira_v2_concept_3_hear.jpg",
    ],
}

DASH_SPECS = {
    "final_1_unique.jpg": [
        {"region": (400, 270, 560, 340), "mode": "dark", "size": 54},
        {"region": (340, 440, 470, 510), "mode": "white", "size": 50},
    ],
    "final_2_health.jpg": [
        {"region": (600, 280, 760, 350), "mode": "dark", "size": 50},
    ],
    "final_3_hear.jpg": [],
}


def resolve_source(candidates: list[Path]) -> Path:
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(f"Source not found among: {candidates}")


def cover_logo(im: Image.Image) -> Image.Image:
    w, h = im.size
    sample = np.array(im.crop((int(w * 0.52), int(h * 0.03), int(w * 0.66), int(h * 0.14))))
    mint = tuple(int(x) for x in sample.mean(axis=(0, 1))[:3])
    ImageDraw.Draw(im).rectangle((int(w * 0.695), 0, w, int(h * 0.32)), fill=mint)
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for x, y, r, a in [
        (int(w * 0.84), int(h * 0.11), 55, 28),
        (int(w * 0.93), int(h * 0.23), 42, 18),
        (int(w * 0.76), int(h * 0.18), 34, 14),
    ]:
        od.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, a))
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")


def paste_transparent_logo(im: Image.Image) -> Image.Image:
    logo = Image.open(LOGO).convert("RGBA")
    im = im.convert("RGBA")
    w, h = im.size
    tw = int(w * 0.195)
    lr = logo.resize((tw, int(logo.height * tw / logo.width)), Image.Resampling.LANCZOS)
    im.paste(lr, (w - lr.width - 36, 26), lr)
    return im.convert("RGB")


def overwrite_dash(im: Image.Image, region, mode: str, size: int) -> Image.Image:
    x0, y0, x1, y1 = region
    patch = np.array(im.crop((x0, y0, x1, y1)))
    if mode == "dark":
        target = np.array([21.0, 90.0, 76.0])
        dist = np.linalg.norm(patch.astype(float) - target, axis=2)
        mask = dist < 30
        fill = (21, 90, 76)
    else:
        mask = (patch[..., 0] > 230) & (patch[..., 1] > 230) & (patch[..., 2] > 230)
        fill = (255, 255, 255)

    h, w = mask.shape
    best = None
    for y in range(h):
        x = 0
        while x < w:
            if mask[y, x]:
                x2 = x
                while x2 < w and mask[y, x2]:
                    x2 += 1
                if x2 - x >= 35:
                    y2 = y
                    while y2 < h and mask[y2, x:x2].mean() > 0.5:
                        y2 += 1
                    if 3 <= y2 - y <= 14:
                        cand = (x, y, x2 - x, y2 - y)
                        if best is None or cand[2] > best[2]:
                            best = cand
                x = x2
            else:
                x += 1
    if not best:
        return im

    bx, by, bw, bh = best
    ax, ay = x0 + bx, y0 + by
    draw = ImageDraw.Draw(im)
    mint = tuple(
        int(v)
        for v in np.array(im.crop((ax, max(0, ay - 12), ax + bw, max(1, ay)))).mean(axis=(0, 1))[:3]
    )
    draw.rectangle((ax - 2, ay - 2, ax + bw + 2, ay + bh + 2), fill=mint)
    font = ImageFont.truetype(str(FONTS / "Montserrat-ExtraBold.ttf"), size)
    family, _ = font.getname()
    if family != "Montserrat":
        raise RuntimeError(f"Expected Montserrat, got {font.getname()}")
    draw.text((ax, ay - size * 0.35), "–", font=font, fill=fill)
    return im


def build_one(dst_name: str) -> Path:
    src = resolve_source(SOURCES[dst_name])
    im = Image.open(src).convert("RGB").resize((1080, 1080), Image.Resampling.LANCZOS)
    im = cover_logo(im)
    for spec in DASH_SPECS[dst_name]:
        im = overwrite_dash(im, spec["region"], spec["mode"], spec["size"])
    im = paste_transparent_logo(im)
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / dst_name
    im.save(out, quality=95)
    return out


def main() -> int:
    if not LOGO.exists():
        raise SystemExit(f"Missing transparent logo: {LOGO}")
    for name in SOURCES:
        path = build_one(name)
        print("saved", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
