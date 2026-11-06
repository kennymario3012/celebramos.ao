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
