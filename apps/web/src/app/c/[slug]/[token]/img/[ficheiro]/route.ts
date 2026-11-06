import { responderFoto } from "@/convite/fotos";
import { naoEncontrado } from "@/convite/respostas";
import { procurarConvidado } from "@/lib/convidados";
import { carregarEvento } from "@/lib/eventos";

export const dynamic = "force-dynamic";

/** Foto da galeria pelo link pessoal: só com um token válido. Não conta como abertura. */
export async function GET(req: Request, { params }: { params: Promise<{ slug: string; token: string; ficheiro: string }> }) {
  const { slug, token, ficheiro } = await params;
  if (!(await carregarEvento(slug)) || !(await procurarConvidado(slug, token))) return naoEncontrado();
  return responderFoto(req, slug, ficheiro);
}
