"""Dónde se guarda el reporte HTML y la respuesta recordada (Historia 21).

Es el ÚNICO lugar, además de ``--salida``, donde AgentReach escribe: la carpeta ``AgentReach-reportes`` dentro de la carpeta
personal (con el reporte HTML y ``preferencias.json``). Nunca dentro de la carpeta analizada y nunca a través de un enlace.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime

__all__ = ["CARPETA", "ResultadoReporte", "carpeta_de_reportes", "dentro", "escribir_reporte", "guardar_preferencia", "leer_preferencia"]

CARPETA = "AgentReach-reportes"
PREFERENCIAS = "preferencias.json"
_CLAVE = "abrir_en_navegador"


@dataclass(frozen=True, slots=True)
class ResultadoReporte:
    ruta: str | None  # el archivo creado, o None si no se creó
    motivo: str = ""  # por qué no: "sin_home", "dentro", "enlace" o "escritura"


def carpeta_de_reportes(home: str) -> str:
    return os.path.join(home, CARPETA)


def dentro(ruta: str, carpeta: str) -> bool:
    """¿Escribir en ``ruta`` tocaría ``carpeta``? Ante la duda, sí (se rechaza)."""
    try:
        destino = os.path.abspath(ruta)
        existente = os.path.dirname(destino)
        while existente and not os.path.exists(existente) and existente != os.path.dirname(existente):
            existente = os.path.dirname(existente)  # el primer ancestro que existe: ahí se resuelven los enlaces
        real = os.path.join(os.path.realpath(existente), os.path.basename(destino))
        b = os.path.normcase(os.path.realpath(carpeta))
        if os.path.splitdrive(real)[0].lower() != os.path.splitdrive(b)[0].lower():
            return False  # en otra unidad de disco (C: y D:) no puede estar dentro de la carpeta auditada
        if os.path.commonpath([os.path.normcase(real), b]) == b:
            return True
        # un archivo que ya existe y tiene más de un enlace duro podría ser el mismo de la carpeta auditada
        return os.path.lexists(destino) and (os.path.islink(destino) or (os.path.isfile(destino) and os.stat(destino).st_nlink > 1))
    except (ValueError, OSError):
        return True


def _es_enlace(ruta: str) -> bool:
    try:
        return os.path.islink(ruta) or bool(getattr(os.lstat(ruta), "st_file_attributes", 0) & 0x400)  # symlink o junction
    except OSError:
        return True


def _nombre_seguro(auditada: str) -> str:
    base = os.path.basename(os.path.normpath(auditada)) or "raiz"
    limpio = re.sub(r"[^A-Za-z0-9._-]+", "-", base).strip("-.")[:40]
    return limpio or "carpeta"


def _carpeta_usable(home: str, auditada: str) -> tuple[str | None, str]:
    if not home or not os.path.isabs(home):
        return None, "sin_home"
    carpeta = carpeta_de_reportes(home)
    if os.path.lexists(carpeta) and _es_enlace(carpeta):
        return None, "enlace"  # primero el enlace: es el motivo más concreto y el que se le explica a la persona
    if dentro(carpeta, auditada) or dentro(auditada, carpeta):
        return None, "dentro"
    return carpeta, ""


def escribir_reporte(html: str, home: str, auditada: str, momento: datetime) -> ResultadoReporte:
    """Guarda ``html`` en ``<home>/AgentReach-reportes/`` con un nombre nuevo (nunca pisa un reporte anterior)."""
    carpeta, motivo = _carpeta_usable(home, auditada)
    if carpeta is None:
        return ResultadoReporte(None, motivo)
    try:
        os.makedirs(carpeta, exist_ok=True)
        base = f"agentreach-{momento:%Y%m%d-%H%M%S}-{_nombre_seguro(auditada)}"
        for n in range(1, 100):
            ruta = os.path.join(carpeta, base + ("" if n == 1 else f"-{n}") + ".html")
            try:
                with open(ruta, "x", encoding="utf-8", newline="\n") as f:  # "x": falla si ya existe, no se pisa nada
                    f.write(html)
                return ResultadoReporte(ruta)
            except FileExistsError:
                continue
    except OSError:
        pass
    return ResultadoReporte(None, "escritura")


def leer_preferencia(home: str, auditada: str) -> bool | None:
    """La respuesta recordada a «¿abrir en el navegador?», o ``None`` si no hay una (o no se entiende)."""
    carpeta, _ = _carpeta_usable(home, auditada)
    if carpeta is None:
        return None
    try:
        with open(os.path.join(carpeta, PREFERENCIAS), encoding="utf-8") as f:
            valor = json.load(f).get(_CLAVE)
    except (OSError, ValueError, AttributeError):
        return None
    return valor if isinstance(valor, bool) else None


def guardar_preferencia(home: str, auditada: str, abrir: bool) -> str | None:
    """Recuerda la respuesta. Devuelve la ruta del archivo, o ``None`` si no se pudo."""
    carpeta, _ = _carpeta_usable(home, auditada)
    if carpeta is None:
        return None
    try:
        os.makedirs(carpeta, exist_ok=True)
        ruta = os.path.join(carpeta, PREFERENCIAS)
        if os.path.lexists(ruta) and (os.path.islink(ruta) or os.stat(ruta).st_nlink > 1):
            return None  # un enlace (simbólico o duro) podría llevar la escritura a otro archivo: no se escribe
        with open(ruta, "w", encoding="utf-8", newline="\n") as f:
            json.dump({_CLAVE: abrir}, f)
            f.write("\n")
        return ruta
    except OSError:
        return None
