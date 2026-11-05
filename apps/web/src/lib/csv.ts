/** CSV para o Excel em português: separador «;», BOM UTF-8 e aspas quando preciso. */
export function paraCsv(linhas: (string | number | undefined)[][]) {
  const celula = (v: string | number | undefined) => {
    const s = v === undefined ? "" : String(v);
    // evita fórmulas injectadas (=, +, -, @) ao abrir no Excel
    const seguro = /^[=+\-@]/.test(s) && !/^[-+]?\d/.test(s) ? "'" + s : s;
    return /[;"\n\r]/.test(seguro) ? `"${seguro.replace(/"/g, '""')}"` : seguro;
  };
  return "\uFEFF" + linhas.map((l) => l.map(celula).join(";")).join("\r\n") + "\r\n";
}
