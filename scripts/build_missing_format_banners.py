"""Rebuild placement-safe variants for creatives that only had one aspect ratio."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from rembg import remove


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tmp_refs" / "all_format_fix" / "design_sources"
STATE_CUTS = ROOT / "tmp_refs" / "all_format_fix" / "cutouts"
OUT = ROOT / "image" / "concepts" / "all_format_fix"
FONT = ROOT / "assets" / "fonts" / "Montserrat-Bold.ttf"
FONT_X = ROOT / "assets" / "fonts" / "Montserrat-ExtraBold.ttf"
LOGO = ROOT / "image" / "brand" / "logo_transparent.png"
PHONE = ROOT / "tmp_refs" / "laser_orlovski" / "phone_icon_ok.png"

MINT = (151, 207, 199)
GREEN = (0, 99, 87)
SEA = (66, 158, 147)
YELLOW = (255, 229, 160)


CONFIGS = {
    "120250487253590770": dict(
        source="120250487253590770_1_1080x1920.jpg", crop=(210, 735, 1080, 1540),
        cut="lugovskaya_cut.png",
        square_box=(330, 300, 1080, 1080),
        headline="ТЕЛЕВИЗОР СТАЛ ГРОМЧЕ,\nЧЕМ РАЗГОВОРЫ?", sub="ПРОВЕРЬТЕ СЛУХ",
        name="Луговская Татьяна Евгеньевна", role="Врач-оториноларинголог\nвысшей категории", formats=("square",),
    ),
    "120250487246110770": dict(
        source="120250487246110770_1_1080x1920.jpg", crop=(210, 735, 1080, 1540),
        cut="lugovskaya_cut.png",
        square_box=(330, 300, 1080, 1080),
        headline="ГОЛОС ПРОПАЛ БЕЗ\nПРЕДУПРЕЖДЕНИЯ?", sub="ПРИЧИНУ ЛУЧШЕ\nНЕ УГАДЫВАТЬ",
        name="Луговская Татьяна Евгеньевна", role="Врач-оториноларинголог\nвысшей категории", formats=("square",),
    ),
    "120250487601200770": dict(
        source="120250487601200770_1_1080x1920.jpg", crop=(440, 650, 1080, 1510),
        headline="НЕЛОВКО СМЕЯТЬСЯ\nИ ЧИХАТЬ?", sub="FEMILIFT ПОМОГАЕТ\nПРИ НЕДЕРЖАНИИ\nПОСЛЕ РОДОВ",
        name="Добровольская Марина Томовна", role="Врач-акушер-гинеколог\nвысшей категории", formats=("square",),
    ),
    "120250486829330770": dict(
        source="120250486829330770_1_1080x1920.jpg", crop=(410, 650, 1080, 1570),
        headline="МЕНОПАУЗА ИЗМЕНИЛА\nОЩУЩЕНИЕ КОМФОРТА?", sub="FEMILIFT - СОВРЕМЕННАЯ\nПРОЦЕДУРА ПРИ СУХОСТИ\nИ ИНТИМНОМ ДИСКОМФОРТЕ",
        name="Гринец Людмила Васильевна", role="Врач-акушер-гинеколог", price="249 РУБ", formats=("square",),
    ),
    "120250486844340770": dict(
        source="120250486844340770_1_1284x799.jpg", crop=(470, 10, 1284, 799),
        headline="ИНТИМНЫЙ ДИСКОМФОРТ\nНЕ НУЖНО ТЕРПЕТЬ", sub="FEMILIFT ПОМОГАЕТ ПРИ\nСУХОСТИ И ЛЁГКОМ\nНЕДЕРЖАНИИ МОЧИ",
        price="249 РУБ", formats=("square", "vertical"),
    ),
    "120250486834710770": dict(
        source="120250486834710770_1_1284x799.jpg", crop=(650, 10, 1230, 799),
        headline="СУХОСТЬ И ДИСКОМФОРТ\nВ ИНТИМНОЙ ЗОНЕ?", sub="FEMILIFT УЛУЧШИТ\nКАЧЕСТВО ИНТИМНОЙ ЖИЗНИ\nВ ПЕРИОД МЕНОПАУЗЫ",
        price="249 РУБ", formats=("square", "vertical"),
    ),
    "120250486838780770": dict(
        source="120250486838780770_1_1284x799.jpg", crop=(650, 0, 1284, 799),
        headline="ИНТИМНОЕ ОМОЛОЖЕНИЕ", sub="ПРИ СУХОСТИ И ЛЁГКОМ\nНЕДЕРЖАНИИ МОЧИ\n\nПОЗАБОТЬТЕСЬ О СЕБЕ\nДЕЛИКАТНО",
        price="249 РУБ", formats=("square", "vertical"),
    ),
    "120250486759170770": dict(
        source="120250486759170770_1_1080x1920.jpg", crop=(0, 610, 670, 1920),
        headline="ЕЖЕГОДНАЯ СПРАВКА\nДОШКОЛЬНИКА", sub="ЗА 1 ДЕНЬ", price="157,03 РУБЛЕЙ",
        theme="school", formats=("square",),
    ),
    "120250486709060770": dict(
        source="120250486709060770_1_1080x1440.jpg", crop=(0, 470, 760, 1230),
        headline="ЕЖЕГОДНАЯ СПРАВКА\nШКОЛЬНИКА", sub="ЗА 1 ДЕНЬ", price="222,44 РУБЛЕЙ",
        theme="school", formats=("square", "vertical"),
    ),
}


def fit_font(text: str, max_width: int, start: int, minimum: int = 30, extra: bool = False):
    path = FONT_X if extra else FONT
    for size in range(start, minimum - 1, -2):
        font = ImageFont.truetype(path, size)
        box = ImageDraw.Draw(Image.new("RGB", (1, 1))).multiline_textbbox((0, 0), text, font=font, spacing=int(size * .08))
        if box[2] <= max_width:
            return font
    return ImageFont.truetype(path, minimum)


def subject(config: dict) -> Image.Image:
    if config.get("cut"):
        return Image.open(STATE_CUTS / config["cut"]).convert("RGBA")
    image = Image.open(SRC / config["source"]).convert("RGB").crop(config["crop"])
    return remove(image, alpha_matting=False)


def paste_fit(canvas: Image.Image, layer: Image.Image, box: tuple[int, int, int, int], anchor="bottom-right"):
    x0, y0, x1, y1 = box
    scale = min((x1 - x0) / layer.width, (y1 - y0) / layer.height)
    layer = layer.resize((int(layer.width * scale), int(layer.height * scale)), Image.Resampling.LANCZOS)
    x = x1 - layer.width if "right" in anchor else x0
    y = y1 - layer.height if "bottom" in anchor else y0
    canvas.alpha_composite(layer, (x, y))


def add_bokeh(canvas: Image.Image):
    glow = Image.new("RGBA", canvas.size)
    d = ImageDraw.Draw(glow)
    for x, y, r in [(85, 850, 48), (145, 935, 42), (475, 810, 58), (525, 925, 36)]:
        d.ellipse((x-r, y-r, x+r, y+r), fill=(199, 232, 208, 100))
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(12)))


def add_logo(canvas: Image.Image, vertical: bool):
    logo = Image.open(LOGO).convert("RGBA")
    width = 315 if vertical else 250
    logo.thumbnail((width, 380), Image.Resampling.LANCZOS)
    canvas.alpha_composite(logo, (canvas.width - logo.width - 35, 35))


def add_phone_background(canvas: Image.Image, vertical: bool):
    h = 230 if vertical else 190
    y = canvas.height - h
    overlay = Image.new("RGBA", (canvas.width, h), (24, 117, 105, 155))
    canvas.alpha_composite(overlay, (0, y))


def add_phone_foreground(canvas: Image.Image, vertical: bool):
    h = 230 if vertical else 190
    y = canvas.height - h
    icon = Image.open(PHONE).convert("RGBA")
    icon.thumbnail((135 if vertical else 105, 135 if vertical else 105), Image.Resampling.LANCZOS)
    canvas.alpha_composite(icon, (35, y + (h-icon.height)//2))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT_X, 165 if vertical else 132)
    draw.text((190 if vertical else 160, y + (h-font.size)//2 - 8), "403", font=font, fill="white")


def add_phone(canvas: Image.Image, vertical: bool):
    add_phone_background(canvas, vertical)
    add_phone_foreground(canvas, vertical)


def doctor_banner(config: dict, fmt: str) -> Image.Image:
    vertical = fmt == "vertical"
    size = (1080, 1920) if vertical else (1080, 1080)
    canvas = Image.new("RGBA", size, MINT + (255,))
    add_bokeh(canvas)
    add_logo(canvas, vertical)
    if vertical:
        cut = subject(config)
        paste_fit(canvas, cut, (400, 760, 1080, 1900))
        x, y, width = 52, 360, 920
        h_font = fit_font(config["headline"], width, 69, 48, True)
        s_font = fit_font(config["sub"], 650, 57, 38, True)
    else:
        x, y, width = 42, 85, 720
        h_font = fit_font(config["headline"], width, 64, 44, True)
        s_font = fit_font(config["sub"], 630, 52, 34, True)
    draw = ImageDraw.Draw(canvas)
    draw.multiline_text((x, y), config["headline"], font=h_font, fill=GREEN, spacing=int(h_font.size*.08))
    hb = draw.multiline_textbbox((x, y), config["headline"], font=h_font, spacing=int(h_font.size*.08))
    sy = hb[3] + 25
    draw.multiline_text((x, sy), config["sub"], font=s_font, fill="white", spacing=int(s_font.size*.08))
    sb = draw.multiline_textbbox((x, sy), config["sub"], font=s_font, spacing=int(s_font.size*.08))
    if config.get("price"):
        pf = ImageFont.truetype(FONT_X, 70 if vertical else 55)
        pb = draw.textbbox((0, 0), config["price"], font=pf)
        px, py = x, min(sb[3] + 30, size[1] - (640 if vertical else 310))
        draw.rounded_rectangle((px-15, py-10, px+pb[2]+20, py+pb[3]+18), 14, fill="white")
        draw.text((px, py), config["price"], font=pf, fill=GREEN)
    if not vertical:
        # The reference squares use a large portrait in front of the phone band,
        # not a small head hidden underneath a translucent rectangle.
        add_phone_background(canvas, False)
        paste_fit(canvas, subject(config), config.get("square_box", (430, 390, 1080, 1080)))
        if config.get("name"):
            nf = fit_font(config["name"], 540, 38, 28, True)
            rf = fit_font(config["role"], 510, 31, 23)
            ny = 670
            draw = ImageDraw.Draw(canvas)
            draw.multiline_text((42, ny), config["name"], font=nf, fill="white", spacing=2)
            name_box = draw.multiline_textbbox((42, ny), config["name"], font=nf, spacing=2)
            draw.multiline_text((42, name_box[3]+8), config["role"], font=rf, fill=GREEN, spacing=3)
        add_phone_foreground(canvas, False)
    else:
        add_phone(canvas, True)
    return canvas.convert("RGB")


def school_banner(config: dict, fmt: str) -> Image.Image:
    vertical = fmt == "vertical"
    size = (1080, 1920) if vertical else (1080, 1080)
    canvas = Image.new("RGBA", size, YELLOW + (255,))
    add_logo(canvas, vertical)
    cut = subject(config)
    if vertical:
        paste_fit(canvas, cut, (0, 600, 720, 1900), anchor="bottom-left")
        badge_y, font_size = 355, 64
    else:
        paste_fit(canvas, cut, (0, 345, 650, 1080), anchor="bottom-left")
        badge_y, font_size = 225, 46
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((45, badge_y, size[0]-45, badge_y+(220 if vertical else 145)), 45, fill=SEA)
    hf = fit_font(config["headline"], size[0]-130, font_size, 34, True)
    box = draw.multiline_textbbox((0,0), config["headline"], font=hf, align="center", spacing=0)
    draw.multiline_text(((size[0]-box[2])/2, badge_y+20), config["headline"], font=hf, fill="white", align="center", spacing=0)
    sf = ImageFont.truetype(FONT_X, 78 if vertical else 56)
    draw.text((560 if vertical else 650, 760 if vertical else 480), config["sub"], font=sf, fill=GREEN)
    pf = fit_font(config["price"], 420 if vertical else 380, 68 if vertical else 48, 34, True)
    px, py = (590, 970) if vertical else (650, 620)
    pb = draw.textbbox((0,0), config["price"], font=pf)
    draw.rounded_rectangle((px-20,py-15,px+pb[2]+20,py+pb[3]+20), 25, fill="white")
    draw.text((px,py), config["price"], font=pf, fill=SEA)
    add_phone(canvas, vertical)
    return canvas.convert("RGB")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for ad_id, config in CONFIGS.items():
        for fmt in config["formats"]:
            image = school_banner(config, fmt) if config.get("theme") == "school" else doctor_banner(config, fmt)
            path = OUT / f"{ad_id}_{fmt}.jpg"
            image.save(path, quality=94, subsampling=0)
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
