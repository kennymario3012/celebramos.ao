import {
  alterarLista, ErroValidacao, interpretarCsv, interpretarLista, lerLista, type LinhaImportada, marcarRepetidas, MAXIMO_CONVIDADOS, novoConvidado,
} from "@/lib/convidados";
import { autorizar, erro, json } from "@/lib/http";

export const dynamic = "force-dynamic";

/** Tamanho máximo do texto: uma lista colada, ou um ficheiro CSV (que o navegador lê e envia como texto). */
const MAXIMO = { lista: 100_000, csv: 500_000 };

const prontas = (linhas: LinhaImportada[]) => linhas.flatMap((l) => (l.ok ? [l.convidado] : []));

function caber(actuais: number, novos: number) {
  if (actuais + novos > MAXIMO_CONVIDADOS) {
    throw new ErroValidacao(`A lista passaria de ${MAXIMO_CONVIDADOS} convidados: já tem ${actuais} e esta importação traz ${novos}.`);
  }
}

/**
 * Importar convidados de uma lista colada (`formato` "lista", por omissão) ou de um ficheiro CSV (`formato` "csv").
 * Sem `confirmar` devolve a pré-visualização; com `confirmar: true` grava as linhas prontas. Nos dois casos, as
 * linhas repetidas (o nome de alguém da lista ou de uma linha anterior) ficam de fora, verificadas outra vez ao gravar.
 */
export async function POST(req: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const a = await autorizar(req, slug);
  if ("resposta" in a) return a.resposta;
  const corpo = (await req.json().catch(() => null)) ?? {};
  const csv = corpo.formato === "csv";
  if (typeof corpo.texto !== "string" || !corpo.texto.trim()) return erro(400, csv ? "O ficheiro está vazio." : "Cole a lista de convidados.");
  if (corpo.texto.length > (csv ? MAXIMO.csv : MAXIMO.lista)) {
    return erro(400, csv ? "O ficheiro é grande demais (máximo 500 KB)." : "A lista é grande demais: cole no máximo 500 linhas de cada vez.");
  }
  try {
    const { linhas, semTitulos } = csv ? interpretarCsv(corpo.texto) : { linhas: interpretarLista(corpo.texto), semTitulos: false };
    if (!corpo.confirmar) {
      const { lista } = await lerLista(slug);
      const marcadas = marcarRepetidas(linhas, lista.convidados);
      caber(lista.convidados.length, prontas(marcadas).length);
      return json({ linhas: marcadas, ...(semTitulos ? { semTitulos } : {}) });
    }
    const { resultado: criados } = await alterarLista(slug, (lista) => {
      const novos = prontas(marcarRepetidas(linhas, lista.convidados));
      if (!novos.length) throw new ErroValidacao(prontas(linhas).length ? "Estes convidados já estão na lista." : "Nenhuma linha válida para importar.");
      caber(lista.convidados.length, novos.length);
      const tokens = new Set(lista.convidados.map((x) => x.token));
      for (const v of novos) {
        const c = novoConvidado(v, tokens);
        tokens.add(c.token);
        lista.convidados.push(c);
      }
      return novos.length;
    });
    return json({ criados, ignoradas: linhas.length - criados });
  } catch (e) {
    if (e instanceof ErroValidacao) return erro(400, e.message);
    console.error(e);
    return erro(500, "Não foi possível gravar. Tente outra vez.");
  }
}
