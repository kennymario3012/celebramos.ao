# apps/web — plataforma (primeira parte)

Aplicação Next.js com duas coisas:

1. **O convite servido pela plataforma**, com links pessoais `/c/{slug}/{token}`. O convidado é resolvido no servidor e o HTML só leva esse convidado. O link geral é `/c/{slug}`.
2. **A zona de gestão de convidados** `/gestao/{slug}`, onde a família entra com um PIN e trata dos convidados:
   - cadastrar, um a um ou colando uma lista;
   - enviar cada link pelo WhatsApp;
   - ver quem abriu e quem tocou em «Confirmar»;
   - marcar as respostas;
   - exportar para Excel.

A experiência do convite vem do protótipo. `scripts/sincronizar-prototipo.mjs` copia `prototipo/template.html`, `icones.json` e os temas antes de `dev` e de `build`, e o protótipo continua a ser a fonte única.

![Zona de gestão](../../docs/img/gestao-03-lista.webp)

## Correr localmente

```bash
cd apps/web
npm install
npm run semear          # eventos fictícios em .dados-locais/ (PIN 123456)
npm run dev             # http://localhost:3000/gestao/exemplo-bela-principe
```

Sem variáveis de ambiente, os dados ficam em ficheiros (`.dados-locais/`, ignorado pelo git).

## Testes

```bash
npm run build
python3 testes/e2e.py             # 40 verificações: convite, acesso, concorrência, interface, exportação, bloqueio
python3 testes/e2e.py --capturas  # + capturas em testes/_capturas/
```

Precisam do Playwright para Python com o Chromium (como os testes do protótipo) e das fontes de `prototipo/node_modules` (`npm install` em `prototipo/`).

## Dados

| Onde | O quê |
|---|---|
| `eventos/{slug}/evento.json` | Evento: a configuração do convite (docs/04 §1), `gestao.pin` (hash scrypt do PIN da família) e `linkGeralActivo`. |
| `eventos/{slug}/convidados.json` | Lista de convidados e mensagem de envio. É gravada com concorrência optimista (ETag). |
| `eventos/{slug}/actividade/{token}/{tipo}-{ms}-…` | Marcadores vazios de «aberto» e «confirmar». O painel agrega-os só pelos nomes. |
| `eventos/{slug}/seguranca.json` | Tentativas de PIN falhadas (bloqueio de 15 minutos ao fim de 10). |
| `sistema/segredo-sessao.json` | Segredo de assinatura das sessões, se `SEGREDO_SESSAO` não estiver definido. |

- **Produção:** Vercel Blob **privado**.
- **Desenvolvimento:** ficheiros em `.dados-locais/`.
- Os eventos também podem vir da variável `CELEBRAMOS_EVENTOS`, com o JSON `{ "<slug>": evento }`. O armazenamento tem prioridade.

**Dados reais nunca entram no repositório.** Para preparar um evento real:

```bash
node scripts/preparar-evento.mjs caminho/para/config.json [--pin 123456]
# → eventos-privados/<slug>.evento.json e eventos-privados/CELEBRAMOS_EVENTOS.json (ignorados pelo git)
```

## Vercel

| Definição | Valor |
|---|---|
| Root Directory | `apps/web` |
| Include files outside the root directory | ligado (a construção lê `prototipo/`) |
| Região das funções | `cpt1`, Cidade do Cabo (`vercel.json`) |
| Armazenamento | Blob **privado** em `cpt1`, ligado ao projecto (cria `BLOB_READ_WRITE_TOKEN`) |

Variáveis de ambiente:

| Variável | Para quê |
|---|---|
| `CELEBRAMOS_EVENTOS` | (opcional) Eventos em JSON, se não estiverem no Blob. |
| `SEGREDO_SESSAO` | (opcional) Segredo das sessões. Sem ela, é gerado e guardado no Blob. |
| `URL_PUBLICO` | (opcional) Domínio próprio dos links (ex.: `https://celebramos.ao`). |

## Limitações conhecidas

- A configuração do evento ainda não se edita na interface: muda-se no Blob ou em `CELEBRAMOS_EVENTOS`. É o back-office do operador, E3 do roadmap.
- Os textos do convite continuam a ser preenchidos por JavaScript, porque o template vem do protótipo. O HTML final gerado no servidor fica para a E1-S2.
- Um só PIN por evento: todos os familiares usam o mesmo. Contas e papéis ficam para a E5-S5.
