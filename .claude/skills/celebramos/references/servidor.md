# Servidor de produção

**Alojamento:**
- conta cPanel da Host2Africa (tema Jupiter, CloudLinux), com o domínio `celebramos.ao`;
- Apache com Passenger 6.2.1 para a aplicação Node.js, e NGINX à frente, com cache;
- limites: 1 GB de memória, 1 MB/s de E/S e 10 GB de disco;
- SSH e Git Version Control existem mas não são usados. Não há Terminal web.

O endereço do painel e as credenciais estão com o titular, não no repositório.

## Pastas, em `/home/<utilizador>`

| Pasta | O quê |
|---|---|
| `celebramos-web/` | Aplicação em produção, o pacote do CI |
| `celebramos-web-anterior/` | Versão anterior, para voltar atrás |
| `celebramos-dados/` | `eventos/<slug>/…` e `sistema/segredo-sessao.json` (fora da aplicação, entra nos backups JetBackup) |
| `logs/celebramos.log` | Registo do Passenger: cada arranque mostra «▲ Next.js …» e «Running next.config took …» |
| `tmp/manter-acordado.txt` | Cabeçalhos da última execução do cron (ver abaixo) |
| `public_html/.htaccess` | Bloco «CLOUDLINUX PASSENGER CONFIGURATION», que o Setup Node.js App escreve |
| `.trash/` | Lixo do Gestor de ficheiros (recuperável em «View Trash → Restaurar») |

Ler ficheiros sem mexer, a partir da página do cPanel com sessão iniciada: `fetch('/cpsess…/execute/Fileman/list_files?dir=…')` e `get_file_content?dir=…&file=…`. Usar a API só para **ler**. As alterações fazem-se pela interface, com o OK do titular.

## HTTPS e redireccionamento

- Certificado Let's Encrypt para `celebramos.ao` e `*.celebramos.ao`, renovado por validação DNS.
- Domínios → «Force HTTPS Redirect»: ligado. `http://` responde 301 para `https://` e mantém o caminho.

## Cache do NGINX

- O link pessoal, as fotos e a zona de gestão nunca ficam em cache (`private` ou `no-store`).
- Ficam em cache:
  - a página inicial `/`;
  - o link geral `/c/<slug>`, durante 60 s;
  - o `calendario.ics`, durante 5 min.

  Depois de cada publicação, carrega-se em «Clear Cache» na página inicial do cPanel.
- Na primeira publicação, sem a limpeza, a raiz continuou a mostrar o antigo «Index of /».

## Arranque a frio e o cron que mantém a aplicação acordada

O Passenger pára a aplicação sem visitas. Arrancar de novo demora **7 a 15 s** com o limite de E/S, e um pedido chegou a esperar mais de 40 s. Para o primeiro convidado não esperar, há um Cron Job com o OK do titular:

```
*/3 * * * * /usr/bin/curl -sS -D /home/<utilizador>/tmp/manter-acordado.txt -o /dev/null --max-time 60 -A "celebramos-manter-acordado" https://celebramos.ao/c/_manter-acordado >/dev/null 2>&1
```

- `_manter-acordado` é um slug inválido: nunca coincide com um evento.
- A resposta é 404 com `no-store`, por isso passa pela cache e chega ao Passenger.
- `manter-acordado.txt` guarda a data (`Date:`) e o código da última execução.
- Verificado: depois de 9 minutos sem visitas, o primeiro pedido levou 0,19 s.
- Os sinais `%` no crontab têm significado especial. O comando foi escrito sem eles de propósito, por isso usa `-D` e não `-w`.

## Registos e estatísticas

- O «Visitors» do cPanel mostra os registos processados, com atraso. Não serve para ver o que aconteceu há minutos.
- O `access-logs` aponta para fora da pasta pessoal e o Gestor de ficheiros não o abre.
- Para ver se a aplicação reiniciou, conta-se o número de «Ready» em `logs/celebramos.log`.

## Problemas conhecidos

| Sintoma | Causa e solução |
|---|---|
| Erro 500 em todas as páginas | Falta `CELEBRAMOS_DADOS`, e o registo do Passenger diz «Definir CELEBRAMOS_DADOS» |
| «Convite não encontrado» | `evento.json` em falta ou com JSON inválido na pasta do evento |
| A raiz ou páginas estáticas desactualizadas | Falta «Clear Cache» |
| Compilação antiga servida | Falta «Reiniciar» no Setup Node.js App |
| O primeiro pedido demora muito | Arranque a frio: confirmar que o cron corre (data em `manter-acordado.txt`) |
| «AJAX Error», ou a API devolve HTML ou 401 | A sessão do cPanel caiu, muitas vezes por mudança do IP do titular. Pedir-lhe que entre outra vez |
| O cron não grava a alteração | Foi a sessão que caiu. Entrar outra vez e repetir «Edit Line» |

## No computador do operador

Os testes ponta a ponta e as compilações ocupam centenas de MB, e o Mac do titular esteve com o disco cheio. Trabalhar na pasta temporária da sessão, apagar o que se gerou (`node_modules`, `.next`, `dist`, cópias de pacotes) e avisar o titular antes de apagar o que não foi o agente a criar.
