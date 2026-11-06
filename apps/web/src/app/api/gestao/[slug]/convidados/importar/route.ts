import { alterarLista, ErroValidacao, interpretarLista, novoConvidado } from "@/lib/convidados";
import { autorizar, erro, json } from "@/lib/http";

export const dynamic = "force-dynamic";

/** Colar uma lista: sem `confirmar` devolve a pré-visualização; com `confirmar: true` grava as linhas válidas. */
export async function POST(req: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const a = await autorizar(req, slug);
  if ("resposta" in a) return a.resposta;
  const corpo = await req.json().catch(() => ({}));
  if (typeof corpo.texto !== "string" || corpo.texto.length > 100_000) return erro(400, "Cole a lista de convidados.");
  const linhas = interpretarLista(corpo.texto);
  if (!corpo.confirmar) return json({ linhas });
  const validas = linhas.flatMap((l) => (l.ok ? [l.convidado] : []));
  if (!validas.length) return erro(400, "Nenhuma linha válida para importar.");
  try {
    await alterarLista(slug, (lista) => {
      if (lista.convidados.length + validas.length > 1000) throw new ErroValidacao("A lista passaria de 1000 convidados.");
      const tokens = new Set(lista.convidados.map((x) => x.token));
      for (const v of validas) {
        const c = novoConvidado(v, tokens);
        tokens.add(c.token);
        lista.convidados.push(c);
      }
    });
    return json({ criados: validas.length, ignoradas: linhas.length - validas.length });
  } catch (e) {
    if (e instanceof ErroValidacao) return erro(400, e.message);
    console.error(e);
    return erro(500, "Não foi possível gravar. Tente outra vez.");
  }
}
