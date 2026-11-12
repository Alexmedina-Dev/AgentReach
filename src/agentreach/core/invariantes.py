"""Invariantes por nivel (FR-23): ``comprobar`` devuelve las reglas que un hallazgo viola. Función pura.

Es una segunda mirada, escrita aparte de ``core.nivel``: revisa el hallazgo ya calculado contra los hechos con que
se calculó. Quien llama (la autocomprobación de la Historia 13) corrige hacia abajo lo que viole alguna regla.
Sin hechos, un "comprobado" no se puede justificar: se rechaza.
"""

from __future__ import annotations

import dataclasses
from enum import Enum

from agentreach.contracts import (
    Certeza,
    Finding,
    Motivo,
    Nivel,
    PermisoLectura,
    Postura,
    fuente_verificada,
)
from agentreach.core.nivel import Hechos
from agentreach.core.politica import Base, base_de, es_mayor, maximo_de, tope
from agentreach.core.verificacion_independiente import Confirmacion

__all__ = ["MOTIVOS_POTENCIAL", "Violacion", "bajar", "comprobar"]


class Violacion(Enum):
    SUPERA_EL_MAXIMO_DEL_TIPO = "supera_el_maximo_del_tipo"
    COMPROBADO_SIN_HECHOS = "comprobado_sin_hechos"
    COMPROBADO_MOTIVO_INCORRECTO = "comprobado_motivo_incorrecto"
    COMPROBADO_SIN_ARCHIVO = "comprobado_sin_archivo"  # hecho 1 de FR-5: el archivo existe
    COMPROBADO_SIN_PERMISO = "comprobado_sin_permiso"  # hecho 2: el sistema permite leerlo
    COMPROBADO_CON_REGLA = "comprobado_con_regla"  # hecho 3: ninguna regla del agente lo impide
    COMPROBADO_REGLA_NO_DETERMINADA = "comprobado_regla_no_determinada"
    COMPROBADO_AMBIGUO = "comprobado_ambiguo"
    COMPROBADO_SIN_CONFIRMAR = "comprobado_sin_confirmar"  # FR-24
    COMPROBADO_SIN_FUENTE = "comprobado_sin_fuente"  # FR-7
    COMPROBADO_SIN_BASE = "comprobado_sin_base"  # un tipo que no se apoya en un hecho medido
    POTENCIAL_SIN_MOTIVO = "potencial_sin_motivo"
    HIPOTESIS_SIN_INDICIO = "hipotesis_sin_indicio"


# Los motivos válidos de un potencial: los cuatro de FR-5 y los tres que añaden FR-7, FR-24 y la regla de certeza.
MOTIVOS_POTENCIAL = frozenset({
    Motivo.NO_DETERMINADO,
    Motivo.REGLA_DENY,
    Motivo.REGLA_ASK,
    Motivo.EXISTE_NO_LEGIBLE,
    Motivo.SIN_FUENTE_VERIFICADA,
    Motivo.NO_CONFIRMADO_INDEPENDIENTE,
    Motivo.SIN_CERTEZA_DEL_ARCHIVO,
})


def comprobar(hallazgo: Finding, hechos: Hechos | None = None) -> tuple[Violacion, ...]:
    """Las reglas que viola ``hallazgo``; vacío si todo está en orden. Nunca lanza."""
    v: list[Violacion] = []
    if es_mayor(hallazgo.nivel, maximo_de(hallazgo.tipo)):
        v.append(Violacion.SUPERA_EL_MAXIMO_DEL_TIPO)
    if hallazgo.nivel is Nivel.POTENCIAL and hallazgo.motivo not in MOTIVOS_POTENCIAL:
        v.append(Violacion.POTENCIAL_SIN_MOTIVO)
    if hallazgo.nivel is Nivel.HIPOTESIS and hallazgo.motivo is not Motivo.INDICIO_DEBIL:
        v.append(Violacion.HIPOTESIS_SIN_INDICIO)
    if hallazgo.nivel is Nivel.COMPROBADO:
        v.extend(_comprobado(hallazgo, hechos))
    return tuple(dict.fromkeys(v))


def _comprobado(h: Finding, hechos: Hechos | None) -> list[Violacion]:
    if hechos is None:
        return [Violacion.COMPROBADO_SIN_HECHOS]
    base = base_de(h.tipo)
    if base in (Base.CONFIG, Base.INDICIO):
        return [Violacion.COMPROBADO_SIN_BASE]
    v: list[Violacion] = []
    if h.motivo is not Motivo.EXISTE_LEGIBLE_SIN_REGLA:
        v.append(Violacion.COMPROBADO_MOTIVO_INCORRECTO)
    if not hechos.existe:
        v.append(Violacion.COMPROBADO_SIN_ARCHIVO)
    if hechos.postura in (Postura.DENY, Postura.ASK):
        v.append(Violacion.COMPROBADO_CON_REGLA)
    if hechos.certeza is Certeza.DUDOSA:
        v.append(Violacion.COMPROBADO_AMBIGUO)
    if hechos.postura not in (Postura.ALLOW, Postura.SIN_REGLA, Postura.DENY, Postura.ASK):
        v.append(Violacion.COMPROBADO_REGLA_NO_DETERMINADA)
    if base is not Base.BYTES:  # los hechos de los bytes no dependen del permiso
        permiso = hechos.permiso
        if permiso is None or permiso.permiso is not PermisoLectura.SI:
            v.append(Violacion.COMPROBADO_SIN_PERMISO)
        elif permiso.ambiguo:
            v.append(Violacion.COMPROBADO_AMBIGUO)
        if hechos.confirmacion is Confirmacion.NO_CONFIRMADO:
            v.append(Violacion.COMPROBADO_SIN_CONFIRMAR)
    if base is Base.POR_NOMBRE and not fuente_verificada(h.tipo):
        v.append(Violacion.COMPROBADO_SIN_FUENTE)
    return v


def bajar(hallazgo: Finding) -> Finding:
    """Corrige hacia abajo un hallazgo que viola alguna invariante: nunca sube. Potencial como mucho (o su máximo)."""
    nivel = tope(Nivel.POTENCIAL, maximo_de(hallazgo.tipo))
    motivo = Motivo.INDICIO_DEBIL if nivel is Nivel.HIPOTESIS else Motivo.NO_DETERMINADO
    return dataclasses.replace(hallazgo, nivel=nivel, motivo=motivo)
