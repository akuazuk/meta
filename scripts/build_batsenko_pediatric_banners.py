"""Build 1:1, 4:5 and 9:16 Batsenko pediatric-urology banners."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "image" / "concepts" / "batsenko_pediatric"
CUT = ROOT / "tmp_refs" / "batsenko_pediatric" / "batsenko_cut.png"
LOGO = ROOT / "image" / "brand" / "logo_transparent.png"
PHONE = ROOT / "tmp_refs" / "laser_orlovski" / "phone_icon_ok.png"
FONT_B = ROOT / "assets" / "fonts" / "Montserrat-Bold.ttf"
FONT_X = ROOT / "assets" / "fonts" / "Montserrat-ExtraBold.ttf"

MINT = (151, 207, 199)
GREEN = (0, 99, 87)
SEA = (45, 142, 130)
HEADLINE = "РЕБЁНОК БОИТСЯ\nСКАЗАТЬ, ЧТО БОЛИТ?"
SUBHEAD = "ФИМОЗ, ПОКРАСНЕНИЕ\nИ ВОСПАЛЕНИЕ -\nНЕ НУЖНО ЖДАТЬ"
CTA = "ПРИЁМ ДЕТЕЙ\nУ УРОЛОГА"
NAME = "Баценко Александр\nОлегович"
ROLE = "Врач-уролог-андролог\nвысшей категории"


def font(path: Path, size: int):
    return ImageFont.truetype(path, size)


def fit_font(text: str, max_width: int, start: int, minimum: int, extra=True):
    path = FONT_X if extra else FONT_B
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for size in range(start, minimum - 1, -2):
        candidate = font(path, size)
        if probe.multiline_textbbox((0, 0), text, font=candidate, spacing=int(size * .08))[2] <= max_width:
            return candidate
    return font(path, minimum)


def bokeh(canvas: Image.Image, scale: float):
    layer = Image.new("RGBA", canvas.size)
    draw = ImageDraw.Draw(layer)
    for x, y, r in [(100, 790, 48), (165, 880, 35), (480, 760, 55), (540, 865, 35)]:
        x, y, r = int(x * scale), int(y * scale), int(r * scale)
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(205, 235, 213, 105))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(max(8, int(12 * scale)))))


def paste_logo(canvas: Image.Image, width: int, x: int, y: int):
    logo = Image.open(LOGO).convert("RGBA")
    logo.thumbnail((width, int(width * .95)), Image.Resampling.LANCZOS)
    canvas.alpha_composite(logo, (x, y))


def paste_doctor(canvas: Image.Image, box: tuple[int, int, int, int]):
    doctor = Image.open(CUT).convert("RGBA")
    x0, y0, x1, y1 = box
    scale = min((x1-x0) / doctor.width, (y1-y0) / doctor.height)
    doctor = doctor.resize((int(doctor.width*scale), int(doctor.height*scale)), Image.Resampling.LANCZOS)
    canvas.alpha_composite(doctor, (x1-doctor.width, y1-doctor.height))


def phone_band(canvas: Image.Image, y: int, height: int, number_size: int, icon_size: int):
    canvas.alpha_composite(Image.new("RGBA", (canvas.width, height), (*SEA, 165)), (0, y))
    icon = Image.open(PHONE).convert("RGBA")
    icon.thumbnail((icon_size, icon_size), Image.Resampling.LANCZOS)
    canvas.alpha_composite(icon, (38, y + (height-icon.height)//2))
    draw = ImageDraw.Draw(canvas)
    number = font(FONT_X, number_size)
    draw.text((38 + icon_size + 30, y + (height-number_size)//2 - 10), "403", font=number, fill="white")


def name_card(draw: ImageDraw.ImageDraw, x: int, y: int, width: int, name_size: int, role_size: int):
    name_font = fit_font(NAME, width - 40, name_size, max(24, name_size-14))
    role_font = fit_font(ROLE, width - 40, role_size, max(20, role_size-10), False)
    name_box = draw.multiline_textbbox((0, 0), NAME, font=name_font, spacing=2)
    role_box = draw.multiline_textbbox((0, 0), ROLE, font=role_font, spacing=2)
    height = name_box[3] + role_box[3] + 34
    draw.rounded_rectangle((x, y, x+width, y+height), 34, fill=(77, 173, 159, 235))
    draw.multiline_text((x+20, y+14), NAME, font=name_font, fill="white", spacing=2)
    draw.multiline_text((x+20, y+18+name_box[3]), ROLE, font=role_font, fill=GREEN, spacing=2)


def build_square():
    canvas = Image.new("RGBA", (1080, 1080), (*MINT, 255))
    bokeh(canvas, 1)
    paste_logo(canvas, 230, 815, 20)
    paste_doctor(canvas, (500, 280, 1080, 1080))
    draw = ImageDraw.Draw(canvas)
    h = fit_font(HEADLINE, 690, 58, 42)
    s = fit_font(SUBHEAD, 555, 42, 30)
    c = fit_font(CTA, 490, 44, 32)
    draw.multiline_text((42, 85), HEADLINE, font=h, fill=GREEN, spacing=3)
    hb = draw.multiline_textbbox((42, 85), HEADLINE, font=h, spacing=3)
    draw.multiline_text((42, hb[3]+22), SUBHEAD, font=s, fill="white", spacing=3)
    sb = draw.multiline_textbbox((42, hb[3]+22), SUBHEAD, font=s, spacing=3)
    draw.multiline_text((42, sb[3]+25), CTA, font=c, fill=GREEN, spacing=3)
    name_card(draw, 36, 665, 525, 36, 26)
    phone_band(canvas, 885, 195, 132, 105)
    return canvas.convert("RGB")


def build_four_five():
    canvas = Image.new("RGBA", (1080, 1350), (*MINT, 255))
    bokeh(canvas, 1.12)
    paste_logo(canvas, 255, 790, 28)
    paste_doctor(canvas, (465, 390, 1080, 1350))
    draw = ImageDraw.Draw(canvas)
    h = fit_font(HEADLINE, 720, 64, 46)
    s = fit_font(SUBHEAD, 610, 48, 34)
    c = fit_font(CTA, 500, 50, 36)
    draw.multiline_text((46, 130), HEADLINE, font=h, fill=GREEN, spacing=4)
    hb = draw.multiline_textbbox((46, 130), HEADLINE, font=h, spacing=4)
    draw.multiline_text((46, hb[3]+28), SUBHEAD, font=s, fill="white", spacing=4)
    sb = draw.multiline_textbbox((46, hb[3]+28), SUBHEAD, font=s, spacing=4)
    draw.multiline_text((46, sb[3]+28), CTA, font=c, fill=GREEN, spacing=4)
    name_card(draw, 38, 865, 535, 38, 27)
    phone_band(canvas, 1120, 230, 150, 118)
    return canvas.convert("RGB")


def build_vertical():
    canvas = Image.new("RGBA", (1080, 1920), (*MINT, 255))
    bokeh(canvas, 1.35)
    paste_logo(canvas, 310, 730, 35)
    paste_doctor(canvas, (390, 700, 1080, 1920))
    draw = ImageDraw.Draw(canvas)
    h = fit_font(HEADLINE, 920, 76, 58)
    s = fit_font(SUBHEAD, 700, 59, 44)
    c = fit_font(CTA, 570, 62, 46)
    draw.multiline_text((52, 300), HEADLINE, font=h, fill=GREEN, spacing=6)
    hb = draw.multiline_textbbox((52, 300), HEADLINE, font=h, spacing=6)
    draw.multiline_text((52, hb[3]+35), SUBHEAD, font=s, fill="white", spacing=5)
    sb = draw.multiline_textbbox((52, hb[3]+35), SUBHEAD, font=s, spacing=5)
    draw.multiline_text((52, sb[3]+36), CTA, font=c, fill=GREEN, spacing=5)
    name_card(draw, 42, 1280, 565, 42, 30)
    phone_band(canvas, 1640, 280, 180, 140)
    return canvas.convert("RGB")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    outputs = {
        "batsenko_pediatric_1x1.jpg": build_square(),
        "batsenko_pediatric_4x5.jpg": build_four_five(),
        "batsenko_pediatric_9x16.jpg": build_vertical(),
    }
    for name, image in outputs.items():
        path = OUT / name
        image.save(path, quality=95, subsampling=0)
        print(path)


if __name__ == "__main__":
    main()
