"""Title-screen art: the EMBERWICK logo (the game's own 5x7 font, chunky and ember-lit) and a pixel moon.

assets/ui/logo.png    assets/ui/moon.png
"""
from pathlib import Path

from PIL import Image

from pxl import new, put, scaled, on_bg
from palette import rgba
from gen_fx_ui import GLYPHS

ROOT = Path(__file__).resolve().parent.parent
PREV = ROOT / "tools" / "previews"

ROW_COLORS = ["e4", "e3", "e3", "e2", "e2", "e1", "e1"]   # ember gradient, top to bottom of each letter
LIGHT = {"e4": "white", "e3": "e4", "e2": "e3", "e1": "e2"}
DARK = {"e4": "e3", "e3": "e2", "e2": "e1", "e1": "r1"}


def logo(text="EMBERWICK", k=4, gap=1):
    glyphs = [GLYPHS[c] for c in text]
    w = sum(len(g[0]) for g in glyphs) + gap * (len(glyphs) - 1)
    pad = 4
    W, H = w * k + pad * 2, 7 * k + pad * 2 + 3
    img = new(W, H)
    mask = set()                                        # pixels of the letters
    x0 = pad
    cells = []
    for g in glyphs:
        for gy, row in enumerate(g):
            for gx, ch in enumerate(row):
                if ch == "#":
                    cells.append((x0 + gx * k, pad + gy * k, gy))
        x0 += (len(g[0]) + gap) * k
    for (x, y, gy) in cells:
        for dy in range(k):
            for dx in range(k):
                mask.add((x + dx, y + dy))
    def grow(src, r):
        out = set(src)
        for (x, y) in src:
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    out.add((x + dx, y + dy))
        return out
    outline = grow(mask, 2)
    for (x, y) in outline:                              # drop shadow, then outline
        put(img, x + 1, y + 3, "m1")
    for (x, y) in outline:
        put(img, x, y, "ink")
    for (x, y, gy) in cells:                            # each font pixel is a lit, bevelled block
        base = ROW_COLORS[gy]
        for dy in range(k):
            for dx in range(k):
                c = base
                if dy == 0 or dx == 0:
                    c = LIGHT[base]
                elif dy == k - 1 or dx == k - 1:
                    c = DARK[base]
                put(img, x + dx, y + dy, c)
    for (x, y, gy) in cells[::7]:                       # a few glints
        put(img, x + 1, y + 1, "white")
    return img


def moon(r=13):
    s = r * 2 + 2
    img = new(s, s)
    cx = cy = r + 0.5
    for y in range(s):
        for x in range(s):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d <= r:
                shade = ((x - cx) * 0.6 + (y - cy) * 0.8) / r    # lit from the upper left
                put(img, x, y, "white" if shade < -0.15 else "s3" if shade < 0.45 else "s2")
    for (dx, dy, rr) in ((4, -4, 3), (-5, 3, 2), (5, 6, 2), (-1, -8, 1.6), (0, 7, 1.4)):   # craters
        for y in range(s):
            for x in range(s):
                if ((x - cx - dx) ** 2 + (y - cy - dy) ** 2) ** 0.5 <= rr and img.getpixel((x, y))[3]:
                    put(img, x, y, "s2")
                    if ((x - cx - dx + 1) ** 2 + (y - cy - dy + 1) ** 2) ** 0.5 > rr:
                        put(img, x, y, "s1")
    return img


def main():
    ui = ROOT / "assets" / "ui"
    lg, mn = logo(), moon()
    lg.save(ui / "logo.png")
    mn.save(ui / "moon.png")
    board = new(lg.width + 40 + mn.width, max(lg.height, mn.height))
    board.alpha_composite(lg, (0, 0))
    board.alpha_composite(mn, (lg.width + 20, 0))
    scaled(on_bg(board, (30, 26, 60, 255)), 3).save(PREV / "title_art.png")
    print("title art", lg.size, mn.size)


if __name__ == "__main__":
    main()
