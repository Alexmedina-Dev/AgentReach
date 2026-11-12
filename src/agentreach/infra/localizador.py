"""Localizador de claves: dice en qué línea (y columna) está una clave en un archivo de configuración.

Para qué sirve: cada hallazgo de AgentReach debe indicar archivo y línea, pero los lectores
estándar (``json`` y ``tomllib``) no entregan números de línea. Este módulo recorre el texto por su
cuenta y devuelve solo POSICIONES, nunca valores.

Reglas que cumple:

- Solo biblioteca estándar.
- No abre archivos: recibe el texto ya leído. Quien lo llama decide qué archivos abrir.
- Nunca devuelve, guarda ni registra valores. Los valores se saltan sin copiarlos. De cada archivo
  solo se retienen nombres de claves y desplazamientos numéricos.
- Si no puede estar seguro (texto mal formado, clave repetida, ruta que cae dentro de algo que el
  escáner no recorre), devuelve ``None``. Nunca adivina.

Formatos admitidos (parámetro ``formato``): ``"json"``, ``"jsonc"``, ``"toml"``, ``"env"``.

- ``json`` y ``jsonc`` se tratan igual: se toleran comentarios ``//`` y ``/* */`` y comas finales,
  porque los archivos de agentes (p. ej. opencode.json) suelen traerlos.
- ``env``: archivos de tipo ``NOMBRE=valor``. De cada línea solo se mira el nombre.

Ruta de la clave (``ruta_clave``): tupla de pasos. Un ``str`` es el nombre de una clave y un ``int``
es el índice (desde 0) dentro de un arreglo. Ejemplos:

- ``("permissions", "deny", 0)``: primer elemento del arreglo ``permissions.deny``.
- ``("permission", "bash")``: clave anidada.
- ``("SERVICE_TOKEN",)``: variable en un archivo ``.env``.

Línea y columna empiezan en 1. La columna cuenta caracteres, no bytes. Los saltos de línea
reconocidos son ``\\n``, ``\\r\\n`` y ``\\r`` suelto.

Límites conocidos de TOML (en estos casos devuelve ``None``):

- Claves dentro de tablas en línea (``a = {b = 1}``) o de arreglos en línea (``a = [1, 2]``).
- Tablas definidas solo de forma implícita por claves con punto (``a.b = 1``) cuando se pregunta
  por la tabla ``("a",)``; la clave ``("a", "b")`` sí se localiza.
- Cualquier ruta que aparezca definida dos veces (TOML inválido) y cualquier texto que el
  escáner no entienda por completo.
"""

from __future__ import annotations

import re
from bisect import bisect_right

Paso = str | int
Posicion = tuple[int, int]

FORMATOS = ("json", "jsonc", "toml", "env")

_PROFUNDIDAD_MAXIMA = 100
_SALTO = re.compile(r"\r\n|\r|\n")


class _Ilegible(Exception):
    """El texto no se pudo recorrer con certeza; se traduce a ``None``."""


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------


def localizar_clave(texto: str, formato: str, ruta_clave: tuple[Paso, ...]) -> int | None:
    """Devuelve la línea (desde 1) de la clave indicada, o ``None`` si no se puede determinar."""
    posicion = localizar_posicion(texto, formato, ruta_clave)
    return None if posicion is None else posicion[0]


def localizar_posicion(texto: str, formato: str, ruta_clave: tuple[Paso, ...]) -> Posicion | None:
    """Como ``localizar_clave`` pero devuelve ``(línea, columna)``, ambas desde 1.

    Lanza ``ValueError`` solo si ``formato`` no es uno de ``FORMATOS`` (error de programación, no
    de datos). Con cualquier texto raro devuelve ``None``.
    """
    if formato not in FORMATOS:
        raise ValueError(f"Formato no admitido: {formato!r}. Use uno de {FORMATOS}.")
    if not ruta_clave or not isinstance(texto, str):
        return None
    for paso in ruta_clave:
        if isinstance(paso, bool) or not isinstance(paso, str | int):
            return None
    texto = texto.removeprefix("﻿")  # marca de orden de bytes: no cuenta como columna
    try:
        if formato in ("json", "jsonc"):
            desplazamiento = _buscar_json(texto, ruta_clave)
        elif formato == "toml":
            desplazamiento = _buscar_toml(texto, ruta_clave)
        else:
            desplazamiento = _buscar_env(texto, ruta_clave)
    except (_Ilegible, RecursionError):
        return None
    if desplazamiento is None:
        return None
    return _a_linea_columna(texto, desplazamiento)


def _a_linea_columna(texto: str, desplazamiento: int) -> Posicion:
    inicios = [0] + [m.end() for m in _SALTO.finditer(texto)]
    indice = bisect_right(inicios, desplazamiento) - 1
    return indice + 1, desplazamiento - inicios[indice] + 1


# ---------------------------------------------------------------------------
# JSON / JSONC
# ---------------------------------------------------------------------------

# Nodo: None (valor simple, no se guarda), ("obj", [(clave, desplazamiento, nodo)]) o
# ("arr", [(desplazamiento, nodo)]).
_NUMERO = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
_LITERAL = re.compile(r"true|false|null")


class _EscanerJson:
    def __init__(self, texto: str) -> None:
        self.t = texto
        self.i = 0

    def documento(self):
        self._blancos()
        nodo = self._valor(0)
        self._blancos()
        if self.i != len(self.t):
            raise _Ilegible
        return nodo

    def _blancos(self) -> None:
        t, n = self.t, len(self.t)
        while self.i < n:
            c = t[self.i]
            if c in " \t\r\n":
                self.i += 1
            elif t.startswith("//", self.i):
                fin = _SALTO.search(t, self.i)
                self.i = fin.start() if fin else n
            elif t.startswith("/*", self.i):
                fin = t.find("*/", self.i + 2)
                if fin < 0:
                    raise _Ilegible
                self.i = fin + 2
            else:
                return

    def _cadena(self) -> str:
        """Recorre una cadena y devuelve su texto decodificado (solo se usa para nombres de clave)."""
        t, n = self.t, len(self.t)
        inicio = self.i
        j = inicio + 1
        while j < n:
            c = t[j]
            if c == "\\":
                j += 2
            elif c == '"':
                self.i = j + 1
                return _decodificar_cadena_json(t[inicio : j + 1])
            elif c in "\r\n":
                raise _Ilegible
            else:
                j += 1
        raise _Ilegible

    def _valor(self, profundidad: int):
        if profundidad > _PROFUNDIDAD_MAXIMA or self.i >= len(self.t):
            raise _Ilegible
        c = self.t[self.i]
        if c == "{":
            return self._objeto(profundidad)
        if c == "[":
            return self._arreglo(profundidad)
        if c == '"':
            self._cadena()  # se descarta: es un valor
            return None
        for patron in (_NUMERO, _LITERAL):
            m = patron.match(self.t, self.i)
            if m:
                self.i = m.end()
                return None
        raise _Ilegible

    def _objeto(self, profundidad: int):
        entradas = []
        self.i += 1
        while True:
            self._blancos()
            if self.i >= len(self.t):
                raise _Ilegible
            if self.t[self.i] == "}":
                self.i += 1
                return ("obj", entradas)
            if self.t[self.i] != '"':
                raise _Ilegible
            donde = self.i
            clave = self._cadena()
            self._blancos()
            if self.i >= len(self.t) or self.t[self.i] != ":":
                raise _Ilegible
            self.i += 1
            self._blancos()
            entradas.append((clave, donde, self._valor(profundidad + 1)))
            self._blancos()
            if self.i < len(self.t) and self.t[self.i] == ",":
                self.i += 1
            elif self.i < len(self.t) and self.t[self.i] == "}":
                continue
            else:
                raise _Ilegible

    def _arreglo(self, profundidad: int):
        elementos = []
        self.i += 1
        while True:
            self._blancos()
            if self.i >= len(self.t):
                raise _Ilegible
            if self.t[self.i] == "]":
                self.i += 1
                return ("arr", elementos)
            donde = self.i
            elementos.append((donde, self._valor(profundidad + 1)))
            self._blancos()
            if self.i < len(self.t) and self.t[self.i] == ",":
                self.i += 1
            elif self.i < len(self.t) and self.t[self.i] == "]":
                continue
            else:
                raise _Ilegible


def _decodificar_cadena_json(literal: str) -> str:
    import json

    try:
        return json.loads(literal)
    except ValueError as error:
        raise _Ilegible from error


def _buscar_json(texto: str, ruta: tuple[Paso, ...]) -> int | None:
    nodo = _EscanerJson(texto).documento()  # valida todo el documento antes de responder
    for numero, paso in enumerate(ruta):
        ultimo = numero == len(ruta) - 1
        if nodo is None:
            return None
        tipo, contenido = nodo
        if isinstance(paso, str):
            if tipo != "obj":
                return None
            coincidencias = [e for e in contenido if e[0] == paso]
            if len(coincidencias) != 1:  # ausente o repetida: no se adivina
                return None
            _, donde, hijo = coincidencias[0]
        else:
            if tipo != "arr" or not 0 <= paso < len(contenido):
                return None
            donde, hijo = contenido[paso]
        if ultimo:
            return donde
        nodo = hijo
    return None


# ---------------------------------------------------------------------------
# .env  (solo se mira el nombre; el valor se salta sin copiarse)
# ---------------------------------------------------------------------------

_NOMBRE_ENV = re.compile(r"[A-Za-z_][A-Za-z0-9_.\-]*")


def _buscar_env(texto: str, ruta: tuple[Paso, ...]) -> int | None:
    if len(ruta) != 1 or not isinstance(ruta[0], str):
        return None
    objetivo = ruta[0]
    encontrados: list[int] = []
    comilla_abierta: str | None = None  # comilla de un valor de varias líneas aún sin cerrar
    inicio_linea = 0
    for salto in [*_SALTO.finditer(texto), None]:
        fin_linea = salto.start() if salto else len(texto)
        linea = texto[inicio_linea:fin_linea]
        if comilla_abierta is not None:
            if _cierra_comilla(linea, comilla_abierta):
                comilla_abierta = None
        else:
            sangria = len(linea) - len(linea.lstrip(" \t"))
            cuerpo = linea[sangria:]
            if cuerpo and not cuerpo.startswith("#"):
                desplazamiento = sangria
                if re.match(r"export[ \t]+", cuerpo):
                    desplazamiento += len(re.match(r"export[ \t]+", cuerpo).group())
                    cuerpo = linea[desplazamiento:]
                m = _NOMBRE_ENV.match(cuerpo)
                if m:
                    despues = cuerpo[m.end() :].lstrip(" \t")
                    if despues.startswith("="):
                        if m.group() == objetivo:
                            encontrados.append(inicio_linea + desplazamiento)
                        valor = despues[1:].lstrip(" \t")
                        if valor[:1] in ('"', "'") and not _cierra_comilla(valor[1:], valor[0]):
                            comilla_abierta = valor[0]
        if salto is None:
            break
        inicio_linea = salto.end()
    if comilla_abierta is not None:  # comilla sin cerrar al final del archivo: no es fiable
        raise _Ilegible
    return encontrados[0] if len(encontrados) == 1 else None


def _cierra_comilla(fragmento: str, comilla: str) -> bool:
    j = 0
    while j < len(fragmento):
        if comilla == '"' and fragmento[j] == "\\":
            j += 2
            continue
        if fragmento[j] == comilla:
            return True
        j += 1
    return False


# ---------------------------------------------------------------------------
# TOML
# ---------------------------------------------------------------------------

_CLAVE_TOML_SIMPLE = re.compile(r"[A-Za-z0-9_\-]+")
# Valor simple sin comillas: una sola palabra (número, booleano, fecha) o fecha con hora separada
# por espacio. Es deliberadamente estricto: ante la duda, el texto se considera ilegible.
_ESCALAR_TOML = re.compile(r"[^\s]+(?: [0-9:.+\-Zz]+)?")
_ESCAPES_TOML = {"b": "\b", "t": "\t", "n": "\n", "f": "\f", "r": "\r", '"': '"', "\\": "\\"}


class _EscanerToml:
    def __init__(self, texto: str) -> None:
        self.t = texto
        self.i = 0
        self.n = len(texto)
        self.encontrados: dict[tuple[Paso, ...], list[int]] = {}

    def _anotar(self, ruta: tuple[Paso, ...], donde: int) -> None:
        self.encontrados.setdefault(ruta, []).append(donde)

    def _espacios(self) -> None:
        while self.i < self.n and self.t[self.i] in " \t":
            self.i += 1

    def _fin_de_linea(self) -> None:
        """Tras una instrucción solo puede haber espacios, un comentario y el salto de línea."""
        self._espacios()
        if self.i < self.n and self.t[self.i] == "#":
            while self.i < self.n and self.t[self.i] not in "\r\n":
                self.i += 1
        if self.i < self.n and self.t[self.i] not in "\r\n":
            raise _Ilegible

    def recorrer(self) -> dict[tuple[Paso, ...], list[int]]:
        tabla: tuple[Paso, ...] = ()
        arreglos: dict[tuple[Paso, ...], int] = {}
        t = self.t
        while self.i < self.n:
            c = t[self.i]
            if c in " \t\r\n":
                self.i += 1
            elif c == "#":
                while self.i < self.n and t[self.i] not in "\r\n":
                    self.i += 1
            elif c == "[":
                tabla = self._encabezado(arreglos)
            else:
                inicio = self.i
                partes = self._clave_con_puntos()
                self._espacios()
                if self.i >= self.n or t[self.i] != "=":
                    raise _Ilegible
                self.i += 1
                self._espacios()
                self._saltar_valor()
                self._fin_de_linea()
                self._anotar(tabla + tuple(partes), inicio)
        return self.encontrados

    def _encabezado(self, arreglos: dict[tuple[Paso, ...], int]) -> tuple[Paso, ...]:
        inicio = self.i
        doble = self.t.startswith("[[", self.i)
        self.i += 2 if doble else 1
        partes = self._clave_con_puntos()
        self._espacios()
        cierre = "]]" if doble else "]"
        if not self.t.startswith(cierre, self.i):
            raise _Ilegible
        self.i += len(cierre)
        self._fin_de_linea()
        resuelta: list[Paso] = []
        for numero, parte in enumerate(partes):
            resuelta.append(parte)
            actual = tuple(resuelta)
            if actual in arreglos and not (doble and numero == len(partes) - 1):
                resuelta.append(arreglos[actual] - 1)
        if doble:
            base = tuple(resuelta)
            arreglos[base] = arreglos.get(base, 0) + 1
            resuelta.append(arreglos[base] - 1)
        ruta = tuple(resuelta)
        self._anotar(ruta, inicio)
        return ruta

    def _clave_con_puntos(self) -> list[str]:
        partes: list[str] = []
        while True:
            self._espacios()
            if self.i >= self.n:
                raise _Ilegible
            c = self.t[self.i]
            if c == '"':
                partes.append(self._clave_basica())
            elif c == "'":
                fin = self.t.find("'", self.i + 1)
                if fin < 0 or _SALTO.search(self.t, self.i, fin):
                    raise _Ilegible
                partes.append(self.t[self.i + 1 : fin])
                self.i = fin + 1
            else:
                m = _CLAVE_TOML_SIMPLE.match(self.t, self.i)
                if not m:
                    raise _Ilegible
                partes.append(m.group())
                self.i = m.end()
            self._espacios()
            if self.i < self.n and self.t[self.i] == ".":
                self.i += 1
                continue
            return partes

    def _clave_basica(self) -> str:
        t = self.t
        j = self.i + 1
        salida: list[str] = []
        while j < self.n:
            c = t[j]
            if c == '"':
                self.i = j + 1
                return "".join(salida)
            if c in "\r\n":
                raise _Ilegible
            if c == "\\":
                sig = t[j + 1 : j + 2]
                if sig in _ESCAPES_TOML:
                    salida.append(_ESCAPES_TOML[sig])
                    j += 2
                elif sig in ("u", "U"):
                    largo = 4 if sig == "u" else 8
                    hexa = t[j + 2 : j + 2 + largo]
                    try:
                        salida.append(chr(int(hexa, 16)))
                    except ValueError as error:
                        raise _Ilegible from error
                    j += 2 + largo
                else:
                    raise _Ilegible
            else:
                salida.append(c)
                j += 1
        raise _Ilegible

    # -- saltar valores sin copiarlos ------------------------------------

    def _saltar_cadena(self, j: int) -> int:
        """``j`` apunta a una comilla de apertura; devuelve la posición tras el cierre."""
        t = self.t
        comilla = t[j]
        if t.startswith(comilla * 3, j):
            j += 3
            while j < self.n:
                if comilla == '"' and t[j] == "\\":
                    j += 2
                elif t.startswith(comilla * 3, j):
                    j += 3
                    extra = 0
                    while j < self.n and t[j] == comilla and extra < 2:
                        j += 1
                        extra += 1
                    return j
                else:
                    j += 1
            raise _Ilegible
        j += 1
        while j < self.n:
            c = t[j]
            if c == "\\" and comilla == '"':
                j += 2
            elif c == comilla:
                return j + 1
            elif c in "\r\n":
                raise _Ilegible
            else:
                j += 1
        raise _Ilegible

    def _saltar_valor(self) -> None:
        t, j = self.t, self.i
        if j >= self.n or t[j] in "\r\n#":
            raise _Ilegible
        if t[j] in "\"'":
            self.i = self._saltar_cadena(j)
            return
        if t[j] in "[{":
            profundidad = 0
            while j < self.n:
                c = t[j]
                if c in "\"'":
                    j = self._saltar_cadena(j)
                    continue
                if c == "#":
                    while j < self.n and t[j] not in "\r\n":
                        j += 1
                    continue
                if c in "[{":
                    profundidad += 1
                elif c in "]}":
                    profundidad -= 1
                    if profundidad == 0:
                        self.i = j + 1
                        return
                j += 1
            raise _Ilegible
        while j < self.n and t[j] not in "\r\n#":
            j += 1
        if not _ESCALAR_TOML.fullmatch(t[self.i : j].strip()):
            raise _Ilegible
        self.i = j


def _buscar_toml(texto: str, ruta: tuple[Paso, ...]) -> int | None:
    encontrados = _EscanerToml(texto).recorrer()
    posiciones = encontrados.get(tuple(ruta), [])
    return posiciones[0] if len(posiciones) == 1 else None
