import { armazenamento, ConflitoEscrita } from "./armazenamento";
import { CsvInvalido, lerCsv, paraCsv } from "./csv";
import { TOKEN_VALIDO } from "./eventos";
import { gerarToken, normalizarTelefone, semAcentos } from "./texto";
import type { Actividade, Convidado, EstadoConfirmacao, ListaConvidados } from "./tipos";

const caminhoLista = (slug: string) => `eventos/${slug}/convidados.json`;
const prefixoActividade = (slug: string) => `eventos/${slug}/actividade/`;

const listaVazia = (): ListaConvidados => ({ versao: 1, convidados: [] });

/** Máximo de convidados por evento. */
export const MAXIMO_CONVIDADOS = 1000;

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
  const valor = typeof d.telefone === "string" ? d.telefone.trim() : "";
  const telefone = normalizarTelefone(valor);
  // o Excel mostra os números compridos como «2,44923E+11» e é isso que grava no CSV
  if (telefone === null && /^\d+([.,]\d+)?e\+?\d+$/i.test(valor)) {
    throw new ErroValidacao(`O Excel transformou o telefone em «${valor}». Escreva-o no Excel com espaços, como 923 000 000.`);
  }
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

/* ---------------- importação: colar uma lista ou um ficheiro CSV ---------------- */

/**
 * Uma linha importada: pronta a gravar (às vezes com um aviso), com um erro para corrigir,
 * ou posta de parte (`ignorada`: repete alguém ou é um exemplo do modelo).
 */
export type LinhaImportada =
  | { linha: number; texto: string; ok: true; convidado: ReturnType<typeof validarConvidado>; aviso?: string }
  | { linha: number; texto: string; ok: false; erro: string; ignorada?: true };

function importarLinha(linha: number, texto: string, d: DadosConvidado): LinhaImportada {
  try {
    return { linha, texto, ok: true, convidado: validarConvidado(d) };
  } catch (e) {
    if (!(e instanceof ErroValidacao)) throw e;
    return { linha, texto, ok: false, erro: e.message };
  }
}

/** «3», «3 pessoas», «3 pax». */
const PESSOAS = /^(\d{1,2})\s*(pessoas?|pax|p)?$/i;

/** Reconhece as partes pelo conteúdo: a primeira é o nome, depois o número de pessoas e o telefone; o resto é o grupo. */
function porConteudo(partes: string[]): DadosConvidado {
  const [nome, ...resto] = partes.map((p) => p.trim());
  let pessoas: string | undefined;
  let telefone: string | undefined;
  const grupo: string[] = [];
  for (const p of resto) {
    if (!p) continue;
    const n = PESSOAS.exec(p);
    if (pessoas === undefined && n) pessoas = n[1];
    else if (telefone === undefined && /^[+\d][\d\s().-]{7,}$/.test(p)) telefone = p;
    else grupo.push(p);
  }
  return { nome, pessoas, telefone, grupo: grupo.join(", ") };
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
    return importarLinha(i + 1, linha, porConteudo(partes));
  });
}

/**
 * Colunas do modelo CSV, pela ordem. Na importação, cada coluna é reconhecida pelo título (sem acentos,
 * maiúsculas nem o que está entre parênteses): o do modelo, um dos `outros` ou, se não houver, um que
 * tenha uma das `raizes` («Nome do convidado», «Telefone do convidado»…).
 */
const COLUNAS = [
  { campo: "nome", titulo: "Nome no convite", outros: ["nome", "nomes", "convidado", "convidados", "nome no envelope"], raizes: ["nome"] },
  { campo: "pessoas", titulo: "Pessoas", outros: ["pessoa", "n de pessoas", "numero de pessoas", "quantidade", "lugares", "pax"], raizes: ["pessoa"] },
  { campo: "telefone", titulo: "Telefone (WhatsApp)", outros: ["telemovel", "whatsapp", "contacto", "contato", "numero", "celular", "tel", "tlm"], raizes: ["telefone", "telemovel", "whatsapp", "contacto"] },
  { campo: "grupo", titulo: "Grupo", outros: ["etiqueta", "categoria"], raizes: ["grupo", "etiqueta"] },
  { campo: "notas", titulo: "Notas (só para a família)", outros: ["nota", "observacoes", "observacao", "obs"], raizes: ["nota", "observ"] },
] as const;
type Campo = (typeof COLUNAS)[number]["campo"];

/** Exemplos do modelo, com telefones fictícios. Se ficarem no ficheiro, a importação põe-nos de parte. */
const EXEMPLOS_MODELO = [
  { nome: "Sr. Carlos Neto e Família", pessoas: 3, telefone: "923 000 000", grupo: "Família do pai", notas: "Mesa 4" },
  { nome: "Ana e Rui Mendes", pessoas: 2, telefone: "912 000 000", grupo: "Amigos da escola", notas: "" },
];
const EXEMPLOS = EXEMPLOS_MODELO.map((e) => `${semAcentos(e.nome)}|${normalizarTelefone(e.telefone)}`);

/** Modelo para preencher no Excel: os títulos das colunas e os exemplos, em CSV como a exportação («;» e BOM). */
export function modeloCsv() {
  return paraCsv([COLUNAS.map((c) => c.titulo), ...EXEMPLOS_MODELO.map((e) => [e.nome, e.pessoas, e.telefone, e.grupo, e.notas])]);
}

const normalizarTitulo = (s: string) => semAcentos(s).replace(/\(.*?\)/g, " ").replace(/[^a-z0-9]+/g, " ").trim();

/** Em que coluna está cada campo, a partir dos títulos. `exactos`: quantos títulos foram reconhecidos sem as raízes. */
function lerTitulos(celulas: string[]) {
  const titulos = celulas.map(normalizarTitulo);
  const colunas: Partial<Record<Campo, number>> = {};
  const livre = (i: number) => !Object.values(colunas).includes(i);
  for (const c of COLUNAS) {
    const aceites: readonly string[] = [normalizarTitulo(c.titulo), ...c.outros];
    const i = titulos.findIndex((t, i) => livre(i) && aceites.includes(t));
    if (i >= 0) colunas[c.campo] = i;
  }
  const exactos = Object.keys(colunas).length;
  for (const c of COLUNAS) {
    if (colunas[c.campo] !== undefined) continue;
    const i = titulos.findIndex((t, i) => livre(i) && t.split(" ").some((p) => c.raizes.some((r) => p.startsWith(r))));
    if (i >= 0) colunas[c.campo] = i;
  }
  return { colunas, exactos };
}

/**
 * Interpreta um ficheiro CSV (do modelo, do Excel, do Google Sheets…). Com a linha dos títulos, as colunas
 * vão pelos títulos, por qualquer ordem, e as outras são ignoradas. Sem ela, cada linha é lida como em
 * «Colar lista». As linhas vazias são saltadas; `linha` é o número da linha no Excel.
 */
export function interpretarCsv(texto: string) {
  if (texto.includes("\0")) throw new ErroValidacao("Este ficheiro não parece uma lista de convidados em CSV.");
  let registos: string[][];
  try {
    registos = lerCsv(texto);
  } catch (e) {
    if (e instanceof CsvInvalido) throw new ErroValidacao(e.message);
    throw e;
  }
  const vazio = (r: string[]) => r.every((c) => !c.trim());
  const primeira = registos.findIndex((r) => !vazio(r));
  if (primeira < 0) throw new ErroValidacao("O ficheiro está vazio.");
  const { colunas, exactos } = lerTitulos(registos[primeira]);
  const comTitulos = colunas.nome !== undefined;
  if (!comTitulos && exactos >= 2) {
    throw new ErroValidacao("Falta a coluna «Nome no convite». Use o modelo: a primeira linha tem os títulos das colunas.");
  }
  const linhas: LinhaImportada[] = [];
  for (let i = comTitulos ? primeira + 1 : primeira; i < registos.length; i++) {
    const r = registos[i].map((c) => c.trim());
    if (vazio(r)) continue;
    if (linhas.length === MAXIMO_CONVIDADOS) {
      throw new ErroValidacao(`O ficheiro tem mais de ${MAXIMO_CONVIDADOS} convidados, o máximo de uma lista.`);
    }
    const celula = (campo: Campo) => {
      const coluna = colunas[campo];
      return coluna === undefined ? undefined : r[coluna];
    };
    const pessoas = celula("pessoas") ?? "";
    const d = comTitulos
      ? { nome: celula("nome"), pessoas: PESSOAS.exec(pessoas)?.[1] ?? pessoas, telefone: celula("telefone"), grupo: celula("grupo"), notas: celula("notas") }
      : porConteudo(r);
    while (!r[r.length - 1]) r.pop();
    linhas.push(importarLinha(i + 1, r.join("; "), d));
  }
  if (!linhas.length) throw new ErroValidacao("O ficheiro só tem a linha dos títulos. Escreva um convidado por linha, a partir da linha 2.");
  return { linhas, semTitulos: !comTitulos };
}

/**
 * Põe de parte as linhas com o nome (sem contar acentos nem maiúsculas) de alguém da lista ou de uma linha
 * anterior, e os exemplos do modelo. Um telefone repetido só fica assinalado: pode ser o contacto de vários convites.
 */
export function marcarRepetidas(linhas: LinhaImportada[], existentes: Convidado[]): LinhaImportada[] {
  const nomes = new Map(existentes.map((c) => [semAcentos(c.nome), "Já está na lista."]));
  const telefones = new Map<string, string>(existentes.flatMap((c) => (c.telefone ? [[c.telefone, `«${c.nome}»`]] : [])));
  return linhas.map((l) => {
    if (!l.ok) return l;
    const ignorar = (erro: string): LinhaImportada => ({ linha: l.linha, texto: l.texto, ok: false, erro, ignorada: true });
    const { nome, telefone } = l.convidado;
    const chave = semAcentos(nome);
    if (EXEMPLOS.includes(`${chave}|${telefone}`)) return ignorar("Exemplo do modelo: apague esta linha.");
    const repetido = nomes.get(chave);
    if (repetido) return ignorar(repetido);
    nomes.set(chave, `Repete a linha ${l.linha}.`);
    const mesmo = telefone && telefones.get(telefone);
    if (telefone && !mesmo) telefones.set(telefone, `a linha ${l.linha}`);
    return mesmo ? { ...l, aviso: `Mesmo telefone que ${mesmo}.` } : l;
  });
}

/* ---------------- resposta do convidado dentro do convite ---------------- */

export interface DadosResposta {
  estado?: unknown;
  pessoas?: unknown;
  mensagem?: unknown;
}

/**
 * Aplica a resposta dada no convite: vou (com as pessoas, até ao número do convite; por omissão, todas)
 * ou não vou, e uma mensagem opcional. Muda o estado, como se a família o marcasse, e guarda a resposta.
 */
export function aplicarResposta(c: Convidado, d: DadosResposta) {
  if (d.estado !== "confirmado" && d.estado !== "recusado") throw new ErroValidacao("Escolha se vai ou não.");
  const mensagem = texto(d.mensagem, 300, "A mensagem");
  const em = new Date().toISOString();
  if (d.estado === "confirmado") {
    const pessoas = d.pessoas === undefined ? c.pessoas : inteiro(d.pessoas, 1, c.pessoas, "Pessoas");
    c.pessoasConfirmadas = pessoas;
    c.resposta = { estado: d.estado, pessoas, ...(mensagem ? { mensagem } : {}), em };
  } else {
    delete c.pessoasConfirmadas;
    c.resposta = { estado: d.estado, ...(mensagem ? { mensagem } : {}), em };
  }
  c.estado = d.estado;
  c.actualizadoEm = em;
}

/** Limite de respostas por link pessoal e por hora (contra pedidos repetidos). */
export const RESPOSTAS_POR_HORA = 10;

/** Respostas deste convidado na última hora, pelos marcadores `resposta-…` (comum a todos os processos). */
export async function respostasRecentes(slug: string, token: string) {
  const desde = Date.now() - 3600_000;
  const itens = await armazenamento().listar(`${prefixoActividade(slug)}${token}/`);
  return itens.filter((it) => Number(/\/resposta-(\d{10,})-/.exec(it.caminho)?.[1] ?? 0) > desde).length;
}

/* ---------------- actividade (aberturas, toques em «Confirmar» e respostas) ---------------- */

export type TipoActividade = "aberto" | "confirmar" | "resposta";

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
