"""Caso de uso ``auditar``: arma los detectores terminados, los ejecuta con la tubería y reúne
lo que no se pudo revisar (Historia 5b).

Cada detector nuevo se registra aquí con UNA línea en ``_detectores``. Todos pasan por la tubería
(``core.pipeline.Pipeline``). Esta capa conoce adaptadores de infraestructura; el núcleo no.
"""

from __future__ import annotations

import dataclasses
import os
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from agentreach.adapters.base import ResultadoAdaptador
from agentreach.adapters.claude_code import AdaptadorClaudeCode, DetectorClaudeCode
from agentreach.adapters.opencode import AdaptadorOpencode, DetectorOpencode
from agentreach.app.agentes import AgenteDetectado, NoDeterminado, detectar_agentes
from agentreach.collectors.archivos_repo import DetectorCredencialesArchivos
from agentreach.collectors.config_ejecuta_sola import DetectorConfigEjecutaSola
from agentreach.collectors.contexto import DetectorContexto
from agentreach.collectors.despliegue import DetectorDespliegue
from agentreach.collectors.enlaces import DetectorEnlaces, recorrer
from agentreach.collectors.entorno import DetectorEntorno
from agentreach.collectors.git_meta import DetectorGit
from agentreach.collectors.instrucciones_fuera import DetectorInstruccionesFuera
from agentreach.collectors.invisibles import DetectorInvisibles
from agentreach.collectors.ubicaciones_usuario import DetectorUbicacionesUsuario
from agentreach.config import Configuracion
from agentreach.contracts import (
    Detector,
    Finding,
    NoRevisado,
    Plataforma,
    ReadOnlyFs,
    Ruta,
    ordenar,
)
from agentreach.core.evaluador import Evaluador
from agentreach.core.nivel import Hechos
from agentreach.core.pipeline import Pipeline
from agentreach.core.relacion_tarea import Referencia, clasificar, palabras
from agentreach.core.verificacion_independiente import Sonda
from agentreach.infra.env_view import EnvVistaProceso
from agentreach.infra.fs_solo_lectura import FsSoloLectura
from agentreach.infra.lectura_segura import leer_seguro


@dataclass(frozen=True, slots=True)
class ResultadoAuditoria:
    hallazgos: tuple[Finding, ...]
    no_revisados: tuple[NoRevisado, ...]
    archivos_mirados: int
    hechos: Mapping[Finding, Hechos] = field(default_factory=dict)  # con qué se calculó cada nivel (autocomprobación)
    contextos: tuple[tuple[Plataforma, ResultadoAdaptador], ...] = ()  # reglas de cada agente, como contexto
    agentes: tuple[AgenteDetectado, ...] = ()  # agentes CONFIGURADOS según el catálogo de firmas (no es «ejecutados»)
    sin_decidir: tuple[NoDeterminado, ...] = ()  # rastros compartidos que no dicen cuál de varios agentes es


# Registro: una línea por detector. Cada fábrica recibe (fs del proyecto, configuración).
_detectores: tuple[Callable[[ReadOnlyFs, Configuracion], Detector], ...] = (
    lambda fs, config: DetectorEnlaces(fs),
    lambda fs, config: DetectorCredencialesArchivos(fs),
    lambda fs, config: DetectorGit(fs),
    lambda fs, config: DetectorContexto(fs),
    lambda fs, config: DetectorDespliegue(fs),
    lambda fs, config: DetectorInvisibles(fs),
    lambda fs, config: DetectorClaudeCode(AdaptadorClaudeCode(fs, config)),
    lambda fs, config: DetectorOpencode(AdaptadorOpencode(fs, config)),
    lambda fs, config: DetectorConfigEjecutaSola(fs, AdaptadorClaudeCode(fs, config)),
    lambda fs, config: DetectorInstruccionesFuera(FsSoloLectura(), config),
    lambda fs, config: DetectorUbicacionesUsuario(FsSoloLectura(), config),
    lambda fs, config: DetectorEntorno(EnvVistaProceso()),  # EV-01: solo NOMBRES de variables, nunca valores
)


def _medidores() -> tuple[Sonda, Sonda | None]:
    """La sonda del permiso y su segunda vía (Historia 18). En POSIX no hay segunda vía todavía (se dice en el reporte)."""
    if sys.platform == "win32":
        from agentreach.infra.sonda_windows import SondaWindows
        from agentreach.infra.verificador_permiso_windows import VerificadorPermisoWindows

        return SondaWindows(), VerificadorPermisoWindows()
    from agentreach.infra.sonda_posix import SondaPosix

    return SondaPosix(), None


_NOMBRES_README = ("README.md", "README", "README.txt", "README.rst", "readme.md")
MAX_TAREA = 2000  # caracteres de --tarea que se miran


def _referencia(trabajo: str, tarea: str | None) -> tuple[Referencia, list[NoRevisado]]:
    """Palabras de la tarea y del README. El README se lee con ``leer_seguro`` y se descarta: solo quedan palabras."""
    readme: frozenset[str] | None = None
    pendientes: list[NoRevisado] = []
    for nombre in _NOMBRES_README:
        ruta = os.path.join(trabajo, nombre)
        if not os.path.lexists(ruta):
            continue
        leido = leer_seguro(Ruta(ruta))
        if isinstance(leido, NoRevisado):  # gigante, no UTF-8, tubería o enlace: no cuelga y se informa
            pendientes.append(leido)
        else:
            readme = palabras(leido)
        break
    return Referencia(palabras(tarea[:MAX_TAREA]) if tarea else None, readme), pendientes


def auditar(
    carpeta: str,
    config: Configuracion,
    medidores: tuple[Sonda, Sonda | None] | None = None,
    tarea: str | None = None,
    trabajo: str | None = None,
) -> ResultadoAuditoria:
    """Audita ``carpeta`` solo en lectura. No escribe nada ni lanza programas.

    ``medidores`` (sonda, verificador) solo se pasa en pruebas; sin él se usan los del sistema.
    ``tarea`` y ``trabajo`` (el directorio donde se lanzaría el agente; por defecto, la carpeta auditada) alimentan
    el campo «ajeno a la tarea».
    """
    carpeta = os.path.abspath(carpeta)  # la sonda del permiso solo mide rutas absolutas
    proyecto = Ruta(carpeta)
    fs = FsSoloLectura(carpeta)
    detectores = [crear(fs, config) for crear in _detectores]
    candidatos = Pipeline(detectores).ejecutar(proyecto)
    sonda, verificador = medidores if medidores is not None else _medidores()
    adaptadores = [d.adaptador for d in detectores if hasattr(d, "adaptador")]
    evaluador = Evaluador(sonda, verificador, adaptadores, existe=lambda r: os.path.lexists(r))
    directorio = os.path.abspath(trabajo) if trabajo else carpeta
    referencia, de_readme = _referencia(directorio, tarea)
    evaluados = evaluador.evaluar(candidatos)  # el nivel real (Historia 11)
    completos: list[Finding] = []
    hechos: dict[Finding, Hechos] = {}
    for h in evaluados:
        con_ajeno = dataclasses.replace(
            h, ajeno_a_tarea=clasificar(h.ubicacion.ruta_real or h.ubicacion.ruta, directorio, referencia))
        completos.append(con_ajeno)
        if h in evaluador.hechos:
            hechos[con_ajeno] = evaluador.hechos[h]
    hallazgos = ordenar(completos)
    pendientes: dict[tuple[str, str], NoRevisado] = {}
    for n in de_readme:
        pendientes[(n.ruta_real or n.ruta, n.motivo.value)] = n
    for n in config.no_revisados:
        pendientes[(n.ruta_real or n.ruta, n.motivo.value)] = n
    for detector in detectores:  # los detectores dejan sus NoRevisado en ``no_revisados``
        for n in getattr(detector, "no_revisados", ()):
            pendientes[(n.ruta_real or n.ruta, n.motivo.value)] = n  # sin duplicados entre detectores
    recorrido = recorrer(fs, proyecto)
    for n in recorrido.no_revisados:  # carpetas ilegibles, enlaces, archivos grandes: nunca se omiten en silencio
        pendientes[(n.ruta_real or n.ruta, n.motivo.value)] = n
    agentes, sin_decidir = detectar_agentes(carpeta, config.home or os.path.expanduser("~"), os.environ, leer_usuario=config.lectura_fuera)  # solo existencia y nombres
    return ResultadoAuditoria(
        hallazgos=tuple(hallazgos),
        no_revisados=tuple(pendientes[k] for k in sorted(pendientes)),
        archivos_mirados=len(recorrido.archivos),
        hechos=hechos,
        contextos=tuple((d.adaptador.plataforma, d.resultado) for d in detectores if hasattr(d, "adaptador")),
        agentes=agentes,
        sin_decidir=sin_decidir,
    )
