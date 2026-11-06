// Prepara um evento real a partir de uma configuração de convite (formato de docs/04 §1).
// Gera o PIN da família (guarda só o hash), trata as fotos da galeria e escreve em eventos-privados/ (ignorado pelo git):
//   <slug>/evento.json        → enviar para CELEBRAMOS_DADOS/eventos/<slug>/evento.json
//   <slug>/img/               → fotos da galeria: enviar para CELEBRAMOS_DADOS/eventos/<slug>/img/
//   CELEBRAMOS_EVENTOS.json   → valor para a variável de ambiente CELEBRAMOS_EVENTOS (alternativa ao evento.json;
//                               as fotos ficam sempre na pasta dos dados)
// Fotos: um `src` relativo («img/foto-1.jpg») é procurado a partir da pasta da configuração. Cada foto é recodificada
// em WebP com 1600 px no máximo, o que apaga os metadados EXIF, incluindo a localização (docs/06). Para isso é preciso
// o sharp (`npm install` em apps/web). Nos exemplos do protótipo (`demonstracao`), as fotos em falta vêm do kit do tema.
// Uso: node scripts/preparar-evento.mjs <config.json> [--pin 123456]
import crypto from "node:crypto";
import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { basename, dirname, join, resolve } from "node:path";
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
const exemplo = configuracao.demonstracao === true;
configuracao.demonstracao = false;
configuracao.convidados = {};

const privados = join(app, "eventos-privados");
const pasta = join(privados, slug);
rmSync(pasta, { recursive: true, force: true });
mkdirSync(pasta, { recursive: true });

// fotos da galeria → <slug>/img/foto-<n>.webp
const origem = dirname(resolve(ficheiro));
const kit = join(app, "..", "..", "prototipo", "temas", configuracao.tema.id);
const faltam = [];
let sharp;
for (const [n, foto] of configuracao.galeria.fotos.entries()) {
  if (/^(\/|https?:)/.test(foto.src)) continue; // endereço absoluto: fica como está
  const nome = `foto-${n + 1}.webp`;
  const destino = join(pasta, "img", nome);
  mkdirSync(dirname(destino), { recursive: true });
  const daConfiguracao = resolve(origem, foto.src);
  if (existsSync(daConfiguracao)) {
    sharp ??= await carregarSharp();
    try {
      // rotate() aplica a orientação do EXIF; a imagem nova sai sem metadados
      await sharp(daConfiguracao)
        .rotate()
        .resize({ width: 1600, height: 1600, fit: "inside", withoutEnlargement: true })
        .webp({ quality: 80 })
        .toFile(destino);
    } catch (e) {
      faltam.push(`${foto.src} (${e.message})`);
      continue;
    }
  } else if (exemplo && existsSync(join(kit, basename(foto.src)))) {
    copyFileSync(join(kit, basename(foto.src)), destino);
    console.warn(`exemplo: ${foto.src} vem do kit do tema ${configuracao.tema.id}`);
  } else {
    faltam.push(foto.src);
    continue;
  }
  foto.src = `img/${nome}`;
}
if (faltam.length) {
  rmSync(pasta, { recursive: true, force: true });
  console.error(`Fotos da galeria em falta ou ilegíveis (procuradas a partir de ${origem}): ${faltam.join(", ")}`);
  process.exit(1);
}

async function carregarSharp() {
  try {
    return (await import("sharp")).default;
  } catch {
    rmSync(pasta, { recursive: true, force: true });
    console.error("As fotos são recodificadas com o sharp: correr `npm install` em apps/web primeiro.");
    process.exit(1);
  }
}

const sal = crypto.randomBytes(16);
const evento = {
  configuracao,
  linkGeralActivo: true,
  gestao: { pin: { sal: sal.toString("base64url"), hash: crypto.scryptSync(pin, sal, 32).toString("base64url") } },
};

writeFileSync(join(pasta, "evento.json"), JSON.stringify(evento));
const caminhoAmbiente = join(privados, "CELEBRAMOS_EVENTOS.json");
const ambiente = existsSync(caminhoAmbiente) ? JSON.parse(readFileSync(caminhoAmbiente, "utf8")) : {};
ambiente[slug] = evento;
writeFileSync(caminhoAmbiente, JSON.stringify(ambiente));
const fotos = configuracao.galeria.fotos.filter((f) => f.src.startsWith("img/")).length;
console.log(
  `evento ${slug} preparado em eventos-privados/${slug}/ (${fotos} ${fotos === 1 ? "foto" : "fotos"}) · ` +
    `zona de gestão: /gestao/${slug} · PIN da família: ${pin}`,
);
