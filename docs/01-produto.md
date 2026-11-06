# 01 · Produto

## Visão

**celebramos.ao** cria convites digitais com a emoção de um convite de papel. O convidado recebe um link pelo WhatsApp, abre um envelope animado e percorre o convite no telemóvel: quem convida, quando, onde, o programa, as regras da festa. Confirma a presença com um toque.

Para o anfitrião, o convite tem de ser **bonito, rápido de aprovar e fácil de enviar**. Também tem de lhe dizer quem já abriu e quem confirmou.

## Contexto

- **Mercado:** Angola (Luanda em primeiro lugar). Os convites circulam pelo **WhatsApp**, e é lá que a família combina tudo, revê o convite e confirma presenças.
- **Aparelhos:** sobretudo Android, muitos de gama baixa ou antigos. Os dados móveis são caros, por isso a página tem de ser leve (ver [06](06-requisitos-nao-funcionais.md)).
- **Referência de mercado:** convites de [convitesdigitais.ao](https://convitesdigitais.ao). A experiência de abertura do envelope e as secções em ecrã inteiro foram estudadas e reproduzidas. Não se copiou código, imagens ou textos, e toda a arte é original (ver [03](03-design-e-temas.md#propriedade-intelectual)).
- **Primeiro tipo de evento:** festas de **15 anos (debutantes)**. A seguir vêm casamentos (o convite de referência é de um casamento), aniversários, baptizados e outros.

## Personas

| Persona | Quem é | O que precisa |
|---|---|---|
| **Anfitrião** | Pais da debutante, noivos, aniversariante. Decide e aprova. | Ver o convite antes de enviar e pedir alterações sem complicação. **Cadastrar os convidados ele próprio** e enviar a cada um o seu link. Saber quantas pessoas vêm. |
| **Convidado** | Família e amigos, de todas as idades. Abre o link no WhatsApp. | Perceber logo quando e onde é. Chegar lá (mapa). Confirmar sem preencher formulários. Lembrar-se da data (calendário). |
| **Operador** | Equipa celebramos.ao que monta o convite para o cliente (modelo «feito por nós»). | Montar um convite novo em pouco tempo, sem tocar em código. Aplicar alterações pedidas por áudio ou captura de ecrã. Publicar com segurança. |
| **Designer de temas** | Cria temas (cores, tipografia, arte). | Criar arte original reutilizável e verificar o contraste e a harmonia entre secções. |

## Proposta de valor

1. **Momento de abertura:** o envelope com selo de cera dá ao convite digital o ritual do convite de papel.
2. **Tudo no telemóvel, num só link:** data, locais com Google Maps e Waze, programa, regras de traje, lista de presentes, contagem regressiva e calendário.
3. **Pessoal:** cada convidado vê o seu nome no envelope e no convite, e para quantas pessoas é válido.
4. **Confirmação sem atrito:** um toque grava a resposta, e outro abre o WhatsApp com a mensagem já escrita para a família.
5. **Feito à medida, com rapidez:** temas e secções configuráveis. A família aprova num link de pré-visualização.

## Modelo de serviço

1. **Fase 1 — «feito por nós»** (actual): o operador recolhe os dados do cliente pelo WhatsApp (texto, áudio, fotos de referência) e monta o convite. Partilha um link de pré-visualização e faz as revisões até à aprovação. Foi assim que o primeiro convite real foi feito.
2. **Fase 2 — self-service:** o anfitrião cria o convite sozinho num assistente, escolhe um tema e paga online. O operador continua disponível para personalizações.

## Âmbito

### Dentro (MVP)

- Convite com a experiência completa do [02](02-experiencia-do-convite.md): envelope, secções, personalização, confirmação (dentro do convite no link pessoal, com aviso pelo WhatsApp), mapas, calendário, contagem regressiva e computador.
- Temas configuráveis (tokens de cor e arte) e ordem de secções configurável.
- Back-office do operador para criar, editar, pré-visualizar e publicar convites.
- **Zona de gestão de convidados para a família** (acesso por PIN, sem conta): cadastrar convidados um a um, colando uma lista ou importando um ficheiro do Excel (CSV), links pessoais, envio pelo WhatsApp, aberturas, confirmações e exportação. **Já implementada** em [`apps/web`](../apps/web/) (ver [05](05-plataforma.md#zona-de-gestão-de-convidados)).
- Tipos de evento: 15 anos. A estrutura tem de estar preparada para casamentos e aniversários.

### Fora (para já)

- Editor self-service e pagamentos online (fase 2).
- Envio automático de mensagens pelo WhatsApp em nome do anfitrião (exige a WhatsApp Business API e aprovação de modelos de mensagem).
- Mesas e lugares, livro de mensagens, galeria pós-evento, transmissão em directo.
- Outras línguas além do português.

## Jornada do anfitrião (caso real, anonimizado)

1. **Pedido:** a família pede o convite e envia os dados pelo WhatsApp: nome da debutante, nomes dos pais, data, tema da festa e cores (fotografia da decoração). O operador parte de um convite de referência.
2. **Primeira versão:** o operador publica um link de pré-visualização no mesmo dia.
3. **Revisões:** a família responde pelo WhatsApp com textos, áudios e capturas de ecrã assinaladas. Houve **6 rondas** de alterações em uma semana (ver «Decisões validadas»).
4. **Aprovação** e decisão sobre o envio: link geral ou links pessoais.
5. **Cadastro e envio:** a família cadastra os convidados na zona de gestão e envia cada link pessoal pelo WhatsApp.
6. **Confirmações** ficam gravadas na zona de gestão e chegam também ao WhatsApp da família.
7. **Dia do evento:** o convite continua acessível (mapa, programa).

## Decisões validadas

Decisões tomadas com o primeiro cliente real (festa de 15 anos, Novembro de 2026). Cada uma tornou-se um requisito da plataforma.

| # | Pedido do cliente | Requisito que gerou |
|---|---|---|
| 1 | **Sem fotografias da debutante** (pedido da mãe). | A galeria é opcional e fica **desligada por omissão em eventos de menores**. A arte ilustrada do tema substitui as fotografias. |
| 2 | **Mais referências ao conceito do tema** («A Bela e o Príncipe»). | O tema inclui ilustração própria (espelho com rosa e coroa, arco de balões com o «15»), selo com ícone (rosa), linha de abertura («Era uma vez…») e textos no mesmo registo («O meu conto de fadas…», «Valsa com o príncipe»). |
| 3 | **Cores da decoração real** (vinho, preto e ouro, a partir de uma fotografia do arco de balões). | Os tokens de cor do tema derivam de uma fotografia de referência do cliente. |
| 4 | **Os convidados não podem usar as cores do tema.** | Regra de traje no manual do bom convidado («Não vista vinho, preto nem dourado!»). |
| 5 | **Culto de Acção de Graças** em vez de missa. | Os eventos são texto livre. Nunca assumir uma religião. |
| 6 | **A mensagem com a ilustração primeiro**, antes de «Com a bênção de Deus». | A ordem das secções é configurável por convite. |
| 7 | **Lista de presentes como lista de artigos**, e não de lojas («Preferimos uma lista do que indicar uma loja»). | A secção de presentes suporta duas formas: artigos (com ícones) ou lojas. |
| 8 | **Ligações entre secções harmonizadas** (cortes visíveis entre secções). | Regras de harmonia entre secções (ver [02 §7](02-experiencia-do-convite.md#7-harmonia-entre-secções)). |
| 9 | **A festa começa às 17h.** O local foi enviado como pin do Google Maps. | Os eventos aceitam coordenadas. Os botões do Google Maps e do Waze usam as coordenadas. |
| 10 | **Confirmação para um número de WhatsApp da família.** | Um ou dois botões de confirmação por convite, cada um com o seu número. |
| 11 | **Horário e local do culto ainda por definir** no momento da aprovação. No fim, **não houve culto**. | Um evento pode estar «a confirmar»: o texto aparece sem botões de mapa. O convite tem de funcionar com um só evento (só a festa). |
| 12 | **«E a lista de convidados tem de se enviar?»** A resposta foi que a família cadastra os convidados ela própria. | **Zona de gestão de convidados para a família**, com acesso por PIN e sem conta ([decisão 0001](decisoes/0001-gestao-de-convidados-pela-familia.md)). Cada convidado cadastrado tem um **link pessoal** (nome e número de pessoas). O **link geral** («Convite para Família e Amigos») continua disponível para grupos. |

## Métricas de sucesso

| Métrica | Meta inicial |
|---|---|
| Tempo do operador para montar um convite novo (tema existente) | ≤ 2 horas, sem tocar em código |
| Rondas de revisão até à aprovação | ≤ 3 |
| Convidados que abrem o convite (links pessoais) | ≥ 80 % |
| Convidados que tocam em «Confirmar presença» | ≥ 60 % |
| Desempenho do convite no telemóvel (Lighthouse, perfil móvel) | ≥ 90 |
| Reclamações de «não abre no meu telemóvel» | 0 |

## Riscos

| Risco | Mitigação |
|---|---|
| Dados pessoais de **menores** (nomes, fotografias) num link partilhável | Galeria desligada por omissão. Links com tokens impossíveis de adivinhar. `noindex`. Apagar os dados após o evento (ver [06](06-requisitos-nao-funcionais.md#privacidade-e-protecção-de-dados)). |
| Clientes pedirem temas com **personagens protegidas** (Disney e outras marcas) | Os temas são sempre conceitos genéricos com arte original («A Bela e o Príncipe», nunca personagens, logótipos ou cenas reconhecíveis). Ver [03](03-design-e-temas.md#propriedade-intelectual). |
| A confirmação pelo WhatsApp não gera dados estruturados | No link pessoal, o convidado responde no convite e a resposta fica gravada ([decisão 0003](decisoes/0003-confirmacao-dentro-do-convite.md)). No link geral, a família continua a marcar à mão. |
| Telemóveis antigos e navegadores dentro de aplicações (WhatsApp, Facebook) | Alternativas para navegadores antigos já testadas no protótipo. Matriz de compatibilidade (ver [06](06-requisitos-nao-funcionais.md#compatibilidade)). |
| Dependência de serviços externos (Google Fonts, mapas) | Fontes alojadas na própria plataforma. Os mapas são só links externos e nunca bloqueiam o convite. |
