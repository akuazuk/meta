"""Баннеры Орловского в точной композиции серии Баценко/Луговская/Мытник.

Ключевые признаки серии: бирюзовый фон с мягким боке, логотип справа сверху,
крупные текстовые блоки без карточек и кнопок, большой врач справа/снизу,
полупрозрачная нижняя полоса и белый телефон 403.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "image" / "concepts" / "orlovski_laser"
FONTS = ROOT / "assets" / "fonts"
LOGO = ROOT / "image" / "brand" / "logo_transparent.png"
DOCTOR = ROOT / "tmp_refs" / "laser_orlovski" / "orlovski_portrait_imagegen_cut.png"
DOCTOR_FALLBACK = ROOT / "tmp_refs" / "laser_orlovski" / "orlovski_cut.png"
PHONE_REFERENCE = Path(
    "/Users/pavelkuzauka/Downloads/Telegram Desktop/Баценко_фимоз 1 к 1.png"
)

W = H = 1080
BG_TOP = (154, 210, 202)
BG_BOTTOM = (140, 194, 187)
DARK = (14, 99, 86)
WHITE = (255, 255, 255)

CONCEPTS = [
    {
        "slug": "1_hide",
        "headline": ["ПРЯЧЕТЕ", "ОБРАЗОВАНИЕ", "НА КОЖЕ?"],
        "headline_y": 128,
        "headline_size": 50,
        "headline_step": 56,
        "white": ["ПАПИЛЛОМЫ, ЛИПОМЫ,", "АТЕРОМЫ - ПОВОД", "ПОКАЗАТЬСЯ ХИРУРГУ"],
        "white_y": 310,
        "white_size": 31,
        "white_step": 38,
        "benefit": ["УДАЛЕНИЕ ЛАЗЕРОМ", "ПО ПОКАЗАНИЯМ"],
        "benefit_y": 438,
        "benefit_size": 35,
        "benefit_step": 42,
        "credentials_y": 550,
    },
    {
        "slug": "2_laser",
        "headline": ["БОИТЕСЬ", "УДАЛЕНИЯ?"],
        "headline_y": 142,
        "headline_size": 54,
        "headline_step": 62,
        "white": ["ЛАЗЕР - ТОЧНО,", "АККУРАТНО,", "ПО ПОКАЗАНИЯМ"],
        "white_y": 278,
        "white_size": 38,
        "white_step": 45,
        "benefit": ["НАЧНИТЕ С", "КОНСУЛЬТАЦИИ ХИРУРГА"],
        "benefit_y": 430,
        "benefit_size": 34,
        "benefit_step": 42,
        "credentials_y": 545,
    },
    {
        "slug": "3_once",
        "headline": ["ПАПИЛЛОМА ИЛИ", "ВРОСШИЙ НОГОТЬ", "МЕШАЮТ?"],
        "headline_y": 128,
        "headline_size": 43,
        "headline_step": 51,
        "white": ["НЕ ЖДИТЕ, ПОКА", "СТАНЕТ ХУЖЕ"],
        "white_y": 296,
        "white_size": 39,
        "white_step": 47,
        "benefit": ["РЕШЕНИЕ НАЧИНАЕТСЯ", "С ОСМОТРА"],
        "benefit_y": 405,
        "benefit_size": 34,
        "benefit_step": 42,
        "credentials_y": 520,
    },
]


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    result = ImageFont.truetype(str(FONTS / name), size)
    if "Montserrat" not in result.getname()[0]:
        raise RuntimeError(f"Expected Montserrat, got {result.getname()}")
    return result


def gradient_background(width: int = W, height: int = H) -> Image.Image:
    im = Image.new("RGB", (width, height))
    px = im.load()
    for y in range(height):
        t = y / (height - 1)
        color = tuple(round(a * (1 - t) + b * t) for a, b in zip(BG_TOP, BG_BOTTOM))
        for x in range(width):
            px[x, y] = color

    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for cx, cy, radius, alpha in [
        (170, 95, 64, 30),
        (130, 300, 42, 26),
        (190, 365, 37, 20),
        (500, 330, 44, 28),
        (435, 745, 40, 20),
        (115, 760, 43, 22),
    ]:
        gd.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            fill=(202, 238, 188, alpha),
        )
    return Image.alpha_composite(im.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(18)))


def draw_lines(draw: ImageDraw.ImageDraw, lines: list[str], y: int, size: int, step: int, fill):
    f = font("Montserrat-ExtraBold.ttf", size)
    for line in lines:
        draw.text((52, y), line, font=f, fill=fill)
        y += step


def add_logo(base: Image.Image, *, width: int = 250, top: int = 26) -> None:
    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.resize((width, round(logo.height * width / logo.width)), Image.Resampling.LANCZOS)
    base.alpha_composite(logo, (base.width - width - 26, top))


def add_credentials(draw: ImageDraw.ImageDraw, y: int, *, scale: float = 1.0) -> None:
    def scaled(value: int) -> int:
        return round(value * scale)

    draw.text((55, y), "Орловский Юрий Николаевич", font=font("Montserrat-Bold.ttf", scaled(25)), fill=WHITE)
    draw.text((55, y + scaled(34)), "Врач-хирург", font=font("Montserrat-Bold.ttf", scaled(21)), fill=DARK)
    draw.text((55, y + scaled(62)), "Высшая квалификационная категория", font=font("Montserrat-Bold.ttf", scaled(18)), fill=DARK)
    draw.text((55, y + scaled(87)), "Кандидат медицинских наук", font=font("Montserrat-Bold.ttf", scaled(18)), fill=DARK)
    draw.text((55, y + scaled(112)), "Стаж по специальности - с 2007 года", font=font("Montserrat-Bold.ttf", scaled(18)), fill=DARK)


def phone_icon() -> Image.Image:
    if PHONE_REFERENCE.exists():
        ref = Image.open(PHONE_REFERENCE).convert("RGB").crop((35, 900, 150, 1045))
        gray = ref.convert("L")
        alpha = gray.point(lambda v: max(0, min(255, (v - 175) * 4)))
        icon = Image.new("RGBA", ref.size, WHITE + (0,))
        icon.putalpha(alpha)
        return icon.resize((92, 116), Image.Resampling.LANCZOS)

    icon = Image.new("RGBA", (92, 116), (0, 0, 0, 0))
    d = ImageDraw.Draw(icon)
    d.arc((6, 5, 88, 105), 45, 225, fill=WHITE, width=17)
    return icon


def add_phone_band(
    base: Image.Image,
    *,
    y: int | None = None,
    height: int = 234,
    text_scale: float = 1.0,
) -> None:
    if y is None:
        y = base.height - height
    band = Image.new("RGBA", (base.width, height), DARK + (105,))
    base.alpha_composite(band, (0, y))
    icon_y = y + max(18, (height - 116) // 2)
    base.alpha_composite(phone_icon(), (42, icon_y))
    d = ImageDraw.Draw(base)
    phone_size = min(round(132 * text_scale), 160)
    number_y = y + max(4, (height - phone_size) // 2 - 11)
    d.text((154, number_y), "403", font=font("Montserrat-Bold.ttf", phone_size), fill=WHITE)


def add_doctor(
    base: Image.Image,
    *,
    target_w: int = 650,
    bottom_offset: int = -24,
    x_offset: int = 10,
) -> None:
    path = DOCTOR if DOCTOR.exists() else DOCTOR_FALLBACK
    doctor = Image.open(path).convert("RGBA")
    bbox = doctor.getbbox()
    if bbox:
        doctor = doctor.crop(bbox)
    doctor = doctor.resize(
        (target_w, round(doctor.height * target_w / doctor.width)), Image.Resampling.LANCZOS
    )
    x = base.width - target_w + x_offset
    y = base.height - doctor.height - bottom_offset
    base.alpha_composite(doctor, (x, y))


def build(concept: dict) -> Path:
    base = gradient_background()
    add_logo(base)
    draw = ImageDraw.Draw(base)
    draw_lines(
        draw,
        concept["headline"],
        concept["headline_y"],
        concept["headline_size"],
        concept["headline_step"],
        DARK,
    )
    draw_lines(
        draw,
        concept["white"],
        concept["white_y"],
        concept["white_size"],
        concept["white_step"],
        WHITE,
    )
    draw_lines(
        draw,
        concept["benefit"],
        concept["benefit_y"],
        concept["benefit_size"],
        concept["benefit_step"],
        DARK,
    )
    add_credentials(draw, concept["credentials_y"])
    add_phone_band(base)
    add_doctor(base)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"orlovski_{concept['slug']}_1x1.jpg"
    base.convert("RGB").save(out, quality=96, optimize=True, subsampling=0)
    print("saved", out)
    return out


def build_4x5(concept: dict) -> Path:
    """Версия для Facebook/Instagram Feed без автоматического кадрирования."""
    width, height = 1080, 1350
    text_scale = math.sqrt((width * height) / (W * H))
    base = gradient_background(width, height)
    add_logo(base)
    draw = ImageDraw.Draw(base)
    layout = {
        "1_hide": {"headline": 120, "white": 340, "benefit": 495},
        "2_laser": {"headline": 132, "white": 300, "benefit": 480},
        "3_once": {"headline": 118, "white": 330, "benefit": 460},
    }[concept["slug"]]
    draw_lines(
        draw,
        concept["headline"],
        layout["headline"],
        round(concept["headline_size"] * text_scale),
        round(concept["headline_step"] * text_scale),
        DARK,
    )
    draw_lines(
        draw,
        concept["white"],
        layout["white"],
        round(concept["white_size"] * text_scale),
        round(concept["white_step"] * text_scale),
        WHITE,
    )
    draw_lines(
        draw,
        concept["benefit"],
        layout["benefit"],
        round(concept["benefit_size"] * text_scale),
        round(concept["benefit_step"] * text_scale),
        DARK,
    )
    add_credentials(draw, 680, scale=text_scale)
    add_phone_band(base, y=1098, height=252, text_scale=text_scale)
    add_doctor(base, target_w=640, bottom_offset=-18)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"orlovski_{concept['slug']}_4x5_text_large_v2.jpg"
    base.convert("RGB").save(out, quality=96, optimize=True, subsampling=0)
    print("saved", out)
    return out


def build_9x16(concept: dict) -> Path:
    """Версия для Stories/Reels с ключевыми элементами внутри безопасной зоны."""
    width, height = 1080, 1920
    text_scale = math.sqrt((width * height) / (W * H))
    base = gradient_background(width, height)
    add_logo(base, width=270, top=72)
    draw = ImageDraw.Draw(base)

    vertical = {
        "1_hide": {"headline": 270, "white": 540, "benefit": 735, "credentials": 920},
        "2_laser": {"headline": 285, "white": 500, "benefit": 710, "credentials": 900},
        "3_once": {"headline": 270, "white": 520, "benefit": 690, "credentials": 870},
    }[concept["slug"]]
    draw_lines(
        draw,
        concept["headline"],
        vertical["headline"],
        round(concept["headline_size"] * text_scale),
        round(concept["headline_step"] * text_scale),
        DARK,
    )
    draw_lines(
        draw,
        concept["white"],
        vertical["white"],
        round(concept["white_size"] * text_scale),
        round(concept["white_step"] * text_scale),
        WHITE,
    )
    draw_lines(
        draw,
        concept["benefit"],
        vertical["benefit"],
        round(concept["benefit_size"] * text_scale),
        round(concept["benefit_step"] * text_scale),
        DARK,
    )
    add_credentials(draw, vertical["credentials"], scale=text_scale)

    # Полоса и номер подняты над нижними элементами интерфейса Stories/Reels.
    add_phone_band(base, y=1460, height=270, text_scale=text_scale)
    add_doctor(base, target_w=745, bottom_offset=-18, x_offset=120)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"orlovski_{concept['slug']}_9x16_text_large_v2.jpg"
    base.convert("RGB").save(out, quality=96, optimize=True, subsampling=0)
    print("saved", out)
    return out


def main() -> int:
    for concept in CONCEPTS:
        build(concept)
        build_4x5(concept)
        build_9x16(concept)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
