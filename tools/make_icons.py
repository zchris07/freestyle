"""Make the tab icon: "wtf" in the wordmark's green Fraunces on the page's dark background (tools/icon.html).
Headless Chrome renders it at 512px (rounded tile, and a full-bleed one for iOS, which rounds it itself); Pillow
scales it down. Writes favicon-32.png, favicon.ico (16/32/48), apple-touch-icon.png (180) and prints the 64px PNG as a
data URI for the <link rel="icon"> in index.html (inline, so it works in the Claude artifact too).

Usage:  python tools/make_icons.py
"""
import base64, io, os, pathlib, subprocess, tempfile
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def render(radius):
    out = os.path.join(tempfile.mkdtemp(), "icon.png")
    url = pathlib.Path(ROOT, "tools", "icon.html").as_uri() + f"?r={radius}"
    subprocess.run([CHROME, "--headless", "--hide-scrollbars", "--force-device-scale-factor=1", "--window-size=512,512",
                    "--default-background-color=00000000", "--virtual-time-budget=4000", f"--screenshot={out}", url],
                   check=True, capture_output=True)
    return Image.open(out).convert("RGBA")


def main():
    tile, full = render(112), render(0)
    small = lambda im, n: im.resize((n, n), Image.LANCZOS)
    small(tile, 32).save(os.path.join(ROOT, "favicon-32.png"))
    small(tile, 48).save(os.path.join(ROOT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    small(full, 180).convert("RGB").save(os.path.join(ROOT, "apple-touch-icon.png"))
    buf = io.BytesIO();small(tile, 64).save(buf, "PNG", optimize=True)
    print("data:image/png;base64," + base64.b64encode(buf.getvalue()).decode())


if __name__ == "__main__":
    main()
