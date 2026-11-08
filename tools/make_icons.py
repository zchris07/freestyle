"""Draw the tab icon: four mirrored waveform bars, one per beat; beats 1-3 green, beat 4 orange (a rhyme landing on
beat 4), on the app's dark background. Writes favicon.svg (also inlined in index.html), favicon-32.png,
apple-touch-icon.png (180, full-bleed: iOS rounds it) and favicon.ico (16/32/48).

Usage:  python tools/make_icons.py
"""
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG, GREEN, ORANGE = "#121212", "#1ed760", "#ffa42b"
# 64-unit grid: bar x, width, height (centred vertically on 32)
BARS = [(6.5, 9, 26, GREEN), (20.5, 9, 42, GREEN), (34.5, 9, 30, GREEN), (48.5, 9, 52, ORANGE)]


def svg():
    bars = "".join(f'<rect x="{x}" y="{32 - h / 2}" width="{w}" height="{h}" rx="{w / 2}" fill="{c}"/>' for x, w, h, c in BARS)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="{BG}"/>'
            f'{bars}</svg>')


def png(size, radius=True):
    s = 8  # supersample, then shrink for smooth edges
    im = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = size * s / 64
    d.rounded_rectangle([0, 0, size * s - 1, size * s - 1], radius=14 * k if radius else 0, fill=BG)
    for x, w, h, c in BARS:
        d.rounded_rectangle([x * k, (32 - h / 2) * k, (x + w) * k, (32 + h / 2) * k], radius=w / 2 * k, fill=c)
    return im.resize((size, size), Image.LANCZOS)


def main():
    open(os.path.join(ROOT, "favicon.svg"), "w", encoding="utf-8").write(svg())
    png(32).save(os.path.join(ROOT, "favicon-32.png"))
    png(180, radius=False).convert("RGB").save(os.path.join(ROOT, "apple-touch-icon.png"))
    png(48).save(os.path.join(ROOT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    print(svg())


if __name__ == "__main__":
    main()
