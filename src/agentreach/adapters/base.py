"""Piezas comunes a todos los adaptadores de plataforma (Claude Code, opencode...).

Un **adaptador** es la pieza que entiende las reglas de una plataforma de agentes. Todos entregan lo
mismo, que es lo que el kit de conformidad (``adapters/conformance``) comprueba:

- ``reglas``: las reglas ``allow``, ``ask`` y ``deny`` con su archivo y línea. El texto de la regla no
  sale en ``repr`` (podría llevar un secreto): solo se usa dentro del adaptador para decidir.
- ``entorno_nombres``: los NOMBRES de las variables de entorno de la configuración, nunca sus valores.
- ``agentes``: las definiciones de agente que encontró.
- ``config_proyecto``: hechos de la configuración DEL PROYECTO que se ejecuta sola (Historia 17).
- ``no_revisados``: todo lo que no pudo leer o interpretar, con su motivo. Un adaptador nunca lanza
  una excepción por una configuración rara: la informa.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from agentreach.contracts import Capacidad, Linea, Location, Plataforma, Postura, Ruta
from agentreach.contracts.no_revisado import NoRevisado


@dataclass(frozen=True, slots=True)
class Regla:
    """Una regla de permisos de la plataforma. ``especificador`` solo sirve para decidir, no para mostrar."""

    accion: str  # "allow", "ask" o "deny"
    herramienta: str  # "Read", "Bash", "Edit"...
    ubicacion: Location  # archivo y línea de la regla
    especificador: str | None = field(default=None, repr=False)
    fuente: str = "proyecto"  # "gestionada", "local", "proyecto" o "usuario"


@dataclass(frozen=True, slots=True)
class DefinicionAgente:
    """Un agente definido en un archivo (por ejemplo ``.claude/agents/revisor.md``). Sin su cuerpo."""

    ruta: Ruta
    nombre: str | None  # solo si es un identificador corto y seguro
    herramientas: tuple[str, ...]
    linea_herramientas: int | Linea
    hereda_todas: bool = False  # sin la clave ``tools``: el agente hereda todas las herramientas (el caso más amplio)


@dataclass(frozen=True, slots=True)
class CasoConfigProyecto:
    """Un hecho de la configuración del proyecto que ejecuta algo al abrir la carpeta (sin su valor)."""

    clave: str  # "hooks", "mcp" y "base_url" (los tres con versión corregida en el catálogo) o "salto_de_permisos" (TH-15)
    ubicacion: Location


@dataclass(frozen=True, slots=True)
class ResultadoAdaptador:
    reglas: tuple[Regla, ...] = ()
    entorno_nombres: tuple[str, ...] = ()
    limpieza_de_entorno: bool = False
    agentes: tuple[DefinicionAgente, ...] = ()
    config_proyecto: tuple[CasoConfigProyecto, ...] = ()
    sandbox_disponible: bool | None = None  # False: se sabe que no hay; None: no se sabe, no se afirma
    no_revisados: tuple[NoRevisado, ...] = ()
    reglas_incompletas: bool = False  # una fuente de reglas existe y no se pudo leer o entender: no se sabe qué reglas hay
    causas_no_determinado: tuple[NoRevisado, ...] = ()  # por qué un nivel puede salir «no determinado»: archivo y clave, sin valores
    esquema: str = ""  # opencode: "1.x", "2.x" o "ambiguo" (por la forma de los archivos; no prueba la versión instalada)


@runtime_checkable
class AdaptadorBase(Protocol):
    """Lo que debe ofrecer cualquier adaptador además del puerto ``AgentAdapter``."""

    plataforma: Plataforma
    capacidad: Capacidad

    def cargar(self, proyecto: Ruta) -> ResultadoAdaptador: ...

    def postura_para(self, ruta: Ruta) -> Postura: ...

    def regla_para(self, ruta: Ruta) -> Location | None: ...
