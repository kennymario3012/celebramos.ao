# Como a plataforma se comporta

Valores confirmados no código de `apps/web` (Novembro de 2026). Se o código mudar, o código ganha. A especificação está em `docs/05` (plataforma) e `docs/06` (requisitos não funcionais).

## Rotas

| Rota | O quê | Cache |
|---|---|---|
| `/c/<slug>` | Link geral («Convite para Família e Amigos»). Só existe se `linkGeralActivo` não for `false`. Não tem formulário de resposta, só os botões do WhatsApp | `s-maxage=60`: o NGINX pode guardá-lo um minuto |
| `/c/<slug>/<token>` | Link pessoal: o HTML só leva este convidado. `?previa=1` (aberto a partir da gestão) não conta como abertura | `private, no-store` |
| `POST /c/<slug>/<token>/i` | Sinais do convite (`aberto`, `confirmar`), por `sendBeacon`. Responde sempre 204 | — |
| `POST /c/<slug>/<token>/resposta` | Resposta do convidado: 204 gravada, 400 inválida, 404, 410 fora do prazo, 429 demasiadas, 503 falha | — |
| `/c/<slug>/img/<ficheiro>` e `/c/<slug>/<token>/img/<ficheiro>` | Fotos da galeria (ver abaixo) | `private, max-age=3600` |
| `/c/<slug>/calendario.ics` | Evento para o calendário | `s-maxage=300` |
| `/gestao/<slug>` | Zona de gestão da família | — |
| `/api/gestao/<slug>/…` | `entrar`, `sair`, `dados`, `convidados` (POST), `convidados/<token>` (PATCH, DELETE), `convidados/importar`, `convidados/modelo`, `mensagem` (PUT), `exportar` | `no-store` |

- Um slug ou token desconhecido dá sempre a **mesma** página 404 («Convite não encontrado»), para não revelar se o evento existe.
- O slug segue `^[a-z0-9]+(-[a-z0-9]+)*$` e o token tem 22 caracteres base64url (128 bits).
- As páginas do convite levam `X-Robots-Tag: noindex, nofollow`, `Referrer-Policy: no-referrer` e `nosniff`.

## Acesso da família

- **PIN:** de 4 a 12 algarismos (o `preparar-evento.mjs` gera 6). Guarda-se só `{sal, hash}` em scrypt (sal de 16 bytes, hash de 32), em base64url.
- **PIN errado:** espera de 600 ms e uma falha registada em `seguranca.json`. Com 10 falhas nos últimos 15 minutos, a entrada responde 429 até a janela passar.
- **Sessão:**
  - cookie `cg_<slug com _ em vez de ->`: `HttpOnly`, `SameSite=Lax`, `Secure` em https, válido 30 dias;
  - assinado com HMAC-SHA256, com o segredo de `SEGREDO_SESSAO` ou, sem ele, de `CELEBRAMOS_DADOS/sistema/segredo-sessao.json` (criado no primeiro uso);
  - a assinatura inclui os primeiros 16 caracteres do hash do PIN. Trocar o PIN termina as sessões desse evento, e apagar o `segredo-sessao.json` termina as de todos.
- **Pedidos forjados:** as alterações exigem o cabeçalho `X-Celebramos: 1`, que outro site não consegue enviar. Sem ele, a resposta é 403.
- Sem sessão, `dados` responde 401, mas com o título e as cores do evento, para o ecrã de entrada.

## Convidados

| Campo | Regra |
|---|---|
| Nome no convite | obrigatório, até 60 caracteres |
| Pessoas | de 1 a 30, 1 por omissão |
| Telefone | normalizado para o `wa.me`: «923 000 000» → `244923000000`. Aceita `+` e `00`, de 9 a 15 algarismos |
| Grupo | até 40 caracteres |
| Notas | até 200 caracteres. Só a família as vê |

- No máximo **1000 convidados** por evento.
- Estados: `pendente`, `confirmado`, `recusado` (na exportação, «Não vem»). Quando a família marca «confirmado», as pessoas confirmadas passam a ser as do convite.
- **«Novo link»** gera outro token e limpa o «enviado». O link antigo deixa de funcionar, tal como o de um convidado apagado.
- **«Enviar pelo WhatsApp»** abre o `wa.me` com a mensagem e marca o convidado como enviado no próprio toque.
- **Mensagem de envio:**
  - marcadores `{convidado}`, `{homenageado}`, `{dataCurta}`, `{hora}`, `{pessoas}` e `{link}`, este obrigatório; até 700 caracteres;
  - por ordem de prioridade: a que a família gravou, a de `evento.json` em `gestao.mensagemEnvio` e o texto por omissão.

## Importar

- **Colar lista:** até 100 000 caracteres. Cada linha lê-se pelo conteúdo: primeiro o nome, depois as pessoas («3», «3 pessoas», «3 pax»), o telefone e o resto como grupo.
- **Ficheiro CSV:**
  - o modelo vem de `convidados/modelo`, com «;» e BOM, como a exportação. Colunas: «Nome no convite; Pessoas; Telefone (WhatsApp); Grupo; Notas (só para a família)», mais dois exemplos fictícios;
  - num Excel em português, o modelo abre nas colunas certas. Num Excel em inglês fica tudo numa só coluna, porque o ficheiro não tem a linha `sep=;`. Nesse caso, usa-se «Colar lista» ou o Google Sheets;
  - as colunas reconhecem-se pelo título, em qualquer ordem e com sinónimos («Telemóvel», «Contacto», «Observações»…). Sem a linha dos títulos, cada linha lê-se como em «Colar lista»;
  - até 500 KB. O navegador lê o ficheiro e envia-o como texto.
- O pedido devolve sempre primeiro uma pré-visualização, e só grava com `confirmar: true`.
- Ficam de fora:
  - os nomes repetidos, sem contar acentos nem maiúsculas, quer repitam a lista quer uma linha anterior;
  - os exemplos do modelo.
- Um telefone repetido só fica assinalado, porque pode ser o contacto de vários convites.
- Quando o Excel transforma o telefone em «2,44923E+11», a importação dá um erro próprio, com a solução.

## Resposta no convite (decisão 0003)

- Só no link pessoal. O convidado escolhe:
  - «Vou» (ou «Vamos», nos convites de várias pessoas), com o número de pessoas: de 1 até ao do convite, e todas por omissão;
  - ou «Não vou» («Não vamos»);
  - e pode juntar uma mensagem de até 300 caracteres.
- A resposta muda o estado, como se a família o marcasse, e fica guardada em `resposta` com a hora. Se a família corrigir o estado depois, a `resposta` mantém-se como o convidado a deu.
- **Prazo:**
  - pode mudar a resposta até ao fim do dia de `confirmacao.ate`, na hora de Luanda (UTC+1);
  - se o texto não seguir o formato «1 de Maio de 2027», ou for depois da festa, o prazo passa a ser o início da festa;
  - depois do prazo, o servidor responde 410 e o convite mostra só os botões do WhatsApp.
- Cada link aceita até 10 respostas por hora (429).
- Depois de gravar, o convite mostra «Resposta registada» e o botão «Avisar a família pelo WhatsApp», com `confirmacao.mensagem` ou `mensagemRecusa`. O WhatsApp **não** abre sozinho.

## Actividade

- Cada sinal é um ficheiro vazio, `actividade/<token>/<tipo>-<ms>-<aleatório>`, e serve a todos os processos do Passenger. Os tipos são:
  - `aberto`;
  - `confirmar` (toque no botão do WhatsApp);
  - `resposta`.
- O painel conta-os pelos nomes, sem os ler.
- Não contam como abertura: as fotos e `?previa=1`.
- **Exportar** dá um CSV com: Nome, Pessoas, Telefone, Grupo, Estado, Pessoas confirmadas, Enviado em, Aberto em, Tocou em confirmar, Respondeu no convite, Mensagem do convidado, Notas e Link. As datas vêm na hora de Luanda.

## Galeria

- Fotos em `eventos/<slug>/img/`, com nomes como `foto-1.webp` (`[A-Za-z0-9][A-Za-z0-9._-]{0,99}` e extensão webp, jpg, jpeg, png ou avif). Nada de pastas nem ficheiros escondidos.
- Só as vê quem pode ver o convite: pelo link geral enquanto estiver activo, ou com um token válido. Qualquer falha dá o mesmo 404.
- `private`: a cache do NGINX não as guarda, por isso a regra vale em cada pedido.
- Com menores, a galeria vem desligada por omissão (`docs/06`).

## Armazenamento

- Ficheiros JSON em `CELEBRAMOS_DADOS`. Cada escrita:
  - é condicional, por ETag;
  - usa um bloqueio entre processos, a pasta `<ficheiro>.bloqueio`. Considera-se abandonado ao fim de 10 s, e a escrita desiste ao fim de 15 s com «O armazenamento está ocupado»;
  - grava num temporário `.tmp` e muda-lhe o nome.
- Restos `.tmp` ou `.bloqueio`, depois de uma falha, são inofensivos.
- Cada processo guarda o evento em memória durante 60 s.
- `CELEBRAMOS_EVENTOS`, com um JSON `{ "<slug>": Evento }`, é a alternativa ao `evento.json`, que tem prioridade. Em produção usa-se o `evento.json`.

## Variáveis de ambiente

| Variável | Para quê |
|---|---|
| `CELEBRAMOS_DADOS` | Pasta dos dados. **Obrigatória** em produção (sem ela, erro 500) |
| `URL_PUBLICO` | Origem dos links enviados aos convidados (`https://celebramos.ao`) |
| `SEGREDO_SESSAO` | Opcional: segredo das sessões em vez do ficheiro |
| `CELEBRAMOS_EVENTOS` | Opcional: eventos na variável |

## Desenvolvimento local

Os comandos estão no `AGENTS.md` («Comandos (plataforma)»). Em resumo:
- `npm run semear` cria `.dados-locais/` com os dois eventos fictícios do protótipo, com o PIN 123456 (ou outro, com `PIN=… npm run semear`).
- `npm run dev` sincroniza o protótipo e arranca em `localhost:3000`.
- `python3 testes/e2e.py` corre depois de `npm run pacote`: arranca o pacote em 2 processos, com uma pasta de dados temporária. Com `--capturas`, grava as capturas em `testes/_capturas/`.

Quem mudar o `prototipo/template.html` segue também as regras do protótipo no `AGENTS.md`. O CI «Plataforma» verifica os tipos, gera o pacote, corre os testes e guarda o artefacto.
