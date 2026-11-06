# 0002 · Alojamento no cPanel do titular

- **Estado:** aceite (Novembro de 2026)
- **Decidiu:** titular do projecto
- **Substitui:** a parte de alojamento e armazenamento da [decisão 0001](0001-gestao-de-convidados-pela-familia.md) (Vercel e Vercel Blob)
- **Afecta:** [04 §8](../04-modelo-de-dados.md#8-implementação-actual-appsweb), [05](../05-plataforma.md#implementação-actual), [06](../06-requisitos-nao-funcionais.md#privacidade-e-protecção-de-dados), [08](../08-roadmap.md#decisões-em-aberto), [`apps/web/README.md`](../../apps/web/README.md)

## Contexto

O titular não vai usar o Vercel. A plataforma fica no alojamento cPanel que já tem, com o domínio `celebramos.ao` e o fornecedor Host2Africa (`host2africa.ao`).

O cPanel tem **Setup Node.js App** (CloudLinux com Passenger; Node.js 24 recomendado), Setup Python App, Git Version Control e acesso SSH. A conta tem limites de 1 GB de memória, 1 MB/s de E/S, 100 processos e 10 GB de disco. O certificado TLS do domínio era auto-assinado no momento da decisão.

## Decisão

1. **Aplicação:** `apps/web` (Next.js) corre como aplicação Node.js do cPanel. O pacote autónomo do Next (`output: "standalone"`) é o ficheiro de arranque `server.js`. **Não se faz `npm install` nem `next build` no servidor**: com 1 GB de memória, a construção pode falhar.
2. **Construção:** o CI do GitHub constrói, testa e guarda o pacote (artefacto `celebramos-web`). Em alternativa, constrói-se localmente com `npm run pacote`. O pacote é enviado para o servidor e substitui a versão anterior.
3. **Dados:** **ficheiros JSON numa pasta fora da aplicação** (`CELEBRAMOS_DADOS`, por exemplo `/home/celebramos/celebramos-dados`). Essa pasta sobrevive às actualizações e entra nas cópias de segurança da conta (JetBackup).
   - Escrita condicional por ETag (concorrência optimista).
   - **Bloqueio entre processos** (pasta `*.bloqueio`, criação atómica), porque o Passenger pode correr vários processos.
   - Sem base de dados por agora: o volume de um evento (centenas de convidados) não a justifica.
4. **Saem:** o Vercel Blob e a dependência `@vercel/blob`, o `vercel.json` e a região `cpt1`.

## Consequências

- **Protecção de dados:** se o servidor estiver em Angola, deixa de haver transferência internacional dos dados dos convidados (Lei n.º 22/11, arts. 33.º e 34.º). **Confirmar a localização do servidor com a Host2Africa.** A notificação à APD (art. 35.º) continua por tratar (E8-S4).
- **HTTPS é obrigatório antes de enviar convites.** Com um certificado auto-assinado, os navegadores e o WhatsApp mostram avisos. É preciso emitir um certificado válido (AutoSSL ou Let's Encrypt, no cPanel ou pelo fornecedor).
- **Cache do NGINX activa no cPanel:** as respostas pessoais e da gestão levam `Cache-Control: private, no-store`. Depois de cada actualização, limpar a cache («Clear Cache»).
- **Escala:** os ficheiros e o bloqueio servem um servidor. Para vários servidores, passar para uma base de dados (a interface `Armazenamento` de `src/lib/armazenamento.ts` permite trocar).
- **Publicação manual** (enviar o pacote) até haver publicação automática por SSH a partir do CI. A publicação automática fica para a E0-S3 e precisa de uma chave SSH guardada nos segredos do GitHub.
