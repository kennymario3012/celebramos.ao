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

SLUG_FECHADO = "exemplo-bela-principe-fechado"  # cópia com o prazo de confirmação já passado
SLUG_IMPORTAR = "exemplo-bela-principe-importar"  # cópia para a importação de ficheiros, com a lista à parte
X = {"X-Celebramos": "1"}


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


def responder(token, corpo, slug=SLUG, base=None):
    """Resposta do convidado dentro do convite (POST /c/<slug>/<token>/resposta). `corpo`: dicionário ou bytes."""
    dados = corpo if isinstance(corpo, bytes) else json.dumps(corpo).encode()
    req = urllib.request.Request(f"{base or BASE}/c/{slug}/{token}/resposta", data=dados, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def preparar_prazos(pasta):
    """Prazos de confirmação fixos, para os testes não dependerem da data de hoje: o evento principal
    aceita respostas até 2099 e uma cópia dele, com o prazo já passado, tem o formulário fechado."""
    ev = pasta / "eventos" / SLUG / "evento.json"
    d = json.loads(ev.read_text())
    d["configuracao"]["data"]["iso"] = "2099-05-15T17:00:00+01:00"
    d["configuracao"]["confirmacao"]["ate"] = "1 de Maio de 2099"
    ev.write_text(json.dumps(d))
    shutil.copytree(pasta / "eventos" / SLUG, pasta / "eventos" / SLUG_FECHADO)
    ev = pasta / "eventos" / SLUG_FECHADO / "evento.json"
    d["configuracao"]["confirmacao"]["ate"] = "1 de Janeiro de 2020"
    ev.write_text(json.dumps(d))


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
    shutil.copytree(pasta / "eventos" / SLUG, pasta / "eventos" / SLUG_IMPORTAR)


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
    # no contexto, para valer também nos separadores novos que o convite abre
    ctx.route("https://wa.me/**", lambda r: r.fulfill(status=200, content_type="text/html", body="whatsapp"))
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
    preparar_prazos(dados)
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
    R.ok("link geral: confirmação só pelo WhatsApp, sem formulário (CA-RSVP-09)", '"responder":' not in html and '"convidadoActual":' not in html)
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

    print("Convite: resposta dentro do convite (pedidos)")
    def lista_api(slug=SLUG, ck=None):
        return json.loads(pedido(f"/api/gestao/{slug}/dados", cookie=ck or cookie)[2])["convidados"]

    def novo(nome, pessoas, slug=SLUG, ck=None):
        pedido(f"/api/gestao/{slug}/convidados", "POST", {"nome": nome, "pessoas": pessoas}, cookie=ck or cookie, cabecalhos=X)
        return next(c for c in lista_api(slug, ck) if c["nome"] == nome)

    t = novo("Convidado da API", 2)["token"]
    html_api = pedido(f"/c/{SLUG}/{t}")[2].decode()
    html_previa = pedido(f"/c/{SLUG}/{t}?previa=1")[2].decode()
    R.ok("link pessoal: formulário com o caminho da resposta; a pré-visualização não grava (CA-RSVP-06/09)",
         f'"caminho": "/c/{SLUG}/{t}/resposta"' in html_api and '"responder": {}' in html_previa)
    desconhecido, pagina404 = responder("AAAAAAAAAAAAAAAAAAAAAA", {"estado": "confirmado"}), pedido(f"/c/{SLUG}/AAAAAAAAAAAAAAAAAAAAAA")
    R.ok("resposta com token desconhecido: o mesmo 404 do convite (CA-RSVP-10)", desconhecido[0] == 404 and desconhecido[1] == pagina404[2])
    invalidos = [{"estado": "talvez"}, {"estado": "confirmado", "pessoas": 3}, {"estado": "confirmado", "pessoas": 0},
                 {"estado": "confirmado", "pessoas": "2a"}, {"estado": "recusado", "mensagem": "x" * 301}, b"nao e json", b"[]", b"null"]
    estados = [responder(t, c)[0] for c in invalidos]
    c_api = next(c for c in lista_api() if c["token"] == t)
    R.ok("resposta inválida: 400 sem gravar (pessoas até ao número do convite, mensagem até 300)",
         estados == [400] * len(invalidos) and c_api["estado"] == "pendente" and "resposta" not in c_api, f"estados={estados}")
    estado, _ = responder(t, {"estado": "recusado", "mensagem": "  Boa   festa!  "})
    c_api = next(c for c in lista_api() if c["token"] == t)
    R.ok("resposta válida: 204, estado «não vem» e a mensagem guardada com a data",
         estado == 204 and c_api["estado"] == "recusado" and c_api["resposta"]["mensagem"] == "Boa festa!" and c_api["resposta"]["em"])
    seguidas = [responder(t, {"estado": "confirmado", "pessoas": 1})[0] for _ in range(9)]
    R.ok("mais de 10 respostas numa hora no mesmo link: 429 (CA-RSVP-10)", seguidas == [204] * 9 and responder(t, {"estado": "recusado"})[0] == 429,
         f"seguidas={seguidas}")

    simultaneos = [novo(f"Convidado em simultâneo {i}", 3)["token"] for i in range(6)]
    def tarefa(i):
        base = BASE if i % 2 else BASE2
        if i < 6:
            return responder(simultaneos[i], {"estado": "confirmado", "pessoas": 2}, base=base)[0]
        return pedido(f"/api/gestao/{SLUG}/convidados", "POST", {"nome": f"Família em simultâneo {i}"}, cookie=cookie, cabecalhos=X, base=base)[0]
    with concurrent.futures.ThreadPoolExecutor(12) as ex:
        estados = list(ex.map(tarefa, range(12)))
    todos = lista_api()
    gravadas = sum(c["token"] in simultaneos and c["estado"] == "confirmado" and c.get("pessoasConfirmadas") == 2 for c in todos)
    cadastros = sum(c["nome"].startswith("Família em simultâneo") for c in todos)
    R.ok("6 respostas de convidados e 6 cadastros da família em simultâneo, em 2 processos: nada se perde (CA-GES-17)",
         estados == [204] * 6 + [201] * 6 and gravadas == 6 and cadastros == 6, f"estados={estados} gravadas={gravadas} cadastros={cadastros}")
    for c in todos:
        pedido(f"/api/gestao/{SLUG}/convidados/{c['token']}", "DELETE", cookie=cookie, cabecalhos=X)

    _, cookie_fechado, _ = entrar(PIN, SLUG_FECHADO)
    fora_do_prazo = novo("Convidado fora do prazo", 2, SLUG_FECHADO, cookie_fechado)
    html_fechado = pedido(f"/c/{SLUG_FECHADO}/{fora_do_prazo['token']}")[2].decode()
    R.ok("depois do prazo: formulário fechado e respostas recusadas com 410 (CA-RSVP-08)",
         '"fechado": true' in html_fechado and responder(fora_do_prazo["token"], {"estado": "confirmado"}, slug=SLUG_FECHADO)[0] == 410)

    print("Zona de gestão: importar ficheiro CSV (pedidos)")
    _, cookie_imp, _ = entrar(PIN, SLUG_IMPORTAR)

    def importar(texto, confirmar=False, formato="csv"):
        corpo = {"texto": texto, "formato": formato, **({"confirmar": True} if confirmar else {})}
        estado, _, resposta = pedido(f"/api/gestao/{SLUG_IMPORTAR}/convidados/importar", "POST", corpo, cookie=cookie_imp, cabecalhos=X)
        return estado, json.loads(resposta)

    estado, cab, corpo = pedido(f"/api/gestao/{SLUG_IMPORTAR}/convidados/modelo", cookie=cookie_imp)
    modelo = corpo.decode("utf-8")
    R.ok("modelo CSV para o Excel: BOM, «;», os títulos das colunas e 2 exemplos; sem sessão, 401 (CA-GES-18)",
         estado == 200 and cab.get("content-type", "").startswith("text/csv") and 'filename="modelo-convidados.csv"' in cab.get("content-disposition", "")
         and modelo.startswith("\ufeffNome no convite;Pessoas;Telefone (WhatsApp);Grupo;Notas (só para a família)\r\n") and modelo.count("\r\n") == 3
         and pedido(f"/api/gestao/{SLUG_IMPORTAR}/convidados/modelo")[0] == 401, modelo[:120])
    estado, r = importar(modelo)
    R.ok("o modelo por preencher: os 2 exemplos ficam de fora (CA-GES-18)",
         estado == 200 and [(l["ok"], l.get("ignorada"), l.get("erro")) for l in r["linhas"]] == [(False, True, "Exemplo do modelo: apague esta linha.")] * 2, r)

    pedido(f"/api/gestao/{SLUG_IMPORTAR}/convidados", "POST", {"nome": "Sr. Exemplo Já Cadastrado", "pessoas": 2, "telefone": "900 000 109"},
           cookie=cookie_imp, cabecalhos=X)
    csv = ("\ufeffNome no convite;Pessoas;Telefone (WhatsApp);Grupo;Notas (só para a família)\r\n"
           '"Família Neto; ramo de Benguela";4;+244 900 000 101;Família do pai;"Disse ""talvez"""\r\n'
           "Avó Rosa;1;900000102;Família da mãe;\r\n"
           ";;;;\r\n"
           "Primos Exemplo;3 pessoas;00244 900 000 103;;\r\n"
           "Tio Exemplo;2;2,44900E+11;;\r\n"
           ";2;900 000 104;;\r\n"
           "Madrinha Exemplo;0;;;\r\n"
           "Vizinhos Exemplo;2;244 900 000 101;Vizinhos;\r\n"
           "avó rosa;1;;;\r\n"
           "Sr. Exemplo já cadastrado;2;;;\r\n"
           "Esposa do Sr. Exemplo;1;900 000 109;;\r\n")
    estado, r = importar(csv)
    por_linha = {l["linha"]: l for l in r.get("linhas", [])}
    def campo(n, nome):
        return por_linha.get(n, {}).get("convidado", {}).get(nome)
    R.ok("CSV com «;», BOM, aspas e linhas vazias: os campos certos e o número da linha do Excel (CA-GES-19)",
         estado == 200 and sorted(por_linha) == [2, 3, 5, 6, 7, 8, 9, 10, 11, 12] and campo(2, "nome") == "Família Neto; ramo de Benguela"
         and campo(2, "pessoas") == 4 and campo(2, "grupo") == "Família do pai" and campo(2, "notas") == 'Disse "talvez"' and campo(5, "pessoas") == 3, r)
    R.ok("telefones com +244, 00244, 244 ou só os 9 algarismos, com ou sem espaços (CA-GES-19)",
         [campo(n, "telefone") for n in (2, 3, 5, 9)] == ["244900000101", "244900000102", "244900000103", "244900000101"])
    erros_csv = {n: por_linha.get(n, {}) for n in (6, 7, 8)}
    R.ok("erros por linha: telefone estragado pelo Excel, nome em falta, pessoas fora do limite (CA-GES-18)",
         all(l.get("ok") is False and not l.get("ignorada") for l in erros_csv.values())
         and erros_csv[6].get("erro", "").startswith("O Excel transformou o telefone em «2,44900E+11».")
         and erros_csv[7].get("erro") == "Falta o nome." and "entre 1 e 30" in erros_csv[8].get("erro", ""), erros_csv)
    R.ok("repetidos: o nome de alguém da lista ou de uma linha anterior fica de fora; o mesmo telefone só é assinalado (CA-GES-18)",
         por_linha.get(10, {}).get("ignorada") and por_linha[10].get("erro") == "Repete a linha 3."
         and por_linha.get(11, {}).get("ignorada") and por_linha[11].get("erro") == "Já está na lista."
         and por_linha.get(9, {}).get("aviso") == "Mesmo telefone que a linha 2."
         and por_linha.get(12, {}).get("aviso") == "Mesmo telefone que «Sr. Exemplo Já Cadastrado».", [por_linha.get(n) for n in (9, 10, 11, 12)])
    _, virgulas = importar('Telemóvel,Nome,Etiqueta,Observações,Pessoas\n900 000 121,"Ana, Rui e filhos",Escola,,4\n')
    _, tabulacoes = importar("Nome\tPessoas\tTelefone\r\nPrimo Exemplo\t2\t900 000 122\r\n")
    R.ok("CSV com «,» (Google Sheets) ou tabulação, colunas por outra ordem e outros títulos (CA-GES-19)",
         [l.get("convidado") for l in virgulas.get("linhas", [])] == [{"nome": "Ana, Rui e filhos", "pessoas": 4, "telefone": "244900000121", "grupo": "Escola"}]
         and [l.get("convidado") for l in tabulacoes.get("linhas", [])] == [{"nome": "Primo Exemplo", "pessoas": 2, "telefone": "244900000122"}],
         f"{virgulas} {tabulacoes}")
    estado, r = importar("Tia Exemplo;2;900 000 131\nSobrinho Exemplo\n")
    R.ok("CSV sem a linha dos títulos: cada linha lida como em «Colar lista», com um aviso",
         estado == 200 and r.get("semTitulos") is True and [l.get("convidado") for l in r["linhas"]]
         == [{"nome": "Tia Exemplo", "pessoas": 2, "telefone": "244900000131"}, {"nome": "Sobrinho Exemplo", "pessoas": 1}], r)
    invalidos = {
        "vazio": ("", "O ficheiro está vazio."),
        "só os títulos": ("Nome no convite;Pessoas\r\n;;\r\n", "O ficheiro só tem a linha dos títulos."),
        "sem a coluna do nome": ("Pessoas;Telefone;Grupo\n2;900 000 141;Escola\n", "Falta a coluna «Nome no convite»."),
        "aspas por fechar": ('Nome;Pessoas\n"Tia Exemplo;2\n', "Há umas aspas por fechar na linha 2."),
        "binário": ("PK\x03\x04\x00\x00", "Este ficheiro não parece uma lista de convidados em CSV."),
        "mais de 500 KB": ("Nome\n" + "x" * 500_000, "O ficheiro é grande demais (máximo 500 KB)."),
        "mais de 1000 linhas": ("Nome\n" + "".join(f"Convidado {i}\n" for i in range(1001)), "O ficheiro tem mais de 1000 convidados"),
        "a lista passaria de 1000": ("Nome\n" + "".join(f"Convidado {i}\n" for i in range(1000)), "A lista passaria de 1000 convidados: já tem 1"),
    }
    respostas = {k: importar(texto) for k, (texto, _) in invalidos.items()}
    falhas = [k for k, (_, msg) in invalidos.items() if respostas[k][0] != 400 or not respostas[k][1].get("erro", "").startswith(msg)]
    R.ok("ficheiro vazio, inválido, grande demais ou que passa de 1000 convidados: 400 com uma mensagem clara (CA-GES-19)",
         not falhas, "; ".join(f"{k}: {respostas[k]}" for k in falhas)[:300])
    estado, r = importar(csv, confirmar=True)
    importados_api = lista_api(SLUG_IMPORTAR, cookie_imp)
    R.ok("importar grava só as linhas prontas, cada uma com o seu link (CA-GES-18)",
         estado == 200 and r == {"criados": 5, "ignoradas": 5} and len({c["token"] for c in importados_api}) == 6
         and sorted(c["nome"] for c in importados_api) == sorted(["Sr. Exemplo Já Cadastrado", "Família Neto; ramo de Benguela", "Avó Rosa",
                                                                  "Primos Exemplo", "Vizinhos Exemplo", "Esposa do Sr. Exemplo"]), r)
    estado_outra_vez, outra_vez = importar(csv, confirmar=True)
    _, exportado = importar(pedido(f"/api/gestao/{SLUG_IMPORTAR}/exportar", cookie=cookie_imp)[2].decode("utf-8"))
    R.ok("importar o mesmo ficheiro outra vez não duplica ninguém, e o CSV exportado volta a ser lido (CA-GES-18)",
         estado_outra_vez == 400 and outra_vez.get("erro") == "Estes convidados já estão na lista." and len(lista_api(SLUG_IMPORTAR, cookie_imp)) == 6
         and [(l.get("ignorada"), l.get("erro")) for l in exportado.get("linhas", [])] == [(True, "Já está na lista.")] * 6, f"{outra_vez} {exportado}"[:300])
    estado, r = importar("Avó Rosa\nNova Prima Exemplo; 2", formato="lista")
    R.ok("colar lista: quem já está na lista fica de fora, como no ficheiro (CA-GES-05)",
         estado == 200 and [(l["ok"], l.get("erro")) for l in r["linhas"]] == [(False, "Já está na lista."), (True, None)], r)

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
        # o convidado responde no convite: vamos 2 (de 3), com mensagem; gravar não abre o WhatsApp
        pg2.evaluate("document.querySelector('[data-seccao=confirmacao]').scrollIntoView()")
        R.ok("formulário no link pessoal: «Vamos», as 3 pessoas do convite por omissão e o botão de gravar, sem WhatsApp (CA-RSVP-06)",
             pg2.is_checked("input[value=confirmado]") and pg2.inner_text("#resp-n") == "3"
             and pg2.inner_text("#resp-enviar").strip().upper() == "CONFIRMAR PRESENÇA" and pg2.locator("[data-rsvp]").count() == 0)
        pg2.click("label:has(input[value=recusado])")
        R.ok("«Não vamos»: sem pessoas e com o botão «Enviar resposta»",
             not pg2.is_visible("#resp-qtd") and pg2.inner_text("#resp-enviar").strip().upper() == "ENVIAR RESPOSTA")
        pg2.click("label:has(input[value=confirmado])")
        pg2.click("button[aria-label='Menos uma pessoa']")
        pg2.click("#resp-escrever")
        pg2.fill("#resp-msg", "Parabéns, Beatriz!")
        if capturas:
            pg2.locator("[data-seccao=confirmacao]").screenshot(path=str(CAPTURAS / "12-convite-resposta.png"))
        separadores = len(ctx2.pages)
        pg2.click("#resp-enviar")
        pg2.wait_for_selector("#resposta .resumo-rot:has-text('Resposta registada')")
        c_api = next(c for c in json.loads(pedido(f"/api/gestao/{SLUG}/dados", cookie=cookie)[2])["convidados"] if c["token"] == carlos["token"])
        R.ok("resposta no convite gravada: vem com 2 pessoas, com a mensagem e a data (CA-RSVP-06)",
             c_api["estado"] == "confirmado" and c_api.get("pessoasConfirmadas") == 2 and c_api.get("resposta", {}).get("mensagem") == "Parabéns, Beatriz!"
             and c_api["resposta"].get("em"), json.dumps(c_api.get("resposta")))
        R.ok("gravar a resposta não abre o WhatsApp sozinho", len(ctx2.pages) == separadores)
        avisar = urllib.parse.unquote(pg2.get_attribute("[data-rsvp='0']", "href"))
        R.ok("depois de gravar, «Avisar a família pelo WhatsApp» com o nome, as 2 pessoas e a mensagem (CA-RSVP-02/03, CA-RSVP-06)",
             pg2.inner_text("[data-rsvp='0']").strip().upper() == "AVISAR A FAMÍLIA PELO WHATSAPP" and avisar.startswith(f"https://wa.me/{TEL_FAMILIA}?text=")
             and "Olá! Eu, Sr. Carlos Neto e Família, confirmo a minha presença (2 pessoas) na festa de 15 anos da Beatriz, no dia 15 de Maio." in avisar
             and avisar.endswith("\n\nParabéns, Beatriz!"), avisar[:160])
        if capturas:
            pg2.locator("[data-seccao=confirmacao]").screenshot(path=str(CAPTURAS / "13-convite-resposta-registada.png"))
        with ctx2.expect_page() as nova:
            pg2.click("[data-rsvp='0']")
        R.ok("«Avisar a família pelo WhatsApp» abre o WhatsApp num separador novo", nova.value.url.startswith(f"https://wa.me/{TEL_FAMILIA}?text="))
        nova.value.close()

        pg.reload()
        pg.wait_for_selector("li.cartao:has-text('Sr. Carlos Neto e Família') >> text=/Abriu \\d/")
        cartao = pg.locator("li.cartao", has_text="Sr. Carlos Neto e Família")
        R.ok("painel: «Abriu», «Respondeu no convite» e a mensagem do convidado (CA-GES-08, CA-GES-16)",
             "Respondeu no convite" in cartao.inner_text() and "«Parabéns, Beatriz!»" in cartao.inner_text() and "e-confirmado" in cartao.get_attribute("class"))
        R.ok("a resposta do convite conta no resumo: 2 pessoas vêm", pg.inner_text(".r-vem strong") == "2")

        # ver convite a partir da gestão não conta como abertura, e a resposta não é gravada
        tia = next(c for c in lista if c["nome"] == "Tia Joana")
        ctx3, pg3, _ = pagina(b)
        pg3.goto(tia["link"] + "?previa=1")
        pg3.click("#envelope")
        pg3.wait_for_timeout(2700)
        pg3.click("#resp-enviar")
        pg3.wait_for_timeout(300)
        aviso_previa = pg3.inner_text("#aviso")
        avisar_previa = pg3.is_visible("[data-rsvp='0']")
        ctx3.close()
        c_api = next(c for c in json.loads(pedido(f"/api/gestao/{SLUG}/dados", cookie=cookie)[2])["convidados"] if c["token"] == tia["token"])
        R.ok("pré-visualização: o formulário funciona e mostra «Avisar a família», mas a resposta não é gravada (CA-RSVP-09)",
             "não fica gravada" in aviso_previa and avisar_previa and c_api["estado"] == "pendente" and "resposta" not in c_api, aviso_previa)
        pg.reload()
        pg.wait_for_selector("li.cartao:has-text('Tia Joana')")
        R.ok("«Ver convite» na gestão não conta como abertura", "Não abriu" in pg.locator("li.cartao", has_text="Tia Joana").inner_text())

        # a família corrige à mão (menos uma pessoa); o convidado vê a correcção e volta a mudar no convite
        cartao.locator("button[aria-label='Menos uma pessoa']").click()
        pg.wait_for_function("document.querySelector('.r-vem strong').textContent === '1'")
        R.ok("a família corrige a resposta: resumo e «A família alterou depois» (CA-GES-09, CA-GES-16)",
             "No convite: vêm 2 pessoas. A família alterou depois." in pg.locator("li.cartao", has_text="Sr. Carlos Neto e Família").inner_text())
        pg2.reload()
        pg2.wait_for_selector("#resposta .resumo")
        avisar = urllib.parse.unquote(pg2.get_attribute("[data-rsvp='0']", "href"))
        R.ok("ao reabrir, o convite mostra a resposta registada (com a correcção da família) e o aviso já com 1 pessoa (CA-RSVP-07)",
             pg2.inner_text("#resposta .resumo-val") == "Vou" and pg2.is_visible("#resp-alterar") and "confirmo a minha presença (1 pessoa)" in avisar, avisar[:120])
        pg2.click("#resp-alterar")
        R.ok("«Alterar resposta»: o formulário volta com a resposta e a mensagem",
             pg2.inner_text("#resp-n") == "1" and pg2.input_value("#resp-msg") == "Parabéns, Beatriz!" and not pg2.is_visible("[data-rsvp='0']"))
        pg2.click("button[aria-label='Mais uma pessoa']")
        pg2.click("#resp-enviar")
        pg2.wait_for_selector("#resposta .resumo-rot:has-text('Resposta registada')")
        R.ok("convite pessoal: sem erros na consola (CA-QUA-01)", not erros2, "; ".join(erros2[:2]))
        ctx2.close()
        pg.reload()
        pg.wait_for_function("document.querySelector('.r-vem strong').textContent === '2'")
        R.ok("a nova resposta do convidado substitui a correcção da família",
             "A família alterou depois" not in pg.locator("li.cartao", has_text="Sr. Carlos Neto e Família").inner_text())

        # «Não vamos» no convite, num telemóvel de 320 px
        ana = next(c for c in lista if c["nome"] == "Ana e Rui Mendes")
        ctx3, pg3, erros3 = pagina(b, 320, 640)
        pg3.goto(ana["link"])
        pg3.click("#envelope")
        pg3.wait_for_timeout(2700)
        transbordo = "[...document.querySelectorAll('main *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.right>innerWidth+1&&!e.closest('.decor')&&!e.closest('.gal')}).length"
        fora = pg3.evaluate(transbordo)
        pg3.click("label:has(input[value=recusado])")
        pg3.click("#resp-enviar")
        pg3.wait_for_selector("#resposta .resumo-rot:has-text('Resposta registada')")
        fora += pg3.evaluate(transbordo)
        R.ok("320 px: formulário e «Avisar a família» sem transbordo horizontal (CA-RES-01)", fora == 0, f"fora={fora}")
        recusa = urllib.parse.unquote(pg3.get_attribute("[data-rsvp='0']", "href"))
        with ctx3.expect_page() as nova:
            pg3.click("[data-rsvp='0']")
        nova.value.close()
        R.ok("«Não vamos» no convite: grava «não vem», e o aviso leva a mensagem de recusa",
             "Olá! Eu, Ana e Rui Mendes, infelizmente não vou poder estar presente na festa de 15 anos da Beatriz, no dia 15 de Maio." in recusa
             and pg3.inner_text("#resposta .resumo-val") == "Não vamos" and not erros3, recusa[:140])
        ctx3.close()

        # se a gravação falhar, o convidado avisa na mesma a família pelo WhatsApp
        ctx3, pg3, _ = pagina(b)
        pg3.route("**/resposta", lambda r: r.abort())
        pg3.goto(tia["link"])
        pg3.click("#envelope")
        pg3.wait_for_timeout(2700)
        pg3.click("#resp-enviar")
        pg3.wait_for_selector("#resp-estado:has-text('Não foi possível')")
        avisar = urllib.parse.unquote(pg3.get_attribute("[data-rsvp='0']", "href") or "")
        R.ok("se a gravação falhar: aviso de erro e «Avisar a família pelo WhatsApp» com a resposta escolhida (CA-RSVP-06)",
             pg3.is_visible("[data-rsvp='0']") and "Olá! Eu, Tia Joana, confirmo a minha presença (1 pessoa)" in avisar, avisar[:120])
        ctx3.close()
        pg.reload()
        pg.wait_for_selector("li.cartao.e-recusado:has-text('Ana e Rui Mendes')")

        # respostas marcadas pela família
        pg.locator("li.cartao", has_text="Família Exemplo").get_by_role("button", name="Vem", exact=True).click()
        pg.wait_for_function("document.querySelector('.r-vem strong').textContent === '6'")
        R.ok("resposta «Vem» marcada pela família: resumo actualizado", "6" == pg.inner_text(".r-vem strong"))
        pg.locator("li.cartao", has_text="Família Exemplo").get_by_role("button", name="Não vem", exact=True).click()
        pg.wait_for_selector("li.cartao.e-recusado:has-text('Família Exemplo')")
        pg.click("button.chip:has-text('Não vêm')")
        R.ok("filtro «Não vêm»: a resposta do convite e a marcada pela família", pg.locator("li.cartao").count() == 2)
        pg.get_by_role("button", name="Vêm", exact=True).click()
        R.ok("filtro «Vêm»", pg.locator("li.cartao").count() == 1)
        pg.click("button.chip:has-text('Todos')")

        # depois do prazo: o convite mostra os botões do WhatsApp e o toque fica registado
        ctx3, pg3, _ = pagina(b)
        pg3.goto(fora_do_prazo["link"])
        pg3.click("#envelope")
        pg3.wait_for_timeout(2700)
        fechado = pg3.inner_text("#resposta")
        if capturas:
            pg3.locator("[data-seccao=confirmacao]").screenshot(path=str(CAPTURAS / "14-convite-prazo-terminado.png"))
        with ctx3.expect_page() as nova:
            pg3.click("[data-rsvp='0']")
        nova.value.close()
        pg3.wait_for_timeout(600)
        ctx3.close()
        c_api = json.loads(pedido(f"/api/gestao/{SLUG_FECHADO}/dados", cookie=cookie_fechado)[2])["convidados"][0]
        R.ok("depois do prazo: botões do WhatsApp e «Tocou em confirmar» no painel (CA-RSVP-05, CA-RSVP-08)",
             "O prazo para responder no convite terminou" in fechado and c_api["actividade"].get("confirmarEm") and c_api["estado"] == "pendente", fechado)

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
        R.ok("exportar: quando respondeu no convite e a mensagem do convidado (CA-GES-16)",
             "Tocou em confirmar;Respondeu no convite;Mensagem do convidado;Notas;Link" in texto.split("\r\n")[0] and ";Parabéns, Beatriz!;" in texto)
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

        print("Zona de gestão: importar ficheiro (interface)")
        ctx7, pg7, erros7 = pagina(b)
        ctx7.add_cookies([{"name": cookie_imp.split("=")[0], "value": cookie_imp.split("=", 1)[1], "url": BASE}])
        enviados = []
        pg7.on("request", lambda r: enviados.append(r.url) if "/convidados/importar" in r.url else None)
        pg7.goto(f"{BASE}/gestao/{SLUG_IMPORTAR}")
        pg7.wait_for_selector("li.cartao")
        pg7.click("text=Importar ficheiro")
        with pg7.expect_download() as descarga:
            pg7.click("text=Descarregar modelo")
        R.ok("«Descarregar modelo» descarrega modelo-convidados.csv, em UTF-8 com BOM (CA-GES-18)",
             descarga.value.suggested_filename == "modelo-convidados.csv"
             and Path(descarga.value.path()).read_bytes().startswith("\ufeffNome no convite;Pessoas;".encode()))
        pg7.set_input_files("input[type=file]", files=[{"name": "convidados.xlsx", "buffer": b"PK\x03\x04" + bytes(60),
                                                        "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}])
        pg7.wait_for_selector(".j .erro")
        xlsx = pg7.inner_text(".j .erro")
        pg7.set_input_files("input[type=file]", files=[{"name": "grande.csv", "mimeType": "text/csv", "buffer": b"Nome\n" + b"x" * 600_000}])
        pg7.wait_for_selector(".j .erro >> text=500 KB")
        R.ok("um .xlsx ou um ficheiro grande demais: mensagem clara, sem enviar nada (CA-GES-19)",
             "«CSV UTF-8 (delimitado por vírgulas)»" in xlsx and pg7.inner_text(".j .erro").startswith("O ficheiro tem 601 KB") and not enviados, xlsx)
        # CSV gravado por um Excel antigo, em Windows-1252
        ficheiro = ("Nome no convite;Pessoas;Telefone (WhatsApp);Grupo\r\n"
                    "Família Gonçalves Exemplo;3;900 000 151;Colegas de trabalho\r\n"
                    ";2;;\r\n"
                    "Avó Rosa;1;;\r\n").encode("cp1252")
        pg7.set_input_files("input[type=file]", files=[{"name": "convidados.csv", "mimeType": "text/csv", "buffer": ficheiro}])
        pg7.wait_for_selector(".previa")
        previa = pg7.inner_text(".previa")
        R.ok("ficheiro em Windows-1252: acentos certos e pré-visualização com as prontas, os erros e os repetidos (CA-GES-18, CA-GES-19)",
             "1 de 3 linhas prontas a importar." in previa and "Família Gonçalves Exemplo · 3 pessoas · +244 900 000 151 · Colegas de trabalho" in previa
             and "Linha 3 («; 2»): Falta o nome." in previa and "Linha 4 («Avó Rosa; 1»): Já está na lista." in previa, previa)
        if capturas:
            pg7.screenshot(path=str(CAPTURAS / "06-importar-ficheiro.png"))
        pg7.click("text=Importar 1 convidado")
        pg7.wait_for_selector("li.cartao:has-text('Família Gonçalves Exemplo')")
        R.ok("«Importar 1 convidado»: aparece na lista e o aviso diz quantos foram importados, sem erros na consola (CA-GES-18)",
             "1 convidado importado." in pg7.inner_text(".aviso") and pg7.locator("li.cartao").count() == 7 and not erros7, "; ".join(erros7[:2]))
        ctx7.close()

        ctx8, pg8, _ = pagina(b, 320, 640)
        ctx8.add_cookies([{"name": cookie_imp.split("=")[0], "value": cookie_imp.split("=", 1)[1], "url": BASE}])
        pg8.goto(f"{BASE}/gestao/{SLUG_IMPORTAR}")
        pg8.wait_for_selector("li.cartao")
        pg8.click("text=Importar ficheiro")
        pg8.set_input_files("input[type=file]", files=[{"name": "convidados.csv", "mimeType": "text/csv", "buffer": ficheiro}])
        pg8.wait_for_selector(".previa")
        fora = pg8.evaluate("[...document.querySelectorAll('.j *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.right>innerWidth+1}).length")
        R.ok("320 px: janela de importação sem transbordo horizontal (CA-GES-14)", fora == 0, f"fora={fora}")
        ctx8.close()
        ctx.close()
        b.close()

    # bloqueio depois de 10 PIN errados (outro evento, para não afectar os testes acima)
    for _ in range(10):
        entrar("111111", "exemplo-jardim-rose")
    estado, _, corpo = entrar(PIN, "exemplo-jardim-rose")
    R.ok("10 PIN errados: bloqueio temporário, mesmo com o PIN certo", estado == 429, f"estado={estado} {corpo[:80]!r}")


if __name__ == "__main__":
    sys.exit(main("--capturas" in sys.argv))
