"""Evaluador: mide los hechos de cada candidato y le pone su nivel real (Historia 11).

Los detectores entregan candidatos con un nivel provisional. Aquí cada candidato se mide (existe, permiso del
sistema, regla de cada agente), se confirma por la segunda vía (Historia 18) si su nivel depende del permiso, y se
calcula con ``core.nivel.calcular``. Un hallazgo apoyado en un archivo sale una vez por agente (FR-17): un ``.env``
puede ser potencial para uno y comprobado para otro.

Núcleo puro: las piezas que miden entran por parámetro (puertos), no se importan.
"""

from __future__ import annotations

import dataclasses
import os
from collections.abc import Callable, Iterable
from typing import Protocol

from agentreach.contracts import (
    Etiqueta,
    Finding,
    Location,
    Nivel,
    PermisosArchivo,
    Plataforma,
    Postura,
    Ruta,
    etiqueta,
)
from agentreach.core.invariantes import bajar, comprobar
from agentreach.core.nivel import Hechos, calcular
from agentreach.core.politica import CARGA_SOLA, Base, base_de
from agentreach.core.verificacion_independiente import Confirmacion, Sonda, confirmar

__all__ = ["Evaluador", "PosturaDeAgente"]


class _Fija:
    """Devuelve siempre el permiso ya medido."""

    def __init__(self, permisos: PermisosArchivo) -> None:
        self._permisos = permisos

    def evaluar(self, ruta: Ruta) -> PermisosArchivo:
        return self._permisos


class PosturaDeAgente(Protocol):
    """Lo que el evaluador pide a un adaptador: su plataforma y la postura de lectura de una ruta."""

    plataforma: Plataforma

    def postura_para(self, ruta: Ruta) -> Postura: ...

    def regla_para(self, ruta: Ruta) -> Location | None: ...


def _clave(ruta: Ruta) -> str:
    return os.path.normcase(os.path.abspath(ruta))


def _agente(adaptador: PosturaDeAgente) -> Etiqueta:
    return etiqueta(adaptador.plataforma.value.replace("_", "-"))


class Evaluador:
    """``verificador`` es la segunda vía del permiso; ``None`` si el sistema no tiene (no se pide confirmación)."""

    def __init__(
        self,
        sonda: Sonda,
        verificador: Sonda | None,
        adaptadores: Iterable[PosturaDeAgente],
        existe: Callable[[Ruta], bool],
    ) -> None:
        self._sonda = sonda
        self._verificador = verificador
        vistos: dict[Plataforma, PosturaDeAgente] = {}
        for a in adaptadores:  # uno por plataforma: dos iguales duplicarían cada hallazgo
            vistos.setdefault(a.plataforma, a)
        self._adaptadores = tuple(vistos.values())
        self._existe = existe
        self._permisos: dict[str, PermisosArchivo | None] = {}
        self._confirmaciones: dict[str, Confirmacion] = {}
        self.hechos: dict[Finding, Hechos] = {}  # con qué se calculó cada hallazgo (lo revisa la autocomprobación)

    def evaluar(self, candidatos: Iterable[Finding]) -> list[Finding]:
        salida: list[Finding] = []
        for c in candidatos:
            salida.extend(self._uno(c))
        return salida

    # ---- un candidato ---------------------------------------------------------------------------------------

    def _uno(self, c: Finding) -> list[Finding]:
        base = base_de(c.tipo)
        if base in (Base.CONFIG, Base.INDICIO):  # no dependen de un archivo medido: una sola respuesta
            d = calcular(c.tipo, Hechos(existe=True, postura=c.postura, certeza=c.certeza))
            return [dataclasses.replace(c, nivel=d.nivel, motivo=d.motivo)]
        if c.tipo in CARGA_SOLA:  # una sola respuesta: la regla de leer archivos no gobierna lo que el agente carga solo
            return [self._para_agente(c, base, None)]
        if c.plataforma is not Plataforma.NO_DETERMINADA:  # ya es de un agente: solo se mide para ese
            propios = [a for a in self._adaptadores if a.plataforma is c.plataforma]
            agentes: list[PosturaDeAgente | None] = list(propios) or [None]
        else:
            agentes = list(self._adaptadores) or [None]
        return [self._para_agente(c, base, a) for a in agentes]

    def _para_agente(self, c: Finding, base: Base, adaptador: PosturaDeAgente | None) -> Finding:
        ruta = Ruta(c.ubicacion.ruta_real or c.ubicacion.ruta)  # la real: un nombre con caracteres raros se mide bien
        postura, regla = c.postura, c.regla  # sin adaptador se conserva lo que traía el candidato
        if c.tipo in CARGA_SOLA:
            consultada = Postura.SIN_REGLA
        else:
            if adaptador is not None:
                postura, regla = self._postura(adaptador, ruta)
            consultada = postura
        hechos = Hechos(
            existe=self._medir_existe(ruta),
            permiso=None if base is Base.BYTES else self._medir_permiso(ruta),
            postura=consultada,
            certeza=c.certeza,
        )
        decision = calcular(c.tipo, hechos)
        if decision.nivel is Nivel.COMPROBADO and base is not Base.BYTES and self._verificador is not None:
            hechos = dataclasses.replace(hechos, confirmacion=self._confirmar(ruta))  # FR-24
            decision = calcular(c.tipo, hechos)
        final = dataclasses.replace(
            c,
            nivel=decision.nivel,
            motivo=decision.motivo,
            postura=postura,
            regla=regla,
            plataforma=adaptador.plataforma if adaptador is not None else c.plataforma,
            agente=_agente(adaptador) if adaptador is not None else c.agente,
        )
        if c.tipo in CARGA_SOLA:
            final = dataclasses.replace(final, postura=Postura.SIN_REGLA)  # ninguna regla de lectura aplica: así lo muestra el reporte
        final = self._corregir(final, hechos)
        self.hechos[final] = hechos
        return final

    def _corregir(self, h: Finding, hechos: Hechos) -> Finding:
        """Segunda mirada (FR-23): si alguna invariante falla, se corrige hacia abajo; nunca se deja pasar."""
        if not comprobar(h, hechos):
            return h
        return bajar(h)

    # ---- mediciones (con memoria por ruta; nunca lanzan) ----------------------------------------------------

    @staticmethod
    def _postura(adaptador: PosturaDeAgente, ruta: Ruta) -> tuple[Postura, Location | None]:
        try:
            postura = adaptador.postura_para(ruta)
        except Exception:  # noqa: BLE001 - un adaptador que falla deja la regla sin determinar, no tumba el reporte
            return Postura.NO_DETERMINADA, None
        if not isinstance(postura, Postura):
            return Postura.NO_DETERMINADA, None
        try:
            regla = adaptador.regla_para(ruta)
        except Exception:  # noqa: BLE001 - la postura ya se conoce; solo falta citar la regla
            regla = None
        return postura, regla if isinstance(regla, Location) else None

    def _medir_existe(self, ruta: Ruta) -> bool:
        try:
            return bool(self._existe(ruta))
        except Exception:  # noqa: BLE001
            return False

    def _medir_permiso(self, ruta: Ruta) -> PermisosArchivo | None:
        clave = _clave(ruta)
        if clave not in self._permisos:
            try:
                resultado = self._sonda.evaluar(ruta)
                self._permisos[clave] = resultado if isinstance(resultado, PermisosArchivo) else None
            except Exception:  # noqa: BLE001
                self._permisos[clave] = None
        return self._permisos[clave]

    def _confirmar(self, ruta: Ruta) -> Confirmacion:
        clave = _clave(ruta)
        if clave not in self._confirmaciones:
            assert self._verificador is not None
            medido = self._medir_permiso(ruta)
            if medido is None:
                self._confirmaciones[clave] = Confirmacion.NO_CONFIRMADO
            else:  # se compara contra el MISMO permiso que decidió el nivel
                self._confirmaciones[clave] = confirmar(_Fija(medido), self._verificador, ruta).estado
        return self._confirmaciones[clave]
