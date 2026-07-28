"""Сборка баннеров Кравира v5.

- прозрачный логотип image/brand/logo_transparent.png
- телефонная иконка из референса image/brand/phone_icon.png
- шрифт Montserrat (ExtraBold/Bold/SemiBold)
- короткое тире –

Запуск:
    source .venv/bin/activate
    python -m scripts.build_ad_banners
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "image" / "brand"
FONTS = ROOT / "assets" / "fonts"
OUT = ROOT / "image" / "concepts"
LOGO = BRAND / "logo_transparent.png"
PHONE = BRAND / "phone_icon.png"

BG = (184, 220, 214)
DARK = (18, 88, 74)
WHITE = (255, 255, 255)
PILL = (70, 143, 130)
W = H = 1080


def fnt(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = FONTS / name
    font = ImageFont.truetype(str(path), size=size)
    family, style = font.getname()
    if family != "Montserrat":
        raise RuntimeError(f"Expected Montserrat, got {font.getname()} from {path}")
    return font


def make_bg() -> Image.Image:
    base = Image.new("RGBA", (W, H), BG + (255,))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for x, y, r, a in [
        (820, 160, 95, 34),
        (960, 400, 70, 24),
        (780, 540, 55, 20),
        (1000, 700, 80, 18),
        (700, 120, 40, 18),
        (860, 860, 60, 16),
        (210, 910, 50, 14),
        (110, 210, 35, 12),
    ]:
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, a))
    return Image.alpha_composite(base, overlay)


def build(
    name: str,
    person_path: Path,
    person_x: int,
    dark_lines: list[str],
    white_lines: list[str],
    pill: str,
    target_h: int,
) -> Path:
    logo = Image.open(LOGO).convert("RGBA")
    phone = Image.open(PHONE).convert("RGBA")
    person = Image.open(person_path).convert("RGBA")

    canvas = make_bg()
    ratio = target_h / person.height
    person_r = person.resize((int(person.width * ratio), target_h), Image.Resampling.LANCZOS)
    x = min(person_x, W - person_r.width + 20)
    y = H - person_r.height + 4
    sh_a = person_r.split()[-1].filter(ImageFilter.GaussianBlur(10))
    sh = Image.new("RGBA", person_r.size, (0, 0, 0, 28))
    sh.putalpha(sh_a)
    canvas.paste(sh, (x + 6, y + 8), sh)
    canvas.paste(person_r, (x, y), person_r)

    tw = int(W * 0.185)
    lr = logo.resize((tw, int(logo.height * tw / logo.width)), Image.Resampling.LANCZOS)
    canvas.paste(lr, (W - lr.width - 40, 30), lr)

    draw = ImageDraw.Draw(canvas)
    x0, y0 = 56, 118
    for line in dark_lines:
        size = 54
        font = fnt("Montserrat-ExtraBold.ttf", size)
        while draw.textlength(line, font=font) > 530 and size > 36:
            size -= 1
            font = fnt("Montserrat-ExtraBold.ttf", size)
        draw.text((x0, y0), line, font=font, fill=DARK)
        y0 = draw.textbbox((x0, y0), line, font=font)[3] + 2
    y0 += 26
    for line in white_lines:
        size = 46
        font = fnt("Montserrat-Bold.ttf", size)
        while draw.textlength(line, font=font) > 530 and size > 32:
            size -= 1
            font = fnt("Montserrat-Bold.ttf", size)
        draw.text((x0, y0), line, font=font, fill=WHITE)
        y0 = draw.textbbox((x0, y0), line, font=font)[3] + 2
    y0 += 32

    f_pill = fnt("Montserrat-SemiBold.ttf", 24)
    pad_x, pad_y = 28, 18
    twl = draw.textlength(pill, font=f_pill)
    bw = int(twl + pad_x * 2)
    bh = pad_y * 2 + 28
    draw.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=32, fill=PILL)
    draw.text((x0 + pad_x, y0 + pad_y - 2), pill, font=f_pill, fill=WHITE)

    icon = phone.resize((88, 88), Image.Resampling.LANCZOS)
    canvas.paste(icon, (46, 956), icon)
    draw.text((148, 946), "403", font=fnt("Montserrat-ExtraBold.ttf", 84), fill=WHITE)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / name
    canvas.convert("RGB").save(out, quality=95)
    return out


def main() -> int:
    if not LOGO.exists() or not PHONE.exists():
        raise SystemExit("Need logo_transparent.png and phone_icon.png in image/brand/")

    # runtime font proof
    proof = fnt("Montserrat-ExtraBold.ttf", 40)
    print("font_ok", proof.getname())

    paths = [
        build(
            "v5_1_unique.jpg",
            OUT / "cut_osi_clean.png",
            560,
            ["КАЖДЫЙ ПАЦИЕНТ –", "ЕДИНСТВЕННЫЙ"],
            ["ЗДОРОВЬЕ – БЕЗ", "ШАБЛОНОВ"],
            "Запишитесь – услышим вас",
            945,
        ),
        build(
            "v5_2_health.jpg",
            OUT / "cut_bat_clean.png",
            510,
            ["ВАШЕ ЗДОРОВЬЕ –", "НАША ГЛАВНАЯ ЦЕЛЬ"],
            ["25 ЛЕТ РЯДОМ –", "В МИНСКЕ С ВАМИ"],
            "3 филиала – 120+ врачей",
            900,
        ),
        build(
            "v5_3_hear.jpg",
            OUT / "cut_bat2_clean.png",
            560,
            ["МЫ СЛЫШИМ", "КАЖДОГО"],
            ["ПУТЬ К ЗДОРОВЬЮ –", "ВСЕГДА СВОЙ"],
            "Кравира – клиника рядом",
            945,
        ),
    ]
    for p in paths:
        print("saved", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
