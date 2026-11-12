"""Ayudas de rutas sin tocar el disco ni la red: rutas de red y nombres reservados de Windows.

``GetDriveTypeW`` solo consulta el tipo de unidad que ya conoce el sistema; no abre nada ni usa la red.
"""

from __future__ import annotations

import ctypes
import os
import sys

__all__ = ["NOMBRES_RESERVADOS", "es_ruta_de_red", "tiene_nombre_reservado"]

_DRIVE_REMOTE = 4  # valor de GetDriveTypeW para una unidad de red

NOMBRES_RESERVADOS = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)


def es_ruta_de_red(ruta: str) -> bool:
    """True si la ruta es UNC (``\\\\servidor\\...``) o está en una unidad de red (Windows).

    Si no se puede saber en una ruta con letra de unidad, se trata como de red (lo prudente).
    """
    if ruta.startswith(("\\\\", "//")):
        return True
    if sys.platform != "win32":
        return False
    unidad = os.path.splitdrive(ruta)[0]
    if not unidad:
        return False
    try:
        tipo = ctypes.WinDLL("kernel32").GetDriveTypeW(unidad + "\\")
    except (OSError, AttributeError):
        return True
    return tipo == _DRIVE_REMOTE


def tiene_nombre_reservado(ruta: str) -> bool:
    """True si algún componente es un nombre de dispositivo de Windows, con o sin extensión."""
    for parte in ruta.replace("/", "\\").split("\\"):
        base = parte.rstrip(" .").split(".")[0].rstrip(" ").upper()
        if base in NOMBRES_RESERVADOS:
            return True
    return False
