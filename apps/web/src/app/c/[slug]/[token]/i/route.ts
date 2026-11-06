import { procurarConvidado, registarActividade } from "@/lib/convidados";

export const dynamic = "force-dynamic";

/** Interacções do convite (sendBeacon): «aberto» e «confirmar». Responde sempre 204. */
export async function POST(req: Request, { params }: { params: Promise<{ slug: string; token: string }> }) {
  const { slug, token } = await params;
  try {
    const corpo = JSON.parse((await req.text()).slice(0, 200) || "{}");
    if ((corpo.tipo === "aberto" || corpo.tipo === "confirmar") && (await procurarConvidado(slug, token))) {
      await registarActividade(slug, token, corpo.tipo);
    }
  } catch (e) {
    console.error("interacção não registada", (e as Error).message);
  }
  return new Response(null, { status: 204, headers: { "Cache-Control": "no-store" } });
}
