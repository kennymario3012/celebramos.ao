# 07 · Critérios de aceitação

Cada critério tem um identificador, e os PRs e as histórias do [08](08-roadmap.md) referem-se a eles. A coluna **Auto** indica o que o protótipo já verifica automaticamente: `prototipo/testes/verificar.py` (o convite construído) e `validar_config.py` (a configuração). Estes scripts são a referência executável que a plataforma tem de portar.

## Como correr (protótipo)

```bash
cd prototipo
npm install                                   # fontes e ícones locais
pip install -r requirements.txt
python3 -m playwright install chromium
npm run validar                               # esquema + coerência das configurações
npm run construir                             # gera exemplos/<id>/
npm run testar                                # 24/24 critérios em cada exemplo
python3 testes/verificar.py exemplos/exemplo-bela-principe --capturas   # + capturas em _capturas/
```

O script serve a pasta num servidor local, troca as Google Fonts por cópias locais e corre os testes no Chromium (Playwright). Resultado esperado em cada exemplo: `24/24 critérios cumpridos`. O mesmo corre no CI em cada push e pull request ([`.github/workflows/prototipo.yml`](../.github/workflows/prototipo.yml)).

## Como correr (plataforma, `apps/web`)

```bash
cd apps/web
npm install && npm run pacote
python3 testes/e2e.py            # 40 verificações (convite servido pela plataforma e zona de gestão)
python3 testes/e2e.py --capturas # + capturas em testes/_capturas/
```

O script arranca o **próprio pacote do cPanel** (`dist/celebramos-web/server.js`) em dois processos, com a mesma pasta de dados temporária (como vários processos do Passenger) e os eventos fictícios (PIN 123456). Corre no CI em [`.github/workflows/plataforma.yml`](../.github/workflows/plataforma.yml), que guarda o pacote testado como artefacto.

## Convite

### Envelope (ecrã de abertura)

| ID | Critério | Auto |
|---|---|:-:|
| CA-ENV-01 | No primeiro acesso aparece o ecrã de abertura. | ✔ |
| CA-ENV-02 | Enquanto o envelope está fechado, o conteúdo está bloqueado (`inert` e sem deslizamento). | ✔ |
| CA-ENV-03 | O envelope está endereçado ao convidado do link (ou ao convidado genérico ou de demonstração). | ✔ |
| CA-ENV-04 | A sequência de animação é selo 500 ms → aba 600 ms → carta 650 ms → dissolução 550 ms, com as curvas do [02 §2.3](02-experiencia-do-convite.md#23-sequência-de-abertura-valores-exactos). | ✔ |
| CA-ENV-05 | No fim, o ecrã de abertura é removido e o conteúdo desbloqueado. | ✔ |
| CA-ENV-06 | O foco vai para o título do convite (`h1`). | ✔ |
| CA-ENV-07 | Na mesma sessão, ao recarregar, o envelope não volta a aparecer. | ✔ |
| CA-ENV-08 | Com `prefers-reduced-motion`, só há a dissolução de 250 ms. | |
| CA-ENV-09 | O envelope abre com `Enter` e com `Espaço`. | |
| CA-ENV-10 | *(Plataforma)* Um toque feito antes de o JavaScript carregar não se perde. | |
| CA-ENV-11 | *(Plataforma)* Sem JavaScript, o conteúdo fica legível (sem ecrã de abertura a bloquear). | |

### Secções

| ID | Critério | Auto |
|---|---|:-:|
| CA-SEC-01 | A ordem das secções é a da configuração. As secções omitidas, ou sem conteúdo (galeria sem fotos, presentes vazios), não aparecem. | ✔ |
| CA-SEC-02 | Depois de abrir, a primeira secção está no topo do ecrã. | ✔ |
| CA-SEC-03 | Cada secção ocupa pelo menos um ecrã e o deslizar encaixa no início das secções. | |
| CA-SEC-04 | As fronteiras entre secções cumprem as regras de harmonia ([02 §7](02-experiencia-do-convite.md#7-harmonia-entre-secções)): sem cortes a direito e uma decoração por fronteira. Verificar nas capturas de transição. | |
| CA-SEC-05 | A data aparece numa só linha (320–430 px). | ✔ |
| CA-SEC-06 | A caixa «Convite válido para N pessoas» só aparece com um link pessoal (ou de demonstração) que tenha número de pessoas. | |
| CA-SEC-07 | Os textos concordam em género e número (Tem/Têm, Obrigada/Obrigado). | |

### Confirmação, mapas, calendário e contagem

| ID | Critério | Auto |
|---|---|:-:|
| CA-RSVP-01 | O número de botões de confirmação é o da configuração (1–2). | ✔ |
| CA-RSVP-02 | Cada botão abre `https://wa.me/<telefone>?text=…` num novo separador. | ✔¹ |
| CA-RSVP-03 | A mensagem leva o nome do convidado e, se houver, o número de pessoas. | ✔¹ |
| CA-RSVP-04 | Sem número configurado, o toque mostra o aviso de pré-visualização e não abre um link partido. | ✔ |
| CA-RSVP-05 | *(Plataforma)* O toque regista `confirmar_tocado` sem atrasar a abertura do WhatsApp. Se o registo falhar, o WhatsApp abre na mesma. | |
| CA-MAP-01 | Cada evento com local (texto ou coordenadas) tem Google Maps e Waze. Um evento sem local não tem nenhum. | ✔ |
| CA-MAP-02 | Com coordenadas, os links usam `query=<lat>,<lng>` (Google) e `ll=<lat>,<lng>&navigate=yes` (Waze). | |
| CA-CAL-01 | O botão de calendário descarrega o `.ics` (com alojamento próprio) ou abre o Google Calendar. | ✔ |
| CA-CAL-02 | O `.ics` é válido segundo o RFC 5545 (abre num leitor como a biblioteca `icalendar`) e tem um lembrete 1 dia antes. | |
| CA-CD-01 | A contagem regressiva actualiza a cada segundo. | ✔ |
| CA-CD-02 | Depois da data, a contagem mostra zeros e o texto «chegou o grande dia!». | |

¹ Só quando o botão tem número configurado. Os exemplos fictícios não têm números, por isso nos exemplos verifica-se o CA-RSVP-04. A mensagem é verificada pelo nome do convidado.

### Galeria

| ID | Critério | Auto |
|---|---|:-:|
| CA-GAL-01 | Tocar numa foto abre o ecrã inteiro nessa foto («Foto 2 de 3»). | ✔ |
| CA-GAL-02 | As setas do teclado navegam, `Esc` fecha, e os botões das pontas ficam desactivados. | |
| CA-GAL-03 | Em eventos de menores, a galeria vem desligada por omissão. | |

### Personalização

| ID | Critério | Auto |
|---|---|:-:|
| CA-PER-01 | O link pessoal mostra o nome do convidado no envelope e na secção Convite. | ✔ |
| CA-PER-02 | O link pessoal mostra o número de pessoas. | ✔ |
| CA-PER-03 | O link geral mostra o convidado genérico, sem a caixa de pessoas. | |
| CA-PER-04 | *(Plataforma)* O HTML de um convite **não** contém nomes de outros convidados. | |
| CA-PER-05 | *(Plataforma)* Um token desconhecido ou revogado responde 404, com a mesma página de um slug inexistente. | |

### Ecrãs e aparelhos

| ID | Critério | Auto |
|---|---|:-:|
| CA-RES-01 | Sem transbordo horizontal a 320, 360, 375 e 430 px de largura. | ✔ |
| CA-RES-02 | No computador (≥ 700 × 560), o convite aparece num cartão de 27 rem (432 px) centrado. | ✔ |
| CA-RES-03 | Funciona nos navegadores mínimos e ao abrir a partir do WhatsApp (matriz do [06](06-requisitos-nao-funcionais.md#compatibilidade)). | |

### Qualidade técnica

| ID | Critério | Auto |
|---|---|:-:|
| CA-QUA-01 | Sem erros na consola. | ✔ |
| CA-QUA-02 | Sem violações graves ou críticas no axe-core. | |
| CA-QUA-03 | Cumpre os orçamentos de desempenho do [06](06-requisitos-nao-funcionais.md#desempenho) (Lighthouse CI). | |
| CA-QUA-04 | *(Plataforma)* Cabeçalhos `X-Robots-Tag: noindex, nofollow` e `Referrer-Policy: no-referrer`, e metadados Open Graph presentes. | |
| CA-QUA-05 | A configuração é válida contra o esquema (`npm run validar`). | ✔ |

## Plataforma

| ID | Critério |
|---|---|
| CA-PLA-01 | Um operador cria um convite completo com um tema existente **sem tocar em código**, em ≤ 2 horas. |
| CA-PLA-02 | A pré-visualização ao vivo reflecte cada alteração em ≤ 1 s, sem gravar. |
| CA-PLA-03 | Não é possível publicar uma configuração inválida (esquema, coerência ou contraste). A mensagem de erro aponta o campo. |
| CA-PLA-04 | Publicar cria uma versão imutável. Os links já enviados mostram a nova versão em ≤ 60 s. |
| CA-PLA-05 | Colar 100 linhas de convidados cria 100 convidados com tokens únicos, depois de uma pré-visualização com os erros assinalados. |
| CA-PLA-06 | «Enviar pelo WhatsApp» abre a conversa com a mensagem e o link pessoal, e marca o convidado como enviado. |
| CA-PLA-07 | O painel mostra, por convidado: enviado, primeira abertura, último toque em «Confirmar» e estado. Os totais batem certo com a lista. |
| CA-PLA-08 | A exportação CSV ou Excel tem as colunas nome, pessoas, estado, pessoas confirmadas e etiqueta. |
| CA-PLA-09 | Revogar um link faz com que deixe de funcionar (404) em ≤ 60 s. Um novo link funciona de imediato. |
| CA-PLA-10 | Arquivar apaga convidados e interacções. Os links respondem 410. |
| CA-PLA-11 | As permissões da tabela do [05](05-plataforma.md#papéis-e-permissões) são verificadas no servidor (há testes por papel). |

## Zona de gestão de convidados

Implementada em `apps/web` ([decisão 0001](decisoes/0001-gestao-de-convidados-pela-familia.md)). A coluna **Auto** indica o que `apps/web/testes/e2e.py` verifica.

| ID | Critério | Auto |
|---|---|:-:|
| CA-GES-01 | Sem sessão, a API responde 401 e o ecrã de entrada só mostra o nome do evento. | ✔ |
| CA-GES-02 | Um PIN errado é recusado. Ao fim de 10 tentativas erradas, o acesso fica bloqueado 15 minutos, mesmo com o PIN certo. | ✔ |
| CA-GES-03 | Um pedido de alteração sem o cabeçalho `X-Celebramos` é recusado (403). | ✔ |
| CA-GES-04 | Um convidado cadastrado (nome, pessoas, WhatsApp, grupo) aparece na lista e no resumo. | ✔ |
| CA-GES-05 | Colar uma lista mostra a pré-visualização com as linhas inválidas assinaladas e importa só as válidas. | ✔ |
| CA-GES-06 | Cada convidado tem um link com token de 22 caracteres. O convite pessoal mostra o nome, as pessoas e só esse convidado (CA-PER-01/02/04). | ✔ |
| CA-GES-07 | «Enviar pelo WhatsApp» abre `wa.me` com o número do convidado e a mensagem com o link, e marca «Enviado». | ✔ |
| CA-GES-08 | Abrir o convite e tocar em «Confirmar» aparecem no painel («Abriu», «Tocou em confirmar»). «Ver convite» a partir da gestão não conta (CA-RSVP-05). | ✔ |
| CA-GES-09 | As respostas «Vem», com o número de pessoas, e «Não vem» actualizam o resumo e os filtros. A pesquisa ignora acentos. | ✔ |
| CA-GES-10 | Editar funciona. Criar um link novo faz o anterior responder 404. Apagar faz o link responder 404 (CA-PLA-09). | ✔ |
| CA-GES-11 | A mensagem do WhatsApp é editável, tem `{link}` obrigatório e é usada no envio. | ✔ |
| CA-GES-12 | A exportação CSV para o Excel tem as colunas e os estados (CA-PLA-08). | ✔ |
| CA-GES-13 | Com 12 cadastros em simultâneo, repartidos por 2 processos com os mesmos dados, nenhum se perde. | ✔ |
| CA-GES-14 | No telemóvel a 320 px não há transbordo, no computador o painel fica centrado, e a consola não tem erros. | ✔ |
| CA-GES-15 | O convite servido pela plataforma é igual, píxel a píxel, ao convite do protótipo com a mesma configuração (excepto a contagem e o botão de calendário). | |

## Portar os testes para a plataforma

1. Reescrever `verificar.py` como testes Playwright da stack escolhida, contra as rotas reais:
   - `#código` passa a `/c/{slug}/{token}`;
   - a configuração vem dos dados de teste e não do HTML.
2. Manter os **mesmos nomes de critérios** (os IDs desta página) nos títulos dos testes.
3. Acrescentar os critérios marcados *(Plataforma)* e os da secção «Plataforma».
4. **Regressão visual:** comparar as capturas com `docs/img/` (os mesmos estados e larguras do `--capturas`), com limiar de diferença e aprovação explícita no PR quando a mudança é intencional.

## Definição de pronto (qualquer PR que toque no convite)

- [ ] Todos os critérios automáticos passam nos dois exemplos.
- [ ] Capturas revistas, em particular as transições entre secções.
- [ ] Testado à mão a 320 px e no computador.
- [ ] Sem dados pessoais reais no código, nos testes ou nas capturas.
- [ ] Documentação actualizada (`docs/`) se o comportamento mudou.
