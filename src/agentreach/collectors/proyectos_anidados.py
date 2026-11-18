"""Carpetas dentro de la revisada que parecen proyectos aparte (Historia 44).

Sobre los archivos que el recorrido ya vio: no recorre ni lee contenido (resuelve la raíz una vez) y no muestra nombres ni rutas.
Solo cuenta. Un nivel interno cuenta si tiene su propio punto de partida de un agente o de un repositorio.
Lo que cuelga de una carpeta de dependencias (``.venv``, ``venv``, ``vendor``, ``site-packages``, ``dist``, ``target``) tampoco cuenta.
Los manifiestos (``package.json``, ``pyproject.toml``…) no son señal: un monorepo es un solo proyecto.
"""

from __future__ import annotations

import os
from collections.abc import Iterable

from agentreach.collectors.enlaces import PREFIJO_NT, _norm
from agentreach.contracts import Metadatos

UMBRAL_PROYECTOS_ANIDADOS = 2  # con 2 o más carpetas internas con punto de partida, el reporte avisa

_N = os.path.normcase
_CARPETAS_DE_HERRAMIENTA = frozenset(_N(n) for n in (".git", "node_modules", ".claude", ".opencode"))
# Carpetas de dependencias o de salida de compilación: lo que traen dentro no es un proyecto aparte. En cualquier nivel y
# sin distinguir mayúsculas (se compara en minúscula en todos los sistemas).
_CARPETAS_DE_DEPENDENCIAS = frozenset({".venv", "venv", "vendor", "site-packages", "dist", "target"})
# Archivo dentro de una carpeta de herramienta: la carpeta del proyecto es la que contiene a esa carpeta.
_DENTRO_DE_HERRAMIENTA = {
    _N(".git"): frozenset({_N("config")}),
    _N(".claude"): frozenset({_N("settings.json"), _N("settings.local.json")}),
    _N(".opencode"): frozenset({_N("opencode.json")}),
}
# Archivo que marca por sí solo la carpeta que lo contiene.
_EN_LA_CARPETA = frozenset(_N(n) for n in ("CLAUDE.md", "opencode.json", "opencode.jsonc"))
_NOMBRES_QUE_IMPORTAN = _EN_LA_CARPETA | {n for grupo in _DENTRO_DE_HERRAMIENTA.values() for n in grupo}


def _relativa(ruta: str, raiz_cruda: str, raiz: str) -> str | None:
    """La ruta relativa a la raíz, o ``None`` si no cuelga de ella. Primero por texto; si no, con la forma canónica."""
    limpia = _N(ruta.removeprefix(PREFIJO_NT))
    for base in (raiz_cruda, raiz):
        prefijo = base.rstrip(os.sep) + os.sep
        if limpia.startswith(prefijo):
            return limpia[len(prefijo):]
    canonica = _norm(ruta)
    prefijo = raiz.rstrip(os.sep) + os.sep
    return canonica[len(prefijo):] if canonica.startswith(prefijo) else None


def contar_proyectos_anidados(archivos: Iterable[Metadatos], raiz: str) -> int:
    """Cuántas carpetas DENTRO de ``raiz`` (nunca ella misma) tienen su propio punto de partida."""
    raiz_cruda = _N(str(raiz).removeprefix(PREFIJO_NT))
    raiz_canonica = _norm(str(raiz))
    carpetas: set[tuple[str, ...]] = set()
    for archivo in archivos:
        ruta = str(archivo.ruta)
        nombre = _N(os.path.basename(ruta))
        if nombre not in _NOMBRES_QUE_IMPORTAN:
            continue
        relativa = _relativa(ruta, raiz_cruda, raiz_canonica)
        if relativa is None:
            continue
        partes = tuple(p for p in relativa.split(os.sep) if p)
        carpeta = partes[:-1]  # carpeta que contiene al archivo
        if carpeta and carpeta[-1] in _DENTRO_DE_HERRAMIENTA:
            if nombre not in _DENTRO_DE_HERRAMIENTA[carpeta[-1]]:
                continue
            carpeta = carpeta[:-1]  # el proyecto es la carpeta que contiene a la de la herramienta
        elif nombre not in _EN_LA_CARPETA:
            continue  # p. ej. un ``config`` suelto que no está en ``.git``
        if not carpeta or any(p in _CARPETAS_DE_HERRAMIENTA for p in carpeta):
            continue  # la raíz nunca cuenta; lo de dentro de herramientas tampoco
        if any(p.lower() in _CARPETAS_DE_DEPENDENCIAS for p in carpeta):
            continue  # lo de dentro de carpetas de dependencias o de salida tampoco
        carpetas.add(carpeta)
    return len(carpetas)
