import crypto from "node:crypto";
import type { ConfiguracaoConvite } from "./tipos";

export const MESES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

export const MENSAGEM_ENVIO_PADRAO =
  "Olá, {convidado}! Temos a alegria de convidar para a festa dos 15 anos da {homenageado}, " +
  "no dia {dataCurta}, às {hora}. Abra aqui o seu convite: {link}";

/** 128 bits aleatórios em base64url (22 caracteres). */
export const gerarToken = () => crypto.randomBytes(16).toString("base64url");

export function dataCurta(c: ConfiguracaoConvite) {
  return `${c.data.dia} de ${MESES[c.data.mes - 1]}`;
}

export function dataLonga(c: ConfiguracaoConvite) {
  const dia = c.data.diaSemana.charAt(0).toUpperCase() + c.data.diaSemana.slice(1);
  return `${dia}, ${c.data.dia} de ${MESES[c.data.mes - 1]} de ${c.data.ano}`;
}

export const semAcentos = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

/**
 * Fim do prazo de confirmação: o fim do dia de `confirmacao.ate` («1 de Maio de 2027») em Luanda
 * (UTC+1, sem hora de Verão). É o prazo que o convidado lê no convite. Se o texto não tiver este
 * formato, ou for depois da festa, o prazo é o início da festa.
 */
export function fimDoPrazo(c: ConfiguracaoConvite): Date {
  const inicio = new Date(c.data.iso);
  const m = /^\s*(\d{1,2})\s+de\s+(\S+)\s+de\s+(\d{4})\s*$/i.exec(c.confirmacao.ate);
  const mes = m ? MESES.findIndex((x) => semAcentos(x) === semAcentos(m[2])) : -1;
  if (!m || mes < 0) return inicio;
  const [dia, ano] = [Number(m[1]), Number(m[3])];
  if (new Date(Date.UTC(ano, mes, dia)).getUTCDate() !== dia) return inicio; // ex.: 31 de Abril
  const fim = new Date(Date.UTC(ano, mes, dia + 1) - 3600_000); // 00h00 do dia seguinte, em Luanda
  return fim < inicio ? fim : inicio;
}

/** Substitui todos os {marcadores} conhecidos; os desconhecidos ficam como estão. */
export function preencher(modelo: string, valores: Record<string, string>) {
  return modelo.replace(/\{(\w+)\}/g, (inteiro, chave: string) => (chave in valores ? valores[chave] : inteiro));
}

export const pessoasTexto = (n: number) => `${n} ${n === 1 ? "pessoa" : "pessoas"}`;

export function escaparHtml(s: string) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);
}

/**
 * Normaliza um número para o formato internacional só com dígitos (o que o wa.me espera).
 * «923 000 000» → «244923000000». Devolve undefined se vazio e null se inválido.
 */
export function normalizarTelefone(valor?: string | null): string | undefined | null {
  if (!valor || !valor.trim()) return undefined;
  let d = valor.trim();
  if (d.startsWith("+")) d = d.slice(1);
  d = d.replace(/[\s().-]/g, "");
  if (d.startsWith("00")) d = d.slice(2);
  if (!/^\d+$/.test(d)) return null;
  if (/^9\d{8}$/.test(d)) d = "244" + d; // telemóvel angolano sem indicativo
  if (d.length < 9 || d.length > 15) return null;
  return d;
}

export function telefoneLegivel(d?: string) {
  if (!d) return "";
  if (/^2449\d{8}$/.test(d)) return `+244 ${d.slice(3, 6)} ${d.slice(6, 9)} ${d.slice(9)}`;
  return "+" + d;
}
