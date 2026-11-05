"""Gera a imagem de partilha (Open Graph, 1200 × 630, JPEG) de cada tema a partir do kit do tema.

Uso:
    python3 arte/gerar_og.py                 # todos os temas
    python3 arte/gerar_og.py bela-principe

A imagem não tem texto nem dados pessoais: o título do convite vai em og:title.
"""
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
TEMAS = ROOT / "temas"
BUILD = ROOT / ".construcao"

HTML = """<!DOCTYPE html><html><head><style>
html,body{margin:0;width:1200px;height:630px;overflow:hidden}
body{position:relative;background:url(papel.webp) center/1200px auto}
img{position:absolute}
.arte{left:50%;bottom:-30px;height:660px;transform:translateX(-50%)}
.c1{top:-14px;left:-14px;width:330px}
.c2{bottom:-14px;right:-14px;width:330px;transform:scale(-1)}
</style></head><body>
<img class="c1" src="florais-canto.webp"><img class="c2" src="florais-canto-alt.webp">
<img class="arte" src="ilustracao-15.webp">
</body></html>"""


def gerar(tema):
    pasta = TEMAS / tema
    BUILD.mkdir(exist_ok=True)
    pagina = pasta / "_og.html"
    pagina.write_text(HTML)
    png = BUILD / f"og-{tema}.png"
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1200, "height": 630})
            pg.goto(pagina.as_uri())
            pg.wait_for_load_state("networkidle")
            pg.screenshot(path=str(png))
            b.close()
    finally:
        pagina.unlink(missing_ok=True)
    destino = pasta / "og.jpg"
    Image.open(png).convert("RGB").save(destino, "JPEG", quality=84, optimize=True, progressive=True)
    print(f"  -> {destino.relative_to(ROOT)} {destino.stat().st_size // 1024} KB")


if __name__ == "__main__":
    temas = sys.argv[1:] or sorted(p.name for p in TEMAS.iterdir() if p.is_dir())
    for t in temas:
        gerar(t)
