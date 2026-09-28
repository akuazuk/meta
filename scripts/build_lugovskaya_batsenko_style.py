"""Build two Lugovskaya squares using the exact recent Batsenko template."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "image" / "concepts" / "all_format_fix"
CUT = ROOT / "tmp_refs" / "all_format_fix" / "cutouts" / "lugovskaya_cut.png"
LOGO = ROOT / "image" / "brand" / "logo_transparent.png"
PHONE = ROOT / "tmp_refs" / "laser_orlovski" / "phone_icon_ok.png"
FONT_B = ROOT / "assets" / "fonts" / "Montserrat-Bold.ttf"
FONT_X = ROOT / "assets" / "fonts" / "Montserrat-ExtraBold.ttf"

MINT = (151, 207, 199)
GREEN = (0, 99, 87)
SEA = (45, 142, 130)
NAME = "Луговская Татьяна\nЕвгеньевна"
ROLE = "Врач-оториноларинголог\nвысшей категории"

VARIANTS = {
    "120250487253590770": {
        "headline": "ТЕЛЕВИЗОР СТАЛ ГРОМЧЕ,\nЧЕМ РАЗГОВОРЫ?",
        "subhead": "ПРОВЕРЬТЕ СЛУХ",
        "cta": "ПРИЁМ ЛОР-ВРАЧА",
    },
    "120250487246110770": {
        "headline": "ГОЛОС ПРОПАЛ БЕЗ\nПРЕДУПРЕЖДЕНИЯ?",
        "subhead": "ПРИЧИНУ ЛУЧШЕ\nНЕ УГАДЫВАТЬ",
        "cta": "ПРИЁМ ЛОР-ВРАЧА",
    },
}


def font(path: Path, size: int):
    return ImageFont.truetype(path, size)


def fit(text: str, width: int, start: int, minimum: int, extra=True):
    path = FONT_X if extra else FONT_B
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for size in range(start, minimum - 1, -2):
        candidate = font(path, size)
        if probe.multiline_textbbox((0, 0), text, font=candidate, spacing=int(size*.08))[2] <= width:
            return candidate
    return font(path, minimum)


def paste_logo(canvas: Image.Image):
    logo = Image.open(LOGO).convert("RGBA")
    logo.thumbnail((230, 220), Image.Resampling.LANCZOS)
    canvas.alpha_composite(logo, (815, 20))


def paste_doctor(canvas: Image.Image):
    doctor = Image.open(CUT).convert("RGBA")
    box = (445, 300, 1080, 1080)
    scale = min((box[2]-box[0])/doctor.width, (box[3]-box[1])/doctor.height)
    doctor = doctor.resize((int(doctor.width*scale), int(doctor.height*scale)), Image.Resampling.LANCZOS)
    canvas.alpha_composite(doctor, (box[2]-doctor.width, box[3]-doctor.height))


def add_bokeh(canvas: Image.Image):
    glow = Image.new("RGBA", canvas.size)
    draw = ImageDraw.Draw(glow)
    for x, y, r in [(85, 790, 48), (155, 875, 38), (470, 785, 55), (535, 870, 35)]:
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(205, 235, 213, 105))
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(12)))


def name_card(draw: ImageDraw.ImageDraw):
    x, y, width = 36, 660, 535
    name_font = fit(NAME, width-40, 38, 28)
    role_font = fit(ROLE, width-40, 29, 23, False)
    nb = draw.multiline_textbbox((0, 0), NAME, font=name_font, spacing=2)
    rb = draw.multiline_textbbox((0, 0), ROLE, font=role_font, spacing=2)
    height = nb[3] + rb[3] + 34
    draw.rounded_rectangle((x, y, x+width, y+height), 34, fill=(77, 173, 159, 235))
    draw.multiline_text((x+20, y+14), NAME, font=name_font, fill="white", spacing=2)
    draw.multiline_text((x+20, y+18+nb[3]), ROLE, font=role_font, fill=GREEN, spacing=2)


def phone_band(canvas: Image.Image):
    y, height = 885, 195
    canvas.alpha_composite(Image.new("RGBA", (1080, height), (*SEA, 165)), (0, y))
    icon = Image.open(PHONE).convert("RGBA")
    icon.thumbnail((105, 105), Image.Resampling.LANCZOS)
    canvas.alpha_composite(icon, (38, y+(height-icon.height)//2))
    draw = ImageDraw.Draw(canvas)
    draw.text((173, y+20), "403", font=font(FONT_X, 132), fill="white")


def build(copy: dict) -> Image.Image:
    canvas = Image.new("RGBA", (1080, 1080), (*MINT, 255))
    add_bokeh(canvas)
    paste_logo(canvas)
    paste_doctor(canvas)
    draw = ImageDraw.Draw(canvas)
    h = fit(copy["headline"], 720, 58, 42)
    s = fit(copy["subhead"], 555, 42, 32)
    c = fit(copy["cta"], 500, 44, 34)
    draw.multiline_text((42, 85), copy["headline"], font=h, fill=GREEN, spacing=3)
    hb = draw.multiline_textbbox((42, 85), copy["headline"], font=h, spacing=3)
    draw.multiline_text((42, hb[3]+22), copy["subhead"], font=s, fill="white", spacing=3)
    sb = draw.multiline_textbbox((42, hb[3]+22), copy["subhead"], font=s, spacing=3)
    draw.multiline_text((42, sb[3]+24), copy["cta"], font=c, fill=GREEN, spacing=3)
    name_card(draw)
    phone_band(canvas)
    return canvas.convert("RGB")


def main():
    for source_id, copy in VARIANTS.items():
        image = build(copy)
        canonical = OUT / f"{source_id}_square.jpg"
        versioned = OUT / f"{source_id}_square_batsenko_style_v3.jpg"
        image.save(canonical, quality=95, subsampling=0)
        image.save(versioned, quality=95, subsampling=0)
        print(versioned)


if __name__ == "__main__":
    main()
