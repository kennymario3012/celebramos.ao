import { renderizarConvite } from "@/convite/renderizar";
import { cabecalhosConvite, naoEncontrado } from "@/convite/respostas";
import { carregarEvento } from "@/lib/eventos";
import { origemPublica } from "@/lib/http";

export const dynamic = "force-dynamic";

/** Link geral do convite («Convite para Família e Amigos»). */
export async function GET(req: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const evento = await carregarEvento(slug);
  if (!evento || evento.linkGeralActivo === false) return naoEncontrado();
  const html = renderizarConvite(evento.configuracao, { slug, origem: origemPublica(req), convidado: null });
  return new Response(html, { headers: cabecalhosConvite("public, max-age=0, s-maxage=60, stale-while-revalidate=300") });
}
