"""Overworld terrain: grass base + 47-tile blob sets (dirt, sand, water, cliff) + preview.

Each overlay terrain is drawn on a transparent background so it can sit on the grass layer.
Bit layout of a tile's neighbourhood (Godot "match corners and sides" order, clockwise from N):
N=1 NE=2 E=4 SE=8 S=16 SW=32 W=64 NW=128. Corner bits only count when both touching sides are set.
"""
import json
import random
from pathlib import Path

from pxl import T, new, put, paste, scaled, on_bg

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "tilesets"
BUILD = ROOT / "tools" / "build"
PREV = ROOT / "tools" / "previews"

N, NE, E, SE, S, SW, W, NW = 1, 2, 4, 8, 16, 32, 64, 128
INF = 99


def reduce_bits(b):
    if not (b & N and b & E):
        b &= ~NE
    if not (b & S and b & E):
        b &= ~SE
    if not (b & S and b & W):
        b &= ~SW
    if not (b & N and b & W):
        b &= ~NW
    return b


BLOB = sorted({reduce_bits(b) for b in range(256)})
assert len(BLOB) == 47
BLOB_INDEX = {b: i for i, b in enumerate(BLOB)}


# ---------------------------------------------------------------- shape mask
def make_wobble(rng, amp):
    arr, v = [0] * T, 0
    for i in range(1, T - 1):
        v = max(0, min(amp, v + rng.choice([-1, 0, 0, 1])))
        arr[i] = v
    return arr


def blob_mask(bits, bw, wob, rr=3):
    """16x16 bool grid: True where the overlay terrain is present."""
    has = lambda f: bool(bits & f)
    rc = bw + 0.5
    m = [[True] * T for _ in range(T)]
    for y in range(T):
        for x in range(T):
            cx, cy = x + 0.5, y + 0.5
            ok = True
            if not has(N) and y < bw + wob["N"][x]: ok = False
            if not has(S) and (T - 1 - y) < bw + wob["S"][x]: ok = False
            if not has(W) and x < bw + wob["W"][y]: ok = False
            if not has(E) and (T - 1 - x) < bw + wob["E"][y]: ok = False
            # rounded convex corners
            for (a, b, fx, fy) in ((N, W, 0, 0), (N, E, 1, 0), (S, W, 0, 1), (S, E, 1, 1)):
                if not has(a) and not has(b):
                    ccx = bw + rr if not fx else T - bw - rr
                    ccy = bw + rr if not fy else T - bw - rr
                    inx = cx < ccx if not fx else cx > ccx
                    iny = cy < ccy if not fy else cy > ccy
                    if inx and iny and (cx - ccx) ** 2 + (cy - ccy) ** 2 > rr * rr:
                        ok = False
            # concave notches
            for (a, b, d, ox, oy) in ((N, W, NW, 0, 0), (N, E, NE, T, 0), (S, W, SW, 0, T), (S, E, SE, T, T)):
                if has(a) and has(b) and not has(d):
                    if (cx - ox) ** 2 + (cy - oy) ** 2 < rc * rc:
                        ok = False
            m[y][x] = ok
    return m


def edge_distances(mask):
    """For every overlay pixel: steps to the nearest empty pixel up/down/left/right (INF if the tile edge is hit first)."""
    out = {}
    for y in range(T):
        for x in range(T):
            if not mask[y][x]:
                continue
            ds = []
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                k, xx, yy = 1, x + dx, y + dy
                while 0 <= xx < T and 0 <= yy < T:
                    if not mask[yy][xx]:
                        break
                    k += 1
                    xx += dx
                    yy += dy
                else:
                    k = INF
                ds.append(k)
            out[(x, y)] = tuple(ds)  # du, dd, dl, dr
    return out


# ---------------------------------------------------------------- shaders
def noise_grid(seed):
    r = random.Random(seed)
    return [[r.random() for _ in range(T)] for _ in range(T)]


def dirt_shader(nz):
    def f(x, y, du, dd, dl, dr, frame=0):
        mn = min(du, dd, dl, dr)
        if mn == 1:
            return "d1" if (dd == 1 or dr == 1) else "d2"
        v = nz[y][x]
        if v < 0.07: return "d2"
        if v > 0.93: return "d4"
        if (du == 2 or dl == 2) and v > 0.5: return "d4"
        return "d3"
    return f


def sand_shader(nz):
    def f(x, y, du, dd, dl, dr, frame=0):
        mn = min(du, dd, dl, dr)
        if mn == 1:
            return "s1"
        v = nz[y][x]
        if v < 0.07: return "s1"
        if v > 0.92: return "s3"
        return "s2"
    return f


def cliff_shader(nz):
    def f(x, y, du, dd, dl, dr, frame=0):
        if min(du, dd, dl, dr) == 1:
            return "ink"
        if 2 <= dd <= 9:  # rock face under the lower edge
            if dd == 9: return "st3"
            if dd == 2: return "st1"
            if (x * 5 + (y // 3) * 4) % 7 == 0: return "st1"
            if dd == 8 or (x * 3 + y * 2) % 11 == 0: return "st3"
            return "st2"
        if du == 2 or dl == 2: return "g4"
        if dr == 2: return "g2"
        v = nz[y][x]
        if v < 0.05: return "g2"
        if v > 0.9: return "g4"
        return "g3"
    return f


def flagstone_shader(nz):
    """Village paving: 8x4 stones in a running bond (all periods divide 16, so tiles join seamlessly)."""
    def f(x, y, du, dd, dl, dr, frame=0):
        if min(du, dd, dl, dr) == 1:
            return "st1"
        off = ((y // 4) % 2) * 4
        mortar = (y % 4 == 3) or ((x + off) % 8 == 7)
        if mortar: return "st1"
        if y % 4 == 0 or (x + off) % 8 == 0: return "st3"
        return "st2" if nz[y][x] > 0.12 else "st1"
    return f


def ruinwall_shader(nz):
    """Raised ruin wall: slab top, brick face under the south edge."""
    def f(x, y, du, dd, dl, dr, frame=0):
        if min(du, dd, dl, dr) == 1:
            return "ink"
        if 2 <= dd <= 9:
            if dd == 9: return "st3"
            if dd == 2: return "st1"
            off = (((y - 1) // 4) % 2) * 4
            if (y - 1) % 4 == 3 or (x + off) % 8 == 7: return "st1"
            return "st2" if nz[y][x] > 0.1 else "st1"
        if du == 2 or dl == 2: return "white"
        if dr == 2: return "st2"
        if x % 8 == 7 or y % 8 == 7: return "st2"
        return "st3" if nz[y][x] > 0.06 else "st2"
    return f


def water_shader(nz):
    # fixed wave dashes: (x, y, length); they drift one pixel right per frame
    waves = [(1, 3, 3), (9, 6, 2), (4, 10, 3), (12, 13, 3), (7, 0, 2)]
    sparkles = [(3, 5), (11, 2), (6, 12), (14, 9)]

    def f(x, y, du, dd, dl, dr, frame=0):
        if min(du, dd, dl, dr) == 1:
            return "w1"
        if du == 2 or dl == 2: return "w1"
        if dd == 2 or dr == 2: return "w4"
        if du == 3 and nz[y][x] > 0.4: return "w1"
        for (wx, wy, ln) in waves:
            if y == wy and (x - wx - frame) % T < ln:
                return "w3"
        for i, (sx, sy) in enumerate(sparkles):
            if (x, y) == (sx, sy) and (frame + i) % 4 == 0:
                return "w4"
        return "w2"
    return f


def make_overlay_tile(bits, bw, wob, shader, frame=0):
    mask = blob_mask(bits, bw, wob)
    dist = edge_distances(mask)
    img = new(T, T)
    for (x, y), (du, dd, dl, dr) in dist.items():
        put(img, x, y, shader(x, y, du, dd, dl, dr, frame))
    return img


def make_wobbles(seed, amp):
    r = random.Random(seed)
    return {k: make_wobble(r, amp) for k in "NSWE"}


# ---------------------------------------------------------------- grass
def grass_base(variant_seed, tufts=0):
    r = random.Random(variant_seed)
    img = new(T, T)
    for y in range(T):
        for x in range(T):
            v = r.random()
            put(img, x, y, "g2" if v < 0.05 else "g4" if v > 0.97 else "g3")
    for _ in range(tufts):
        x, y = r.randrange(2, T - 2), r.randrange(3, T - 1)
        put(img, x, y, "g1")
        put(img, x - 1, y - 1, "g4")
        put(img, x + 1, y - 1, "g4")
        put(img, x, y - 1, "g2")
        put(img, x, y - 2, "g4")
    return img


FLOWERS = {  # petal, centre
    "white": ("white", "e3"),
    "red": ("r3", "e4"),
    "blue": ("b3", "white"),
    "yellow": ("e3", "e2"),
}


def flower(img, x, y, kind):
    petal, centre = FLOWERS[kind]
    for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        put(img, x + dx, y + dy, petal)
    put(img, x, y, centre)
    put(img, x, y + 2, "g2")  # little stem shadow


def grass_sheet():
    sheet = new(8 * T, 2 * T)
    tiles = [grass_base(10 + i) for i in range(4)] + [grass_base(20 + i, tufts=2) for i in range(2)] \
        + [grass_base(30, tufts=1), grass_base(31, tufts=3)]
    for i, t in enumerate(tiles):
        paste(sheet, t, (i % 8) * T, 0)
    r = random.Random(99)
    row = []
    for k, kind in enumerate(FLOWERS):
        for dens in (1, 3):
            t = grass_base(40 + k * 2 + dens)
            spots = []
            while len(spots) < dens:
                p = (r.randrange(3, T - 3), r.randrange(3, T - 3))
                if all(abs(p[0] - q[0]) + abs(p[1] - q[1]) > 6 for q in spots):
                    spots.append(p)
            for (fx, fy) in spots:
                flower(t, fx, fy, kind)
            row.append(t)
    for i, t in enumerate(row):
        paste(sheet, t, (i % 8) * T, T)
    return sheet


# ---------------------------------------------------------------- sheets
TERRAINS = {
    #  name   bw  wobble-amp  seed  shader
    "dirt":  dict(bw=2, amp=1, seed=1, shader=dirt_shader),
    "sand":  dict(bw=2, amp=1, seed=2, shader=sand_shader),
    "cliff": dict(bw=2, amp=0, seed=3, shader=cliff_shader),
    "water": dict(bw=3, amp=1, seed=4, shader=water_shader),
    "cobble": dict(bw=2, amp=0, seed=5, shader=flagstone_shader),
    "ruin_wall": dict(bw=2, amp=0, seed=6, shader=ruinwall_shader),
}
WATER_FRAMES = 4
sheet_cache = {}


def build_terrain(name):
    cfg = TERRAINS[name]
    wob = make_wobbles(cfg["seed"], cfg["amp"])
    shader = cfg["shader"](noise_grid(cfg["seed"] * 7))
    frames = WATER_FRAMES if name == "water" else 1
    tiles = [[make_overlay_tile(b, cfg["bw"], wob, shader, f) for f in range(frames)] for b in BLOB]
    if frames == 1:
        sheet = new(8 * T, 6 * T)
        for i, (t,) in enumerate(tiles):
            paste(sheet, t, (i % 8) * T, (i // 8) * T)
    else:  # each tile's frames sit side by side; 4 tiles per sheet row
        sheet = new(4 * frames * T, 12 * T)
        for i, fr in enumerate(tiles):
            for f, t in enumerate(fr):
                paste(sheet, t, ((i % 4) * frames + f) * T, (i // 4) * T)
    sheet_cache[name] = tiles
    return sheet


def atlas_coords(name, i):
    if name == "water":
        return [(i % 4) * WATER_FRAMES, i // 4]
    return [i % 8, i // 8]


# ---------------------------------------------------------------- preview map
MAP = [
    "cccccccc..dd..cccccc",
    "cccccccc..dd..cccccc",
    "..........dd........",
    "...ssss...dd........",
    "..sswwss..dd........",
    "..swwwws..dddddddd..",
    "..swwwws..dddddddd..",
    "..sswwss..dd........",
    "...ssss...dd........",
    "..........dd........",
    "..........dd........",
]
LAYERS = [("dirt", "d"), ("sand", "s"), ("water", "w"), ("cliff", "c")]


def cell_is(mp, ch, x, y):
    if y < 0 or y >= len(mp) or x < 0 or x >= len(mp[0]):
        return True  # off-map counts as same terrain so the map edge has no border
    return mp[y][x] == ch or (ch == "s" and mp[y][x] == "w")  # sand continues under water


def bits_at(mp, ch, x, y):
    b = 0
    for flag, (dx, dy) in ((N, (0, -1)), (NE, (1, -1)), (E, (1, 0)), (SE, (1, 1)),
                           (S, (0, 1)), (SW, (-1, 1)), (W, (-1, 0)), (NW, (-1, -1))):
        if cell_is(mp, ch, x + dx, y + dy):
            b |= flag
    return reduce_bits(b)


def render_preview(frame=0):
    h, w = len(MAP), len(MAP[0])
    img = new(w * T, h * T)
    grass = [t for t in [grass_base(10 + i) for i in range(4)] + [grass_base(20, tufts=2)]]
    fl = grass_sheet()
    r = random.Random(5)
    for y in range(h):
        for x in range(w):
            roll = r.random()
            if roll < 0.08:
                fx = r.randrange(8) * T
                t = fl.crop((fx, T, fx + T, 2 * T))
            else:
                t = r.choice(grass)
            paste(img, t, x * T, y * T)
    for name, ch in LAYERS:
        for y in range(h):
            for x in range(w):
                here = MAP[y][x] == ch or (ch == "s" and MAP[y][x] == "w")
                if not here:
                    continue
                i = BLOB_INDEX[bits_at(MAP, ch, x, y)]
                tile = sheet_cache[name][i][frame % len(sheet_cache[name][i])]
                paste(img, tile, x * T, y * T)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    PREV.mkdir(parents=True, exist_ok=True)
    grass_sheet().save(OUT / "terrain_grass.png")
    for name in TERRAINS:
        build_terrain(name).save(OUT / f"terrain_{name}.png")
    meta = {
        "tile_size": T,
        "blob_bits": BLOB,
        "bit_flags": dict(N=N, NE=NE, E=E, SE=SE, S=S, SW=SW, W=W, NW=NW),
        "water_frames": WATER_FRAMES,
        "atlas": {name: [atlas_coords(name, i) for i in range(47)] for name in TERRAINS},
    }
    (BUILD / "terrain_meta.json").write_text(json.dumps(meta, indent=1))

    scaled(on_bg(render_preview(0)), 3).save(PREV / "terrain_preview.png")
    # tile-sheet overview for inspection
    names = ("dirt", "sand", "cliff", "water")
    ov = new(2 * (8 * T + 8), 2 * (6 * T + 8))
    for k, name in enumerate(names):
        sheet = OUT / f"terrain_{name}.png"
        from PIL import Image
        s = Image.open(sheet)
        if name == "water":  # show frame 0 of each tile only
            s0 = new(8 * T, 6 * T)
            for i in range(47):
                cx, cy = atlas_coords("water", i)
                paste(s0, s.crop((cx * T, cy * T, cx * T + T, cy * T + T)), (i % 8) * T, (i // 8) * T)
            s = s0
        paste(ov, s, (k % 2) * (8 * T + 8), (k // 2) * (6 * T + 8))
    scaled(on_bg(ov), 3).save(PREV / "terrain_sheets.png")
    print("terrain done")


if __name__ == "__main__":
    main()
