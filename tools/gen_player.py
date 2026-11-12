"""Main character: the lantern-keeper. 16x24 body drawn in a 32x32 cell (feet anchored) so sword swings fit.

Sheet rows (one row per animation+direction, frames run left to right):
idle (2) / walk (4) / attack (3) / hurt (1) for down, up, left, right, then death (3, down only).
"""
import json
from pathlib import Path

from PIL import Image

from pxl import new, put, paste, scaled, on_bg

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "characters"
BUILD = ROOT / "tools" / "build"
PREV = ROOT / "tools" / "previews"

CELL = 32
OX, OY = 8, 6          # where the 16x24 body sits inside the cell
W, H = 16, 24

COL = {
    ".": None, "o": "ink", "e": "ink",
    "h": "d2", "j": "d3", "H": "d1",                 # hair
    "s": "sk2", "S": "sk1", "k": "sk3",              # skin
    "t": "b2", "T": "b1", "u": "b3",                 # tunic
    "r": "r2", "R": "r1", "q": "r3",                 # scarf
    "B": "d2", "y": "e3",                            # belt, buckle
    "P": "s1", "Q": "d3", "x": "d1", "X": "d2",      # trousers (lit / shade), boots
}


def rle(s):
    out, i = [], 0
    while i < len(s):
        ch = s[i]
        i += 1
        n = ""
        while i < len(s) and s[i].isdigit():
            n += s[i]
            i += 1
        out.append(ch * int(n))
    line = "".join(out)
    if len(line) != W:                   # symmetric rows are written without padding
        assert len(line) % 2 == 0 and len(line) < W, (s, len(line))
        line = line.center(W, ".")
    return line


def draw_rows(img, rows, y0=0, mapping=COL):
    for dy, spec in enumerate(rows):
        for x, ch in enumerate(rle(spec)):
            name = mapping[ch]
            if name:
                put(img, x, y0 + dy, name)


# ------------------------------------------------------------------ upper body (rows 1..16)
FRONT = [
    "", "o8", "o1h3j2h3o1", "o1h3j3h4o1", "o1h10o1", "o1h10o1", "o1h3s4h3o1",
    "o1h1s1e1s4e1s1h1o1", "o1h1s1e1s4e1s1h1o1", "o1s1S1s6S1s1o1", "o2s8o2",
    "o2r6o2", "o1u2t5T1o1", "o1t3y2t3o1", "o1t8o1", "o1s1B2y2B2s1o1", "o1T8o1",
]
FRONT_HURT = list(FRONT)
FRONT_HURT[7] = "o1h1s1S1s4S1s1h1o1"          # eyes squeezed shut ...
FRONT_HURT[8] = "o1h1s1e1s4e1s1h1o1"          # ... as a single dark line
FRONT_HURT[9] = "o1s1S1s2o2s2S1s1o1"          # open mouth

BACK = [
    "", "o8", "o1h3j2h3o1", "o1h3j3h4o1", "o1h10o1", "o1h10o1", "o1h10o1",
    "o1h10o1", "o1h10o1", "o1h3H4h3o1", "o2h8o2",
    "o2r6o2", "o1u2t5T1o1", "o1t3r2t3o1", "o1t3R2t3o1", "o1s1B6s1o1", "o1T8o1",
]

SIDE = [
    "", ".4o7.5", ".3o1h4j2h1o1.4", ".2o1h5j2h2o1.3", ".2o1h8s1o1.3", ".2o1h7s2o1.3",
    ".2o1h5s4o1.3", ".2o1h4s3e1s1o1.3", ".2o1h3S1s3e1s1o1.3",
    ".2o1h3s6o2.2", ".3o1h2s6o1.3", ".3o1r7o1.4",
    ".4o1u1t4T1o1.4", ".4o1t6o1.4", ".4o1t2T2t2o1.4", ".4o1B4s2o1.4", ".4o1T6o1.4",
]
SIDE_HURT = list(SIDE)
SIDE_HURT[7] = ".2o1h4s5o1.3"                  # eye squeezed shut (line stays on the row below)
SIDE_HURT[9] = ".2o1h3s3o1s2o2.2"              # open mouth


def upper(d, hurt=False):
    img = new(W, H)
    rows = {"down": FRONT_HURT if hurt else FRONT, "up": BACK, "right": SIDE_HURT if hurt else SIDE}[d]
    draw_rows(img, rows)
    return img


# ------------------------------------------------------------------ legs (rows 17..23)
def leg(img, px, pw, bx, bw, raise_, lit, mp=COL, bob=False):
    """One leg: trousers (px, pw) over boots (bx, bw), each wrapped in ink.
    The sole sits at row 23 - raise_; the leg keeps its length (it starts higher) so a lifted foot never looks stubby.
    Legs are drawn *under* the torso, which hides the top rows."""
    pants, shade = ("P", "Q") if lit else ("Q", "x")
    sole = 23 - raise_
    top = 17 - max(raise_, 1 if bob else 0)
    for y in range(top, sole):
        r = "x" if y >= sole - 2 else shade if y == sole - 3 else pants
        x0, iw = (bx, bw) if r == "x" else (px, pw)
        put(img, x0 - 1, y, "ink")
        put(img, x0 + iw, y, "ink")
        for k in range(iw):
            put(img, x0 + k, y, mp[r])
    for k in range(bx - 1, bx + bw + 1):
        put(img, k, sole, "ink")


def legs_front(img, raise_l=0, raise_r=0, mp=COL, bob=False):
    leg(img, 5, 2, 4, 3, raise_l, True, mp, bob)
    leg(img, 9, 2, 9, 3, raise_r, True, mp, bob)


def legs_side(img, near_x, far_x, near_raise=0, far_raise=0, mp=COL, bob=False):
    leg(img, far_x, 3, far_x, 4, far_raise, False, mp, bob)
    leg(img, near_x, 3, near_x, 4, near_raise, True, mp, bob)


# ------------------------------------------------------------------ lantern (hangs behind the hip)
def lantern(img, x, y, bright=True):
    put(img, x + 1, y, "d1")
    put(img, x + 2, y, "d1")
    for k in range(4):
        put(img, x + k, y + 1, "ink")
    glow = ("e4", "e3") if bright else ("e3", "e2")
    for (gx, gy, c) in ((1, 2, glow[0]), (2, 2, glow[1]), (1, 3, glow[1]), (2, 3, "e2")):
        put(img, x + gx, y + gy, c)
    put(img, x, y + 2, "ink"); put(img, x + 3, y + 2, "ink")
    put(img, x, y + 3, "ink"); put(img, x + 3, y + 3, "ink")
    put(img, x + 1, y + 4, "ink"); put(img, x + 2, y + 4, "ink")


def shift(img, dx, dy):
    out = new(img.width, img.height)
    out.paste(img, (dx, dy), img)
    return out


def body(d, *, breathe=0, legs=None, hurt=False, lantern_dy=0, bright=True, carry=True):
    """16x24 sprite for direction d in {down, up, right}.
    breathe > 0 sinks the upper body (idle); breathe < 0 lifts it (walk 'passing' frames). Feet never leave the ground."""
    spr = new(W, H)
    lx, ly = (1, 15) if d == "right" else (0, 15)
    if carry:
        lantern(spr, lx, ly + lantern_dy + min(0, breathe), bright)
    if d == "right":
        legs_side(spr, *(legs or (6, 6, 0, 0)), bob=breathe < 0)
    else:
        legs_front(spr, *(legs or (0, 0)), bob=breathe < 0)
    paste(spr, shift(upper(d, hurt), 0, breathe), 0, 0)
    return spr


def to_cell(spr, dx=0, dy=0):
    cell = new(CELL, CELL)
    cell.paste(spr, (OX + dx, OY + dy), spr)
    return cell


def mirror(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)


# ------------------------------------------------------------------ animations
def idle_frames(d):
    return [body(d, lantern_dy=0, bright=True), body(d, breathe=1, lantern_dy=1, bright=False)]


SIDE_STRIDE = [  # (near_x, far_x, near_raise, far_raise, bob): contact, pass, contact (swapped), pass
    (8, 5, 0, 0, False), (6, 8, 0, 2, True), (5, 8, 0, 0, False), (8, 6, 2, 0, True),
]
FRONT_STEP = [(1, 0, False), (0, 0, True), (0, 1, False), (0, 0, True)]  # (raise_l, raise_r, bob)


def walk_frames(d):
    out = []
    for i in range(4):
        if d == "right":
            nx, fx, nr, fr, bob = SIDE_STRIDE[i]
            out.append(body(d, legs=(nx, fx, nr, fr), breathe=-1 if bob else 0, lantern_dy=i % 2))
        else:
            rl, rr, bob = FRONT_STEP[i]
            out.append(body(d, legs=(rl, rr), breathe=-1 if bob else 0, lantern_dy=i % 2))
    return out


def hurt_frame(d):
    return [body(d, hurt=True, bright=False)]


def line(p0, p1):
    (x0, y0), (x1, y1) = p0, p1
    pts, dx, dy = [], abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return pts
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def sword(cell, grip, tip):
    """Short sword: dark halo, steel blade with a bright edge, gold guard, wooden grip, and the hand."""
    pts = line(grip, tip)
    vx, vy = tip[0] - grip[0], tip[1] - grip[1]
    n = max(abs(vx), abs(vy))
    ux, uy = vx / n, vy / n
    handle = pts[:2]
    blade = pts[3:]
    for (x, y) in pts[2:]:
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                put(cell, x + ox, y + oy, "ink")
    for (x, y) in handle:
        put(cell, x, y, "d2")
    gx, gy = pts[2]
    px, py = -uy, ux                                    # perpendicular to the blade
    for k in (-1, 0, 1):
        put(cell, round(gx + px * k), round(gy + py * k), "ink" if k else "e3")
        put(cell, round(gx + px * k), round(gy + py * k), "e3")
    for i, (x, y) in enumerate(blade):
        put(cell, x, y, "white" if i % 2 == 0 else "st3")
    put(cell, *tip, "white")
    hx, hy = grip
    for (ax, ay) in ((0, 0), (1, 0), (0, 1), (1, 1)):
        put(cell, hx + ax - 1, hy + ay - 1, "sk2")
    put(cell, hx - 1, hy, "sk3")


ATTACK = {  # grip -> tip, in cell coordinates, per frame (wind-up, slash, follow-through)
    "down":  [((22, 20), (22, 11)), ((22, 21), (29, 27)), ((17, 23), (17, 31))],
    "up":    [((22, 19), (26, 12)), ((22, 17), (25, 7)),  ((23, 18), (23, 5))],
    "right": [((22, 19), (19, 10)), ((22, 20), (30, 15)), ((23, 22), (31, 23))],
}
LEAN = {"down": [(0, 0), (0, 1), (0, 1)], "up": [(0, 0), (0, 0), (0, -1)], "right": [(-1, 0), (0, 0), (1, 0)]}


def attack_frames(d):
    frames = []
    for i in range(3):
        cell = to_cell(body(d, legs=((6, 6, 0, 0) if d == "right" else (0, 0))), *LEAN[d][i])
        sw = new(CELL, CELL)
        grip, tip = ATTACK[d][i]
        sword(sw, grip, tip)
        if d == "up":
            under = new(CELL, CELL)
            paste(under, sw, 0, 0)
            paste(under, cell, 0, 0)
            cell = under
        else:
            paste(cell, sw, 0, 0)
        frames.append(cell)
    return frames


def death_frames():
    hurt = body("down", hurt=True, bright=False)
    kneel = new(W, H)
    lantern(kneel, 0, 18, False)
    bare = body("down", hurt=True, carry=False)
    paste(kneel, bare.crop((0, 0, W, 17)), 0, 3)
    paste(kneel, bare.crop((0, 20, W, 24)), 0, 20)
    lying = hurt.rotate(90, expand=True)                 # 24x16, head on the left
    f0 = to_cell(kneel)
    f1 = new(CELL, CELL)
    f1.paste(lying, (4, CELL - 16 - 2), lying)
    f2 = f1.copy()
    for (x, y, c) in ((9, 18, "e3"), (15, 14, "e4"), (21, 17, "e2"), (12, 11, "e2")):
        put(f2, x, y, c)
    return [f0, f1, f2]


def build():
    rows = []   # (name, frames, loop, fps)
    dirs = ["down", "up", "left", "right"]

    def src(d):
        return "right" if d == "left" else d

    def cells(frames, d, *, already_cell=False):
        out = [f if already_cell else to_cell(f) for f in frames]
        return [mirror(c) for c in out] if d == "left" else out

    for d in dirs:
        rows.append((f"idle_{d}", cells(idle_frames(src(d)), d), True, 3))
    for d in dirs:
        rows.append((f"walk_{d}", cells(walk_frames(src(d)), d), True, 8))
    for d in dirs:
        rows.append((f"attack_{d}", cells(attack_frames(src(d)), d, already_cell=True), False, 14))
    for d in dirs:
        rows.append((f"hurt_{d}", cells(hurt_frame(src(d)), d), False, 1))
    rows.append(("death", death_frames(), False, 5))
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    PREV.mkdir(parents=True, exist_ok=True)
    rows = build()
    cols = max(len(f) for _, f, _, _ in rows)
    sheet = new(cols * CELL, len(rows) * CELL)
    meta = {"cell": CELL, "body": [W, H], "body_offset": [OX, OY], "feet_y": OY + H - 1, "animations": {}}
    for r, (name, frames, loop, fps) in enumerate(rows):
        for c, fr in enumerate(frames):
            paste(sheet, fr, c * CELL, r * CELL)
        meta["animations"][name] = dict(row=r, frames=len(frames), loop=loop, fps=fps)
    sheet.save(OUT / "player.png")
    (BUILD / "player_meta.json").write_text(json.dumps(meta, indent=1))
    scaled(on_bg(sheet, (60, 90, 60, 255)), 4).save(PREV / "player_sheet.png")
    print("player done:", sheet.size)


if __name__ == "__main__":
    main()
