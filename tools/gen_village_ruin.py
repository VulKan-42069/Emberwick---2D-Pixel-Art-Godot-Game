"""Village + ruin pieces that are not autotiled.

assets/tilesets/village.png     16x16 tiles, 8 columns (houses, fences, bridge) - order in tools/build/village_meta.json
assets/tilesets/ruin.png        16x16 tiles, 8 columns (floors, cracked wall, doorway, stairs, pit)
assets/tilesets/torch.png       4 frames of an animated wall torch (16x16)
assets/props/village_props.png  well (32x32), barrel, crate, lamp post (16x32: unlit + 2 lit frames) - see meta
assets/props/ruin_props.png     16x24 cells: pillar, broken pillar, rubble, cobweb
"""
import json
import random
from pathlib import Path

from pxl import T, new, put, rect, paste, scaled, on_bg, ellipse, tri, outline
import gen_terrain as G

ROOT = Path(__file__).resolve().parent.parent
TS = ROOT / "assets" / "tilesets"
PR = ROOT / "assets" / "props"
BUILD = ROOT / "tools" / "build"
PREV = ROOT / "tools" / "previews"


# ------------------------------------------------------------------ village tiles
def roof_tile(left=False, right=False, top=False, bottom=False, chimney=False):
    img = new(T, T)
    rect(img, 0, 0, T, T, "r2")
    for y in range(T):
        off = ((y // 4) % 2) * 4
        for x in range(T):
            if y % 4 == 3:
                put(img, x, y, "r1")
            elif (x + off) % 8 == 7:
                put(img, x, y, "r1")
            elif y % 4 == 0 and (x + off) % 8 in (1, 2, 3):
                put(img, x, y, "r3")
    if top:
        for x in range(T):
            put(img, x, 0, "ink"); put(img, x, 1, "r3"); put(img, x, 2, "r2")
    if bottom:
        for x in range(T):
            put(img, x, 12, "r1"); put(img, x, 13, "r2"); put(img, x, 14, "r1"); put(img, x, 15, "ink")
            if x % 4 == 3:
                put(img, x, 14, "ink")
    if left:
        for y in range(T):
            put(img, 0, y, "ink"); put(img, 1, y, "r3")
    if right:
        for y in range(T):
            put(img, 15, y, "ink"); put(img, 14, y, "r1")
    if chimney:
        rect(img, 9, 2, 5, 10, "st2")
        rect(img, 9, 2, 1, 10, "st3"); rect(img, 13, 2, 1, 10, "st1")
        rect(img, 8, 1, 7, 2, "st3"); rect(img, 8, 2, 7, 1, "st2")
        for y in range(5, 12, 3):
            for x in range(10, 13):
                put(img, x, y, "st1")
        for x in range(8, 15):
            put(img, x, 0, "ink")
        for y in range(1, 12):
            put(img, 8 if y > 2 else 7, y, "ink"); put(img, 14 if y > 2 else 15, y, "ink")
    return img


def plaster(img, y0=0, y1=T):
    rect(img, 0, y0, T, y1 - y0, "s3")
    r = random.Random(y0 + 3)
    for _ in range(10):
        put(img, r.randrange(T), r.randrange(y0, y1), "s2")


def wall_up(window=False, edge=None):
    img = new(T, T)
    plaster(img)
    rect(img, 0, 0, T, 2, "d2"); rect(img, 0, 0, T, 1, "d3")
    if window:
        rect(img, 3, 3, 10, 10, "d2")
        rect(img, 4, 4, 8, 8, "w3")
        for (x, y) in ((4, 4), (5, 4), (4, 5)):
            put(img, x, y, "w4")
        for i in range(4, 12):
            put(img, 7, i, "d2"); put(img, 8, i, "d2"); put(img, i, 8, "d2")
        rect(img, 2, 13, 12, 2, "d3"); rect(img, 2, 14, 12, 1, "d1")
        rect(img, 1, 4, 2, 8, "b2"); rect(img, 13, 4, 2, 8, "b2")
        for y in (5, 7, 9, 11):
            put(img, 1, y, "b1"); put(img, 14, y, "b1")
    if edge in ("l", "r"):
        x0 = 0 if edge == "l" else 14
        rect(img, x0, 0, 2, T, "d2"); rect(img, x0, 0, 1, T, "d3")
    return img


def wall_low(edge=None):
    img = new(T, T)
    plaster(img, 0, 12)
    rect(img, 0, 12, T, 4, "st2")
    for x in range(T):
        put(img, x, 12, "st3"); put(img, x, 15, "st1")
        if x % 6 == 5:
            for y in range(13, 15):
                put(img, x, y, "st1")
    if edge in ("l", "r"):
        x0 = 0 if edge == "l" else 14
        rect(img, x0, 0, 2, 12, "d2"); rect(img, x0, 0, 1, 12, "d3")
    return img


def door_top():
    img = new(T, T)
    plaster(img)
    rect(img, 0, 0, T, 2, "d2"); rect(img, 0, 0, T, 1, "d3")
    rect(img, 2, 4, 12, 12, "d1")
    rect(img, 3, 5, 10, 11, "d3")
    tri(img, (3, 5), (13, 5), (8, 3), "d3")
    for x in (5, 8, 11):
        for y in range(5, 16):
            put(img, x, y, "d2")
    for y in range(5, 16):
        put(img, 3, y, "d4")
    rect(img, 6, 8, 4, 2, "ink"); put(img, 7, 8, "e3")
    return img


def door_bottom():
    img = new(T, T)
    plaster(img, 0, 12)
    rect(img, 0, 12, T, 4, "st2")
    rect(img, 2, 0, 12, 14, "d1")
    rect(img, 3, 0, 10, 14, "d3")
    for x in (5, 8, 11):
        for y in range(0, 14):
            put(img, x, y, "d2")
    for y in range(0, 14):
        put(img, 3, y, "d4")
    for x in range(0, 16):
        put(img, x, 14, "st3"); put(img, x, 15, "st1")
    rect(img, 10, 6, 2, 2, "e3")
    for y in (2, 9):
        for x in range(3, 13):
            put(img, x, y, "st1")
    return img


def fence(kind):
    img = new(T, T)
    if kind in ("h", "hl", "hr"):
        x0 = 8 if kind == "hl" else 0
        x1 = 8 if kind == "hr" else 16
        for (y, h) in ((5, 2), (10, 2)):
            rect(img, x0, y, x1 - x0, h, "d3")
            for x in range(x0, x1):
                put(img, x, y, "d4"); put(img, x, y + 1, "d2")
        px = {"h": [7], "hl": [7], "hr": [7]}[kind]
        for p in px:
            rect(img, p, 2, 3, 13, "d2"); rect(img, p, 2, 1, 13, "d3"); rect(img, p + 2, 2, 1, 13, "d1")
            put(img, p + 1, 2, "d4")
    else:  # vertical
        for (x, w) in ((5, 2), (10, 2)):
            rect(img, x, 0, w, T, "d3")
            for y in range(T):
                put(img, x, y, "d4"); put(img, x + 1, y, "d2")
        rect(img, 3, 7, 10, 3, "d2")
        rect(img, 3, 7, 10, 1, "d3")
    outline(img)
    return img


def bridge(horizontal):
    img = new(T, T)
    rect(img, 0, 0, T, T, "d3")
    if horizontal:
        for x in range(0, T, 4):
            for y in range(T):
                put(img, x + 3, y, "d2")
                put(img, x, y, "d4") if 3 < y < 12 else None
        for y in (0, 1, 2):
            rect(img, 0, y, T, 1, ("d2", "d3", "d1")[y])
        for y in (13, 14, 15):
            rect(img, 0, y, T, 1, ("d3", "d2", "d1")[y - 13])
    else:
        for y in range(0, T, 4):
            for x in range(T):
                put(img, x, y + 3, "d2")
                put(img, x, y, "d4") if 3 < x < 12 else None
        for x in (0, 1, 2):
            rect(img, x, 0, 1, T, ("d2", "d3", "d1")[x])
        for x in (13, 14, 15):
            rect(img, x, 0, 1, T, ("d3", "d2", "d1")[x - 13])
    for (x, y) in ((5, 6), (10, 9), (6, 11)):
        put(img, x, y, "st2")
    return img


VILLAGE = [
    ("roof_tl", lambda: roof_tile(left=True, top=True)), ("roof_t", lambda: roof_tile(top=True)),
    ("roof_tr", lambda: roof_tile(right=True, top=True)), ("roof_ml", lambda: roof_tile(left=True)),
    ("roof_m", roof_tile), ("roof_mr", lambda: roof_tile(right=True)),
    ("roof_bl", lambda: roof_tile(left=True, bottom=True)), ("roof_b", lambda: roof_tile(bottom=True)),
    ("roof_br", lambda: roof_tile(right=True, bottom=True)), ("roof_chimney", lambda: roof_tile(chimney=True)),
    ("wall_up", wall_up), ("wall_up_window", lambda: wall_up(True)),
    ("wall_up_left", lambda: wall_up(edge="l")), ("wall_up_right", lambda: wall_up(edge="r")),
    ("wall_low", wall_low), ("wall_low_left", lambda: wall_low("l")), ("wall_low_right", lambda: wall_low("r")),
    ("door_top", door_top), ("door_bottom", door_bottom),
    ("fence_h", lambda: fence("h")), ("fence_h_left", lambda: fence("hl")), ("fence_h_right", lambda: fence("hr")),
    ("fence_v", lambda: fence("v")), ("bridge_h", lambda: bridge(True)), ("bridge_v", lambda: bridge(False)),
]


# ------------------------------------------------------------------ ruin tiles
def ruin_floor(variant):
    img = new(T, T)
    r = random.Random(40 + variant)
    rect(img, 0, 0, T, T, "st2")
    for i in range(T):
        for k in (7, 15):
            put(img, i, k, "st1"); put(img, k, i, "st1")
    for (cx, cy) in ((0, 0), (8, 0), (0, 8), (8, 8)):
        put(img, cx, cy, "st3"); put(img, cx + 1, cy, "st3"); put(img, cx, cy + 1, "st3")
    for _ in range(6):
        put(img, r.randrange(T), r.randrange(T), "st1" if variant != 1 else "st3")
    if variant == 2:   # cracked
        for (x, y) in ((3, 2), (4, 3), (5, 3), (5, 4), (6, 5), (7, 6), (8, 7), (9, 9), (10, 10), (10, 11), (11, 12), (12, 13)):
            put(img, x, y, "ink")
    if variant == 3:   # mossy
        for (x, y) in ((1, 1), (2, 1), (1, 2), (3, 2), (12, 12), (13, 12), (13, 13), (12, 14), (14, 5), (13, 6)):
            put(img, x, y, "g2")
        for (x, y) in ((2, 2), (13, 13), (14, 6)):
            put(img, x, y, "g3")
    return img


def wall_variant(kind):
    """Take the plain bottom-edge wall tile from the autotile set and modify its brick face."""
    bits = G.reduce_bits(G.N | G.NE | G.E | G.W | G.NW)
    tile = G.sheet_cache["ruin_wall"][G.BLOB_INDEX[bits]][0].copy()
    if kind == "cracked":
        for (x, y) in ((6, 5), (6, 6), (7, 7), (8, 8), (8, 9), (9, 10), (9, 11), (10, 11), (7, 9), (6, 10)):
            put(tile, x, y, "ink")
        for (x, y) in ((11, 7), (4, 8), (12, 9)):
            put(tile, x, y, "st1")
    elif kind == "doorway":
        for y in range(5, 14):
            for x in range(4, 12):
                put(tile, x, y, "ink")
        for (x, y) in ((4, 5), (11, 5)):
            put(tile, x, y, "st2")
        for x in range(3, 13):
            put(tile, x, 4, "st3")
        for y in range(4, 14):
            put(tile, 3, y, "st1"); put(tile, 12, y, "st1")
    return tile


def stairs_down():
    img = new(T, T)
    rect(img, 0, 0, T, T, "ink")
    bands = [("st3", "st2"), ("st2", "st1"), ("st1", "ink"), ("ink", "ink")]
    for i, (lit, shade) in enumerate(bands):
        y0 = i * 4
        rect(img, 1, y0, 14, 3, lit)
        rect(img, 1, y0 + 3, 14, 1, shade)
    for y in range(T):
        put(img, 0, y, "st1"); put(img, 15, y, "st1")
    return img


def pit():
    img = new(T, T)
    rect(img, 0, 0, T, T, "ink")
    ellipse(img, 8, 8, 5.5, 5.5, "m1")
    ellipse(img, 8, 8.5, 3.2, 3.2, "ink")
    r = random.Random(9)
    for _ in range(14):
        x, y = r.randrange(T), r.choice([0, 1, 14, 15, r.randrange(T)])
        if (x - 8) ** 2 + (y - 8) ** 2 > 38:
            put(img, x, y, "st1")
    for x in range(T):
        put(img, x, 0, "st2") if x % 3 else None
    return img


RUIN = [("floor_a", lambda: ruin_floor(0)), ("floor_b", lambda: ruin_floor(1)), ("floor_cracked", lambda: ruin_floor(2)),
        ("floor_moss", lambda: ruin_floor(3)), ("wall_cracked", lambda: wall_variant("cracked")),
        ("wall_doorway", lambda: wall_variant("doorway")), ("stairs_down", stairs_down), ("pit", pit)]


# ------------------------------------------------------------------ torch
def torch(frame):
    img = new(T, T)
    glow = new(T, T)
    layer = new(T, T)
    ellipse(layer, 8, 6, 7, 6, "e3")
    for y in range(T):
        for x in range(T):
            if layer.getpixel((x, y))[3]:
                put(glow, x, y, "e3", 26 if frame % 2 == 0 else 40)
    rect(img, 7, 8, 2, 6, "d2"); put(img, 7, 9, "d3")
    rect(img, 6, 7, 4, 2, "st1"); put(img, 6, 7, "st2")
    rect(img, 5, 13, 6, 2, "st1")
    flick = [(0, 0), (1, 1), (0, 2), (-1, 1)][frame]
    ox, h = flick[0], 5 + flick[1] % 2
    for yy in range(h):
        half = max(0.4, 2.2 - yy * 0.4)
        for xx in range(-3, 4):
            if abs(xx) <= half:
                c = "e4" if yy < 2 and abs(xx) < 1.2 else "e3" if yy < 4 else "e2"
                put(img, 8 + xx + (ox if yy > 1 else 0), 6 - yy, c)
    put(img, 8 + ox, 0 + frame, "e3")
    outline(img, "ink")
    glow.alpha_composite(img)
    return glow


# ------------------------------------------------------------------ props
def well():
    img = new(32, 32)
    rect(img, 5, 7, 2, 14, "d2"); rect(img, 25, 7, 2, 14, "d2")
    rect(img, 5, 7, 1, 14, "d3"); rect(img, 25, 7, 1, 14, "d3")
    rect(img, 5, 7, 22, 2, "d2"); rect(img, 5, 7, 22, 1, "d3")
    tri(img, (16, 0.5), (3, 8), (29, 8), "r2")
    tri(img, (16, 2), (7, 8), (16, 8), "r3")
    for y in (4, 6):
        for x in range(8, 25):
            if abs(x - 16) < (y - 1) * 2.6:
                put(img, x, y, "r1") if (x + y) % 4 == 0 else None
    G_ = __import__("gen_props")
    G_.lit_ellipse(img, 16, 22, 12, 7.5, ["st3", "st2", "st2", "st1"])
    ellipse(img, 16, 21, 8.5, 4.6, "w2")
    ellipse(img, 15, 20.5, 5, 2.6, "w3")
    put(img, 13, 20, "w4"); put(img, 14, 20, "w4")
    for x in range(5, 27):
        for y in range(25, 29):
            if img.getpixel((x, y))[3] and (x + y // 3) % 5 == 0:
                put(img, x, y, "st1")
    rect(img, 16, 9, 1, 8, "d1")
    rect(img, 15, 17, 3, 2, "d3")
    outline(img)
    return img


def barrel():
    img = new(T, T)
    G_ = __import__("gen_props")
    G_.lit_ellipse(img, 8, 9, 5.8, 6.2, ["d4", "d3", "d3", "d2"])
    for y in (5, 11):
        for x in range(2, 14):
            if img.getpixel((x, y))[3]:
                put(img, x, y, "st2")
                put(img, x, y + 1, "st1") if img.getpixel((x, y + 1))[3] else None
    ellipse(img, 8, 3.6, 4.6, 1.7, "d4")
    ellipse(img, 8, 3.8, 3.4, 1.0, "d2")
    outline(img)
    return img


def crate():
    img = new(T, T)
    rect(img, 1, 1, 14, 14, "d2")
    rect(img, 2, 2, 12, 12, "d3")
    for i in range(2, 14):
        put(img, i, 2, "d4"); put(img, 2, i, "d4")
        put(img, i, 13, "d2"); put(img, 13, i, "d2")
        put(img, i, i, "d2") if 3 < i < 12 else None
        put(img, 15 - i, i, "d2") if 3 < i < 12 else None
    outline(img)
    return img


def lamp_post(frame):
    img = new(16, 32)
    glow = new(16, 32)
    lit = frame > 0
    if lit:
        for rr, a in ((11, 22), (8, 40)):
            layer = new(16, 32)
            ellipse(layer, 8, 8, rr, rr, "e3")
            for y in range(32):
                for x in range(16):
                    if layer.getpixel((x, y))[3]:
                        put(glow, x, y, "e3", a)
    rect(img, 7, 12, 2, 18, "st1"); put(img, 7, 14, "st2"); put(img, 7, 20, "st2")
    rect(img, 5, 29, 6, 2, "st1"); rect(img, 6, 27, 4, 2, "st2")
    rect(img, 4, 3, 8, 2, "st2")
    tri(img, (8, 0), (3, 3), (13, 3), "st1")
    rect(img, 4, 5, 8, 7, "e4" if lit else "st1")
    if lit:
        rect(img, 5, 6, 6, 5, "e3")
        rect(img, 6 + (frame - 1), 6, 3, 3, "e4")
        put(img, 7, 10, "e2"); put(img, 9, 9, "e2")
    for y in range(5, 12):
        put(img, 4, y, "st2"); put(img, 11, y, "st1")
    rect(img, 4, 12, 8, 1, "st2")
    outline(img)
    glow.alpha_composite(img)
    return glow


def pillar():
    img = new(16, 24)
    rect(img, 2, 20, 12, 4, "st2"); rect(img, 2, 20, 12, 1, "st3"); rect(img, 2, 23, 12, 1, "st1")
    rect(img, 4, 3, 8, 17, "st2"); rect(img, 4, 3, 2, 17, "st3"); rect(img, 10, 3, 2, 17, "st1")
    rect(img, 2, 0, 12, 4, "st2"); rect(img, 2, 0, 12, 1, "st3"); rect(img, 2, 3, 12, 1, "st1")
    for (x, y) in ((6, 8), (7, 9), (7, 10), (8, 14), (7, 15)):
        put(img, x, y, "st1")
    put(img, 5, 12, "g2"); put(img, 5, 13, "g2"); put(img, 6, 13, "g3")
    outline(img)
    return img


def pillar_broken():
    img = new(16, 24)
    rect(img, 2, 18, 12, 4, "st2"); rect(img, 2, 18, 12, 1, "st3"); rect(img, 2, 21, 12, 1, "st1")
    rect(img, 4, 13, 8, 5, "st2"); rect(img, 4, 13, 2, 5, "st3"); rect(img, 10, 13, 2, 5, "st1")
    for (x, y) in ((4, 12), (6, 11), (7, 12), (9, 12), (10, 11), (11, 12)):
        put(img, x, y, "st2")
    for (x, y) in ((5, 12), (8, 11), (10, 12)):
        put(img, x, y, "st3")
    for (x, y) in ((1, 21), (13, 22), (14, 21), (0, 22)):
        put(img, x, y, "st2")
    outline(img)
    return img


def rubble():
    img = new(16, 24)
    for (cx, cy, rx, ry) in ((5, 20, 3.5, 2.5), (10.5, 21, 4, 2.8), (8, 18.5, 2.8, 2.2), (13, 19.5, 2, 1.6)):
        G_ = __import__("gen_props")
        G_.lit_ellipse(img, cx, cy, rx, ry, ["st3", "st2", "st2", "st1"])
    outline(img)
    return img


def cobweb():
    img = new(16, 24)
    for k in range(10):
        put(img, k, 0 + (k * 0), "white", 200)
        put(img, 0, k, "white", 200)
    for k in range(9):
        put(img, k, k, "white", 200)
    for (x, y) in ((4, 1), (5, 2), (6, 3), (1, 4), (2, 5), (3, 6), (3, 3), (4, 4), (2, 2), (1, 1)):
        put(img, x, y, "white", 150)
    for (x, y) in ((7, 1), (8, 2), (9, 3), (1, 7), (2, 8), (3, 9)):
        put(img, x, y, "white", 130)
    return img


VILLAGE_PROPS = [("well", well, (32, 32)), ("barrel", barrel, (16, 16)), ("crate", crate, (16, 16))]


# ------------------------------------------------------------------ output
def atlas(items, cols=8):
    sheet = new(cols * T, ((len(items) + cols - 1) // cols) * T)
    for i, (_, fn) in enumerate(items):
        paste(sheet, fn(), (i % cols) * T, (i // cols) * T)
    return sheet


def main():
    G.main()                                   # builds sheet_cache for the wall variants (and refreshes terrain)
    for n in ("ruin_wall",):
        G.build_terrain(n)
    village = atlas(VILLAGE)
    ruin = atlas(RUIN)
    village.save(TS / "village.png")
    ruin.save(TS / "ruin.png")
    tor = new(4 * T, T)
    for i in range(4):
        paste(tor, torch(i), i * T, 0)
    tor.save(TS / "torch.png")

    PR.mkdir(parents=True, exist_ok=True)
    vp = new(32 + 16 + 16 + 3 * 16, 32)
    paste(vp, well(), 0, 0)
    paste(vp, barrel(), 32, 0)
    paste(vp, crate(), 48, 0)
    for i in range(3):
        paste(vp, lamp_post(i), 64 + i * 16, 0)
    vp.save(PR / "village_props.png")
    rp = new(4 * 16, 24)
    for i, fn in enumerate((pillar, pillar_broken, rubble, cobweb)):
        paste(rp, fn(), i * 16, 0)
    rp.save(PR / "ruin_props.png")

    meta = dict(
        village=dict(cell=16, columns=8, order=[n for n, _ in VILLAGE]),
        ruin=dict(cell=16, columns=8, order=[n for n, _ in RUIN]),
        torch=dict(frames=4, fps=8, cell=16),
        village_props=dict(well=[0, 0, 32, 32], barrel=[32, 0, 16, 16], crate=[48, 0, 16, 16],
                           lamp_post=dict(cell=[16, 32], x0=64, frames=3, note="0 unlit, 1-2 lit flicker")),
        ruin_props=dict(cell=[16, 24], order=["pillar", "pillar_broken", "rubble", "cobweb"]),
    )
    (BUILD / "village_meta.json").write_text(json.dumps(meta, indent=1))

    # ---- preview: a little village square and a ruin room built from the tiles
    names = {n: i for i, (n, _) in enumerate(VILLAGE)}
    vt = lambda n: village.crop(((names[n] % 8) * T, (names[n] // 8) * T, (names[n] % 8) * T + T, (names[n] // 8) * T + T))
    rn = {n: i for i, (n, _) in enumerate(RUIN)}
    rt = lambda n: ruin.crop(((rn[n] % 8) * T, (rn[n] // 8) * T, (rn[n] % 8) * T + T, (rn[n] // 8) * T + T))
    board = new(20 * T, 11 * T)
    for y in range(11):
        for x in range(20):
            paste(board, G.grass_sheet().crop(((x * 3 + y) % 4 * T, 0, ((x * 3 + y) % 4) * T + T, T)), x * T, y * T)
    # cobbled square
    cob = ["cccccccc", "cccccccc", "cccccccc", "cccccccc"]
    for y in range(4):
        for x in range(8):
            ch_map = ["c" * 8] * 4
    for y in range(4):
        for x in range(8):
            b = 0
            for flag, (dx, dy) in ((G.N, (0, -1)), (G.NE, (1, -1)), (G.E, (1, 0)), (G.SE, (1, 1)),
                                   (G.S, (0, 1)), (G.SW, (-1, 1)), (G.W, (-1, 0)), (G.NW, (-1, -1))):
                if 0 <= x + dx < 8 and 0 <= y + dy < 4 or True:
                    b |= flag if (0 <= x + dx < 8 and 0 <= y + dy < 4) else 0
            tile = G.sheet_cache["cobble"][G.BLOB_INDEX[G.reduce_bits(b)]][0]
            paste(board, tile, (6 + x) * T, (6 + y) * T)
    # house: roof 4x3, walls 4x2 with a door
    hx, hy = 1, 1
    rows = [["roof_tl", "roof_t", "roof_t", "roof_tr"], ["roof_ml", "roof_m", "roof_chimney", "roof_mr"],
            ["roof_bl", "roof_b", "roof_b", "roof_br"],
            ["wall_up_left", "wall_up_window", "wall_up", "wall_up_right"],
            ["wall_low_left", "wall_low", "door_bottom", "wall_low_right"]]
    for ry, row in enumerate(rows):
        for rx, n in enumerate(row):
            paste(board, vt(n), (hx + rx) * T, (hy + ry) * T)
    paste(board, vt("door_top"), (hx + 2) * T, (hy + 3) * T)
    for i in range(5):
        paste(board, vt("fence_h"), (hx + i - 1 + 0) * T, (hy + 6) * T) if i not in (0,) else None
    paste(board, vt("fence_h_left"), (hx - 1) * T, (hy + 6) * T)
    paste(board, vt("fence_h_right"), (hx + 4) * T, (hy + 6) * T)
    pv = Image_open(PR / "village_props.png")
    paste(board, pv.crop((0, 0, 32, 32)), 14 * T, 1 * T)
    paste(board, pv.crop((32, 0, 48, 16)), 11 * T, 2 * T)
    paste(board, pv.crop((48, 0, 64, 16)), 12 * T, 2 * T + 4)
    paste(board, pv.crop((80, 0, 96, 32)), 6 * T - 4, 3 * T)
    # ruin room on the right-bottom: wall blob + floor
    for y in range(6, 11):
        for x in range(13, 20):
            paste(board, rt("floor_a" if (x + y) % 3 else "floor_b"), x * T, y * T)
    paste(board, rt("floor_cracked"), 15 * T, 8 * T)
    paste(board, rt("floor_moss"), 18 * T, 7 * T)
    paste(board, rt("stairs_down"), 14 * T, 6 * T)
    paste(board, rt("pit"), 17 * T, 9 * T)
    for x in range(13, 20):
        paste(board, rt("wall_cracked") if x == 16 else rt("wall_doorway") if x == 18 else G.sheet_cache["ruin_wall"][G.BLOB_INDEX[G.reduce_bits(G.N | G.NE | G.E | G.W | G.NW)]][0], x * T, 5 * T)
    paste(board, torch(0), 14 * T, 5 * T)
    paste(board, torch(2), 20 * T - T * 1, 5 * T) if False else None
    pr = Image_open(PR / "ruin_props.png")
    paste(board, pr.crop((0, 0, 16, 24)), 13 * T, 7 * T - 8)
    paste(board, pr.crop((16, 0, 32, 24)), 19 * T - 16, 8 * T)
    paste(board, pr.crop((32, 0, 48, 24)), 16 * T, 9 * T - 8)
    scaled(on_bg(board, (60, 90, 60, 255)), 3).save(PREV / "village_ruin_preview.png")
    print("village/ruin done")


def Image_open(p):
    from PIL import Image
    return Image.open(p).convert("RGBA")


if __name__ == "__main__":
    main()
