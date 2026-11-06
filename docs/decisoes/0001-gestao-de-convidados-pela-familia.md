# 0001 · Gestão de convidados pela própria família

- **Estado:** aceite (Novembro de 2026). O alojamento e o armazenamento (ponto 4) foram **substituídos pela [decisão 0002](0002-alojamento-no-cpanel.md)**: cPanel e ficheiros no servidor, em vez de Vercel e Vercel Blob.
- **Decidiu:** titular do projecto, a partir do pedido do primeiro cliente real
- **Afecta:** [01](../01-produto.md#decisões-validadas), [04](../04-modelo-de-dados.md#8-implementação-actual-appsweb), [05](../05-plataforma.md#zona-de-gestão-de-convidados), [07](../07-criterios-de-aceitacao.md#zona-de-gestão-de-convidados), [08](../08-roadmap.md#estado)

## Contexto

A família do primeiro convite perguntou se tinha de enviar a lista de convidados. A resposta do titular foi que a lista precisa de uma **zona de gestão de convidados para cadastrar**, usada pela **própria família**. A alternativa seria a família enviar a lista e o operador cadastrar.

A festa era dali a duas semanas. A plataforma (contas, back-office) ainda não existia, e o alojamento de demonstração (artefacto no claude.ai) não guarda dados de visitantes sem sessão iniciada.

## Decisão

1. **Zona de gestão por evento**, em `/gestao/{slug}`, com **acesso por PIN** (6 algarismos, sem conta).
   - O PIN é guardado só como hash scrypt.
   - A sessão fica num cookie assinado (HMAC) e mudar o PIN invalida as sessões.
   - Ao fim de 10 tentativas erradas, o acesso bloqueia durante 15 minutos.
2. **Funções:**
   - cadastrar convidados (nome, pessoas, WhatsApp, grupo, notas), um a um ou colando uma lista;
   - link pessoal por convidado e envio pelo WhatsApp com mensagem editável;
   - «Enviado», «Abriu» e «Tocou em confirmar»;
   - resposta (vem com N pessoas, não vem);
   - filtros, pesquisa e exportação para Excel (CSV);
   - criar um link novo (o anterior deixa de funcionar) e apagar.
3. **Convite servido pela plataforma:**
   - link pessoal `/c/{slug}/{token}`, com token de 128 bits resolvido no servidor (o HTML só leva esse convidado);
   - link geral `/c/{slug}`;
   - interacções registadas por `sendBeacon`;
   - `.ics` e imagem de partilha.
4. **Tecnologia (é a proposta «a confirmar» do [05](../05-plataforma.md#arquitectura-proposta), agora em uso):**
   - Next.js em `apps/web`, alojado no Vercel;
   - dados em **Vercel Blob privado** na região `cpt1` (Cidade do Cabo, a mais próxima de Luanda), com escrita condicional por ETag para vários familiares ao mesmo tempo;
   - configuração do evento no Blob ou na variável `CELEBRAMOS_EVENTOS`;
   - o template do convite continua a vir do protótipo.

## Alternativas consideradas

- **Operador cadastra** (página privada do operador; a família envia nomes pelo WhatsApp). Mais rápido, mas não é o que o titular pediu.
- **Só especificar** para os agentes construírem. Não servia esta festa.
- **Contas com código por SMS ou WhatsApp** para cada familiar. É o objectivo (E5-S5), mas exige fornecedor de mensagens e mais tempo.

## Consequências

- Um PIN por evento, partilhado pela família: não há registo de *quem* fez cada alteração. As contas e os papéis (E5-S5) resolvem isto.
- Os dados dos convidados ficam fora de Angola (Cidade do Cabo). O parecer jurídico sobre a Lei n.º 22/11 (E8-S4) continua a bloquear o lançamento comercial.
- A configuração do evento ainda não se edita na interface. O back-office do operador (E3) passa a ser o passo seguinte natural.
- O marco M3 (convidados) adiantou-se a M1 e M2: a paridade completa do renderizador (textos no servidor, E1-S2) continua por fazer.
