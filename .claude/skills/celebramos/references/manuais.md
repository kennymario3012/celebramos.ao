# Manuais para as famílias

Há dois manuais. Nenhum vai para o git.

| Manual | O quê | Onde fica |
|---|---|---|
| **Geral** | Toda a zona de gestão e o convite, sem dados de clientes | Pasta privada do operador (`manuais/Manual-da-familia-celebramos.pdf`, 8 páginas) e um documento Claude Docs do titular |
| **De um evento** | O geral com o nome do evento, o link `celebramos.ao/gestao/<slug>`, as datas concretas e capturas reais desse evento | Pasta privada do operador, ao lado do geral. Tem nomes e capturas reais |

**O PIN nunca entra no manual.** O manual de um evento diz numa caixa de aviso que o PIN foi entregue em separado, que é o mesmo para toda a família e que não se reencaminha, porque quem o tem vê e altera a lista.

## Conteúdo

O manual geral tem 8 secções:
1. O que a família recebe: o link da gestão, o PIN e o link geral, se houver.
2. Entrar na zona de gestão: o PIN, a sessão de 30 dias nesse aparelho, «Sair» num aparelho alheio, e o bloqueio de 15 minutos depois de 10 PINs errados.
3. Cadastrar convidados: um a um, «Colar lista» e importar o modelo CSV.
4. Enviar os convites pelo WhatsApp: a mensagem, o envio a cada convidado, o «enviado» e o link geral.
5. O que o convidado vê e faz: o envelope, a resposta e «Avisar a família pelo WhatsApp».
6. Acompanhar as respostas: o resumo, os filtros, os sinais de abertura e de resposta, marcar à mão e «Exportar (Excel)».
7. Prazo e dia da festa: depois do prazo o formulário fecha, e a família continua a poder marcar à mão.
8. Problemas frequentes, numa tabela.

O manual de um evento junta, no início:
- «Os links e o PIN»;
- um «Calendário até à festa», com as datas reais: enviar, prazo de resposta e exportar a lista final.

**Escrita:**
- português de Angola, frases curtas, a tratar a família com cortesia («Abra», «Toque em»);
- os botões com o nome exacto do ecrã, entre «»;
- valores (30 dias, 10 tentativas, 1000 convidados, 500 KB) iguais aos de `plataforma.md`. Se a plataforma mudar, os manuais mudam também.

## Capturas

- **Fictícias, para o manual geral:** os testes ponta a ponta gravam-nas em `apps/web/testes/_capturas/`, ignorada pelo git.
  ```bash
  cd apps/web && npm install && npm run pacote
  python3 testes/e2e.py --capturas
  ```
  Ficam lá, entre outras, `00-entrada`, `02-adicionar`, `03-lista`, `04-painel`, `10-convite-envelope`, `12-convite-resposta`, `13-convite-resposta-registada` e `14-convite-prazo-terminado`.
- **Reais, para o manual de um evento:**
  - o titular abre a zona de gestão do evento no browser interno, com a sessão dele, porque o agente não escreve o PIN;
  - o agente emula 390×844 (telemóvel) e tira as capturas;
  - o convite de um convidado abre-se com `?previa=1`, para não contar como abertura.
- **Recortes, no Mac:**
  ```bash
  sips --cropToHeightWidth <altura> <largura> --cropOffset <y> 1 entrada.png --out recorte.png
  ```
  - Um deslocamento 0 é lido como «centrar», por isso usa-se 1.
  - Um recorte que chegue exactamente ao fundo da imagem não se aplica. Tira-se 2 px à altura.

## PDF

1. **HTML em A4:**
   - `@page { size: A4; margin: 0 }` e cada página com 210×297 mm e `break-after: page`;
   - `print-color-adjust: exact`, para os fundos saírem impressos.
2. **Personalização:**
   - a arte do tema do evento, em `prototipo/temas/<tema>/`: `papel.webp` no fundo da capa, `florais-canto*.webp` nos cantos, e `grinalda.webp` e `espelho.webp` como ornamentos;
   - as fontes do convite, do Google Fonts: Allura nos títulos, Cormorant SC nas pequenas maiúsculas e EB Garamond no texto.
3. **Imprimir** com o Chrome for Testing do Playwright, sem interface:
   ```bash
   CHROME=$(ls -d "$HOME"/Library/Caches/ms-playwright/chromium-*/chrome-mac-arm64/"Google Chrome for Testing.app"/Contents/MacOS/"Google Chrome for Testing" | tail -1)
   "$CHROME" --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=20000 \
     --run-all-compositor-stages-before-draw --user-data-dir="$(mktemp -d)" \
     --print-to-pdf=manual.pdf "file://$PWD/manual.html"
   ```
   - O `--virtual-time-budget` dá tempo às fontes para carregarem.
   - Enquanto imprime, aparece no Dock um ícone «Google Chrome for Testing». É só isto, e fecha sozinho.
4. **Rever** todas as páginas em miniatura antes de entregar:
   ```bash
   pdftoppm -r 42 -png manual.pdf rev/p
   ```
   - Na capa, os florais chegaram a tapar o texto. Resolveu-se com os florais a 82 mm e `padding-bottom: 30mm`.

Com capturas, um manual ocupa de 4 a 6 MB em 8 a 10 páginas.

Ao gerar o HTML em Python, o `%` do CSS choca com a formatação `%`. Usam-se marcadores como `{{PAPEL}}` e `.replace()`.

## Entregar

O titular envia o PDF à família por um canal privado, juntamente com o link da gestão. O PIN segue numa mensagem à parte (ver `eventos-reais.md`).
