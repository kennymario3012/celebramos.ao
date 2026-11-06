/** CSV para o Excel em português: separador «;», BOM UTF-8 e aspas quando preciso. */
export function paraCsv(linhas: (string | number | undefined)[][]) {
  const celula = (v: string | number | undefined) => {
    const s = v === undefined ? "" : String(v);
    // evita fórmulas injectadas (=, +, -, @) ao abrir no Excel
    const seguro = /^[=+\-@]/.test(s) && !/^[-+]?\d/.test(s) ? "'" + s : s;
    return /[;"\n\r]/.test(seguro) ? `"${seguro.replace(/"/g, '""')}"` : seguro;
  };
  return "﻿" + linhas.map((l) => l.map(celula).join(";")).join("\r\n") + "\r\n";
}

export class CsvInvalido extends Error {}

/** O separador mais frequente, fora das aspas, na primeira linha com texto. Em caso de empate: «;», «,», tabulação. */
function separadorDe(texto: string) {
  const zero = () => ({ ";": 0, ",": 0, "\t": 0 }) as Record<string, number>;
  let conta = zero();
  let aspas = false;
  let comTexto = false;
  for (const c of texto) {
    if (c === '"') {
      aspas = !aspas;
      comTexto = true;
    } else if (aspas) continue;
    else if (c === "\n" || c === "\r") {
      if (comTexto) break;
      conta = zero(); // linha sem texto (por exemplo «;;;;»): não conta
    } else if (c in conta) conta[c]++;
    else if (c.trim()) comTexto = true;
  }
  return [";", ",", "\t"].reduce((a, b) => (conta[b] > conta[a] ? b : a));
}

/**
 * Lê um CSV como o Excel, o Google Sheets ou o Numbers o gravam: separador «;», «,» ou tabulação,
 * BOM, campos entre aspas (com «""» para as aspas e quebras de linha lá dentro) e fins de linha
 * CRLF, LF ou CR. Devolve as linhas pela ordem do ficheiro, incluindo as vazias: a posição de
 * cada uma mais 1 é o número da linha no Excel.
 */
export function lerCsv(texto: string): string[][] {
  if (texto.startsWith("﻿")) texto = texto.slice(1);
  const sep = separadorDe(texto);
  const linhas: string[][] = [];
  let linha: string[] = [];
  let campo = "";
  let aspas = false;
  let inicioAspas = 0;
  for (let i = 0; i < texto.length; i++) {
    const c = texto[i];
    if (aspas) {
      if (c !== '"') campo += c;
      else if (texto[i + 1] === '"') {
        campo += '"';
        i++;
      } else aspas = false;
    } else if (c === '"' && !campo) {
      aspas = true;
      inicioAspas = linhas.length + 1;
    } else if (c === sep) {
      linha.push(campo);
      campo = "";
    } else if (c === "\n" || c === "\r") {
      if (c === "\r" && texto[i + 1] === "\n") i++;
      linha.push(campo);
      linhas.push(linha);
      linha = [];
      campo = "";
    } else campo += c;
  }
  if (aspas) throw new CsvInvalido(`Há umas aspas por fechar na linha ${inicioAspas}. Corrija-a no Excel e guarde o ficheiro outra vez.`);
  if (campo || linha.length) {
    linha.push(campo);
    linhas.push(linha);
  }
  return linhas;
}
