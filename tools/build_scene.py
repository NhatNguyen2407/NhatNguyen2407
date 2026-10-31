"""Build the opening scene from the editable cat and committed lettering.

Run from any directory: python tools/build_assets.py
Only the Python standard library is needed for the normal build.
"""

import json
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
LETTERING = json.loads((ROOT / "design/lettering.json").read_text(encoding="utf-8"))


def rect(x, y, width, height, fill, radius=0, stroke="none"):
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'


def line(d, color, width=1):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'


def circle(x, y, radius, color):
    return f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}"/>'


def label(x, y, value, color, size=12, spacing=1.4):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="ui-monospace,Consolas,monospace" font-size="{size}" letter-spacing="{spacing}">{escape(value)}</text>'


def lettering(value, x, baseline, size, color):
    shape = LETTERING["labels"][value]
    scale = size / LETTERING["units"]
    return f'<g fill="{color}" transform="translate({x} {baseline}) scale({scale} {-scale})">{shape["path"]}</g>'


def cat_markup():
    # Reuse the same simple shapes in the standalone file and both scenes.
    namespace = "http://www.w3.org/2000/svg"
    ET.register_namespace("", namespace)
    source = ET.parse(ASSETS / "mascot-cat.svg").getroot()
    artwork = source.find(f"{{{namespace}}}g[@id='cat-art']")
    if artwork is None:
        raise ValueError("The mascot SVG must contain a cat-art group.")
    return ET.tostring(artwork, encoding="unicode")


def document(title, description, width, height, content):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">\n'
        f'<title id="title">{escape(title)}</title>\n'
        f'<desc id="description">{escape(description)}</desc>\n{content}\n</svg>\n'
    )


PALETTES = {
    "dark": {
        "wall": "#34283F", "floor": "#241F30", "frame": "#5E4866", "inset": "#2D253A",
        "ink": "#FFF0DC", "muted": "#CFB9D1", "grid": "#46364D", "sky": "#7C6B9E",
        "horizon": "#C597AB", "buildings": "#594B6B", "window": "#D8ACCB", "desk": "#DCB298",
        "monitor": "#B8AAC9", "screen": "#252237", "code": "#BBCEAF", "footer": "#BBA6C7",
    },
    "light": {
        "wall": "#F3EBDD", "floor": "#E5D9CD", "frame": "#C8B2BB", "inset": "#F9F3E9",
        "ink": "#463A4E", "muted": "#7A697B", "grid": "#CDBCC2", "sky": "#B3B8CE",
        "horizon": "#E6BFAF", "buildings": "#8D839B", "window": "#BD9EAF", "desk": "#C29A7D",
        "monitor": "#A293AE", "screen": "#363044", "code": "#C1D8B3", "footer": "#7E6E83",
    },
}


def build_scene(mode, palette):
    p = palette
    content = rect(0, 0, 960, 360, p["wall"], 12)
    content += rect(0, 275, 960, 85, p["floor"])
    for x in range(0, 961, 48):
        content += line(f"M{x} 275l-50 85", p["grid"])
    for y in (290, 317, 350):
        content += line(f"M0 {y}H960", p["grid"])
    content += rect(34, 28, 892, 264, p["frame"])
    content += rect(46, 40, 868, 240, p["inset"])
    content += rect(530, 57, 340, 193, p["window"])
    content += rect(540, 67, 320, 173, p["sky"])
    content += rect(540, 135, 320, 105, p["horizon"])
    content += circle(791, 104, 21, "#FFE2AD")
    for x, y, height in ((545, 170, 70), (575, 145, 95), (620, 180, 60), (652, 125, 115), (698, 161, 79), (745, 176, 64), (780, 145, 95), (824, 169, 71)):
        content += rect(x, y, 31, height, p["buildings"])
        for window_y in range(y + 10, 230, 20):
            content += rect(x + 7, window_y, 5, 6, "#F1D5BD")
    content += rect(695, 67, 7, 173, p["window"])
    content += rect(540, 153, 320, 6, p["window"])
    content += label(79, 90, "JOHN / NHAT NGUYEN", p["muted"], spacing=2)
    content += lettering("Small ideas.", 76, 154, 49, p["ink"])
    content += lettering("Built with care.", 76, 211, 49, p["ink"])
    content += label(80, 247, "WEB / DATA / SMALL INTERACTIVE THINGS", p["muted"], size=10, spacing=.8)

    # Desk and macOS-inspired monitor. The mascot is placed on the same surface.
    content += rect(516, 272, 355, 12, p["desk"])
    content += rect(535, 284, 12, 48, p["frame"])
    content += rect(841, 284, 12, 48, p["frame"])
    content += rect(566, 177, 147, 95, p["monitor"], 4)
    content += rect(574, 185, 131, 74, p["screen"], 2)
    for index, color in enumerate(("#DF9B98", "#E3C58A", "#AED1A1")):
        content += circle(582 + index * 7, 192, 1.8, color)
    for index, width in enumerate((43, 70, 54, 85)):
        content += rect(587, 205 + index * 11, width, 3, p["code"] if index % 2 == 0 else "#C9A4BF", 1)
    content += rect(630, 272, 17, 9, p["monitor"])
    content += rect(612, 280, 54, 4, p["monitor"])
    content += '<g transform="translate(737 180) scale(1.05)">' + cat_markup() + "</g>"
    content += label(79, 322, "a little corner of the internet", p["footer"], size=12, spacing=.5)
    title = "John / Nhat Nguyen - a little corner of the internet"
    desc = "A quiet desk at sunset, a macOS-inspired monitor and my orange tabby cat. Small ideas. Built with care."
    (ASSETS / f"scene-{mode}.svg").write_text(document(title, desc, 960, 360, content), encoding="utf-8")


def build_heading(mode, palette):
    content = line("M0 9H27", palette["footer"], 2)
    content += lettering("自己紹介", 0, 51, 39, palette["ink"])
    content += label(1, 79, "ABOUT ME", palette["muted"], size=11, spacing=1.1)
    # A smaller intrinsic size keeps the Japanese title readable on a phone.
    (ASSETS / f"about-{mode}.svg").write_text(
        document("自己紹介 / About me", "About me, with Japanese Mincho lettering.", 280, 92, content),
        encoding="utf-8",
    )


for mode, palette in PALETTES.items():
    build_scene(mode, palette)
    build_heading(mode, palette)
for path in ASSETS.glob("*.svg"):
    ET.parse(path)
print("Built the scene and validated the SVG assets.")
