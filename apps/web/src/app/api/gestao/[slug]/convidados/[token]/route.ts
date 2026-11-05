import { alterarLista, aplicarAlteracao, ErroValidacao } from "@/lib/convidados";
import { autorizar, erro, json } from "@/lib/http";
import { gerarToken } from "@/lib/texto";

export const dynamic = "force-dynamic";

type Contexto = { params: Promise<{ slug: string; token: string }> };

class NaoEncontrado extends Error {}

/** Alterar um convidado (dados, estado da confirmação, enviado) ou gerar um link novo (`novoLink: true`). */
export async function PATCH(req: Request, { params }: Contexto) {
  const { slug, token } = await params;
  const a = await autorizar(req, slug);
  if ("resposta" in a) return a.resposta;
  const corpo = await req.json().catch(() => ({}));
  try {
    const { resultado } = await alterarLista(slug, (lista) => {
      const c = lista.convidados.find((x) => x.token === token);
      if (!c) throw new NaoEncontrado();
      aplicarAlteracao(c, corpo);
      if (corpo.novoLink === true) {
        const tokens = new Set(lista.convidados.map((x) => x.token));
        let novo = gerarToken();
        while (tokens.has(novo)) novo = gerarToken();
        c.token = novo;
        delete c.enviadoEm;
      }
      return c;
    });
    return json({ convidado: resultado });
  } catch (e) {
    if (e instanceof NaoEncontrado) return erro(404, "Este convidado já não existe (a lista foi alterada noutro aparelho).");
    if (e instanceof ErroValidacao) return erro(400, e.message);
    console.error(e);
    return erro(500, "Não foi possível gravar. Tente outra vez.");
  }
}

/** Apagar um convidado: o link deixa de funcionar. */
export async function DELETE(req: Request, { params }: Contexto) {
  const { slug, token } = await params;
  const a = await autorizar(req, slug);
  if ("resposta" in a) return a.resposta;
  try {
    await alterarLista(slug, (lista) => {
      lista.convidados = lista.convidados.filter((x) => x.token !== token);
    });
    return new Response(null, { status: 204 });
  } catch (e) {
    console.error(e);
    return erro(500, "Não foi possível apagar. Tente outra vez.");
  }
}
