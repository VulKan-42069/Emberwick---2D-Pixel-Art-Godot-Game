"""World props, trees, the lantern shrine and item icons. Shape-built, shaded top-left, auto-outlined.

assets/props/props.png    16x16 cells, 8 columns (see PROPS order below / tools/build/props_meta.json)
assets/props/tree_large.png (32x40)  tree_small.png (24x32)
assets/props/shrine.png   32x32 cells: [unlit, lit x4]
assets/items/items.png    16x16 cells, one row
"""
import json
import random
from pathlib import Path

from pxl import T, new, put, rect, paste, scaled, on_bg, ellipse, tri, outline, line_pts

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "tools" / "build"
PREV = ROOT / "tools" / "previews"


def lit_ellipse(img, cx, cy, rx, ry, ramp):
    """Ellipse shaded from the top-left; ramp runs lightest -> darkest (4 tones)."""
    for y in range(img.height):
        for x in range(img.width):
            nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if nx * nx + ny * ny <= 1:
                t = nx * 0.6 + ny * 0.8
                put(img, x, y, ramp[0] if t < -0.45 else ramp[1] if t < 0.15 else ramp[2] if t < 0.6 else ramp[3])


GREEN = ["g4", "g3", "g2", "g1"]
STONE = ["st3", "st2", "st2", "st1"]
CLAY = ["d4", "d3", "d3", "d2"]


# ------------------------------------------------------------------ 16x16 props
def bush(berries=False):
    img = new(T, T)
    for (cx, cy, rx, ry) in ((4.8, 10, 4.6, 4), (11.2, 10, 4.6, 4), (8, 7.5, 5.6, 4.6)):
        lit_ellipse(img, cx, cy, rx, ry, GREEN)
    r = random.Random(4)
    for _ in range(7):
        x, y = r.randrange(3, 13), r.randrange(4, 12)
        if img.getpixel((x, y))[3]:
            put(img, x, y, "g4" if y < 8 else "g1")
    if berries:
        for (x, y) in ((5, 7), (10, 6), (8, 10), (12, 10), (4, 11)):
            put(img, x, y, "r2"); put(img, x, y - 1, "r3")
    outline(img)
    return img


def bush_cut():
    img = new(T, T)
    for (x, y) in ((4, 12), (5, 11), (7, 12), (9, 11), (10, 12), (12, 12), (8, 10)):
        put(img, x, y, "g2"); put(img, x, y - 1, "g3")
    for x in range(3, 13):
        put(img, x, 13, "d2")
    for x in range(4, 12):
        put(img, x, 12, "d3") if (x % 3) else None
    outline(img)
    return img


def rock(small=False):
    img = new(T, T)
    if small:
        lit_ellipse(img, 8, 11.5, 4.2, 3.2, STONE)
        put(img, 7, 10, "st3")
    else:
        lit_ellipse(img, 8, 9.5, 6.6, 5.2, STONE)
        for (x, y) in ((6, 7), (7, 8), (7, 9), (11, 11), (10, 10)):
            put(img, x, y, "st1")
        for (x, y) in ((4, 7), (5, 6)):
            put(img, x, y, "st3")
        put(img, 3, 11, "g2"); put(img, 4, 12, "g2"); put(img, 12, 12, "g2")   # a little moss
    outline(img)
    return img


def block():
    img = new(T, T)
    rect(img, 0, 0, 16, 16, "ink")
    rect(img, 1, 1, 14, 14, "st1")
    rect(img, 2, 2, 12, 12, "st2")
    for i in range(2, 14):
        put(img, i, 2, "st3"); put(img, 2, i, "st3")
        put(img, i, 13, "st1"); put(img, 13, i, "st1")
    for (x, y) in ((8, 5), (7, 6), (8, 6), (9, 6), (6, 7), (7, 7), (8, 7), (9, 7), (10, 7),
                   (7, 8), (8, 8), (9, 8), (8, 9)):                    # ember rune
        put(img, x, y, "e2")
    put(img, 8, 7, "e4"); put(img, 8, 6, "e3"); put(img, 7, 7, "e3")
    for (x, y) in ((3, 12), (4, 12), (3, 11), (12, 3), (11, 3)):
        put(img, x, y, "g2")
    return img


def pot(broken=False):
    img = new(T, T)
    if not broken:
        lit_ellipse(img, 8, 10.5, 5.4, 4.9, CLAY)
        rect(img, 5, 4, 6, 3, "d3")
        for x in range(5, 11):
            put(img, x, 4, "d4"); put(img, x, 6, "d2")
        ellipse(img, 8, 4.3, 3.2, 1.1, "ink")
        for x in range(3, 14):
            if img.getpixel((x, 9))[3]:
                put(img, x, 9, "e1")
        put(img, 5, 10, "d4"); put(img, 5, 11, "d4")
    else:
        for (pts, c) in (
            (((2, 13), (6, 8), (8, 13)), "d3"), (((8, 13), (10, 9), (14, 13)), "d2"),
            (((5, 13), (7, 11), (9, 13)), "d4"),
        ):
            tri(img, *pts, c)
        for (x, y) in ((3, 10), (12, 11), (1, 13), (14, 13)):
            put(img, x, y, "d3")
        for x in range(2, 15):
            put(img, x, 13, "d2") if x % 2 else None
    outline(img)
    return img


def chest(opened=False):
    img = new(T, T)
    if not opened:
        rect(img, 1, 6, 14, 8, "d3")
        rect(img, 2, 3, 12, 4, "d3")
        for x in range(2, 14):
            put(img, x, 3, "d4"); put(img, x, 6, "d2")
        for y in range(7, 14):
            put(img, 1, y, "d4")
        for x in range(1, 15):
            put(img, x, 12, "d2"); put(img, x, 13, "d2")
        for bx in (3, 11):
            for y in range(3, 14):
                put(img, bx, y, "st2"); put(img, bx + 1, y, "st1")
        rect(img, 7, 7, 3, 3, "e3"); put(img, 8, 8, "ink"); put(img, 9, 7, "e4")
    else:
        rect(img, 2, 1, 12, 4, "d2")                       # raised lid, seen from behind
        for x in range(2, 14):
            put(img, x, 1, "d3"); put(img, x, 4, "d1")
        rect(img, 1, 5, 14, 4, "ink")                      # dark inside
        for (x, y) in ((6, 6), (9, 7), (11, 6), (4, 7)):
            put(img, x, y, "e3")
        put(img, 9, 7, "e4")
        rect(img, 1, 9, 14, 5, "d3")
        for x in range(1, 15):
            put(img, x, 9, "d4"); put(img, x, 13, "d2"); put(img, x, 12, "d2")
        for bx in (3, 11):
            for y in range(1, 14):
                if y not in (5, 6, 7, 8):
                    put(img, bx, y, "st2"); put(img, bx + 1, y, "st1")
        rect(img, 7, 9, 3, 2, "e3")
    outline(img)
    return img


def signpost():
    img = new(T, T)
    rect(img, 7, 8, 2, 7, "d2")
    for y in range(8, 15):
        put(img, 7, y, "d3")
    rect(img, 1, 2, 14, 7, "d3")
    for x in range(1, 15):
        put(img, x, 2, "d4"); put(img, x, 8, "d2")
    for x in range(3, 9):
        put(img, x, 4, "d1")
    for x in range(3, 12):
        put(img, x, 6, "d1")
    outline(img)
    return img


def door(opened=False):
    img = new(T, T)
    rect(img, 0, 0, 16, 16, "ink")
    rect(img, 1, 1, 14, 15, "st2")
    for x in range(1, 15):
        put(img, x, 1, "st3")
    for y in range(1, 16):
        put(img, 1, y, "st3"); put(img, 14, y, "st1")
    if not opened:
        rect(img, 3, 3, 10, 13, "d2")
        for x in (5, 8, 11):
            for y in range(3, 16):
                put(img, x, y, "d1")
        for y in range(3, 16):
            put(img, 3, y, "d3")
        for y in (5, 12):
            for x in range(3, 13):
                put(img, x, y, "st1")
        rect(img, 7, 8, 3, 3, "e3"); put(img, 8, 9, "ink"); put(img, 8, 10, "ink")
    else:
        rect(img, 3, 3, 10, 13, "ink")
        for y in range(3, 16):
            put(img, 3, y, "st1")
        for x in range(3, 13):
            put(img, x, 15, "st1")
    return img


def floor_switch(pressed=False):
    img = new(T, T)
    if not pressed:
        ellipse(img, 8, 10.5, 6.2, 4.2, "st1")
        lit_ellipse(img, 8, 9, 6.2, 4.2, STONE)
        for (x, y) in ((7, 8), (8, 7), (8, 8), (9, 8), (8, 9)):
            put(img, x, y, "e1")
        put(img, 8, 8, "e2")
    else:
        lit_ellipse(img, 8, 10.5, 6.2, 3.6, ["st2", "st2", "st1", "st1"])
        ellipse(img, 8, 10.5, 3.6, 1.8, "e2")
        ellipse(img, 8, 10.2, 2, 0.9, "e4")
    outline(img)
    return img


PROPS = [
    ("bush", bush), ("bush_berries", lambda: bush(True)), ("bush_cut", bush_cut), ("rock", rock),
    ("rock_small", lambda: rock(True)), ("push_block", block), ("pot", pot), ("pot_broken", lambda: pot(True)),
    ("chest_closed", chest), ("chest_open", lambda: chest(True)), ("signpost", signpost),
    ("door_locked", door), ("door_open", lambda: door(True)), ("floor_switch_up", floor_switch),
    ("floor_switch_down", lambda: floor_switch(True)),
]


# ------------------------------------------------------------------ trees
def tree(w, h, lobes, trunk, seed):
    img = new(w, h)
    tx0, tx1, ty0, ty1 = trunk
    for y in range(ty0, ty1 + 1):
        flare = max(0, y - (ty1 - 3))
        for x in range(tx0 - flare, tx1 + flare + 1):
            c = "d2"
            if x <= tx0 - flare + 1: c = "d3"
            elif x >= tx1 + flare - 1: c = "d1"
            put(img, x, y, c)
    r = random.Random(seed)
    for y in range(ty0 + 2, ty1 - 2, 3):
        put(img, r.randrange(tx0 + 1, tx1), y, "d1")
    for (cx, cy, rx, ry) in lobes:
        lit_ellipse(img, cx, cy, rx, ry, GREEN)
    for _ in range(w):
        x, y = r.randrange(w), r.randrange(int(h * 0.7))
        px = img.getpixel((x, y))
        if px[3] and px[:3] == (148, 209, 92):
            continue
        if px[3] and px[:3] in ((95, 174, 75), (59, 135, 65)):
            put(img, x, y, "g4" if px[:3] == (95, 174, 75) else "g1")
    outline(img)
    return img


def tree_large():
    return tree(32, 40, [(11, 22, 8, 6), (21, 22, 8, 6), (8.5, 15, 7.5, 6.5), (23.5, 15, 7.5, 6.5),
                         (16, 18, 9, 7.5), (16, 9.5, 9.5, 7.5)], (13, 18, 24, 38), 11)


def tree_small():
    return tree(24, 32, [(8, 14, 6, 5), (16, 14, 6, 5), (12, 13, 7, 6.5), (12, 8, 6.5, 6)], (10, 13, 19, 30), 12)


# ------------------------------------------------------------------ lantern shrine
def shrine(frame):
    img = new(32, 32)
    glow = new(32, 32)
    lit = frame > 0
    f = frame - 1
    if lit:                                            # warm glow, kept on its own layer so it isn't outlined
        pulse = (0, 1, 2, 1)[f]
        for rr, a in ((12 + pulse, 20), (9 + pulse, 34)):
            layer = new(32, 32)
            ellipse(layer, 16, 12, rr, rr * 0.8, "e3")
            for y in range(32):
                for x in range(32):
                    if layer.getpixel((x, y))[3]:
                        put(glow, x, y, "e3", a)
    rect(img, 4, 27, 24, 4, "st2"); rect(img, 4, 27, 24, 1, "st3"); rect(img, 4, 30, 24, 1, "st1")
    rect(img, 7, 24, 18, 4, "st2"); rect(img, 7, 24, 18, 1, "st3"); rect(img, 7, 27, 18, 1, "st1")
    rect(img, 12, 13, 8, 11, "st2"); rect(img, 12, 13, 2, 11, "st3"); rect(img, 18, 13, 2, 11, "st1")
    glyph = "e3" if lit else "st1"
    for (x, y) in ((16, 17), (15, 18), (16, 18), (17, 18), (16, 19)):
        put(img, x, y, glyph)
    if lit:
        put(img, 16, 18, "e4")
    rect(img, 10, 9, 12, 5, "st2")
    rect(img, 10, 9, 2, 5, "st3"); rect(img, 20, 9, 2, 5, "st1")
    rect(img, 12, 10, 8, 3, "ink" if not lit else "e2")
    if lit:
        h = (3, 4, 3, 4)[f]
        ox = (0, 1, 0, -1)[f]
        for yy in range(h):
            half = max(0, 2.6 - yy * 0.7)
            for xx in range(-3, 4):
                if abs(xx) <= half:
                    put(img, 16 + xx + ox, 13 - yy, "e4" if yy < 2 and abs(xx) < 1.5 else "e3")
        ellipse(img, 16 + ox, 11.5, 2.2, 1.4, "e4")
    else:
        for (x, y) in ((13, 10), (14, 11), (18, 10), (17, 11)):
            put(img, x, y, "st1")
    tri(img, (16, 1.5), (7, 9), (25, 9), "st1")
    tri(img, (16, 3), (10, 9), (16, 9), "st2")
    for x in range(8, 25):
        put(img, x, 9, "st2") if x % 2 else None
    if lit:
        for (sx, sy) in (((9, 6), (22, 5), (14, 3)) if f % 2 == 0 else ((10, 4), (23, 7), (18, 2))):
            put(img, sx, sy - f, "e3")
    outline(img)
    glow.alpha_composite(img)
    return glow


# ------------------------------------------------------------------ items (16x16)
def heart_item():
    img = new(T, T)
    for (cx, cy) in ((5.3, 5.5), (10.7, 5.5)):
        ellipse(img, cx, cy, 3.6, 3.6, "r2")
    tri(img, (1.7, 6.5), (14.3, 6.5), (8, 14), "r2")
    for y in range(T):
        for x in range(T):
            if img.getpixel((x, y))[3] and (x + y > 17 or x > 11):
                put(img, x, y, "r1" if x + y > 19 else "r2")
    for (x, y) in ((3, 4), (4, 3), (4, 4), (11, 3)):
        put(img, x, y, "r3")
    put(img, 3, 3, "white")
    outline(img)
    return img


def shard_item():
    img = new(T, T)
    tri(img, (8, 1), (3.5, 6.5), (8, 15), "e3")
    tri(img, (8, 1), (12.5, 6.5), (8, 15), "e2")
    tri(img, (8, 1), (3.5, 6.5), (8, 6.5), "e4")
    tri(img, (8, 6.5), (12.5, 6.5), (8, 15), "e1")
    put(img, 6, 4, "white"); put(img, 6, 5, "white")
    outline(img)
    return img


def coin_item():
    img = new(T, T)
    ellipse(img, 8, 8, 5.6, 5.6, "e2")
    ellipse(img, 8, 8, 4.4, 4.4, "e3")
    for (x, y) in ((8, 5), (7, 6), (8, 6), (9, 6), (6, 7), (7, 7), (8, 7), (9, 7), (10, 7),
                   (7, 8), (8, 8), (9, 8), (8, 9), (8, 10)):
        put(img, x, y, "e1") if (x, y) in ((8, 5), (7, 6), (9, 6), (6, 7), (10, 7), (7, 8), (9, 8), (8, 9), (8, 10)) else put(img, x, y, "e2")
    for (x, y) in ((4, 5), (5, 4), (4, 6)):
        put(img, x, y, "e4")
    outline(img)
    return img


def key_item():
    img = new(T, T)
    ellipse(img, 8, 4.5, 3.4, 3.4, "e3")
    ellipse(img, 8, 4.5, 1.5, 1.5, "ink")
    for y in range(7, 14):
        put(img, 7, y, "e3"); put(img, 8, y, "e2")
    for (x, y) in ((9, 10), (10, 10), (9, 12), (10, 12), (11, 12)):
        put(img, x, y, "e2")
    put(img, 6, 3, "e4"); put(img, 5, 4, "e4")
    for y in range(7, 14):
        img.putpixel((7, y), (255, 196, 74, 255))
    outline(img)
    # ellipse hole is ink-filled; punch it out so it reads as a ring
    for (x, y) in ((8, 4), (7, 4), (8, 5), (7, 5)):
        img.putpixel((x, y), (27, 27, 47, 255))
    return img


def potion_item():
    img = new(T, T)
    lit_ellipse(img, 8, 10, 4.9, 4.6, ["r3", "r2", "r2", "r1"])
    rect(img, 7, 4, 3, 3, "st3")
    put(img, 7, 4, "white")
    rect(img, 6, 2, 5, 2, "d3"); put(img, 6, 2, "d4")
    put(img, 5, 9, "white"); put(img, 5, 10, "white")
    for x in range(5, 12):
        put(img, x, 7, "r3") if img.getpixel((x, 7))[3] else None
    outline(img)
    return img


def sword_item():
    img = new(T, T)
    pts = line_pts((13, 2), (4, 11))
    for (x, y) in pts:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                put(img, x + dx, y + dy, "ink")
    for i, (x, y) in enumerate(pts):
        put(img, x, y, "white" if i % 2 == 0 else "st3")
    for (x, y) in ((3, 9), (4, 10), (5, 11), (6, 12), (2, 12)):
        put(img, x, y, "e3")
    put(img, 3, 13, "d2"); put(img, 2, 14, "d2")
    for (x, y) in ((3, 9), (4, 10), (5, 11), (6, 12), (3, 12), (4, 11)):
        put(img, x, y, "e3")
    return img


def lantern_item():
    img = new(T, T)
    for x in (6, 7, 8, 9):
        put(img, x, 1, "d1")
    put(img, 5, 2, "d1"); put(img, 10, 2, "d1")
    rect(img, 4, 3, 8, 2, "st2")
    rect(img, 4, 5, 8, 7, "e3")
    rect(img, 6, 6, 4, 4, "e4")
    for y in range(5, 12):
        put(img, 4, y, "st2"); put(img, 11, y, "st1")
    rect(img, 4, 12, 8, 2, "st2")
    put(img, 5, 6, "e4"); put(img, 10, 10, "e2"); put(img, 9, 11, "e2")
    outline(img)
    return img


ITEMS = [("ember_shard", shard_item), ("heart", heart_item), ("coin", coin_item), ("key", key_item),
         ("potion", potion_item), ("sword", sword_item), ("lantern", lantern_item)]


# ------------------------------------------------------------------ output
def main():
    (ROOT / "assets" / "props").mkdir(parents=True, exist_ok=True)
    (ROOT / "assets" / "items").mkdir(parents=True, exist_ok=True)
    cols = 8
    sheet = new(cols * T, ((len(PROPS) + cols - 1) // cols) * T)
    for i, (_, fn) in enumerate(PROPS):
        paste(sheet, fn(), (i % cols) * T, (i // cols) * T)
    sheet.save(ROOT / "assets" / "props" / "props.png")
    tl, ts = tree_large(), tree_small()
    tl.save(ROOT / "assets" / "props" / "tree_large.png")
    ts.save(ROOT / "assets" / "props" / "tree_small.png")
    sh = new(5 * 32, 32)
    for i in range(5):
        paste(sh, shrine(i), i * 32, 0)
    sh.save(ROOT / "assets" / "props" / "shrine.png")
    items = new(len(ITEMS) * T, T)
    for i, (_, fn) in enumerate(ITEMS):
        paste(items, fn(), i * T, 0)
    items.save(ROOT / "assets" / "items" / "items.png")
    meta = dict(
        props=dict(cell=16, columns=cols, order=[n for n, _ in PROPS]),
        trees=dict(large=[32, 40], small=[24, 32], trunk_base_y=dict(large=38, small=30)),
        shrine=dict(cell=32, frames=dict(unlit=0, lit=[1, 2, 3, 4]), lit_fps=6),
        items=dict(cell=16, order=[n for n, _ in ITEMS]),
    )
    (BUILD / "props_meta.json").write_text(json.dumps(meta, indent=1))
    board = new(250, 150)
    paste(board, sheet, 0, 0)
    paste(board, items, 0, 36)
    paste(board, tl, 4, 56)
    paste(board, ts, 42, 66)
    paste(board, sh, 72, 54)
    scaled(on_bg(board, (60, 90, 60, 255)), 5).save(PREV / "props_sheet.png")
    print("props done")


if __name__ == "__main__":
    main()
