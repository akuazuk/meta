"""Build dedicated 1.91:1 Facebook Search creatives only."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from scripts.build_critical_format_rebuild import (
    CUTS, ENDOSCOPY, FONT_B, FONT_X, GREEN, LOGO, LUGOVSKAYA_CUT,
    MINT, PHONE, SEA, doctor, fit, logo,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "image" / "concepts" / "facebook_search_only_2026-08-12"
W, H = 1080, 566


def f(path: Path, size: int):
    return ImageFont.truetype(path, size)


def phone_chip(canvas: Image.Image):
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((38, 435, 335, 540), 25, fill=(*SEA, 255))
    icon = Image.open(PHONE).convert("RGBA")
    icon.thumbnail((68, 68), Image.Resampling.LANCZOS)
    canvas.alpha_composite(icon, (56, 453))
    draw.text((137, 442), "403", font=f(FONT_X, 76), fill="white")


def endoscopy(cut: Path, name: str, role: str):
    c = Image.new("RGBA", (W, H), (*MINT, 255))
    # Keep the brand mark in its own safe area. Facebook Search can crop a few
    # pixels at either side, so neither the logo nor the portrait touches it.
    logo(c, 120, (620, 14))
    doctor(c, cut, (655, 82, 1072, 566))
    d = ImageDraw.Draw(c)
    d.multiline_text((42, 42), "ФГДС /\nГАСТРОСКОПИЯ", font=f(FONT_X, 52), fill=GREEN, spacing=0)
    d.multiline_text((42, 180), "ВО ВТОРОЙ ПОЛОВИНЕ ДНЯ", font=fit("ВО ВТОРОЙ ПОЛОВИНЕ ДНЯ", 590, 34, 28), fill="white")
    d.text((42, 235), "ВСЕГО ЗА 86 РУБЛЕЙ", font=f(FONT_X, 36), fill=GREEN)
    d.rounded_rectangle((38, 295, 580, 385), 22, fill="white")
    d.multiline_text((58, 312), "НАПРАВЛЕНИЕ ТЕРАПЕВТА\nБЕСПЛАТНО", font=f(FONT_X, 25), fill=GREEN, spacing=0)
    short_name = name.replace("\n", " ")
    d.text((360, 447), short_name, font=fit(short_name, 300, 25, 20, False), fill=GREEN)
    d.text((360, 482), role, font=f(FONT_B, 21), fill=GREEN)
    phone_chip(c)
    return c.convert("RGB")


def lugovskaya():
    c = Image.new("RGBA", (W, H), (*MINT, 255))
    logo(c, 120, (620, 14))
    doctor(c, LUGOVSKAYA_CUT, (655, 85, 1072, 566))
    d = ImageDraw.Draw(c)
    d.multiline_text((42, 48), "ГОЛОС ПРОПАЛ БЕЗ\nПРЕДУПРЕЖДЕНИЯ?", font=f(FONT_X, 46), fill=GREEN, spacing=0)
    d.multiline_text((42, 182), "ПРИЧИНУ ЛУЧШЕ\nНЕ УГАДЫВАТЬ", font=f(FONT_X, 37), fill="white", spacing=0)
    d.text((42, 295), "ПРИЁМ ЛОР-ВРАЧА", font=f(FONT_X, 36), fill=GREEN)
    d.text((360, 438), "Луговская Татьяна", font=f(FONT_X, 27), fill="white")
    d.text((360, 474), "Евгеньевна", font=f(FONT_X, 27), fill="white")
    d.text((360, 512), "Врач высшей категории", font=f(FONT_B, 20), fill=GREEN)
    phone_chip(c)
    return c.convert("RGB")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "120250661689710770_search.jpg"
    lugovskaya().save(path, quality=95, subsampling=0)
    print(path)
    for ad_id, (filename, name, role) in ENDOSCOPY.items():
        path = OUT / f"{ad_id}_search.jpg"
        endoscopy(CUTS / filename, name, role).save(path, quality=95, subsampling=0)
        print(path)


if __name__ == "__main__":
    main()
