import { lerActividade, lerLista } from "@/lib/convidados";
import { paraCsv } from "@/lib/csv";
import { autorizar, origemPublica } from "@/lib/http";
import { telefoneLegivel } from "@/lib/texto";

export const dynamic = "force-dynamic";

const ESTADO = { pendente: "Pendente", confirmado: "Confirmado", recusado: "Não vem" } as const;
const data = (iso?: string) => (iso ? new Date(iso).toLocaleString("pt-PT", { timeZone: "Africa/Luanda" }) : "");

/** Exportar a lista em CSV (abre no Excel). */
export async function GET(req: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const a = await autorizar(req, slug);
  if ("resposta" in a) return a.resposta;
  const [{ lista }, actividade] = await Promise.all([lerLista(slug), lerActividade(slug)]);
  const origem = origemPublica(req);
  const linhas: (string | number | undefined)[][] = [
    ["Nome", "Pessoas", "Telefone", "Grupo", "Estado", "Pessoas confirmadas", "Enviado em", "Aberto em", "Tocou em confirmar",
      "Respondeu no convite", "Mensagem do convidado", "Notas", "Link"],
    ...lista.convidados.map((c) => [
      c.nome, c.pessoas, telefoneLegivel(c.telefone), c.grupo, ESTADO[c.estado], c.estado === "confirmado" ? (c.pessoasConfirmadas ?? c.pessoas) : "",
      data(c.enviadoEm), data(actividade[c.token]?.abertoEm), data(actividade[c.token]?.confirmarEm),
      data(c.resposta?.em), c.resposta?.mensagem, c.notas, `${origem}/c/${slug}/${c.token}`,
    ]),
  ];
  return new Response(paraCsv(linhas), {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="convidados-${slug}.csv"`,
      "Cache-Control": "no-store",
    },
  });
}
