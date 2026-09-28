"""Build the first critical format-safe creative package.

Every layout is composed independently. No finished banner is cropped to make
another placement. The 9:16 phone band is kept above the Stories/Reels UI zone.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "image" / "concepts" / "critical_rebuild_2026-08-12"
CUTS = ROOT / "tmp_refs" / "creative_rebuild_2026-08-12" / "cutouts"
AUDIT = ROOT / "tmp_refs" / "active_search_audit_2026-08-12"
LOGO = ROOT / "image" / "brand" / "logo_transparent.png"
PHONE = ROOT / "tmp_refs" / "laser_orlovski" / "phone_icon_ok.png"
FONT_B = ROOT / "assets" / "fonts" / "Montserrat-Bold.ttf"
FONT_X = ROOT / "assets" / "fonts" / "Montserrat-ExtraBold.ttf"

MINT = (151, 207, 199)
GREEN = (0, 99, 87)
SEA = (45, 142, 130)

ENDOSCOPY = {
    "120250631220810770": ("yarovoy.png", "Яровой Иван\nЮрьевич", "Врач-эндоскопист"),
    "120250631218260770": ("bogdashich.png", "Богдашич Анатолий\nМихайлович", "Врач-эндоскопист"),
    "120250631222800770": ("kazak.png", "Казак Игорь\nМихайлович", "Врач-эндоскопист"),
}

SPRAVKI = {
    "120250631580830770": AUDIT / "all_120250631580830770_d6cc846a.jpg",
    "120250631548710770": AUDIT / "all_120250631548710770_975f804f.jpg",
    "120250631315520770": AUDIT / "all_120250631315520770_9c82d0e3.jpg",
}

LUGOVSKAYA_CUT = ROOT / "tmp_refs" / "all_format_fix" / "cutouts" / "lugovskaya_cut.png"


def f(path: Path, size: int):
    return ImageFont.truetype(path, size)


def fit(text: str, width: int, start: int, minimum: int, extra=True):
    path = FONT_X if extra else FONT_B
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for size in range(start, minimum - 1, -2):
        font = f(path, size)
        if probe.multiline_textbbox((0, 0), text, font=font, spacing=max(2, size // 14))[2] <= width:
            return font
    return f(path, minimum)


def bokeh(canvas: Image.Image, scale: float):
    layer = Image.new("RGBA", canvas.size)
    draw = ImageDraw.Draw(layer)
    for x, y, r in [(90, 780, 55), (170, 890, 42), (460, 800, 62), (540, 900, 40)]:
        draw.ellipse((x-r*scale, y-r*scale, x+r*scale, y+r*scale), fill=(210, 238, 218, 100))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(int(13 * scale))))


def logo(canvas: Image.Image, max_w: int, xy: tuple[int, int]):
    image = Image.open(LOGO).convert("RGBA")
    image.thumbnail((max_w, max_w), Image.Resampling.LANCZOS)
    canvas.alpha_composite(image, xy)


def doctor(canvas: Image.Image, cut: Path, box: tuple[int, int, int, int]):
    image = Image.open(cut).convert("RGBA")
    bbox = image.getbbox()
    image = image.crop(bbox)
    bw, bh = box[2] - box[0], box[3] - box[1]
    scale = min(bw / image.width, bh / image.height)
    image = image.resize((int(image.width * scale), int(image.height * scale)), Image.Resampling.LANCZOS)
    canvas.alpha_composite(image, (box[2] - image.width, box[3] - image.height))


def phone(canvas: Image.Image, y: int, h: int, size: int, left: int = 42):
    band = Image.new("RGBA", (canvas.width, h), (*SEA, 180))
    canvas.alpha_composite(band, (0, y))
    icon = Image.open(PHONE).convert("RGBA")
    icon.thumbnail((int(size * .72), int(size * .72)), Image.Resampling.LANCZOS)
    canvas.alpha_composite(icon, (left, y + (h - icon.height) // 2))
    ImageDraw.Draw(canvas).text((left + int(size * .92), y + (h-size)//2 - int(size*.08)), "403", font=f(FONT_X, size), fill="white")


def phone_compact(canvas: Image.Image, y: int, h: int, width: int, size: int):
    band = Image.new("RGBA", (width, h), (*SEA, 190))
    canvas.alpha_composite(band, (0, y))
    icon = Image.open(PHONE).convert("RGBA")
    icon.thumbnail((int(size * .65), int(size * .65)), Image.Resampling.LANCZOS)
    canvas.alpha_composite(icon, (38, y + (h-icon.height)//2))
    ImageDraw.Draw(canvas).text((135, y + (h-size)//2 - int(size*.08)), "403", font=f(FONT_X, size), fill="white")


def name_card(draw: ImageDraw.ImageDraw, xy: tuple[int, int], width: int, name: str, role: str, name_size: int, role_size: int):
    nf = fit(name, width - 38, name_size, name_size - 8)
    rf = fit(role, width - 38, role_size, role_size - 5, False)
    nb = draw.multiline_textbbox((0, 0), name, font=nf, spacing=2)
    rb = draw.multiline_textbbox((0, 0), role, font=rf, spacing=1)
    height = nb[3] + rb[3] + 36
    x, y = xy
    draw.rounded_rectangle((x, y, x+width, y+height), 28, fill=(77, 173, 159, 235))
    draw.multiline_text((x+19, y+12), name, font=nf, fill="white", spacing=2)
    draw.multiline_text((x+19, y+20+nb[3]), role, font=rf, fill=GREEN, spacing=1)


def endoscopy_square(cut: Path, name: str, role: str):
    c = Image.new("RGBA", (1080, 1080), (*MINT, 255)); bokeh(c, 1); logo(c, 210, (835, 18))
    doctor(c, cut, (500, 370, 1080, 1080)); d = ImageDraw.Draw(c)
    d.multiline_text((48, 72), "ФГДС /\nГАСТРОСКОПИЯ", font=f(FONT_X, 60), fill=GREEN, spacing=2)
    d.multiline_text((48, 230), "ВО ВТОРОЙ\nПОЛОВИНЕ ДНЯ", font=f(FONT_X, 44), fill="white", spacing=2)
    d.multiline_text((48, 350), "ВСЕГО ЗА\n86 РУБЛЕЙ", font=f(FONT_X, 48), fill=GREEN, spacing=2)
    d.rounded_rectangle((40, 490, 535, 625), 28, fill="white")
    d.multiline_text((65, 512), "НАПРАВЛЕНИЕ ТЕРАПЕВТА\nБЕСПЛАТНО", font=f(FONT_X, 31), fill=GREEN, spacing=1)
    name_card(d, (40, 665), 510, name, role, 37, 27)
    phone(c, 895, 185, 120)
    return c.convert("RGB")


def endoscopy_feed(cut: Path, name: str, role: str):
    c = Image.new("RGBA", (1080, 1350), (*MINT, 255)); bokeh(c, 1); logo(c, 220, (825, 22))
    doctor(c, cut, (465, 430, 1080, 1350)); d = ImageDraw.Draw(c)
    d.multiline_text((50, 90), "ФГДС /\nГАСТРОСКОПИЯ", font=f(FONT_X, 70), fill=GREEN, spacing=3)
    d.multiline_text((50, 280), "ВО ВТОРОЙ\nПОЛОВИНЕ ДНЯ", font=f(FONT_X, 52), fill="white", spacing=3)
    d.multiline_text((50, 425), "ВСЕГО ЗА\n86 РУБЛЕЙ", font=f(FONT_X, 58), fill=GREEN, spacing=2)
    d.rounded_rectangle((42, 590, 565, 750), 30, fill="white")
    d.multiline_text((68, 618), "НАПРАВЛЕНИЕ ТЕРАПЕВТА\nБЕСПЛАТНО", font=f(FONT_X, 34), fill=GREEN, spacing=2)
    name_card(d, (42, 800), 525, name, role, 40, 29)
    phone(c, 1115, 205, 132)
    return c.convert("RGB")


def endoscopy_vertical(cut: Path, name: str, role: str):
    c = Image.new("RGBA", (1080, 1920), (*MINT, 255)); bokeh(c, 1); logo(c, 235, (805, 25))
    doctor(c, cut, (400, 690, 1080, 1920)); d = ImageDraw.Draw(c)
    d.multiline_text((58, 240), "ФГДС /\nГАСТРОСКОПИЯ", font=f(FONT_X, 76), fill=GREEN, spacing=4)
    d.multiline_text((58, 450), "ВО ВТОРОЙ\nПОЛОВИНЕ ДНЯ", font=f(FONT_X, 58), fill="white", spacing=3)
    d.multiline_text((58, 612), "ВСЕГО ЗА\n86 РУБЛЕЙ", font=f(FONT_X, 64), fill=GREEN, spacing=3)
    d.rounded_rectangle((50, 800, 590, 975), 34, fill="white")
    d.multiline_text((78, 830), "НАПРАВЛЕНИЕ ТЕРАПЕВТА\nБЕСПЛАТНО", font=f(FONT_X, 37), fill=GREEN, spacing=2)
    name_card(d, (50, 1025), 540, name, role, 42, 31)
    # Bottom 340 px stay free of critical content; the band ends at 1520.
    phone(c, 1300, 220, 142)
    return c.convert("RGB")


def build_spravki_feed(source: Path):
    src = Image.open(source).convert("RGB")
    canvas = Image.new("RGB", (1080, 1350), src.getpixel((20, 20)))
    src.thumbnail((1012, 1350), Image.Resampling.LANCZOS)
    canvas.paste(src, ((1080-src.width)//2, 0))
    return canvas


def build_spravki_vertical(source: Path):
    src = Image.open(source).convert("RGB")
    bg = src.getpixel((20, 20))
    canvas = Image.new("RGB", (1080, 1920), bg)
    # Preserve the original 1080x1440 artwork at native scale. This keeps its
    # typography large and places its phone band above the lower UI zone.
    canvas.paste(src, (0, 70))
    return canvas


def lugovskaya(size: tuple[int, int], copy: dict):
    w, h = size
    c = Image.new("RGBA", size, (*MINT, 255)); bokeh(c, 1); logo(c, 225, (w-255, 24))
    d = ImageDraw.Draw(c)
    if h == 1350:
        doctor(c, LUGOVSKAYA_CUT, (455, 390, w, h))
        d.multiline_text((48, 105), copy["headline"], font=fit(copy["headline"], 720, 68, 54), fill=GREEN, spacing=3)
        d.multiline_text((48, 300), copy["subhead"], font=fit(copy["subhead"], 570, 50, 40), fill="white", spacing=3)
        d.text((48, 465), "ПРИЁМ ЛОР-ВРАЧА", font=f(FONT_X, 44), fill=GREEN)
        name_card(d, (42, 720), 535, "Луговская Татьяна\nЕвгеньевна", "Врач-оториноларинголог\nвысшей категории", 40, 25)
        phone(c, 1115, 205, 132)
    else:
        doctor(c, LUGOVSKAYA_CUT, (535, 790, w, h))
        d.multiline_text((58, 245), copy["headline"], font=fit(copy["headline"], 760, 78, 62), fill=GREEN, spacing=4)
        d.multiline_text((58, 480), copy["subhead"], font=fit(copy["subhead"], 650, 58, 46), fill="white", spacing=4)
        d.text((58, 690), "ПРИЁМ ЛОР-ВРАЧА", font=f(FONT_X, 50), fill=GREEN)
        name_card(d, (50, 980), 560, "Луговская Татьяна\nЕвгеньевна", "Врач-оториноларинголог\nвысшей категории", 43, 27)
        # Compact left band leaves the doctor's face unobstructed and stays
        # above the bottom Stories/Reels controls.
        phone_compact(c, 1330, 210, 540, 136)
    return c.convert("RGB")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for ad_id, (filename, name, role) in ENDOSCOPY.items():
        cut = CUTS / filename
        for suffix, image in {
            "1x1": endoscopy_square(cut, name, role),
            "4x5": endoscopy_feed(cut, name, role),
            "9x16": endoscopy_vertical(cut, name, role),
        }.items():
            path = OUT / f"{ad_id}_{suffix}.jpg"
            image.save(path, quality=95, subsampling=0)
            print(path)
    for ad_id, source in SPRAVKI.items():
        for suffix, image in {
            "4x5": build_spravki_feed(source),
            "9x16": build_spravki_vertical(source),
        }.items():
            path = OUT / f"{ad_id}_{suffix}.jpg"
            image.save(path, quality=95, subsampling=0)
            print(path)
    lug_copy = {
        "headline": "ГОЛОС ПРОПАЛ БЕЗ\nПРЕДУПРЕЖДЕНИЯ?",
        "subhead": "ПРИЧИНУ ЛУЧШЕ\nНЕ УГАДЫВАТЬ",
    }
    for suffix, image in {
        "4x5": lugovskaya((1080, 1350), lug_copy),
        "9x16": lugovskaya((1080, 1920), lug_copy),
    }.items():
        path = OUT / f"120250661689710770_{suffix}.jpg"
        image.save(path, quality=95, subsampling=0)
        print(path)


if __name__ == "__main__":
    main()
