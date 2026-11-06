# Eventos reais

Tudo o que identifica um cliente (nomes, telefones, coordenadas, fotos, PIN) **fica fora do git**:
- na pasta privada do operador, por exemplo `Celebramos/envio-cpanel/` no iCloud;
- e no servidor, em `CELEBRAMOS_DADOS/eventos/<slug>/`.

Nos exemplos usa-se `<slug>`, e nunca o nome de um cliente.

## Ficheiros de um evento no servidor

| Ficheiro | O quê | Quem escreve |
|---|---|---|
| `evento.json` | `{configuracao, linkGeralActivo, gestao: {pin: {sal, hash}}}` | o operador, por envio |
| `img/` | Fotos da galeria (`foto-1.webp`…) | o operador |
| `convidados.json` | Lista, respostas e mensagem de envio | a plataforma, **nunca o envio** |
| `actividade/` | Sinais de abertura, confirmação e resposta | a plataforma |
| `seguranca.json` | PINs errados recentes: 10 em 15 min bloqueiam durante 15 min | a plataforma |

O evento fica em memória até 60 s, por isso uma mudança no `evento.json` só aparece depois disso.

## Preparar a configuração

- Formato: `docs/04` §1 e `docs/esquemas/convite.schema.json`. Pode partir-se de `prototipo/configs/exemplo-*.json`.
- `id` é o slug: minúsculas, algarismos e hífenes, por exemplo `nome-15-anos`. O convite fica em `celebramos.ao/c/<slug>`.
- `confirmacao.ate` escreve-se como no convite, por exemplo «14 de Novembro de 2026». O formulário fecha no **fim desse dia, na hora de Luanda**.
- Textos do WhatsApp, com os textos aprovados pelo titular (decisão 0003, revisão):
  - `confirmacao.mensagem`: «Olá! Eu, {convidado}, confirmo a minha presença{pessoas} na festa de 15 anos da {debutante}, no dia {dataCurta}.»
  - `confirmacao.mensagemRecusa`: «Olá! Eu, {convidado}, infelizmente não vou poder estar presente na festa de 15 anos da {debutante}, no dia {dataCurta}. Agradeço muito o convite e desejo uma festa muito bonita!»
  - `{pessoas}` dá « (3 pessoas)» e `{dataCurta}` dá «21 de Novembro». No link geral, `{convidado}` passa a «[o seu nome]».
  - Noutros tipos de evento, adaptar «festa de 15 anos».
  - O `evento.json` tem prioridade sobre os textos por omissão. Mudar um texto num evento já publicado é reenviar o `evento.json`.
- A mensagem de envio dos convites é outra. Edita-a a família na zona de gestão, em «Mensagem do WhatsApp», com `{convidado}`, `{homenageado}`, `{dataCurta}`, `{hora}`, `{pessoas}` e `{link}` (obrigatório).
- Validar:
  ```bash
  python3 -m venv /tmp/v && /tmp/v/bin/pip install -q jsonschema
  cd prototipo && /tmp/v/bin/python testes/validar_config.py /caminho/config.json
  ```
  Para validar um `evento.json` completo, extrai-se antes só a `configuracao`.

## Gerar o evento

```bash
cd apps/web && npm install        # o sharp recodifica as fotos
node scripts/preparar-evento.mjs /caminho/config.json > /pasta-privada/PIN-<slug>.txt
# → eventos-privados/<slug>/evento.json (+ img/)
```

O script **escreve o PIN na saída**, por isso redirecciona-se a saída para um ficheiro privado e não a mostrar. As fotos de `img/` ao lado da configuração passam a WebP com 1600 px no máximo, sem EXIF nem GPS. Com menores, a galeria vem desligada por omissão, e só se publicam fotos com autorização registada.

Se o titular já trouxer um `evento.json` completo, valida-se a `configuracao` e envia-se tal como está. Só se acrescentam textos ou outros campos que ele tenha aprovado.

## Trocar o PIN de um evento

Faz-se quando a família o perdeu, ou quando o PIN veio num ficheiro sem o texto em claro. Gera-se como o script, sem o mostrar:

```js
import crypto from "node:crypto";
const pin = String(crypto.randomInt(0, 1_000_000)).padStart(6, "0");
const sal = crypto.randomBytes(16);
evento.gestao.pin = { sal: sal.toString("base64url"), hash: crypto.scryptSync(pin, sal, 32).toString("base64url") };
// escrever o PIN só num ficheiro privado; confirmar com scryptSync(pin, sal, 32) == hash
```

No servidor:
1. Renomear `evento.json` para `evento.json.antes-pin`.
2. Extrair o ZIP novo.
3. Confirmar que o `sal` e o `hash` coincidem com o ficheiro local.

O PIN antigo deixa de funcionar e as sessões abertas caducam, porque a assinatura das sessões inclui a impressão do PIN.

## Enviar para o servidor

- Faz-se um ZIP só com `celebramos-dados/eventos/<slug>/evento.json`, mais `img/` se houver. Extrai-se em `/home/<utilizador>` (o caminho `/`).
- **Nunca** se inclui `convidados.json`, porque apagaria a lista da família.
- Cada versão leva um nome novo (`evento-<slug>-v2.zip`), e confirma-se o tamanho antes de extrair.

## Verificar

```bash
curl -s https://celebramos.ao/c/<slug> | grep -o '<title>[^<]*</title>'
curl -s https://celebramos.ao/c/<slug>/calendario.ics | grep -E '^(SUMMARY|DTSTART)'
```

Abrir `/gestao/<slug>` no browser interno: deve aparecer o ecrã do PIN com o nome do evento. O agente não entra. Quem testa a entrada é o titular.

## Entregar à família

- O link `celebramos.ao/gestao/<slug>` e o PIN seguem por um canal privado. Depois, apaga-se o ficheiro do PIN.
- O manual personalizado acompanha-os (ver `manuais.md`).

## Retirar um evento

1. Exportar a lista.
2. Mover a pasta `eventos/<slug>` para o lixo do cPanel.

Em produção ficou também o evento de teste `exemplo-bela-principe`, criado na primeira publicação, que se pode retirar da mesma forma.
