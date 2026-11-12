"""Player's house interior + diary UI.

assets/tilesets/interior.png     16x16 tiles, 8 columns (order in INTERIOR below, also in tools/build/interior_meta.json)
assets/props/interior_props.png  fixed layout, see RECTS (scripts/game/furniture.gd uses the same rectangles)
assets/ui/diary_book.png         224x137 open diary (left page / right page, ribbon)
assets/ui/checkbox.png           7x7 x2 (empty, ticked)
assets/fx/light_shaft.png        48x64 morning light from a window
"""
import json
import random
from pathlib import Path

from pxl import T, new, put, rect, paste, scaled, on_bg, ellipse, tri, outline
from gen_props import lit_ellipse, GREEN

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "tools" / "build"
PREV = ROOT / "tools" / "previews"


# ------------------------------------------------------------------ tiles
def floor_tile(v):
    img = new(T, T)
    r = random.Random(70 + v)
    rect(img, 0, 0, T, T, "d3")
    for y in range(T):
        if y % 4 == 3:
            for x in range(T):
                put(img, x, y, "d2")
    for row in range(4):                       # staggered plank ends
        jx = (row * 5 + v * 3 + 2) % 16
        for y in range(row * 4, row * 4 + 3):
            put(img, jx, y, "d2")
    for _ in range(7):
        put(img, r.randrange(T), r.randrange(T), "d4" if r.random() < 0.6 else "d2")
    if v == 2:                                 # a knot in the wood
        ellipse(img, 10, 6, 2.4, 1.6, "d2")
        put(img, 10, 6, "d1")
    if v == 1:
        for x in range(1, 8):
            put(img, x, 1, "d4")
    return img


def wall_plain(window=False):
    img = new(T, T)
    rect(img, 0, 0, T, T, "s3")
    r = random.Random(5)
    for _ in range(12):
        put(img, r.randrange(T), r.randrange(3, T), "s2")
    rect(img, 0, 0, T, 3, "d2")
    for x in range(T):
        put(img, x, 0, "d3")
        put(img, x, 2, "d1")
    if window:
        rect(img, 2, 3, 12, 12, "d1")
        rect(img, 3, 4, 10, 10, "w4")
        for y in range(4, 14):
            for x in range(3, 13):
                if y > 9:
                    put(img, x, y, "w3")
        for (x, y) in ((4, 5), (5, 5), (4, 6)):
            put(img, x, y, "white")
        for i in range(3, 13):
            put(img, 7, i + 1 if i < 12 else i, "d2")
            put(img, 8, i + 1 if i < 12 else i, "d2")
        for i in range(3, 13):
            put(img, i, 9, "d2")
        rect(img, 1, 14, 14, 2, "d3")
        for x in range(1, 15):
            put(img, x, 14, "d4")
            put(img, x, 15, "d1")
    return img


def wall_wains():
    img = new(T, T)
    rect(img, 0, 0, T, T, "d2")
    for x in range(T):
        put(img, x, 0, "d4")
        put(img, x, 1, "d3")
        put(img, x, 14, "d1")
        put(img, x, 15, "d1")
    for x in range(1, T, 4):
        for y in range(3, 14):
            put(img, x, y, "d1")
            put(img, x + 1, y, "d3") if y % 5 else None
    return img


def side_wall(left=True):
    img = new(T, T)
    rect(img, 0, 0, T, T, "d1")
    for y in range(T):
        for x in range(T):
            if (y // 4) % 2 == 0 and x % 5 == 0:
                put(img, x, y, "d2")
    inner = 15 if left else 0
    for y in range(T):
        put(img, inner, y, "ink")
        put(img, inner + (-1 if left else 1), y, "d2")
        put(img, inner + (-2 if left else 2), y, "d3")
    return img


def bottom_band():
    img = new(T, T)
    rect(img, 0, 0, T, T, "d1")
    for x in range(T):
        put(img, x, 0, "ink")
        put(img, x, 1, "d3")
        put(img, x, 2, "d2")
    for y in range(3, T, 4):
        for x in range(T):
            put(img, x, y, "d2")
    return img


def door_exit():
    img = new(T, T)
    for y in range(T):                          # floor with a welcome mat
        for x in range(T):
            put(img, x, y, "d3" if y % 4 != 3 else "d2")
    rect(img, 2, 1, 12, 8, "r1")
    rect(img, 3, 2, 10, 6, "r2")
    for (x, y) in ((8, 3), (7, 4), (8, 4), (9, 4), (8, 5), (6, 6), (10, 6)):
        put(img, x, y, "e3")
    rect(img, 0, 10, T, 6, "w4")                # bright doorway (daylight outside)
    for y in range(10, 16):
        for x in range(T):
            if y > 12:
                put(img, x, y, "white")
    rect(img, 0, 10, 2, 6, "d2"); rect(img, 14, 10, 2, 6, "d2")
    for x in range(T):
        put(img, x, 9, "d1")
    return img


INTERIOR = [("floor_a", lambda: floor_tile(0)), ("floor_b", lambda: floor_tile(1)), ("floor_c", lambda: floor_tile(2)),
            ("wall_plain", wall_plain), ("wall_window", lambda: wall_plain(True)), ("wall_wains", wall_wains),
            ("side_left", lambda: side_wall(True)), ("side_right", lambda: side_wall(False)),
            ("bottom_band", bottom_band), ("door_exit", door_exit)]


# ------------------------------------------------------------------ props (rect = x, y, w, h in the sheet)
RECTS = {
    "bed_asleep": (0, 0, 24, 32), "bed_sit": (32, 0, 24, 32), "bed_empty": (64, 0, 24, 32),
    "desk": (96, 0, 32, 24), "hearth": (128, 0, 32, 32),            # hearth: 4 frames, 32 px apart
    "shelf": (0, 32, 32, 32), "rug": (32, 32, 32, 24), "table": (64, 32, 16, 16), "chair": (80, 32, 16, 16),
    "plant": (96, 32, 16, 24), "trunk": (112, 32, 16, 16),
}


def bed(state):
    img = new(24, 32)
    rect(img, 0, 0, 24, 32, "d2")
    rect(img, 0, 0, 24, 4, "d3")
    for x in range(24):
        put(img, x, 0, "d4")
    rect(img, 2, 4, 20, 26, "s3")                              # mattress sheet
    rect(img, 3, 5, 18, 7, "white")                            # pillow
    for x in range(3, 21):
        put(img, x, 11, "st3")
    rect(img, 0, 30, 24, 2, "d2")
    top = {"asleep": 12, "sit": 18, "empty": 15}[state]
    rect(img, 2, top, 20, 30 - top, "b2")
    for x in range(2, 22):
        put(img, x, top, "b3")
        put(img, x, 29, "b1")
    for y in range(top, 30):
        put(img, 2, y, "b3")
        put(img, 21, y, "b1")
    if state == "empty":
        tri(img, (2, top), (13, top), (2, top + 9), "b3")      # blanket thrown back
        tri(img, (2, top + 9), (13, top), (6, top + 9), "b1")
        for x in range(5, 19):
            put(img, x, 8, "st3") if x % 3 else None           # dent in the pillow
    if state == "asleep":
        ellipse(img, 12, 8.5, 4.6, 3.8, "sk2")                 # head on the pillow
        rect(img, 7, 4, 10, 3, "d2")
        for (x, y) in ((7, 7), (8, 8), (16, 7), (15, 8), (9, 5), (14, 5)):
            put(img, x, y, "d2")
        put(img, 9, 4, "d3"); put(img, 10, 4, "d3")
        for (x, y) in ((10, 9), (11, 9), (14, 9), (13, 9)):    # closed eyes
            put(img, x, y, "ink")
        put(img, 12, 11, "sk1")
    if state == "sit":
        rect(img, 7, 14, 10, 6, "b2")                          # sitting up: shoulders over the blanket
        for x in range(7, 17):
            put(img, x, 14, "b3")
        put(img, 5, 16, "sk2"); put(img, 18, 16, "sk2")
        ellipse(img, 12, 9.5, 4.6, 4.2, "sk2")
        rect(img, 7, 4, 10, 4, "d2")
        for (x, y) in ((7, 8), (8, 9), (16, 8), (15, 9), (8, 5), (15, 5), (10, 4), (13, 4)):
            put(img, x, y, "d2")
        put(img, 10, 4, "d3"); put(img, 11, 4, "d3")
        for (x, y) in ((10, 10), (14, 10)):
            put(img, x, y, "ink"); put(img, x, y - 1, "white")
        put(img, 12, 13, "sk1")
        for x in (11, 12, 13):
            put(img, x, 12, "sk1")
    outline(img)
    return img


def desk():
    img = new(32, 24)
    rect(img, 0, 0, 32, 9, "d4")
    rect(img, 0, 8, 32, 2, "d2")
    rect(img, 1, 10, 30, 13, "d3")
    for x in range(1, 31):
        put(img, x, 10, "d2")
    for (x0, x1) in ((3, 14), (17, 28)):
        rect(img, x0, 12, x1 - x0, 8, "d2")
        rect(img, x0 + 1, 13, x1 - x0 - 2, 6, "d3")
        put(img, (x0 + x1) // 2, 16, "e3")
    rect(img, 3, 1, 10, 7, "r1")                                # the diary, closed, on the desk
    rect(img, 4, 2, 8, 5, "r2")
    for y in range(1, 8):
        put(img, 3, y, "r1")
    put(img, 11, 4, "e3"); put(img, 11, 5, "e3")
    rect(img, 4, 2, 7, 1, "r3")
    rect(img, 18, 2, 8, 6, "white")                             # loose paper, ink and quill
    for y in (3, 5):
        for x in range(19, 25):
            put(img, x, y, "st3")
    rect(img, 27, 4, 3, 3, "st1")
    for k in range(5):
        put(img, 28 + k // 3, 3 - k, "white")
    outline(img)
    return img


def hearth(frame):
    img = new(32, 32)
    rect(img, 0, 6, 32, 26, "st2")
    for y in range(6, 32):
        off = ((y // 4) % 2) * 4
        for x in range(32):
            if y % 4 == 3 or (x + off) % 8 == 7:
                put(img, x, y, "st1")
            elif y % 4 == 0 and (x + off) % 8 in (1, 2):
                put(img, x, y, "st3")
    rect(img, 0, 2, 32, 5, "st3")
    for x in range(32):
        put(img, x, 6, "st1")
    rect(img, 6, 12, 20, 20, "ink")
    ellipse(img, 16, 14, 10, 6, "ink")
    glow = [(0, 0), (1, 1), (0, 2), (-1, 1)][frame]
    for (cx, cy, rx, ry, c) in ((16 + glow[0], 27, 7, 5, "e1"), (16 + glow[0], 26 - glow[1] % 2, 5, 5 + glow[1] % 2, "e2"),
                                (16 - glow[0], 27, 3, 3 + (frame % 2), "e3")):
        ellipse(img, cx, cy, rx, ry, c)
    rect(img, 8, 29, 16, 3, "d2")                               # logs
    put(img, 12, 29, "d3"); put(img, 18, 30, "d1")
    ellipse(img, 16, 28, 3, 2, "e4") if frame % 2 == 0 else ellipse(img, 15, 27, 2, 2, "e4")
    outline(img)
    return img


def shelf():
    img = new(32, 32)
    rect(img, 0, 0, 32, 32, "d2")
    rect(img, 1, 1, 30, 30, "d1")
    for y in (10, 21):
        rect(img, 1, y, 30, 2, "d3")
    colors = ["r2", "b2", "g2", "e2", "m2", "r3", "b3", "g3"]
    r = random.Random(11)
    for (y0, y1) in ((2, 10), (13, 21), (24, 31)):
        x = 2
        while x < 29:
            w = r.choice([2, 2, 3, 3, 4])
            h = r.randrange(5, y1 - y0 + 1)
            c = r.choice(colors)
            rect(img, x, y1 - h, w, h, c)
            put(img, x, y1 - h, "white") if w > 2 else None
            x += w + (1 if r.random() < 0.5 else 0)
    outline(img)
    return img


def rug():
    img = new(32, 24)
    rect(img, 0, 2, 32, 20, "r1")
    rect(img, 2, 4, 28, 16, "r2")
    rect(img, 4, 6, 24, 12, "r1")
    rect(img, 5, 7, 22, 10, "r2")
    for k in range(4):
        x = 8 + k * 5
        for (dx, dy) in ((0, 0), (-1, 1), (1, 1), (0, 2), (0, 1)):
            put(img, x + dx, 11 + dy, "e3" if (dx, dy) == (0, 1) else "e1")
    for y in range(3, 21, 2):
        put(img, 0, y, "white"); put(img, 31, y, "white")
    return img


def table():
    img = new(16, 16)
    rect(img, 1, 7, 14, 3, "d4")
    rect(img, 2, 10, 12, 5, "d2")
    rect(img, 3, 11, 10, 3, "d3")
    put(img, 8, 12, "e3")
    for y in range(11, 16):
        put(img, 2, y, "d3")
    rect(img, 5, 1, 6, 6, "st1")                                 # the bedside lantern (unlit)
    rect(img, 6, 2, 4, 4, "st2")
    put(img, 6, 2, "st3")
    rect(img, 6, 0, 4, 1, "d1")
    outline(img)
    return img


def chair():
    img = new(16, 16)
    rect(img, 3, 0, 10, 9, "d2")
    for x in (5, 8, 11):
        for y in range(1, 8):
            put(img, x, y, "d1")
    rect(img, 2, 8, 12, 3, "d3")
    put(img, 3, 8, "d4")
    for x in range(2, 14):
        put(img, x, 8, "d4")
    rect(img, 3, 11, 2, 5, "d1"); rect(img, 11, 11, 2, 5, "d1")
    outline(img)
    return img


def plant():
    img = new(16, 24)
    rect(img, 4, 15, 8, 8, "d3")
    rect(img, 3, 14, 10, 2, "d4")
    for y in range(16, 23):
        put(img, 4, y, "d4"); put(img, 11, y, "d2")
    for (cx, cy, rx, ry) in ((5, 9, 4, 5), (11, 9, 4, 5), (8, 5, 4.5, 5.5)):
        lit_ellipse(img, cx, cy, rx, ry, GREEN)
    outline(img)
    return img


def trunk():
    img = new(16, 16)
    rect(img, 1, 4, 14, 11, "d3")
    rect(img, 1, 3, 14, 3, "d4")
    for x in (3, 12):
        for y in range(3, 15):
            put(img, x, y, "st2")
    rect(img, 7, 7, 2, 3, "e3")
    for x in range(1, 15):
        put(img, x, 13, "d2")
    outline(img)
    return img


def props_sheet():
    sheet = new(256, 96)
    pieces = [("bed_asleep", bed("asleep")), ("bed_sit", bed("sit")), ("bed_empty", bed("empty")), ("desk", desk()),
              ("shelf", shelf()), ("rug", rug()), ("table", table()), ("chair", chair()), ("plant", plant()),
              ("trunk", trunk())]
    for name, im in pieces:
        x, y, w, h = RECTS[name]
        paste(sheet, im, x, y)
    x, y, _, _ = RECTS["hearth"]
    for f in range(4):
        paste(sheet, hearth(f), x + f * 32, y)
    return sheet


def light_shaft():
    img = new(48, 64)
    tri(img, (0, 0), (16, 0), (40, 62), "e4")
    tri(img, (16, 0), (24, 62), (40, 62), "e4")
    for y in range(64):
        for x in range(48):
            p = img.getpixel((x, y))
            if p[3]:
                a = int(70 * (1 - y / 70))
                img.putpixel((x, y), p[:3] + (a,))
    return img


# ------------------------------------------------------------------ UI: diary
def diary_book():
    W, H = 224, 137
    img = new(W, H)
    rect(img, 0, 1, W, 133, "ink")                              # cover
    rect(img, 1, 2, W - 2, 131, "d2")
    rect(img, 1, 2, W - 2, 1, "d3")
    rect(img, 3, 4, W - 6, 127, "d1")
    for (x, y) in ((0, 1), (W - 1, 1), (0, 133), (W - 1, 133)):
        img.putpixel((x, y), (0, 0, 0, 0))
    left, right = (6, 6, 104, 124), (114, 6, 104, 124)
    r = random.Random(21)
    for (x, y, w, h) in (left, right):
        rect(img, x, y, w, h, "s3")
        for _ in range(60):
            put(img, r.randrange(x + 1, x + w - 1), r.randrange(y + 1, y + h - 1), "s2")
        for yy in range(30, 118, 9):                            # faint ruled lines
            for xx in range(x + 8, x + w - 8):
                put(img, xx, yy, "s2")
    for k in range(6):                                          # gutter shading
        c = ("s1", "s2", "s2", "s3", "s3", "s3")[k]
        for y in range(6, 130):
            put(img, 109 - k + 0, y, c) if k < 3 else None
    for y in range(6, 130):
        put(img, 109, y, "s1"); put(img, 110, y, "d1"); put(img, 111, y, "d1"); put(img, 112, y, "s1"); put(img, 113, y, "s2")
        put(img, 108, y, "s2"); put(img, 107, y, "s3")
    for k in range(3):                                          # page-edge thickness at the bottom
        for x in range(8 + k, 108):
            put(img, x, 130 - 0 + (k if k < 2 else 0) - (0 if k < 2 else 0), "s2") if (x + k) % 2 else None
    for x in range(7, 109):
        put(img, x, 130, "s1")
    for x in range(115, 217):
        put(img, x, 130, "s1")
    for (x, y) in ((4, 5), (W - 6, 5), (4, 129), (W - 6, 129)):  # brass corners
        rect(img, x, y, 2, 2, "e3")
    tri(img, (216, 112), (216, 130), (198, 130), "s2")          # curled corner
    tri(img, (216, 112), (216, 130), (205, 130), "s1")
    rect(img, 110, 128, 4, 9, "r2")                             # ribbon marker
    put(img, 110, 136, "r1"); put(img, 113, 136, "r1")
    for y in range(128, 136):
        put(img, 110, y, "r3")
    return img


def checkbox():
    img = new(14, 7)
    for i, ticked in enumerate((False, True)):
        x0 = i * 7
        for k in range(7):
            put(img, x0 + k, 0, "d1"); put(img, x0 + k, 6, "d1")
            put(img, x0, k, "d1"); put(img, x0 + 6, k, "d1")
        rect(img, x0 + 1, 1, 5, 5, "s3")
        if ticked:
            for (dx, dy) in ((1, 3), (2, 4), (3, 3), (4, 2), (5, 1)):
                put(img, x0 + dx, dy, "g2")
                put(img, x0 + dx, dy - 1 if dy > 1 else dy, "g2") if dx >= 3 else None
    return img


# ------------------------------------------------------------------ output
def main():
    (ROOT / "assets" / "ui").mkdir(parents=True, exist_ok=True)
    tiles = new(8 * T, ((len(INTERIOR) + 7) // 8) * T)
    for i, (_, fn) in enumerate(INTERIOR):
        paste(tiles, fn(), (i % 8) * T, (i // 8) * T)
    tiles.save(ROOT / "assets" / "tilesets" / "interior.png")
    props = props_sheet()
    props.save(ROOT / "assets" / "props" / "interior_props.png")
    book = diary_book()
    book.save(ROOT / "assets" / "ui" / "diary_book.png")
    checkbox().save(ROOT / "assets" / "ui" / "checkbox.png")
    light_shaft().save(ROOT / "assets" / "fx" / "light_shaft.png")
    (BUILD / "interior_meta.json").write_text(json.dumps(dict(
        tiles=dict(cell=16, columns=8, order=[n for n, _ in INTERIOR]), props=RECTS), indent=1))

    # preview: a room assembled from the tiles and props
    names = {n: i for i, (n, _) in enumerate(INTERIOR)}
    t = lambda n: tiles.crop(((names[n] % 8) * T, (names[n] // 8) * T, (names[n] % 8) * T + T, (names[n] // 8) * T + T))
    room = new(16 * T, 10 * T)
    for y in range(10):
        for x in range(16):
            if y == 0:
                n = "side_left" if x == 0 else "side_right" if x == 15 else ("wall_window" if x in (5, 9) else "wall_plain")
            elif y == 1:
                n = "side_left" if x == 0 else "side_right" if x == 15 else "wall_wains"
            elif y == 9:
                n = "door_exit" if x == 7 else "bottom_band"
            elif x == 0 or x == 15:
                n = "side_left" if x == 0 else "side_right"
            else:
                n = ("floor_a", "floor_a", "floor_b", "floor_c")[(x * 3 + y * 5) % 4]
            paste(room, t(n), x * T, y * T)
    sh = light_shaft()
    paste(room, sh, 5 * T - 4, 2 * T - 4)
    paste(room, sh, 9 * T - 4, 2 * T - 4)
    crop = lambda k, f=0: props.crop((RECTS[k][0] + f * 32, RECTS[k][1], RECTS[k][0] + f * 32 + RECTS[k][2], RECTS[k][1] + RECTS[k][3]))
    paste(room, crop("rug"), 6 * T, 5 * T + 4)
    paste(room, crop("bed_asleep"), 28, 32)
    paste(room, crop("table"), 60, 32)
    paste(room, crop("hearth"), 104, 32)
    paste(room, crop("desk"), 144, 32)
    paste(room, crop("shelf"), 196, 32)
    paste(room, crop("chair"), 120, 62)
    paste(room, crop("plant"), 216, 100)
    paste(room, crop("trunk"), 20, 110)
    board = new(16 * T + 8 + 224, 10 * T)
    paste(board, room, 0, 0)
    paste(board, book, 16 * T + 8, 0)
    scaled(on_bg(board, (30, 30, 46, 255)), 3).save(PREV / "interior_preview.png")
    extra = new(16 * 6, 32)
    for i, n in enumerate(("bed_asleep", "bed_sit", "bed_empty")):
        paste(extra, crop(n), i * 28, 0)
    for f in range(3):
        paste(extra, crop("hearth", f), 90 + f * 34, 0)
    scaled(on_bg(extra, (60, 90, 60, 255)), 6).save(PREV / "interior_props_zoom.png")
    print("interior done")


if __name__ == "__main__":
    main()
