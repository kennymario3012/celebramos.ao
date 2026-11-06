---
name: celebramos
description: Conhecimento de operação da plataforma celebramos.ao (convites digitais para Angola) — como a plataforma funciona, onde está cada coisa, como se publica e actualiza no cPanel da Host2Africa, como se prepara e publica um evento real (evento.json, fotos, PIN da família, textos do WhatsApp), como se mantém o servidor (HTTPS, cache do NGINX, cron que mantém a aplicação acordada), como se fazem os manuais para as famílias e quais são os problemas já conhecidos. Usar sempre que o trabalho tocar neste repositório, no servidor, num evento real, na zona de gestão ou no convite, incluindo perguntas como «como publico a versão nova?», «como preparo o evento de um cliente?», «a família perdeu o PIN», «porque é que o site está lento?» ou «faz o manual para a família».
---

# celebramos.ao: operação da plataforma

As regras de código e de conteúdo estão no [`AGENTS.md`](../../../AGENTS.md), e a especificação está em [`docs/`](../../../docs/README.md). Esta skill junta o que **não** está lá: como a plataforma corre em produção e como se trabalha com ela no dia a dia. Foi escrita depois da primeira publicação, em Novembro de 2026.

## Em 30 segundos

- **O que é:** o convidado recebe pelo WhatsApp um link pessoal, abre um envelope e percorre o convite. Responde no próprio convite e, a seguir, avisa a família pelo WhatsApp. A família gere a lista numa zona com PIN: cadastra, envia, acompanha e exporta.
- **Onde corre:** `apps/web` (Next.js, `output: "standalone"`) no **cPanel da Host2Africa**, como aplicação Node.js do Passenger, em `https://celebramos.ao`. Não há base de dados: os eventos são ficheiros JSON em `CELEBRAMOS_DADOS`, fora da aplicação ([decisão 0002](../../../docs/decisoes/0002-alojamento-no-cpanel.md)).
- **Como chega lá:** PR → CI «Plataforma» na `main` → artefacto `celebramos-web` → ZIP enviado pelo Gestor de ficheiros do cPanel → reinício da aplicação → limpeza da cache do NGINX. Ainda não há publicação automática (E0-S3).
- **Quem decide:** o titular. Integrar PRs, mexer no servidor e publicar eventos só com o pedido ou o OK dele.

## Mapa

| Área | Onde |
|---|---|
| Experiência do convite (fonte única) | `prototipo/template.html`, copiado para `apps/web` por `scripts/sincronizar-prototipo.mjs` |
| Renderização no servidor | `apps/web/src/convite/renderizar.ts` |
| Rotas do convite | `apps/web/src/app/c/[slug]/…`: geral, `[token]` (pessoal), `[token]/i` (sinais), `[token]/resposta` (POST da resposta), `img/` e `[token]/img/` (fotos), `calendario.ics` |
| Zona de gestão | `apps/web/src/app/gestao/[slug]/Gestao.tsx` + `apps/web/src/app/api/gestao/[slug]/…` |
| Convidados, CSV, sessões | `apps/web/src/lib/convidados.ts`, `csv.ts`, `sessao.ts`, `armazenamento.ts`, `texto.ts` |
| Preparar um evento real | `apps/web/scripts/preparar-evento.mjs` |
| Testes | `apps/web/testes/e2e.py`, `prototipo/testes/validar_config.py` |
| CI | `.github/workflows/plataforma.yml` (gera o artefacto `celebramos-web`, 30 dias) e `prototipo.yml` |
| Decisões | `docs/decisoes/0001` (gestão pela família), `0002` (cPanel), `0003` (resposta no convite) |

## Regras de operação

Estas regras juntam-se às do `AGENTS.md`.

1. **Dados reais fora do git.** Configurações de clientes, `evento.json`, PINs, listas e capturas com dados reais ficam na pasta privada do operador e no servidor. Nunca ficam no repositório nem em mensagens de commit ou de PR.
2. **O PIN nunca aparece em claro.** Gera-se para um ficheiro privado, que o titular entrega à família, e o servidor guarda só o hash. Não se escreve no chat.
3. **Não entrar na zona de gestão real.** O agente não escreve PINs em produção. Para testar com login, usa os dados locais: `npm run semear`, com o PIN de teste 123456.
4. **O cPanel é do titular.** O agente pode navegar numa sessão que o titular abriu, mas não escreve a palavra-passe dele. Enviar, apagar, criar a aplicação ou mudar definições pede o OK do titular. Apagar quer dizer mover para o lixo do cPanel, nunca «Skip the trash».
5. **Integrar só com pedido explícito** («Integra»). Antes de pedir, o CI tem de estar verde.
6. **Cada versão de um ficheiro enviado leva um nome novo** (`…-v2.zip`, `…-<sha>.zip`), e confirma-se o tamanho no servidor antes de extrair. Já aconteceu o operador arrastar uma versão antiga com o mesmo nome.

## Tarefas → referência

| Tarefa | Ler |
|---|---|
| Publicar uma versão nova, voltar atrás, primeira instalação | [references/publicar-no-cpanel.md](references/publicar-no-cpanel.md) |
| Publicar o evento de um cliente, trocar o PIN, mudar textos ou fotos | [references/eventos-reais.md](references/eventos-reais.md) |
| Servidor: estrutura, HTTPS, cache, cron, lentidão, registos | [references/servidor.md](references/servidor.md) |
| Como a plataforma se comporta (fluxos, limites, segurança) | [references/plataforma.md](references/plataforma.md) |
| Manuais para as famílias (texto e PDF com capturas) | [references/manuais.md](references/manuais.md) |
| O que já foi feito e quando | [references/historico.md](references/historico.md) |

## Verificações rápidas, sem login

```bash
B=https://celebramos.ao
ID=$(cat celebramos-web/.next/BUILD_ID)                      # BUILD_ID do pacote enviado
curl -s $B/gestao/<slug> | grep -c "$ID"                     # 1 = o site já serve essa compilação
curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' $B/c/<slug>
curl -s -o /dev/null -w '%{http_code} -> %{redirect_url}\n' http://celebramos.ao/   # 301 para https
curl -s -o /dev/null -w '%{http_code}\n' $B/c/<slug>/calendario.ics
```

Na página da zona de gestão, o `BUILD_ID` aparece como `\"b\":\"<id>\"`. Se o site servir um diferente do enviado, a aplicação não foi reiniciada. Se só a página inicial estiver desactualizada, falta limpar a cache do NGINX.
