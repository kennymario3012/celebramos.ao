"""Converte .construcao/<nome>.svg em PNG transparente com o Chromium (Playwright), com as fontes locais.

Uso directo:  python3 arte/render.py [--bg=#cor] nome1 nome2 ...
"""
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent          # prototipo/
BUILD = ROOT / ".construcao"
FONTS = ROOT / "node_modules" / "@fontsource"

FONT_CSS = f"""
@font-face {{ font-family: 'Cormorant SC'; font-weight: 700; src: url('file://{FONTS}/cormorant-sc/files/cormorant-sc-latin-700-normal.woff2'); }}
@font-face {{ font-family: 'Cormorant SC'; font-weight: 500; src: url('file://{FONTS}/cormorant-sc/files/cormorant-sc-latin-500-normal.woff2'); }}
@font-face {{ font-family: 'Allura'; src: url('file://{FONTS}/allura/files/allura-latin-400-normal.woff2'); }}
@font-face {{ font-family: 'EB Garamond'; font-weight: 500; src: url('file://{FONTS}/eb-garamond/files/eb-garamond-latin-500-normal.woff2'); }}
@font-face {{ font-family: 'Cinzel'; font-weight: 700; src: url('file://{FONTS}/cinzel/files/cinzel-latin-700-normal.woff2'); }}
@font-face {{ font-family: 'Cinzel'; font-weight: 600; src: url('file://{FONTS}/cinzel/files/cinzel-latin-600-normal.woff2'); }}
@font-face {{ font-family: 'Playfair Display'; font-weight: 700; font-style: italic; src: url('file://{FONTS}/playfair-display/files/playfair-display-latin-700-italic.woff2'); }}
@font-face {{ font-family: 'Playfair Display'; font-weight: 600; src: url('file://{FONTS}/playfair-display/files/playfair-display-latin-600-normal.woff2'); }}
html,body{{margin:0;padding:0;background:transparent}}
svg{{display:block}}
"""


def render(names, bg=None, scale=1.0):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name in names:
            svg = (BUILD / f"{name}.svg").read_text()
            w = int(svg.split('width="')[1].split('"')[0])
            h = int(svg.split('height="')[1].split('"')[0])
            page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)
            back = f"background:{bg};" if bg else ""
            html = f"<!DOCTYPE html><html><head><style>{FONT_CSS} body{{{back}}}</style></head><body>{svg}</body></html>"
            tmp = BUILD / f"_{name}.html"
            tmp.write_text(html)
            page.goto(f"file://{tmp}")
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(400)
            out = BUILD / f"{name}.png"
            page.locator("svg").first.screenshot(path=str(out), omit_background=bg is None)
            page.close()
            print("rendered", out)
        browser.close()


def to_webp(name, dest, quality=84, size=None):
    im = Image.open(BUILD / f"{name}.png")
    if size:
        im = im.resize(size, Image.LANCZOS)
    im.save(dest, "WEBP", quality=quality, method=6)
    print("webp", dest, Path(dest).stat().st_size // 1024, "KB")


if __name__ == "__main__":
    args = sys.argv[1:]
    bg = None
    if args and args[0].startswith("--bg="):
        bg = args[0][5:]
        args = args[1:]
    render(args, bg=bg)
