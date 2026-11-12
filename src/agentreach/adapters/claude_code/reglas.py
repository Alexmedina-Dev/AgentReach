"""Reglas de permisos de Claude Code: cómo se leen y cómo se comparan con una ruta.

Una regla es ``Herramienta`` o ``Herramienta(especificador)``, por ejemplo ``Read(./.env)`` o
``Bash(git diff:*)``. Para ``Read`` el especificador es un patrón de ruta (glob) con estas formas:

- ``//ruta``: ruta absoluta. ``~/ruta``: relativa a la carpeta personal.
- ``./ruta`` o ``ruta``: relativa a la carpeta del proyecto. ``/ruta``: [SUPUESTO] también relativa al
  proyecto (a la carpeta personal si la regla viene del archivo de usuario).
- ``*`` no cruza carpetas, ``**`` sí, ``?`` es un carácter. Un patrón que nombra una carpeta cubre su contenido.

La precedencia entre reglas es ``deny`` > ``ask`` > ``allow``; entre archivos de configuración manda la
gestionada, luego la local, luego la del proyecto y al final la de usuario.
"""

from __future__ import annotations

import os
import re

PRECEDENCIA_ACCION = ("deny", "ask", "allow")
PRECEDENCIA_FUENTE = ("gestionada", "local", "proyecto", "usuario")
_REGLA = re.compile(r"^([A-Za-z_][\w.\-:]*)(?:\((.*))?$", re.DOTALL)


def parsear_regla(texto: str) -> tuple[str, str | None] | None:
    """(herramienta, especificador) o ``None`` si la regla está vacía o no tiene forma de regla."""
    limpio = texto.strip()
    if not limpio:
        return None
    m = _REGLA.match(limpio)
    if m is None:
        return None
    especificador = m.group(2)
    if especificador is not None:
        especificador = especificador.removesuffix(")")
    return m.group(1), especificador


def _glob_a_regex(patron: str) -> str:
    salida: list[str] = []
    i = 0
    while i < len(patron):
        c = patron[i]
        if patron.startswith("**/", i):
            salida.append("(?:.*/)?")
            i += 3
            continue
        if patron.startswith("**", i):
            salida.append(".*")
            i += 2
            continue
        if c == "*":
            salida.append("[^/]*")
        elif c == "?":
            salida.append("[^/]")
        else:
            salida.append(re.escape(c))
        i += 1
    return "".join(salida)


def compilar(patron: str, ignorar_mayusculas: bool) -> re.Pattern[str]:
    """Compila el patrón; además de la ruta exacta, cubre todo lo que haya dentro si nombra una carpeta."""
    cuerpo = _glob_a_regex(patron.rstrip("/"))
    return re.compile(f"(?:{cuerpo})(?:/.*)?", re.IGNORECASE if ignorar_mayusculas else 0)


def _posix(ruta: str) -> str:
    return ruta.replace("\\", "/")


def relativa_a(ruta: str, base: str) -> str | None:
    """Ruta relativa y con ``/`` si ``ruta`` está dentro de ``base``; si no, ``None``."""
    try:
        rel = os.path.relpath(ruta, base)
    except ValueError:  # otra unidad
        return None
    rel = _posix(rel)
    if rel == ".." or rel.startswith("../"):
        return None
    return "" if rel == "." else rel


_UNIDAD = re.compile(r"^([A-Za-z]):/")


def _a_forma_de_claude(ruta: str) -> str:
    """En Windows Claude Code normaliza ``C:\\Users\\x`` a ``/c/Users/x`` antes de comparar (documentación de permisos)."""
    posix = _posix(ruta)
    m = _UNIDAD.match(posix)
    return f"/{m.group(1).lower()}/{posix[3:]}" if m else posix


def patron_indeterminable(patron: str) -> bool:
    """Formas que este lector no interpreta con certeza: vacío, negación ``!``, clases ``[..]``, llaves ``{..}``, barra invertida y
    segmentos ``.`` o ``..`` (salvo un ``./`` inicial): ``././.env`` y ``sub/../.env`` no tienen un significado documentado.

    En gitignore ``\\`` escapa el carácter siguiente y ``[``/``{`` tienen significado propio: no se adivina.
    """
    if (not patron) or patron.startswith("!") or any(c in patron for c in "[]{}\\"):
        return True
    if patron in (".", "./"):
        return False  # toda la carpeta de trabajo: forma válida
    resto = patron.removeprefix("./")  # un solo ``./`` inicial es la forma documentada
    return any(segmento in (".", "..") for segmento in resto.replace("\\", "/").split("/"))  # ``././x`` y ``a/../x``: no se adivina


def _es_nombre_simple(segmento: str) -> bool:
    return bool(segmento) and "**" not in segmento


def _real(ruta: str) -> str:
    try:
        return os.path.realpath(ruta)
    except (OSError, ValueError):
        return ruta


def coincide(especificador: str, ruta: str, proyecto: str, home: str, fuente: str, ignorar_mayusculas: bool) -> bool | None:
    """¿El patrón alcanza a ``ruta``, escrita como viene o ya resuelta (nombre largo, enlaces)? Ver ``_coincide``."""
    veredictos = [_coincide(especificador, ruta, proyecto, home, fuente, ignorar_mayusculas)]
    real = (_real(ruta), _real(proyecto), _real(home))
    if real != (os.path.abspath(ruta), os.path.abspath(proyecto), os.path.abspath(home)):
        veredictos.append(_coincide(especificador, *real[:1], *real[1:], fuente, ignorar_mayusculas))
    if True in veredictos:
        return True
    return None if None in veredictos else False


def _coincide(especificador: str, ruta: str, proyecto: str, home: str, fuente: str, ignorar_mayusculas: bool) -> bool | None:
    """¿El patrón de una regla ``Read`` alcanza a ``ruta``? ``None`` si el patrón no se puede interpretar con certeza.

    Sigue la sintaxis gitignore que documenta Claude Code: un nombre sin barra (``.env``, ``*.env``) coincide en cualquier
    profundidad bajo la carpeta de trabajo; ``nombre/**`` (una sola carpeta) coincide en cualquier profundidad; el resto se ancla
    donde se escribió. ``//ruta`` es absoluta, ``~/ruta`` parte de la carpeta personal y ``/ruta`` parte de la carpeta del archivo
    de configuración (el proyecto, o ``~/.claude`` en la configuración de usuario).
    """
    patron = especificador.strip()
    if patron_indeterminable(patron):
        return None
    ruta = os.path.abspath(ruta)
    anclado = False
    if patron.startswith("//"):  # ruta absoluta; en Windows ``//c/**/.env`` (o la forma con unidad ``//C:/``)
        candidata = _a_forma_de_claude(ruta).lstrip("/")
        patron = patron[2:]
        m = _UNIDAD.match(patron)
        patron = f"{m.group(1).lower()}/{patron[3:]}" if m else patron.lstrip("/")
        anclado = True
    elif patron.startswith("~/"):
        if not home:  # sin carpeta personal utilizable no se adivina (una cadena vacía caería en el directorio actual)
            return None
        candidata, patron, anclado = relativa_a(ruta, home), patron[2:], True
    elif patron.startswith("/"):
        if fuente == "gestionada":
            return None  # a qué carpeta se ancla una regla gestionada no está documentado: no se adivina
        base = os.path.join(home, ".claude") if fuente == "usuario" else proyecto
        candidata, patron, anclado = relativa_a(ruta, base), patron[1:], True
    else:
        candidata, patron = relativa_a(ruta, proyecto), patron.removeprefix("./")
    if candidata is None or candidata == "":
        return False
    if patron in ("", "."):  # "./", "." o "/": la carpeta base entera
        return True
    patron = patron.rstrip("/")
    segmentos = patron.split("/")
    if not anclado and (len(segmentos) == 1 or (_es_nombre_simple(segmentos[0]) and all(s in ("**", "") for s in segmentos[1:]))):
        patron = "**/" + patron  # gitignore: un nombre sin barra (o ``nombre/**``) coincide en cualquier profundidad
    return compilar(patron, ignorar_mayusculas).fullmatch(candidata) is not None
