"""Detector de credenciales en archivos del proyecto (TH-1 y TH-17), por nombre y sin retener valores.

El nivel de cada hallazgo es provisional (hipótesis): la Historia 11 lo calcula de verdad.
"""

from __future__ import annotations

from collections.abc import Iterable

from agentreach.collectors.detector.archivos import (
    Candidato,
    ClaseArchivo,
    analizar,
    candidato_por_nombre,
    clase_de_archivo,
)
from agentreach.collectors.enlaces import recorrer
from agentreach.contracts import (
    Ajeno,
    ArchivoNoLegible,
    Etiqueta,
    Finding,
    Location,
    Motivo,
    MotivoNoRevisado,
    Nivel,
    NoRevisado,
    Plataforma,
    Postura,
    ReadOnlyFs,
    Ruta,
)
from agentreach.infra.lectura_segura import revisar_profundidad_json


class DetectorCredencialesArchivos:
    """``no_revisados`` queda con lo que no se pudo revisar en la última llamada, cada uno con su motivo."""

    def __init__(self, fs: ReadOnlyFs) -> None:
        self._fs = fs
        self.no_revisados: tuple[NoRevisado, ...] = ()

    def detectar(self, proyecto: Ruta) -> Iterable[Finding]:
        self.no_revisados = ()  # nunca queda la lista de una llamada anterior
        hallazgos: list[Finding] = []
        pendientes: list[NoRevisado] = []
        recorrido = recorrer(self._fs, proyecto)
        pendientes.extend(recorrido.no_revisados)
        for omitido in recorrido.omitidos:  # demasiado grande para leerlo: se reporta por nombre
            clase = clase_de_archivo(omitido, proyecto)
            por_nombre = candidato_por_nombre(clase) if clase else None
            if por_nombre:
                hallazgos.append(_a_hallazgo(Ruta(omitido), por_nombre))
        for archivo in recorrido.archivos:
            clase = clase_de_archivo(archivo.ruta, proyecto)
            if clase is None:
                continue
            real = Ruta(archivo.ruta_real if archivo.ruta_real is not None else archivo.ruta)
            for candidato in self._candidatos(real, clase, pendientes):
                hallazgos.append(_a_hallazgo(archivo.ruta, candidato))
        self.no_revisados = tuple(pendientes)
        return hallazgos

    def _candidatos(self, ruta: Ruta, clase: ClaseArchivo, no_revisados: list[NoRevisado]) -> list[Candidato]:
        try:
            texto = self._fs.leer_texto(ruta)
        except (ArchivoNoLegible, OSError) as error:
            motivo = getattr(error, "motivo", MotivoNoRevisado.ARCHIVO_ILEGIBLE)
            no_revisados.append(NoRevisado(ruta, motivo))  # se informa, no se salta en silencio
            por_nombre = candidato_por_nombre(clase)  # existe pero no se puede leer (p. ej. PP-03)
            return [por_nombre] if por_nombre else []
        if clase is ClaseArchivo.CREDENCIALES_JSON:
            excedido = revisar_profundidad_json(ruta, texto)
            if excedido is not None:
                no_revisados.append(excedido)
                por_nombre = candidato_por_nombre(clase)  # igual que un archivo ilegible: existe, no se leyó
                return [por_nombre] if por_nombre else []
        return analizar(clase, texto)  # el contenido no sale de aquí


def _a_hallazgo(ruta: Ruta, c: Candidato) -> Finding:
    return Finding(
        ubicacion=Location(ruta, c.linea),
        tipo=c.tipo,
        proveedor=c.proveedor,
        nivel=Nivel.HIPOTESIS,
        motivo=Motivo.NO_DETERMINADO,
        ajeno_a_tarea=Ajeno.NO_DETERMINADO,
        plataforma=Plataforma.NO_DETERMINADA,
        agente=Etiqueta("sin-agente"),
        postura=Postura.NO_DETERMINADA,
    )
