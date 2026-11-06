/**
 * Acesso da família à zona de gestão: PIN (scrypt) e sessão em cookie assinado (HMAC).
 * Sem contas nem palavras-passe guardadas em claro.
 */
import crypto from "node:crypto";
import { armazenamento, ConflitoEscrita } from "./armazenamento";
import type { Evento, PinGuardado } from "./tipos";

const DURACAO_SESSAO_S = 30 * 24 * 3600;
const JANELA_FALHAS_MS = 15 * 60 * 1000;
const MAX_FALHAS = 10;

let segredoEmCache: Buffer | null = null;

/** Segredo de assinatura: SEGREDO_SESSAO, ou um segredo aleatório guardado (uma vez) no armazenamento privado. */
async function segredo(): Promise<Buffer> {
  if (segredoEmCache) return segredoEmCache;
  if (process.env.SEGREDO_SESSAO) return (segredoEmCache = Buffer.from(process.env.SEGREDO_SESSAO));
  const caminho = "sistema/segredo-sessao.json";
  const a = armazenamento();
  let lido = await a.lerJSON<{ segredo: string }>(caminho);
  if (!lido) {
    try {
      await a.escreverJSON(caminho, { segredo: crypto.randomBytes(32).toString("base64url") }, { criar: true });
    } catch (e) {
      if (!(e instanceof ConflitoEscrita)) throw e;
    }
    lido = await a.lerJSON<{ segredo: string }>(caminho);
  }
  if (!lido) throw new Error("Não foi possível obter o segredo de sessão.");
  return (segredoEmCache = Buffer.from(lido.dados.segredo, "base64url"));
}

export function criarPin(pin: string): PinGuardado {
  const sal = crypto.randomBytes(16);
  const hash = crypto.scryptSync(pin, sal, 32);
  return { sal: sal.toString("base64url"), hash: hash.toString("base64url") };
}

export function verificarPin(pin: string, guardado: PinGuardado) {
  const esperado = Buffer.from(guardado.hash, "base64url");
  const obtido = crypto.scryptSync(pin, Buffer.from(guardado.sal, "base64url"), esperado.length);
  return crypto.timingSafeEqual(esperado, obtido);
}

export const nomeCookie = (slug: string) => `cg_${slug.replace(/-/g, "_")}`;

/** Mudar o PIN invalida as sessões abertas (a impressão digital entra na assinatura). */
const impressao = (evento: Evento) => evento.gestao?.pin?.hash.slice(0, 16) ?? "sem-pin";

async function assinar(evento: Evento, expira: number) {
  return crypto.createHmac("sha256", await segredo()).update(`gestao:${evento.slug}:${expira}:${impressao(evento)}`).digest("base64url");
}

export async function cookieDeSessao(evento: Evento, https: boolean) {
  const expira = Math.floor(Date.now() / 1000) + DURACAO_SESSAO_S;
  const valor = `${expira}.${await assinar(evento, expira)}`;
  return `${nomeCookie(evento.slug)}=${valor}; Path=/; Max-Age=${DURACAO_SESSAO_S}; HttpOnly; SameSite=Lax${https ? "; Secure" : ""}`;
}

export function cookieDeSaida(slug: string) {
  return `${nomeCookie(slug)}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax`;
}

function lerCookie(req: Request, nome: string) {
  const cabecalho = req.headers.get("cookie") || "";
  for (const parte of cabecalho.split(";")) {
    const [k, ...v] = parte.trim().split("=");
    if (k === nome) return v.join("=");
  }
  return null;
}

export async function sessaoValida(req: Request, evento: Evento) {
  const valor = lerCookie(req, nomeCookie(evento.slug));
  if (!valor) return false;
  const [expiraTxt, assinatura] = valor.split(".");
  const expira = Number(expiraTxt);
  if (!Number.isInteger(expira) || expira < Date.now() / 1000 || !assinatura) return false;
  const esperado = Buffer.from(await assinar(evento, expira));
  const obtido = Buffer.from(assinatura);
  return esperado.length === obtido.length && crypto.timingSafeEqual(esperado, obtido);
}

/* ---------------- tentativas falhadas (por evento) ---------------- */

const caminhoSeguranca = (slug: string) => `eventos/${slug}/seguranca.json`;

export async function bloqueado(slug: string) {
  const lido = await armazenamento().lerJSON<{ falhas: number[] }>(caminhoSeguranca(slug));
  const recentes = (lido?.dados.falhas ?? []).filter((t) => t > Date.now() - JANELA_FALHAS_MS);
  return recentes.length >= MAX_FALHAS;
}

export async function registarFalha(slug: string) {
  const a = armazenamento();
  for (let i = 0; i < 3; i++) {
    const lido = await a.lerJSON<{ falhas: number[] }>(caminhoSeguranca(slug));
    const falhas = (lido?.dados.falhas ?? []).filter((t) => t > Date.now() - JANELA_FALHAS_MS);
    falhas.push(Date.now());
    try {
      await a.escreverJSON(caminhoSeguranca(slug), { falhas }, lido ? { etag: lido.etag } : { criar: true });
      return;
    } catch (e) {
      if (!(e instanceof ConflitoEscrita)) throw e;
    }
  }
}

export async function limparFalhas(slug: string) {
  const a = armazenamento();
  const lido = await a.lerJSON<{ falhas: number[] }>(caminhoSeguranca(slug));
  if (lido && lido.dados.falhas.length) {
    await a.escreverJSON(caminhoSeguranca(slug), { falhas: [] }, { etag: lido.etag }).catch(() => {});
  }
}
