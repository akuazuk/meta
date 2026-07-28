"""Сборка баннеров Кравира: прозрачный логотип + Montserrat + короткое тире.

Запуск из корня проекта:
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
LOGO_SRC = ROOT / "image" / "logo_1.PNG"

BG = (186, 221, 215)
DARK = (17, 86, 72)
WHITE = (255, 255, 255)
PILL = (74, 146, 133)
W = H = 1080

EB = "Montserrat-ExtraBold.ttf"
B = "Montserrat-Bold.ttf"
SB = "Montserrat-SemiBold.ttf"
MD = "Montserrat-Medium.ttf"


def make_transparent_logo(src: Path = LOGO_SRC) -> Image.Image:
    """Убирает чёрный фон у logo_1.PNG и сохраняет прозрачный PNG."""
    BRAND.mkdir(parents=True, exist_ok=True)
    img = Image.open(src).convert("RGBA")
    arr = np.array(img).astype(np.float32)
    rgb = arr[..., :3]
    luma = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    chroma = rgb.max(axis=2) - rgb.min(axis=2)
    alpha = np.clip((luma - 8) * (255 / 28), 0, 255)
    alpha = np.maximum(alpha, np.clip((chroma - 5) * (255 / 20), 0, 255)).astype(np.uint8)
    alpha = np.array(Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(0.6)))
    out = arr.copy()
    out[..., 3] = alpha
    logo = Image.fromarray(out.astype(np.uint8), "RGBA")
    bbox = logo.getbbox()
    if bbox:
        logo = logo.crop(bbox)
    logo.save(BRAND / "logo_transparent.png")
    logo.resize((logo.width * 2, logo.height * 2), Image.Resampling.LANCZOS).save(
        BRAND / "logo_transparent@2x.png"
    )
    return logo


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size=size)


def make_bg() -> Image.Image:
    base = Image.new("RGBA", (W, H), BG + (255,))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for x, y, r, a in [
        (840, 170, 95, 38),
        (960, 410, 72, 28),
        (780, 560, 58, 24),
        (1000, 700, 84, 22),
        (720, 110, 42, 20),
        (880, 860, 64, 18),
        (210, 910, 52, 16),
        (110, 210, 36, 14),
    ]:
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, a))
    return Image.alpha_composite(base, overlay)


def place_logo(canvas: Image.Image, logo: Image.Image) -> Image.Image:
    target_w = int(W * 0.20)
    ratio = target_w / logo.width
    lr = logo.resize((target_w, int(logo.height * ratio)), Image.Resampling.LANCZOS)
    lx = W - lr.width - int(W * 0.035)
    ly = int(H * 0.03)
    canvas.paste(lr, (lx, ly), lr)
    return canvas


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont, max_w: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_lines(draw, lines, x, y, fnt, fill, gap=3):
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y = draw.textbbox((x, y), line, font=fnt)[3] + gap
    return y


def draw_phone(draw: ImageDraw.ImageDraw) -> None:
    # Белая трубка в стиле референсов Кравира
    x, y = 52, 968
    draw.pieslice((x, y, x + 58, y + 58), 200, 340, fill=WHITE)
    draw.ellipse((x + 8, y + 18, x + 28, y + 38), fill=BG)
    draw.ellipse((x + 30, y + 18, x + 50, y + 38), fill=BG)
    draw.text((118, 948), "403", font=font(EB, 78), fill=WHITE)


def draw_pill(draw: ImageDraw.ImageDraw, text: str, x: int, y: int) -> None:
    f_title = font(SB, 24)
    parts = text.split("\n")
    pad_x, pad_y = 22, 14
    widths = [draw.textlength(p, font=f_title) for p in parts]
    box_w = int(max(widths) + pad_x * 2)
    box_h = pad_y * 2 + 30 * len(parts)
    draw.rounded_rectangle((x, y, x + box_w, y + box_h), radius=28, fill=PILL)
    cy = y + pad_y - 1
    for p in parts:
        draw.text((x + pad_x, cy), p, font=f_title, fill=WHITE)
        cy += 32


def build(
    name: str,
    headlines: list[tuple[str, tuple[int, int, int], int, str]],
    person: Image.Image,
    target_h: int,
    x_pos: int,
    pill_text: str,
    logo: Image.Image,
    text_max: int = 540,
) -> Path:
    canvas = make_bg()
    ratio = target_h / person.height
    person = person.resize((int(person.width * ratio), target_h), Image.Resampling.LANCZOS)
    alpha = person.split()[-1].filter(ImageFilter.GaussianBlur(10))
    shadow = Image.new("RGBA", person.size, (0, 0, 0, 45))
    shadow.putalpha(alpha)
    y_pos = H - person.height + 10
    canvas.paste(shadow, (x_pos + 6, y_pos + 8), shadow)
    canvas.paste(person, (x_pos, y_pos), person)
    canvas = place_logo(canvas, logo)
    draw = ImageDraw.Draw(canvas)
    y = 100
    for text, color, size, weight in headlines:
        fnt = font(weight, size)
        lines = wrap(draw, text, fnt, text_max)
        y = draw_lines(draw, lines, 52, y, fnt, color)
        y += 10
    draw_pill(draw, pill_text, 52, min(y + 6, 760))
    draw_phone(draw)
    OUT.mkdir(parents=True, exist_ok=True)
    jpg = OUT / name
    canvas.convert("RGB").save(jpg, quality=95)
    canvas.save(OUT / name.replace(".jpg", ".png"))
    return jpg


def main() -> int:
    logo = make_transparent_logo()
    osi = Image.open(OUT / "cut_osi.png").convert("RGBA")
    bat = Image.open(OUT / "cut_bat.png").convert("RGBA")
    bat2 = Image.open(OUT / "cut_bat2.png").convert("RGBA")

    paths = [
        build(
            "v4_1_unique.jpg",
            [
                ("КАЖДЫЙ ПАЦИЕНТ –", DARK, 52, EB),
                ("ЕДИНСТВЕННЫЙ", DARK, 52, EB),
                ("ЗДОРОВЬЕ – БЕЗ", WHITE, 44, B),
                ("ШАБЛОНОВ", WHITE, 44, B),
            ],
            osi,
            900,
            560,
            "Запишитесь – услышим вас",
            logo,
        ),
        build(
            "v4_2_health.jpg",
            [
                ("ВАШЕ ЗДОРОВЬЕ –", DARK, 48, EB),
                ("НАША ГЛАВНАЯ ЦЕЛЬ", DARK, 42, EB),
                ("25 ЛЕТ РЯДОМ –", WHITE, 40, B),
                ("В МИНСКЕ С ВАМИ", WHITE, 40, B),
            ],
            bat,
            860,
            500,
            "3 филиала – 120+ врачей",
            logo,
        ),
        build(
            "v4_3_hear.jpg",
            [
                ("МЫ СЛЫШИМ", DARK, 54, EB),
                ("КАЖДОГО", DARK, 54, EB),
                ("ПУТЬ К ЗДОРОВЬЮ –", WHITE, 34, B),
                ("ВСЕГДА СВОЙ", WHITE, 34, B),
            ],
            bat2,
            900,
            560,
            "Кравира – клиника рядом",
            logo,
        ),
    ]
    for p in paths:
        print(f"saved {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
