import { armazenamento } from "./armazenamento";
import type { Evento } from "./tipos";

export const SLUG_VALIDO = /^[a-z0-9]+(-[a-z0-9]+)*$/;
export const TOKEN_VALIDO = /^[A-Za-z0-9_-]{22}$/;

export const caminhoEvento = (slug: string) => `eventos/${slug}/evento.json`;

const cache = new Map<string, { evento: Evento | null; ate: number }>();
const VALIDADE_MS = 60_000;

/** Eventos definidos na variável de ambiente CELEBRAMOS_EVENTOS (JSON: { "<slug>": Evento }). */
function eventosDoAmbiente(): Record<string, Omit<Evento, "slug">> {
  const bruto = process.env.CELEBRAMOS_EVENTOS;
  if (!bruto) return {};
  try {
    return JSON.parse(bruto);
  } catch {
    console.error("CELEBRAMOS_EVENTOS não é JSON válido");
    return {};
  }
}

/**
 * Carrega um evento: primeiro do armazenamento (eventos/<slug>/evento.json),
 * depois da variável de ambiente CELEBRAMOS_EVENTOS. Fica em memória 60 s.
 */
export async function carregarEvento(slug: string): Promise<Evento | null> {
  if (!SLUG_VALIDO.test(slug)) return null;
  const emCache = cache.get(slug);
  if (emCache && emCache.ate > Date.now()) return emCache.evento;

  let evento: Evento | null = null;
  const lido = await armazenamento().lerJSON<Omit<Evento, "slug">>(caminhoEvento(slug));
  if (lido) evento = { ...lido.dados, slug };
  else {
    const doAmbiente = eventosDoAmbiente()[slug];
    if (doAmbiente) evento = { ...doAmbiente, slug };
  }
  cache.set(slug, { evento, ate: Date.now() + VALIDADE_MS });
  return evento;
}
