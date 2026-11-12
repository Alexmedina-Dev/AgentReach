"""Tubería mínima: reúne los candidatos de los detectores registrados.

Núcleo puro: solo conoce los contratos (``agentreach.contracts``), nunca adaptadores,
infraestructura ni reporte. No calcula niveles ni explica nada; eso llega en historias posteriores.
"""

from __future__ import annotations

from collections.abc import Iterable

from agentreach.contracts import Detector, Finding, Ruta, ordenar


class Pipeline:
    """Ejecuta, en orden de registro, los detectores sobre un proyecto y ordena el resultado."""

    def __init__(self, detectores: Iterable[Detector] = ()) -> None:
        self._detectores: list[Detector] = list(detectores)

    def registrar(self, detector: Detector) -> None:
        self._detectores.append(detector)

    @property
    def detectores(self) -> tuple[Detector, ...]:
        return tuple(self._detectores)

    def ejecutar(self, proyecto: Ruta) -> list[Finding]:
        """Reúne los hallazgos de todos los detectores. Si un detector falla, el error se
        propaga con su nombre; nunca se descarta en silencio."""
        reunidos: list[Finding] = []
        for detector in self._detectores:
            try:
                reunidos.extend(detector.detectar(proyecto))
            except Exception as error:
                nombre = type(detector).__name__
                raise RuntimeError(f"El detector {nombre} falló") from error
        return ordenar(reunidos)
