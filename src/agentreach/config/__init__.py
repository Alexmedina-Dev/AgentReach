"""Configuración global y reglas de precedencia.

Lo que activa algo sensible (las ubicaciones del usuario) viene SOLO de dos fuentes: un flag de la
línea de comandos o el archivo de configuración GLOBAL del usuario. Nunca de un archivo del proyecto
auditado: ``cargar_configuracion`` ni siquiera recibe la ruta del proyecto, así que no puede leerlo.
"""

from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass

from agentreach.contracts import Ruta
from agentreach.contracts.no_revisado import MotivoNoRevisado, NoRevisado
from agentreach.infra.lectura_segura import leer_seguro

# TODO(Q11): nombre y lugar del archivo de política del proyecto y política de supresiones: decisión abierta.
# [SUPUESTO] lugar del archivo global: ~/.agentreach/config.toml


def archivo_global_por_defecto() -> str | None:
    """Ruta absoluta del archivo global, calculada al pedirla. ``None`` si no se conoce la carpeta
    personal: una ruta relativa podría caer dentro del proyecto auditado, y eso nunca puede activar nada."""
    base = os.path.expanduser("~")
    if not os.path.isabs(base):
        return None
    return os.path.join(base, ".agentreach", "config.toml")

CLAVE_UBICACIONES = "incluir_ubicaciones_sensibles"


@dataclass(frozen=True, slots=True)
class Configuracion:
    """Opciones del usuario. Todo lo sensible está apagado por defecto."""

    incluir_ubicaciones_sensibles: bool = False
    home: str | None = None  # carpeta personal a mirar; por defecto la del usuario (--home para pruebas)
    no_revisados: tuple[NoRevisado, ...] = ()  # archivo global que no se pudo interpretar
    # Historia 28: ¿se dio permiso para leer las reglas FUERA del proyecto (configuración de usuario, gestionada y opencode.json de las
    # carpetas padre)? Sin él no se abre ni se lista nada fuera del proyecto. La línea de comandos lo pone en False si la persona dice N.
    lectura_fuera: bool = True


def cargar_configuracion(
    flags: Mapping[str, object] | None = None,
    archivo_global: str | None = None,
) -> Configuracion:
    """Combina el flag de la línea de comandos y el archivo global.

    Cualquiera de los dos puede ENCENDER el opt-in; ninguno puede apagar al otro. Solo un ``True``
    literal enciende; cualquier otro valor lo deja apagado. Una ruta global relativa se ignora.
    """
    flags = flags or {}
    home = flags.get("home")
    no_revisados: list[NoRevisado] = []
    encendido = flags.get(CLAVE_UBICACIONES) is True
    if not encendido and archivo_global is not None and os.path.isabs(archivo_global):
        valor, problema = _leer_archivo_global(archivo_global)
        encendido = valor is True
        if problema is not None:
            no_revisados.append(problema)
    return Configuracion(
        incluir_ubicaciones_sensibles=encendido,
        home=str(home) if isinstance(home, str) and home else None,
        no_revisados=tuple(no_revisados),
    )


def _leer_archivo_global(ruta: str) -> tuple[object, NoRevisado | None]:
    if not os.path.lexists(ruta):
        return None, None  # no hay archivo global: es lo normal
    texto = leer_seguro(Ruta(ruta))
    if isinstance(texto, NoRevisado):
        return None, texto
    try:
        datos = tomllib.loads(texto)
    except (tomllib.TOMLDecodeError, RecursionError, ValueError):
        return None, NoRevisado(Ruta(ruta), MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE)
    return datos.get(CLAVE_UBICACIONES), None
