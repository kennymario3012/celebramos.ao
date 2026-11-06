import { carregarEvento } from "@/lib/eventos";
import { erro, json, pedidoHttps } from "@/lib/http";
import { bloqueado, cookieDeSessao, limparFalhas, registarFalha, verificarPin } from "@/lib/sessao";

export const dynamic = "force-dynamic";

export async function POST(req: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const evento = await carregarEvento(slug);
  if (!evento?.gestao?.pin) return erro(404, "Evento não encontrado.");
  if (req.headers.get("x-celebramos") !== "1") return erro(403, "Pedido recusado.");
  if (await bloqueado(slug)) return erro(429, "Demasiadas tentativas erradas. Tente outra vez daqui a 15 minutos.");
  const corpo = await req.json().catch(() => ({}));
  const pin = typeof corpo.pin === "string" ? corpo.pin.replace(/\s/g, "") : "";
  if (!/^\d{4,12}$/.test(pin) || !verificarPin(pin, evento.gestao.pin)) {
    await registarFalha(slug);
    await new Promise((r) => setTimeout(r, 600));
    return erro(401, "PIN errado.");
  }
  await limparFalhas(slug);
  return json({ ok: true }, 200, { "Set-Cookie": await cookieDeSessao(evento, pedidoHttps(req)) });
}
