"""Testes ponta a ponta da zona de gestão de convidados e do convite servido pela plataforma.

Uso (a partir de apps/web, depois de `npm run pacote`):
    python3 testes/e2e.py            # arranca o pacote do cPanel (dist/celebramos-web/server.js) duas vezes,
                                     # com a mesma pasta de dados temporária (como vários processos do Passenger)
    python3 testes/e2e.py --capturas # grava capturas em testes/_capturas/

Usa os eventos fictícios do protótipo (PIN 123456) e números de telefone fictícios.
Os IDs entre parênteses são os critérios de docs/07.
"""
import concurrent.futures
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

APP = Path(__file__).resolve().parent.parent
FONTES = APP.parent.parent / "prototipo" / "node_modules" / "@fontsource"
PORTA = 3107
PORTA2 = 3108  # segundo processo com os mesmos dados
BASE = f"http://127.0.0.1:{PORTA}"
BASE2 = f"http://127.0.0.1:{PORTA2}"
SERVIDOR = APP / "dist" / "celebramos-web" / "server.js"
SLUG = "exemplo-bela-principe"
SLUG_GALERIA = "exemplo-jardim-rose"  # tem galeria de fotos
SLUG_PRIVADO = "exemplo-jardim-rose-privado"  # cópia com o link geral desligado
KIT_GALERIA = APP.parent.parent / "prototipo" / "temas" / "jardim-rose"
PIN = "123456"
TEL_FAMILIA = "244900000000"  # fictício
CAPTURAS = APP / "testes" / "_capturas"


class Relatorio:
    def __init__(self):
        self.itens = []

    def ok(self, nome, cond, detalhe=""):
        self.itens.append((bool(cond), nome))
        print(("  PASSA  " if cond else "  FALHA  ") + nome + (f" — {detalhe}" if detalhe and not cond else ""))


def pedido(caminho, metodo="GET", corpo=None, cookie=None, cabecalhos=None, base=None):
    h = {"Content-Type": "application/json"}
    if cookie:
        h["Cookie"] = cookie
    h.update(cabecalhos or {})
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request((base or BASE) + caminho, data=dados, method=metodo, headers=h)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read()
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in e.headers.items()}, e.read()


def entrar(pin=PIN, slug=SLUG):
    estado, cab, corpo = pedido(f"/api/gestao/{slug}/entrar", "POST", {"pin": pin}, cabecalhos={"X-Celebramos": "1"})
    cookie = (cab.get("set-cookie") or "").split(";")[0]
    return estado, cookie, corpo


def preparar_dados(pasta):
    env = {**os.environ, "CELEBRAMOS_DADOS": str(pasta), "PIN": PIN}
    subprocess.run(["node", "scripts/semear-local.mjs"], cwd=APP, env=env, check=True, capture_output=True)
    # botão de confirmação com um número fictício, para testar o registo do toque em «Confirmar»
    ev = pasta / "eventos" / SLUG / "evento.json"
    d = json.loads(ev.read_text())
    d["configuracao"]["confirmacao"]["botoes"][0]["telefone"] = TEL_FAMILIA
    ev.write_text(json.dumps(d))
    # evento com o link geral desligado (cópia do Jardim Rosé, com as fotos): só os links pessoais mostram a galeria
    shutil.copytree(pasta / "eventos" / SLUG_GALERIA, pasta / "eventos" / SLUG_PRIVADO)
    ev = pasta / "eventos" / SLUG_PRIVADO / "evento.json"
    d = json.loads(ev.read_text())
    d["linkGeralActivo"] = False
    ev.write_text(json.dumps(d))


def pagina(browser, w=375, h=812, movel=True):
    ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=2, is_mobile=movel, has_touch=movel)
    pg = ctx.new_page()
    # fontes: o Google Fonts não está acessível nos testes; servir cópias locais (como em prototipo/testes)
    def fontes(route):
        if "fonts.googleapis.com" in route.request.url:
            regras = []
            for familia, pasta, ficheiros in [
                ("Allura", "allura", [("400", "normal", "allura-latin-400-normal")]),
                ("Cormorant SC", "cormorant-sc", [("500", "normal", "cormorant-sc-latin-500-normal"), ("700", "normal", "cormorant-sc-latin-700-normal")]),
                ("EB Garamond", "eb-garamond", [("400", "normal", "eb-garamond-latin-400-normal"), ("500", "normal", "eb-garamond-latin-500-normal"),
                                                 ("400", "italic", "eb-garamond-latin-400-italic"), ("500", "italic", "eb-garamond-latin-500-italic")]),
            ]:
                for peso, estilo, nome in ficheiros:
                    regras.append(f"@font-face{{font-family:'{familia}';font-weight:{peso};font-style:{estilo};src:url(/__fontes/{pasta}/{nome}.woff2) format('woff2')}}")
            route.fulfill(status=200, content_type="text/css", body="".join(regras))
        else:
            route.abort()
    pg.route("https://fonts.googleapis.com/**", fontes)
    pg.route("https://fonts.gstatic.com/**", lambda r: r.abort())

    def ficheiro_fonte(route):
        nome = route.request.url.split("/__fontes/", 1)[1]
        caminho = FONTES / nome.split("/")[0] / "files" / nome.split("/")[1]
        if caminho.exists():
            route.fulfill(status=200, content_type="font/woff2", body=caminho.read_bytes())
        else:
            route.abort()
    pg.route("**/__fontes/**", ficheiro_fonte)
    pg.route("https://wa.me/**", lambda r: r.fulfill(status=200, content_type="text/html", body="whatsapp"))
    erros = []
    pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.on("console", lambda m: erros.append(m.text) if m.type == "error" and "401" not in m.text and "Failed to load resource" not in m.text else None)
    return ctx, pg, erros


def main(capturas=False):
    R = Relatorio()
    if not SERVIDOR.exists():
        sys.exit("Falta o pacote: correr `npm run pacote` primeiro.")
    for base in (BASE, BASE2):
        try:
            urllib.request.urlopen(base + "/robots.txt", timeout=1)
            sys.exit(f"{base} já está ocupado: terminar o servidor antigo primeiro.")
        except urllib.error.URLError:
            pass
    dados = Path(tempfile.mkdtemp(prefix="celebramos-e2e-"))
    preparar_dados(dados)
    servidores = []
    for porta in (PORTA, PORTA2):
        env = {**os.environ, "CELEBRAMOS_DADOS": str(dados), "NODE_ENV": "production", "PORT": str(porta),
               "HOSTNAME": "127.0.0.1", "NEXT_TELEMETRY_DISABLED": "1"}
        # cada servidor num grupo de processos próprio, para o terminar de vez no fim
        servidores.append(subprocess.Popen(["node", str(SERVIDOR)], cwd=SERVIDOR.parent, env=env,
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True))
    try:
        for base in (BASE, BASE2):
            for _ in range(60):
                try:
                    urllib.request.urlopen(base + "/robots.txt", timeout=1)
                    break
                except Exception:
                    time.sleep(0.5)
        if capturas:
            CAPTURAS.mkdir(exist_ok=True)
        correr(R, capturas)
    finally:
        for s in servidores:
            os.killpg(s.pid, signal.SIGTERM)
            s.wait(timeout=10)
        shutil.rmtree(dados, ignore_errors=True)
    falhas = [n for ok, n in R.itens if not ok]
    print(f"\n{len(R.itens) - len(falhas)}/{len(R.itens)} verificações cumpridas")
    return 1 if falhas else 0


def correr(R, capturas):
    print("Convite servido pela plataforma")
    estado, cab, corpo = pedido(f"/c/{SLUG}")
    html = corpo.decode()
    R.ok("link geral responde 200", estado == 200)
    R.ok("noindex e sem referenciador (CA-QUA-04)", cab.get("x-robots-tag") == "noindex, nofollow" and cab.get("referrer-policy") == "no-referrer")
    R.ok("metadados Open Graph com imagem do tema (CA-QUA-04)", 'property="og:title"' in html and f"/temas/bela-principe/og.jpg" in html)
    R.ok("o HTML não leva nomes de convidados de exemplo (CA-PER-04)", "Carlos Neto" not in html and "Rui Mendes" not in html)
    estado404, _, corpo404 = pedido(f"/c/{SLUG}/AAAAAAAAAAAAAAAAAAAAAA")
    estado404b, _, corpo404b = pedido("/c/nao-existe/AAAAAAAAAAAAAAAAAAAAAA")
    R.ok("token ou evento inexistente: 404 igual (CA-PER-05)", estado404 == 404 and estado404b == 404 and corpo404 == corpo404b)
    estado, cab, corpo = pedido(f"/c/{SLUG}/calendario.ics")
    R.ok("calendário .ics (CA-CAL-01)", estado == 200 and cab.get("content-type", "").startswith("text/calendar") and b"BEGIN:VCALENDAR" in corpo and b"TRIGGER:-P1D" in corpo)

    print("Convite: fotos da galeria (do evento, com a regra de acesso do convite)")
    estado, _, corpo = pedido(f"/c/{SLUG_GALERIA}")
    html = corpo.decode()
    fotos = re.findall(rf'"src": "(/c/{SLUG_GALERIA}/img/[^"]+)"', html)
    R.ok("link geral: as 3 fotos da galeria apontam para o evento", estado == 200 and len(fotos) == 3 and '"src": "img/' not in html, f"fotos={fotos}")
    respostas = [pedido(f) for f in fotos]
    R.ok("link geral: as fotos carregam, iguais às enviadas, em cache privada e com noindex",
         len(respostas) == 3 and all(e == 200 and c.get("content-type") == "image/webp" and c.get("cache-control", "").startswith("private")
                                     and c.get("x-robots-tag") == "noindex, nofollow" and b == (KIT_GALERIA / f.rsplit("/", 1)[1]).read_bytes()
                                     for (e, c, b), f in zip(respostas, fotos)))
    foto = fotos[0] if fotos else f"/c/{SLUG_GALERIA}/img/foto-1.webp"
    nome = foto.rsplit("/", 1)[1]
    estado, cab, _ = pedido(foto)
    estado304, _, _ = pedido(foto, cabecalhos={"If-None-Match": cab.get("etag", "")})
    R.ok("foto já vista: 304 pelo ETag", estado == 200 and estado304 == 304)
    nao_existe = pedido(f"/c/nao-existe/img/{nome}")
    geral_desligado = pedido(f"/c/{SLUG_PRIVADO}/img/{nome}")
    token_invalido = pedido(f"/c/{SLUG_PRIVADO}/AAAAAAAAAAAAAAAAAAAAAA/img/{nome}")
    R.ok("link geral desligado ou token inválido: fotos com o 404 do convite (CA-PER-05)",
         nao_existe[0] == geral_desligado[0] == token_invalido[0] == 404 and nao_existe[2] == geral_desligado[2] == token_invalido[2])
    invalidos = ["..%2Fevento.json", "..%2F..%2Fsistema%2Fsegredo-sessao.json", "%2E%2E%2Fconvidados.json", "evento.json", ".escondida.webp", "nao-existe.webp"]
    estados = [pedido(f"/c/{SLUG_GALERIA}/img/{n}")[0] for n in invalidos]
    R.ok("nomes inválidos ou fora da pasta das fotos: 404", estados == [404] * len(invalidos), f"estados={estados}")
    _, cookie_privado, _ = entrar(PIN, SLUG_PRIVADO)
    pedido(f"/api/gestao/{SLUG_PRIVADO}/convidados", "POST", {"nome": "Convidada da galeria", "pessoas": 1},
           cookie=cookie_privado, cabecalhos={"X-Celebramos": "1"})
    _, _, corpo = pedido(f"/api/gestao/{SLUG_PRIVADO}/dados", cookie=cookie_privado)
    token_galeria = json.loads(corpo)["convidados"][0]["token"]
    estado, _, corpo = pedido(f"/c/{SLUG_PRIVADO}/{token_galeria}")
    pessoais = re.findall(rf'"src": "(/c/{SLUG_PRIVADO}/{token_galeria}/img/[^"]+)"', corpo.decode())
    R.ok("link geral desligado: as fotos vêem-se pelo link pessoal", estado == 200 and len(pessoais) == 3 and all(pedido(f)[0] == 200 for f in pessoais),
         f"fotos={pessoais}")

    print("Zona de gestão: acesso")
    estado, _, _ = pedido(f"/api/gestao/{SLUG}/dados")
    R.ok("sem sessão: 401", estado == 401)
    estado, cookie, _ = entrar("000000")
    R.ok("PIN errado: recusado", estado == 401 and not cookie)
    estado, _, _ = pedido(f"/api/gestao/{SLUG}/entrar", "POST", {"pin": PIN})
    R.ok("pedido sem X-Celebramos: 403", estado == 403)
    estado, cookie, _ = entrar()
    R.ok("PIN certo: sessão em cookie HttpOnly", estado == 200 and cookie.startswith("cg_"))

    print("Zona de gestão: concorrência (dois processos, os mesmos dados)")
    def criar(i):
        return pedido(f"/api/gestao/{SLUG}/convidados", "POST", {"nome": f"Convidado paralelo {i}", "pessoas": 2},
                      cookie=cookie, cabecalhos={"X-Celebramos": "1"}, base=BASE if i % 2 else BASE2)[0]
    with concurrent.futures.ThreadPoolExecutor(12) as ex:
        estados = list(ex.map(criar, range(12)))
    _, _, corpo = pedido(f"/api/gestao/{SLUG}/dados", cookie=cookie)
    nomes = [c["nome"] for c in json.loads(corpo)["convidados"]]
    R.ok("12 cadastros em simultâneo em 2 processos: nenhum se perde", estados == [201] * 12 and sum(n.startswith("Convidado paralelo") for n in nomes) == 12,
         f"estados={estados} gravados={sum(n.startswith('Convidado paralelo') for n in nomes)}")
    for c in json.loads(corpo)["convidados"]:
        pedido(f"/api/gestao/{SLUG}/convidados/{c['token']}", "DELETE", cookie=cookie, cabecalhos={"X-Celebramos": "1"})

    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx, pg, erros = pagina(b)
        print("Zona de gestão: interface (telemóvel)")
        pg.goto(f"{BASE}/gestao/{SLUG}")
        pg.wait_for_selector("#pin")
        R.ok("ecrã de entrada com o nome do evento", "15 Anos da Beatriz" in pg.inner_text("main"))
        if capturas:
            pg.screenshot(path=str(CAPTURAS / "00-entrada.png"))
        pg.fill("#pin", "999999")
        pg.click("text=Entrar")
        pg.wait_for_selector("text=PIN errado.")
        R.ok("PIN errado: mensagem", True)
        pg.fill("#pin", PIN)
        pg.click("text=Entrar")
        pg.wait_for_selector("text=Ainda não há convidados.")
        R.ok("PIN certo: painel vazio com instruções", True)
        if capturas:
            pg.screenshot(path=str(CAPTURAS / "01-painel-vazio.png"), full_page=True)

        # cadastrar um convidado
        pg.click("text=+ Adicionar convidado")
        pg.fill("#f-nome", "Sr. Carlos Neto e Família")
        pg.fill("#f-pessoas", "3")
        pg.fill("#f-telefone", "900 000 001")
        pg.fill("#f-grupo", "Família do pai")
        if capturas:
            pg.screenshot(path=str(CAPTURAS / "02-adicionar.png"))
        pg.click("button.b-principal:has-text('Gravar')")
        pg.wait_for_selector("li.cartao:has-text('Sr. Carlos Neto e Família')")
        cartao = pg.locator("li.cartao", has_text="Sr. Carlos Neto e Família")
        R.ok("cadastro: nome, pessoas, grupo e telefone no cartão", "3 pessoas" in cartao.inner_text() and "Família do pai" in cartao.inner_text() and "+244 900 000 001" in cartao.inner_text())

        # colar uma lista
        pg.click("text=Colar lista")
        pg.fill("textarea[aria-label='Lista de convidados']", "Ana e Rui Mendes; 2; Escola\nTia Joana\nFamília Exemplo, 4, 900 000 002\n; 3")
        pg.click("text=Ver como fica")
        pg.wait_for_selector(".previa")
        previa = pg.inner_text(".previa")
        R.ok("colar lista: pré-visualização com 3 válidas e 1 erro", "3 de 4" in previa and "Falta o nome" in previa)
        pg.click("text=Importar 3 convidados")
        pg.wait_for_selector("li.cartao:has-text('Tia Joana')")
        R.ok("colar lista: 4 convidados no total", pg.locator("li.cartao").count() == 4)
        R.ok("resumo: 4 convites · 10 pessoas", "4" in pg.inner_text(".resumo") and "10 pessoas" in pg.inner_text(".resumo"))
        if capturas:
            pg.add_style_tag(content=".aviso{display:none!important}")
            pg.screenshot(path=str(CAPTURAS / "03-lista.png"), full_page=True)

        # link pessoal: copiar, enviar pelo WhatsApp (marca como enviado)
        _, _, corpo = pedido(f"/api/gestao/{SLUG}/dados", cookie=cookie)
        lista = json.loads(corpo)["convidados"]
        carlos = next(c for c in lista if c["nome"] == "Sr. Carlos Neto e Família")
        R.ok("token de 22 caracteres no link pessoal", len(carlos["token"]) == 22 and carlos["link"].endswith(f"/c/{SLUG}/{carlos['token']}"))
        wa = cartao.locator("a.b-whatsapp").get_attribute("href")
        R.ok("WhatsApp: número do convidado e mensagem com o link", wa.startswith("https://wa.me/244900000001?text=") and carlos["token"] in urllib.parse.unquote(wa))
        with ctx.expect_page() as nova:
            cartao.locator("a.b-whatsapp").click()
        nova.value.close()
        pg.wait_for_selector("li.cartao:has-text('Sr. Carlos Neto e Família') >> text=/Enviado \\d/")
        R.ok("enviar pelo WhatsApp marca «Enviado»", True)

        # o convidado abre o link pessoal
        ctx2, pg2, erros2 = pagina(b)
        pg2.goto(carlos["link"])
        pg2.evaluate("document.fonts.ready")
        R.ok("convite pessoal: envelope com o nome (CA-ENV-03, CA-PER-01)", pg2.inner_text(".env-address .nome").strip().upper() == "SR. CARLOS NETO E FAMÍLIA")
        html_pessoal = pg2.content()
        R.ok("convite pessoal: só este convidado no HTML (CA-PER-04)", "Tia Joana" not in html_pessoal and "Ana e Rui" not in html_pessoal)
        if capturas:
            pg2.screenshot(path=str(CAPTURAS / "10-convite-envelope.png"))
        pg2.click("#envelope")
        pg2.wait_for_timeout(2700)
        R.ok("convite pessoal: «válido para 3 pessoas» (CA-PER-02)", "3 pessoas" in pg2.inner_text('[data-g="valido"]'))
        rsvp = pg2.get_attribute("[data-rsvp='0']", "href")
        R.ok("convite pessoal: confirmação com nome e pessoas (CA-RSVP-02/03)", rsvp.startswith(f"https://wa.me/{TEL_FAMILIA}?text=") and "Sr. Carlos Neto e Família (3 pessoas)" in urllib.parse.unquote(rsvp))
        pg2.evaluate("document.querySelector('[data-rsvp]').scrollIntoView()")
        with ctx2.expect_page() as nova:
            pg2.click("[data-rsvp='0']")
        nova.value.close()
        pg2.wait_for_timeout(600)
        R.ok("convite pessoal: sem erros na consola (CA-QUA-01)", not erros2, "; ".join(erros2[:2]))
        ctx2.close()

        pg.reload()
        pg.wait_for_selector("li.cartao:has-text('Sr. Carlos Neto e Família') >> text=/Abriu \\d/")
        cartao = pg.locator("li.cartao", has_text="Sr. Carlos Neto e Família")
        R.ok("painel: «Abriu» e «Tocou em confirmar» (CA-RSVP-05)", "Tocou em confirmar" in cartao.inner_text())

        # ver convite a partir da gestão não conta como abertura
        tia = next(c for c in lista if c["nome"] == "Tia Joana")
        ctx3, pg3, _ = pagina(b)
        pg3.goto(tia["link"] + "?previa=1")
        pg3.wait_for_timeout(500)
        ctx3.close()
        pg.reload()
        pg.wait_for_selector("li.cartao:has-text('Tia Joana')")
        R.ok("«Ver convite» na gestão não conta como abertura", "Não abriu" in pg.locator("li.cartao", has_text="Tia Joana").inner_text())

        # resposta: vem, com número de pessoas
        cartao.get_by_role("button", name="Vem", exact=True).click()
        pg.wait_for_selector("li.cartao.e-confirmado:has-text('Sr. Carlos Neto e Família')")
        pg.locator("li.cartao", has_text="Sr. Carlos Neto e Família").locator("button[aria-label='Menos uma pessoa']").click()
        pg.wait_for_function("document.querySelector('.r-vem strong').textContent === '2'")
        R.ok("resposta «Vem» com 2 pessoas: resumo actualizado", "2" == pg.inner_text(".r-vem strong"))
        pg.locator("li.cartao", has_text="Ana e Rui Mendes").get_by_role("button", name="Não vem", exact=True).click()
        pg.wait_for_selector("li.cartao.e-recusado:has-text('Ana e Rui Mendes')")
        pg.click("button.chip:has-text('Não vêm')")
        R.ok("filtro «Não vêm»", pg.locator("li.cartao").count() == 1)
        pg.click("button.chip:has-text('Todos')")
        pg.fill("input.pesquisa", "joana")
        R.ok("pesquisa por nome (sem acentos)", pg.locator("li.cartao").count() == 1)
        pg.fill("input.pesquisa", "")

        # editar e criar link novo
        link_antigo = tia["link"]
        pg.locator("li.cartao", has_text="Tia Joana").locator("button", has_text="Editar").click()
        pg.fill("#f-nome", "Tia Joana Exemplo")
        pg.click("button.b-principal:has-text('Gravar')")
        pg.wait_for_selector("li.cartao:has-text('Tia Joana Exemplo')")
        pg.locator("li.cartao", has_text="Tia Joana Exemplo").locator("button", has_text="Editar").click()
        pg.click("text=Criar link novo")
        pg.wait_for_selector("text=Link novo criado.")
        R.ok("link novo: o anterior deixa de funcionar (CA-PLA-09)", pedido(link_antigo.replace(BASE, ""))[0] == 404)

        # apagar
        familia = next(c for c in lista if c["nome"] == "Família Exemplo")
        pg.locator("li.cartao", has_text="Família Exemplo").locator("button", has_text="Apagar").click()
        pg.click("button.b-perigo")
        pg.wait_for_selector("text=Convidado apagado.")
        R.ok("apagar: o link deixa de funcionar", pedido(familia["link"].replace(BASE, ""))[0] == 404 and pg.locator("li.cartao").count() == 3)

        # mensagem do WhatsApp
        pg.click("text=Mensagem do WhatsApp")
        pg.fill("textarea[aria-label='Mensagem']", "Olá {convidado}! Convite: {link}")
        pg.click(".j button.b-principal:has-text('Gravar')")
        pg.wait_for_selector("text=Mensagem gravada.")
        wa = pg.locator("li.cartao", has_text="Ana e Rui Mendes").locator("a.b-whatsapp").get_attribute("href")
        R.ok("mensagem personalizada usada no envio", urllib.parse.unquote(wa).split("text=", 1)[1].startswith("Olá Ana e Rui Mendes! Convite: http"))

        # exportar
        estado, cab, corpo = pedido(f"/api/gestao/{SLUG}/exportar", cookie=cookie)
        texto = corpo.decode("utf-8")
        R.ok("exportar CSV para Excel (CA-PLA-08)", estado == 200 and texto.startswith("\ufeffNome;Pessoas;Telefone;Grupo;Estado") and "Sr. Carlos Neto e Família;3;+244 900 000 001;Família do pai;Confirmado;2" in texto)
        if capturas:
            pg.screenshot(path=str(CAPTURAS / "04-painel.png"), full_page=True)

        # computador
        ctx4, pg4, erros4 = pagina(b, 1366, 900, movel=False)
        ctx4.add_cookies([{"name": cookie.split("=")[0], "value": cookie.split("=", 1)[1], "url": BASE}])
        pg4.goto(f"{BASE}/gestao/{SLUG}")
        pg4.wait_for_selector("li.cartao")
        largura = pg4.evaluate("document.querySelector('.painel').getBoundingClientRect().width")
        R.ok("computador: painel centrado e legível", 600 < largura <= 740)
        if capturas:
            pg4.screenshot(path=str(CAPTURAS / "05-computador.png"))
        R.ok("gestão sem erros na consola", not erros and not erros4, "; ".join((erros + erros4)[:2]))
        ctx4.close()

        # sair
        pg.click("text=Sair")
        pg.wait_for_selector("#pin")
        R.ok("sair: volta ao ecrã de entrada", True)

        # 320 px: sem transbordo
        ctx5, pg5, _ = pagina(b, 320, 640)
        ctx5.add_cookies([{"name": cookie.split("=")[0], "value": cookie.split("=", 1)[1], "url": BASE}])
        pg5.goto(f"{BASE}/gestao/{SLUG}")
        pg5.wait_for_selector("li.cartao")
        fora = pg5.evaluate("[...document.querySelectorAll('.painel *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.right>innerWidth+1&&!e.closest('.filtros')}).length")
        R.ok("320 px: sem transbordo horizontal", fora == 0, f"fora={fora}")
        ctx5.close()

        # galeria no telemóvel: as fotos aparecem (a consola não mostra recursos em falta, por isso ver as respostas)
        ctx6, pg6, _ = pagina(b)
        falhadas = []
        pg6.on("response", lambda r: falhadas.append(f"{r.status} {r.url}") if r.status >= 400 and "/img/" in r.url else None)
        pg6.goto(f"{BASE}/c/{SLUG_PRIVADO}/{token_galeria}?previa=1")
        pg6.click("#envelope")
        pg6.wait_for_timeout(2700)
        pg6.evaluate("document.querySelector('[data-seccao=galeria]').scrollIntoView()")
        carregadas = "[...document.querySelectorAll('#galeria img')].filter(i => i.complete && i.naturalWidth > 0).length"
        try:
            pg6.wait_for_function(f"{carregadas} === 3", timeout=10_000)
        except Exception:
            pass
        vistas = pg6.evaluate(carregadas)
        R.ok("galeria no telemóvel: as 3 fotos aparecem, sem pedidos falhados", vistas == 3 and not falhadas, f"vistas={vistas} {'; '.join(falhadas[:2])}")
        if capturas:
            pg6.screenshot(path=str(CAPTURAS / "11-convite-galeria.png"))
        ctx6.close()
        ctx.close()
        b.close()

    # bloqueio depois de 10 PIN errados (outro evento, para não afectar os testes acima)
    for _ in range(10):
        entrar("111111", "exemplo-jardim-rose")
    estado, _, corpo = entrar(PIN, "exemplo-jardim-rose")
    R.ok("10 PIN errados: bloqueio temporário, mesmo com o PIN certo", estado == 429, f"estado={estado} {corpo[:80]!r}")


if __name__ == "__main__":
    sys.exit(main("--capturas" in sys.argv))
