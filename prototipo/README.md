# Protótipo de referência

Implementação de referência do convite digital. Foi validada com um cliente real (festa de 15 anos, Novembro de 2026). Gera um convite estático (um `index.html` autónomo e as imagens) a partir de um ficheiro de configuração JSON.

**É a referência da experiência**: tempos, medidas e comportamento. A plataforma porta-a ([docs/05](../docs/05-plataforma.md#do-protótipo-à-plataforma)) e não a usa directamente em produção.

![Visão geral](../docs/img/visao-geral-bela-principe.webp)

## Estrutura

```
prototipo/
  template.html           o convite: HTML + CSS + JS (sem dependências), com __CONFIG__, __ICONS__ e __TITLE__
  construir.py            configuração → exemplos/<id>/ (index.html, img/, calendario.ics)
  icones.json             subconjunto dos Tabler Icons usados (caminhos SVG)
  configs/                configurações de exemplo (fictícias)
  temas/<tema>/           kit de imagens de cada tema (WebP)
  exemplos/<id>/          convites construídos (versionados, para abrir sem instalar nada)
  testes/verificar.py     critérios de aceitação automáticos (Playwright + Chromium)
  testes/validar_config.py  validação das configurações (esquema JSON + coerência)
  arte/                   geração procedural da arte dos temas (SVG → PNG → WebP)
  package.json            fontes (@fontsource) e ícones (@tabler/icons) para testes e arte
  requirements.txt        dependências Python
```

## Começar

Requisitos: Python 3.11+, Node 18+.

```bash
cd prototipo
npm install
pip install -r requirements.txt
python3 -m playwright install chromium     # na primeira vez (no Linux: --with-deps)

npm run validar      # valida configs/*.json
npm run construir    # constrói os dois exemplos em exemplos/
npm run testar       # 24/24 critérios em cada exemplo

python3 -m http.server -d exemplos/exemplo-bela-principe 8080
# abrir http://localhost:8080 (tamanho de telemóvel nas ferramentas de programador)
# link pessoal de exemplo: http://localhost:8080/#ana-e-rui-mendes
```

Para ver de novo o envelope na mesma sessão, apagar a chave `convite-aberto:<id>` do `sessionStorage` ou abrir uma janela privada.

## Criar um convite

1. Copiar uma configuração de `configs/` e editá-la. Os campos estão em [docs/04](../docs/04-modelo-de-dados.md#1-configuração-do-convite) e o esquema em [`docs/esquemas/convite.schema.json`](../docs/esquemas/convite.schema.json).
2. `python3 testes/validar_config.py configs/<ficheiro>.json`
3. `python3 construir.py configs/<ficheiro>.json [pasta-de-saída]`
4. `python3 testes/verificar.py <pasta-de-saída> --capturas` e rever as capturas em `<pasta-de-saída>/_capturas/`, em particular as transições `2*-transicao-*`.

> **Dados reais nunca entram no repositório**, porque o repositório é público. Guardar as configurações de clientes em `configs/privado/` (ignorada pelo git) e construir para fora do repositório ou para `saida/` (também ignorada).

A saída é estática e pode ser servida por qualquer servidor de ficheiros. Os links pessoais usam `#código` (chaves de `convidados`). **No protótipo, a lista de convidados vai dentro do HTML.** Para listas reais, usar só o link geral (`"convidados": {}`) ou a plataforma.

## Arte

```bash
npm run arte                              # todos os temas
python3 arte/gerar_arte.py bela-principe  # um tema
```

Gera `temas/<tema>/*.webp`. A imagem de partilha de cada tema (`og.jpg`, 1200 × 630) gera-se com `python3 arte/gerar_og.py`. Os ficheiros intermédios (SVG, PNG) ficam em `.construcao/`, ignorada pelo git. As sementes são fixas, por isso o resultado é reprodutível. Ver [docs/03](../docs/03-design-e-temas.md#pipeline-de-arte-procedural-no-protótipo).

## Limitações conhecidas

Compromissos aceites por causa do alojamento estático, que a plataforma tem de resolver. A lista completa está em [docs/05 · Do protótipo à plataforma](../docs/05-plataforma.md#do-protótipo-à-plataforma):

- personalização por `#código`, com todos os convidados no HTML;
- textos preenchidos por JavaScript;
- campos redundantes na configuração (`data.dia`…);
- textos fixos de 15 anos;
- Google Fonts;
- sem Open Graph;
- sem alternativa sem JavaScript;
- `inset` sem alternativa para navegadores antigos.
