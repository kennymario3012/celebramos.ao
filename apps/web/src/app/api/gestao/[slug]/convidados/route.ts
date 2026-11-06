import { alterarLista, ErroValidacao, novoConvidado } from "@/lib/convidados";
import { autorizar, erro, json } from "@/lib/http";

export const dynamic = "force-dynamic";
const MAXIMO = 1000;

/** Cadastrar um convidado. */
export async function POST(req: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const a = await autorizar(req, slug);
  if ("resposta" in a) return a.resposta;
  const corpo = await req.json().catch(() => ({}));
  try {
    const { resultado } = await alterarLista(slug, (lista) => {
      if (lista.convidados.length >= MAXIMO) throw new ErroValidacao(`Máximo de ${MAXIMO} convidados.`);
      const c = novoConvidado(corpo, new Set(lista.convidados.map((x) => x.token)));
      lista.convidados.push(c);
      return c;
    });
    return json({ convidado: resultado }, 201);
  } catch (e) {
    if (e instanceof ErroValidacao) return erro(400, e.message);
    console.error(e);
    return erro(500, "Não foi possível gravar. Tente outra vez.");
  }
}
