"""Caracteres Unicode invisibles en archivos de instrucciones (TH-12): "contrabando de ASCII".

Hay caracteres que no se dibujan pero un agente sí lee: con ellos se puede esconder una orden dentro
de un ``CLAUDE.md`` o un ``.cursor/rules/estilo.mdc`` que la persona no ve (*Rules File Backdoor*).

Qué se busca (seis grupos):

- ``etiquetas``: U+E0000 a U+E007F
- ``ancho_cero``: U+200B a U+200F
- ``direccion``: U+202A a U+202E, los aislamientos U+2066 a U+2069 y U+061C (*Trojan Source*)
- ``operadores_invisibles``: U+2060 a U+2064 y los formatos obsoletos U+206A a U+206F
- ``selectores_variacion``: U+FE00 a U+FE0F y el suplemento U+E0100 a U+E01EF
- ``bom_intermedio``: U+FEFF que no esté al inicio del archivo

Qué NO se reporta: el pegamento de ancho cero (U+200D) dentro de un emoji compuesto, los selectores de
variación pegados a un emoji (y a una tecla numérica) y las tres banderas con etiquetas que existen
(Inglaterra, Escocia y Gales: una bandera negra, el código y la etiqueta de cierre). Un U+200D o U+FE0F
aislado sí se reporta, y también cualquier "bandera" con otro contenido: así no se puede esconder un
mensaje detrás de una bandera. Por línea se admiten como máximo ``MAX_LEGITIMOS_POR_LINEA`` de estos
invisibles "legítimos"; el resto se cuenta como hallazgo.

Nunca se decodifica ni se copia el mensaje oculto: de cada línea solo se cuenta cuántos caracteres
hay en cada grupo. Los archivos se leen solo con la lectura segura (un archivo que no es UTF-8 no se
decodifica a la fuerza: así no se pierde un carácter oculto) y lo que no se pueda leer, o sea un enlace,
sale como ``NoRevisado``, nunca como "sin caracteres invisibles". El nivel es provisional (hipótesis);
la Historia 11 lo calcula (es un hecho de los bytes).

Límite conocido: el texto legítimo en escrituras que usan U+200C o U+200E/F (persa, árabe, hebreo,
indias) se reporta; sin una lista por escritura, es preferible el aviso de más al descuido.
"""

from __future__ import annotations

import os
import re
import unicodedata
from collections.abc import Iterable

from agentreach.collectors.enlaces import recorrer
from agentreach.contracts import (
    Ajeno,
    ArchivoNoLegible,
    Etiqueta,
    Finding,
    Linea,
    Location,
    Motivo,
    MotivoNoRevisado,
    Nivel,
    NoRevisado,
    Plataforma,
    Postura,
    Proveedor,
    ReadOnlyFs,
    Ruta,
    Tipo,
)

# (grupo, primer código, último código). Los caracteres se construyen con chr(): el código fuente
# tampoco lleva ningún carácter invisible escrito literalmente.
RANGOS = (
    ("etiquetas", 0xE0000, 0xE007F),
    ("ancho_cero", 0x200B, 0x200F),
    ("direccion", 0x202A, 0x202E),
    ("direccion", 0x2066, 0x2069),
    ("direccion", 0x061C, 0x061C),
    ("operadores_invisibles", 0x2060, 0x2064),
    ("operadores_invisibles", 0x206A, 0x206F),
    ("selectores_variacion", 0xFE00, 0xFE0F),
    ("selectores_variacion", 0xE0100, 0xE01EF),
    ("bom_intermedio", 0xFEFF, 0xFEFF),
)
GRUPOS = tuple(dict.fromkeys(g for g, _, _ in RANGOS))  # nombres, en orden y sin repetir
_CANDIDATOS = re.compile("[" + "".join(f"{chr(a)}-{chr(b)}" for _, a, b in RANGOS) + "]")
_SALTO = re.compile(r"\r\n|\r|\n")  # los mismos saltos que reconoce el resto del programa

MAX_LEGITIMOS_POR_LINEA = 24
_ZWJ = chr(0x200D)
_BANDERA_NEGRA = chr(0x1F3F4)
_FIN_ETIQUETAS = 0xE007F
_VARIACION_EMOJI = (chr(0xFE0E), chr(0xFE0F))
_KEYCAP = chr(0x20E3)
_BASES_TECLA = "0123456789#*"
# Las únicas banderas con etiquetas que existen como emoji: Inglaterra, Escocia y Gales.
_BANDERAS_CON_ETIQUETAS = frozenset({"gbeng", "gbsct", "gbwls"})
_EMOJI_SUELTOS = frozenset({
    0xA9, 0xAE, 0x203C, 0x2049, 0x2122, 0x2139, 0x24C2, 0x25AA, 0x25AB, 0x25B6, 0x25C0,
    0x25FB, 0x25FC, 0x25FD, 0x25FE, 0x2934, 0x2935, 0x3030, 0x303D, 0x3297, 0x3299,
})

_NOMBRES_ANYWHERE = {"claude.md", "agents.md", "gemini.md", "conventions.md"}
_NOMBRES_RAIZ = {".cursorrules", ".windsurfrules", ".clinerules", ".roorules"}
_EXCLUIDAS = {".git", "node_modules", ".venv", "venv", "site-packages"}


def _grupo(codigo: int) -> str:
    return next(g for g, a, b in RANGOS if a <= codigo <= b)


def _es_emoji(c: str) -> bool:
    """Aproximación sin tabla: pictogramas y símbolos de emoji, no cualquier símbolo (flechas de cajas, etc.)."""
    o = ord(c)
    if 0x1F3FB <= o <= 0x1F3FF:  # modificador de tono de piel
        return True
    if o in _EMOJI_SUELTOS:  # lista explícita de puntos de código que son emoji aunque su categoría sea otra
        return True
    return (0x1F000 <= o <= 0x1FAFF or 0x2600 <= o <= 0x27BF or 0x2300 <= o <= 0x23FF
            or 0x2B00 <= o <= 0x2BFF or 0x2190 <= o <= 0x21FF) and unicodedata.category(c) in ("So", "Sk", "Sm")


def _es_etiqueta(c: str) -> bool:
    return 0xE0000 <= ord(c) <= 0xE007F


def _tramo_de_etiquetas(linea: str, i: int) -> int:
    """Fin (exclusivo) del tramo de etiquetas que empieza en ``i``. Se recorre una sola vez."""
    e = i
    while e < len(linea) and _es_etiqueta(linea[e]):
        e += 1
    return e


def _es_bandera_con_etiquetas(linea: str, inicio: int, fin: int) -> bool:
    """🏴 + código de una de las tres banderas + etiqueta de cierre. Cualquier otra cosa no es una bandera."""
    if inicio == 0 or linea[inicio - 1] != _BANDERA_NEGRA or ord(linea[fin - 1]) != _FIN_ETIQUETAS:
        return False
    codigo = "".join(chr(ord(c) - 0xE0000) for c in linea[inicio:fin - 1])
    return codigo in _BANDERAS_CON_ETIQUETAS


def _es_legitimo(linea: str, i: int) -> bool:
    c = linea[i]
    n = len(linea)
    previo = linea[i - 1] if i > 0 else ""
    siguiente = linea[i + 1] if i + 1 < n else ""
    if c == _ZWJ:  # pegamento de un emoji compuesto: emoji (y su selector), ZWJ, emoji
        if not siguiente or not _es_emoji(siguiente):
            return False
        if previo and _es_emoji(previo):
            return True
        return bool(previo in _VARIACION_EMOJI and i >= 2 and _es_emoji(linea[i - 2]))
    if c in _VARIACION_EMOJI:  # selector pegado a un emoji, o a una tecla numérica (1 + FE0F + keycap)
        if previo and _es_emoji(previo):
            return True
        return bool(previo and previo in _BASES_TECLA and siguiente == _KEYCAP)
    return False


def contar_invisibles(texto: str) -> dict[int, dict[str, int]]:
    """Por número de línea (desde 1): cuántos invisibles hay por grupo. Solo las líneas que tienen alguno."""
    resultado: dict[int, dict[str, int]] = {}
    for numero, linea in enumerate(_SALTO.split(texto), start=1):
        cuentas: dict[str, int] = {}
        legitimos = 0
        saltar_hasta = 0
        for m in _CANDIDATOS.finditer(linea):
            i = m.start()
            if i < saltar_hasta:
                continue  # parte de un tramo de etiquetas ya evaluado
            codigo = ord(linea[i])
            if numero == 1 and i == 0 and codigo == 0xFEFF:
                continue  # la marca de orden de bytes del inicio no cuenta
            if _es_etiqueta(linea[i]):
                fin = _tramo_de_etiquetas(linea, i)  # el tramo entero se evalúa una vez
                saltar_hasta = fin
                if _es_bandera_con_etiquetas(linea, i, fin):
                    legitimos += 1
                    if legitimos <= MAX_LEGITIMOS_POR_LINEA:
                        continue
                cuentas["etiquetas"] = cuentas.get("etiquetas", 0) + (fin - i)
                continue
            if _es_legitimo(linea, i):
                legitimos += 1
                if legitimos <= MAX_LEGITIMOS_POR_LINEA:
                    continue  # pasado el tope, los "legítimos" también se cuentan: podrían ser un canal
            grupo = _grupo(codigo)
            cuentas[grupo] = cuentas.get(grupo, 0) + 1
        if cuentas:
            resultado[numero] = cuentas
    return resultado


def es_archivo_de_instrucciones(relativa: str) -> bool:
    """¿Esta ruta, relativa al proyecto, es un archivo de instrucciones de agentes?"""
    partes = relativa.replace("\\", "/").lower().split("/")
    nombre = partes[-1]
    if _EXCLUIDAS & set(partes[:-1]):
        return False
    if nombre in _NOMBRES_ANYWHERE or nombre.startswith("readme"):
        return True
    if len(partes) == 1:
        return nombre in _NOMBRES_RAIZ
    ruta = "/".join(partes)
    return (ruta.startswith((".cursor/rules/", ".github/instructions/", ".github/prompts/", ".windsurf/rules/"))
            or ruta == ".github/copilot-instructions.md"
            or (ruta.startswith(".claude/") and nombre.endswith(".md")))


class DetectorInvisibles:
    """``no_revisados`` y ``detalles`` quedan con lo de la última llamada a ``detectar``.

    ``detalles`` asocia (ruta, línea) del hallazgo con ((grupo, cuántos), ...), en el orden de ``GRUPOS``.
    """

    def __init__(self, fs: ReadOnlyFs) -> None:
        self._fs = fs
        self.no_revisados: tuple[NoRevisado, ...] = ()
        self.detalles: dict[tuple[str, int | Linea], tuple[tuple[str, int], ...]] = {}

    def detectar(self, proyecto: Ruta) -> Iterable[Finding]:
        self.no_revisados = ()
        self.detalles = {}
        pendientes: list[NoRevisado] = []
        hallazgos: list[Finding] = []
        recorrido = recorrer(self._fs, proyecto)
        for omitido in recorrido.omitidos:  # demasiado grande para leerlo: no es "sin invisibles"
            if self._interesa(omitido, proyecto):
                pendientes.append(NoRevisado(Ruta(omitido), MotivoNoRevisado.ARCHIVO_DEMASIADO_GRANDE))
        # un enlace con nombre de archivo de instrucciones no se sigue: se informa, no parece limpio
        enlaces = [e.ruta for e in recorrido.enlaces] + [
            n.ruta for n in recorrido.no_revisados if n.motivo is MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR
        ]
        for enlace in dict.fromkeys(enlaces):
            if self._interesa(enlace, proyecto):
                pendientes.append(NoRevisado(Ruta(enlace), MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR))
        for archivo in recorrido.archivos:
            if not self._interesa(archivo.ruta, proyecto):
                continue
            real = Ruta(archivo.ruta_real if archivo.ruta_real is not None else archivo.ruta)
            try:
                texto = self._fs.leer_texto(real)
            except (ArchivoNoLegible, OSError, ValueError) as error:
                pendientes.append(NoRevisado(archivo.ruta, getattr(error, "motivo", None) or MotivoNoRevisado.ARCHIVO_ILEGIBLE))
                continue  # sin decodificar a la fuerza: no es "sin caracteres invisibles"
            por_linea = contar_invisibles(texto)
            del texto  # el contenido no sobrevive al análisis
            for linea, cuentas in por_linea.items():
                ubicacion = Location(archivo.ruta, linea)
                self.detalles[(ubicacion.ruta, linea)] = tuple((g, cuentas[g]) for g in GRUPOS if g in cuentas)
                hallazgos.append(_hallazgo(ubicacion))
        self.no_revisados = tuple(pendientes)
        return hallazgos

    @staticmethod
    def _interesa(ruta: str, proyecto: str) -> bool:
        try:
            relativa = os.path.relpath(ruta, proyecto)
        except ValueError:  # otra unidad
            return False
        if relativa == ".." or relativa.startswith(".." + os.sep):
            return False  # fuera del proyecto (un nombre que solo empieza por dos puntos sí cuenta)
        return es_archivo_de_instrucciones(relativa)


def _hallazgo(ubicacion: Location) -> Finding:
    return Finding(
        ubicacion=ubicacion,
        tipo=Tipo.TEXTO_INVISIBLE,
        proveedor=Proveedor.NO_APLICA,
        nivel=Nivel.HIPOTESIS,  # provisional: el nivel final (un hecho de los bytes) lo calcula la Historia 11
        motivo=Motivo.NO_DETERMINADO,
        ajeno_a_tarea=Ajeno.NO_DETERMINADO,
        plataforma=Plataforma.NO_DETERMINADA,
        agente=Etiqueta("sin-agente"),
        postura=Postura.NO_DETERMINADA,
    )
