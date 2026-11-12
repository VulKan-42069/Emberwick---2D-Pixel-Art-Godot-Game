"""Effects, UI and the bitmap font.

assets/fx/slash.png       32x32 cells, rows down/up/left/right, 3 frames (aligned with the player's cell)
assets/fx/hit_spark.png   16x16 x3     assets/fx/dust_puff.png 16x16 x4     assets/fx/mist_puff.png 16x16 x4
assets/fx/mist_overlay.png 64x64 seamless    assets/fx/shadow.png  [16x6, 12x5, 24x8 side by side]
assets/ui/hearts.png      12x11 x3 (full, half, empty)    slot_frame.png 22x22    dialogue_box.png 24x24 (9-slice, 8px margin)
assets/ui/prompt_interact.png 14x15 x2    assets/ui/font/emberwick_font.png + .fnt (BMFont, all-caps)
"""
import math
import random
from pathlib import Path

from pxl import new, put, rect, paste, scaled, on_bg, ellipse, tri, outline
from palette import rgba

ROOT = Path(__file__).resolve().parent.parent
FX = ROOT / "assets" / "fx"
UI = ROOT / "assets" / "ui"
PREV = ROOT / "tools" / "previews"


def mirror(img):
    from PIL import Image
    return img.transpose(Image.FLIP_LEFT_RIGHT)


# ------------------------------------------------------------------ sword slash
SLASH = {  # centre (cell coords), facing angle in degrees (screen coords, y down), radius
    "down": ((19, 19), 90, 11),
    "up": ((16, 17), -90, 11),
    "right": ((19, 19), 0, 11),
}
SWEEPS = [(-75, -15, 0.0), (-75, 55, 0.0), (-20, 75, 1.0)]  # start, end, fade for frames 0..2


def slash_frame(d, i):
    img = new(32, 32)
    (cx, cy), face, R = SLASH[d]
    a0, a1, fade = SWEEPS[i]
    for y in range(32):
        for x in range(32):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy)
            if r < 3 or r > R + 1:
                continue
            ang = (math.degrees(math.atan2(dy, dx)) - face + 180) % 360 - 180
            if not (a0 <= ang <= a1):
                continue
            t = (ang - a0) / (a1 - a0)                      # 0 at the tail, 1 at the leading tip
            thick = (1.5 + 4.2 * t) * (1 - 0.35 * fade)      # crescent: thin tail, fat head
            if R - thick <= r <= R + 0.2 + 0.6 * t:
                if r > R - 1.1 + 0.6 * t:
                    put(img, x, y, "white")
                elif t > 0.3:
                    put(img, x, y, "e4" if i < 2 else "e3", 255 if i < 2 else 200)
                else:
                    put(img, x, y, "e3", 150)
    return img


# ------------------------------------------------------------------ hit spark / puffs
def hit_spark(i):
    img = new(16, 16)
    c = 8
    if i == 0:
        for (dx, dy) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            put(img, c + dx, c + dy, "white")
    elif i == 1:
        for k in range(1, 6):
            for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                put(img, c + dx * k, c + dy * k, "e4" if k < 4 else "e3")
        for k in range(1, 4):
            for (dx, dy) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                put(img, c + dx * k, c + dy * k, "white" if k == 1 else "e3")
        put(img, c, c, "white")
    else:
        for (dx, dy) in ((6, 0), (-6, 0), (0, 6), (0, -6), (4, 4), (-4, 4), (4, -4), (-4, -4)):
            put(img, c + dx, c + dy, "e3")
            put(img, c + dx // 2, c + dy // 2, "e4", 160)
    return img


def puff(i, cols):
    img = new(16, 16)
    r = random.Random(7)
    spec = [(2.2, 0, 255), (3.6, 2, 255), (4.8, 4, 200), (5.6, 5, 120)][i]
    rad, spread, alpha = spec
    blobs = [(0, 0), (-1, 1), (1, 1), (-1, -1), (1, -1), (0, 2)]
    for k, (bx, by) in enumerate(blobs):
        cx, cy = 8 + bx * spread * 0.8, 9 + by * spread * 0.5
        rr = max(1.0, rad - 0.6 * (k % 3) - (0.4 * i if k else 0))
        ellipse(img, cx, cy, rr, rr * 0.9, cols[1])
        ellipse(img, cx - 0.6, cy - 0.7, rr * 0.6, rr * 0.55, cols[0])
    for y in range(16):
        for x in range(16):
            p = img.getpixel((x, y))
            if p[3]:
                img.putpixel((x, y), p[:3] + (alpha,))
    return img


# ------------------------------------------------------------------ mist overlay (seamless) + shadows
def mist_overlay(size=64, cell=8, seed=3):
    r = random.Random(seed)
    g = [[r.random() for _ in range(size // cell)] for _ in range(size // cell)]
    n = size // cell
    img = new(size, size)
    for y in range(size):
        for x in range(size):
            fx, fy = x / cell, y / cell
            x0, y0 = int(fx) % n, int(fy) % n
            x1, y1 = (x0 + 1) % n, (y0 + 1) % n
            tx, ty = fx - int(fx), fy - int(fy)
            tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            v = (g[y0][x0] * (1 - tx) + g[y0][x1] * tx) * (1 - ty) + (g[y1][x0] * (1 - tx) + g[y1][x1] * tx) * ty
            if v > 0.62:
                put(img, x, y, "m3", 110)
            elif v > 0.5:
                put(img, x, y, "m2", 80)
            elif v > 0.42:
                put(img, x, y, "m2", 40)
    return img


def shadow(w, h):
    img = new(w, h)
    ellipse(img, w / 2, h / 2, w / 2, h / 2, "ink")
    for y in range(h):
        for x in range(w):
            if img.getpixel((x, y))[3]:
                img.putpixel((x, y), (27, 27, 47, 90))
    return img


# ------------------------------------------------------------------ UI
def heart_cell(mode):
    img = new(12, 11)
    mask = new(12, 11)
    for (cx, cy) in ((4.2, 4.2), (7.8, 4.2)):
        ellipse(mask, cx + 0.0, cy, 2.9, 2.9, "white")
    tri(mask, (1.1, 5.0), (10.9, 5.0), (6, 10), "white")
    for y in range(11):
        for x in range(12):
            if not mask.getpixel((x, y))[3]:
                continue
            filled = mode == "full" or (mode == "half" and x < 6)
            if filled:
                c = "r3" if (x, y) in ((2, 2), (3, 2), (2, 3)) else "r1" if (x + y > 12 or x > 8) else "r2"
            else:
                c = "st1" if (x + y > 11) else "st2"
                if (x, y) in ((2, 2), (3, 2)):
                    c = "st3"
            put(img, x, y, c)
    outline(img)
    return img


def slot_frame():
    img = new(22, 22)
    rect(img, 0, 0, 22, 22, "ink")
    rect(img, 1, 1, 20, 20, "d2")
    rect(img, 2, 2, 18, 18, "d1")
    rect(img, 3, 3, 16, 16, "st1")
    for i in range(1, 21):
        put(img, i, 1, "d3"); put(img, 1, i, "d3")
    for (x, y) in ((0, 0), (21, 0), (0, 21), (21, 21)):
        img.putpixel((x, y), (0, 0, 0, 0))
    for (x, y) in ((2, 2), (19, 2), (2, 19), (19, 19)):
        put(img, x, y, "e3")
    return img


def dialogue_box(w=24, h=24):
    img = new(w, h)
    rect(img, 0, 0, w, h, "ink")
    rect(img, 1, 1, w - 2, h - 2, "e3")
    rect(img, 2, 2, w - 4, h - 4, "e1")
    rect(img, 3, 3, w - 6, h - 6, "ink")
    rect(img, 4, 4, w - 8, h - 8, "m1")
    for x in range(4, w - 4):
        put(img, x, 4, "m2")
    for y in range(4, h - 4):
        put(img, 4, y, "m2")
    for (x, y) in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
        img.putpixel((x, y), (0, 0, 0, 0)) if (x in (0, w - 1) and y in (0, h - 1)) else put(img, x, y, "ink")
    return img


def prompt_interact(pressed):
    img = new(14, 15)
    oy = 1 if pressed else 0
    rect(img, 1, 1 + oy, 12, 10, "ink")
    rect(img, 2, 2 + oy, 10, 8, "white")
    for x in range(2, 12):
        put(img, x, 9 + oy, "st3")
    tri(img, (5, 11 + oy), (9, 11 + oy), (7, 14), "ink")
    put(img, 7, 11 + oy, "white")
    for (x, y) in ((1, 1), (12, 1), (1, 10), (12, 10)):
        img.putpixel((x, y + oy), (0, 0, 0, 0))
    glyph = GLYPHS["E"]
    for gy, row in enumerate(glyph):
        for gx, ch in enumerate(row):
            if ch == "#":
                put(img, 4 + gx, 3 + gy + oy, "ink")
    if not pressed:
        pass
    return img


# ------------------------------------------------------------------ font (5x7 caps)
def _g(*rows):
    return list(rows)


GLYPHS = {
    "A": _g(".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": _g("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": _g(".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": _g("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": _g("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": _g("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": _g(".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": _g("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": _g("###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"),
    "J": _g("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": _g("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": _g("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": _g("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": _g("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": _g(".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": _g("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": _g(".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": _g("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": _g(".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": _g("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": _g("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": _g("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": _g("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": _g("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": _g("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": _g("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": _g(".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": _g("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": _g(".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": _g("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": _g("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": _g("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": _g(".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": _g("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": _g(".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": _g(".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ".": _g(".", ".", ".", ".", ".", ".", "#"),
    ",": _g(".", ".", ".", ".", ".", "#", "#"),
    "!": _g("#", "#", "#", "#", "#", ".", "#"),
    "?": _g(".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    ":": _g(".", ".", "#", ".", "#", ".", "."),
    "'": _g("#", "#", ".", ".", ".", ".", "."),
    "\"": _g("#.#", "#.#", ".", ".", ".", ".", "."),
    "-": _g(".....", ".....", ".....", "####.", ".....", ".....", "....."),
    "/": _g("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": _g("..#", ".#.", "#..", "#..", "#..", ".#.", "..#"),
    ")": _g("#..", ".#.", "..#", "..#", "..#", ".#.", "#.."),
    "+": _g(".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": _g(".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "_": _g(".....", ".....", ".....", ".....", ".....", ".....", "#####"),
}
SPACE_ADVANCE = 4


def build_font():
    chars = sorted(GLYPHS)
    cw = [len(GLYPHS[c][0]) for c in chars]
    sheet_w = 128
    x = y = 1
    placed = {}
    for c, w in zip(chars, cw):
        if x + w + 1 > sheet_w:
            x, y = 1, y + 9
        placed[c] = (x, y, w)
        x += w + 1
    sheet = new(sheet_w, y + 9)
    for c, (px, py, w) in placed.items():
        for gy, row in enumerate(GLYPHS[c]):
            for gx, ch in enumerate(row):
                if ch == "#":
                    put(sheet, px + gx, py + gy, "white")
    lines = [
        'info face="Emberwick" size=8 bold=0 italic=0 charset="" unicode=1 stretchH=100 smooth=0 aa=0 padding=0,0,0,0 spacing=0,0 outline=0',
        f"common lineHeight=9 base=7 scaleW={sheet.width} scaleH={sheet.height} pages=1 packed=0",
        'page id=0 file="emberwick_font.png"',
    ]
    entries = []
    for c, (px, py, w) in placed.items():
        ids = [ord(c)] + ([ord(c.lower())] if c.isalpha() else [])      # lowercase reuses the capitals
        for cid in ids:
            entries.append(f"char id={cid} x={px} y={py} width={w} height=7 xoffset=0 yoffset=1 xadvance={w + 1} page=0 chnl=15")
    entries.append(f"char id=32 x=0 y=0 width=0 height=0 xoffset=0 yoffset=0 xadvance={SPACE_ADVANCE} page=0 chnl=15")
    lines.append(f"chars count={len(entries)}")
    return sheet, "\n".join(lines + entries) + "\n"


def font_preview(sheet):
    text = "THE LANTERNS HAVE GONE OUT!"
    img = new(200, 22)
    x = 2
    for ch in text:
        if ch == " ":
            x += SPACE_ADVANCE
            continue
        g = GLYPHS[ch]
        for gy, row in enumerate(g):
            for gx, c in enumerate(row):
                if c == "#":
                    put(img, x + gx, 3 + gy, "white")
        x += len(g[0]) + 1
    return img


# ------------------------------------------------------------------ output
def main():
    FX.mkdir(parents=True, exist_ok=True)
    (UI / "font").mkdir(parents=True, exist_ok=True)
    dirs = ["down", "up", "left", "right"]
    sl = new(3 * 32, 4 * 32)
    for r, d in enumerate(dirs):
        for i in range(3):
            f = slash_frame("right" if d == "left" else d, i)
            paste(sl, mirror(f) if d == "left" else f, i * 32, r * 32)
    sl.save(FX / "slash.png")
    hs = new(3 * 16, 16)
    for i in range(3):
        paste(hs, hit_spark(i), i * 16, 0)
    hs.save(FX / "hit_spark.png")
    dp = new(4 * 16, 16)
    mp = new(4 * 16, 16)
    for i in range(4):
        paste(dp, puff(i, ("s3", "s2")), i * 16, 0)
        paste(mp, puff(i, ("m3", "m2")), i * 16, 0)
    dp.save(FX / "dust_puff.png")
    mp.save(FX / "mist_puff.png")
    ov = mist_overlay()
    ov.save(FX / "mist_overlay.png")
    sh = new(16 + 12 + 24, 8)
    paste(sh, shadow(16, 6), 0, 0)
    paste(sh, shadow(12, 5), 16, 0)
    paste(sh, shadow(24, 8), 28, 0)
    sh.save(FX / "shadow.png")

    hearts = new(3 * 12, 11)
    for i, m in enumerate(("full", "half", "empty")):
        paste(hearts, heart_cell(m), i * 12, 0)
    hearts.save(UI / "hearts.png")
    slot_frame().save(UI / "slot_frame.png")
    box = dialogue_box()
    box.save(UI / "dialogue_box.png")
    pr = new(28, 15)
    paste(pr, prompt_interact(False), 0, 0)
    paste(pr, prompt_interact(True), 14, 0)
    pr.save(UI / "prompt_interact.png")
    sheet, fnt = build_font()
    sheet.save(UI / "font" / "emberwick_font.png")
    (UI / "font" / "emberwick_font.fnt").write_text(fnt)

    # preview board: effects, UI and a sample dialogue
    board = new(260, 190)
    paste(board, sl, 0, 0)
    paste(board, hs, 100, 0)
    paste(board, dp, 100, 18)
    paste(board, mp, 100, 36)
    paste(board, sh, 100, 54)
    paste(board, hearts, 100, 66)
    paste(board, slot_frame(), 140, 66)
    paste(board, pr, 168, 66)
    bg = new(260, 190)
    rect(bg, 0, 0, 260, 190, "g3")
    bg.alpha_composite(board)
    for ox in range(0, 260, 64):
        for oy in range(0, 190, 64):
            pass
    ov_big = new(260, 190)
    for ox in range(0, 260, 64):
        for oy in range(0, 190, 64):
            ov_big.alpha_composite(ov, (ox, oy)) if ox + 64 <= 260 and oy + 64 <= 190 else None
    bg.alpha_composite(ov_big.crop((130, 100, 260, 190)), (130, 100))
    # dialogue box stretched with its 9-slice margins
    big = new(200, 40)
    m = 8
    for (sx, sy, sw, sh_, dx, dy, dw, dh) in (
        (0, 0, m, m, 0, 0, m, m), (24 - m, 0, m, m, 200 - m, 0, m, m),
        (0, 24 - m, m, m, 0, 40 - m, m, m), (24 - m, 24 - m, m, m, 200 - m, 40 - m, m, m),
    ):
        big.alpha_composite(box.crop((sx, sy, sx + sw, sy + sh_)), (dx, dy))
    for dx in range(m, 200 - m, 8):
        big.alpha_composite(box.crop((m, 0, 2 * m, m)), (dx, 0))
        big.alpha_composite(box.crop((m, 24 - m, 2 * m, 24)), (dx, 40 - m))
        for dy in range(m, 40 - m, 8):
            big.alpha_composite(box.crop((m, m, 2 * m, 2 * m)), (dx, dy))
    for dy in range(m, 40 - m, 8):
        big.alpha_composite(box.crop((0, m, m, 2 * m)), (0, dy))
        big.alpha_composite(box.crop((24 - m, m, 24, 2 * m)), (200 - m, dy))
    big.alpha_composite(font_preview(sheet).crop((0, 0, 190, 22)), (4, 8))
    bg.alpha_composite(big, (4, 130))
    scaled(bg, 4).save(PREV / "fx_ui_sheet.png")
    print("fx/ui/font done")


if __name__ == "__main__":
    main()
