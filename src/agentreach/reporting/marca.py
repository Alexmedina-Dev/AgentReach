"""Banner de marca de AgentReach en tres tamaños (Historia 13c; diseño ``docs/presentacion-terminal/diseno.md``, secciones 3 y 4).

AGENT va en ``#EAF4F2`` y REACH en ``#3DF5D0`` en fondo oscuro (en 16 colores, blanco y cian brillantes); en fondo claro,
``#0B1114`` y el menta con la luminosidad movida hasta 3:1; sin saber el fondo (``claro=None``), AGENT sin color propio y
REACH ``#07856C`` (cian normal en 16 colores). Cada tamaño tiene respaldo ASCII. El banner es identidad, no contenido: solo
sale si la salida es una terminal interactiva y nunca estorba a quien automatiza (``debe_mostrarse``).
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum

from agentreach.reporting.formato import Color, pintar

__all__ = ["LEMA", "Tamano", "banner", "debe_mostrarse", "tamano_efectivo"]

LEMA = "Know what your agents can reach."
ANCHO = {"grande": 61, "mediano": 69, "minimo": 57}  # lo que mide cada tamaño con su versión
_CORTE = 29  # columnas de la palabra AGENT; luego tres espacios y REACH


class Tamano(Enum):
    GRANDE = "grande"
    MEDIANO = "mediano"
    MINIMO = "minimo"


_GRANDE = (
    " ███   ████ █████ █   █ █████   ████  █████  ███   ████ █   █",
    "█   █ █     █     ██  █   █     █   █ █     █   █ █     █   █",
    "█████ █  ██ ████  █ █ █   █     ████  ████  █████ █     █████",
    "█   █ █   █ █     █  ██   █     █  █  █     █   █ █     █   █",
    "█   █  ███  █████ █   █   █     █   █ █████ █   █  ████ █   █",
)
_MEDIANO = (
    "▄▀▀▀▄ ▄▀▀▀▀ █▀▀▀▀ █▄  █ ▀▀█▀▀   █▀▀▀▄ █▀▀▀▀ ▄▀▀▀▄ ▄▀▀▀▀ █   █",
    "█▀▀▀█ █  ▀█ █▀▀▀  █ ▀▄█   █     █▀▀█  █▀▀▀  █▀▀▀█ █     █▀▀▀█",
    "▀   ▀  ▀▀▀  ▀▀▀▀▀ ▀   ▀   ▀     ▀   ▀ ▀▀▀▀▀ ▀   ▀  ▀▀▀▀ ▀   ▀",
)


def _a_ascii(filas: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(f.replace("█", "#") for f in filas)


def tamano_efectivo(pedido: Tamano, ancho: int, unicode_ok: bool) -> Tamano | None:
    """El tamaño que cabe, o ``None`` si la terminal es más angosta que 40 columnas (no hay banner)."""
    if ancho < 40:
        return None
    if pedido is not Tamano.MINIMO and ancho < ANCHO[pedido.value] + 1:
        return Tamano.MINIMO
    return pedido


def debe_mostrarse(
    es_terminal: bool, env: Mapping[str, str], no_banner: bool, json: bool, salida: bool, ancho: int
) -> bool:
    """Solo en una terminal interactiva. Nunca con redirección, ``NO_COLOR``, ``--no-banner``, ``--json``, ``--salida``,
    ``TERM=dumb`` ni una terminal de menos de 40 columnas."""
    if not es_terminal or salida or json or no_banner:
        return False
    if env.get("NO_COLOR") or env.get("AGENTREACH_NO_BANNER") or env.get("TERM") == "dumb":
        return False
    return ancho >= 40


def _letras(fila: str, color: Color, claro: bool | None) -> str:
    agent, reach = fila[:_CORTE], fila[_CORTE + 3:]
    return pintar(agent, "marca_agent", color, claro) + "   " + pintar(reach, "marca_reach", color, claro)


def banner(
    tamano: Tamano, version: str, *, ascii_: bool = False, color: Color = Color.NINGUNO, claro: bool | None = False, ancho: int = 80
) -> list[str]:
    """Las líneas del banner (con color si ``color`` lo pide). ``ascii_``: ningún carácter fuera de ASCII."""
    if tamano is Tamano.GRANDE:
        filas = _a_ascii(_GRANDE) if ascii_ else _GRANDE
        lineas = [_letras(f, color, claro) for f in filas]
        lineas.append(" " * 14 + pintar(LEMA, "marca_lema", color, claro))
        return lineas
    if tamano is Tamano.MEDIANO:
        if ascii_:
            return _mediano_ascii(version, color, claro)
        filas = list(_MEDIANO)
        lineas = [_letras(f, color, claro) for f in filas]
        lineas[-1] += "  " + pintar(f"v{version}", "marca_sec", color, claro)
        return lineas
    return [_minimo(version, ascii_, color, claro, corto=ancho < ANCHO['minimo'] + 1)]


def _minimo(version: str, ascii_: bool, color: Color, claro: bool | None, corto: bool = False) -> str:
    separador = "-" if ascii_ else "·"
    marca = (pintar("AGENT", "marca_agent", color, claro) + " " + pintar("REACH", "marca_reach", color, claro)
             + "  " + pintar(f"v{version}", "marca_sec", color, claro))
    if corto:  # una terminal angosta: sin el lema, para que la línea no se parta
        return marca
    return marca + f"  {separador}  " + pintar(LEMA, "marca_lema", color, claro)


def _mediano_ascii(version: str, color: Color, claro: bool | None) -> list[str]:
    ancho = 46
    borde = "+" + "-" * ancho + "+"
    titulo_plano = "A G E N T   R E A C H"
    version_texto = f"v{version}"
    relleno = " " * (ancho - 2 - len(titulo_plano) - len(version_texto) - 2)
    primera = (
        "|  " + pintar("A G E N T", "marca_agent", color, claro) + "   " + pintar("R E A C H", "marca_reach", color, claro)
        + relleno + "  " + pintar(version_texto, "marca_sec", color, claro) + "|"
    )
    segunda = "|  " + pintar(LEMA, "marca_lema", color, claro) + " " * (ancho - 2 - len(LEMA)) + "|"
    return [borde, primera, segunda, borde]
