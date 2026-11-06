import { responderFoto } from "@/convite/fotos";
import { naoEncontrado } from "@/convite/respostas";
import { carregarEvento } from "@/lib/eventos";

export const dynamic = "force-dynamic";

/** Foto da galeria pelo link geral: só enquanto o link geral estiver activo. */
export async function GET(req: Request, { params }: { params: Promise<{ slug: string; ficheiro: string }> }) {
  const { slug, ficheiro } = await params;
  const evento = await carregarEvento(slug);
  if (!evento || evento.linkGeralActivo === false) return naoEncontrado();
  return responderFoto(req, slug, ficheiro);
}
