/** Ficheiro de calendário (RFC 5545), igual ao de prototipo/construir.py (docs/04 §6). */
import type { ConfiguracaoConvite } from "@/lib/tipos";

const escapar = (s: string) => s.replace(/\\/g, "\\\\").replace(/;/g, "\;").replace(/,/g, "\\,").replace(/\r?\n/g, "\\n");

/** Linhas com mais de 75 octetos são dobradas (RFC 5545 §3.1). */
function dobrar(linha: string) {
  const partes: string[] = [];
  let actual = "";
  let octetos = 0;
  for (const ch of linha) {
    const n = Buffer.byteLength(ch);
    if (octetos + n > 73) {
      partes.push(actual);
      actual = " " + ch;
      octetos = 1 + n;
    } else {
      actual += ch;
      octetos += n;
    }
  }
  partes.push(actual);
  return partes.join("\r\n");
}

export function gerarIcs(cfg: ConfiguracaoConvite, slug: string, sequencia = 0) {
  const c = cfg.calendario;
  const agora = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
  const linhas = [
    "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//celebramos.ao//convite//PT", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
    "BEGIN:VEVENT",
    `UID:${slug}@celebramos.ao`,
    `SEQUENCE:${sequencia}`,
    `DTSTAMP:${agora}`,
    `DTSTART:${c.inicioUTC}`,
    `DTEND:${c.fimUTC}`,
    `SUMMARY:${escapar(c.titulo)}`,
    `LOCATION:${escapar(c.local)}`,
    `DESCRIPTION:${escapar(c.detalhes)}`,
    "BEGIN:VALARM", "TRIGGER:-P1D", "ACTION:DISPLAY", `DESCRIPTION:${escapar(c.titulo)}`, "END:VALARM",
    "END:VEVENT", "END:VCALENDAR",
  ];
  return linhas.map(dobrar).join("\r\n") + "\r\n";
}
