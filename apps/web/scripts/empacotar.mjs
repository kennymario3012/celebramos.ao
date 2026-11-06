// Monta o pacote para o cPanel (Setup Node.js App) a partir de `next build`:
//   dist/celebramos-web/server.js      ficheiro de arranque
//   dist/celebramos-web/.next/static   recursos do Next
//   dist/celebramos-web/public         temas (imagens)
//   dist/celebramos-web/node_modules   só as dependências necessárias (não é preciso npm install no servidor)
// Uso: npm run build && npm run empacotar
import { cpSync, existsSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const app = join(dirname(fileURLToPath(import.meta.url)), "..");
const standalone = join(app, ".next", "standalone");
if (!existsSync(join(standalone, "server.js"))) {
  console.error("Falta .next/standalone/server.js: correr `npm run build` primeiro.");
  process.exit(1);
}
const destino = join(app, "dist", "celebramos-web");
rmSync(join(app, "dist"), { recursive: true, force: true });
cpSync(standalone, destino, { recursive: true });
cpSync(join(app, ".next", "static"), join(destino, ".next", "static"), { recursive: true });
cpSync(join(app, "public"), join(destino, "public"), { recursive: true });

// nunca levar dados (locais ou reais) no pacote
const proibidos = [/(^|\/)\.dados-locais(\/|$)/, /(^|\/)eventos-privados(\/|$)/, /(^|\/)\.env/];
function percorrer(pasta) {
  for (const nome of readdirSync(pasta)) {
    const completo = join(pasta, nome);
    const rel = relative(destino, completo).split("\\").join("/");
    if (proibidos.some((p) => p.test(rel))) {
      rmSync(completo, { recursive: true, force: true });
      console.warn(`removido do pacote: ${rel}`);
      continue;
    }
    if (statSync(completo).isDirectory()) percorrer(completo);
  }
}
percorrer(destino);

writeFileSync(
  join(destino, "LEIA-ME.txt"),
  `celebramos.ao — pacote para o cPanel (Setup Node.js App)

1. Enviar o conteúdo desta pasta para a raiz da aplicação (ex.: /home/<utilizador>/celebramos-web).
2. Setup Node.js App: Node.js 20 ou mais recente · Modo de aplicação: Production ·
   Raiz da aplicação: celebramos-web · Ficheiro de arranque: server.js
3. Variáveis de ambiente:
   CELEBRAMOS_DADOS=/home/<utilizador>/celebramos-dados   (pasta dos dados, FORA da raiz da aplicação)
   URL_PUBLICO=https://<domínio>
4. Dados de cada evento: <CELEBRAMOS_DADOS>/eventos/<slug>/evento.json, e as fotos da galeria em
   <CELEBRAMOS_DADOS>/eventos/<slug>/img/ (a pasta que scripts/preparar-evento.mjs gera)
5. Reiniciar a aplicação. Depois de actualizar o pacote: reiniciar e limpar a cache do NGINX.

Não é preciso «Run NPM Install»: as dependências já vêm no pacote.
Instruções completas: apps/web/README.md no repositório.
`,
);
console.log(`pacote pronto: ${relative(app, destino)}`);
