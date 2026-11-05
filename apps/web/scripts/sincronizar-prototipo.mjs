// Copia do protótipo (fonte única da experiência do convite) para a aplicação:
//   prototipo/template.html + icones.json  ->  src/convite/gerado/recursos.ts
//   prototipo/temas/<tema>/*.webp, og.jpg ->  public/temas/<tema>/
// Corre antes de `dev` e de `build`. Os ficheiros gerados não vão para o git.
import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const app = join(dirname(fileURLToPath(import.meta.url)), "..");
const prototipo = join(app, "..", "..", "prototipo");
if (!existsSync(join(prototipo, "template.html"))) {
  console.error("prototipo/ não encontrado: construir a partir do repositório completo (apps/web usa ../../prototipo).");
  process.exit(1);
}

// telemóveis antigos sem unidades de contentor (cqi): cada declaração ganha antes uma alternativa em vw
// (a mesma transformação de prototipo/construir.py)
const html = readFileSync(join(prototipo, "template.html"), "utf8").replace(
  /([a-z-]+):([^;{}"<>]*?\d(?:\.\d+)?cqi[^;{}"<>]*)/g,
  (_, prop, valor) => `${prop}:${valor.replaceAll("cqi", "vw")};${prop}:${valor}`,
);
const icones = JSON.parse(readFileSync(join(prototipo, "icones.json"), "utf8"));

mkdirSync(join(app, "src", "convite", "gerado"), { recursive: true });
writeFileSync(
  join(app, "src", "convite", "gerado", "recursos.ts"),
  "// GERADO por scripts/sincronizar-prototipo.mjs a partir de prototipo/. Não editar.\n" +
    `export const TEMPLATE: string = ${JSON.stringify(html)};\n` +
    `export const ICONES: Record<string, string> = ${JSON.stringify(icones)};\n`,
);

const destinoTemas = join(app, "public", "temas");
rmSync(destinoTemas, { recursive: true, force: true });
for (const tema of readdirSync(join(prototipo, "temas"), { withFileTypes: true })) {
  if (!tema.isDirectory()) continue;
  const pasta = join(destinoTemas, tema.name);
  mkdirSync(pasta, { recursive: true });
  for (const f of readdirSync(join(prototipo, "temas", tema.name))) {
    if (/\.(webp|jpg)$/.test(f)) cpSync(join(prototipo, "temas", tema.name, f), join(pasta, f));
  }
}
console.log("protótipo sincronizado: template, ícones e temas");
