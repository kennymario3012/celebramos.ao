"""Valida configurações de convite contra o esquema (docs/esquemas/convite.schema.json) e regras extra.

Uso:
    python3 testes/validar_config.py                      # todas as configs/*.json
    python3 testes/validar_config.py configs/meu.json     # ficheiros indicados

Termina com código ≠ 0 se alguma configuração for inválida.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
ESQUEMA = ROOT.parent / "docs" / "esquemas" / "convite.schema.json"
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]


def regras_extra(cfg):
    """Coerência entre campos que o esquema JSON não consegue exprimir."""
    erros = []
    d = cfg["data"]
    try:
        inicio = datetime.fromisoformat(d["iso"].replace("Z", "+00:00"))
    except ValueError:
        return [f"data.iso inválida: {d['iso']}"]
    if (inicio.day, inicio.month, inicio.year) != (d["dia"], d["mes"], d["ano"]):
        erros.append("data.dia/mes/ano não coincidem com data.iso")
    if DIAS[inicio.weekday()] != d["diaSemana"]:
        erros.append(f"data.diaSemana devia ser «{DIAS[inicio.weekday()]}»")
    if f"{inicio.hour}h{inicio.minute:02d}" != d["hora"].lstrip("0") and f"{inicio.hour:02d}h{inicio.minute:02d}" != d["hora"]:
        erros.append("data.hora não coincide com data.iso")
    cal = cfg["calendario"]
    utc = inicio.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if cal["inicioUTC"] != utc:
        erros.append(f"calendario.inicioUTC devia ser {utc}")
    if cal["fimUTC"] <= cal["inicioUTC"]:
        erros.append("calendario.fimUTC tem de ser depois do início")
    seccoes = cfg.get("seccoes") or []
    for s in (cfg.get("decoracao") or {}):
        if seccoes and s not in seccoes:
            erros.append(f"decoracao.{s}: secção não incluída em `seccoes`")
    if "galeria" in seccoes and not cfg["galeria"]["fotos"]:
        erros.append("secção «galeria» na ordem mas sem fotos")
    if "presentes" in seccoes and not cfg.get("presentes"):
        erros.append("secção «presentes» na ordem mas `presentes` está vazio")
    if cfg.get("demonstracao") and cfg.get("convidadoDemonstracao") not in cfg["convidados"]:
        erros.append("demonstracao ligada mas convidadoDemonstracao não existe em `convidados`")
    for m in re.findall(r"\{(\w+)\}", cfg["confirmacao"]["mensagem"]):
        if m not in ("debutante", "dataCurta", "convidado", "pessoas"):
            erros.append(f"confirmacao.mensagem: marcador desconhecido {{{m}}}")
    n = sum(len(col) for col in cfg["pais"])
    if n == 1 and cfg["convidam"].startswith("Têm"):
        erros.append("um só anfitrião: usar «Tem a honra de convidar»")
    if n > 1 and cfg["convidam"].startswith("Tem "):
        erros.append("vários anfitriões: usar «Têm a honra de convidar»")
    return erros


def validar(caminho, validador):
    cfg = json.loads(Path(caminho).read_text())
    erros = [f"{'/'.join(map(str, e.absolute_path)) or '(raiz)'}: {e.message}" for e in validador.iter_errors(cfg)]
    if not erros:
        erros = regras_extra(cfg)
    print(("OK      " if not erros else "INVÁLIDA") + f"  {caminho}")
    for e in erros:
        print("   -", e)
    return not erros


def main(ficheiros):
    validador = Draft202012Validator(json.loads(ESQUEMA.read_text()))
    ficheiros = ficheiros or sorted(str(p) for p in (ROOT / "configs").glob("*.json"))
    ok = [validar(f, validador) for f in ficheiros]
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
