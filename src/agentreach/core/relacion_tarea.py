"""«Ajeno a la tarea» (FR-9, campo 4): ¿tiene relación el hallazgo con lo que el agente va a hacer?

Reglas [SUPUESTO] de la Historia 12 (el PRD deja la regla exacta por definir, FR-9):

1. Una ruta FUERA del directorio de trabajo es ajena (``SI``).
2. Un archivo suelto en la raíz del directorio de trabajo, o dentro de una carpeta de configuración (``.git``, ``.claude``,
   ``.vscode``...), es del propio proyecto (``NO``).
3. Dentro, se comparan las palabras de la ruta con las de la tarea (``--tarea``) y las del README:
   - coincide con alguna: ``NO``;
   - no coincide y se dio una tarea: ``SI``;
   - no coincide y solo hay README (o nada): ``NO_DETERMINADO`` (un README no dice qué se va a hacer).
4. Sin README ni tarea: ``NO_DETERMINADO``.

Núcleo puro: recibe palabras, no textos. El texto de la tarea y del README se descarta tras sacar las palabras,
así nunca puede salir en un reporte.
"""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass

from agentreach.contracts import Ajeno

__all__ = ["Referencia", "clasificar", "palabras"]

_MAX_PALABRAS = 5000  # un README enorme no hace crecer el cálculo sin límite
_PALABRA = re.compile(r"[a-z0-9]+")
# Palabras que no distinguen un archivo de otro (carpetas y extensiones corrientes) y conectores cortos.
_VACIAS = frozenset({
    "src", "lib", "app", "docs", "doc", "config", "env", "txt", "md", "json", "yml", "yaml", "toml", "cfg", "ini",
    "the", "and", "for", "with", "del", "las", "los", "una", "uno", "por", "con", "que", "para", "este", "esta",
})


@dataclass(frozen=True, slots=True)
class Referencia:
    """Palabras de la tarea y del README. ``None``: no se dio o no se pudo leer."""

    tarea: frozenset[str] | None = None
    readme: frozenset[str] | None = None


def palabras(texto: str) -> frozenset[str]:
    """Palabras en minúscula y sin acentos (3 letras o más, sin las vacías). El texto no se conserva."""
    plano = unicodedata.normalize("NFKD", texto.lower())
    plano = "".join(c for c in plano if not unicodedata.combining(c))
    encontradas = (p for p in _PALABRA.findall(plano) if len(p) >= 3 and p not in _VACIAS)
    salida: set[str] = set()
    for p in encontradas:
        salida.add(p)
        if len(salida) >= _MAX_PALABRAS:
            break
    return frozenset(salida)


def _coincide(a: str, b: str) -> bool:
    """Iguales, o una empieza por la otra (formulario / formularios), con al menos 4 letras."""
    return a == b or (min(len(a), len(b)) >= 4 and (a.startswith(b) or b.startswith(a)))


def _hay_relacion(de_la_ruta: frozenset[str], referencia: frozenset[str]) -> bool:
    return any(_coincide(a, b) for a in de_la_ruta for b in referencia)


def _relativa(ruta: str, trabajo: str) -> str | None:
    """Ruta relativa al directorio de trabajo, o ``None`` si queda fuera (o no se puede decidir)."""
    try:
        absoluta = os.path.normcase(os.path.abspath(ruta))
        base = os.path.normcase(os.path.abspath(trabajo))
        if os.path.commonpath([absoluta, base]) != base:
            return None
        return os.path.relpath(absoluta, base)
    except ValueError:  # otra unidad de disco, o una ruta con caracteres imposibles
        return None


def clasificar(ruta: str, trabajo: str, referencia: Referencia) -> Ajeno:
    """¿Es ``ruta`` ajena a la tarea? Una ruta que no es de un archivo (``(Windows nativo)``) no se puede decidir."""
    if not ruta or ruta.startswith("(") or not os.path.isabs(ruta):
        return Ajeno.NO_DETERMINADO
    relativa = _relativa(ruta, trabajo)
    if relativa is None:
        return Ajeno.SI  # fuera del directorio de trabajo
    if os.sep not in relativa and "/" not in relativa:
        return Ajeno.NO  # suelto en la raíz: del propio proyecto
    if relativa.replace("\\", "/").split("/")[0].startswith("."):
        return Ajeno.NO  # carpeta de configuración del propio proyecto
    de_la_ruta = palabras(relativa)
    if referencia.tarea is None and referencia.readme is None:
        return Ajeno.NO_DETERMINADO
    for conocido in (referencia.tarea, referencia.readme):
        if conocido and _hay_relacion(de_la_ruta, conocido):
            return Ajeno.NO
    return Ajeno.SI if referencia.tarea else Ajeno.NO_DETERMINADO
