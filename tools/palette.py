"""Shared palette for every Emberwick asset. Every generator pulls colours from here by name."""

_HEX = {
    "ink":   "#1b1b2f",
    # grass
    "g1": "#245a3a", "g2": "#3b8741", "g3": "#5fae4b", "g4": "#94d15c",
    # dirt / wood
    "d1": "#4a2c24", "d2": "#7a4a31", "d3": "#a8693c", "d4": "#d09560",
    # sand
    "s1": "#c9a05a", "s2": "#e6c987", "s3": "#f4e2ae",
    # water
    "w1": "#1f4c7a", "w2": "#2e72a8", "w3": "#4ba3d1", "w4": "#a6e0f0",
    # stone
    "st1": "#3c3f55", "st2": "#646a80", "st3": "#9ba0b3",
    # skin
    "sk1": "#b86f50", "sk2": "#e0a07a", "sk3": "#f5cfa5",
    # red cloth / flowers
    "r1": "#7c2a3a", "r2": "#b94545", "r3": "#e8694f",
    # ember / fire / gold
    "e1": "#c8601f", "e2": "#f08a2a", "e3": "#ffc44a", "e4": "#fff0a0",
    # blue cloth
    "b1": "#2a3a7a", "b2": "#3f5fb0", "b3": "#6e93e0",
    # night mist
    "m1": "#3a2a5a", "m2": "#6a4f96", "m3": "#9a86c8",
    "white": "#f5f0e6",
}


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


PALETTE = {name: _rgb(h) for name, h in _HEX.items()}


def rgba(name, alpha=255):
    r, g, b = PALETTE[name]
    return (r, g, b, alpha)


if __name__ == "__main__":
    from PIL import Image, ImageDraw
    cols = 9
    names = list(PALETTE)
    rows = (len(names) + cols - 1) // cols
    cell = 48
    img = Image.new("RGBA", (cols * cell, rows * cell), (40, 40, 40, 255))
    d = ImageDraw.Draw(img)
    for i, n in enumerate(names):
        x, y = (i % cols) * cell, (i // cols) * cell
        d.rectangle([x, y, x + cell - 1, y + cell - 1], fill=rgba(n))
        d.text((x + 3, y + 3), n, fill=(255, 255, 255, 255) if sum(PALETTE[n]) < 380 else (0, 0, 0, 255))
    img.save("previews/palette.png")
    print(len(names), "colours")
