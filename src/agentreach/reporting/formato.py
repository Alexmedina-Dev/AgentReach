"""Forma del reporte de terminal (Historia 13b): ancho, ajuste, color y salida segura (diseño, secciones 2, 3 y 4).

Todo es texto y funciones puras, salvo ``activar_vt`` y ``preparar_salida``, que tocan la consola y solo se llaman desde
``main()``. El color se aplica DESPUÉS de ajustar: primero se mide y se parte el texto plano, luego se pinta cada línea.
Solo se emiten secuencias de color (las que terminan en ``m``): nunca mover el cursor, borrar pantalla, títulos ni enlaces.
"""

from __future__ import annotations

import colorsys
import logging
import re
import sys
import unicodedata
from collections.abc import Mapping
from enum import Enum

__all__ = [
    "Color",
    "activar_vt",
    "ajustar",
    "ancho_de_trabajo",
    "ancho_visible",
    "colores_de_marca",
    "contraste",
    "decidir_color",
    "fondo_claro",
    "pintar",
    "preparar_salida",
    "resolver_tema",
    "resolver_tema_marca",
    "ultima_comprobacion",
]

ANCHO_MIN, ANCHO_MAX = 60, 100
_LOG = logging.getLogger(__name__)


# ---- ancho ------------------------------------------------------------------------------------------------------------


def ancho_visible(texto: str) -> int:
    """Columnas que ocupa el texto: los caracteres de ancho doble cuentan 2 y los que se pegan al anterior, 0."""
    columnas = 0
    for c in texto:
        if unicodedata.combining(c) or unicodedata.category(c) in ("Mn", "Me", "Cf"):
            continue
        columnas += 2 if unicodedata.east_asian_width(c) in ("W", "F") else 1
    return columnas


def ancho_de_trabajo(columnas: int) -> int:
    """El ancho de trabajo: las columnas de la terminal, entre 60 y 100."""
    return min(max(columnas, ANCHO_MIN), ANCHO_MAX)


_ESPACIOS = re.compile(r"( +)")


def ajustar(texto: str, ancho: int, primera: int = 0, resto: int | None = None) -> list[str]:
    """Parte ``texto`` en límites de palabra a ``ancho - 1`` columnas con sangría francesa.

    Nunca parte una palabra (ni después de un guion): una palabra más larga que la línea queda entera y la terminal la
    parte sola. Mide con ``ancho_visible``. Las líneas salen sin espacios al final.
    """
    resto = primera if resto is None else resto
    limite = max(ancho - 1, 20)
    lineas: list[str] = []
    actual, usado, sangria = "", 0, primera
    pendiente_espacio = ""
    for ficha in _ESPACIOS.split(texto):
        if not ficha:
            continue
        if ficha.isspace():
            pendiente_espacio = ficha
            continue
        necesario = ancho_visible(pendiente_espacio) + ancho_visible(ficha) if actual else ancho_visible(ficha)
        if actual and sangria + usado + necesario > limite:
            lineas.append(" " * sangria + actual)
            actual, usado, sangria = ficha, ancho_visible(ficha), resto
        else:
            actual = actual + pendiente_espacio + ficha if actual else ficha
            usado += necesario
        pendiente_espacio = ""
    lineas.append(" " * sangria + actual)
    return lineas


# ---- color ------------------------------------------------------------------------------------------------------------


class Color(Enum):
    NINGUNO = "ninguno"
    DE_16 = "16"
    DE_24_BITS = "24"


# rol: (24 bits fondo oscuro, 24 bits fondo claro, 16 colores fondo oscuro, 16 colores fondo claro)
_PALETA: dict[str, tuple[str, str, int, int]] = {
    "comprobado": ("FF6B6B", "B3201A", 91, 31),
    "potencial": ("FFB224", "7A4300", 33, 33),
    "hipotesis": ("A9BDB9", "3A524D", 37, 90),
    "no_revisar": ("B9A2FF", "5A3DC0", 95, 35),
    "ok": ("3DF5D0", "005F4D", 96, 32),
    "info": ("6DB6FF", "0A58A8", 94, 34),
    "sec": ("7C928E", "46635E", 90, 90),
    # marca: AGENT #EAF4F2 y REACH #3DF5D0 en fondo oscuro (decisión de Alex, 2026-11-09). En fondo claro (Historia 29, se asume
    # blanco): AGENT #0B1114 y REACH el menta con la luminosidad movida hasta 3:1; son lo que da colores_de_marca. La versión
    # y el lema del banner tienen roles propios (marca_sec, marca_lema) con los mismos colores que sec e hipotesis.
    # Historia 29: en fondo claro (se asume blanco) AGENT #0B1114 y REACH el menta con la luminosidad movida hasta 3:1
    "marca_agent": ("EAF4F2", "0B1114", 97, 30),
    "marca_reach": ("3DF5D0", "09A888", 96, 36),
    "marca_sec": ("7C928E", "46635E", 90, 90),
    "marca_lema": ("A9BDB9", "3A524D", 37, 90),
}
# Historia 29: sin saber el fondo no se adivina. AGENT usa el texto normal de la terminal; REACH, un menta-teal que da
# 4,5:1 contra blanco y contra negro; en 16 colores, el cian normal (36).
REACH_UNIVERSAL = "07856C"
REACH_UNIVERSAL_16 = 36
GRIS_UNIVERSAL = "767676"  # versión y lema del banner sin tema: ~4,5:1 contra blanco y contra negro
GRIS_UNIVERSAL_16 = 90
_AGENT_CLARO, _AGENT_OSCURO, _REACH_MARCA = "0B1114", "EAF4F2", "3DF5D0"
RESET = "\x1b[0m"


def _luminancia(rgb: tuple[int, int, int]) -> float:
    def canal(v: int) -> float:
        c = v / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def _a_rgb(hexa: str) -> tuple[int, int, int]:
    return int(hexa[0:2], 16), int(hexa[2:4], 16), int(hexa[4:6], 16)


def _a_hex(rgb: tuple[int, int, int]) -> str:
    return "{:02X}{:02X}{:02X}".format(*rgb)


def contraste(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    """Contraste de la WCAG entre dos colores RGB: (L1 + 0,05) / (L2 + 0,05), con L1 la mayor luminancia."""
    la, lb = sorted((_luminancia(a), _luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def colores_de_marca(fondo: tuple[int, int, int]) -> tuple[str, str | None]:
    """(AGENT, REACH) en hexadecimal para un fondo RGB conocido. Función pura.

    AGENT: ``#EAF4F2`` o ``#0B1114``, el de más contraste. REACH: el matiz y la saturación del menta de marca; solo
    cambia la luminosidad, la más cercana a la original que llegue a 3:1 (dentro de 20 % a 80 %); si ninguna llega, la de
    más contraste en ese rango. Si ni así llega a 3:1 (fondo casi menta), REACH es ``None``: el llamador usa el caso
    «desconocido» (color universal).
    """
    agent = max((_AGENT_OSCURO, _AGENT_CLARO), key=lambda h: contraste(_a_rgb(h), fondo))
    r, g, b = (v / 255 for v in _a_rgb(_REACH_MARCA))
    tono, luz0, sat = colorsys.rgb_to_hls(r, g, b)

    def candidato(luz: float) -> tuple[int, int, int]:
        rr, gg, bb = colorsys.hls_to_rgb(tono, luz, sat)
        return round(rr * 255), round(gg * 255), round(bb * 255)

    if contraste(_a_rgb(_REACH_MARCA), fondo) >= 3:
        return agent, _REACH_MARCA
    for i in range(1, 601):  # de 0,001 en 0,001 a partir de la luminosidad original, hacia ambos lados
        for luz in (luz0 + i / 1000, luz0 - i / 1000):
            if 0.2 <= luz <= 0.8 and contraste(candidato(luz), fondo) >= 3:
                return agent, _a_hex(candidato(luz))
    mejor = max((candidato(n / 1000) for n in range(200, 801)), key=lambda c: contraste(c, fondo))
    if contraste(mejor, fondo) >= 3:
        return agent, _a_hex(mejor)
    _LOG.info("Ninguna luminosidad del menta llega a 3:1 con el fondo %s: se usa el color universal", fondo)
    return agent, None


def fondo_claro(env: Mapping[str, str]) -> bool:
    """``COLORFGBG`` («primer plano;fondo»): un fondo 7 o 15 es claro. Windows Terminal no lo define: se asume oscuro."""
    try:
        return int(env.get("COLORFGBG", "").rsplit(";", 1)[-1]) in (7, 15)
    except ValueError:
        return False


def resolver_tema(opcion: str | None, env: Mapping[str, str]) -> bool:
    """¿Fondo claro? ``--tema`` gana a ``AGENTREACH_TEMA`` y esta a ``COLORFGBG``; si no se puede saber, oscuro.

    Una opción explícita (``auto`` incluido) corta la cascada: ``auto`` va directo a ``COLORFGBG``. Un valor que no se
    entiende cuenta como no dicho y se pasa a la fuente siguiente.
    """
    elegido = (opcion or "").lower()
    if elegido in ("claro", "oscuro"):
        return elegido == "claro"
    if elegido != "auto":
        variable = env.get("AGENTREACH_TEMA", "").lower()
        if variable in ("claro", "oscuro"):
            return variable == "claro"
    return fondo_claro(env)


def _tema_colorfgbg(env: Mapping[str, str]) -> bool | None:
    """``COLORFGBG`` a tres estados: claro (7 o 15), oscuro (otro color 0-15) o ``None`` (no está o no se entiende)."""
    try:
        fondo = int(env.get("COLORFGBG", "").rsplit(";", 1)[-1])
    except ValueError:
        return None
    return fondo in (7, 15) if 0 <= fondo <= 15 else None


def resolver_tema_marca(opcion: str | None, env: Mapping[str, str]) -> bool | None:
    """Como ``resolver_tema`` pero con el estado «no sé»: ``True`` claro, ``False`` oscuro, ``None`` desconocido.

    Prioridad: ``--tema`` > ``AGENTREACH_TEMA`` > ``COLORFGBG`` > desconocido. Solo la usa el logo.
    """
    elegido = (opcion or "").lower()
    if elegido in ("claro", "oscuro"):
        return elegido == "claro"
    if elegido != "auto":
        variable = env.get("AGENTREACH_TEMA", "").lower()
        if variable in ("claro", "oscuro"):
            return variable == "claro"
    return _tema_colorfgbg(env)


def decidir_color(opcion: str, es_terminal: bool, env: Mapping[str, str], plataforma: str, vt_activo: bool) -> Color:
    """Prioridad del diseño: ``--color``, ``NO_COLOR``, salida no terminal, ``TERM=dumb``, modo de secuencias de Windows."""
    if opcion == "nunca":
        return Color.NINGUNO
    if opcion != "siempre":
        if env.get("NO_COLOR"):
            return Color.NINGUNO
        if not es_terminal or env.get("TERM") == "dumb":
            return Color.NINGUNO
        if plataforma == "win32" and not vt_activo:
            return Color.NINGUNO
    señal = (
        env.get("COLORTERM", "").lower() in ("truecolor", "24bit") or "WT_SESSION" in env or env.get("TERM_PROGRAM") == "vscode"
    )
    return Color.DE_24_BITS if señal else Color.DE_16


def pintar(linea: str, rol: str | None, color: Color, claro: bool | None = False) -> str:
    """La línea con su color; cada trozo pintado termina en ``ESC[0m``. Sin color o sin rol, la línea tal cual.

    ``claro=None`` (tema desconocido) solo cambia el logo: AGENT sin color propio y REACH con el color universal; los
    demás roles se pintan como en fondo oscuro, igual que antes.
    """
    if color is Color.NINGUNO or rol is None or rol not in _PALETA or not linea.strip():
        return linea
    oscuro, claro_hex, codigo, codigo_claro = _PALETA[rol]
    if claro is None and rol == "marca_agent":
        return linea
    if claro is None and rol in ("marca_sec", "marca_lema"):
        codigo = GRIS_UNIVERSAL_16
        oscuro = GRIS_UNIVERSAL
    if claro is None and rol == "marca_reach":
        codigo = REACH_UNIVERSAL_16
        oscuro = REACH_UNIVERSAL
    if color is Color.DE_16:
        inicio = f"\x1b[{codigo_claro if claro else codigo}m"
    else:
        hexa = claro_hex if claro else oscuro
        r, g, b = (int(hexa[i:i + 2], 16) for i in (0, 2, 4))
        inicio = f"\x1b[38;2;{r};{g};{b}m"
    sangria = len(linea) - len(linea.lstrip(" "))
    return linea[:sangria] + inicio + linea[sangria:] + RESET


def activar_vt(flujo: object | None = None) -> bool:
    """Activa el modo de secuencias de la consola de Windows (``ENABLE_VIRTUAL_TERMINAL_PROCESSING``). ``False`` si falla."""
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetStdHandle.argtypes = [wintypes.DWORD]
        kernel.GetStdHandle.restype = wintypes.HANDLE
        kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.GetConsoleMode.restype = wintypes.BOOL
        kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.SetConsoleMode.restype = wintypes.BOOL
        manejador = kernel.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        if manejador in (None, wintypes.HANDLE(-1).value):  # sin consola o manejador inválido
            return False
        modo = wintypes.DWORD()
        if not kernel.GetConsoleMode(manejador, ctypes.byref(modo)):
            return False
        return bool(kernel.SetConsoleMode(manejador, modo.value | 0x0004))
    except Exception:  # noqa: BLE001 - ctypes.ArgumentError y compañía: sin color, nunca un error interno
        return False


# ---- salida -----------------------------------------------------------------------------------------------------------

# solo las formas que emite ``pintar``: reset, colores de 16 y primer plano de 24 bits
_SECUENCIA_PROPIA = re.compile(r"\x1b\[(?:0|3[0-7]|9[0-7]|38;2;\d{1,3};\d{1,3};\d{1,3})m")
_CONTROLES = re.compile("[\x00-\x09\x0b-\x1f\x7f-\x9f]")  # todo control menos el salto de línea


def ultima_comprobacion(texto: str) -> str:
    """Solo pueden salir ESC de nuestras secuencias de color. Lo demás (ESC ajeno, BEL, CSI y OSC de 8 bits) se quita."""
    partes = _SECUENCIA_PROPIA.split(texto)
    propias = _SECUENCIA_PROPIA.findall(texto)
    limpias = [_CONTROLES.sub("", p) for p in partes]
    salida = limpias[0]
    for secuencia, parte in zip(propias, limpias[1:], strict=True):
        salida += secuencia + parte
    return salida


def preparar_salida(flujo: object) -> None:
    """UTF-8 sin trazas en un flujo que no es una terminal. No falla con un ``StringIO`` ni con un flujo cerrado."""
    try:
        flujo.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError, OSError):
        pass  # StringIO de una prueba, flujo ya usado o cerrado: se sigue con lo que haya
