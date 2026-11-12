"""Puertos: ReadOnlyFs, EnvView, FsProbe, AgentAdapter y Narrator (interfaces, sin implementación).

Son contratos (``typing.Protocol``) de solo lectura. Ningún puerto devuelve el valor de un secreto:
``ReadOnlyFs`` entrega metadatos y texto de configuración que quien lo usa debe descartar tras
detectar, y ``EnvView`` entrega solo NOMBRES de variables.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from agentreach.contracts.finding import Finding, Plataforma, Postura, Ruta
from agentreach.contracts.no_revisado import MotivoNoRevisado

# TODO(Q10): ¿Narrator queda como puerto vacío o se difiere por completo? Decisión abierta.
# TODO(Q7): capacidad que declara el adaptador de Claude Code en el MVP: decisión abierta.


LIMITE_BYTES = 1024 * 1024  # 1 MiB: un archivo más grande se salta (no se lee)


class ArchivoNoLegible(Exception):
    """El archivo es binario, gigante o no se pudo leer. El mensaje nunca lleva contenido.

    ``motivo`` es el motivo de lista cerrada con que el detector informa lo que no pudo revisar.
    """

    def __init__(self, mensaje: str = "", motivo: MotivoNoRevisado | None = None) -> None:
        super().__init__(mensaje)
        self.motivo = motivo if motivo is not None else MotivoNoRevisado.ARCHIVO_ILEGIBLE


class FueraDelProyecto(ArchivoNoLegible):
    """La ruta, una vez resuelta, queda fuera de la raíz del proyecto (enlace en el camino): no se lee."""

    def __init__(self, mensaje: str = "", motivo: MotivoNoRevisado | None = None) -> None:
        super().__init__(mensaje, motivo if motivo is not None else MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR)


class PermisoLectura(Enum):
    """Resultado de preguntar si la identidad que ejecuta AgentReach puede leer un archivo."""

    SI = "si"
    NO = "no"
    NO_DETERMINADO = "no_determinado"


class Capacidad(Enum):
    """Qué sabe hacer un adaptador (glosario del PRD)."""

    SOLO_AUDITAR = "solo_auditar"
    AUDITAR_Y_ADVERTIR = "auditar_y_advertir"
    AUDITAR_Y_BLOQUEAR = "auditar_y_bloquear"


@dataclass(frozen=True, slots=True)
class Metadatos:
    """Datos de un archivo o carpeta que no requieren abrirlo."""

    ruta: Ruta  # SOLO para mostrar: ya limpia de caracteres de control
    tamano: int
    es_carpeta: bool
    es_enlace: bool = False
    destino_enlace: Ruta | None = None  # solo si es_enlace; nunca se lee el contenido del destino
    ruta_real: str | None = None  # la ruta tal cual existe en disco: SOLO para uso interno, nunca se muestra
    destino_real: str | None = None  # destino del enlace sin limpiar, solo para comparar
    es_regular: bool = False  # solo True si el tipo medido con lstat es archivo regular (falla cerrado)


@dataclass(frozen=True, slots=True)
class PermisosArchivo:
    """Qué puede hacer con un archivo el usuario que ejecuta AgentReach (FR-5). Sin contenido.

    ``ambiguo`` es True cuando el resultado no se determina con certeza desde el propio archivo
    (permiso heredado, regla de denegar o lectura incompleta); la Historia 11 lo deja en potencial.
    """

    permiso: PermisoLectura
    abierto_a_todos: bool
    ambiguo: bool
    usuario: str
    comando_verificacion: str  # lo ejecuta la persona a mano; AgentReach nunca lo lanza
    modo: str | None = None  # solo POSIX, en octal (p. ej. "0o644")
    propietario: str | None = None  # solo POSIX
    pasa_por_enlace: bool = False  # la ruta o un padre es junction o enlace: se midió el destino


@runtime_checkable
class ReadOnlyFs(Protocol):
    """Sistema de archivos de solo lectura (no hay métodos de escritura, borrado ni creación)."""

    def listar(self, carpeta: Ruta) -> Iterable[Metadatos]: ...

    def metadatos(self, ruta: Ruta) -> Metadatos | None:
        """``None`` si no existe."""
        ...

    def leer_texto(self, ruta: Ruta) -> str:
        """Texto de un archivo de configuración. El llamador descarta cualquier valor."""
        ...


@runtime_checkable
class EnvView(Protocol):
    """Vista del entorno del proceso. Solo nombres, nunca valores."""

    def nombres(self) -> Iterable[str]: ...


@runtime_checkable
class FsProbe(Protocol):
    """Sonda de permisos: calcula desde metadatos y ACL (lista de control de acceso) sin abrir
    el archivo (FR-5), porque abrirlo mediría los permisos de AgentReach y no los del agente."""

    def permiso_lectura(self, ruta: Ruta) -> PermisoLectura: ...


@runtime_checkable
class AgentAdapter(Protocol):
    """Adaptador de una plataforma: lee sus reglas y las entrega al núcleo."""

    plataforma: Plataforma
    capacidad: Capacidad

    def postura_para(self, ruta: Ruta) -> Postura: ...


@runtime_checkable
class Detector(Protocol):
    """Detector registrado en la tubería: entrega candidatos a hallazgo."""

    def detectar(self, proyecto: Ruta) -> Iterable[Finding]: ...


@runtime_checkable
class Narrator(Protocol):
    """Narración con modelo de lenguaje. Vacío a propósito en el MVP (los textos salen de un
    catálogo fijo, FR-11); ver TODO(Q10)."""
