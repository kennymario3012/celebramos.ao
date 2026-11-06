import { paginaNaoEncontrada } from "./renderizar";

/** Cabeçalhos de todas as páginas de convite (docs/06: noindex, sem referenciador). */
export function cabecalhosConvite(cache: string): Record<string, string> {
  return {
    "Content-Type": "text/html; charset=utf-8",
    "Cache-Control": cache,
    "X-Robots-Tag": "noindex, nofollow",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
  };
}

/** Mesma resposta para slug e token inexistentes (não revela se o evento existe). */
export const naoEncontrado = () =>
  new Response(paginaNaoEncontrada(), { status: 404, headers: cabecalhosConvite("no-store") });
