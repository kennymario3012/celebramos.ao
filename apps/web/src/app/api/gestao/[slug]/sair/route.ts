import { json } from "@/lib/http";
import { cookieDeSaida } from "@/lib/sessao";

export const dynamic = "force-dynamic";

export async function POST(_req: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return json({ ok: true }, 200, { "Set-Cookie": cookieDeSaida(slug) });
}
