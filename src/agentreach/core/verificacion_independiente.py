"""Verificación independiente (FR-24): un segundo cálculo, escrito aparte, que intenta refutar al primero.

La sonda principal (Historia 3) y el verificador (Historia 18) calculan, cada uno por su vía, tres hechos
sobre un archivo para el usuario que ejecuta AgentReach: si puede leerlo, si hay una entrada de la ACL que
lo abre a "Todos" y si el resultado es ambiguo. ``confirmar`` dice "confirmado" si los tres coinciden y
"no confirmado" si discrepan, si alguna de las dos no puede determinar o si alguna falla. Es el equivalente
a "intentar refutar" del informe de la skill de Cloudflare.

Límite que se dice en el reporte: las dos vías leen la MISMA ACL del sistema, así que comparten el riesgo
de interpretarla mal (``LIMITACION_TEXTO``). Este módulo es núcleo puro: solo conoce los contratos.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from agentreach.contracts import Idioma, PermisoLectura, PermisosArchivo, Ruta


class Confirmacion(Enum):
    CONFIRMADO = "confirmado"
    NO_CONFIRMADO = "no_confirmado"


@dataclass(frozen=True, slots=True)
class ResultadoConfirmacion:
    estado: Confirmacion
    discrepancias: tuple[str, ...] = ()  # nombres de los hechos que no coinciden, o la razón por la que no se pudo


class Sonda(Protocol):
    def evaluar(self, ruta: Ruta) -> PermisosArchivo: ...


LIMITACION_TEXTO: dict[Idioma, str] = {
    Idioma.ES: ("Esta verificación la hace otro código de AgentReach, pero ambos leen la misma ACL (la lista que Windows "
                "guarda de quién puede leer cada archivo): comparten el riesgo de interpretarla mal."),
    Idioma.EN: ("This check is made by separate AgentReach code, but both read the same ACL (the list Windows keeps of "
                "who can read each file): they share the risk of misreading it."),
}

_HECHOS = (
    ("permiso", lambda p: p.permiso),
    ("abierto_a_todos", lambda p: p.abierto_a_todos),
    ("ambiguo", lambda p: p.ambiguo),
)


def comparar(principal: PermisosArchivo, verificador: PermisosArchivo) -> ResultadoConfirmacion:
    """Compara los tres hechos, en este orden: permiso, abierto a Todos y ambiguo."""
    discrepancias = tuple(nombre for nombre, hecho in _HECHOS if hecho(principal) != hecho(verificador))
    estado = Confirmacion.NO_CONFIRMADO if discrepancias else Confirmacion.CONFIRMADO
    return ResultadoConfirmacion(estado, discrepancias)


def confirmar(principal: Sonda, verificador: Sonda, ruta: Ruta) -> ResultadoConfirmacion:
    """Confirma el resultado de la sonda principal con el verificador. Nunca lanza una excepción.

    "No confirmado" si discrepan en cualquiera de los tres hechos, si alguna vía no puede determinar el
    permiso o si alguna falla. El mensaje de una excepción no se copia.
    """
    razones: list[str] = []
    resultados: dict[str, PermisosArchivo] = {}
    for nombre, sonda in (("principal", principal), ("verificador", verificador)):
        try:
            resultados[nombre] = sonda.evaluar(ruta)
        except Exception:  # noqa: BLE001 - la verificación no puede tumbar al reporte
            razones.append(f"{nombre}_fallo")
    for nombre in list(resultados):
        if not isinstance(resultados[nombre], PermisosArchivo):  # una sonda que devuelve otra cosa cuenta como fallo
            razones.append(f"{nombre}_fallo")
            del resultados[nombre]
    for nombre in ("principal", "verificador"):
        if nombre in resultados and resultados[nombre].permiso is PermisoLectura.NO_DETERMINADO:
            razones.append(f"{nombre}_no_determinado")
    if razones:
        return ResultadoConfirmacion(Confirmacion.NO_CONFIRMADO, tuple(razones))
    return comparar(resultados["principal"], resultados["verificador"])
