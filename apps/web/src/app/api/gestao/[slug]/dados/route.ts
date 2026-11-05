import { lerActividade, lerLista } from "@/lib/convidados";
import { autorizar, erro, json, origemPublica } from "@/lib/http";
import { carregarEvento } from "@/lib/eventos";
import { dataCurta, dataLonga, MENSAGEM_ENVIO_PADRAO } from "@/lib/texto";

export const dynamic = "force-dynamic";

export async function GET(req: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const a = await autorizar(req, slug);
  if ("resposta" in a) {
    // o ecrã de entrada mostra o nome do evento mesmo sem sessão
    if (a.resposta.status === 401) {
      const ev = await carregarEvento(slug);
      if (ev) return json({ erro: "Sessão terminada.", evento: { titulo: ev.configuracao.calendario.titulo, cores: cores(ev.configuracao.tema.tokens) } }, 401);
    }
    return a.resposta;
  }
  const cfg = a.evento.configuracao;
  try {
    const [{ lista }, actividade] = await Promise.all([lerLista(slug, true), lerActividade(slug)]);
    const origem = origemPublica(req);
    return json({
      evento: {
        slug,
        titulo: cfg.calendario.titulo,
        homenageado: cfg.debutante,
        dataCurta: dataCurta(cfg),
        dataLonga: dataLonga(cfg),
        hora: cfg.data.hora,
        prazoConfirmacao: cfg.confirmacao.ate,
        linkGeral: a.evento.linkGeralActivo === false ? null : `${origem}/c/${slug}`,
        cores: cores(cfg.tema.tokens),
      },
      mensagemEnvio: lista.mensagemEnvio || a.evento.gestao?.mensagemEnvio || MENSAGEM_ENVIO_PADRAO,
      convidados: lista.convidados.map((c) => ({
        ...c,
        link: `${origem}/c/${slug}/${c.token}`,
        actividade: actividade[c.token] ?? { aberturas: 0 },
      })),
    });
  } catch (e) {
    console.error(e);
    return erro(500, "Não foi possível ler a lista de convidados. Tente outra vez.");
  }
}

function cores(t: Record<string, string>) {
  return { accent: t["--accent"], bg: t["--bg"], ink: t["--ink"], muted: t["--muted"], gold: t["--gold"] };
}
