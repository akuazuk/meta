"""Сборка финальных баннеров Кравиры.

Исходники уже содержат утверждённую композицию «триггер → решение → действие».
Скрипт нормализует размер и добавляет официальный знак как ненавязчивый
полупрозрачный элемент фона, не перекрывающий врача или рекламный текст.

Запуск:
    source .venv/bin/activate
    python -m scripts.build_ad_banners
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "image" / "concepts"
BRAND = ROOT / "image" / "brand"
WATERMARK = ROOT / "image" / "logo_circle.png"

SOURCES = {
    "final_1_unique.jpg": BRAND / "sources" / "kravira_v2_concept_1_unique.jpg",
    "final_2_health.jpg": BRAND / "sources" / "kravira_v2_concept_2_health.jpg",
    "final_3_hear.jpg": BRAND / "sources" / "kravira_v2_concept_3_hear.jpg",
}


def add_background_logo(im: Image.Image) -> Image.Image:
    """Добавляет официальный знак в свободную верхнюю область как watermark."""
    base = im.convert("RGBA")
    mark = Image.open(WATERMARK).convert("RGBA")
    target_width = int(base.width * 0.16)
    mark = mark.resize(
        (target_width, int(mark.height * target_width / mark.width)),
        Image.Resampling.LANCZOS,
    )
    alpha = mark.getchannel("A").point(lambda value: int(value * 0.16))
    mark.putalpha(alpha)
    position = ((base.width - mark.width) // 2, 24)
    base.alpha_composite(mark, position)
    return base.convert("RGB")


def build_one(dst_name: str) -> Path:
    source = SOURCES[dst_name]
    if not source.exists():
        raise FileNotFoundError(f"Missing source: {source}")

    im = Image.open(source).convert("RGB")
    im = im.resize((1080, 1080), Image.Resampling.LANCZOS)
    im = add_background_logo(im)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / dst_name
    im.save(out, quality=95, optimize=True, subsampling=0)
    return out


def main() -> int:
    if not WATERMARK.exists():
        raise SystemExit(f"Missing watermark logo: {WATERMARK}")
    for name in SOURCES:
        path = build_one(name)
        print("saved", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
