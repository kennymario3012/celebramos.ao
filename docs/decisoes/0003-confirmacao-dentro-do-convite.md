# 0003 · Confirmação de presença dentro do convite

- **Estado:** aceite (Novembro de 2026); revista no mesmo dia, depois do teste em produção (ponto 3 e [Revisão](#revisão-6-de-novembro-de-2026))
- **Decidiu:** titular do projecto, depois de testar a zona de gestão com o evento fictício
- **Resolve:** a decisão em aberto D4 do [08](../08-roadmap.md#decisões-em-aberto) (fase 2 das confirmações)
- **Afecta:** [01](../01-produto.md#âmbito), [02 §4.3](../02-experiencia-do-convite.md#43-confirmação-de-presença), [04](../04-modelo-de-dados.md), [05](../05-plataforma.md#confirmações), [06](../06-requisitos-nao-funcionais.md#privacidade-e-protecção-de-dados), [07](../07-criterios-de-aceitacao.md), [08](../08-roadmap.md#estado), [`apps/web/README.md`](../../apps/web/README.md)

## Contexto

Ao testar a zona de gestão com o evento fictício `exemplo-bela-principe`, o titular viu que a confirmação só seguia pelo WhatsApp. O convite abria a conversa com a mensagem pré-escrita para a família e registava apenas o toque em «Confirmar». Depois, a família tinha de marcar «Vem» ou «Não vem» à mão. O titular pediu que a resposta ficasse também gravada na plataforma.

## Decisão

1. **No link pessoal, o convidado responde dentro do convite:**
   - vou ou não vou («vamos» ou «não vamos» num convite para várias pessoas);
   - quantas pessoas vão, de 1 até ao número do convite (por omissão, todas);
   - uma mensagem opcional para a família, até 300 caracteres.
2. **A resposta fica gravada no convidado** (estado e pessoas confirmadas, como se a família a marcasse) e aparece logo na zona de gestão: resumo, filtros «Vêm» e «Não vêm» e exportação, com «Respondeu no convite», a data e a hora. A família continua a poder corrigir à mão, e o painel indica quando a resposta do convite foi alterada depois.
3. **Depois de gravar, o convite mostra «Avisar a família pelo WhatsApp»**, que abre o WhatsApp com a mensagem já escrita, conforme a resposta:
   - vou: «Olá! Eu, {convidado}, confirmo a minha presença (3 pessoas) na festa de 15 anos da {homenageado}, no dia {data}.»;
   - não vou: «Olá! Eu, {convidado}, infelizmente não vou poder estar presente na festa de 15 anos da {homenageado}, no dia {data}. Agradeço muito o convite e desejo uma festa muito bonita!».

   A mensagem do convidado vai no fim. Os textos ficam na configuração do evento (`confirmacao.mensagem` e `confirmacao.mensagemRecusa`). Quem envia o aviso é sempre o convidado: o envio automático em nome da família exige a WhatsApp Business API e fica fora do âmbito ([01](../01-produto.md#fora-para-já)). Se a gravação falhar, o botão do WhatsApp aparece na mesma.
4. **O convidado pode mudar a resposta até ao prazo.** Ao reabrir o link, vê a resposta registada (também a que a família marcou) e «Alterar resposta».
5. **Depois do prazo, o formulário fecha.** O prazo é o fim do dia de `confirmacao.ate` em Luanda. O convite mostra a resposta registada, se houver, e os botões do WhatsApp para falar com a família, e o servidor recusa respostas. A família continua a marcar à mão.
6. **No link geral (sem nome), fica como antes:** só o WhatsApp, com «[o seu nome]». Sem convidado não há onde gravar, e assim ninguém com o link geral consegue meter respostas falsas na lista.

## Alternativas consideradas

- **Só WhatsApp**, a proposta do MVP: a família continua a marcar tudo à mão.
- **Abrir o WhatsApp sozinho, no mesmo toque em que grava** (a primeira versão, ver a [Revisão](#revisão-6-de-novembro-de-2026)). Avisava sempre a família, mas o convidado saltava para o WhatsApp antes de ver que a resposta ficara registada.
- **No link geral, pedir o nome** e gravar a resposta numa lista à parte, para a família a juntar ao convidado certo. Dá mais trabalho e abre uma porta sem token.
- **Aceitar respostas depois do prazo**, com ou sem a marca «fora do prazo».

## Revisão (6 de Novembro de 2026)

Na primeira versão (PR #3), o WhatsApp abria sozinho, no mesmo toque em que a resposta era gravada, com a mensagem «Olá! Confirmo a presença na festa… Convidado: … (3 pessoas)». Depois de testar o convite publicado, o titular pediu um botão para o convidado avisar a família pelo WhatsApp, com a mensagem já escrita e personalizada: «Eu, …, confirmo a minha presença» para quem vai e, para quem não vai, uma mensagem mais calma, a dizer que infelizmente não vai. Escolheu:

- o WhatsApp **deixa de abrir sozinho**: o botão redondo só grava, e «Avisar a família pelo WhatsApp» aparece a seguir (também ao reabrir o link);
- os dois textos do ponto 3.

## Consequências

- A plataforma passa a guardar, por convidado, a última resposta dada no convite: estado, pessoas, mensagem opcional e data. A mensagem é mais um dado pessoal, apagado com a lista de convidados ([06](../06-requisitos-nao-funcionais.md#privacidade-e-protecção-de-dados)).
- Há uma rota pública nova, `POST /c/{slug}/{token}/resposta`, com o acesso do convite (um token desconhecido dá o mesmo 404), um limite de 10 respostas por hora em cada link e a resposta 410 depois do prazo.
- O prazo que o convidado lê (`confirmacao.ate`, «1 de Maio de 2027») passa a ter efeito. Tem de estar escrito por extenso e não pode ser depois da festa (`validar_config.py` verifica).
- O campo opcional `confirmacao.mensagemRecusa` é o modelo da mensagem de recusa.
- O protótipo, que não tem servidor, continua só com o WhatsApp: o formulário só aparece quando a plataforma passa `responder` ao convite.
- Avisar a família passa a ser um segundo toque. Alguns convidados vão gravar sem avisar pelo WhatsApp: a família vê na mesma a resposta na zona de gestão.
- Quem responde no convite deixa de gerar o sinal «Tocou em confirmar». O sinal continua depois do prazo, quando os botões voltam a abrir só o WhatsApp.
- Depois de integrada, a alteração só chega aos convidados com o pacote novo no servidor (procedimento «Actualizar» de [`apps/web/README.md`](../../apps/web/README.md)). Os eventos já publicados funcionam sem mudanças: sem `mensagemRecusa`, o convite usa a mensagem por omissão.
