"""Autocomprobación antes de imprimir (FR-23, FR-25): corrige hacia abajo lo que no se sostiene; nunca imprime algo que no pasó.

Cada hallazgo pasa por tres revisiones, en este orden:

1. **Invariantes por nivel** (``core.invariantes.comprobar``) con los hechos con que se calculó. Si viola alguna, baja.
2. **El archivo citado sigue existiendo.** Si no existe, baja un nivel (comprobado a potencial, potencial a hipótesis) y la
   línea queda "no determinada".
3. **La línea citada contiene la clave.** Si el archivo no se puede reabrir o la línea no tiene lo que el tipo dice, la línea
   queda "línea no determinada" (FR-10): mejor no decir una línea que decir una falsa.

Cada corrección se devuelve para que el reporte la diga. El lector (qué archivos existen y su texto) entra por parámetro: el
núcleo no abre nada. Del texto solo se pregunta, de paso, si una línea tiene la forma esperada; nunca se conserva.
"""

from __future__ import annotations

import dataclasses
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from agentreach.contracts import Finding, Linea, Location, Nivel, Plataforma, Tipo
from agentreach.core.invariantes import bajar, comprobar
from agentreach.core.nivel import Hechos
from agentreach.core.politica import maximo_de, tope

__all__ = ["Autocomprobado", "Correccion", "Lector", "RazonCorreccion", "autocomprobar", "linea_contiene_clave"]


class Lector(Protocol):
    def existe(self, ruta: str) -> bool: ...

    def lineas(self, ruta: str) -> list[str] | None:
        """Las líneas del archivo, o ``None`` si no se pudo reabrir (gigante, no UTF-8, tubería, enlace...)."""
        ...


class RazonCorreccion(Enum):
    INVARIANTE_VIOLADA = "invariante_violada"
    ARCHIVO_YA_NO_EXISTE = "archivo_ya_no_existe"
    LINEA_NO_CONFIRMADA = "linea_no_confirmada"


@dataclass(frozen=True, slots=True)
class Correccion:
    ubicacion: Location
    tipo: Tipo
    razon: RazonCorreccion
    plataforma: Plataforma = Plataforma.NO_DETERMINADA
    nivel_antes: Nivel | None = None  # el nivel con que llegó el hallazgo
    nivel_despues: Nivel | None = None  # el nivel con que se imprime (igual al de antes si solo se retiró la línea)


@dataclass(frozen=True, slots=True)
class Autocomprobado:
    hallazgos: tuple[Finding, ...]
    correcciones: tuple[Correccion, ...] = ()


_CREDENCIAL = re.compile(
    r"SECRET|TOKEN|PASSW|API_?KEY|PRIVATE_?KEY|ACCESS_?KEY|CREDENTIAL|DATABASE_URL|DB_URL|CONNECTION_STRING|_KEY\b|PASS(?:WORD|WD)?(?:_|\b)"
    r"|_URI\b|_auth|client_secret|\"password\"|\"token\"",
    re.IGNORECASE,
)
_TIPOS_DE_CREDENCIAL = frozenset({Tipo.CREDENCIAL_EN_ARCHIVO, Tipo.SECRETO_DE_ALTO_PODER})


def linea_contiene_clave(tipo: Tipo, texto: str) -> bool:
    """¿La línea tiene la forma que el tipo dice? Solo responde sí o no; el texto no se conserva."""
    limpio = texto.strip()
    if not limpio:
        return False
    if tipo in _TIPOS_DE_CREDENCIAL:
        return bool(_CREDENCIAL.search(limpio)) and not limpio.startswith(("#", "//", ";"))
    if tipo is Tipo.GIT_REMOTO_SOSPECHOSO:
        return "url" in limpio.lower() or "@" in limpio or limpio.startswith("[")
    if tipo is Tipo.GIT_EJECUTA_PROGRAMAS:
        return not limpio.startswith(("#", ";"))
    return True


def _es_de_archivo(ruta: str) -> bool:
    return bool(ruta) and not ruta.startswith("(") and os.path.isabs(ruta)


def autocomprobar(
    hallazgos: tuple[Finding, ...] | list[Finding],
    hechos: Mapping[Finding, Hechos],
    lector: Lector,
) -> Autocomprobado:
    salida: list[Finding] = []
    correcciones: list[Correccion] = []
    memoria: dict[str, list[str] | None] = {}

    def anotar(h: Finding, razon: RazonCorreccion) -> None:
        correcciones.append(Correccion(h.ubicacion, h.tipo, razon, h.plataforma, h.nivel))

    for original in hallazgos:
        h = original
        primera = len(correcciones)
        if comprobar(h, hechos.get(h)):
            h = bajar(h)
            anotar(original, RazonCorreccion.INVARIANTE_VIOLADA)
        real = str(h.ubicacion.ruta_real or h.ubicacion.ruta)
        if _es_de_archivo(real):
            h = _revisar_archivo(h, real, lector, memoria, lambda r, o=original: anotar(o, r))
        for n in range(primera, len(correcciones)):  # el nivel final recién se conoce aquí
            correcciones[n] = dataclasses.replace(correcciones[n], nivel_despues=h.nivel)
        salida.append(h)
    return Autocomprobado(tuple(salida), tuple(correcciones))


def _revisar_archivo(h: Finding, real: str, lector: Lector, memoria: dict[str, list[str] | None], anotar) -> Finding:
    if not lector.existe(real):
        anotar(RazonCorreccion.ARCHIVO_YA_NO_EXISTE)
        return dataclasses.replace(_bajar_un_nivel(h), ubicacion=dataclasses.replace(h.ubicacion, linea=Linea.NO_DETERMINADA))
    linea = h.ubicacion.linea
    if not isinstance(linea, int):
        return h
    if real not in memoria:
        memoria[real] = lector.lineas(real)
    lineas = memoria[real]
    if lineas is None or linea > len(lineas) or not linea_contiene_clave(h.tipo, lineas[linea - 1]):
        anotar(RazonCorreccion.LINEA_NO_CONFIRMADA)
        return dataclasses.replace(h, ubicacion=dataclasses.replace(h.ubicacion, linea=Linea.NO_DETERMINADA))
    return h


def _bajar_un_nivel(h: Finding) -> Finding:
    """Comprobado a potencial, potencial a hipótesis; nunca por encima del máximo del tipo."""
    if h.nivel is Nivel.COMPROBADO:
        return bajar(h)
    if h.nivel is Nivel.POTENCIAL:
        from agentreach.contracts import Motivo

        nivel = tope(Nivel.HIPOTESIS, maximo_de(h.tipo))
        return dataclasses.replace(h, nivel=nivel, motivo=Motivo.INDICIO_DEBIL)
    return h
