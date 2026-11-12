"""Política del nivel de confianza: de qué se apoya cada tipo de hallazgo y hasta dónde puede subir (FR-5, FR-7, FR-18).

Dos tablas fijas, una fila por tipo (TH-1 a TH-20):

- ``BASE_POR_TIPO``: en qué hecho se apoya el hallazgo (``Base``). Decide qué mide el cálculo del nivel.
- ``NIVEL_MAXIMO``: el nivel más alto que el tipo puede tener (FR-18). El cálculo nunca lo supera.

Núcleo puro: no importa adaptadores, infraestructura ni reporte. Un tipo que falte en una tabla se trata con
lo más prudente (base ``CONFIG`` y nivel máximo potencial), nunca con lo más generoso.
"""

from __future__ import annotations

from enum import Enum

from agentreach.contracts import Nivel, Tipo

__all__ = ["BASE_POR_TIPO", "CARGA_SOLA", "NIVEL_MAXIMO", "Base", "base_de", "es_mayor", "maximo_de", "tope"]


class Base(Enum):
    """En qué hecho se apoya un hallazgo. Cada base mide cosas distintas (ver ``core.nivel.calcular``)."""

    ARCHIVO = "archivo"  # un archivo existe, el sistema operativo permite leerlo y ninguna regla del agente lo impide
    POR_NOMBRE = "por_nombre"  # como ARCHIVO, pero el secreto se reconoce solo por su nombre o prefijo (FR-7)
    BYTES = "bytes"  # un hecho del texto, los bytes o el disco del propio archivo; una regla puede bajarlo
    CONFIG = "config"  # depende de la plataforma, su versión o una decisión de la persona: no se ve desde el archivo
    INDICIO = "indicio"  # un indicio débil o indirecto: nunca pasa de hipótesis


BASE_POR_TIPO: dict[Tipo, Base] = {
    Tipo.CREDENCIAL_EN_ARCHIVO: Base.ARCHIVO,
    Tipo.CLAVE_PRIVADA_SSH: Base.ARCHIVO,
    Tipo.CREDENCIALES_DE_NUBE: Base.ARCHIVO,
    Tipo.VARIABLE_DE_ENTORNO: Base.INDICIO,
    Tipo.CONTEXTO_SOSPECHOSO: Base.INDICIO,
    Tipo.ENLACE_FUERA_DEL_PROYECTO: Base.BYTES,
    Tipo.REGLA_PERMISIVA: Base.CONFIG,
    Tipo.CAPACIDAD_DE_SHELL: Base.CONFIG,
    Tipo.SCRIPT_DE_DESPLIEGUE: Base.INDICIO,
    Tipo.PLATAFORMA_SIN_SANDBOX: Base.CONFIG,
    Tipo.DEFINICION_DE_AGENTE: Base.CONFIG,
    Tipo.TEXTO_INVISIBLE: Base.BYTES,
    Tipo.INSTRUCCIONES_FUERA_DE_PROYECTO: Base.BYTES,
    Tipo.HOOK_O_MCP_DE_COMANDO: Base.CONFIG,
    Tipo.SALTO_DE_PERMISOS: Base.CONFIG,
    Tipo.TAREA_AL_ABRIR_CARPETA: Base.CONFIG,
    Tipo.SECRETO_DE_ALTO_PODER: Base.POR_NOMBRE,
    Tipo.GIT_EJECUTA_PROGRAMAS: Base.BYTES,
    Tipo.GIT_REMOTO_SOSPECHOSO: Base.ARCHIVO,
    Tipo.GIT_NO_INTERPRETABLE: Base.CONFIG,
}

# FR-18 y decisiones de Alex del 2026-11-09 (pregunta 23): TH-2, TH-3, TH-6, TH-7, TH-8 y TH-10 llegan a potencial
# como máximo; TH-5 y TH-9 a hipótesis. El resto de las filas con tope potencial son [SUPUESTO] de la Historia 11:
# TH-4 (EV-01: hipótesis, el entorno que se ve es el de AgentReach y no el del agente), TH-11, TH-14, TH-15, TH-16 (no se ve la versión del agente ni si la persona aceptó el aviso de
# confianza), TH-17 (AT-08: el poder real del token no se ve) y TH-20 (la configuración no se pudo interpretar).
NIVEL_MAXIMO: dict[Tipo, Nivel] = {
    Tipo.CREDENCIAL_EN_ARCHIVO: Nivel.POTENCIAL,
    Tipo.CLAVE_PRIVADA_SSH: Nivel.POTENCIAL,
    Tipo.CREDENCIALES_DE_NUBE: Nivel.POTENCIAL,
    Tipo.VARIABLE_DE_ENTORNO: Nivel.HIPOTESIS,
    Tipo.CONTEXTO_SOSPECHOSO: Nivel.HIPOTESIS,
    Tipo.ENLACE_FUERA_DEL_PROYECTO: Nivel.POTENCIAL,
    Tipo.REGLA_PERMISIVA: Nivel.POTENCIAL,
    Tipo.CAPACIDAD_DE_SHELL: Nivel.POTENCIAL,
    Tipo.SCRIPT_DE_DESPLIEGUE: Nivel.HIPOTESIS,
    Tipo.PLATAFORMA_SIN_SANDBOX: Nivel.POTENCIAL,
    Tipo.DEFINICION_DE_AGENTE: Nivel.POTENCIAL,
    Tipo.TEXTO_INVISIBLE: Nivel.COMPROBADO,
    Tipo.INSTRUCCIONES_FUERA_DE_PROYECTO: Nivel.COMPROBADO,
    Tipo.HOOK_O_MCP_DE_COMANDO: Nivel.POTENCIAL,
    Tipo.SALTO_DE_PERMISOS: Nivel.POTENCIAL,
    Tipo.TAREA_AL_ABRIR_CARPETA: Nivel.POTENCIAL,
    Tipo.SECRETO_DE_ALTO_PODER: Nivel.POTENCIAL,
    Tipo.GIT_EJECUTA_PROGRAMAS: Nivel.COMPROBADO,
    Tipo.GIT_REMOTO_SOSPECHOSO: Nivel.COMPROBADO,
    Tipo.GIT_NO_INTERPRETABLE: Nivel.POTENCIAL,
}


# Lo que no depende de que el agente LEA un archivo (instrucciones que carga solo, y lo que git ejecuta por su cuenta): una regla de
# lectura (ask/deny) no lo gobierna, y por eso un archivo de configuración del agente roto no puede bajar estos hallazgos.
CARGA_SOLA = frozenset({Tipo.TEXTO_INVISIBLE, Tipo.INSTRUCCIONES_FUERA_DE_PROYECTO, Tipo.GIT_EJECUTA_PROGRAMAS})


def base_de(tipo: Tipo) -> Base:
    """Base del tipo; si falta la fila, ``CONFIG`` (lo más prudente: nunca llega a comprobado)."""
    return BASE_POR_TIPO.get(tipo, Base.CONFIG)


def maximo_de(tipo: Tipo) -> Nivel:
    """Nivel máximo del tipo; si falta la fila, potencial."""
    return NIVEL_MAXIMO.get(tipo, Nivel.POTENCIAL)


def es_mayor(a: Nivel, b: Nivel) -> bool:
    """``a`` es más alto que ``b`` (comprobado > potencial > hipótesis)."""
    return a.prioridad < b.prioridad


def tope(nivel: Nivel, maximo: Nivel) -> Nivel:
    """El menor de los dos: nunca sube un nivel, solo lo limita."""
    return maximo if es_mayor(nivel, maximo) else nivel
