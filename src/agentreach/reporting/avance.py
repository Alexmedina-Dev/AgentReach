"""Historia 41: una sola línea que se actualiza en su sitio mientras AgentReach revisa una carpeta grande.

Solo muestra el paso (X de Y), cuántas carpetas distintas se han recorrido y el tiempo transcurrido: nunca nombres de archivo,
rutas ni valores (AD-15). No hay hilos ni temporizadores: la línea se redibuja cuando el recorrido avanza, con el reloj al
momento de dibujar, y así una línea quieta delata un bloqueo real. Escribe solo en el flujo que recibe (la salida de errores),
sin abrir archivos. Todo texto visible sale del catálogo es/en y pasa por ``formato.ajustar``; la línea nunca se parte.

El borrado usa solo retorno de carro y espacios (nunca secuencias que muevan el cursor); lo único que se emite además son las
secuencias de color de ``formato.pintar`` y solo si la persona no pidió quitar el color.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from agentreach.contracts import Idioma
from agentreach.reporting.formato import Color, ajustar, pintar

__all__ = ["Avance"]

_CATALOGO: dict[Idioma, dict[str, str]] = {
    Idioma.ES: {
        "revisando": "Revisando…", "paso": "paso {n} de {total}", "carpeta": "1 carpeta", "carpetas": "{n} carpetas",
        "evaluando": "Evaluando los hallazgos…", "reporte": "Preparando el reporte…",
    },
    Idioma.EN: {
        "revisando": "Checking…", "paso": "step {n} of {total}", "carpeta": "1 folder", "carpetas": "{n} folders",
        "evaluando": "Evaluating the findings…", "reporte": "Preparing the report…",
    },
}
_SEPARADOR = " · "
_CASILLAS = 10
_ACTUALIZAR_CADA = 0.1  # segundos entre dos dibujos por carpetas nuevas; los cambios de paso siempre se dibujan


def _miles(n: int, idioma: Idioma, unicode_ok: bool) -> str:
    if not unicode_ok:
        return str(n)  # sin UTF-8 no hay espacio duro: el número va sin separador
    return f"{n:,}".replace(",", " " if idioma is Idioma.ES else ",")


def _tiempo(segundos: float) -> str:
    s = int(segundos)
    return f"{s} s" if s < 60 else f"{s // 60} min {s % 60} s"


class Avance:
    """Indicador de avance. Se llama como ``avance(evento, a, b)``; eventos: ``paso`` (n, total), ``carpetas`` (cantidad),
    ``evaluando`` y ``reporte``. ``cerrar()`` borra la línea y es seguro llamarlo varias veces."""

    def __init__(self, flujo, idioma: Idioma, columnas: Callable[[], int], *, ascii_: bool = False, color: Color = Color.NINGUNO,
                 claro: bool | None = False, reloj: Callable[[], float] = time.monotonic) -> None:
        self._flujo = flujo
        self._idioma = idioma
        self._columnas = columnas
        self._unicode = not ascii_
        self._color = color
        self._claro = claro
        self._reloj = reloj
        self._inicio = reloj()
        self._ultimo_dibujo = float("-inf")
        self._largo = 0  # columnas de la última línea dibujada (para borrarla entera)
        self._activo = True
        self._paso: tuple[int, int] | None = None
        self._fase = "revisando"
        self._carpetas = 0

    # -- entrada -------------------------------------------------------------------------------------------------------

    def __call__(self, evento: str, a: int = 0, b: int = 0) -> None:
        if not self._activo:
            return
        try:
            if evento == "paso":
                self._paso, self._fase = (a, b), "revisando"
            elif evento == "carpetas":
                self._carpetas = a
                if self._reloj() - self._ultimo_dibujo < _ACTUALIZAR_CADA:
                    return
            elif evento in ("evaluando", "reporte"):
                self._fase = evento
            else:
                return
            self._dibujar()
        except Exception:  # noqa: BLE001 - el avance es cosmético: nunca cambia ni aborta la revisión
            self._activo = False

    # -- línea ---------------------------------------------------------------------------------------------------------

    def _barra(self) -> str:
        hecho, total = self._paso or (0, 1)
        llenas = min(_CASILLAS, max(0, (hecho * _CASILLAS) // max(total, 1)))
        lleno, vacio = ("█", "░") if self._unicode else ("#", "-")
        return "[" + lleno * llenas + vacio * (_CASILLAS - llenas) + "]"

    def _texto_carpetas(self) -> str:
        t = _CATALOGO[self._idioma]
        if not self._carpetas:
            return ""
        return t["carpeta"] if self._carpetas == 1 else t["carpetas"].format(n=_miles(self._carpetas, self._idioma, self._unicode))

    def _candidatas(self) -> list[str]:
        t = _CATALOGO[self._idioma]
        punto = t["revisando"] if self._unicode else t["revisando"].replace("…", "...")
        tiempo = _tiempo(self._reloj() - self._inicio)
        sep = _SEPARADOR if self._unicode else " - "
        if self._fase != "revisando":
            texto = t[self._fase] if self._unicode else t[self._fase].replace("…", "...")
            piezas = [p for p in (self._texto_carpetas(), tiempo) if p]
            return [texto + "".join(sep + p for p in piezas), f"{texto}{sep}{tiempo}", texto]
        hecho, total = self._paso or (0, 0)
        paso = t["paso"].format(n=hecho, total=total)
        piezas = [p for p in (self._texto_carpetas(), tiempo) if p]
        return [
            f"{punto} {paso} {self._barra()}" + "".join(sep + p for p in piezas),
            f"{punto} {paso}" + "".join(sep + p for p in piezas),
            f"{punto} {paso}{sep}{tiempo}",
            paso,
            f"{hecho}/{total}",
        ]

    def _linea(self) -> str:
        ancho = min(max(self._columnas(), 21), 100)  # ajustar deja ancho - 1 columnas: la línea no llega al borde y no se parte
        candidatas = self._candidatas()
        for c in candidatas:
            lineas = ajustar(c, ancho)
            if len(lineas) == 1:
                return lineas[0]
        return ajustar(candidatas[-1], ancho)[0]  # una terminal diminuta: se acota la más corta

    # -- salida --------------------------------------------------------------------------------------------------------

    def _escribir(self, texto: str) -> None:
        try:
            try:
                self._flujo.write(texto)
            except UnicodeEncodeError:  # una consola que no entiende un símbolo: nunca una traza
                codificacion = getattr(self._flujo, "encoding", None) or "ascii"
                self._flujo.write(texto.encode(codificacion, "replace").decode(codificacion))
            self._flujo.flush()
        except (OSError, ValueError, LookupError):  # la salida de errores se cerró: el avance se apaga, la revisión sigue
            self._activo = False

    def _dibujar(self) -> None:
        linea = self._linea()
        ancho = len(linea)
        relleno = " " * max(0, self._largo - ancho)
        self._escribir("\r" + pintar(linea, "sec", self._color, self._claro) + relleno)
        self._largo = max(ancho, 0)
        self._ultimo_dibujo = self._reloj()

    def cerrar(self) -> None:
        """Borra la línea (si se dibujó) y no vuelve a escribir."""
        if self._largo and self._flujo is not None:
            self._activo = True  # que el borrado se intente aunque un dibujo anterior haya fallado
            self._escribir("\r" + " " * self._largo + "\r")
        self._activo = False
        self._largo = 0
