"""Constrói um convite (HTML estático) a partir de um ficheiro de configuração.

Uso:
    python3 construir.py configs/exemplo-bela-principe.json            # -> exemplos/<id>/
    python3 construir.py configs/exemplo-bela-principe.json /tmp/saida  # pasta à escolha

A saída é autónoma: index.html + img/ (imagens do tema) + calendario.ics (se `calendario.ics` estiver definido).
Abrir com um servidor local, p. ex.:  python3 -m http.server -d exemplos/exemplo-bela-principe 8080
"""
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def ics_escape(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def dobrar(linha):
    """Linhas iCalendar com mais de 75 octetos são dobradas (RFC 5545 §3.1)."""
    out, cur = [], b""
    for ch in linha:
        b = ch.encode("utf-8")
        if len(cur) + len(b) > 73:
            out.append(cur.decode("utf-8"))
            cur = b" " + b
        else:
            cur += b
    out.append(cur.decode("utf-8"))
    return "\r\n".join(out)


def gerar_ics(cfg):
    cal = cfg["calendario"]
    agora = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    linhas = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//celebramos.ao//convite//PT", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{cfg['id']}@celebramos.ao",
        f"DTSTAMP:{agora}",
        f"DTSTART:{cal['inicioUTC']}",
        f"DTEND:{cal['fimUTC']}",
        f"SUMMARY:{ics_escape(cal['titulo'])}",
        f"LOCATION:{ics_escape(cal['local'])}",
        f"DESCRIPTION:{ics_escape(cal['detalhes'])}",
        "BEGIN:VALARM", "TRIGGER:-P1D", "ACTION:DISPLAY", f"DESCRIPTION:{ics_escape(cal['titulo'])}", "END:VALARM",
        "END:VEVENT", "END:VCALENDAR",
    ]
    return ("\r\n".join(dobrar(l) for l in linhas) + "\r\n").encode("utf-8")


def construir(cfg_path, out=None):
    cfg = json.loads(Path(cfg_path).read_text())
    out = Path(out) if out else ROOT / "exemplos" / cfg["id"]
    (out / "img").mkdir(parents=True, exist_ok=True)

    html = (ROOT / "template.html").read_text()
    # telemóveis antigos sem unidades de contentor (cqi): cada declaração ganha antes uma alternativa em vw
    html = re.sub(r'([a-z-]+):([^;{}"<>]*?\d(?:\.\d+)?cqi[^;{}"<>]*)',
                  lambda m: f"{m.group(1)}:{m.group(2).replace('cqi', 'vw')};{m.group(1)}:{m.group(2)}", html)
    icones = json.loads((ROOT / "icones.json").read_text())
    html = (html.replace("__CONFIG__", json.dumps(cfg, ensure_ascii=False, indent=1))
                .replace("__ICONS__", json.dumps(icones, ensure_ascii=False))
                .replace("__TITLE__", cfg["tituloPagina"]))
    (out / "index.html").write_text(html)

    tema = ROOT / "temas" / cfg["tema"]["id"]
    for f in sorted(tema.glob("*.webp")):
        shutil.copy2(f, out / "img" / f.name)

    if cfg.get("calendario", {}).get("ics"):
        (out / cfg["calendario"]["ics"]).write_bytes(gerar_ics(cfg))

    print(f"construído: {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}  ({len(html) // 1024} KB)")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    construir(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
