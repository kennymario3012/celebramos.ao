import { renderizarConvite } from "@/convite/renderizar";
import { cabecalhosConvite, naoEncontrado } from "@/convite/respostas";
import { procurarConvidado } from "@/lib/convidados";
import { carregarEvento } from "@/lib/eventos";
import { origemPublica } from "@/lib/http";

export const dynamic = "force-dynamic";

/** Link pessoal: o convidado é resolvido no servidor; o HTML só leva este convidado. */
export async function GET(req: Request, { params }: { params: Promise<{ slug: string; token: string }> }) {
  const { slug, token } = await params;
  const evento = await carregarEvento(slug);
  if (!evento) return naoEncontrado();
  const convidado = await procurarConvidado(slug, token);
  if (!convidado) return naoEncontrado();
  // ?previa=1: aberto a partir da zona de gestão, não conta como abertura do convidado
  const previa = new URL(req.url).searchParams.get("previa") === "1";
  const html = renderizarConvite(evento.configuracao, {
    slug,
    origem: origemPublica(req),
    convidado: {
      token: convidado.token,
      nome: convidado.nome,
      pessoas: convidado.pessoas,
      estado: convidado.estado,
      pessoasConfirmadas: convidado.pessoasConfirmadas,
      mensagem: convidado.resposta?.mensagem,
    },
    registar: !previa,
  });
  return new Response(html, { headers: cabecalhosConvite("private, no-store") });
}
