"""Lector propio de JSON con comentarios (``//`` y ``/* */``) y comas finales: el "JSON de VS Code".

``.vscode/tasks.json``, ``.vscode/settings.json`` y otros archivos de editor y de agentes llevan
comentarios y comas finales, que ``json.loads`` rechaza. Este lector los quita SIN cambiar el número de
líneas (así el localizador de la Historia 1 sigue citando la línea correcta en el texto original) y luego
usa ``json.loads``.

No hace nada más allá: no acepta comillas simples ni claves sin comillas (ante la duda, error propio), no
sigue ``$schema`` ni ``include`` y no abre archivos: recibe el texto ya leído por la lectura segura. Los
errores nunca copian texto del archivo. Profundidad máxima de anidamiento: 64 niveles.
"""

from __future__ import annotations

import json

from agentreach.infra.lectura_segura import PROFUNDIDAD_MAXIMA


class JsoncNoInterpretable(Exception):
    """El texto no se pudo interpretar. El mensaje nunca copia texto del archivo."""


class ProfundidadExcedida(JsoncNoInterpretable):
    """El anidamiento supera el máximo."""


def limpiar_jsonc(texto: str) -> str:
    """Quita comentarios y comas finales. Conserva todos los saltos de línea y no toca las cadenas."""
    sin_comentarios: list[str] = []
    i, n = 0, len(texto)
    en_cadena = False
    while i < n:
        c = texto[i]
        if en_cadena:
            sin_comentarios.append(c)
            if c == "\\" and i + 1 < n:
                sin_comentarios.append(texto[i + 1])
                i += 2
                continue
            if c == '"':
                en_cadena = False
            i += 1
        elif c == '"':
            en_cadena = True
            sin_comentarios.append(c)
            i += 1
        elif texto.startswith("//", i):
            while i < n and texto[i] not in "\r\n":  # un comentario termina en cualquier fin de línea
                sin_comentarios.append(" ")
                i += 1
        elif texto.startswith("/*", i):
            fin = texto.find("*/", i + 2)
            if fin < 0:
                raise JsoncNoInterpretable("comentario de bloque sin cerrar")
            sin_comentarios.append("".join("\n" if ch == "\n" else " " for ch in texto[i:fin + 2]))
            i = fin + 2
        else:
            sin_comentarios.append(c)
            i += 1
    return _sin_comas_finales("".join(sin_comentarios))


def _sin_comas_finales(texto: str) -> str:
    salida = list(texto)
    en_cadena = False
    i, n = 0, len(texto)
    while i < n:
        c = texto[i]
        if en_cadena:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                en_cadena = False
        elif c == '"':
            en_cadena = True
        elif c == ",":
            j = i + 1
            while j < n and texto[j] in " \t\r\n":
                j += 1
            if j < n and texto[j] in "}]":
                salida[i] = " "  # coma final: se quita, la línea no cambia
        i += 1
    return "".join(salida)


def _profundidad(texto: str, maximo: int) -> None:
    nivel = 0
    en_cadena = False
    i, n = 0, len(texto)
    while i < n:
        c = texto[i]
        if en_cadena:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                en_cadena = False
        elif c == '"':
            en_cadena = True
        elif c in "{[":
            nivel += 1
            if nivel > maximo:
                raise ProfundidadExcedida("anidamiento demasiado profundo")
        elif c in "}]":
            nivel = max(0, nivel - 1)
        i += 1


class ClaveRepetida(JsoncNoInterpretable):
    """Una clave repetida en un objeto. ``clave`` es su NOMBRE (nunca su valor), para poder decirle a la persona cuál es."""

    def __init__(self, clave: str) -> None:
        super().__init__("clave repetida")
        self.clave = clave


def _sin_repetidas(pares: list[tuple[str, object]]) -> dict:
    """Un objeto JSON cuya clave se repite no tiene un único significado (cada lector se queda con una): no se interpreta."""
    vistas: set[str] = set()
    for k, _ in pares:
        if k in vistas:
            raise ClaveRepetida(k)
        vistas.add(k)
    return dict(pares)


def parsear_jsonc(texto: str, profundidad_maxima: int = PROFUNDIDAD_MAXIMA, *, rechazar_repetidas: bool = False) -> object:
    """El objeto del JSON. Lanza ``JsoncNoInterpretable`` (o ``ProfundidadExcedida``), nunca otra excepción.

    Con ``rechazar_repetidas``, una clave repetida dentro de un mismo objeto también lanza ``JsoncNoInterpretable``.
    """
    limpio = limpiar_jsonc(texto.removeprefix(chr(0xFEFF)))  # la marca BOM de Windows no es parte del JSON
    _profundidad(limpio, profundidad_maxima)
    try:
        return json.loads(limpio, object_pairs_hook=_sin_repetidas if rechazar_repetidas else None)
    except (ValueError, RecursionError):
        raise JsoncNoInterpretable("el texto no es JSON") from None
