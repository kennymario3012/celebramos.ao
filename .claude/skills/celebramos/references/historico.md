# Histórico

O que já foi feito, para não se repetir nem se perguntar outra vez. O plano está em `docs/08`, e a história de cada PR no GitHub.

## 6 de Novembro de 2026: a plataforma vai para o ar

| PR | Commit na `main` | O quê |
|---|---|---|
| #1 | `07d8527` | E4: zona de gestão de convidados para a família, com PIN, e alojamento no cPanel (decisões 0001 e 0002) |
| #2 | `361ca8d` | Fotos da galeria servidas a partir de `eventos/<slug>/img/`. O `preparar-evento.mjs` passa a WebP sem EXIF |
| #3 | `862dc2f` | E5-S6: resposta dentro do convite (decisão 0003) |
| #4 | `53d6ea7` | E5-S6: depois de gravar, «Avisar a família pelo WhatsApp». O WhatsApp deixa de abrir sozinho |
| #5 | `334e424` | E4-S2: importar convidados de um ficheiro CSV, com modelo para o Excel |

**No servidor, pela ordem:**
1. Primeira instalação com o pacote do #1:
   - certificado válido e aplicação Node.js criada;
   - variáveis de ambiente;
   - evento de teste `exemplo-bela-principe`;
   - «Force HTTPS Redirect» ligado.

   O titular testou a entrada com PIN, o cadastro e o envio pelo WhatsApp.
2. O #2 e o #3 juntos. O arranque a frio a seguir demorou 14,8 s.
3. O #4, com 7 s de arranque a frio.
4. O #5, com 10 s de arranque a frio. Desde então, a cópia de retorno `celebramos-web-anterior` é o `53d6ea7`.

**No mesmo dia:**
- Publicou-se o primeiro evento real, uma festa de 15 anos com o tema `bela-principe` e sem galeria.
  - O titular trouxe um `evento.json` completo, mas sem o PIN em claro. Gerou-se um PIN novo, que ficou só num ficheiro privado.
  - Acrescentaram-se ao evento os textos do WhatsApp aprovados (ver `eventos-reais.md`).
- Criou-se o cron que mantém a aplicação acordada (ver `servidor.md`).
- Fizeram-se os manuais, o geral e o desse evento, em Claude Docs e em PDF (ver `manuais.md`).
- Os ZIPs enviados e o `evento.json` substituído foram para o lixo do cPanel, com o OK do titular.
- Escreveu-se esta skill.

## Lições

- **Integrar um PR:** o modo automático bloqueou um merge sem revisão. O agente só integra quando o titular o pede por escrito («Integra tu», «Integra e publica»).
- **Ficheiros com o mesmo nome:** quando um ZIP foi substituído por outro com o mesmo nome, o titular enviou primeiro o antigo. Daí a regra de dar um nome novo a cada versão e confirmar o tamanho.
- **GitGuardian:** no PR #2, um comentário com «`<token>/img/…`» foi assinalado como segredo. Era um falso positivo e reescreveu-se antes do merge. Se voltar a acontecer, reescreve-se o texto, ou o titular marca-o como falso positivo no painel do GitGuardian.
- **Sessão do cPanel:** cai quando o IP do titular muda, também a meio de uma gravação. Pede-se ao titular que entre outra vez e repete-se o passo.
- **Disco do Mac:** encheu duas vezes com compilações e testes. Apagar o que se gerou e avisar antes (ver `servidor.md`).

## Em aberto

- Publicação automática por SSH a partir do CI (E0-S3).
- Autorização registada para fotografias de menores (E8-S3). Até lá, os eventos de menores ficam sem galeria.
- `.xlsx` na importação e na exportação (E4-S2, E5-S4), partilha nativa (E4-S4), e ligar ou desligar o link geral na zona de gestão (E4-S3).
- O evento de teste `exemplo-bela-principe` continua em produção. Retira-se quando o titular quiser.
- Esvaziar o lixo do cPanel é decisão do titular. Antes de uma publicação, convém ver com `list_files` se ficaram ZIPs antigos em `/home/<utilizador>`.
