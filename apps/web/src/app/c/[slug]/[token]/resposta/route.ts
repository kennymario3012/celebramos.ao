import { naoEncontrado } from "@/convite/respostas";
import {
  alterarLista, aplicarResposta, type DadosResposta, ErroValidacao, procurarConvidado, registarActividade, respostasRecentes, RESPOSTAS_POR_HORA,
} from "@/lib/convidados";
import { carregarEvento } from "@/lib/eventos";
import { erro } from "@/lib/http";
import { fimDoPrazo } from "@/lib/texto";

export const dynamic = "force-dynamic";

class NaoEncontrado extends Error {}

/**
 * Resposta do convidado dentro do convite (link pessoal): `{estado, pessoas?, mensagem?}`.
 * O acesso é o do convite: um slug ou token desconhecido dá o mesmo 404. Responde 204 quando grava,
 * 410 depois do prazo de confirmação e 429 com demasiadas respostas seguidas.
 */
export async function POST(req: Request, { params }: { params: Promise<{ slug: string; token: string }> }) {
  const { slug, token } = await params;
  const evento = await carregarEvento(slug);
  if (!evento || !(await procurarConvidado(slug, token))) return naoEncontrado();
  if (Date.now() >= fimDoPrazo(evento.configuracao).getTime()) return erro(410, "O prazo de confirmação terminou.");
  let corpo: DadosResposta | null;
  try {
    corpo = JSON.parse((await req.text()).slice(0, 2000));
  } catch {
    return erro(400, "Pedido inválido.");
  }
  if (!corpo || typeof corpo !== "object") return erro(400, "Pedido inválido.");
  const dados = corpo;
  try {
    if ((await respostasRecentes(slug, token)) >= RESPOSTAS_POR_HORA) {
      return erro(429, "Demasiadas respostas seguidas. Tente outra vez mais tarde.");
    }
    await alterarLista(slug, (lista) => {
      const c = lista.convidados.find((x) => x.token === token);
      if (!c) throw new NaoEncontrado();
      aplicarResposta(c, dados);
    });
    await registarActividade(slug, token, "resposta").catch(() => {});
    return new Response(null, { status: 204, headers: { "Cache-Control": "no-store" } });
  } catch (e) {
    if (e instanceof NaoEncontrado) return naoEncontrado();
    if (e instanceof ErroValidacao) return erro(400, e.message);
    console.error("resposta não gravada", (e as Error).message);
    return erro(503, "Não foi possível gravar a resposta. Tente outra vez.");
  }
}
