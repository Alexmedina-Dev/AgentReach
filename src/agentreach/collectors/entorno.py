"""Variables de entorno con nombre de credencial (TH-4). Solo NOMBRES, nunca valores.

El entorno llega por el puerto ``EnvView`` (una lista de nombres): este módulo no importa ``os``, no
lee archivos y por eso no usa ``leer_seguro``. Se filtran los nombres por su forma de credencial.

El nivel es provisional (hipótesis): la Historia 11 lo calcula. Si el agente hereda o no la variable
(el bloque de limpieza del entorno) lo lee la Historia 9; aquí no se decide.
"""

from __future__ import annotations

from collections.abc import Iterable

from agentreach.collectors.detector.patrones import clasificar_nombre
from agentreach.contracts import (
    Ajeno,
    EnvView,
    Etiqueta,
    Finding,
    Location,
    Motivo,
    Nivel,
    Plataforma,
    Postura,
    Ruta,
    Tipo,
    limpiar_ruta,
)


class DetectorEntorno:
    def __init__(self, env: EnvView) -> None:
        self._env = env

    def detectar(self, proyecto: Ruta) -> Iterable[Finding]:
        vistos: set[str] = set()
        hallazgos: list[Finding] = []
        for nombre in self._env.nombres() or ():
            if not isinstance(nombre, str):
                continue  # una vista de entorno mal hecha no tumba el detector
            ruta = limpiar_ruta(f"entorno:{nombre}")  # lo que se muestra, sin caracteres de control
            if ruta in vistos:  # un hallazgo por nombre (en Windows el entorno ya no repite mayúsculas)
                continue
            vistos.add(ruta)
            clase = clasificar_nombre(nombre)
            if clase is None:
                continue  # sin forma de credencial: se ignora
            hallazgos.append(
                Finding(
                    ubicacion=Location(ruta),  # no hay archivo ni línea: solo el nombre
                    tipo=Tipo.VARIABLE_DE_ENTORNO,
                    proveedor=clase.proveedor,
                    nivel=Nivel.HIPOTESIS,
                    motivo=Motivo.NO_DETERMINADO,
                    ajeno_a_tarea=Ajeno.NO_DETERMINADO,
                    plataforma=Plataforma.NO_DETERMINADA,
                    agente=Etiqueta("sin-agente"),
                    postura=Postura.NO_DETERMINADA,
                )
            )
        return sorted(hallazgos, key=lambda h: h.ubicacion.ruta)
