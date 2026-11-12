"""Recorrido del proyecto y enlaces que salen de él (TH-6, FR-19).

Recorre solo con el puerto ``ReadOnlyFs``. Un enlace (junction o enlace simbólico) nunca se sigue:
si su destino cae fuera del proyecto se reporta el enlace y su destino, nada de lo que hay detrás.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass

from agentreach.contracts import (
    LIMITE_BYTES,
    Ajeno,
    Etiqueta,
    Finding,
    Location,
    Metadatos,
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
from agentreach.contracts.rutas import es_ruta_de_red

MAX_PROFUNDIDAD = 64
PREFIJO_NT = "\\\\?\\"  # prefijo de ruta larga de Windows


@dataclass(frozen=True, slots=True)
class Enlace:
    """Un enlace que sale del proyecto. ``destino`` es solo texto; nunca se abre."""

    ruta: Ruta
    destino: Ruta | None


@dataclass(frozen=True, slots=True)
class Recorrido:
    archivos: tuple[Metadatos, ...]
    enlaces: tuple[Enlace, ...]
    no_revisadas: tuple[str, ...]  # rutas de red, ilegibles o demasiado profundas
    omitidos: tuple[str, ...]  # archivos que se saltan por tamaño
    no_revisados: tuple[NoRevisado, ...] = ()  # lo mismo con su motivo de lista cerrada (Historia 4b)


def _norm(ruta: str) -> str:
    """Forma canónica para comparar: resuelve nombres cortos 8.3 y quita el prefijo de ruta larga de Windows.

    ``realpath`` resuelve los componentes de la ruta (consulta metadatos de enlaces), pero no abre
    ni lee el contenido del destino. Una raíz o un destino de red ya se descartó antes por texto.
    """
    resuelta = os.path.realpath(ruta)
    resuelta = resuelta.removeprefix(PREFIJO_NT)
    return os.path.normcase(resuelta)


def _sale_del_proyecto(enlace: Metadatos, raiz: str) -> bool:
    # Se compara con el texto original (sin limpiar): limpiarlo podría cambiar a dónde apunta.
    destino = enlace.destino_real if enlace.destino_real is not None else enlace.destino_enlace
    if destino is None or es_ruta_de_red(destino):
        return True  # no se puede probar que quede dentro (o es de red, que no se consulta): se reporta
    base = enlace.ruta_real if enlace.ruta_real is not None else enlace.ruta
    unido = os.path.join(os.path.dirname(base), destino)
    if es_ruta_de_red(unido):
        return True
    absoluto = _norm(unido)
    try:
        return os.path.commonpath([absoluto, raiz]) != raiz
    except ValueError:  # otra unidad
        return True


def recorrer(fs: ReadOnlyFs, proyecto: Ruta) -> Recorrido:
    """Lista los archivos del proyecto sin seguir enlaces ni tocar rutas de red."""
    if es_ruta_de_red(proyecto):  # UNC o unidad de red: no se consulta
        return Recorrido(
            (), (), (str(proyecto),), (),
            (NoRevisado(Ruta(str(proyecto)), MotivoNoRevisado.RUTA_DE_RED),),
        )
    raiz = _norm(proyecto)
    archivos: list[Metadatos] = []
    enlaces: list[Enlace] = []
    no_revisadas: list[str] = []
    omitidos: list[str] = []
    no_revisados: list[NoRevisado] = []
    pendientes: list[tuple[Ruta, int]] = [(proyecto, 0)]
    while pendientes:
        carpeta, profundidad = pendientes.pop()
        if profundidad > MAX_PROFUNDIDAD:
            no_revisadas.append(str(carpeta))
            no_revisados.append(NoRevisado(carpeta, MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA))
            continue
        try:
            entradas = list(fs.listar(carpeta))
        except OSError:
            no_revisadas.append(str(carpeta))
            no_revisados.append(NoRevisado(carpeta, MotivoNoRevisado.ARCHIVO_ILEGIBLE))
            continue
        for entrada in entradas:
            if entrada.es_enlace:
                if _sale_del_proyecto(entrada, raiz):
                    enlaces.append(Enlace(entrada.ruta, entrada.destino_enlace))
                else:  # enlace interno: no se sigue, y se informa en vez de saltarlo en silencio
                    no_revisados.append(NoRevisado(entrada.ruta, MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR))
            elif entrada.es_carpeta:
                # se usa la ruta real (sin limpiar) para listar; la limpia es solo para mostrar
                real = entrada.ruta_real if entrada.ruta_real is not None else entrada.ruta
                pendientes.append((Ruta(real), profundidad + 1))
            elif entrada.tamano > LIMITE_BYTES:
                omitidos.append(str(entrada.ruta))
                no_revisados.append(NoRevisado(entrada.ruta, MotivoNoRevisado.ARCHIVO_DEMASIADO_GRANDE))
            else:
                archivos.append(entrada)
    return Recorrido(
        tuple(sorted(archivos, key=lambda m: m.ruta)),
        tuple(sorted(enlaces, key=lambda e: e.ruta)),
        tuple(sorted(no_revisadas)),
        tuple(sorted(omitidos)),
        tuple(sorted(no_revisados, key=lambda n: (n.ruta, n.motivo.value))),
    )


class DetectorEnlaces:
    """Detector TH-6. El nivel es provisional (hipótesis): la Historia 11 lo calcula de verdad."""

    def __init__(self, fs: ReadOnlyFs) -> None:
        self._fs = fs
        self.enlaces: tuple[Enlace, ...] = ()

    def detectar(self, proyecto: Ruta) -> Iterable[Finding]:
        self.enlaces = recorrer(self._fs, proyecto).enlaces
        return [
            Finding(
                ubicacion=Location(e.ruta),
                tipo=Tipo.ENLACE_FUERA_DEL_PROYECTO,
                proveedor=Proveedor.NO_APLICA,
                nivel=Nivel.HIPOTESIS,
                motivo=Motivo.NO_DETERMINADO,
                ajeno_a_tarea=Ajeno.NO_DETERMINADO,
                plataforma=Plataforma.NO_DETERMINADA,
                agente=Etiqueta("sin-agente"),
                postura=Postura.NO_DETERMINADA,
            )
            for e in self.enlaces
        ]
