"""Nombres peligrosos: se muestran ESCRITOS, nunca borrados en silencio (diseño P4, sección 7).

Un nombre de archivo puede traer ``ESC[2J`` (borra la pantalla), U+202E (invierte el orden del texto), un salto de línea que
falsifica una línea del reporte... ``escribir_peligrosos`` cambia cada carácter peligroso por su forma escrita (``\\x1b``,
``\\u202e``, ``\\U000e0041``) para que quien lee vea que pasa algo raro y el nombre mostrado siga siendo el real.
La Historia 13b amplía esta pieza con la segunda barrera al imprimir y la comprobación final de ESC.
"""

from __future__ import annotations

import unicodedata

__all__ = ["MAX_NOMBRE", "escribir_peligrosos"]

MAX_NOMBRE = 1000  # un nombre más largo se corta con una marca explícita
_PELIGROSAS = frozenset({"Cc", "Cf", "Zl", "Zp", "Cs", "Co", "Cn"})
_ESCRITOS = {"\x1b": "\\x1b", "\n": "\\n", "\r": "\\r", "\t": "\\t", "\x00": "\\x00"}


def _peligroso(c: str) -> bool:
    categoria = unicodedata.category(c)
    return categoria in _PELIGROSAS or (categoria == "Zs" and c != " ")


def _escrito(c: str) -> str:
    if c in _ESCRITOS:
        return _ESCRITOS[c]
    n = ord(c)
    if n < 0x100:
        return f"\\x{n:02x}"
    return f"\\u{n:04x}" if n < 0x10000 else f"\\U{n:08x}"


def escribir_peligrosos(texto: str, recortar: bool = True) -> tuple[str, bool]:
    """El texto con los caracteres peligrosos escritos, y si hubo alguno. Recorta lo que pase de ``MAX_NOMBRE`` (solo una vez)."""
    cambio = False
    salida: list[str] = []
    for c in texto:
        if _peligroso(c):
            salida.append(_escrito(c))
            cambio = True
        else:
            salida.append(c)
    resultado = "".join(salida)
    if recortar and len(resultado) > MAX_NOMBRE:
        resultado = f"{resultado[:MAX_NOMBRE]}...[recortada: {len(resultado) - MAX_NOMBRE} caracteres]"
    return resultado, cambio
