"""``agentreach doctor``: comprobaciones de SOLO LECTURA de la terminal y del entorno (Historia 13c).

Siete comprobaciones, en este orden fijo: (1) versión de Python, (2) permisos de lectura, (3) codificación de la consola,
(4) color, (5) Unicode, (6) idioma, (7) ancho. Cada una dice «bien», «aviso» o «falla» con una frase de qué hacer. El
``doctor`` no escribe archivos, no lanza procesos y no arregla nada: solo informa. Los avisos no cuentan para el código de salida;
una falla sí (código 1).

Qué es una falla (decisión de la Historia 13c): algo que impide leer el reporte tal como sale: Python más viejo que 3.12, una
carpeta sin permiso de lectura, una consola que no puede escribir letras con tilde, una consola de terminal que no activó los
colores, o una consola que no puede escribir los símbolos del reporte. Un «sin color» elegido (``NO_COLOR``, redirección) es un aviso.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from agentreach.contracts import Idioma
from agentreach.core.catalogo_explicaciones import Tono
from agentreach.reporting.formato import Color, ajustar, pintar

__all__ = ["FRASE_FINAL", "Comprobacion", "Entorno", "Estado", "codigo_de_salida", "comprobar", "formatear"]

PYTHON_MINIMO = (3, 12)
SIMBOLOS = "■▲◊○√→"
FRASE_FINAL = {
    Idioma.ES: "AgentReach no modifica nada ni ejecuta ningún programa.",
    Idioma.EN: "AgentReach does not modify anything or run any program.",
}


class Estado(Enum):
    BIEN = "bien"
    AVISO = "aviso"
    FALLA = "falla"


@dataclass(frozen=True, slots=True)
class Entorno:
    """Lo que se mide del entorno. Todo entra por parámetro: así las pruebas simulan cualquier consola."""

    python: tuple[int, int, int]
    carpeta: str
    carpeta_indicada: bool
    codificacion: str
    es_terminal: bool
    columnas: int
    env: Mapping[str, str]
    plataforma: str
    color: Color
    color_activado: bool  # False: en Windows, no se pudo activar el modo de secuencias de la consola
    idioma: Idioma
    origen_idioma: str  # "opcion", "variable", "regional" o "defecto"
    color_opcion: str = "auto"  # lo que se pidió con --color


@dataclass(frozen=True, slots=True)
class Comprobacion:
    clave: str
    estado: Estado
    detalle: str
    consejo: str | None = None


_NOMBRES: dict[str, dict[Idioma, str]] = {
    "python": {Idioma.ES: "Python", Idioma.EN: "Python"},
    "permisos": {Idioma.ES: "Permisos de lectura", Idioma.EN: "Read permissions"},
    "codificacion": {Idioma.ES: "Codificación de consola", Idioma.EN: "Console encoding"},
    "color": {Idioma.ES: "Color", Idioma.EN: "Color"},
    "unicode": {Idioma.ES: "Unicode", Idioma.EN: "Unicode"},
    "idioma": {Idioma.ES: "Idioma", Idioma.EN: "Language"},
    "ancho": {Idioma.ES: "Ancho de la terminal", Idioma.EN: "Terminal width"},
}
_ORIGEN = {
    "opcion": {Idioma.ES: "la opción --idioma", Idioma.EN: "the --idioma option"},
    "variable": {Idioma.ES: "AGENTREACH_IDIOMA", Idioma.EN: "AGENTREACH_IDIOMA"},
    "regional": {Idioma.ES: "la configuración regional", Idioma.EN: "regional settings"},
    "defecto": {Idioma.ES: "el valor por defecto", Idioma.EN: "the default"},
}
_IDIOMA = {Idioma.ES: {Idioma.ES: "español", Idioma.EN: "Spanish"}, Idioma.EN: {Idioma.ES: "inglés", Idioma.EN: "English"}}

# (clave, qué) -> {idioma: texto} o, para el consejo en español, {tono: texto}
_CONSEJOS_ES: dict[str, tuple[str, str]] = {  # (cercano, formal)
    "python": ("Instala Python 3.12 o más reciente.", "Instale Python 3.12 o más reciente."),
    "permisos": ("Comprueba que tienes permiso de lectura en esa carpeta.", "Compruebe que tiene permiso de lectura en esa carpeta."),
    "codificacion": ("Usa Windows Terminal o ejecuta con --ascii.", "Use Windows Terminal o ejecute con --ascii."),
    "color_falla": ("Usa Windows Terminal o ejecuta con --color nunca.", "Use Windows Terminal o ejecute con --color nunca."),
    "color_aviso": ("Si quieres color, quita NO_COLOR o ejecuta con --color siempre.", "Si desea color, quite NO_COLOR o ejecute con --color siempre."),
    "unicode": ("Usa Windows Terminal o ejecuta con --ascii.", "Use Windows Terminal o ejecute con --ascii."),
    "ancho": ("Agranda la ventana para que las líneas no se partan.", "Agrande la ventana para que las líneas no se partan."),
}
_CONSEJOS_EN: dict[str, str] = {
    "python": "Install Python 3.12 or newer.",
    "permisos": "Check that you have read permission on that folder.",
    "codificacion": "Use Windows Terminal or run with --ascii.",
    "color_falla": "Use Windows Terminal or run with --color nunca.",
    "color_aviso": "If you want color, remove NO_COLOR or run with --color siempre.",
    "unicode": "Use Windows Terminal or run with --ascii.",
    "ancho": "Make the window wider so lines do not break.",
}
_INTRO = {
    Idioma.ES: "Comprobación de solo lectura de este equipo.",
    Idioma.EN: "Read-only check of this computer.",
}
_RESUMEN = {
    Idioma.ES: "{bien} comprobaciones correctas, {avisos} avisos, {fallos} fallos.",
    Idioma.EN: "{bien} checks passed, {avisos} warnings, {fallos} failures.",
}
_SALIDA = {
    Idioma.ES: ("Código de salida: 0 (sin fallos).", "Código de salida: 1 (hay fallos)."),
    Idioma.EN: ("Exit code: 0 (no failures).", "Exit code: 1 (there are failures)."),
}
_PALABRA = {
    Estado.BIEN: {Idioma.ES: "BIEN", Idioma.EN: "OK"},
    Estado.AVISO: {Idioma.ES: "AVISO", Idioma.EN: "WARNING"},
    Estado.FALLA: {Idioma.ES: "FALLO", Idioma.EN: "FAILURE"},
}


def _consejo(clave: str, idioma: Idioma, tono: Tono) -> str:
    if idioma is Idioma.EN:
        return _CONSEJOS_EN[clave]
    cercano, formal = _CONSEJOS_ES[clave]
    return formal if tono is Tono.FORMAL else cercano


def _puede_escribir(codificacion: str, texto: str) -> bool:
    try:
        texto.encode(codificacion)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def _leer_carpeta(carpeta: str) -> bool:
    """¿Dice el sistema que la carpeta se puede leer? Solo pregunta los permisos: NO lista ni abre nada de la carpeta
    (el ``doctor`` no pide permiso de lectura, así que no puede mirar dentro)."""
    try:
        return os.path.isdir(carpeta) and os.access(carpeta, os.R_OK | os.X_OK)
    except OSError:
        return False


def comprobar(e: Entorno, tono: Tono = Tono.CERCANO) -> list[Comprobacion]:
    """Las siete comprobaciones, en orden fijo. Nunca lanza."""
    i = e.idioma
    resultados: list[Comprobacion] = []
    v = ".".join(str(n) for n in e.python)
    if e.python[:2] >= PYTHON_MINIMO:
        resultados.append(Comprobacion("python", Estado.BIEN, f"{v} ({'se necesita 3.12 o más' if i is Idioma.ES else '3.12 or newer is needed'})"))
    else:
        resultados.append(Comprobacion("python", Estado.FALLA, f"{v} ({'se necesita 3.12 o más' if i is Idioma.ES else '3.12 or newer is needed'})",
                                       _consejo("python", i, tono)))
    sujeto = ("la carpeta indicada" if e.carpeta_indicada else "la carpeta actual") if i is Idioma.ES else (
        "the folder you gave" if e.carpeta_indicada else "the current folder")
    if _leer_carpeta(e.carpeta):
        resultados.append(Comprobacion("permisos", Estado.BIEN, f"{'puede leer' if i is Idioma.ES else 'can read'} {sujeto}"))
    else:
        resultados.append(Comprobacion("permisos", Estado.FALLA, f"{'no puede leer' if i is Idioma.ES else 'cannot read'} {sujeto}",
                                       _consejo("permisos", i, tono)))
    enc = e.codificacion or "utf-8"  # un flujo sin codificación declarada (como un StringIO) no es una consola rota
    if enc.lower().replace("-", "") in ("utf8", "utf8sig"):
        resultados.append(Comprobacion("codificacion", Estado.BIEN, enc))
    elif _puede_escribir(enc, "áéíóúñ"):
        resultados.append(Comprobacion("codificacion", Estado.AVISO, f"{enc} ({'no es UTF-8' if i is Idioma.ES else 'not UTF-8'})",
                                       _consejo("codificacion", i, tono)))
    else:
        resultados.append(Comprobacion(
            "codificacion", Estado.FALLA,
            f"{enc} {'no puede escribir letras con tilde' if i is Idioma.ES else 'cannot write accented letters'}",
            _consejo("codificacion", i, tono)))
    if e.es_terminal and e.plataforma == "win32" and not e.color_activado and e.color is Color.NINGUNO:
        resultados.append(Comprobacion("color", Estado.FALLA,
                                       "la consola no activó los colores" if i is Idioma.ES else "the console did not turn colors on",
                                       _consejo("color_falla", i, tono)))
    elif e.color is Color.NINGUNO:
        motivo = ("--color nunca" if e.color_opcion == "nunca" else "NO_COLOR" if e.env.get("NO_COLOR") else (
            "TERM=dumb" if e.env.get("TERM") == "dumb" else (
                "la salida no es una terminal" if i is Idioma.ES else "the output is not a terminal")))
        resultados.append(Comprobacion("color", Estado.AVISO, f"{'sin color' if i is Idioma.ES else 'no color'} ({motivo})",
                                       _consejo("color_aviso", i, tono)))
    else:
        detalle = "24 bits" if e.color is Color.DE_24_BITS else ("16 colores" if i is Idioma.ES else "16 colors")
        resultados.append(Comprobacion("color", Estado.BIEN, detalle))
    if _puede_escribir(enc, SIMBOLOS):
        resultados.append(Comprobacion("unicode", Estado.BIEN,
                                       f"{'puede escribir' if i is Idioma.ES else 'can write'} {' '.join(SIMBOLOS)}"))
    else:
        resultados.append(Comprobacion(
            "unicode", Estado.FALLA,
            "no puede escribir los símbolos; se usarán marcas ASCII" if i is Idioma.ES else "cannot write the symbols; ASCII marks will be used",
            _consejo("unicode", i, tono)))
    resultados.append(Comprobacion(
        "idioma", Estado.BIEN, f"{_IDIOMA[i][i]} ({'de' if i is Idioma.ES else 'from'} {_ORIGEN[e.origen_idioma][i]})"))
    if e.columnas >= 60:
        resultados.append(Comprobacion("ancho", Estado.BIEN, f"{e.columnas} {'columnas' if i is Idioma.ES else 'columns'}"))
    else:
        resultados.append(Comprobacion(
            "ancho", Estado.AVISO,
            f"{e.columnas} {'columnas (se usarán 60 como mínimo)' if i is Idioma.ES else 'columns (60 will be used as a minimum)'}",
            _consejo("ancho", i, tono)))
    return resultados


def codigo_de_salida(resultados: list[Comprobacion]) -> int:
    """0 si ninguna falla; 1 si alguna falla. Los avisos no cuentan."""
    return 1 if any(r.estado is Estado.FALLA for r in resultados) else 0


def formatear(
    resultados: list[Comprobacion],
    idioma: Idioma,
    version: str,
    *,
    ancho: int = 80,
    ascii_: bool = False,
    color: Color = Color.NINGUNO,
    claro: bool = False,
    banner: list[str] | None = None,
    simbolos_ascii: bool | None = None,
) -> str:
    """El texto del ``doctor``. Símbolo y palabra siempre; el fallo usa ámbar, nunca rojo (el rojo es solo «comprobado»)."""
    marcas = ascii_ if simbolos_ascii is None else (simbolos_ascii or ascii_)
    simbolo = {Estado.BIEN: "[ok]" if marcas else "√", Estado.AVISO: "[!]" if marcas else "▲", Estado.FALLA: "[!!]" if marcas else "■"}
    rol = {Estado.BIEN: "ok", Estado.AVISO: "potencial", Estado.FALLA: "potencial"}
    lineas: list[str] = list(banner or [f"AGENT REACH  doctor  v{version}"])
    lineas += ["", _INTRO[idioma], ""]
    for r in resultados:
        nombre = _NOMBRES[r.clave][idioma]
        palabra = "" if r.estado is Estado.BIEN else f"{_PALABRA[r.estado][idioma]}  "
        cabeza = f"{simbolo[r.estado]} {palabra}{nombre:<22} {r.detalle}"
        lineas.extend(pintar(linea, rol[r.estado], color, claro) for linea in ajustar(cabeza, ancho, 2, 6))
        if r.consejo:
            lineas.extend(ajustar(r.consejo, ancho, 6, 6))
    bien = sum(r.estado is Estado.BIEN for r in resultados)
    avisos = sum(r.estado is Estado.AVISO for r in resultados)
    fallos = sum(r.estado is Estado.FALLA for r in resultados)
    lineas += ["", _RESUMEN[idioma].format(bien=bien, avisos=avisos, fallos=fallos), "", FRASE_FINAL[idioma]]
    lineas.append(_SALIDA[idioma][codigo_de_salida(resultados)])
    texto = "\n".join(lineas) + "\n"
    if ascii_:
        import unicodedata

        texto = "".join(c for c in unicodedata.normalize("NFKD", texto.replace("·", "-")) if not unicodedata.combining(c))
        texto = "".join(c if ord(c) < 128 else "?" for c in texto)
    return texto
