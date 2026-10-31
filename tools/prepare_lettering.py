"""Optional: regenerate lettering after changing the labels.

Needs fonttools and the original, unmodified ShipporiMincho-Regular.ttf.
The normal build does not need a font or this optional dependency.
"""

import argparse
import hashlib
import json
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
LABELS = ("Small ideas.", "Built with care.", "自己紹介")

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("font", type=Path, help="Path to ShipporiMincho-Regular.ttf")
args = parser.parse_args()
font = TTFont(args.font)
glyphs = font.getGlyphSet()
cmap = font.getBestCmap()
result = {
    "font": "Shippori Mincho Regular",
    "font_source": "https://github.com/google/fonts/tree/main/ofl/shipporimincho",
    "font_sha256": hashlib.sha256(args.font.read_bytes()).hexdigest(),
    "license": "SIL Open Font License 1.1; see licenses/OFL-ShipporiMincho.txt",
    "units": font["head"].unitsPerEm,
    "labels": {},
}
for label in LABELS:
    offset = 0
    parts = []
    for char in label:
        name = cmap.get(ord(char))
        if name is None:
            raise ValueError(f"Missing font glyph: {char}")
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        parts.append(f'<g transform="translate({offset} 0)"><path d="{pen.getCommands()}"/></g>')
        offset += font["hmtx"][name][0]
    result["labels"][label] = {"advance": offset, "path": "".join(parts)}
(ROOT / "design/lettering.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Prepared vector lettering. Run tools/build_assets.py next.")
