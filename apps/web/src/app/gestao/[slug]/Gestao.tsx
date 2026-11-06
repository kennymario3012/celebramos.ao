"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

/* ---------------- tipos (espelham a API /api/gestao/<slug>/dados) ---------------- */

type Estado = "pendente" | "confirmado" | "recusado";
interface Actividade {
  aberturas: number;
  abertoEm?: string;
  ultimaAberturaEm?: string;
  confirmarEm?: string;
}
interface Convidado {
  token: string;
  nome: string;
  pessoas: number;
  telefone?: string;
  grupo?: string;
  notas?: string;
  estado: Estado;
  pessoasConfirmadas?: number;
  /** Última resposta dada pelo próprio convidado no convite. */
  resposta?: { estado: "confirmado" | "recusado"; pessoas?: number; mensagem?: string; em: string };
  enviadoEm?: string;
  link: string;
  actividade: Actividade;
}
interface Cores {
  accent?: string;
  bg?: string;
  ink?: string;
  muted?: string;
  gold?: string;
}
interface Dados {
  evento: {
    titulo: string;
    homenageado: string;
    dataCurta: string;
    dataLonga: string;
    hora: string;
    prazoConfirmacao: string;
    prazoTerminado?: boolean;
    linkGeral: string | null;
    cores: Cores;
  };
  mensagemEnvio: string;
  convidados: Convidado[];
}
interface LinhaImportada {
  linha: number;
  ok: boolean;
  convidado?: { nome: string; pessoas: number; telefone?: string; grupo?: string };
  texto?: string;
  erro?: string;
}
type Filtro = "todos" | "por-enviar" | "enviados" | "abriram" | "nao-abriram" | "confirmados" | "recusados" | "pendentes";
type Dialogo =
  | { tipo: "novo" }
  | { tipo: "editar"; convidado: Convidado }
  | { tipo: "apagar"; convidado: Convidado }
  | { tipo: "colar" }
  | { tipo: "mensagem" };

class ErroApi extends Error {
  constructor(mensagem: string, public estado: number, public dados: Record<string, unknown>) {
    super(mensagem);
  }
}

/* ---------------- utilidades ---------------- */

function api(slug: string, caminho: string, metodo = "GET", corpo?: unknown) {
  return fetch(`/api/gestao/${slug}/${caminho}`, {
    method: metodo,
    headers: { "Content-Type": "application/json", "X-Celebramos": "1" },
    body: corpo === undefined ? undefined : JSON.stringify(corpo),
    cache: "no-store",
  }).then(async (r) => {
    if (r.status === 204) return null;
    const dados = await r.json().catch(() => ({}));
    if (!r.ok) throw new ErroApi(dados.erro || "Algo correu mal. Tente outra vez.", r.status, dados);
    return dados;
  });
}

const preencher = (modelo: string, v: Record<string, string>) =>
  modelo.replace(/\{(\w+)\}/g, (inteiro, k: string) => (k in v ? v[k] : inteiro));

const pessoasTxt = (n: number) => `${n} ${n === 1 ? "pessoa" : "pessoas"}`;

/** O que o convidado respondeu no convite, visto pela família. */
function respostaTxt(r: NonNullable<Convidado["resposta"]>) {
  if (r.estado === "recusado") return "não vem";
  return r.pessoas === 1 ? "vem 1 pessoa" : `vêm ${r.pessoas} pessoas`;
}

/** A família mudou o estado ou as pessoas depois da resposta dada no convite. */
const alteradaPelaFamilia = (c: Convidado) =>
  !!c.resposta && (c.estado !== c.resposta.estado || (c.estado === "confirmado" && (c.pessoasConfirmadas ?? c.pessoas) !== c.resposta.pessoas));

function quando(iso?: string) {
  if (!iso) return "";
  return new Date(iso).toLocaleString("pt-PT", { timeZone: "Africa/Luanda", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function telefoneLegivel(d?: string) {
  if (!d) return "";
  return /^2449\d{8}$/.test(d) ? `+244 ${d.slice(3, 6)} ${d.slice(6, 9)} ${d.slice(9)}` : `+${d}`;
}

async function copiar(texto: string) {
  try {
    await navigator.clipboard.writeText(texto);
    return true;
  } catch {
    window.prompt("Copie o link:", texto);
    return false;
  }
}

const FILTROS: { id: Filtro; rotulo: string }[] = [
  { id: "todos", rotulo: "Todos" },
  { id: "por-enviar", rotulo: "Por enviar" },
  { id: "enviados", rotulo: "Enviados" },
  { id: "abriram", rotulo: "Abriram" },
  { id: "nao-abriram", rotulo: "Não abriram" },
  { id: "confirmados", rotulo: "Vêm" },
  { id: "recusados", rotulo: "Não vêm" },
  { id: "pendentes", rotulo: "Sem resposta" },
];

function passaFiltro(c: Convidado, f: Filtro) {
  switch (f) {
    case "por-enviar": return !c.enviadoEm;
    case "enviados": return !!c.enviadoEm;
    case "abriram": return c.actividade.aberturas > 0;
    case "nao-abriram": return c.actividade.aberturas === 0;
    case "confirmados": return c.estado === "confirmado";
    case "recusados": return c.estado === "recusado";
    case "pendentes": return c.estado === "pendente";
    default: return true;
  }
}

const sem = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

/* ---------------- componente principal ---------------- */

export default function Gestao({ slug }: { slug: string }) {
  const [fase, setFase] = useState<"a-carregar" | "entrar" | "pronto" | "nao-existe" | "erro">("a-carregar");
  const [dados, setDados] = useState<Dados | null>(null);
  const [cabecalho, setCabecalho] = useState<{ titulo?: string; cores?: Cores }>({});
  const [aviso, setAviso] = useState<string | null>(null);
  const [filtro, setFiltro] = useState<Filtro>("todos");
  const [pesquisa, setPesquisa] = useState("");
  const [dialogo, setDialogo] = useState<Dialogo | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const temporizador = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const mostrarAviso = useCallback((texto: string) => {
    setAviso(texto);
    clearTimeout(temporizador.current);
    temporizador.current = setTimeout(() => setAviso(null), 4000);
  }, []);

  const carregar = useCallback(
    async (silencioso = false) => {
      try {
        const d: Dados = await api(slug, "dados");
        setDados(d);
        setCabecalho({ titulo: d.evento.titulo, cores: d.evento.cores });
        setFase("pronto");
      } catch (e) {
        const err = e as ErroApi;
        if (err.estado === 401) {
          const ev = err.dados?.evento as { titulo?: string; cores?: Cores } | undefined;
          if (ev) setCabecalho(ev);
          setFase("entrar");
        } else if (err.estado === 404) setFase("nao-existe");
        else if (!silencioso) {
          setFase((f) => (f === "a-carregar" ? "erro" : f));
          mostrarAviso(err.message);
        }
      }
    },
    [slug, mostrarAviso],
  );

  useEffect(() => {
    carregar();
  }, [carregar]);

  // outro familiar pode ter alterado a lista: actualiza ao voltar a esta página
  useEffect(() => {
    const aoVoltar = () => {
      if (document.visibilityState === "visible" && fase === "pronto") carregar(true);
    };
    document.addEventListener("visibilitychange", aoVoltar);
    return () => document.removeEventListener("visibilitychange", aoVoltar);
  }, [carregar, fase]);

  // os convidados respondem no convite a qualquer momento: actualiza de 30 em 30 s enquanto a página está à vista
  useEffect(() => {
    if (fase !== "pronto" || dialogo || ocupado) return;
    const id = setInterval(() => document.visibilityState === "visible" && carregar(true), 30_000);
    return () => clearInterval(id);
  }, [carregar, fase, dialogo, ocupado]);

  async function mudar(accao: () => Promise<unknown>, sucesso?: string) {
    setOcupado(true);
    try {
      await accao();
      if (sucesso) mostrarAviso(sucesso);
      await carregar(true);
      return true;
    } catch (e) {
      const err = e as ErroApi;
      if (err.estado === 401) setFase("entrar");
      mostrarAviso(err.message);
      return false;
    } finally {
      setOcupado(false);
    }
  }

  const estilo = useMemo(() => {
    const c = cabecalho.cores || {};
    return {
      "--acento": c.accent || "#6f1d2e",
      "--fundo": c.bg || "#f7f2ea",
      "--tinta": c.ink || "#1f1416",
      "--suave": c.muted || "#5f4c4f",
      "--ouro": c.gold || "#b8913f",
    } as React.CSSProperties;
  }, [cabecalho.cores]);

  return (
    <div className="g" style={estilo}>
      {fase === "a-carregar" && <p className="g-centro">A carregar…</p>}
      {fase === "nao-existe" && <p className="g-centro">Este evento não existe ou não tem zona de gestão.</p>}
      {fase === "erro" && (
        <div className="g-centro">
          <p>Não foi possível abrir a zona de gestão.</p>
          <button className="b b-principal" onClick={() => carregar()}>Tentar outra vez</button>
        </div>
      )}
      {fase === "entrar" && <Entrar slug={slug} titulo={cabecalho.titulo} aoEntrar={() => carregar()} />}
      {fase === "pronto" && dados && (
        <Painel
          slug={slug}
          dados={dados}
          filtro={filtro}
          setFiltro={setFiltro}
          pesquisa={pesquisa}
          setPesquisa={setPesquisa}
          abrir={setDialogo}
          mudar={mudar}
          mostrarAviso={mostrarAviso}
          sair={async () => {
            await api(slug, "sair", "POST").catch(() => {});
            setFase("entrar");
          }}
        />
      )}
      {dialogo && dados && (
        <Janela aoFechar={() => setDialogo(null)}>
          {(dialogo.tipo === "novo" || dialogo.tipo === "editar") && (
            <FormConvidado
              convidado={dialogo.tipo === "editar" ? dialogo.convidado : undefined}
              existentes={dados.convidados}
              ocupado={ocupado}
              aoFechar={() => setDialogo(null)}
              aoGravar={async (corpo, outro) => {
                const ok =
                  dialogo.tipo === "editar"
                    ? await mudar(() => api(slug, `convidados/${dialogo.convidado.token}`, "PATCH", corpo), "Alterações gravadas.")
                    : await mudar(() => api(slug, "convidados", "POST", corpo), `${corpo.nome} foi adicionado.`);
                if (ok && !outro) setDialogo(null);
                return ok;
              }}
              aoNovoLink={
                dialogo.tipo === "editar"
                  ? async () => {
                      const ok = await mudar(
                        () => api(slug, `convidados/${dialogo.convidado.token}`, "PATCH", { novoLink: true }),
                        "Link novo criado. O anterior deixou de funcionar.",
                      );
                      if (ok) setDialogo(null);
                    }
                  : undefined
              }
            />
          )}
          {dialogo.tipo === "apagar" && (
            <div className="j-conteudo">
              <h2>Apagar convidado?</h2>
              <p>
                <strong>{dialogo.convidado.nome}</strong> sai da lista e o link dele deixa de funcionar.
              </p>
              <div className="j-accoes">
                <button className="b" onClick={() => setDialogo(null)}>Cancelar</button>
                <button
                  className="b b-perigo"
                  disabled={ocupado}
                  onClick={async () => {
                    if (await mudar(() => api(slug, `convidados/${dialogo.convidado.token}`, "DELETE"), "Convidado apagado.")) setDialogo(null);
                  }}
                >
                  Apagar
                </button>
              </div>
            </div>
          )}
          {dialogo.tipo === "colar" && (
            <ColarLista slug={slug} ocupado={ocupado} aoFechar={() => setDialogo(null)} mudar={mudar} />
          )}
          {dialogo.tipo === "mensagem" && (
            <EditarMensagem
              dados={dados}
              ocupado={ocupado}
              aoFechar={() => setDialogo(null)}
              aoGravar={async (texto) => {
                if (await mudar(() => api(slug, "mensagem", "PUT", { mensagemEnvio: texto }), "Mensagem gravada.")) setDialogo(null);
              }}
            />
          )}
        </Janela>
      )}
      <div className={`aviso${aviso ? " on" : ""}`} role="status" aria-live="polite">
        {aviso}
      </div>
    </div>
  );
}

/* ---------------- entrada com PIN ---------------- */

function Entrar({ slug, titulo, aoEntrar }: { slug: string; titulo?: string; aoEntrar: () => void }) {
  const [pin, setPin] = useState("");
  const [erro, setErro] = useState("");
  const [aEntrar, setAEntrar] = useState(false);
  return (
    <main className="entrar">
      <p className="marca">celebramos.ao</p>
      <h1>Gestão de convidados</h1>
      {titulo && <p className="entrar-evento">{titulo}</p>}
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setAEntrar(true);
          setErro("");
          try {
            await api(slug, "entrar", "POST", { pin });
            aoEntrar();
          } catch (err) {
            setErro((err as Error).message);
            setPin("");
          } finally {
            setAEntrar(false);
          }
        }}
      >
        <label htmlFor="pin">PIN de acesso</label>
        <input
          id="pin"
          type="password"
          inputMode="numeric"
          autoComplete="current-password"
          pattern="[0-9]*"
          maxLength={12}
          value={pin}
          onChange={(e) => setPin(e.target.value.replace(/\D/g, ""))}
          required
          autoFocus
        />
        {erro && <p className="erro" role="alert">{erro}</p>}
        <button className="b b-principal b-largo" disabled={aEntrar || pin.length < 4}>
          {aEntrar ? "A entrar…" : "Entrar"}
        </button>
      </form>
      <p className="nota">O PIN foi enviado à família por quem preparou o convite.</p>
    </main>
  );
}

/* ---------------- painel ---------------- */

interface PropsPainel {
  slug: string;
  dados: Dados;
  filtro: Filtro;
  setFiltro: (f: Filtro) => void;
  pesquisa: string;
  setPesquisa: (s: string) => void;
  abrir: (d: Dialogo) => void;
  mudar: (accao: () => Promise<unknown>, sucesso?: string) => Promise<boolean>;
  mostrarAviso: (s: string) => void;
  sair: () => void;
}

function Painel({ slug, dados, filtro, setFiltro, pesquisa, setPesquisa, abrir, mudar, mostrarAviso, sair }: PropsPainel) {
  const { evento, convidados } = dados;
  const t = useMemo(() => {
    const soma = (f: (c: Convidado) => number) => convidados.reduce((s, c) => s + f(c), 0);
    return {
      registos: convidados.length,
      pessoas: soma((c) => c.pessoas),
      enviados: convidados.filter((c) => c.enviadoEm).length,
      abriram: convidados.filter((c) => c.actividade.aberturas > 0).length,
      vem: soma((c) => (c.estado === "confirmado" ? (c.pessoasConfirmadas ?? c.pessoas) : 0)),
      vemRegistos: convidados.filter((c) => c.estado === "confirmado").length,
      naoVem: convidados.filter((c) => c.estado === "recusado").length,
      semResposta: convidados.filter((c) => c.estado === "pendente").length,
    };
  }, [convidados]);

  const visiveis = useMemo(() => {
    const q = sem(pesquisa.trim());
    return convidados
      .filter((c) => passaFiltro(c, filtro))
      .filter((c) => !q || sem(`${c.nome} ${c.grupo ?? ""} ${c.telefone ?? ""}`).includes(q))
      .sort((a, b) => a.nome.localeCompare(b.nome, "pt"));
  }, [convidados, filtro, pesquisa]);

  return (
    <main className="painel">
      <header className="topo">
        <div>
          <p className="marca">Gestão de convidados</p>
          <h1>{evento.titulo}</h1>
          <p className="suave">
            {evento.dataLonga}, às {evento.hora} · confirmações até {evento.prazoConfirmacao}
            {evento.prazoTerminado && " (prazo terminado)"}
          </p>
        </div>
        <button className="b b-discreto" onClick={sair}>Sair</button>
      </header>

      <section className="resumo" aria-label="Resumo">
        <div><strong>{t.registos}</strong><span>{t.registos === 1 ? "convite" : "convites"} · {pessoasTxt(t.pessoas)}</span></div>
        <div><strong>{t.enviados}</strong><span>enviados</span></div>
        <div><strong>{t.abriram}</strong><span>abriram</span></div>
        <div className="r-vem"><strong>{t.vem}</strong><span>pessoas vêm ({t.vemRegistos} {t.vemRegistos === 1 ? "convite" : "convites"})</span></div>
        <div><strong>{t.naoVem}</strong><span>não vêm</span></div>
        <div><strong>{t.semResposta}</strong><span>sem resposta</span></div>
      </section>

      <section className="accoes">
        <button className="b b-principal" onClick={() => abrir({ tipo: "novo" })}>+ Adicionar convidado</button>
        <button className="b" onClick={() => abrir({ tipo: "colar" })}>Colar lista</button>
        <button className="b" onClick={() => abrir({ tipo: "mensagem" })}>Mensagem do WhatsApp</button>
        <a className="b" href={`/api/gestao/${slug}/exportar`} download>Exportar (Excel)</a>
      </section>

      {evento.linkGeral && (
        <section className="geral">
          <div>
            <p className="rotulo">Link geral (para grupos, sem nome)</p>
            <p className="link-texto">{evento.linkGeral}</p>
          </div>
          <button className="b b-pequeno" onClick={async () => (await copiar(evento.linkGeral!)) && mostrarAviso("Link geral copiado.")}>Copiar</button>
        </section>
      )}

      <section className="lista-topo">
        <input
          className="pesquisa"
          type="search"
          placeholder="Procurar por nome, grupo ou telefone"
          aria-label="Procurar convidados"
          value={pesquisa}
          onChange={(e) => setPesquisa(e.target.value)}
        />
        <div className="filtros" role="group" aria-label="Filtrar">
          {FILTROS.map((f) => (
            <button key={f.id} className={`chip${filtro === f.id ? " on" : ""}`} aria-pressed={filtro === f.id} onClick={() => setFiltro(f.id)}>
              {f.rotulo}
            </button>
          ))}
        </div>
      </section>

      {convidados.length === 0 ? (
        <div className="vazio">
          <p><strong>Ainda não há convidados.</strong></p>
          <p>Adicione um de cada vez, ou cole a lista que já tem (por exemplo, das notas do telemóvel).</p>
          <p className="suave">Cada convidado recebe um link só seu, com o nome dele no envelope e o número de pessoas do convite.</p>
        </div>
      ) : visiveis.length === 0 ? (
        <p className="vazio">Nenhum convidado neste filtro.</p>
      ) : (
        <ul className="lista">
          {visiveis.map((c) => (
            <Cartao key={c.token} slug={slug} c={c} dados={dados} abrir={abrir} mudar={mudar} mostrarAviso={mostrarAviso} />
          ))}
        </ul>
      )}
      <p className="rodape suave">
        {visiveis.length} de {convidados.length} convidados
      </p>
    </main>
  );
}

function Cartao({ slug, c, dados, abrir, mudar, mostrarAviso }: { slug: string; c: Convidado; dados: Dados; abrir: (d: Dialogo) => void; mudar: PropsPainel["mudar"]; mostrarAviso: (s: string) => void }) {
  const ev = dados.evento;
  const mensagem = preencher(dados.mensagemEnvio, {
    convidado: c.nome,
    homenageado: ev.homenageado,
    dataCurta: ev.dataCurta,
    hora: ev.hora,
    pessoas: pessoasTxt(c.pessoas),
    link: c.link,
  });
  const whatsapp = `https://wa.me/${c.telefone ?? ""}?text=${encodeURIComponent(mensagem)}`;
  const definirEstado = (estado: Estado) =>
    estado !== c.estado && mudar(() => api(slug, `convidados/${c.token}`, "PATCH", { estado }));
  const confirmadas = c.pessoasConfirmadas ?? c.pessoas;

  return (
    <li className={`cartao e-${c.estado}`}>
      <div className="c-cabeca">
        <div>
          <p className="c-nome">{c.nome}</p>
          <p className="suave">
            {pessoasTxt(c.pessoas)}
            {c.grupo && <> · {c.grupo}</>}
            {c.telefone && <> · {telefoneLegivel(c.telefone)}</>}
          </p>
          {c.notas && <p className="c-notas">{c.notas}</p>}
        </div>
        <button className="b b-discreto b-pequeno" onClick={() => abrir({ tipo: "editar", convidado: c })} aria-label={`Editar ${c.nome}`}>
          Editar
        </button>
      </div>

      <div className="c-sinais">
        <span className={c.enviadoEm ? "sinal on" : "sinal"}>{c.enviadoEm ? `Enviado ${quando(c.enviadoEm)}` : "Por enviar"}</span>
        <span className={c.actividade.aberturas ? "sinal on" : "sinal"}>
          {c.actividade.aberturas ? `Abriu ${quando(c.actividade.abertoEm)}` : "Não abriu"}
        </span>
        {c.resposta && <span className="sinal on">Respondeu no convite {quando(c.resposta.em)}</span>}
        {c.actividade.confirmarEm && <span className="sinal on">Tocou em confirmar {quando(c.actividade.confirmarEm)}</span>}
      </div>
      {c.resposta?.mensagem && <p className="c-mensagem">«{c.resposta.mensagem}»</p>}
      {c.resposta && alteradaPelaFamilia(c) && (
        <p className="c-notas">No convite: {respostaTxt(c.resposta)}. A família alterou depois.</p>
      )}

      <div className="c-estado" role="group" aria-label={`Resposta de ${c.nome}`}>
        {([
          ["pendente", "Sem resposta"],
          ["confirmado", "Vem"],
          ["recusado", "Não vem"],
        ] as [Estado, string][]).map(([id, rotulo]) => (
          <button key={id} className={`seg${c.estado === id ? " on" : ""}`} aria-pressed={c.estado === id} onClick={() => definirEstado(id)}>
            {rotulo}
          </button>
        ))}
      </div>
      {c.estado === "confirmado" && (
        <div className="c-pessoas">
          <span>Pessoas que vêm</span>
          <button className="b b-pequeno" aria-label="Menos uma pessoa" disabled={confirmadas <= 0}
            onClick={() => mudar(() => api(slug, `convidados/${c.token}`, "PATCH", { pessoasConfirmadas: confirmadas - 1 }))}>−</button>
          <strong aria-live="polite">{confirmadas}</strong>
          <button className="b b-pequeno" aria-label="Mais uma pessoa" disabled={confirmadas >= 30}
            onClick={() => mudar(() => api(slug, `convidados/${c.token}`, "PATCH", { pessoasConfirmadas: confirmadas + 1 }))}>+</button>
        </div>
      )}

      <div className="c-accoes">
        <a
          className="b b-whatsapp"
          href={whatsapp}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => {
            if (!c.enviadoEm) mudar(() => api(slug, `convidados/${c.token}`, "PATCH", { enviado: true }));
          }}
        >
          Enviar pelo WhatsApp
        </a>
        <button className="b" onClick={async () => (await copiar(c.link)) && mostrarAviso("Link copiado.")}>Copiar link</button>
        <a className="b" href={`${c.link}?previa=1`} target="_blank" rel="noopener noreferrer">Ver convite</a>
        <button className="b b-discreto" onClick={() => abrir({ tipo: "apagar", convidado: c })}>Apagar</button>
      </div>
    </li>
  );
}

/* ---------------- janelas ---------------- */

function Janela({ children, aoFechar }: { children: React.ReactNode; aoFechar: () => void }) {
  useEffect(() => {
    const tecla = (e: KeyboardEvent) => e.key === "Escape" && aoFechar();
    document.addEventListener("keydown", tecla);
    const antes = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", tecla);
      document.body.style.overflow = antes;
    };
  }, [aoFechar]);
  return (
    <div className="j-fundo" onMouseDown={(e) => e.target === e.currentTarget && aoFechar()}>
      <div className="j" role="dialog" aria-modal="true">
        {children}
      </div>
    </div>
  );
}

function FormConvidado({
  convidado,
  existentes,
  ocupado,
  aoFechar,
  aoGravar,
  aoNovoLink,
}: {
  convidado?: Convidado;
  existentes: Convidado[];
  ocupado: boolean;
  aoFechar: () => void;
  aoGravar: (corpo: { nome: string; pessoas: number; telefone: string; grupo: string; notas: string }, outro: boolean) => Promise<boolean>;
  aoNovoLink?: () => void;
}) {
  const vazio = { nome: "", pessoas: 1, telefone: "", grupo: "", notas: "" };
  const [v, setV] = useState(
    convidado
      ? { nome: convidado.nome, pessoas: convidado.pessoas, telefone: convidado.telefone ? telefoneLegivel(convidado.telefone) : "", grupo: convidado.grupo ?? "", notas: convidado.notas ?? "" }
      : vazio,
  );
  const [outro, setOutro] = useState(false);
  const nomeRef = useRef<HTMLInputElement>(null);
  const repetido = !convidado && v.nome.trim() && existentes.some((c) => sem(c.nome) === sem(v.nome.trim()));
  const grupos = useMemo(() => [...new Set(existentes.map((c) => c.grupo).filter(Boolean))] as string[], [existentes]);

  return (
    <form
      className="j-conteudo"
      onSubmit={async (e) => {
        e.preventDefault();
        const ok = await aoGravar({ ...v, pessoas: Number(v.pessoas) || 1 }, outro);
        if (ok && outro) {
          setV({ ...vazio, grupo: v.grupo });
          nomeRef.current?.focus();
        }
      }}
    >
      <h2>{convidado ? "Editar convidado" : "Adicionar convidado"}</h2>
      <label htmlFor="f-nome">Nome no convite</label>
      <input id="f-nome" ref={nomeRef} value={v.nome} maxLength={60} required autoFocus
        placeholder="Ex.: Sr. Carlos Neto e Família" onChange={(e) => setV({ ...v, nome: e.target.value })} />
      {repetido && <p className="nota">Já existe um convidado com este nome.</p>}
      <div className="f-linha">
        <div>
          <label htmlFor="f-pessoas">Pessoas</label>
          <input id="f-pessoas" type="number" inputMode="numeric" min={1} max={30} value={v.pessoas} required
            onChange={(e) => setV({ ...v, pessoas: Number(e.target.value) })} />
        </div>
        <div className="f-cresce">
          <label htmlFor="f-telefone">WhatsApp (opcional)</label>
          <input id="f-telefone" type="tel" inputMode="tel" value={v.telefone} placeholder="923 000 000"
            onChange={(e) => setV({ ...v, telefone: e.target.value })} />
        </div>
      </div>
      <label htmlFor="f-grupo">Grupo (opcional)</label>
      <input id="f-grupo" list="grupos" value={v.grupo} maxLength={40} placeholder="Ex.: Família do pai, Escola, Igreja"
        onChange={(e) => setV({ ...v, grupo: e.target.value })} />
      <datalist id="grupos">{grupos.map((g) => <option key={g} value={g} />)}</datalist>
      <label htmlFor="f-notas">Notas (só para a família)</label>
      <textarea id="f-notas" rows={2} value={v.notas} maxLength={200} onChange={(e) => setV({ ...v, notas: e.target.value })} />
      <div className="j-accoes">
        <button type="button" className="b" onClick={aoFechar}>Cancelar</button>
        {!convidado && (
          <button type="submit" className="b" disabled={ocupado} onClick={() => setOutro(true)}>Gravar e adicionar outro</button>
        )}
        <button type="submit" className="b b-principal" disabled={ocupado} onClick={() => setOutro(false)}>Gravar</button>
      </div>
      {aoNovoLink && (
        <div className="j-extra">
          <p className="nota">Enviou o link à pessoa errada? Crie um link novo: o anterior deixa de funcionar.</p>
          <button type="button" className="b b-pequeno" disabled={ocupado} onClick={aoNovoLink}>Criar link novo</button>
        </div>
      )}
    </form>
  );
}

function ColarLista({ slug, ocupado, aoFechar, mudar }: { slug: string; ocupado: boolean; aoFechar: () => void; mudar: PropsPainel["mudar"] }) {
  const [texto, setTexto] = useState("");
  const [linhas, setLinhas] = useState<LinhaImportada[] | null>(null);
  const [erro, setErro] = useState("");
  const validas = linhas?.filter((l) => l.ok).length ?? 0;

  return (
    <div className="j-conteudo">
      <h2>Colar lista de convidados</h2>
      <p className="nota">
        Um convidado por linha: <strong>nome; pessoas; telefone; grupo</strong>. Só o nome é obrigatório (sem número, conta 1 pessoa).
      </p>
      <textarea rows={8} value={texto} aria-label="Lista de convidados"
        placeholder={"Sr. Carlos Neto e Família; 3; 923 000 000; Família do pai\nAna e Rui Mendes; 2\nTia Joana"}
        onChange={(e) => {
          setTexto(e.target.value);
          setLinhas(null);
        }} />
      {erro && <p className="erro" role="alert">{erro}</p>}
      {linhas && (
        <div className="previa">
          <p><strong>{validas}</strong> de {linhas.length} linhas prontas a importar.</p>
          <ul>
            {linhas.map((l) => (
              <li key={l.linha} className={l.ok ? "" : "erro"}>
                {l.ok && l.convidado
                  ? `${l.convidado.nome} · ${pessoasTxt(l.convidado.pessoas)}${l.convidado.telefone ? " · " + telefoneLegivel(l.convidado.telefone) : ""}${l.convidado.grupo ? " · " + l.convidado.grupo : ""}`
                  : `Linha ${l.linha} («${l.texto}»): ${l.erro}`}
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="j-accoes">
        <button className="b" onClick={aoFechar}>Cancelar</button>
        {!linhas ? (
          <button className="b b-principal" disabled={!texto.trim() || ocupado}
            onClick={async () => {
              setErro("");
              try {
                const r = await api(slug, "convidados/importar", "POST", { texto });
                setLinhas(r.linhas);
              } catch (e) {
                setErro((e as Error).message);
              }
            }}>
            Ver como fica
          </button>
        ) : (
          <button className="b b-principal" disabled={!validas || ocupado}
            onClick={async () => {
              const ok = await mudar(() => api(slug, "convidados/importar", "POST", { texto, confirmar: true }), `${validas} convidados importados.`);
              if (ok) aoFechar();
            }}>
            Importar {validas} convidados
          </button>
        )}
      </div>
    </div>
  );
}

function EditarMensagem({ dados, ocupado, aoFechar, aoGravar }: { dados: Dados; ocupado: boolean; aoFechar: () => void; aoGravar: (t: string) => void }) {
  const [texto, setTexto] = useState(dados.mensagemEnvio);
  const exemplo = dados.convidados[0];
  const previa = preencher(texto, {
    convidado: exemplo?.nome ?? "Sr. Carlos Neto e Família",
    homenageado: dados.evento.homenageado,
    dataCurta: dados.evento.dataCurta,
    hora: dados.evento.hora,
    pessoas: pessoasTxt(exemplo?.pessoas ?? 3),
    link: exemplo?.link ?? "https://…",
  });
  return (
    <div className="j-conteudo">
      <h2>Mensagem do WhatsApp</h2>
      <p className="nota">
        Texto enviado com cada convite. Os campos entre chavetas são trocados automaticamente: {"{convidado}"}, {"{homenageado}"}, {"{dataCurta}"}, {"{hora}"}, {"{pessoas}"} e {"{link}"} (obrigatório).
      </p>
      <textarea rows={6} value={texto} maxLength={700} aria-label="Mensagem" onChange={(e) => setTexto(e.target.value)} />
      <p className="rotulo">Como fica</p>
      <p className="previa-msg">{previa}</p>
      <div className="j-accoes">
        <button className="b" onClick={aoFechar}>Cancelar</button>
        <button className="b b-principal" disabled={ocupado || !texto.includes("{link}")} onClick={() => aoGravar(texto)}>Gravar</button>
      </div>
    </div>
  );
}
