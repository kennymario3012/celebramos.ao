# Documentação

Especificação da plataforma **celebramos.ao**. É a fonte de verdade para quem desenvolve: pessoas e agentes de código.

## Índice

| Documento | Conteúdo |
|---|---|
| [01 · Produto](01-produto.md) | Visão, personas, âmbito, jornada do anfitrião, **decisões validadas com um cliente real**, métricas, riscos |
| [02 · Experiência do convite](02-experiencia-do-convite.md) | O que o convidado vê, com valores exactos: envelope, secções, personalização, computador, **harmonia entre secções**, acessibilidade, textos |
| [03 · Design e temas](03-design-e-temas.md) | Tipografia, tokens de cor, contraste, componentes, ícones, kit de um tema, pipeline de arte, propriedade intelectual |
| [04 · Modelo de dados](04-modelo-de-dados.md) | Configuração do convite campo a campo ([esquema JSON](esquemas/convite.schema.json)), entidades da plataforma, `.ics`, identificadores |
| [05 · Plataforma](05-plataforma.md) | Módulos, estados, papéis, autenticação, back-office, convidados, confirmações, rotas, arquitectura proposta, **do protótipo à plataforma** |
| [06 · Requisitos não funcionais](06-requisitos-nao-funcionais.md) | Desempenho, compatibilidade, acessibilidade, privacidade (Lei n.º 22/11), segurança, partilha, fiabilidade |
| [07 · Critérios de aceitação](07-criterios-de-aceitacao.md) | Critérios com ID, o que já está automatizado, como portar os testes, definição de pronto |
| [08 · Roadmap](08-roadmap.md) | Marcos, épicos e histórias com «Feito quando», **decisões em aberto** |

Imagens de referência (capturas do protótipo e da zona de gestão): [`img/`](img/). A implementação de referência está em [`../prototipo/`](../prototipo/). A primeira parte da plataforma (convite servido com links pessoais e zona de gestão de convidados) está em [`../apps/web/`](../apps/web/).

Decisões tomadas: [`decisoes/`](decisoes/). A primeira é a [0001 · Gestão de convidados pela própria família](decisoes/0001-gestao-de-convidados-pela-familia.md).

## Ordem de leitura

- **Toda a gente:** 01, depois 02 (com o protótipo aberto ao lado).
- **Front-end do convite:** 02 → 03 → 04 §1–3 → 06 (desempenho e compatibilidade) → 07.
- **Back-end e painel:** 04 → 05 → 06 (privacidade e segurança) → 07 (plataforma) → 08.
- **Design de temas:** 03 → 02 §7 → 07.

## Convenções

- **tem de** = obrigatório · **deve** = recomendado (desvio justificado no PR) · **pode** = opcional.
- **«a confirmar»** = proposta à espera de decisão do titular (lista em [08](08-roadmap.md#decisões-em-aberto)).
- *(Plataforma)* = só se aplica à plataforma, não ao protótipo.
- Todos os nomes e dados dos exemplos são **fictícios**.

## Glossário

| Termo | Significado |
|---|---|
| **Anfitrião** | Quem convida e contrata (pais da debutante, noivos). No convite aparece como «pais». |
| **Homenageado** | A pessoa celebrada. Na configuração do protótipo: `debutante`. |
| **Convidado** | Pessoa ou grupo («Sr. Carlos Neto e Família») a quem se envia um link pessoal, válido para N pessoas. |
| **Convite** | A página que o convidado abre. Na plataforma corresponde a um **evento**. |
| **Link pessoal** | `/c/{slug}/{token}`: personalizado para um convidado. |
| **Link geral** | `/c/{slug}`: sem nome, para grupos («Convite para Família e Amigos»). |
| **Pré-visualização** | Link para a família aprovar o convite antes do envio, em **modo demonstração** (convidado de exemplo). |
| **Ecrã de abertura** | O envelope fechado que aparece antes do convite. |
| **Selo** | O selo de cera do envelope (monograma, «15» ou rosa). |
| **Monograma** | Iniciais do homenageado em versaletes. |
| **Secção** | Um ecrã do convite (Mensagem, Convite, Confirmação, Galeria, Cronograma, Contagem, Manual, Presentes, Obrigada). |
| **Tema** | Cores (tokens), selo e arte (papel, cantos, grinalda, ilustrações). |
| **Tokens** | Variáveis CSS do tema (`--bg`, `--accent`…). |
| **Decoração** | As imagens florais de cada secção (cantos e grinaldas) e a sua posição. |
| **Harmonia** | As regras que evitam cortes e excessos nas fronteiras entre secções. |
| **Confirmação** | O convidado avisa que vai. Hoje é feita por WhatsApp, com uma mensagem pré-escrita. |
| **Intenção de confirmação** | O registo de que o convidado tocou em «Confirmar presença». |
| **Versão** | Uma fotografia imutável da configuração, criada a cada publicação. |
| **Operador** | Membro da equipa celebramos.ao que monta convites para clientes. |
| **Zona de gestão de convidados** | Página `/gestao/{slug}` onde a família, com um PIN, cadastra os convidados, envia os links e acompanha as respostas. |
| **Convite de referência** | O convite de mercado que inspirou a experiência ([01](01-produto.md#contexto)). |
