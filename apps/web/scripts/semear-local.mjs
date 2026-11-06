// Desenvolvimento: cria em .dados-locais/ os dois eventos fictícios do protótipo, com o PIN 123456.
// As fotos da galeria dos exemplos são as do kit do tema (como em prototipo/construir.py) e vão para eventos/<id>/img/.
// Uso: npm run semear   (depois: npm run dev  →  http://localhost:3000/gestao/exemplo-bela-principe)
import crypto from "node:crypto";
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const app = join(dirname(fileURLToPath(import.meta.url)), "..");
const prototipo = join(app, "..", "..", "prototipo");
const raiz = process.env.CELEBRAMOS_DADOS || join(app, ".dados-locais");
const PIN = process.env.PIN || "123456";

function criarPin(pin) {
  const sal = crypto.randomBytes(16);
  return { sal: sal.toString("base64url"), hash: crypto.scryptSync(pin, sal, 32).toString("base64url") };
}

for (const id of ["exemplo-bela-principe", "exemplo-jardim-rose"]) {
  const configuracao = JSON.parse(readFileSync(join(prototipo, "configs", `${id}.json`), "utf8"));
  delete configuracao.$comentario;
  const evento = { configuracao, linkGeralActivo: true, gestao: { pin: criarPin(PIN) } };
  const pasta = join(raiz, "eventos", id);
  mkdirSync(pasta, { recursive: true });
  writeFileSync(join(pasta, "evento.json"), JSON.stringify(evento, null, 1));
  for (const { src } of configuracao.galeria.fotos) {
    mkdirSync(join(pasta, "img"), { recursive: true });
    copyFileSync(join(prototipo, "temas", configuracao.tema.id, basename(src)), join(pasta, "img", basename(src)));
  }
  console.log(`evento ${id}: /gestao/${id} (PIN ${PIN})`);
}
