"""Contrato ``NoRevisado``: algo que AgentReach no pudo revisar, y por qué (FR-21, FR-25, FR-26).

Los motivos son una lista cerrada de razones de IMPOSIBILIDAD ("no se pudo leer", "demasiado
grande"). Ninguno habla de nivel ni de sospecha: no revisar algo no lo vuelve ni más ni menos grave.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from agentreach.contracts.finding import Ruta, RutaReal, limpiar_ruta


class MotivoNoRevisado(Enum):
    UBICACION_SENSIBLE_SIN_ACTIVAR = "ubicacion_sensible_sin_activar"
    ARCHIVO_ILEGIBLE = "archivo_ilegible"
    ARCHIVO_DEMASIADO_GRANDE = "archivo_demasiado_grande"
    NO_ES_ARCHIVO_REGULAR = "no_es_archivo_regular"
    CODIFICACION_NO_UTF8 = "codificacion_no_utf8"
    PROFUNDIDAD_EXCEDIDA = "profundidad_excedida"
    RUTA_DE_RED = "ruta_de_red"
    CONFIGURACION_NO_INTERPRETABLE = "configuracion_no_interpretable"
    VERSION_NO_RECONOCIDA = "version_no_reconocida"
    HISTORIAL_GIT_FASE2 = "historial_git_fase2"
    FUNCION_NO_MODELADA = "funcion_no_modelada"  # la configuración usa algo que cambia las reglas y este adaptador no lo modela
    SIN_PERMISO_FUERA_DEL_PROYECTO = "sin_permiso_fuera_del_proyecto"  # la persona no dio permiso para leer las reglas fuera del proyecto


@dataclass(frozen=True, slots=True)
class NoRevisado:
    """Una ruta que no se revisó y el motivo (de la lista cerrada). Nunca lleva contenido."""

    ruta: Ruta
    motivo: MotivoNoRevisado
    ruta_real: RutaReal | None = field(default=None, repr=False)  # antes de limpiar: solo para reabrir
    clave: str = ""  # la CLAVE de la configuración que no se interpreta (p. ej. ``hooks.PreToolUse``): nunca un valor

    def __post_init__(self) -> None:
        if not isinstance(self.motivo, MotivoNoRevisado):
            raise TypeError("el motivo debe ser un miembro de MotivoNoRevisado (lista cerrada)")
        if self.ruta_real is None:
            object.__setattr__(self, "ruta_real", RutaReal(str(self.ruta)))
        object.__setattr__(self, "ruta", limpiar_ruta(self.ruta))
        object.__setattr__(self, "clave", limpiar_ruta(self.clave)[:80])  # sin caracteres de control y acotada
