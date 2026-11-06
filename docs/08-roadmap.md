# 08 · Roadmap

Épicos (E) e histórias (S), cada uma com o critério **Feito quando**. Os IDs `CA-…` são os do [07](07-criterios-de-aceitacao.md). Ordem sugerida: por marcos; dentro de cada épico, pela ordem das histórias.

## Marcos

| Marco | Épicos | Resultado |
|---|---|---|
| **M1 · Paridade** | E0, E1 | A plataforma serve os dois convites de exemplo com a mesma experiência do protótipo, e os critérios do convite passam no CI. |
| **M2 · Operador** | E2, E3, E6 (S1–S2) | A equipa cria, revê e publica convites reais sem tocar em código. |
| **M3 · Convidados** | E4, E5, E8 | Links pessoais, envio pelo WhatsApp, painel de confirmações e privacidade em conformidade. **Lançamento comercial.** |
| **M4 · Self-service** | E7 | O anfitrião cria e paga sozinho. |
| **M5 · Mais celebrações** | E9, E10 | Casamentos, aniversários, baptizados e extras. |

## Estado

Actualizado em Novembro de 2026. A pedido do primeiro cliente real, a **zona de gestão de convidados** para a família (marco M3) passou à frente ([decisão 0001](decisoes/0001-gestao-de-convidados-pela-familia.md)). Está em `apps/web`.

| História | Estado | Notas |
|---|---|---|
| E0-S2 | Feito | CI do protótipo e da plataforma |
| E1-S3 | Feito | `/c/{slug}` e `/c/{slug}/{token}`, 404 igual para slug e token |
| E1-S6 | Feito | `.ics` servido. Imagem de partilha por tema (`og.jpg`) |
| E4-S1 | Feito | Sem conta. Avisa quando o nome se repete. Ao colar ou importar, os nomes repetidos ficam de fora e os telefones repetidos são assinalados |
| E4-S2 | Parcial | Colar texto e importar ficheiro CSV, com modelo para o Excel: feito. Ficheiro `.xlsx`: por fazer |
| E4-S3 | Parcial | Link novo e apagar: feito. Ligar e desligar o link geral só na configuração |
| E4-S4 | Parcial | WhatsApp e copiar: feito. Partilha nativa: por fazer |
| E5-S1 | Feito | «aberto» e «confirmar» por `sendBeacon`, uma vez por aparelho |
| E5-S2 | Feito | Resumo, lista, filtros, pesquisa, respostas com número de pessoas |
| E5-S6 | Feito | Resposta dentro do convite e, depois de gravar, «Avisar a família pelo WhatsApp» ([decisão 0003](decisoes/0003-confirmacao-dentro-do-convite.md)) |
| E5-S4 | Parcial | CSV para o Excel. Ficheiro `.xlsx`: por fazer |
| E5-S5 | Parcial | PIN por evento em vez de contas e papéis |

Próximos passos sugeridos:

1. **Pôr no ar no cPanel**: certificado TLS válido e primeira publicação, como em `apps/web/README.md`.
2. Publicação automática por SSH a partir do CI (E0-S3).
3. E3 (back-office, para não editar JSON à mão).
4. E1-S2 (textos no servidor).
5. E8-S4 (parecer jurídico).
6. E5-S3 (lembretes).

## E0 · Fundações

| ID | História | Feito quando |
|---|---|---|
| E0-S1 | Estrutura do repositório (`apps/web`, `packages/convite`, `packages/esquemas`, `packages/temas`), TypeScript estrito, lint e formatação. | `install`, `build` e `test` passam no CI. O `prototipo/` continua a funcionar. |
| E0-S2 | CI: lint, tipos, testes unitários e de aceitação, e o fluxo do protótipo. | Cada PR mostra os resultados. Um PR com testes falhados não pode ser integrado. |
| E0-S3 | Ambientes (desenvolvimento, staging, produção), base de dados com migrações e dados de teste com os dois exemplos fictícios. | Staging serve `/c/exemplo-bela-principe` e `/c/exemplo-jardim-rose`. |
| E0-S4 | Armazenamento de ficheiros com CDN e cabeçalhos de segurança base. | Imagens servidas com cache imutável. Cabeçalhos do [06](06-requisitos-nao-funcionais.md#segurança) presentes. |
| E0-S5 | Monitorização de erros sem dados pessoais. | Um erro forçado aparece no serviço, sem nomes nem tokens. |

## E1 · Renderizador do convite (paridade)

| ID | História | Feito quando |
|---|---|---|
| E1-S1 | `packages/esquemas`: tipos gerados de `convite.schema.json` e validação equivalente a `validar_config.py`. | Valida os dois exemplos e rejeita os casos negativos (decoração, secção, dia da semana, ícone, botões, marcadores, coerência UTC). |
| E1-S2 | `packages/convite`: `renderizarConvite(config, convidado)` porta o `template.html`, com os textos no servidor. | As capturas dos dois exemplos coincidem com `docs/img/` dentro do limiar de regressão visual. |
| E1-S3 | Rotas `/c/{slug}` e `/c/{slug}/{token}`, com 404 e 410. | CA-PER-01 a CA-PER-05. |
| E1-S4 | Envelope e interacções com JavaScript próprio (≤ 15 KB), `<noscript>` e toque registado antes de carregar. | CA-ENV-01 a CA-ENV-11. |
| E1-S5 | Fontes alojadas e pré-carregadas. Imagens em AVIF/WebP com `srcset`. CSS gerado para os navegadores alvo. | CA-QUA-03 e CA-RES-03. |
| E1-S6 | `.ics` e imagem de partilha (Open Graph). | CA-CAL-02 e CA-QUA-04. A pré-visualização no WhatsApp mostra título, descrição e imagem. |
| E1-S7 | Porta dos testes de aceitação para Playwright, com regressão visual. | Todos os critérios do convite correm no CI, com os IDs nos títulos dos testes. |

## E2 · Dados e publicação

| ID | História | Feito quando |
|---|---|---|
| E2-S1 | Entidades do [04 §5](04-modelo-de-dados.md#5-modelo-de-domínio-plataforma) e migrações. | Migração aplicada em staging. Testes de modelo para as restrições (slug único, token único, estados). |
| E2-S2 | Gerar a configuração do convite a partir do evento, com os campos derivados ([04 §4](04-modelo-de-dados.md#4-campos-derivados)). | A partir dos dados de teste, gera configurações válidas, iguais aos exemplos nos campos de conteúdo. |
| E2-S3 | Versões imutáveis: publicar, suspender, retomar, repor. Invalidação da cache por etiqueta. | CA-PLA-04. Repor cria uma versão nova. |
| E2-S4 | Pré-visualização com token próprio e modo demonstração. | O link de pré-visualização funciona em rascunho. Renovar o token invalida o link anterior. |
| E2-S5 | Transições automáticas de estado (concluído, arquivado). | Uma tarefa diária muda os estados nas datas certas (testado com relógio simulado). |

## E3 · Back-office do operador

| ID | História | Feito quando |
|---|---|---|
| E3-S1 | Entrada de operadores (email e TOTP) e registo de auditoria. | Sem TOTP não há acesso. As exportações e os apagamentos ficam registados. |
| E3-S2 | Criar evento e editor por secções gerado a partir do esquema (limites, contadores, listas ordenáveis, selector de ícones). | Todos os campos do esquema são editáveis sem JSON à mão. |
| E3-S3 | Pré-visualização ao vivo (`iframe` com `postMessage`, larguras de 320, 375 e 430 px). | CA-PLA-02. |
| E3-S4 | Ordem das secções (arrastar e largar) e decoração automática com ajuste manual. | Mudar a ordem recalcula a decoração segundo o [02 §7](02-experiencia-do-convite.md#7-harmonia-entre-secções). |
| E3-S5 | Locais: colar um link do Google Maps e obter as coordenadas, ou pesquisar. | O link `https://maps.google.com/maps?q=<lat>%2C<lng>…` dá as coordenadas certas. |
| E3-S6 | Validação antes de publicar (esquema, coerência, contraste, eventos sem local, prazo antes da data). | CA-PLA-03. |
| E3-S7 | Teste de aceitação do back-office: recriar o convite real (anonimizado) a partir das decisões do [01](01-produto.md#decisões-validadas). | CA-PLA-01. |

## E4 · Convidados e envio

| ID | História | Feito quando |
|---|---|---|
| E4-S1 | Lista de convidados (criar, editar, apagar, etiquetas, duplicados). | Os duplicados (nome ou telefone) são assinalados. |
| E4-S2 | Colar texto e importar CSV ou Excel, com pré-visualização. | CA-PLA-05. |
| E4-S3 | Links pessoais, link geral (ligar e desligar), revogar e gerar novo. | CA-PLA-09. Com o link geral desligado, `/c/{slug}` responde 404. |
| E4-S4 | Enviar pelo WhatsApp (mensagem editável), copiar link, partilha nativa. Marcar como enviado. | CA-PLA-06. |

## E5 · Confirmações e painel

| ID | História | Feito quando |
|---|---|---|
| E5-S1 | Registo de interacções (`sendBeacon`, limite de pedidos, resposta 204). | CA-RSVP-05. O painel mostra as aberturas. |
| E5-S2 | Painel do anfitrião: números, lista filtrável, estados (confirmado/recusado, pessoas). | CA-PLA-07. |
| E5-S3 | Lembretes pelo WhatsApp para os pendentes. | A mensagem leva o link pessoal certo. |
| E5-S4 | Exportação CSV e Excel. | CA-PLA-08. |
| E5-S5 | Entrada dos anfitriões (código por telemóvel ou email) e papéis (proprietário, editor, revisor). | CA-PLA-11. |
| E5-S6 | Confirmação dentro do convite (fase 2): no link pessoal, vou ou não vou, pessoas e mensagem; grava e depois oferece «Avisar a família pelo WhatsApp»; alterar até ao prazo ([decisão 0003](decisoes/0003-confirmacao-dentro-do-convite.md)). | CA-RSVP-06 a CA-RSVP-10, CA-GES-16 e CA-GES-17. |

## E6 · Temas

| ID | História | Feito quando |
|---|---|---|
| E6-S1 | Registo de temas no back-office (tokens, selo, imagens), com verificação de contraste. | Um tema que falha o contraste não pode ser publicado. |
| E6-S2 | Migrar os temas «A Bela e o Príncipe» e «Jardim Rosé». | Os exemplos usam os temas da base de dados. |
| E6-S3 | Processo de tema novo (pipeline de arte e revisão de propriedade intelectual, [03](03-design-e-temas.md#criar-um-tema-novo)). | Um tema novo entra com capturas de referência e passa os critérios. |
| E6-S4 | Catálogo curado de ícones, por categorias. | O editor só oferece ícones do catálogo. |

## E7 · Self-service e pagamentos (fase 2)

| ID | História | Feito quando |
|---|---|---|
| E7-S1 | Assistente para o anfitrião: tipo, dados, tema, textos, pré-visualizar, publicar. | Um utilizador sem ajuda publica um convite em ≤ 30 minutos (teste com 5 pessoas). |
| E7-S2 | Textos por omissão por tipo de evento. | Cada tipo tem textos completos e com a concordância certa. |
| E7-S3 | Planos e pagamentos (meios angolanos, por exemplo Multicaixa Express e pagamento por referência; fornecedor a escolher). | Pagamento de teste ponta a ponta. A publicação depende do pagamento. |
| E7-S4 | Comentários de revisão por secção, na pré-visualização. | O revisor comenta sem conta. O operador vê e resolve. |

## E8 · Privacidade, segurança e conformidade

| ID | História | Feito quando |
|---|---|---|
| E8-S1 | Política de privacidade e termos. Link «Privacidade» no fim do convite. | Páginas publicadas e revistas por um jurista. |
| E8-S2 | Retenção automática (arquivar e apagar). | CA-PLA-10. |
| E8-S3 | Autorização para fotografias de menores e galeria desligada por omissão. | CA-GAL-03. Não é possível publicar fotografias num evento de menor sem a autorização registada. |
| E8-S4 | Revisão jurídica: notificação à APD e transferência internacional (Lei n.º 22/11). | Parecer escrito. **Bloqueia o lançamento comercial.** |
| E8-S5 | Revisão de segurança (cabeçalhos, limites de pedidos, permissões, ficheiros). | Lista do [06](06-requisitos-nao-funcionais.md#segurança) verificada. Sem falhas graves abertas. |

## E9 · Mais tipos de evento

| ID | História | Feito quando |
|---|---|---|
| E9-S1 | Remover os textos fixos de 15 anos ([05](05-plataforma.md#do-protótipo-à-plataforma), linha 4). Campo `homenageado`. | Nenhum texto do renderizador menciona «15 anos» ou «debutante» fora da configuração. |
| E9-S2 | Casamento: duas famílias em duas colunas, textos próprios, «Branco é a cor da noiva!», dois botões de confirmação. | Exemplo fictício de casamento construído e com os critérios a passar. |
| E9-S3 | Aniversário e baptizado. | Um exemplo fictício de cada. |

## E10 · Extras (por prioridade a definir)

Música (com licenças), livro de mensagens, galeria depois do evento, mesas e lugares, outras línguas. (A confirmação dentro do convite passou para a E5-S6.)

## Decisões em aberto

Para o titular do projecto decidir. Quando uma decisão for tomada, registá-la em `docs/decisoes/NNNN-titulo.md` (contexto, decisão, consequências) e actualizar estes documentos.

| # | Decisão | Opções | Proposta | Bloqueia |
|---|---|---|---|---|
| D1 | Stack | Next.js + Postgres + S3 / outra | A do [05](05-plataforma.md#arquitectura-proposta). **Em uso em `apps/web`:** Next.js com ficheiros JSON no servidor em vez de Postgres (decisões 0001 e 0002). Confirmar quando houver vários eventos em simultâneo | E0 |
| D2 | Alojamento e região | Europa, África do Sul, Angola | **Decidido:** cPanel do titular, Host2Africa ([decisão 0002](decisoes/0002-alojamento-no-cpanel.md)). Confirmar com o fornecedor que o servidor está em Angola | E8-S4 |
| D3 | Entrada dos anfitriões | Código por SMS, por WhatsApp, email | **Decidido para já:** PIN por evento para a família (decisão 0001). Depois, código por telemóvel com email como alternativa | E5-S5 |
| D4 | Confirmação | Só WhatsApp / formulário no convite + WhatsApp | **Decidido:** no link pessoal, resposta dentro do convite e, depois de gravar, botão para avisar pelo WhatsApp; no link geral, só WhatsApp ([decisão 0003](decisoes/0003-confirmacao-dentro-do-convite.md)) | — |
| D5 | Retenção dos dados dos convidados | 30, 90 ou 180 dias depois do evento | 90 dias | E8-S2 |
| D6 | Preços e pagamentos | Por convite, por pacote. Meios e fornecedor | — | E7-S3 |
| D7 | Licença do código | Privado (todos os direitos reservados) ou código aberto | — | O repositório está **público** e sem licença: o código fica visível mas não licenciado. Tornar o repositório privado se o código for proprietário. |
| D8 | Domínio e marca | `celebramos.ao` | — | E0-S3 |
| D9 | Música | Sem música, biblioteca licenciada, ficheiro do cliente | Ficheiro do cliente, com declaração de direitos | E10 |
