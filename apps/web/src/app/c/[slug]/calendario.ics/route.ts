import { gerarIcs } from "@/convite/ics";
import { naoEncontrado } from "@/convite/respostas";
import { carregarEvento } from "@/lib/eventos";

export const dynamic = "force-dynamic";

export async function GET(_req: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const evento = await carregarEvento(slug);
  if (!evento) return naoEncontrado();
  return new Response(gerarIcs(evento.configuracao, slug), {
    headers: {
      "Content-Type": "text/calendar; charset=utf-8",
      "Content-Disposition": `attachment; filename="${slug}.ics"`,
      "Cache-Control": "public, max-age=0, s-maxage=300",
      "X-Robots-Tag": "noindex, nofollow",
    },
  });
}
