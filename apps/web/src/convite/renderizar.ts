/**
 * Renderizador do convite: configuração (+ convidado actual) → HTML.
 * Usa o template do protótipo (fonte única da experiência), sincronizado por scripts/sincronizar-prototipo.mjs.
 * O HTML só leva o convidado actual: nunca a lista de convidados.
 */
import { ICONES, TEMPLATE } from "./gerado/recursos";
import { dataLonga, escaparHtml } from "@/lib/texto";
import type { ConfiguracaoConvite, ImagemTema } from "@/lib/tipos";

export interface OpcoesRender {
  slug: string;
  /** Origem pública absoluta (para og:image). */
  origem: string;
  convidado?: { token: string; nome: string; pessoas?: number } | null;
  /** Falso na pré-visualização a partir da zona de gestão (não conta como abertura). */
  registar?: boolean;
}

/** JSON seguro dentro de <script>: sem «</script>», «<!--» nem separadores de linha Unicode. */
function jsonParaScript(valor: unknown) {
  return JSON.stringify(valor, null, 1)
    .replace(/</g, "\\u003c")
    .replace(/>/g, "\\u003e")
    .replace(/&/g, "\\u0026")
    .split(String.fromCharCode(0x2028)).join("\\u2028")
    .split(String.fromCharCode(0x2029)).join("\\u2029");
}

/** Caminhos relativos do kit do tema («img/papel.webp») passam a absolutos («/temas/<tema>/papel.webp»). */
function caminhoTema(temaId: string, v: string) {
  return /^(\/|https?:)/.test(v) ? v : `/temas/${temaId}/${v.replace(/^img\//, "")}`;
}

function imagemTema<T extends ImagemTema | string>(temaId: string, v: T): T {
  if (typeof v === "string") return caminhoTema(temaId, v) as T;
  const img = v as ImagemTema;
  return { ...img, src: caminhoTema(temaId, img.src) } as T;
}

/**
 * As fotos da galeria são do evento, não do tema: «img/foto-1.webp» passa a «/c/<slug>/img/foto-1.webp»
 * no link geral e a «/c/<slug>/<token>/img/foto-1.webp» no pessoal, com a regra de acesso do convite (fotos.ts).
 */
function srcFoto(prefixo: string, v: string) {
  return /^(\/|https?:)/.test(v) ? v : prefixo + encodeURIComponent(v.replace(/^(\.\/)?img\//, ""));
}

export function configuracaoParaConvidado(base: ConfiguracaoConvite, op: OpcoesRender): ConfiguracaoConvite {
  const cfg: ConfiguracaoConvite = structuredClone(base);
  const temaId = cfg.tema.id;
  const im = cfg.tema.imagens;
  cfg.tema.imagens = {
    papel: imagemTema(temaId, im.papel),
    canto: imagemTema(temaId, im.canto),
    cantoAlt: imagemTema(temaId, im.cantoAlt),
    grinalda: imagemTema(temaId, im.grinalda),
    ilustracao: imagemTema(temaId, im.ilustracao),
    mensagem: imagemTema(temaId, im.mensagem),
  };
  const prefixoFotos = `/c/${op.slug}/${op.convidado ? `${op.convidado.token}/` : ""}img/`;
  cfg.galeria = { ...cfg.galeria, fotos: cfg.galeria.fotos.map((f) => ({ ...f, src: srcFoto(prefixoFotos, f.src) })) };
  cfg.id = op.slug;
  cfg.demonstracao = false;
  cfg.convidados = {};
  delete cfg.convidadoDemonstracao;
  cfg.calendario = { ...cfg.calendario, ics: `/c/${op.slug}/calendario.ics` };
  if (op.convidado) {
    cfg.convidadoActual = { nome: op.convidado.nome, pessoas: op.convidado.pessoas };
    if (op.registar !== false) cfg.registo = `/c/${op.slug}/${op.convidado.token}/i`;
    else delete cfg.registo;
  } else {
    delete cfg.convidadoActual;
    delete cfg.registo;
  }
  return cfg;
}

export function renderizarConvite(base: ConfiguracaoConvite, op: OpcoesRender) {
  const cfg = configuracaoParaConvidado(base, op);
  const titulo = escaparHtml(cfg.tituloPagina);
  const meta = [
    `<meta property="og:type" content="website">`,
    `<meta property="og:title" content="${titulo}">`,
    `<meta property="og:description" content="${escaparHtml(`${dataLonga(cfg)} · Toque para abrir o convite`)}">`,
    `<meta property="og:image" content="${escaparHtml(`${op.origem}/temas/${cfg.tema.id}/og.jpg`)}">`,
    `<meta property="og:image:width" content="1200">`,
    `<meta property="og:image:height" content="630">`,
    `<meta name="twitter:card" content="summary_large_image">`,
  ].join("\n");
  return TEMPLATE.replace("<title>__TITLE__</title>", `<title>${titulo}</title>\n${meta}`)
    .replace("__CONFIG__", () => jsonParaScript(cfg))
    .replace("__ICONS__", () => JSON.stringify(ICONES))
    .replace(/<meta name="theme-color" content="[^"]*">/, `<meta name="theme-color" content="${escaparHtml(cfg.tema.tokens["--bg"] || "#f7f2ea")}">`);
}

export function paginaNaoEncontrada() {
  return `<!DOCTYPE html><html lang="pt"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>Convite não encontrado</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#f7f2ea;color:#1f1416;font:18px/1.5 Georgia,serif;text-align:center;padding:2rem}</style></head>
<body><main><h1 style="font-weight:400">Convite não encontrado</h1><p>Confirme o link que recebeu ou peça um novo a quem o convidou.</p></main></body></html>`;
}
