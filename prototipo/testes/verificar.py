"""Verificação automática de um convite construído (critérios de aceitação do docs/07).

Uso:
    python3 testes/verificar.py exemplos/exemplo-bela-principe            # verifica
    python3 testes/verificar.py exemplos/exemplo-bela-principe --capturas # verifica e grava capturas em <pasta>/_capturas

Serve a pasta num servidor local, troca as Google Fonts por cópias locais (node_modules/@fontsource) e
corre os testes em Chromium (Playwright). Termina com código ≠ 0 se algum critério falhar.
"""
import http.server
import json
import socketserver
import sys
import threading
import urllib.parse
from functools import partial
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FONTES = ROOT / "node_modules" / "@fontsource"
PORTA = 8765
F = f"http://127.0.0.1:{PORTA}/__fontes"
CSS_FONTES = f"""
@font-face{{font-family:'Allura';src:url({F}/allura/files/allura-latin-400-normal.woff2) format('woff2')}}
@font-face{{font-family:'Cormorant SC';font-weight:500;src:url({F}/cormorant-sc/files/cormorant-sc-latin-500-normal.woff2) format('woff2')}}
@font-face{{font-family:'Cormorant SC';font-weight:700;src:url({F}/cormorant-sc/files/cormorant-sc-latin-700-normal.woff2) format('woff2')}}
@font-face{{font-family:'EB Garamond';font-weight:400;src:url({F}/eb-garamond/files/eb-garamond-latin-400-normal.woff2) format('woff2')}}
@font-face{{font-family:'EB Garamond';font-weight:500;src:url({F}/eb-garamond/files/eb-garamond-latin-500-normal.woff2) format('woff2')}}
@font-face{{font-family:'EB Garamond';font-style:italic;font-weight:400;src:url({F}/eb-garamond/files/eb-garamond-latin-400-italic.woff2) format('woff2')}}
@font-face{{font-family:'EB Garamond';font-style:italic;font-weight:500;src:url({F}/eb-garamond/files/eb-garamond-latin-500-italic.woff2) format('woff2')}}
"""


class Servidor(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if path.startswith("/__fontes/"):
            return str(FONTES / path[len("/__fontes/"):].split("?")[0])
        return super().translate_path(path)

    def log_message(self, *a):
        pass


def servir(pasta):
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORTA), partial(Servidor, directory=str(pasta)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def pagina(browser, w, h, movel=True):
    ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=2, is_mobile=movel, has_touch=movel)
    pg = ctx.new_page()
    pg.route("https://fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=CSS_FONTES))
    pg.route("https://fonts.gstatic.com/**", lambda r: r.abort())
    erros = []
    pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
    return ctx, pg, erros


class Relatorio:
    def __init__(self):
        self.itens = []

    def ok(self, nome, cond, detalhe=""):
        self.itens.append((bool(cond), nome, detalhe))
        print(("  PASSA  " if cond else "  FALHA  ") + nome + (f" — {detalhe}" if detalhe else ""))


def main(pasta, capturas=False):
    pasta = Path(pasta).resolve()
    cfg = json.loads((pasta / "index.html").read_text().split("const CONFIG = ", 1)[1].split(";\n(function", 1)[0])
    ordem = cfg.get("seccoes") or ["mensagem", "convite", "confirmacao", "galeria", "cronograma", "contagem", "manual", "presentes", "obrigada"]
    if not cfg["galeria"]["fotos"]:
        ordem = [s for s in ordem if s != "galeria"]
    out = pasta / "_capturas"
    if capturas:
        out.mkdir(exist_ok=True)
    R = Relatorio()
    httpd = servir(pasta)
    base = f"http://127.0.0.1:{PORTA}/index.html"
    print(f"Convite: {cfg['id']}")
    with sync_playwright() as p:
        b = p.chromium.launch()

        # 1. abertura do envelope
        ctx, pg, erros = pagina(b, 375, 812)
        pg.goto(base)
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(400)
        R.ok("ecrã de abertura visível no primeiro acesso", pg.locator("#abertura").count() == 1)
        R.ok("conteúdo bloqueado (inert + scroll) enquanto o envelope está fechado",
             pg.evaluate("document.querySelector('main').hasAttribute('inert') && document.documentElement.style.overflow==='hidden'"))
        nome_env = pg.inner_text(".env-address .nome")
        esperado = cfg["convidados"][cfg["convidadoDemonstracao"]]["nome"] if cfg.get("demonstracao") and cfg.get("convidadoDemonstracao") else cfg["convidadoGenerico"]
        R.ok("envelope endereçado ao convidado", nome_env.strip().upper() == esperado.upper(), nome_env)
        if capturas:
            pg.screenshot(path=str(out / "00-envelope.png"))
        pg.evaluate("""window.__anims=[];const o=Element.prototype.animate;Element.prototype.animate=function(k,op){
            var c=this.className;window.__anims.push({el:(this.id||(c&&c.baseVal!==undefined?c.baseVal:c)||'').toString(),d:op&&op.duration,e:op&&op.easing});return o.call(this,k,op)};'ok'""")
        pg.click("#envelope")
        if capturas:
            pg.wait_for_timeout(1250)
            pg.screenshot(path=str(out / "01-a-abrir.png"))
        pg.wait_for_timeout(2600)
        anims = pg.evaluate("window.__anims")
        seq = [(a["el"], a["d"]) for a in anims]
        R.ok("sequência selo 500 ms → aba 600 ms → carta 650 ms → fade 550 ms",
             [d for _, d in seq] == [500, 600, 650, 550] and "selo" in seq[0][0] and "aba" in seq[1][0] and "carta" in seq[2][0], str(seq))
        R.ok("ecrã de abertura removido e conteúdo desbloqueado",
             pg.locator("#abertura").count() == 0 and not pg.evaluate("document.querySelector('main').hasAttribute('inert')"))
        R.ok("foco no título do convite após abrir", pg.evaluate("document.activeElement.id") == "convite-titulo")
        reais = pg.evaluate("[...document.querySelectorAll('main > section')].map(s=>s.dataset.seccao)")
        R.ok("ordem das secções igual à configuração", reais == ordem, f"{reais}")
        R.ok("primeira secção visível no topo após abrir", pg.evaluate("Math.round(document.querySelector('main > section').getBoundingClientRect().top)") == 0)

        # 1b. capturas das secções (e das transições)
        if capturas:
            pg.evaluate("document.documentElement.style.scrollSnapType='none'")
            tops = pg.evaluate("[...document.querySelectorAll('main > section')].map(s=>Math.round(s.getBoundingClientRect().top+scrollY))")
            for i, t in enumerate(tops):
                pg.evaluate(f"window.scrollTo(0,{t})")
                pg.wait_for_timeout(350)
                pg.screenshot(path=str(out / f"1{i}-{reais[i]}.png"))
            for i, t in enumerate(tops[1:]):
                pg.evaluate(f"window.scrollTo(0,{t - 406})")
                pg.wait_for_timeout(350)
                pg.screenshot(path=str(out / f"2{i}-transicao-{reais[i]}-{reais[i + 1]}.png"))

        # 2. confirmação por WhatsApp
        hrefs = pg.evaluate("[...document.querySelectorAll('[data-rsvp]')].map(a=>a.getAttribute('href'))")
        R.ok("botões de confirmação = configuração", len(hrefs) == len(cfg["confirmacao"]["botoes"]))
        for bt, h in zip(cfg["confirmacao"]["botoes"], hrefs):
            tel = "".join(ch for ch in bt.get("telefone", "") if ch.isdigit())
            if tel:
                R.ok(f"link WhatsApp correcto ({bt['rotulo']})", h.startswith(f"https://wa.me/{tel}?text="), h[:60])
            else:
                pg.click('[data-rsvp="0"]')
                pg.wait_for_timeout(300)
                R.ok("sem número: aviso de pré-visualização em vez de link partido", "on" in pg.get_attribute("#aviso", "class"))

        # 3. calendário, mapas, contagem
        cal = pg.get_attribute("#cal-principal", "href")
        R.ok("botão de calendário configurado", (cal == cfg["calendario"].get("ics")) or cal.startswith("https://calendar.google.com/"), cal[:60])
        mapas = pg.evaluate("[...document.querySelectorAll('#eventos a')].map(a=>a.href)")
        com_local = [e for e in cfg["eventos"] if e.get("mapa") or e.get("coordenadas")]
        R.ok("Google Maps + Waze por cada evento com local (e nenhum sem local)", len(mapas) == 2 * len(com_local), f"{len(mapas)} links")
        s1 = pg.inner_text('[data-cd="s"]')
        pg.wait_for_timeout(1100)
        R.ok("contagem regressiva a actualizar", pg.inner_text('[data-cd="s"]') != s1 or pg.evaluate("Date.now()>new Date(CONFIG.data.iso).getTime()"))

        # 4. galeria (se houver fotos)
        if cfg["galeria"]["fotos"]:
            pg.evaluate("document.querySelector('[data-seccao=galeria]').scrollIntoView()")
            pg.wait_for_timeout(400)
            pg.click(".gal-frame[data-i='1']")
            pg.wait_for_timeout(500)
            R.ok("galeria abre em ecrã inteiro na foto tocada", pg.evaluate("document.getElementById('lb').open") and pg.inner_text("#lb-count").startswith("Foto 2"))
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(300)
        R.ok("sem erros na consola", not erros, "; ".join(erros[:3]))

        # 6. regresso na mesma sessão: o envelope não volta a aparecer
        pg.reload()
        pg.wait_for_timeout(400)
        R.ok("na mesma sessão o envelope não volta a aparecer", pg.locator("#abertura").count() == 0)
        ctx.close()

        # 7. link pessoal (#código)
        for codigo, conv in list(cfg["convidados"].items())[:2]:
            ctx, pg, erros = pagina(b, 375, 812)
            pg.goto(base + "#" + codigo)
            pg.wait_for_timeout(300)
            R.ok(f"link pessoal #{codigo} mostra o nome", pg.inner_text(".convidado p").upper() == conv["nome"].upper())
            if conv.get("pessoas"):
                R.ok(f"link pessoal #{codigo} mostra o número de pessoas", str(conv["pessoas"]) in pg.inner_text('[data-g="valido"]'))
            msg = pg.evaluate("(document.querySelector('[data-rsvp]')||{}).getAttribute ? document.querySelector('[data-rsvp]').getAttribute('href') : ''")
            if "text=" in msg:
                R.ok(f"mensagem de WhatsApp leva o nome de #{codigo}", conv["nome"] in urllib.parse.unquote(msg.split("text=")[1]))
            ctx.close()

        # 8. larguras de telemóvel: sem transbordo horizontal; data numa só linha
        for w, h in [(320, 568), (360, 740), (375, 812), (430, 932)]:
            ctx, pg, erros = pagina(b, w, h)
            pg.goto(base)
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(300)
            pg.click("#envelope")
            pg.wait_for_timeout(2500)
            fora = pg.evaluate("[...document.querySelectorAll('main *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.right>innerWidth+1&&!e.closest('.decor')&&!e.closest('.gal')}).length")
            datas = pg.evaluate("[...document.querySelectorAll('.data time')].map(t=>t.getBoundingClientRect().height < parseFloat(getComputedStyle(t).fontSize)*1.6)")
            R.ok(f"{w}px: sem transbordo horizontal e data numa linha", fora == 0 and all(datas), f"fora={fora}")
            ctx.close()

        # 9. computador: cartão centrado tipo telemóvel
        ctx, pg, erros = pagina(b, 1366, 900, movel=False)
        pg.goto(base)
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(400)
        larg = pg.evaluate("document.querySelector('.card').getBoundingClientRect().width")
        R.ok("computador: convite num cartão de 27rem", abs(larg - 432) < 2, f"{larg}px")
        if capturas:
            pg.screenshot(path=str(out / "30-computador-envelope.png"))
            pg.click("#envelope")
            pg.wait_for_timeout(2600)
            pg.screenshot(path=str(out / "31-computador-aberto.png"))
        ctx.close()
        b.close()
    httpd.shutdown()

    falhas = [n for ok, n, _ in R.itens if not ok]
    print(f"\n{len(R.itens) - len(falhas)}/{len(R.itens)} critérios cumpridos")
    return 1 if falhas else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], "--capturas" in sys.argv))
