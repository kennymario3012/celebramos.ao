# AGENTS.md — instruções para agentes de código

Este ficheiro é para agentes de código (Claude Code, Codex, Cursor, …) e para quem trabalha neste repositório. O `CLAUDE.md` importa-o.

## O projecto em 30 segundos

**celebramos.ao** é uma plataforma de convites digitais para Angola. O convidado recebe um link pelo WhatsApp, abre um envelope animado e percorre o convite no telemóvel. Pode confirmar a presença pelo WhatsApp, abrir o local no mapa e guardar a data no calendário. O primeiro tipo de evento são as festas de 15 anos. A seguir vêm casamentos, aniversários e outros.

Estado actual: **especificação e protótipo de referência**, validados com um cliente real. **A plataforma ainda não existe.** O teu trabalho é construí-la segundo `docs/`.

## Leitura obrigatória antes de qualquer tarefa

1. [`docs/README.md`](docs/README.md): índice, convenções e glossário.
2. O documento da área da tarefa (ver «Ordem de leitura» no índice).
3. A história do [`docs/08-roadmap.md`](docs/08-roadmap.md) e os critérios do [`docs/07-criterios-de-aceitacao.md`](docs/07-criterios-de-aceitacao.md) que ela cita.
4. Para qualquer coisa que o convidado veja: abrir `prototipo/exemplos/exemplo-bela-principe/index.html` e comparar com `docs/img/`.

## Fontes de verdade

| Assunto | Referência |
|---|---|
| O que o convidado vê e sente (animações, medidas, ordem, comportamento) | `docs/02` + `prototipo/template.html` + `docs/img/` (os três têm de concordar; uma diferença entre eles é um defeito a corrigir e a reportar) |
| Configuração do convite | `docs/04` §1–3 + `docs/esquemas/convite.schema.json` |
| Entidades, rotas, permissões, fluxos | `docs/04` §5–7, `docs/05` |
| Desempenho, compatibilidade, privacidade, segurança | `docs/06` |
| Quando está pronto | `docs/07` (critérios com ID) e a coluna «Feito quando» do `docs/08` |

## Regras inegociáveis

1. **Fidelidade à experiência.** Não alterar tempos de animação, medidas, ordem por omissão, comportamento ou textos por omissão sem pedido explícito. As mudanças visuais exigem capturas antes e depois (320 px e computador) no PR.
2. **Repositório público: zero dados pessoais reais.** Nada de nomes de clientes ou convidados, telefones, moradas, coordenadas de eventos reais, fotografias de pessoas ou capturas com dados reais. Isto vale para código, testes, *fixtures*, documentação e mensagens de commit. Usa os exemplos fictícios (`exemplo-bela-principe`, `exemplo-jardim-rose`) ou cria outros, claramente fictícios.
3. **Menores.** Em eventos de menores, a galeria vem desligada por omissão. Nenhuma fotografia de menor é publicada sem autorização registada.
4. **Propriedade intelectual.**
   - Só arte original.
   - Nada de personagens, logótipos ou marcas, nem «parecidos».
   - Nada copiado do convite de referência ou de outros sites.
   - Qualquer fonte, ícone, imagem ou biblioteca distribuída nova é registada em [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md), com uma licença compatível.
5. **Privacidade técnica.**
   - O HTML de um convite só contém o convidado actual, nunca a lista.
   - Tokens de 128 bits.
   - `noindex` em todas as páginas de convite.
   - `Referrer-Policy: no-referrer` e `rel="noopener noreferrer"` nos links externos.
   - Sem rastreadores de terceiros.
6. **Convite leve.**
   - O convite não usa framework no cliente (JS próprio ≤ 15 KB comprimido).
   - Os orçamentos do `docs/06` são critérios de aceitação.
   - Respeitar a lista de navegadores mínimos.
7. **Língua.** Toda a interface em **português de Angola com a ortografia anterior ao Acordo Ortográfico de 1990** (acção, directamente, actual, óptimo, recepção, «15 de Maio de 2027»), com a concordância certa (Tem/Têm, Obrigada/Obrigado). Os nomes dos campos do modelo de dados são os da especificação, em português.
8. **Não decidir o que está em aberto.** As decisões da tabela «Decisões em aberto» do `docs/08` são do titular do projecto. Se uma tarefa depender de uma delas, implementa a proposta marcada **«a confirmar»** de forma fácil de trocar e assinala-o no PR. Quando uma decisão for tomada, regista-a em `docs/decisoes/NNNN-titulo.md`.

## Como trabalhar

- **Uma história por pull request.** Ramo `e1-s2-renderizador`, título `E1-S2: Renderizador do convite`.
- **Nunca fazer push directo para `main`.** Abrir sempre um PR com:
  - o que muda e porquê;
  - os critérios cobertos (`CA-…`) e como foram verificados;
  - capturas, se houver mudança visual;
  - as decisões assumidas.
- **Testes com os IDs dos critérios** nos títulos (ex.: `test("CA-ENV-04 sequência de abertura", …)`).
- **Documentação no mesmo PR** quando o comportamento muda. A documentação e o código não podem divergir.
- Mensagens de commit em português, no presente («Acrescenta…», «Corrige…»).
- As capturas de referência em `docs/img/` só mudam com aprovação explícita (são a base da regressão visual).

## Comandos (protótipo)

```bash
cd prototipo
npm install && pip install -r requirements.txt && python3 -m playwright install chromium
npm run validar        # esquema + coerência das configurações
npm run construir      # exemplos/<id>/
npm run testar         # 24/24 critérios por exemplo
python3 testes/verificar.py exemplos/exemplo-bela-principe --capturas
python3 -m http.server -d exemplos/exemplo-bela-principe 8080
```

Se alterares `prototipo/template.html`, `construir.py` ou as configurações, corre `validar`, `construir` e `testar`, e faz commit dos `exemplos/` reconstruídos. O CI (`.github/workflows/prototipo.yml`) faz o mesmo em cada PR.

## Estrutura do repositório

```
AGENTS.md / CLAUDE.md        instruções para agentes
README.md                    apresentação do projecto
THIRD_PARTY_NOTICES.md       licenças de terceiros
docs/                        especificação (01–08), esquema JSON, capturas de referência
prototipo/                   implementação de referência, testes de aceitação e pipeline de arte
.github/workflows/           CI
```

A estrutura proposta para a plataforma (`apps/`, `packages/`) está no `docs/05`, secção «Arquitectura proposta».

## Quando parar e perguntar

- O pedido contradiz uma regra inegociável.
- O pedido exige dados reais de clientes.
- Uma decisão em aberto bloqueia a tarefa e não há proposta «a confirmar».
- Os documentos, o protótipo e as capturas contradizem-se e não é claro qual está certo.
