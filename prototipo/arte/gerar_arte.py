"""Gera as imagens dos temas do protótipo — arte própria, procedural (SVG -> PNG com Chromium -> WebP).

Uso:
    python3 arte/gerar_arte.py              # todos os temas
    python3 arte/gerar_arte.py bela-principe
    python3 arte/gerar_arte.py jardim-rose

Requer: `npm install` (fontes @fontsource) e `pip install -r requirements.txt` + `playwright install chromium`
se o Chromium não estiver disponível. As sementes são fixas: a mesma versão do código gera as mesmas imagens.
"""
import importlib
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arte  # noqa: E402
import papel  # noqa: E402
import render  # noqa: E402

ROOT = arte.ROOT
TEMAS = ROOT / "temas"
B = arte.BUILD


def mascarar(svg, W, H, inicio, dy=0, H0=None, mid="fade"):
    """Envolve o desenho numa máscara que o dissolve no fundo da imagem (a partir de `inicio`, 0–1).
    `dy` desloca o desenho para baixo (folga no topo); `H0` é a altura original antes da folga."""
    head, body = svg.split("</defs>", 1)
    body = body.replace("</svg>", "")
    if H0:
        head = head.replace(f'width="{W}" height="{H0}" viewBox="0 0 {W} {H0}"', f'width="{W}" height="{H}" viewBox="0 0 {W} {H}"')
    fade = (f'<linearGradient id="{mid}g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/>'
            f'<stop offset="{inicio}" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>'
            f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
            f'<rect width="{W}" height="{H}" fill="url(#{mid}g)"/></mask>')
    inner = f'<g transform="translate(0,{dy})">{body}</g>' if dy else body
    return head + fade + f'</defs><g mask="url(#{mid})">' + inner + "</g></svg>"


def gravar(nome, svg):
    B.mkdir(parents=True, exist_ok=True)
    (B / f"{nome}.svg").write_text(svg)


def webp(nome, destino, q=82, rgb=False):
    im = Image.open(B / f"{nome}.png").convert("RGBA")
    (im.convert("RGB") if rgb else im).save(destino, "WEBP", quality=q, method=6)
    print("  ->", destino.relative_to(ROOT), f"{destino.stat().st_size // 1024} KB")


def fundo_papel(papel_path, w, h, topo, base, alpha):
    p = Image.open(papel_path).convert("RGBA").crop((0, 0, w, h)).resize((w, h))
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    for c in range(3):
        arr[..., c] = np.linspace(topo[c], base[c], h)[:, None].astype(np.uint8)
    arr[..., 3] = alpha
    p.alpha_composite(Image.fromarray(arr, "RGBA"))
    return p


def jardim_rose():
    """Tema «Jardim Rosé»: rosas blush e marfim, eucalipto, arco floral com o 15 dourado, vestido rosa."""
    importlib.reload(arte)  # paletas originais
    out = TEMAS / "jardim-rose"
    out.mkdir(parents=True, exist_ok=True)
    print("tema jardim-rose")
    papel.paper(out / "papel.webp", base=(249, 240, 238), deep=(238, 214, 214))
    gravar("jr_canto", arte.corner_a().svg())
    gravar("jr_canto_alt", arte.corner_b().svg())
    gravar("jr_grinalda", arte.garland().svg())
    gravar("jr_ilustracao", mascarar(arte.hero().svg(arte.GOLD_DEFS), 1200, 1000, 0.86))
    cv, _ = arte.gown(fade=False)
    gravar("jr_vestido", mascarar(cv.svg(arte.GOLD_DEFS), 1200, 1270, 0.76, dy=170, H0=1100))
    gravar("jr_vestido_simples", arte.gown(fade=False)[0].svg(arte.GOLD_DEFS))
    gravar("jr_ramo", arte.bouquet().svg())
    render.render(["jr_canto", "jr_canto_alt", "jr_grinalda", "jr_ilustracao", "jr_vestido", "jr_vestido_simples", "jr_ramo"])
    webp("jr_canto", out / "florais-canto.webp")
    webp("jr_canto_alt", out / "florais-canto-alt.webp")
    webp("jr_grinalda", out / "grinalda.webp")
    webp("jr_ilustracao", out / "ilustracao-15.webp")
    webp("jr_vestido", out / "vestido.webp")
    webp("jr_ramo", out / "foto-1.webp", q=84, rgb=True)
    # «fotos» de exemplo para a galeria (substituídas pelas fotografias reais na plataforma)
    arco = Image.open(B / "jr_ilustracao.png").convert("RGBA").crop((290, 150, 910, 925))
    f2 = fundo_papel(out / "papel.webp", arco.width, arco.height, (253, 246, 240), (244, 214, 219), 150)
    f2.alpha_composite(arco)
    f2.convert("RGB").resize((800, 1000), Image.LANCZOS).save(out / "foto-2.webp", "WEBP", quality=84, method=6)
    vest = Image.open(B / "jr_vestido_simples.png").convert("RGBA").crop((160, 40, 1040, 1140))
    f3 = fundo_papel(out / "papel.webp", vest.width, vest.height, (246, 224, 228), (236, 196, 205), 170)
    f3.alpha_composite(vest)
    f3.convert("RGB").resize((800, 1000), Image.LANCZOS).save(out / "foto-3.webp", "WEBP", quality=84, method=6)
    print("  -> fotos de exemplo 2 e 3")


def bela_principe():
    """Tema «A Bela e o Príncipe» — vinho, preto e ouro: rosas vinho/marfim, folhas douradas, arco de balões, espelho."""
    importlib.reload(arte)
    arte.use_wine_theme()
    out = TEMAS / "bela-principe"
    out.mkdir(parents=True, exist_ok=True)
    print("tema bela-principe")
    papel.paper(out / "papel.webp", base=(250, 245, 237), deep=(238, 227, 210))
    gravar("bp_canto", arte.wine_corner(arte.corner_a, [(395, 175, 8, 28), (205, 330, 7, 26), (470, 95, 6, 22)]).svg())
    gravar("bp_canto_alt", arte.wine_corner(arte.corner_b, [(420, 195, 8, 26), (165, 425, 7, 24), (250, 320, 6, 22)]).svg())
    gravar("bp_grinalda", arte.wine_corner(arte.garland, [(430, 180, 8, 28), (790, 190, 8, 28), (610, 330, 6, 24)]).svg())
    gravar("bp_ilustracao", mascarar(arte.hero_baloes().svg(arte.GOLD_DEFS), 1200, 1000, 0.8))
    gravar("bp_espelho", mascarar(arte.espelho().svg(arte.GOLD_DEFS), 1200, 1390, 0.83, dy=95, H0=1300))
    render.render(["bp_canto", "bp_canto_alt", "bp_grinalda", "bp_ilustracao", "bp_espelho"])
    webp("bp_canto", out / "florais-canto.webp")
    webp("bp_canto_alt", out / "florais-canto-alt.webp")
    webp("bp_grinalda", out / "grinalda.webp")
    webp("bp_ilustracao", out / "ilustracao-15.webp")
    webp("bp_espelho", out / "espelho.webp")


if __name__ == "__main__":
    alvo = sys.argv[1] if len(sys.argv) > 1 else "todos"
    if alvo in ("todos", "jardim-rose"):
        jardim_rose()
    if alvo in ("todos", "bela-principe"):
        bela_principe()
