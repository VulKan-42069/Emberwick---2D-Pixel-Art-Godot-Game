"""NPCs: elder (quest giver), shopkeeper, child (hints) and a village cat.

People reuse the player's body templates with different palettes/accessories. 16x24 cells, feet on the bottom row.
Sheet rows: idle (2 frames) and walk (4 frames) for down, up, left, right. Cat cells are 16x16.
"""
import json
from pathlib import Path

from PIL import Image

import gen_player as P
from pxl import new, put, paste, scaled, on_bg, ellipse, tri, outline

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "characters"
BUILD = ROOT / "tools" / "build"
PREV = ROOT / "tools" / "previews"
W, H = P.W, P.H
DIRS = ["down", "up", "left", "right"]


def palette(**over):
    m = dict(P.COL)
    m.update(over)
    return m


# ------------------------------------------------------------------ accessories (sprite coords, 'right' = facing right)
def staff(img, d):
    for y in range(8, 24):
        put(img, 14, y, "d2")
    for (x, y) in ((14, 4), (15, 5), (15, 6), (14, 7), (13, 5), (13, 6)):
        put(img, x, y, "ink")
    put(img, 14, 5, "e4")
    put(img, 14, 6, "e3")
    put(img, 13, 15, "sk2")
    if d == "right":
        put(img, 12, 15, "sk2")


def beard(img, d):
    if d == "down":
        for x in range(4, 12):
            put(img, x, 9, "st3" if x in (4, 11) else "white")
        for x in range(4, 12):
            put(img, x, 10, "st3" if x in (4, 11) else "white")
        for x in range(5, 11):
            put(img, x, 11, "st3" if x in (5, 10) else "white")
        for x in range(6, 10):
            put(img, x, 12, "st3" if x in (6, 9) else "white")
        put(img, 7, 13, "st3"); put(img, 8, 13, "st3")
    elif d == "right":
        for x in range(8, 12):
            put(img, x, 9, "white")
        for x in range(7, 12):
            put(img, x, 10, "white")
        for x in range(8, 11):
            put(img, x, 11, "white")
        put(img, 9, 12, "st3"); put(img, 10, 12, "st3")
        put(img, 7, 10, "st3")


def hat(img, d):
    for y in range(0, 3):                      # remove the hair on top so the crown sits cleanly
        for x in range(W):
            img.putpixel((x, y), (0, 0, 0, 0))
    rows = [".5o6.5", ".4o1b2a4o1.4", ".4o1a6o1.4", ".1o14.1", ".1o1b2a6A4o1.1", ".2o12.2"]
    mp = palette(a="s2", A="s1", b="s3")
    P.draw_rows(img, rows, 0, mp)


def moustache(img, d):
    if d == "down":
        for x in range(6, 10):
            put(img, x, 9, "d1")
    elif d == "right":
        for x in (9, 10, 11):
            put(img, x, 9, "d1")


def apron(img, d):
    if d == "down":
        for y in range(12, 17):
            for x in range(5, 11):
                put(img, x, y, "st3" if x == 5 else "white")
        for x in (4, 11):
            put(img, x, 15, "e3")
    elif d == "right":
        for y in range(13, 17):
            for x in (8, 9, 10):
                put(img, x, y, "st3" if x == 8 else "white")
    else:
        for x in range(4, 12):
            put(img, x, 15, "white")
        put(img, 7, 16, "white"); put(img, 8, 16, "white")


def squash(img, remove):
    keep = [y for y in range(H) if y not in remove]
    out = new(W, H)
    off = H - len(keep)
    for i, y in enumerate(keep):
        for x in range(W):
            out.putpixel((x, off + i), img.getpixel((x, y)))
    return out


# ------------------------------------------------------------------ robe legs (elder)
def robe_legs(img, d, step, mp):
    if d == "right":
        P.draw_rows(img, [".4o1t6o1.4", ".4o1t6o1.4", ".4o1t2T2t2o1.4", ".4o1t6o1.4", ".4o1T6o1.4", ".4o8.4"], 16, mp)
        sh = {0: 1, 1: 0, 2: -1, 3: 0}[step]
        for x in range(6 + sh, 10 + sh):
            put(img, x, 22, "d1")
        put(img, 5 + sh, 22, "ink"); put(img, 10 + sh, 22, "ink")
        for x in range(5 + sh, 11 + sh):
            put(img, x, 23, "ink")
    else:
        P.draw_rows(img, ["o1t8o1", "o1t8o1", "o1t3T2t3o1", "o1t8o1", "o1T8o1", "o10"], 16, mp)
        for foot, x0 in (("l", 4), ("r", 9)):
            hidden = (step == 0 and foot == "l") or (step == 2 and foot == "r")
            if hidden:
                continue
            for x in range(x0, x0 + 3):
                put(img, x, 22, "d1")
            put(img, x0 - 1, 22, "ink"); put(img, x0 + 3, 22, "ink")
            for x in range(x0 - 1, x0 + 4):
                put(img, x, 23, "ink")


# ------------------------------------------------------------------ person builder
def person(spec, d, step=None, breathe=0):
    """d in down/up/right. step None = idle, 0..3 = walk frame. Legs sit under the torso; only the upper body bobs."""
    mp = spec["map"]
    walk = step is not None
    bob = walk and step in (1, 3)
    img = new(W, H)
    if spec["legs"] == "robe":
        robe_legs(img, d, step if walk else 1, mp)
    elif d == "right":
        table = {None: (6, 6, 0, 0), 0: (8, 5, 0, 0), 1: (6, 8, 0, 2), 2: (5, 8, 0, 0), 3: (8, 6, 2, 0)}
        P.legs_side(img, *table[step], mp=mp, bob=bob)
    else:
        table = {None: (0, 0), 0: (1, 0), 1: (0, 0), 2: (0, 1), 3: (0, 0)}
        P.legs_front(img, *table[step], mp=mp, bob=bob)
    upper = new(W, H)
    P.draw_rows(upper, {"down": P.FRONT, "up": P.BACK, "right": P.SIDE}[d], 0, mp)
    paste(img, P.shift(upper, 0, -1 if bob else breathe), 0, 0)
    for fn in spec.get("extras", []):
        fn(img, d)
    if spec.get("squash"):
        img = squash(img, spec["squash"])
    return img


SPECS = {
    "elder": dict(
        map=palette(h="st3", j="white", H="st2", t="m2", T="m1", u="m3", r="e3", R="e1", q="e4", B="e1"),
        legs="robe", extras=[beard, staff]),
    "shopkeeper": dict(
        map=palette(h="d1", j="d2", H="ink", t="g2", T="g1", u="g3", r="white", R="st3", q="white"),
        legs="pants", extras=[apron, hat, moustache]),
    "child": dict(
        map=palette(h="e3", j="e4", H="e2", t="r2", T="r1", u="r3", r="r3", R="r1", q="r3", P="g2", Q="g1", x="d2"),
        legs="pants", squash=[13, 14, 18, 19]),
}


def mirror(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)


def person_rows(spec):
    rows = []
    src = lambda d: "right" if d == "left" else d
    fix = lambda d, im: mirror(im) if d == "left" else im
    for d in DIRS:
        rows.append((f"idle_{d}", [fix(d, person(spec, src(d))), fix(d, person(spec, src(d), breathe=1))], 2))
    for d in DIRS:
        rows.append((f"walk_{d}", [fix(d, person(spec, src(d), step=i)) for i in range(4)], 8))
    return rows


# ------------------------------------------------------------------ cat (16x16, ginger tabby)
def cat_side(f, walk):
    img = new(16, 16)
    far = {0: (-1, 1), 1: (0, 0), 2: (1, -1), 3: (0, 0)}[f] if walk else (0, 0)
    lift = {1: "near", 3: "far"}.get(f) if walk else None
    nf = {0: 1, 1: 0, 2: -1, 3: 0}[f] if walk else 0
    tail_dx = (0, 1, 0, -1)[f % 4] if not walk else (0, 0, 1, 1)[f]
    # tail
    for (x, y) in ((1, 8), (1, 7), (0, 6), (0, 5 - 0), (1 + tail_dx, 4), (2 + tail_dx, 4)):
        put(img, x, y, "e2")
    # far legs then body then near legs
    def legs(pairs):
        for (x, lifted, col, paw) in pairs:
            top = 11
            bot = 12 if lifted else 14
            for y in range(top, bot):
                put(img, x, y, col)
                put(img, x + 1, y, col)
            if not lifted and paw:
                put(img, x, bot - 1, "white")
                put(img, x + 1, bot - 1, "white")
    legs([(11 + far[0], lift == "far", "e1", True), (5 + far[1], False, "e1", False)])
    ellipse(img, 7.5, 9, 5.5, 3, "e2")
    ellipse(img, 12, 6.5, 3, 3, "e2")
    tri(img, (9, 0.5), (9, 4), (11.5, 4), "e2")
    tri(img, (12.5, 4), (14.8, 4), (14.8, 0.5), "e2")
    put(img, 10, 2, "r3"); put(img, 14, 2, "r3")
    ellipse(img, 14, 7.8, 1.3, 1.1, "white")
    for x in (4, 6, 8):
        put(img, x, 6, "e1")
    for x in (3, 5, 7):
        put(img, x, 7, "e1")
    for x in range(6, 10):
        put(img, x, 11, "white")
    put(img, 12, 6, "ink")
    put(img, 15, 7, "r3")
    legs([(9 + nf, lift == "near", "e2", True), (3 + nf, False, "e2", False)])
    return img


def cat_front(f, walk, back=False):
    img = new(16, 16)
    lift = (f in (0,), f in (2,)) if walk else (False, False)
    ellipse(img, 8, 11.5, 3.6, 3.2, "e2")
    if not back:
        ellipse(img, 8, 12.5, 1.6, 2, "white")
    for i, x in enumerate((5, 9)):   # paws
        if not lift[i]:
            put(img, x, 14, "white" if not back else "e1"); put(img, x + 1, 14, "white" if not back else "e1")
            put(img, x, 13, "e2"); put(img, x + 1, 13, "e2")
    tail = ((12, 12), (13, 11), (13, 10), (12 + (1 if f % 2 else 0), 9)) if not back else ((8, 9), (8, 8), (9, 7), (9 + (1 if f % 2 else 0), 6))
    for (x, y) in tail:
        put(img, x, y, "e2")
    ellipse(img, 8, 6, 4.6, 3.5, "e2")
    tri(img, (3.5, 0.8), (3.5, 4.5), (7, 3), "e2")
    tri(img, (12.5, 0.8), (12.5, 4.5), (9, 3), "e2")
    put(img, 4, 3, "r3"); put(img, 11, 3, "r3")
    for (x, y) in ((8, 3), (7, 4), (9, 4)):
        put(img, x, y, "e1")
    if not back:
        blink = walk is False and f == 1
        for x in (5, 10):
            put(img, x, 6, "e1" if blink else "ink")
            if not blink:
                put(img, x, 5, "g4")  # green eyes
        put(img, 7, 7, "white"); put(img, 8, 7, "white"); put(img, 7, 8, "white"); put(img, 8, 8, "white")
        put(img, 7, 7, "r3")
    else:
        for (x, y) in ((6, 10), (9, 10), (7, 12), (8, 12)):
            put(img, x, y, "e1")
    return img


def cat_frame(d, f, walk):
    if d in ("right", "left"):
        im = cat_side(f, walk)
    else:
        im = cat_front(f, walk, back=(d == "up"))
    outline(im)
    return mirror(im) if d == "left" else im


def cat_rows():
    rows = []
    for d in DIRS:
        rows.append((f"idle_{d}", [cat_frame(d, 0, False), cat_frame(d, 1, False)], 2))
    for d in DIRS:
        rows.append((f"walk_{d}", [cat_frame(d, i, True) for i in range(4)], 8))
    return rows


# ------------------------------------------------------------------ output
def save_sheet(name, rows, cell):
    cw, ch = cell
    sheet = new(4 * cw, len(rows) * ch)
    anims = {}
    for r, (anim, frames, fps) in enumerate(rows):
        for c, fr in enumerate(frames):
            paste(sheet, fr, c * cw, r * ch)
        anims[anim] = dict(row=r, frames=len(frames), loop=True, fps=fps)
    sheet.save(OUT / f"{name}.png")
    return sheet, dict(cell=[cw, ch], feet_y=ch - 1, animations=anims)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    meta, previews = {}, []
    for name, spec in SPECS.items():
        sheet, meta[name] = save_sheet(name, person_rows(spec), (W, H))
        previews.append(sheet)
    sheet, meta["cat"] = save_sheet("cat", cat_rows(), (16, 16))
    previews.append(sheet)
    (BUILD / "npc_meta.json").write_text(json.dumps(meta, indent=1))
    pw = sum(p.width + 8 for p in previews)
    ph = max(p.height for p in previews)
    board = new(pw, ph)
    x = 0
    for p in previews:
        paste(board, p, x, 0)
        x += p.width + 8
    scaled(on_bg(board, (60, 90, 60, 255)), 5).save(PREV / "npc_sheet.png")
    print("npcs done")


if __name__ == "__main__":
    main()
