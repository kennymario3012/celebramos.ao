import { modeloCsv } from "@/lib/convidados";
import { autorizar } from "@/lib/http";

export const dynamic = "force-dynamic";

/** Modelo CSV para preencher no Excel e importar com «Importar ficheiro». */
export async function GET(req: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const a = await autorizar(req, slug);
  if ("resposta" in a) return a.resposta;
  return new Response(modeloCsv(), {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": 'attachment; filename="modelo-convidados.csv"',
      "Cache-Control": "no-store",
    },
  });
}
