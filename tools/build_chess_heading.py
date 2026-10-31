"""Optional artwork build: python tools/build_chess_heading.py path/to/ShipporiMincho-Regular.ttf

Only needed when changing the Japanese title; requires fonttools locally.
The committed SVGs are used by the regular workflows without font downloads.
"""

import sys
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

root = Path(__file__).resolve().parents[1]
font = TTFont(sys.argv[1])
glyphs = font.getGlyphSet()
cmap = font.getBestCmap()
parts = []
offset = 0
for char in 'チェス':
    name = cmap[ord(char)]
    pen = SVGPathPen(glyphs)
    glyphs[name].draw(pen)
    parts.append(f'<g transform="translate({offset} 0)"><path d="{pen.getCommands()}"/></g>')
    offset += font['hmtx'][name][0]
scale = 39 / font['head'].unitsPerEm
for theme, ink, muted in [('dark', '#e7eaf2', '#9eacc1'), ('light', '#2d344a', '#657084')]:
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="280" height="92" viewBox="0 0 280 92" role="img"><title>チェス / Chess with John</title><path d="M0 8H25" stroke="{muted}" stroke-width="2"/><g fill="{ink}" transform="translate(0 51) scale({scale} {-scale})">{"".join(parts)}</g><text x="1" y="78" fill="{muted}" font-family="ui-monospace,Consolas,monospace" font-size="11" letter-spacing="1.1">CHESS WITH JOHN</text></svg>\n'
    (root/f'assets/heading-chess-{theme}.svg').write_text(svg, encoding='utf-8')
