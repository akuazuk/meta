"""Баннеры врачей в стиле папки «Врачи и услуги».

Эталон – Яровой и Ладыгин: мятный кадр, врач справа, официальный логотип
справа сверху, три блока текста слева, полоса с телефоном 403 снизу.
На вертикали ещё карточка имени и стаж. Логотип и номер не вырезаются
из чужого баннера и не рисуются нейросетью.

Портрет – уже готовый кадр без текста (Higgsfield или фото). Скрипт
только собирает макет.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "assets" / "fonts"
LOGO = ROOT / "image" / "brand" / "logo_transparent.png"
PHONE_REF = ROOT / "image" / "brand" / "phone_403.png"

DARK = (14, 99, 86)
WHITE = (255, 255, 255)
CARD = (91, 176, 159)
MINT = (147, 201, 193)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    face = ImageFont.truetype(str(FONTS / name), size)
    if "Montserrat" not in face.getname()[0]:
        raise RuntimeError(f"Expected Montserrat, got {face.getname()}")
    return face


def phone_sprite() -> Image.Image:
    """Белая трубка и 403, вырезанные один раз с эталона Ярового."""
    return Image.open(PHONE_REF).convert("RGBA")


def cover(portrait: Image.Image, width: int, height: int, shift_down: int) -> Image.Image:
    """Кадр на весь холст. Врач у правого края, голова ниже зоны логотипа."""
    src = portrait.convert("RGB")
    scale = max(width / src.width, height / src.height)
    resized = src.resize(
        (round(src.width * scale), round(src.height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = max(0, resized.width - width)
    resized = resized.crop((left, 0, left + width, resized.height))
    canvas = Image.new("RGB", (width, height), MINT)
    if shift_down > 0:
        strip = resized.crop((0, 0, width, min(120, resized.height)))
        strip = strip.resize((width, shift_down), Image.Resampling.BILINEAR)
        strip = strip.filter(ImageFilter.GaussianBlur(12))
        canvas.paste(strip, (0, 0))
    canvas.paste(resized, (0, shift_down))
    return canvas


def is_mint(pixel: tuple[int, int, int]) -> bool:
    r, g, b = pixel
    return abs(r - 150) < 36 and abs(g - 201) < 36 and abs(b - 193) < 40 and g > r


BAND = (72, 138, 128)


def paint_rect(base: Image.Image, right: int, top: int) -> None:
    """Прямоугольник до низа кадра. Правый край прямой и правее тройки."""
    px = base.load()
    for y in range(top, base.height):
        for x in range(min(right, base.width)):
            r, g, b = px[x, y]
            if r > 190 and g > 185 and b > 180:
                continue
            px[x, y] = BAND


def add_logo(base: Image.Image, width: int = 292, margin: int = 36, top: int = 28) -> None:
    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.resize((width, round(logo.height * width / logo.width)), Image.Resampling.LANCZOS)
    layer = base.convert("RGBA")
    layer.alpha_composite(logo, (base.width - width - margin, top))
    base.paste(layer.convert("RGB"))


def draw_blocks(base: Image.Image, blocks: list[dict], x: int = 56) -> None:
    draw = ImageDraw.Draw(base)
    for block in blocks:
        face = font("Montserrat-ExtraBold.ttf", block["size"])
        y = block["y"]
        for line in block["lines"]:
            draw.text((x, y), line, font=face, fill=block["fill"])
            y += block["step"]


def coat_left(base: Image.Image, y0: int, y1: int) -> int:
    """Левый край халата в полосе номера. Тройка должна закончиться раньше."""
    left = base.width
    for y in range(max(0, y0), min(base.height, y1)):
        for x in range(base.width):
            r, g, b = base.getpixel((x, y))
            if r > 190 and g > 185 and b > 180:
                left = min(left, x)
                break
    return left


def add_phone(base: Image.Image, x: int = 48) -> None:
    """Номер внизу кадра. Полоса доходит до низа и правее тройки, рукав её не режет."""
    sprite = phone_sprite()
    gap = 40
    y = base.height - sprite.height - 56
    room = coat_left(base, y, min(base.height, y + sprite.height)) - gap - x
    if room < sprite.width:
        fitted = max(room, 200) / sprite.width
        sprite = sprite.resize(
            (round(sprite.width * fitted), round(sprite.height * fitted)),
            Image.Resampling.LANCZOS,
        )
        y = base.height - sprite.height - 56
    coat = coat_left(base, y, base.height)
    right = min(coat - 8, x + sprite.width + gap)
    right = max(right, x + sprite.width + 16)
    paint_rect(base, right, y - 28)
    layer = base.convert("RGBA")
    layer.alpha_composite(sprite, (x, y))
    base.paste(layer.convert("RGB"))


def add_card(base: Image.Image, name: list[str], role: list[str], years: list[str], box: tuple[int, int, int, int]) -> None:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(box, radius=36, fill=CARD + (255,))
    layer = base.convert("RGBA")
    layer.alpha_composite(overlay)
    base.paste(layer.convert("RGB"))
    draw = ImageDraw.Draw(base)
    x, y = box[0] + 28, box[1] + 22
    name_font = font("Montserrat-ExtraBold.ttf", 40)
    for line in name:
        draw.text((x, y), line, font=name_font, fill=WHITE)
        y += 48
    y += 8
    role_font = font("Montserrat-Bold.ttf", 28)
    for line in role:
        draw.text((x, y), line, font=role_font, fill=DARK)
        y += 36
    years_y = box[3] + 22
    years_font = font("Montserrat-ExtraBold.ttf", 32)
    for line in years:
        draw.text((box[0] + 8, years_y), line, font=years_font, fill=DARK)
        years_y += 40


def build_square(portrait: Path, blocks: list[dict], out: Path) -> Path:
    base = cover(Image.open(portrait), 1080, 1080, shift_down=150)
    draw_blocks(base, blocks)
    add_logo(base)
    add_phone(base)
    out.parent.mkdir(parents=True, exist_ok=True)
    base.save(out, quality=95, subsampling=0)
    return out


def build_vertical(portrait: Path, blocks: list[dict], card: dict, out: Path) -> Path:
    base = cover(Image.open(portrait), 1080, 1920, shift_down=0)
    draw_blocks(base, blocks)
    add_card(base, card["name"], card["role"], card["years"], card["box"])
    add_logo(base, width=300, top=36)
    add_phone(base)
    out.parent.mkdir(parents=True, exist_ok=True)
    base.save(out, quality=95, subsampling=0)
    return out


def main() -> int:
    out_dir = Path("/tmp/fleb_refs/style")
    card = {
        "name": ["Попченко Андрей", "Леонидович"],
        "role": ["К.м.н., врач-флеболог", "высшей категории"],
        "years": ["Стаж работы", "по специальности", "с 1993 года"],
        "box": (52, 1088, 500, 1324),
    }
    buzzing = [
        {"lines": ["НОГИ К ВЕЧЕРУ", "ГУДЯТ, А НЕ", "ОТДЫХАЮТ?"], "y": 168, "size": 52, "step": 62, "fill": DARK},
        {"lines": ["ЭВЛК И СКЛЕРОТЕРАПИЯ", "У ПОПЧЕНКО"], "y": 372, "size": 36, "step": 46, "fill": WHITE},
        {"lines": ["ЗАПИШИТЕСЬ,", "ПОКА ВЕНЫ", "НЕ СТАЛИ ГРОМЧЕ"], "y": 490, "size": 40, "step": 50, "fill": DARK},
    ]
    mesh = [
        {"lines": ["СЕТОЧКА НА НОГАХ", "УЖЕ НЕ КОСМЕТИКА"], "y": 188, "size": 46, "step": 56, "fill": DARK},
        {"lines": ["МИНИФЛЕБЭКТОМИЯ", "БЕЗ ДОЛГИХ", "РАЗРЕЗОВ"], "y": 328, "size": 40, "step": 50, "fill": WHITE},
        {"lines": ["ПОКАЖИТЕ ВЕНЫ", "ВРАЧУ ПОПЧЕНКО"], "y": 504, "size": 40, "step": 50, "fill": DARK},
    ]
    buzzing_vt = [
        {"lines": ["НОГИ К ВЕЧЕРУ", "ГУДЯТ, А НЕ", "ОТДЫХАЮТ?"], "y": 360, "size": 58, "step": 70, "fill": DARK},
        {"lines": ["ЭВЛК И СКЛЕРОТЕРАПИЯ", "У ПОПЧЕНКО"], "y": 590, "size": 40, "step": 52, "fill": WHITE},
        {"lines": ["ЗАПИШИТЕСЬ,", "ПОКА ВЕНЫ", "НЕ СТАЛИ ГРОМЧЕ"], "y": 720, "size": 44, "step": 56, "fill": DARK},
    ]
    mesh_vt = [
        {"lines": ["СЕТОЧКА НА НОГАХ", "УЖЕ НЕ КОСМЕТИКА"], "y": 360, "size": 52, "step": 64, "fill": DARK},
        {"lines": ["МИНИФЛЕБЭКТОМИЯ", "БЕЗ ДОЛГИХ", "РАЗРЕЗОВ"], "y": 520, "size": 44, "step": 56, "fill": WHITE},
        {"lines": ["ПОКАЖИТЕ ВЕНЫ", "ВРАЧУ ПОПЧЕНКО"], "y": 720, "size": 44, "step": 56, "fill": DARK},
    ]
    pairs = [
        ("gen_sq1.png", "gen_vt1.png", buzzing, buzzing_vt, "buzz"),
        ("gen_sq2.png", "gen_vt2.png", mesh, mesh_vt, "mesh"),
    ]
    src = Path("/tmp/fleb_refs")
    for sq, vt, sq_blocks, vt_blocks, slug in pairs:
        print(build_square(src / sq, sq_blocks, out_dir / f"pop_{slug}_sq.jpg"))
        print(build_vertical(src / vt, vt_blocks, card, out_dir / f"pop_{slug}_vt.jpg"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
