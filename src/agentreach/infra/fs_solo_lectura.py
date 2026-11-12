"""Sistema de archivos de solo lectura: implementa el puerto ``ReadOnlyFs`` con la biblioteca estándar.

Reglas que cumple:

- No tiene ningún método que escriba, borre o cree algo.
- No sigue enlaces: de un enlace solo entrega su ruta y su destino (texto), nunca lo que hay detrás.
- No ejecuta programas externos.
- Lee solo con ``leer_seguro`` (la única función de lectura). Si no se puede, ``leer_texto`` lanza
  ``ArchivoNoLegible`` con el motivo y sin copiar contenido en el mensaje.
"""

from __future__ import annotations

import os
import stat
from collections.abc import Iterable

from agentreach.contracts import (
    ArchivoNoLegible,
    FueraDelProyecto,
    Metadatos,
    MotivoNoRevisado,
    NoRevisado,
    Ruta,
    limpiar_ruta,
)
from agentreach.contracts.ports import LIMITE_BYTES
from agentreach.contracts.rutas import es_ruta_de_red
from agentreach.infra.lectura_segura import leer_seguro

_PREFIJO_NT = "\\\\?\\"


def _destino(ruta: str) -> Ruta | None:
    try:
        destino = os.readlink(ruta)
    except OSError:
        return None
    if destino.startswith(_PREFIJO_NT + "UNC\\"):
        destino = "\\\\" + destino[len(_PREFIJO_NT + "UNC\\"):]
    elif destino.startswith(_PREFIJO_NT):
        destino = destino[len(_PREFIJO_NT):]
    return limpiar_ruta(destino)


def _es_enlace(ruta: str) -> bool:
    return os.path.islink(ruta) or os.path.isjunction(ruta)


def _destino_real(ruta: str) -> str | None:
    """Destino del enlace tal cual (sin limpiar), solo para comparar dentro del programa."""
    try:
        destino = os.readlink(ruta)
    except OSError:
        return None
    if destino.startswith(_PREFIJO_NT + "UNC\\"):
        return "\\\\" + destino[len(_PREFIJO_NT + "UNC\\"):]
    return destino.removeprefix(_PREFIJO_NT)


def _metadatos(ruta: str, tamano: int, es_carpeta: bool, modo: int | None = None) -> Metadatos:
    enlace = _es_enlace(ruta)
    return Metadatos(
        ruta=limpiar_ruta(ruta),  # para mostrar
        tamano=tamano,
        es_carpeta=es_carpeta,
        es_enlace=enlace,
        destino_enlace=_destino(ruta) if enlace else None,  # para mostrar
        ruta_real=ruta,  # para usar: sin limpiar
        destino_real=_destino_real(ruta) if enlace else None,
        es_regular=(not enlace and not es_carpeta and modo is not None and stat.S_ISREG(modo)),
    )


def _canonica(ruta: str) -> str:
    """Ruta resuelta (enlaces incluidos) y en minúsculas donde el sistema no distingue mayúsculas."""
    return os.path.normcase(os.path.realpath(ruta).removeprefix(_PREFIJO_NT))


def _hay_enlace_en_el_camino(ruta: str) -> bool:
    """True si algún componente de la ruta (no solo el último) es un enlace o junction."""
    absoluta = os.path.abspath(ruta)
    unidad, resto = os.path.splitdrive(absoluta)
    actual = unidad + os.sep
    for parte in [p for p in resto.split(os.sep) if p]:
        actual = os.path.join(actual, parte)
        if _es_enlace(actual):
            return True
    return False


class FsSoloLectura:
    """Lectura de metadatos y de texto de configuración, sin seguir enlaces.

    ``raiz`` es la carpeta del proyecto. Con ella, ``leer_texto`` resuelve la ruta completa y no lee
    nada que quede fuera (un enlace en una carpeta intermedia). Sin ella, rechaza cualquier ruta que
    pase por un enlace, que es lo más estricto.
    """

    def __init__(self, raiz: str | None = None) -> None:
        self._raiz = raiz

    def listar(self, carpeta: Ruta) -> Iterable[Metadatos]:
        with os.scandir(carpeta) as it:
            entradas = sorted(it, key=lambda e: e.name)
        for e in entradas:
            enlace = _es_enlace(e.path)
            es_carpeta = enlace or e.is_dir(follow_symlinks=False)
            st = None if es_carpeta else e.stat(follow_symlinks=False)  # una sola consulta
            yield _metadatos(e.path, 0 if st is None else st.st_size, es_carpeta, None if st is None else st.st_mode)

    def metadatos(self, ruta: Ruta) -> Metadatos | None:
        try:
            st = os.lstat(ruta)
        except OSError:
            return None
        enlace = _es_enlace(ruta)
        es_carpeta = enlace or os.path.isdir(ruta)
        return _metadatos(ruta, 0 if es_carpeta else st.st_size, es_carpeta, st.st_mode)

    def _confinar(self, ruta: str) -> None:
        """Lanza ``FueraDelProyecto`` si la ruta completa resuelta no queda dentro del proyecto."""
        if es_ruta_de_red(ruta) or (self._raiz is not None and es_ruta_de_red(self._raiz)):
            raise ArchivoNoLegible("ruta de red: no se consulta", MotivoNoRevisado.RUTA_DE_RED)
        try:
            if self._raiz is None:
                fuera = _hay_enlace_en_el_camino(ruta)
            else:
                raiz = _canonica(self._raiz)
                fuera = os.path.commonpath([_canonica(ruta), raiz]) != raiz
        except (OSError, ValueError):  # ValueError: otra unidad o ruta inválida
            fuera = True
        if fuera:
            raise FueraDelProyecto("la ruta sale del proyecto o pasa por un enlace: no se lee")

    def leer_texto(self, ruta: Ruta) -> str:
        """Texto del archivo con las reglas de ``leer_seguro``, con el tope de ``LIMITE_BYTES`` (1 MiB).

        Los archivos de configuración que se leen son pequeños: el tope de 5 MB de ``leer_seguro`` es
        el máximo absoluto; aquí se usa uno menor a propósito.
        """
        if _es_enlace(ruta):
            raise ArchivoNoLegible("es un enlace: no se sigue", MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR)
        self._confinar(ruta)
        resultado = leer_seguro(ruta, tope=LIMITE_BYTES)
        if isinstance(resultado, NoRevisado):
            raise ArchivoNoLegible(resultado.motivo.value, resultado.motivo)
        return resultado


def carpeta_que_es_archivo(ruta: str) -> str | None:
    """Si ``ruta`` no existe porque una de sus carpetas es en realidad un archivo (p. ej. ``.claude`` o ``.opencode``), esa «carpeta».

    Es lo contrario de «no existe, lo normal»: hay algo en el lugar de la configuración que no se puede leer como carpeta, así que no
    se sabe qué reglas había. Devuelve ``None`` si el ancestro que existe es una carpeta de verdad (o no hay ninguno). Solo consulta.
    """
    actual = os.path.dirname(os.path.abspath(ruta))
    while True:
        if os.path.lexists(actual):
            return None if os.path.isdir(actual) else actual
        superior = os.path.dirname(actual)
        if superior == actual:
            return None
        actual = superior
