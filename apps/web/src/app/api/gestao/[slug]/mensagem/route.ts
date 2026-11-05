import { alterarLista } from "@/lib/convidados";
import { autorizar, erro, json } from "@/lib/http";

export const dynamic = "force-dynamic";

/** Mensagem usada em «Enviar pelo WhatsApp». Tem de levar {link}. */
export async function PUT(req: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const a = await autorizar(req, slug);
  if ("resposta" in a) return a.resposta;
  const corpo = await req.json().catch(() => ({}));
  const texto = typeof corpo.mensagemEnvio === "string" ? corpo.mensagemEnvio.trim() : "";
  if (!texto.includes("{link}")) return erro(400, "A mensagem tem de incluir {link}, que é substituído pelo link do convidado.");
  if (texto.length > 700) return erro(400, "A mensagem é demasiado longa (máximo 700 caracteres).");
  await alterarLista(slug, (lista) => {
    lista.mensagemEnvio = texto;
  });
  return json({ mensagemEnvio: texto });
}
