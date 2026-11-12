"""Lector propio de la configuración de git, fiel a cómo la lee git, que NUNCA ejecuta nada.

Reemplaza a cualquier llamada a ``git``: una carpeta que trae su ``.git`` puede llevar un
``core.fsmonitor`` que ejecuta un programa en cuanto alguien consulta git, así que AgentReach solo
lee el texto. Regla de oro: ante la duda, ``ConfigNoInterpretable`` (el llamador reporta TH-20).

Qué entiende (lo mismo que git):

- ``[sección]``, ``[sección "subsección"]`` (con ``\\\\`` y ``\\"``) y la forma antigua
  ``[sección.subsección]`` (la subsección va en minúsculas). Sección y clave no distinguen mayúsculas.
- Comentarios con ``;`` y ``#`` (línea entera o tras el valor, fuera de comillas).
- Valores con comillas, escapes ``\\n \\t \\b \\\\ \\"`` y continuación de línea con ``\\`` al final.
- Variable en la misma línea que el encabezado y clave sin ``=`` (valor verdadero).
- Marca BOM al inicio y fin de línea de Windows.

La función ``leer_con_includes`` sigue ``include.path`` e ``includeIf.*.path`` (todos, sin evaluar la
condición: ante la duda se sigue) con tope de profundidad y detección de ciclos.
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from dataclasses import dataclass, field

from agentreach.contracts import ArchivoNoLegible
from agentreach.contracts.no_revisado import MotivoNoRevisado

PROFUNDIDAD_MAXIMA_INCLUDE = 10
_BOM = chr(0xFEFF)  # marca de orden de bytes que git acepta al inicio del archivo

_NOMBRE = re.compile(r"[A-Za-z][A-Za-z0-9-]*")
_SECCION = re.compile(r"[A-Za-z0-9.-]+")
_ENTERO = re.compile(r"[+-]?\d+[kKmMgG]?")
_ESPACIOS = " \t\r\f\v"


class ConfigNoInterpretable(Exception):
    """El texto no se pudo interpretar. El mensaje nunca copia texto del archivo."""


@dataclass(frozen=True, slots=True)
class Entrada:
    """Una variable de la configuración. El valor existe solo para decidir; no sale en ``repr``."""

    seccion: str  # en minúsculas
    subseccion: str | None
    nombre: str  # en minúsculas
    valor: str | None = field(repr=False)  # None: clave sin "=" (verdadero)
    linea: int
    ruta: str = ""  # archivo del que viene (lo rellena ``leer_con_includes``)
    peculiar: bool = False  # sección o clave con mayúsculas, o valor con continuación de línea: el lector aún no se validó contra git


@dataclass(frozen=True, slots=True)
class Problema:
    ruta: str
    motivo: MotivoNoRevisado
    th20: bool = True  # False: solo se informa como no revisado (no es un fallo de lectura de git)


@dataclass(frozen=True, slots=True)
class Lectura:
    entradas: tuple[Entrada, ...]
    problemas: tuple[Problema, ...]


def es_booleano_git(valor: str | None) -> bool | None:
    """``True``/``False`` si git leería el valor como booleano; ``None`` si no lo es (un programa, un texto).

    Git acepta true/yes/on, false/no/off, un entero (distinto de 0 es verdadero) y el valor vacío (falso).
    Una clave sin ``=`` (``None``) es verdadera.
    """
    if valor is None:
        return True
    v = valor.strip().lower()
    if v == "":
        return False
    if v in ("true", "yes", "on"):
        return True
    if v in ("false", "no", "off"):
        return False
    if _ENTERO.fullmatch(v):
        digitos = re.sub(r"[^0-9]", "", v)
        if len(digitos) > 18:  # un entero desmesurado no es un booleano que git acepte
            return None
        return int(digitos) != 0
    return None


def parsear_config(texto: str) -> list[Entrada]:
    """Lee el texto de un archivo de configuración. Lanza ``ConfigNoInterpretable`` ante la duda."""
    texto = texto.removeprefix(_BOM)
    lineas = [ln.removesuffix("\r") for ln in texto.split("\n")]
    entradas: list[Entrada] = []
    seccion: str | None = None
    subseccion: str | None = None
    seccion_peculiar = False
    i = 0
    while i < len(lineas):
        s = lineas[i].lstrip(_ESPACIOS)
        numero = i + 1
        if not s or s[0] in ";#":
            i += 1
            continue
        if s[0] == "[":
            crudo = re.match(r"\[\s*([^\]\s\"]+)", s)
            seccion_peculiar = bool(crudo) and crudo.group(1) != crudo.group(1).lower()  # type: ignore[union-attr]
            seccion, subseccion, resto = _encabezado(s)
            s = resto.lstrip(_ESPACIOS)
            if not s or s[0] in ";#":
                i += 1
                continue
        if seccion is None:
            raise ConfigNoInterpretable("variable fuera de una sección")
        crudo_nombre = _NOMBRE.match(s)
        inicial = i
        nombre, valor, i = _variable(lineas, i, s)
        peculiar = seccion_peculiar or i != inicial or (bool(crudo_nombre) and _nombre_inusual(crudo_nombre.group(0)))  # type: ignore[union-attr]
        entradas.append(Entrada(seccion, subseccion, nombre, valor, numero, peculiar=peculiar))
        i += 1
    return entradas


def _nombre_inusual(nombre: str) -> bool:
    """``sshCommand`` y ``hooksPath`` son la forma normal (camelCase); ``FsMonitor`` o ``FSMONITOR`` no: git los lee igual, el lector aún no se validó."""
    return nombre[:1].isupper() or (len(nombre) > 1 and nombre == nombre.upper())


def _encabezado(s: str) -> tuple[str, str | None, str]:
    m = _SECCION.match(s, 1)
    if m is None:
        raise ConfigNoInterpretable("encabezado de sección inválido")
    nombre, pos = m.group(0), m.end()
    sub: str | None = None
    if pos < len(s) and s[pos] in _ESPACIOS:
        while pos < len(s) and s[pos] in _ESPACIOS:
            pos += 1
        if pos >= len(s) or s[pos] != '"':
            raise ConfigNoInterpretable("subsección sin comillas")
        pos += 1
        partes: list[str] = []
        while True:
            if pos >= len(s):
                raise ConfigNoInterpretable("subsección sin cerrar")
            c = s[pos]
            if c == '"':
                pos += 1
                break
            if c == "\\":
                pos += 1
                if pos >= len(s):
                    raise ConfigNoInterpretable("subsección sin cerrar")
                c = s[pos]  # tras una barra, el carácter va tal cual (se descarta la barra)
            partes.append(c)
            pos += 1
        sub = "".join(partes)
    elif "." in nombre:  # forma antigua [sección.subsección]: todo en minúsculas
        nombre, _, sub = nombre.partition(".")
        sub = sub.lower()
    if pos >= len(s) or s[pos] != "]":
        raise ConfigNoInterpretable("encabezado de sección sin cerrar")
    if not nombre:
        raise ConfigNoInterpretable("sección sin nombre")
    return nombre.lower(), sub, s[pos + 1:]


_ESCAPES = {"n": "\n", "t": "\t", "b": "\b", "\\": "\\", '"': '"'}


def _variable(lineas: list[str], i: int, s: str) -> tuple[str, str | None, int]:
    """Lee ``nombre [= valor]`` desde ``s`` (el resto de la línea ``i``). Devuelve la línea donde termina."""
    m = _NOMBRE.match(s)
    if m is None:
        raise ConfigNoInterpretable("nombre de variable inválido")
    nombre, pos = m.group(0).lower(), m.end()
    while pos < len(s) and s[pos] in _ESPACIOS:
        pos += 1
    if pos >= len(s) or s[pos] in ";#":
        return nombre, None, i
    if s[pos] != "=":
        raise ConfigNoInterpretable("línea de configuración inválida")
    pos += 1
    while pos < len(s) and s[pos] in _ESPACIOS:
        pos += 1
    partes: list[str] = []
    espera = ""  # espacios sin comillas: se descartan si son los últimos
    en_comillas = False
    actual = s
    while True:
        if pos >= len(actual):
            break
        c = actual[pos]
        if c == "\\":
            if pos == len(actual) - 1:  # continuación de línea
                i += 1
                if i >= len(lineas):
                    raise ConfigNoInterpretable("continuación al final del archivo")
                actual, pos = lineas[i], 0
                continue
            pos += 1
            e = actual[pos]
            if e not in _ESCAPES:
                raise ConfigNoInterpretable("escape desconocido")
            partes.append(espera + _ESCAPES[e])
            espera = ""
            pos += 1
        elif c == '"':
            en_comillas = not en_comillas
            partes.append(espera)
            espera = ""
            pos += 1
        elif en_comillas:
            partes.append(c)
            pos += 1
        elif c in ";#":
            break
        elif c in _ESPACIOS:
            espera += c
            pos += 1
        else:
            partes.append(espera + c)
            espera = ""
            pos += 1
    if en_comillas:
        raise ConfigNoInterpretable("comillas sin cerrar")
    return nombre, "".join(partes), i


_Leer = Callable[[str], str]
_Existe = Callable[[str], bool]


def leer_con_includes(
    leer: _Leer,
    existe: _Existe,
    ruta: str,
    profundidad_maxima: int = PROFUNDIDAD_MAXIMA_INCLUDE,
) -> Lectura:
    """Lee ``ruta`` y sigue sus ``include``. Nunca lanza: lo que falla queda en ``problemas``.

    ``leer`` es la lectura segura (puede lanzar ``ArchivoNoLegible``) y ``existe`` dice si hay archivo
    (git ignora en silencio un include que no existe).
    """
    entradas: list[Entrada] = []
    problemas: list[Problema] = []
    _leer_uno(leer, existe, ruta, [], entradas, problemas, profundidad_maxima, es_raiz=True)
    return Lectura(tuple(entradas), tuple(problemas))


def _clave(ruta: str) -> str:
    return os.path.normcase(os.path.normpath(ruta))


def _leer_uno(leer: _Leer, existe: _Existe, ruta: str, cadena: list[str], entradas: list[Entrada],
              problemas: list[Problema], maximo: int, es_raiz: bool = False) -> None:
    if len(cadena) > maximo or _clave(ruta) in cadena:  # demasiado profundo, o un ciclo
        problemas.append(Problema(ruta, MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA))
        return
    if not es_raiz and not existe(ruta):
        return  # git ignora un include que no existe
    try:
        texto = leer(ruta)
        propias = parsear_config(texto)
    except ArchivoNoLegible as error:
        problemas.append(Problema(ruta, error.motivo))
        return
    except (ConfigNoInterpretable, RecursionError, ValueError):
        problemas.append(Problema(ruta, MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE))
        return
    cadena = [*cadena, _clave(ruta)]
    for e in propias:
        entradas.append(Entrada(e.seccion, e.subseccion, e.nombre, e.valor, e.linea, ruta, e.peculiar))
        if e.nombre == "path" and e.seccion in ("include", "includeif") and e.valor:
            if e.valor.startswith("~"):  # depende de la carpeta personal: no se sigue
                # la ruta que se informa es la del archivo que incluye, nunca texto escrito en él
                problemas.append(Problema(ruta, MotivoNoRevisado.ARCHIVO_ILEGIBLE, th20=False))
                continue
            incluida = os.path.normpath(os.path.join(os.path.dirname(ruta), e.valor))
            _leer_uno(leer, existe, incluida, cadena, entradas, problemas, maximo)
