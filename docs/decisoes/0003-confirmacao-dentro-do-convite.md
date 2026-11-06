# 0003 · Confirmação de presença dentro do convite

- **Estado:** aceite (Novembro de 2026)
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
3. **O WhatsApp abre sozinho, no mesmo toque** em que a resposta é enviada. Leva a mensagem de confirmação (com as pessoas escolhidas) ou a de recusa, seguida da mensagem do convidado. Quem envia o aviso é sempre o convidado: o envio automático em nome da família exige a WhatsApp Business API e fica fora do âmbito ([01](../01-produto.md#fora-para-já)). Se a gravação falhar, o WhatsApp abre na mesma.
4. **O convidado pode mudar a resposta até ao prazo.** Ao reabrir o link, vê a resposta registada (também a que a família marcou) e «Alterar resposta».
5. **Depois do prazo, o formulário fecha.** O prazo é o fim do dia de `confirmacao.ate` em Luanda. O convite mostra a resposta registada, se houver, e os botões do WhatsApp para falar com a família, e o servidor recusa respostas. A família continua a marcar à mão.
6. **No link geral (sem nome), fica como antes:** só o WhatsApp, com «[o seu nome]». Sem convidado não há onde gravar, e assim ninguém com o link geral consegue meter respostas falsas na lista.

## Alternativas consideradas

- **Só WhatsApp**, a proposta do MVP: a família continua a marcar tudo à mão.
- **Gravar e oferecer «Avisar também pelo WhatsApp»** num botão à parte (a proposta anterior do [05](../05-plataforma.md#confirmações)). Há menos saltos para o WhatsApp, mas muitos convidados não avisariam e a família passaria a depender da zona de gestão.
- **No link geral, pedir o nome** e gravar a resposta numa lista à parte, para a família a juntar ao convidado certo. Dá mais trabalho e abre uma porta sem token.
- **Aceitar respostas depois do prazo**, com ou sem a marca «fora do prazo».

## Consequências

- A plataforma passa a guardar, por convidado, a última resposta dada no convite: estado, pessoas, mensagem opcional e data. A mensagem é mais um dado pessoal, apagado com a lista de convidados ([06](../06-requisitos-nao-funcionais.md#privacidade-e-protecção-de-dados)).
- Há uma rota pública nova, `POST /c/{slug}/{token}/resposta`, com o acesso do convite (um token desconhecido dá o mesmo 404), um limite de 10 respostas por hora em cada link e a resposta 410 depois do prazo.
- O prazo que o convidado lê (`confirmacao.ate`, «1 de Maio de 2027») passa a ter efeito. Tem de estar escrito por extenso e não pode ser depois da festa (`validar_config.py` verifica).
- O campo opcional `confirmacao.mensagemRecusa` é o modelo da mensagem de recusa.
- O protótipo, que não tem servidor, continua só com o WhatsApp: o formulário só aparece quando a plataforma passa `responder` ao convite.
- Quem responde no convite deixa de gerar o sinal «Tocou em confirmar». O sinal continua depois do prazo, quando os botões voltam a abrir só o WhatsApp.
- Depois de integrada, a alteração só chega aos convidados com o pacote novo no servidor (procedimento «Actualizar» de [`apps/web/README.md`](../../apps/web/README.md)). Os eventos já publicados funcionam sem mudanças: sem `mensagemRecusa`, o convite usa a mensagem por omissão.
