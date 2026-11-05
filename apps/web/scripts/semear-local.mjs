// Desenvolvimento: cria em .dados-locais/ os dois eventos fictícios do protótipo, com o PIN 123456.
// Uso: npm run semear   (depois: npm run dev  →  http://localhost:3000/gestao/exemplo-bela-principe)
import crypto from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const app = join(dirname(fileURLToPath(import.meta.url)), "..");
const raiz = process.env.CELEBRAMOS_DADOS || join(app, ".dados-locais");
const PIN = process.env.PIN || "123456";

function criarPin(pin) {
  const sal = crypto.randomBytes(16);
  return { sal: sal.toString("base64url"), hash: crypto.scryptSync(pin, sal, 32).toString("base64url") };
}

for (const id of ["exemplo-bela-principe", "exemplo-jardim-rose"]) {
  const configuracao = JSON.parse(readFileSync(join(app, "..", "..", "prototipo", "configs", `${id}.json`), "utf8"));
  delete configuracao.$comentario;
  const evento = { configuracao, linkGeralActivo: true, gestao: { pin: criarPin(PIN) } };
  mkdirSync(join(raiz, "eventos", id), { recursive: true });
  writeFileSync(join(raiz, "eventos", id, "evento.json"), JSON.stringify(evento, null, 1));
  console.log(`evento ${id}: /gestao/${id} (PIN ${PIN})`);
}
