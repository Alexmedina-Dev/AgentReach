"""Cálculo del nivel de confianza (FR-5, FR-6, FR-7, FR-24): la tabla de decisión como una función pura.

``calcular(tipo, hechos)`` recibe los hechos ya medidos y devuelve el nivel y el motivo. No mide nada, no abre
archivos y no importa adaptadores ni infraestructura: quien mide es ``core.evaluador``. Así cada fila de la tabla
se prueba con hechos falsos.

Reglas fijadas por Alex (2026-11-09) que esta función cumple:

1. La herencia de permisos NO baja el nivel: el permiso efectivo ya la incluye. Solo bajan una regla ``deny``
   o ``ask``, una ACL no estándar, un cálculo incompleto o fallido y un texto dudoso.
2. Un ``deny`` (o un ``ask``) del agente solo baja a potencial; no borra el hallazgo.
3. Si la verificación independiente (Historia 18) discrepa o no puede determinar, baja a potencial.
4. Un tipo reconocido por nombre o prefijo sin fuente verificada no pasa de potencial.

"Comprobado" es solo lo que se determina con certeza y sin ambigüedad desde el propio archivo. Ante cualquier
duda el resultado baja; nunca sube.
"""

from __future__ import annotations

from dataclasses import dataclass

from agentreach.contracts import (
    Certeza,
    Motivo,
    Nivel,
    PermisoLectura,
    PermisosArchivo,
    Postura,
    Tipo,
    fuente_verificada,
)
from agentreach.core.politica import Base, base_de, es_mayor, maximo_de, tope
from agentreach.core.verificacion_independiente import Confirmacion

__all__ = ["Decision", "Hechos", "calcular"]


@dataclass(frozen=True, slots=True)
class Hechos:
    """Lo que se midió de un hallazgo. Sin contenido de archivos.

    ``permiso`` es ``None`` si no se midió o no se pudo (cuenta como no determinado). ``confirmacion`` es ``None``
    cuando no se pidió la segunda vía (no hay verificador en este sistema, o el nivel no depende del permiso).
    """

    existe: bool
    permiso: PermisosArchivo | None = None
    postura: Postura = Postura.NO_DETERMINADA
    certeza: Certeza = Certeza.COMPLETA
    confirmacion: Confirmacion | None = None


@dataclass(frozen=True, slots=True)
class Decision:
    nivel: Nivel
    motivo: Motivo


def calcular(tipo: Tipo, hechos: Hechos) -> Decision:
    """La tabla de FR-5 para un tipo. El resultado nunca supera el nivel máximo del tipo (FR-18)."""
    decision = _decidir(tipo, hechos)
    return Decision(tope(decision.nivel, maximo_de(tipo)), decision.motivo)


def _potencial(motivo: Motivo) -> Decision:
    return Decision(Nivel.POTENCIAL, motivo)


def _decidir(tipo: Tipo, h: Hechos) -> Decision:
    base = base_de(tipo)
    if base is Base.INDICIO:
        return Decision(Nivel.HIPOTESIS, Motivo.INDICIO_DEBIL)
    if base is Base.CONFIG:  # no se ve desde el archivo: la plataforma, su versión o una decisión de la persona
        return _potencial(Motivo.NO_DETERMINADO)
    # ARCHIVO, POR_NOMBRE y BYTES: el hecho se mide
    if not h.existe or not isinstance(h.postura, Postura):
        return _potencial(Motivo.NO_DETERMINADO)
    if h.postura is Postura.DENY:  # FR-6: política del agente, no barrera del sistema operativo
        return _potencial(Motivo.REGLA_DENY)
    if h.postura is Postura.ASK:
        return _potencial(Motivo.REGLA_ASK)
    if base is not Base.BYTES:  # la lectura depende del permiso del sistema y de la regla del agente
        permiso = h.permiso
        if permiso is None or permiso.permiso is PermisoLectura.NO_DETERMINADO:
            return _potencial(Motivo.NO_DETERMINADO)
        if permiso.permiso is PermisoLectura.NO:
            return _potencial(Motivo.EXISTE_NO_LEGIBLE)
        if permiso.ambiguo:  # regla de denegar, ACL no estándar o cálculo incompleto (la herencia no cuenta)
            return _potencial(Motivo.SIN_CERTEZA_DEL_ARCHIVO)
    if h.postura not in (Postura.ALLOW, Postura.SIN_REGLA):  # solo una regla conocida deja pasar a comprobado
        return _potencial(Motivo.NO_DETERMINADO)
    if h.certeza is Certeza.DUDOSA:  # valor de relleno, ayudante de credenciales, un hook sin bit verificado...
        return _potencial(Motivo.SIN_CERTEZA_DEL_ARCHIVO)
    if base is not Base.BYTES and h.confirmacion is Confirmacion.NO_CONFIRMADO:  # FR-24
        return _potencial(Motivo.NO_CONFIRMADO_INDEPENDIENTE)
    if base is Base.POR_NOMBRE and not fuente_verificada(tipo):  # FR-7
        return _potencial(Motivo.SIN_FUENTE_VERIFICADA)
    if es_mayor(Nivel.COMPROBADO, maximo_de(tipo)):  # el tipo no llega a comprobado
        return _potencial(Motivo.NO_DETERMINADO if fuente_verificada(tipo) else Motivo.SIN_FUENTE_VERIFICADA)
    return Decision(Nivel.COMPROBADO, Motivo.EXISTE_LEGIBLE_SIN_REGLA)
