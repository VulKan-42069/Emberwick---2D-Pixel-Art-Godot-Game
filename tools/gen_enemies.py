"""Enemies: mist slime (hop), mist bat (fly), shade (ruin wraith). All use the night-mist purple family.

slime.png  16x16 cells, 1 row  x 4 frames (squash, stretch, airborne, land)
bat.png    16x16 cells, 1 row  x 4 frames (wings up, mid, down, mid)
shade.png  16x24 cells, 4 rows (down, up, left, right) x 4 frames (float + hem ripple)
"""
import json
import math
from pathlib import Path

from PIL import Image

from pxl import new, put, paste, scaled, on_bg, ellipse, tri, outline

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "enemies"
BUILD = ROOT / "tools" / "build"
PREV = ROOT / "tools" / "previews"


def mirror(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)


# ------------------------------------------------------------------ mist slime
SLIME = [  # cx, cy, rx, ry
    (8, 12.0, 6.0, 3.4),   # squash
    (8, 8.5, 4.2, 6.0),    # stretch (take-off)
    (8, 7.0, 5.0, 4.6),    # airborne
    (8, 12.4, 6.4, 3.0),   # landing splat
]


def slime_frame(i):
    cx, cy, rx, ry = SLIME[i]
    img = new(16, 16)
    ellipse(img, cx, cy, rx, ry, "m2")
    for y in range(16):                                   # shaded underside, lit top-left
        for x in range(16):
            if img.getpixel((x, y))[3]:
                if y + 0.5 > cy + ry * 0.35 or (x + 0.5 > cx + rx * 0.55 and y + 0.5 > cy - ry * 0.2):
                    put(img, x, y, "m1")
    ellipse(img, cx - rx * 0.35, cy - ry * 0.45, max(1.0, rx * 0.28), max(1.0, ry * 0.25), "m3")
    put(img, int(cx - rx * 0.45), int(cy - ry * 0.55), "white")
    ey = int(cy - ry * 0.05)
    for ex in (int(cx - rx * 0.4), int(cx + rx * 0.25)):   # eyes: white with a dark pupil
        put(img, ex, ey, "white"); put(img, ex + 1, ey, "white")
        put(img, ex, ey + 1, "ink"); put(img, ex + 1, ey + 1, "ink")
    top = int(cy - ry)
    for (dx, dy) in ((-2, -1), (1, -2), (3, -1)):          # mist wisps rising off it
        put(img, int(cx) + dx, top + dy + 1, "m3", 170)
    outline(img)
    return img


# ------------------------------------------------------------------ mist bat
WINGS = [  # (left wing triangle, y of the body centre)
    [((6, 7), (0.5, 2), (2.5, 9)), 8],           # up
    [((6, 8), (0, 7), (2.5, 11)), 8],            # mid
    [((6, 9), (1, 14), (3.5, 8)), 9],            # down
    [((6, 8), (0, 7), (2.5, 11)), 8],            # mid
]


def bat_frame(i):
    img = new(16, 16)
    pts, by = WINGS[i]
    for sign in (1, -1):
        p = [((x if sign == 1 else 16 - x), y) for (x, y) in pts]
        tri(img, *p, "m2")
        tri(img, p[0], p[1], ((p[0][0] + p[1][0]) / 2, (p[0][1] + p[1][1]) / 2 + 1.5), "m3")  # lit wing edge
        put(img, int(p[2][0]) if sign == 1 else int(p[2][0]) - 1, int(p[2][1]), "m1")
    ellipse(img, 8, by, 2.6, 3.2, "m1")
    ellipse(img, 7.6, by - 0.6, 1.4, 1.8, "m2")
    tri(img, (5.8, by - 2), (6.2, by - 4.6), (7.4, by - 2.6), "m1")      # ears
    tri(img, (10.2, by - 2), (9.8, by - 4.6), (8.6, by - 2.6), "m1")
    put(img, 7, by - 1, "e3"); put(img, 9, by - 1, "e3")                 # ember eyes
    put(img, 8, by + 1, "white")                                         # little fang
    outline(img)
    return img


# ------------------------------------------------------------------ shade
def shade_frame(d, i):
    img = new(16, 24)
    bob = (0, 1, 1, 0)[i]
    wave = i * math.pi / 2
    narrow = 1 if d == "right" else 0
    # cloak
    for y in range(9, 23):
        t = (y - 9) / 13
        half = 3.3 + t * (3.3 - narrow * 1.4)
        shift = 0.0 if d != "right" else -t * 1.2
        for x in range(16):
            cx = 8 + shift
            if abs(x + 0.5 - cx) <= half:
                put(img, x, y + bob, "m2")
    # ragged hem: cut the bottom edge per column with a travelling wave
    for x in range(16):
        edge = 21 + round(1.6 * math.sin(wave + x * 0.9)) + bob
        for y in range(edge + 1, 24):
            img.putpixel((x, y), (0, 0, 0, 0))
    for x in range(16):                                    # shade the far side and the folds
        for y in range(9, 24):
            if img.getpixel((x, y))[3]:
                if x >= 10 - narrow or (x == 7 and y > 14 and y % 3 == 0):
                    put(img, x, y, "m1")
                elif x <= 5 and y > 11:
                    put(img, x, y, "m3" if x == 4 else "m2")
    # hood
    ellipse(img, 8, 6.5 + bob, 4.4 - narrow * 0.6, 5.2, "m2")
    for y in range(24):
        for x in range(16):
            if img.getpixel((x, y))[3] and 1 <= y <= 10 and (x >= 10 - narrow):
                put(img, x, y, "m1")
    # face void and eyes
    if d == "down":
        ellipse(img, 8, 7.6 + bob, 2.8, 3.0, "ink")
        for ex in (6, 9):
            put(img, ex, 7 + bob, "e4"); put(img, ex + 1, 7 + bob, "e3")
    elif d == "right":
        ellipse(img, 10, 7.6 + bob, 2.2, 3.0, "ink")
        put(img, 10, 7 + bob, "e4"); put(img, 11, 7 + bob, "e3")
    # claws poking out of the sleeves
    ax = 3 if d != "right" else 11
    for (x, y) in ((ax - 1, 15 + bob), (ax - 1, 16 + bob), (ax, 17 + bob)):
        put(img, x, y, "m3")
    if d != "right":
        for (x, y) in ((12, 15 + bob), (12, 16 + bob), (11, 17 + bob)):
            put(img, x, y, "m3")
    # drifting mist motes
    for (mx, my) in ((2 + i, 20), (13 - i, 22)):
        put(img, mx, my, "m3", 150)
    outline(img)
    return img


# ------------------------------------------------------------------ output
def sheet_of(rows, cw, ch):
    sheet = new(max(len(r) for r in rows) * cw, len(rows) * ch)
    for r, frames in enumerate(rows):
        for c, fr in enumerate(frames):
            paste(sheet, fr, c * cw, r * ch)
    return sheet


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    slime = sheet_of([[slime_frame(i) for i in range(4)]], 16, 16)
    bat = sheet_of([[bat_frame(i) for i in range(4)]], 16, 16)
    shade_rows = []
    for d in ("down", "up", "left", "right"):
        src = "right" if d == "left" else d
        frames = [shade_frame(src, i) for i in range(4)]
        shade_rows.append([mirror(f) for f in frames] if d == "left" else frames)
    shade = sheet_of(shade_rows, 16, 24)
    slime.save(OUT / "slime.png")
    bat.save(OUT / "bat.png")
    shade.save(OUT / "shade.png")
    meta = {
        "slime": dict(cell=[16, 16], frames=4, fps=6, animation="hop"),
        "bat": dict(cell=[16, 16], frames=4, fps=10, animation="fly"),
        "shade": dict(cell=[16, 24], frames=4, fps=5, rows=["down", "up", "left", "right"]),
    }
    (BUILD / "enemy_meta.json").write_text(json.dumps(meta, indent=1))
    board = new(16 * 4 + 8 + 16 * 4 + 8 + 16 * 4, 24 * 4)
    paste(board, slime, 0, 0)
    paste(board, bat, 0, 20)
    paste(board, shade, 16 * 4 + 8, 0)
    scaled(on_bg(board, (60, 60, 70, 255)), 6).save(PREV / "enemy_sheet.png")
    print("enemies done")


if __name__ == "__main__":
    main()
