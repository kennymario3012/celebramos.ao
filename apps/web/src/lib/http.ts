import { carregarEvento } from "./eventos";
import { sessaoValida } from "./sessao";
import type { Evento } from "./tipos";

export function json(dados: unknown, estado = 200, cabecalhos: Record<string, string> = {}) {
  return new Response(JSON.stringify(dados), {
    status: estado,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", ...cabecalhos },
  });
}

export const erro = (estado: number, mensagem: string) => json({ erro: mensagem }, estado);

/** Origem pública (para os links enviados aos convidados). URL_PUBLICO tem prioridade (domínio próprio). */
export function origemPublica(req: Request) {
  if (process.env.URL_PUBLICO) return process.env.URL_PUBLICO.replace(/\/$/, "");
  const url = new URL(req.url);
  const host = req.headers.get("x-forwarded-host") || url.host;
  const proto = req.headers.get("x-forwarded-proto") || url.protocol.replace(":", "");
  return `${proto}://${host}`;
}

export const pedidoHttps = (req: Request) => origemPublica(req).startsWith("https://");

/**
 * Pedidos da zona de gestão: evento existente, sessão válida e, nas alterações,
 * o cabeçalho X-Celebramos (impede pedidos forjados a partir de outros sites).
 */
export async function autorizar(req: Request, slug: string): Promise<{ evento: Evento } | { resposta: Response }> {
  const evento = await carregarEvento(slug);
  if (!evento || !evento.gestao?.pin) return { resposta: erro(404, "Evento não encontrado.") };
  if (req.method !== "GET" && req.headers.get("x-celebramos") !== "1") return { resposta: erro(403, "Pedido recusado.") };
  if (!(await sessaoValida(req, evento))) return { resposta: erro(401, "Sessão terminada. Entre outra vez com o PIN.") };
  return { evento };
}
