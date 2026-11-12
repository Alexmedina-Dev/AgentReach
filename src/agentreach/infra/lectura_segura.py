"""La única función que lee texto de archivos: ``leer_seguro`` (FR-25 y FR-26).

Reglas, en este orden y antes de abrir nada:

1. Una ruta de red no se consulta.
2. El tipo se comprueba con metadatos (``lstat``): un enlace, una *junction*, una tubería con nombre,
   un dispositivo o una carpeta se rechazan sin abrirlos (abrir una tubería puede bloquear).
3. Un archivo de más de ``TOPE_BYTES`` se rechaza por su tamaño, sin abrirlo.
4. Se abre sin seguir enlaces ni bloquear, se vuelve a comprobar el tipo sobre el descriptor ya
   abierto y se lee a lo sumo ``TOPE_BYTES + 1`` bytes.
5. El texto debe ser UTF-8 estricto (se acepta la marca BOM del inicio).

Todo fallo es un ``NoRevisado`` con un motivo de lista cerrada, nunca una excepción ni texto del archivo.
"""

from __future__ import annotations

import os
import stat
from collections.abc import Callable

from agentreach.contracts import Ruta
from agentreach.contracts.no_revisado import MotivoNoRevisado, NoRevisado
from agentreach.contracts.rutas import es_ruta_de_red

TOPE_BYTES = 5 * 1024 * 1024  # 5 MB
PROFUNDIDAD_MAXIMA = 64  # niveles de anidamiento que aceptan los lectores de JSON, TOML e include


def _es_enlace(ruta: str) -> bool:
    return os.path.islink(ruta) or os.path.isjunction(ruta)


def leer_seguro(
    ruta: Ruta,
    *,
    tope: int = TOPE_BYTES,
    lstat: Callable[[str], os.stat_result] = os.lstat,
) -> str | NoRevisado:
    """Texto del archivo, o ``NoRevisado`` con el motivo. ``lstat`` se inyecta solo en las pruebas."""

    def no(motivo: MotivoNoRevisado) -> NoRevisado:
        return NoRevisado(ruta, motivo)

    if es_ruta_de_red(ruta):
        return no(MotivoNoRevisado.RUTA_DE_RED)
    try:
        datos_ruta = lstat(ruta)
    except (OSError, ValueError):
        return no(MotivoNoRevisado.ARCHIVO_ILEGIBLE)
    if _es_enlace(ruta) or not stat.S_ISREG(datos_ruta.st_mode):
        return no(MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR)
    if datos_ruta.st_size > tope:
        return no(MotivoNoRevisado.ARCHIVO_DEMASIADO_GRANDE)
    try:
        # O_NOFOLLOW (donde exista) no sigue un enlace puesto a última hora; O_NONBLOCK evita
        # quedarse esperando en una tubería puesta entre la comprobación y la apertura.
        banderas = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        banderas |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        descriptor = os.open(ruta, banderas)
        try:
            archivo = os.fdopen(descriptor, "rb")
        except BaseException:
            os.close(descriptor)  # que un fallo al envolverlo no deje el descriptor abierto
            raise
        with archivo as f:
            if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
                return no(MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR)
            datos = f.read(tope + 1)
    except (OSError, ValueError):
        return no(MotivoNoRevisado.ARCHIVO_ILEGIBLE)
    if len(datos) > tope:
        return no(MotivoNoRevisado.ARCHIVO_DEMASIADO_GRANDE)
    if b"\x00" in datos:  # un byte NUL: no es texto
        return no(MotivoNoRevisado.CODIFICACION_NO_UTF8)
    try:
        return datos.decode("utf-8-sig")
    except UnicodeDecodeError:
        return no(MotivoNoRevisado.CODIFICACION_NO_UTF8)


def revisar_profundidad_json(ruta: Ruta, texto: str, maximo: int = PROFUNDIDAD_MAXIMA) -> NoRevisado | None:
    """``NoRevisado`` si el JSON se anida más de ``maximo`` niveles; ``None`` si es aceptable.

    Cuenta llaves y corchetes sin construir el árbol (un ``json.loads`` con anidamiento extremo
    agotaría la pila) y sin mirar el contenido de las cadenas.
    """
    nivel = 0
    en_cadena = False
    escape = False
    for c in texto:
        if en_cadena:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                en_cadena = False
        elif c == '"':
            en_cadena = True
        elif c in "{[":
            nivel += 1
            if nivel > maximo:
                return NoRevisado(ruta, MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA)
        elif c in "}]":
            nivel = max(0, nivel - 1)
    return None
