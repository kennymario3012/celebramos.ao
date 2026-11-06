# Publicar no cPanel

É o procedimento usado nas publicações de Novembro de 2026. O servidor só **corre** a aplicação: nunca se faz `npm install` nem `next build` no cPanel, porque a conta tem 1 GB de memória.

## 1. Antes de começar

- O PR está integrado na `main` e a execução da «Plataforma» desse commit está verde:
  ```bash
  gh run list --repo kennymario3012/celebramos.ao --branch main --workflow plataforma.yml --limit 3
  ```
- O titular tem uma sessão aberta no cPanel, no browser interno.
  - A sessão cai quando o IP dele muda («Your IP address has changed. Please log in again.»). Nesse caso pede-se que entre outra vez. O agente nunca escreve a palavra-passe.
  - O endereço do painel tem um token `cpsess…`, que muda a cada entrada.

## 2. Preparar o ZIP

Descarregar o artefacto exige autenticação no GitHub, mesmo com o repositório público:

```bash
R=kennymario3012/celebramos.ao
RUN=<id da execução>
AID=$(gh api repos/$R/actions/runs/$RUN/artifacts --jq '.artifacts[] | select(.name=="celebramos-web") | .id')
gh api repos/$R/actions/artifacts/$AID/zip > celebramos-web.zip
```

O artefacto tem `server.js`, `.next/` (incluída graças a `include-hidden-files: true`), `public/`, `node_modules/`, `package.json` e `LEIA-ME.txt`. Para que a extracção recrie a pasta, embrulha-se tudo numa pasta `celebramos-web/`:

```bash
mkdir -p staging/celebramos-web && unzip -q celebramos-web.zip -d staging/celebramos-web
cat staging/celebramos-web/.next/BUILD_ID             # para verificar depois
(cd staging && zip -r -X -q ../actualizacao-celebramos-<sha>.zip celebramos-web)
```

Dá-se um nome novo ao ZIP em cada versão. O ZIP vai para a pasta privada do operador (por exemplo `envio-cpanel/`), e mostra-se no Finder para ele o arrastar.

## 3. Enviar

O browser interno do agente **não consegue escolher ficheiros locais**: o input do upload está escondido e as ferramentas do browser não enviam ficheiros.

1. Abrir `…/frontend/jupiter/filemanager/upload-ajax.html?dir=%2Fhome%2F<utilizador>`.
2. Pedir ao titular que arraste o ZIP para «Drop files here to start uploading».
3. Confirmar o tamanho no servidor antes de extrair. Lê-se a partir da página do cPanel com sessão iniciada:
   `fetch('/cpsess…/execute/Fileman/list_files?dir=%2Fhome%2F<utilizador>')`.

## 4. Trocar a aplicação, com retorno possível

No Gestor de ficheiros, em `/home/<utilizador>`:

1. Mover a cópia antiga `celebramos-web-anterior` para o lixo: «Remover», com «Skip the trash and permanently delete» **desmarcado**. No lixo, o cPanel acrescenta `.1`, `.2` aos nomes repetidos.
2. Renomear `celebramos-web` para `celebramos-web-anterior`.
3. Seleccionar o ZIP → «Extract» → no campo do caminho escrever `/`, que é a pasta pessoal → «Extract Files».
   - No DOM há cópias escondidas da caixa. Clique-se no botão **visível**.
   - Depois de renomear, a lista do cPanel pode mostrar nomes antigos até se recarregar. Confirme-se pela API (`list_files`).
4. Confirmar `celebramos-web/.next/BUILD_ID`.
5. **Setup Node.js App** → aplicação `celebramos.ao/` → **«Reiniciar»**.
6. Página inicial do cPanel → «NGINX Caching» → **«Clear Cache»**. Já aconteceu o primeiro clique falhar, por isso confirma-se.

Não se toca em `celebramos-dados`. O ZIP fica em `/home/<utilizador>` até o titular o mandar para o lixo.

## 5. Verificar

```bash
ID=<BUILD_ID do pacote>
curl -s -o /tmp/g -w '%{http_code} %{time_total}s\n' https://celebramos.ao/gestao/<slug>; grep -c "$ID" /tmp/g
curl -s https://celebramos.ao/ | grep -c "$ID"      # página inicial: depende da limpeza da cache
```

O primeiro pedido depois de reiniciar demora **7 a 15 s**, enquanto o Passenger arranca o Node. Os seguintes demoram cerca de 0,1 s. Uma rota nova de POST responde **405** a um GET, e um token desconhecido dá **404**.

## Voltar atrás

Renomear `celebramos-web` para outro nome e `celebramos-web-anterior` para `celebramos-web`. Depois «Reiniciar» e «Clear Cache».

## Primeira instalação

A produção já está instalada, por isso isto é só referência.

- **SSL:** certificado válido. Hoje é Let's Encrypt com `*.celebramos.ao`, emitido por validação DNS.
- **Setup Node.js App → Criar aplicação:**

  | Campo | Valor |
  |---|---|
  | Versão do Node.js | 24 |
  | Modo de aplicação | Production |
  | Raiz da aplicação | `celebramos-web` |
  | URL da aplicação | domínio na raiz |
  | Ficheiro de arranque | `server.js` |
  | Registo do Passenger | `/home/<utilizador>/logs/celebramos.log` |

  O formulário mostra o prefixo `/home/<utilizador>/`.
- **Variáveis de ambiente:** `CELEBRAMOS_DADOS=/home/<utilizador>/celebramos-dados` e `URL_PUBLICO=https://celebramos.ao`.
- **Nunca** carregar em «Executar NPM Install». O `node_modules` do pacote é uma pasta real, e o Passenger usa-a.
- **Domínios → «Force HTTPS Redirect»:** ligado. Demorou cerca de 50 s a aplicar e recarrega o servidor, o que obriga a um arranque a frio.
- No painel estreito do browser interno, o formulário do Node.js e o Gestor de ficheiros ficam apertados. Emular uma janela de 1280 px de largura antes de clicar.
