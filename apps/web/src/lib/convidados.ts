import { armazenamento, ConflitoEscrita } from "./armazenamento";
import { TOKEN_VALIDO } from "./eventos";
import { gerarToken, normalizarTelefone } from "./texto";
import type { Actividade, Convidado, EstadoConfirmacao, ListaConvidados } from "./tipos";

const caminhoLista = (slug: string) => `eventos/${slug}/convidados.json`;
const prefixoActividade = (slug: string) => `eventos/${slug}/actividade/`;

const listaVazia = (): ListaConvidados => ({ versao: 1, convidados: [] });

export class ErroValidacao extends Error {}

export async function lerLista(slug: string) {
  const lido = await armazenamento().lerJSON<ListaConvidados>(caminhoLista(slug));
  return { lista: lido?.dados ?? listaVazia(), etag: lido?.etag ?? null };
}

/**
 * Altera a lista com concorrência optimista: lê, aplica `alterar` e grava só se ninguém
 * tiver gravado entretanto (ETag). Em conflito, repete com a versão nova (até 6 vezes).
 */
export async function alterarLista<T>(slug: string, alterar: (lista: ListaConvidados) => T): Promise<{ lista: ListaConvidados; resultado: T }> {
  for (let tentativa = 0; tentativa < 6; tentativa++) {
    const { lista, etag } = await lerLista(slug);
    const resultado = alterar(lista);
    try {
      await armazenamento().escreverJSON(caminhoLista(slug), lista, etag ? { etag } : { criar: true });
      return { lista, resultado };
    } catch (e) {
      if (!(e instanceof ConflitoEscrita)) throw e;
      await new Promise((r) => setTimeout(r, 80 + Math.random() * 200));
    }
  }
  throw new Error("Muitas alterações ao mesmo tempo. Tente outra vez.");
}

/** Procura o convidado de um link pessoal. */
export async function procurarConvidado(slug: string, token: string): Promise<Convidado | null> {
  if (!TOKEN_VALIDO.test(token)) return null;
  const { lista } = await lerLista(slug);
  return lista.convidados.find((x) => x.token === token) ?? null;
}

/* ---------------- validação dos dados vindos da zona de gestão ---------------- */

const texto = (v: unknown, max: number, campo: string, obrigatorio = false) => {
  const s = typeof v === "string" ? v.replace(/\s+/g, " ").trim() : "";
  if (obrigatorio && !s) throw new ErroValidacao(`Falta ${campo}.`);
  if (s.length > max) throw new ErroValidacao(`${campo} tem mais de ${max} caracteres.`);
  return s || undefined;
};

const inteiro = (v: unknown, min: number, max: number, campo: string) => {
  const n = typeof v === "string" && v.trim() !== "" ? Number(v) : v;
  if (typeof n !== "number" || !Number.isInteger(n) || n < min || n > max) {
    throw new ErroValidacao(`${campo}: escreva um número entre ${min} e ${max}.`);
  }
  return n;
};

export interface DadosConvidado {
  nome?: unknown;
  pessoas?: unknown;
  telefone?: unknown;
  grupo?: unknown;
  notas?: unknown;
}

export function validarConvidado(d: DadosConvidado) {
  const telefone = normalizarTelefone(typeof d.telefone === "string" ? d.telefone : "");
  if (telefone === null) throw new ErroValidacao("Telefone inválido. Exemplo: 923 000 000 ou +244 923 000 000.");
  return {
    nome: texto(d.nome, 60, "o nome", true)!,
    pessoas: d.pessoas === undefined || d.pessoas === "" ? 1 : inteiro(d.pessoas, 1, 30, "Pessoas"),
    telefone,
    grupo: texto(d.grupo, 40, "O grupo"),
    notas: texto(d.notas, 200, "As notas"),
  };
}

export function novoConvidado(d: DadosConvidado, tokensExistentes: Set<string>): Convidado {
  const v = validarConvidado(d);
  let token = gerarToken();
  while (tokensExistentes.has(token)) token = gerarToken();
  const agora = new Date().toISOString();
  return { token, ...v, estado: "pendente", criadoEm: agora, actualizadoEm: agora };
}

export interface Alteracao extends DadosConvidado {
  estado?: unknown;
  pessoasConfirmadas?: unknown;
  enviado?: unknown;
}

export function aplicarAlteracao(c: Convidado, a: Alteracao) {
  if (a.nome !== undefined || a.pessoas !== undefined || a.telefone !== undefined || a.grupo !== undefined || a.notas !== undefined) {
    const v = validarConvidado({
      nome: a.nome ?? c.nome,
      pessoas: a.pessoas ?? c.pessoas,
      telefone: a.telefone ?? c.telefone ?? "",
      grupo: a.grupo ?? c.grupo ?? "",
      notas: a.notas ?? c.notas ?? "",
    });
    Object.assign(c, v);
    for (const k of ["telefone", "grupo", "notas"] as const) if (v[k] === undefined) delete c[k];
  }
  if (a.estado !== undefined) {
    if (!["pendente", "confirmado", "recusado"].includes(a.estado as string)) throw new ErroValidacao("Estado inválido.");
    c.estado = a.estado as EstadoConfirmacao;
    if (c.estado === "confirmado" && c.pessoasConfirmadas === undefined) c.pessoasConfirmadas = c.pessoas;
    if (c.estado !== "confirmado") delete c.pessoasConfirmadas;
  }
  if (a.pessoasConfirmadas !== undefined && c.estado === "confirmado") {
    c.pessoasConfirmadas = inteiro(a.pessoasConfirmadas, 0, 30, "Pessoas confirmadas");
  }
  if (a.enviado === true && !c.enviadoEm) c.enviadoEm = new Date().toISOString();
  if (a.enviado === false) delete c.enviadoEm;
  c.actualizadoEm = new Date().toISOString();
}

/**
 * Interpreta uma lista colada: um convidado por linha, «Nome; pessoas; telefone; grupo».
 * Separadores aceites: «;», tabulação, « - » e vírgula (se a linha não tiver «;» nem tabulação).
 */
export function interpretarLista(textoColado: string) {
  const linhas = textoColado.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  return linhas.slice(0, 500).map((linha, i) => {
    let partes: string[];
    if (/[;\t]/.test(linha)) partes = linha.split(/[;\t]/);
    else if (/ - /.test(linha)) partes = linha.split(/ - /);
    else partes = linha.split(",");
    partes = partes.map((p) => p.trim());
    const [nome, ...resto] = partes;
    let pessoas: string | undefined;
    let telefone: string | undefined;
    const grupo: string[] = [];
    for (const p of resto) {
      if (!p) continue;
      const n = /^(\d{1,2})\s*(pessoas?|pax|p)?$/i.exec(p);
      if (pessoas === undefined && n) pessoas = n[1];
      else if (telefone === undefined && /^[+\d][\d\s().-]{7,}$/.test(p)) telefone = p;
      else grupo.push(p);
    }
    try {
      const v = validarConvidado({ nome, pessoas, telefone, grupo: grupo.join(", ") });
      return { linha: i + 1, ok: true as const, convidado: v };
    } catch (e) {
      return { linha: i + 1, ok: false as const, texto: linha, erro: (e as Error).message };
    }
  });
}

/* ---------------- actividade (aberturas e toques em «Confirmar») ---------------- */

export type TipoActividade = "aberto" | "confirmar";

export async function registarActividade(slug: string, token: string, tipo: TipoActividade) {
  await armazenamento().criarMarcador(`${prefixoActividade(slug)}${token}/${tipo}-${Date.now()}`);
}

/** Agrega os marcadores por convidado, só a partir dos nomes (sem ler conteúdos). */
export async function lerActividade(slug: string): Promise<Record<string, Actividade>> {
  const itens = await armazenamento().listar(prefixoActividade(slug));
  const porToken: Record<string, Actividade> = {};
  for (const it of itens) {
    const [token, resto] = it.caminho.slice(prefixoActividade(slug).length).split("/");
    if (!token || !resto) continue;
    const m = /^(aberto|confirmar)-(\d{10,})/.exec(resto);
    if (!m) continue;
    const quando = new Date(Number(m[2])).toISOString();
    const a = (porToken[token] ??= { aberturas: 0 });
    if (m[1] === "aberto") {
      a.aberturas++;
      if (!a.abertoEm || quando < a.abertoEm) a.abertoEm = quando;
      if (!a.ultimaAberturaEm || quando > a.ultimaAberturaEm) a.ultimaAberturaEm = quando;
    } else if (!a.confirmarEm || quando > a.confirmarEm) a.confirmarEm = quando;
  }
  return porToken;
}
