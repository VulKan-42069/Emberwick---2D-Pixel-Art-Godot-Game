"""Tiny pixel-art helpers shared by all generators."""
from PIL import Image
from palette import rgba

T = 16  # tile size


def new(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def put(img, x, y, name, alpha=255):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), rgba(name, alpha))


def rect(img, x, y, w, h, name):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            put(img, xx, yy, name)


def paste(dst, src, x, y):
    dst.alpha_composite(src, (x, y))


def scaled(img, k):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def on_bg(img, color=(24, 24, 36, 255)):
    bg = Image.new("RGBA", img.size, color)
    bg.alpha_composite(img)
    return bg


def ellipse(img, cx, cy, rx, ry, name):
    for y in range(img.height):
        for x in range(img.width):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                put(img, x, y, name)


def tri(img, p0, p1, p2, name):
    (x0, y0), (x1, y1), (x2, y2) = p0, p1, p2
    den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if den == 0:
        return
    for y in range(img.height):
        for x in range(img.width):
            px, py = x + 0.5, y + 0.5
            a = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / den
            b = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / den
            if a >= 0 and b >= 0 and 1 - a - b >= 0:
                put(img, x, y, name)


def outline(img, name="ink"):
    """Add a 1px outline (4-neighbour) around every opaque pixel."""
    src = img.copy()
    for y in range(img.height):
        for x in range(img.width):
            if src.getpixel((x, y))[3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < img.width and 0 <= ny < img.height and src.getpixel((nx, ny))[3]:
                    put(img, x, y, name)
                    break


def line_pts(p0, p1):
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
