// Prepara um evento real a partir de uma configuração de convite (formato de docs/04 §1):
// gera o PIN da família, guarda só o hash, e escreve em eventos-privados/ (ignorado pelo git):
//   <slug>.evento.json        → carregar no armazenamento como eventos/<slug>/evento.json
//   CELEBRAMOS_EVENTOS.json   → valor para a variável de ambiente CELEBRAMOS_EVENTOS (alternativa)
// Uso: node scripts/preparar-evento.mjs <config.json> [--pin 123456]
import crypto from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const app = join(dirname(fileURLToPath(import.meta.url)), "..");
const [ficheiro, ...resto] = process.argv.slice(2);
if (!ficheiro) {
  console.error("Uso: node scripts/preparar-evento.mjs <config.json> [--pin 123456]");
  process.exit(1);
}
const i = resto.indexOf("--pin");
const pin = i >= 0 ? resto[i + 1] : String(crypto.randomInt(0, 1_000_000)).padStart(6, "0");
if (!/^\d{6,12}$/.test(pin)) {
  console.error("O PIN tem de ter 6 a 12 algarismos.");
  process.exit(1);
}

const configuracao = JSON.parse(readFileSync(ficheiro, "utf8"));
delete configuracao.$comentario;
const slug = configuracao.id;
if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(slug)) {
  console.error("`id` da configuração não é um slug válido.");
  process.exit(1);
}
configuracao.demonstracao = false;
configuracao.convidados = {};

const sal = crypto.randomBytes(16);
const evento = {
  configuracao,
  linkGeralActivo: true,
  gestao: { pin: { sal: sal.toString("base64url"), hash: crypto.scryptSync(pin, sal, 32).toString("base64url") } },
};

const pasta = join(app, "eventos-privados");
mkdirSync(pasta, { recursive: true });
writeFileSync(join(pasta, `${slug}.evento.json`), JSON.stringify(evento));
const caminhoAmbiente = join(pasta, "CELEBRAMOS_EVENTOS.json");
const ambiente = existsSync(caminhoAmbiente) ? JSON.parse(readFileSync(caminhoAmbiente, "utf8")) : {};
ambiente[slug] = evento;
writeFileSync(caminhoAmbiente, JSON.stringify(ambiente));
console.log(`evento ${slug} preparado em eventos-privados/ · zona de gestão: /gestao/${slug} · PIN da família: ${pin}`);
