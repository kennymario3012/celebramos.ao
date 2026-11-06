# 06 · Requisitos não funcionais

Convenção: **tem de** = obrigatório; **deve** = recomendado (desvio justificado no PR); **pode** = opcional.

## Desempenho

Os convidados abrem o convite em telemóveis modestos e com dados móveis caros. Orçamentos para o **convite** (por convite, sem galeria nem música):

| Medida | Orçamento | Protótipo (medido) |
|---|---|---|
| HTML com CSS e JS embutidos (comprimido) | ≤ 30 KB | 20 KB (CSS 5 KB, JS 12 KB, dos quais 2 KB de configuração e ícones) |
| JavaScript próprio (comprimido) | ≤ 15 KB | 10 KB |
| Até o envelope estar pronto: HTML, 3 fontes (Allura, Cormorant SC 500/700), papel e canto | ≤ 250 KB | ≈ 230 KB |
| Convite completo (todas as imagens do tema e as 7 fontes) | ≤ 1 MB | ≈ 850 KB em WebP (o AVIF deve baixar ~30 %) |
| Lighthouse, perfil móvel: Desempenho | ≥ 90 | — |
| LCP | ≤ 2,5 s | — |
| CLS | ≤ 0,05 | — |
| TBT | ≤ 200 ms | — |

- As imagens das secções abaixo do primeiro ecrã **tem de** ter `loading="lazy"` e dimensões declaradas (`width` e `height`), para não provocarem deslocamentos.
- As fontes do ecrã de abertura **devem** ser pré-carregadas e usar `font-display: swap`.
- As animações usam só `transform` e `opacity`.
- O painel e o back-office não têm orçamento tão apertado, mas **devem** carregar em menos de 3 s numa ligação 4G.

## Compatibilidade

| Plataforma | Mínimo suportado |
|---|---|
| Chrome para Android e Android System WebView (navegadores dentro do WhatsApp, Facebook, Instagram) | 87 |
| Samsung Internet | 14 |
| Safari iOS (e vistas web no iOS) | 14.5 |
| Firefox para Android | 90 |
| Computador: Chrome, Edge, Firefox, Safari | 2 últimas versões |

Abaixo destes mínimos, o convite **tem de** continuar legível, mesmo sem animações.

Alternativas já implementadas no protótipo, a manter:

- `100vh` antes de `100svh`, e `@supports (height: 100svh)` para as alturas do cartão;
- `vw` antes de cada declaração em `cqi`, inserida na construção por expressão regular;
- cor sólida antes de cada `color-mix()`;
- `transform` em vez da propriedade `translate` e margens negativas para centrar o selo;
- altura do envelope por `calc()` em vez de `aspect-ratio`;
- `<dialog>`: `showModal()` se existir, senão o atributo `open`;
- `sessionStorage` em `try/catch` (algumas vistas web bloqueiam-no);
- `element.animate()` com recurso a `setTimeout` se não houver `finished`.

A plataforma **deve** gerar o CSS com uma ferramenta que conheça a lista de navegadores alvo (Lightning CSS ou PostCSS com `browserslist`). Por exemplo, `inset` → `top/right/bottom/left` e `gap` em flex. O protótipo usa `inset` sem alternativa.

**Matriz de teste manual antes de cada lançamento:** Android antigo (Android 9–10, Chrome actualizado), Android recente, iPhone com iOS 15+, abertura **a partir do WhatsApp** (Android e iOS) e computador.

## Acessibilidade

- WCAG 2.1 nível AA no convite e no painel.
- O convite usa-se só com teclado: envelope (`Enter`/`Espaço`), links, galeria (setas, `Esc`), botão de música.
- Leitores de ecrã: `h1` com o propósito do convite, `h2` por secção, decorações escondidas (`aria-hidden`), avisos com `aria-live`.
- Contraste conforme as regras do tema ([03](03-design-e-temas.md#regras-de-contraste-obrigatórias-para-publicar-um-tema)).
- `prefers-reduced-motion` respeitado.
- Alvos de toque ≥ 44 × 44 px.
- Texto ampliável até 200 % sem perder conteúdo (sem `user-scalable=no`).

## Privacidade e protecção de dados

O convite expõe dados pessoais (nomes, datas, locais) e, em festas de 15 anos, dados de **menores**. Aplica-se a **Lei n.º 22/11, de 17 de Junho** (Lei da Protecção de Dados Pessoais), fiscalizada pela **Agência de Protecção de Dados (APD)** ([texto da lei](https://angolex.com/paginas/leis/lei-de-protecao-de-dados-pessoais.html)).

> **Alojamento actual:** cPanel da Host2Africa ([decisão 0002](decisoes/0002-alojamento-no-cpanel.md)). Se o servidor estiver em Angola, os dados dos convidados não saem do país. Confirmar a localização com o fornecedor.
>
> **Antes do lançamento comercial, confirmar com um jurista:** a notificação ou o pedido de autorização à APD (art. 35.º). A transferência internacional de dados, se o alojamento ficar fora de Angola (arts. 33.º e 34.º). O papel da celebramos.ao: responsável pelo tratamento dos dados das contas e, provavelmente, subcontratante dos dados dos convidados, que são decididos pelo anfitrião. Os termos de serviço e a política de privacidade. A APD já aplicou multas por transferências internacionais sem autorização e por falta de notificação ([nota PLMJ, 2024](https://plmj.com/xms/files/03_Novidades_legislativas/2024/N_Colab_RVA-PLMJ_Dados_Pessoais_e_Ciber-seguranca_em_Angola.pdf)).

Requisitos:

1. **Minimização.** Do convidado guarda-se só o nome, o número de pessoas, a resposta (vou ou não vou, pessoas e uma mensagem opcional, até 300 caracteres) e, opcionalmente, o telefone e a etiqueta. Nada de moradas, emails ou documentos.
2. **Menores.**
   - A galeria fica desligada por omissão.
   - Uma fotografia de menor só é publicada com **autorização expressa** dos pais ou do representante legal, registada em `ficheiro.autorizacao`.
   - A imagem de partilha nunca leva fotografias de menores.
3. **Links não adivinháveis.** Tokens de 128 bits, sem listagens públicas e sem pesquisa. `noindex` em todas as páginas de convite.
4. **Nada de listas no navegador.** O HTML de um convite só contém o convidado actual.
5. **Tokens protegidos.** `Referrer-Policy: no-referrer` nas páginas de convite e `rel="noopener noreferrer"` nos links externos, para o token não passar ao WhatsApp, ao Google ou ao Waze.
6. **Retenção** *(a confirmar)*.
   - Os convidados e as interacções são apagados **90 dias depois do evento**. O anfitrião pode apagar mais cedo, e pode exportar antes de apagar.
   - O convite passa a «arquivado».
   - Os registos do servidor com IP são guardados até 30 dias, só para segurança.
7. **Direitos dos titulares.**
   - O anfitrião edita e apaga os dados dos seus convidados.
   - Um convidado pode pedir para ser removido: o convite **deve** ter, no fim, um link discreto «Privacidade» com a política e o contacto.
8. **Fotografias carregadas.** Os metadados EXIF (incluindo a localização GPS) são **sempre** removidos, porque a imagem é recodificada.
9. **Sem rastreadores de terceiros** no convite (nada de pixels de publicidade ou analítica de terceiros).

## Segurança

- **HTTPS:** certificado TLS válido no domínio (nunca auto-assinado: os navegadores e o WhatsApp mostram avisos). **Tem de** estar activo antes de enviar convites.
- **Público:**
  - limite de pedidos nas rotas `/c/` e no envio de códigos de acesso (nas respostas dentro do convite: 10 por hora em cada link);
  - respostas 404 iguais para slug e token inexistentes;
  - tokens comparados em tempo constante.
- **Cabeçalhos** nas páginas de convite:
  - `Content-Security-Policy` com `script-src` por *nonce*, `img-src 'self' data:` e `frame-ancestors 'self'` (para a pré-visualização no back-office);
  - `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` e `Permissions-Policy` mínima.
- **Painel:**
  - verificação de permissões **no servidor** em cada pedido e protecção CSRF;
  - sessões em cookies `HttpOnly`, `Secure`, `SameSite=Lax`;
  - registo de auditoria para exportações, apagamentos e acessos de operadores.
- **Ficheiros:**
  - tipo validado pelo conteúdo e limite de 10 MB por imagem;
  - recodificação obrigatória;
  - URLs de envio assinadas e de curta duração.
- **Dados:**
  - cópias de segurança diárias cifradas, guardadas 30 dias, com reposição testada;
  - segredos só em variáveis de ambiente ou num cofre;
  - registos sem nomes nem telefones.
- **Dependências:** actualizações automáticas (Dependabot ou Renovate) e auditoria no CI.

## SEO e partilha

- Todas as páginas de convite levam `noindex, nofollow` (meta e cabeçalho `X-Robots-Tag`).
- **Não** bloquear `/c/` no `robots.txt`. O bloqueio impediria as pré-visualizações de links do WhatsApp e a leitura do próprio `noindex`.
- Metadados Open Graph por evento (o WhatsApp mostra-os ao partilhar o link):

  ```html
  <meta property="og:type" content="website">
  <meta property="og:title" content="Convite · 15 Anos de Beatriz Almeida">
  <meta property="og:description" content="Sábado, 15 de Maio de 2027 · Toque para abrir o convite">
  <meta property="og:image" content="https://celebramos.ao/temas/bela-principe/og.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  ```

- Imagem de partilha: 1200 × 630, JPEG, até ~300 KB (o WhatsApp pode ignorar imagens pesadas), sem o nome do convidado. Ver [05](05-plataforma.md#imagem-de-partilha-open-graph).
- `<meta name="theme-color">` com o `--bg` do tema.

## Fiabilidade

- Disponibilidade das rotas `/c/` ≥ 99,5 % por mês.
- O convite publicado **tem de** abrir mesmo com a base de dados indisponível: versão imutável, cache na CDN com `stale-if-error`, e links de WhatsApp, mapas e calendário directos.
- As interacções são registadas «na melhor das hipóteses». Perder uma é aceitável, mas bloquear o convidado nunca é. A resposta dentro do convite também não bloqueia: o WhatsApp abre no mesmo toque, mesmo que a gravação falhe.
- Recuperação: RPO ≤ 24 h, RTO ≤ 4 h.

## Observabilidade e métricas

- Monitorização de erros no servidor e no cliente, **sem dados pessoais** (filtrar nomes, tokens e telefones).
- Métricas próprias do produto, a partir de `interaccao`:
  - taxa de abertura do envelope;
  - toques em «Confirmar»;
  - tempo entre o envio e a abertura;
  - aparelhos (telemóvel ou computador).
- Monitorização de disponibilidade dos convites de exemplo (`/c/exemplo-…`).

## Língua, datas e formatos

- Português de Angola com a ortografia **anterior ao Acordo Ortográfico de 1990**. Meses com maiúscula («15 de Maio de 2027»), dias da semana em minúscula («sábado»).
- Horas no formato «17h00». Datas por extenso no convite.
- Fuso **Africa/Luanda** (UTC+1, sem hora de Verão). Guardar em UTC e mostrar sempre no fuso do evento, nunca no do aparelho.
- Telefones guardados em E.164 e mostrados como `+244 923 000 000`.
- Moeda (fase 2): kwanza, «Kz 15 000,00».
- Textos da interface centralizados (preparados para outras línguas), mesmo que só exista `pt-AO`.

## Qualidade

- Os critérios do [07](07-criterios-de-aceitacao.md) correm no CI em cada pull request.
- **Regressão visual:** as capturas de `docs/img/` são a referência. Diferenças acima do limiar exigem aprovação explícita no PR.
- Os dois exemplos fictícios (`exemplo-bela-principe`, `exemplo-jardim-rose`) existem em todos os ambientes como convites de teste.
