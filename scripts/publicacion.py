#!/usr/bin/env python3
"""Registro de publicacion por video (solo libreria estandar).

Cada carpeta DatoPixel/<tema> - dd-mm-aaaa/ tiene un `publicacion.md` con una tabla
(YouTube, TikTok, Instagram) y un estado por red: pendiente | programado | publicado.

Comandos:
  indice            regenera docs/estado-publicacion.md con el estado de todos los videos
  marcar            lista las carpetas publicadas en las 3 redes que aun no tienen el prefijo
  marcar --aplicar  les agrega el prefijo "SUBIDO - " al nombre de la carpeta

IMPORTANTE: no renombrar una carpeta mientras queden posts programados que lean su video
por URL (raw de GitHub); por eso solo se marca cuando las 3 redes estan en "publicado".
"""
import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "DatoPixel"
INDICE = Path(__file__).resolve().parent.parent / "docs" / "estado-publicacion.md"
PREFIJO = "SUBIDO - "
REDES = ("YouTube", "TikTok", "Instagram")
ESTADOS = ("pendiente", "programado", "publicado")


def leer_estados(carpeta: Path) -> dict:
    archivo = carpeta / "publicacion.md"
    if not archivo.exists():
        return {}
    estados = {}
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if len(celdas) >= 3 and celdas[0] in REDES:
            estado = celdas[1].lower()
            if estado not in ESTADOS:
                raise SystemExit(f"{archivo}: estado invalido '{celdas[1]}' en {celdas[0]}")
            estados[celdas[0]] = (estado, celdas[2])
    return estados


def carpetas() -> list:
    return sorted((p for p in RAIZ.iterdir() if p.is_dir()), key=lambda p: p.name.removeprefix(PREFIJO))


def resumen(estados: dict) -> str:
    if not estados:
        return "sin registro"
    valores = [estados.get(r, ("pendiente", ""))[0] for r in REDES]
    if all(v == "publicado" for v in valores):
        return "publicado en las 3"
    if all(v in ("programado", "publicado") for v in valores):
        return "programado"
    return "incompleto"


def cmd_indice() -> None:
    filas = ["| Video | Estado | YouTube | TikTok | Instagram | Salida (Santiago) |", "|---|---|---|---|---|---|"]
    for c in carpetas():
        e = leer_estados(c)
        fecha = next((e[r][1] for r in REDES if r in e and e[r][1]), "")
        celdas = [e.get(r, ("pendiente", ""))[0] for r in REDES]
        filas.append(f"| {c.name} | {resumen(e)} | {celdas[0]} | {celdas[1]} | {celdas[2]} | {fecha} |")
    INDICE.write_text(
        "# Estado de publicación por video\n\nGenerado con `python3 scripts/publicacion.py indice`. "
        "El detalle de cada video está en `DatoPixel/<carpeta>/publicacion.md`.\n\n" + "\n".join(filas) + "\n",
        encoding="utf-8")
    print(f"{INDICE} actualizado ({len(filas) - 2} videos)")


def cmd_marcar(aplicar: bool) -> None:
    for c in carpetas():
        if c.name.startswith(PREFIJO):
            continue
        if resumen(leer_estados(c)) == "publicado en las 3":
            destino = c.with_name(PREFIJO + c.name)
            print(("renombrando " if aplicar else "se marcaria ") + f"{c.name} -> {destino.name}")
            if aplicar:
                c.rename(destino)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("indice")
    m = sub.add_parser("marcar")
    m.add_argument("--aplicar", action="store_true")
    a = p.parse_args()
    cmd_indice() if a.cmd == "indice" else cmd_marcar(a.aplicar)
    return 0


if __name__ == "__main__":
    sys.exit(main())
