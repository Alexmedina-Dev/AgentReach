"""Archivos de instrucciones de agentes FUERA de un proyecto (TH-13), solo con el opt-in de la Historia 5.

Un ``AGENTS.md`` suelto en la carpeta personal o en Descargas, Escritorio o Documentos lo lee como si
fuera de confianza un agente lanzado desde ahí (BleepingComputer, 2026-10-25). Aquí solo se mira la
EXISTENCIA y el tipo (``lstat``): ni se abre el archivo ni se enumeran las carpetas, solo se pregunta
por cada nombre conocido. Un enlace o una tubería sale como ``NoRevisado`` y no se sigue.

Con el opt-in apagado (el estado por defecto) no se toca el disco: cada carpeta sale como
``NoRevisado(ubicacion_sensible_sin_activar)``. Lo que activa esto viene de la configuración (flag o
archivo global), nunca del proyecto auditado. El nivel es provisional (hipótesis).
"""

from __future__ import annotations

import os
from collections.abc import Iterable

from agentreach.config import Configuracion
from agentreach.contracts import (
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

NOMBRES_INSTRUCCIONES = ("AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursorrules")
# [SUPUESTO] carpetas "de alto alcance": la carpeta personal y sus carpetas de uso común (español e inglés).
CARPETAS = ("", "Downloads", "Descargas", "Desktop", "Escritorio", "Documents", "Documentos")


class DetectorInstruccionesFuera:
    def __init__(self, fs: ReadOnlyFs, config: Configuracion) -> None:
        self._fs = fs
        self._config = config
        self.no_revisados: tuple[NoRevisado, ...] = ()

    def detectar(self, proyecto: Ruta) -> Iterable[Finding]:
        self.no_revisados = ()
        if not self._config.incluir_ubicaciones_sensibles:
            self.no_revisados = tuple(  # nombres lógicos: no se revela la carpeta personal real
                NoRevisado(Ruta("~/" + c if c else "~"), MotivoNoRevisado.UBICACION_SENSIBLE_SIN_ACTIVAR)
                for c in CARPETAS
            )
            return []
        if not self._config.lectura_fuera:  # sin el permiso de segundo nivel no se mira nada de la carpeta personal, ni sus metadatos
            self.no_revisados = (NoRevisado(Ruta("~"), MotivoNoRevisado.SIN_PERMISO_FUERA_DEL_PROYECTO),)
            return []
        home = self._config.home or os.path.expanduser("~")
        pendientes: list[NoRevisado] = []
        hallazgos: list[Finding] = []
        meta_home = self._metadatos(home, pendientes) if os.path.isabs(home) else None
        if meta_home is None or not meta_home.es_carpeta or meta_home.es_enlace:
            self.no_revisados = (NoRevisado(Ruta("~"), MotivoNoRevisado.ARCHIVO_ILEGIBLE), *pendientes)
            return []
        for carpeta in CARPETAS:
            ruta_carpeta = os.path.join(home, carpeta) if carpeta else home
            meta = self._metadatos(ruta_carpeta, pendientes)
            if meta is None or not meta.es_carpeta or meta.es_enlace:
                continue  # no existe, o no es una carpeta de verdad: no se entra
            for nombre in NOMBRES_INSTRUCCIONES:
                entrada = self._metadatos(os.path.join(ruta_carpeta, nombre), pendientes)
                if entrada is None:
                    continue
                if entrada.es_enlace or entrada.es_carpeta or not entrada.es_regular:
                    pendientes.append(NoRevisado(entrada.ruta, MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR))
                    continue
                hallazgos.append(_hallazgo(entrada))
        self.no_revisados = tuple(pendientes)
        return hallazgos

    def _metadatos(self, ruta: str, pendientes: list[NoRevisado]) -> Metadatos | None:
        try:
            return self._fs.metadatos(Ruta(ruta))
        except OSError:
            pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.ARCHIVO_ILEGIBLE))
            return None


def _hallazgo(entrada: Metadatos) -> Finding:
    return Finding(
        ubicacion=Location(entrada.ruta),
        tipo=Tipo.INSTRUCCIONES_FUERA_DE_PROYECTO,
        proveedor=Proveedor.NO_APLICA,
        nivel=Nivel.HIPOTESIS,
        motivo=Motivo.NO_DETERMINADO,
        ajeno_a_tarea=Ajeno.NO_DETERMINADO,
        plataforma=Plataforma.NO_DETERMINADA,
        agente=Etiqueta("sin-agente"),
        postura=Postura.NO_DETERMINADA,
    )
