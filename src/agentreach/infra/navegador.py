"""Abre un archivo local en el navegador (Historia 21). Es la ÚNICA vía del producto que le pide algo al sistema.

Solo se llama después de terminar la revisión, con permiso de la persona (``--abrir`` o un «s» a la pregunta) y solo con la ruta de
un archivo local: ``file://``, sin red. Nunca durante el análisis.
"""

from __future__ import annotations

import os
import webbrowser
from pathlib import Path

__all__ = ["abrir"]


def abrir(ruta: str) -> bool:
    """``True`` si el sistema aceptó abrirlo. Un archivo que no existe no se abre."""
    if not os.path.isfile(ruta):
        return False
    try:
        return bool(webbrowser.open(Path(ruta).resolve().as_uri()))
    except (webbrowser.Error, OSError):
        return False
