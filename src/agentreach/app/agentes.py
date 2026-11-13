"""Reconoce qué agentes están CONFIGURADOS en el proyecto o en el equipo, con el catálogo de firmas (Historia 24).

Qué hace y qué no (reglas de ``docs/agentes-catalogo/catalogo-agentes.md``):

- Solo mira si EXISTEN archivos y carpetas (``lexists``/``isdir``/``glob`` de nombres) y los NOMBRES de variables de entorno
  (nunca sus valores). No abre el contenido de nada. Dice «configurado», nunca «ejecutado»: que existan rastros de configuración no
  prueba que el agente haya corrido.
- **Alta**: una firma fuerte con fuente verificada. **Potencial**: firma fuerte sin fuente verificada (tope por FR-7). **Hipótesis**:
  solo indicios débiles y un único candidato; se muestra como «indicio». Nunca se afirma un agente por una firma débil.
- Nombres compartidos (``AGENTS.md``, ``.mcp.json``, ``.vscode/``, ``.github/``, ``.env``, ``~/.gemini/``, ``~/.agents/``...) jamás
  identifican a un agente: si no hay otro agente claro, se dice «no determinado» con la lista de candidatos.
- Los archivos de historial y los secretos (``tipo`` datos, estado, secretos) no cuentan como configuración y no se mencionan.
- Un marco (gentle-ai, BMAD) se reporta como instalado SOBRE el agente cuya carpeta toca, y necesita su huella propia (una habilidad
  sola no basta).
- Ámbitos separados: «proyecto» y «usuario» (y «entorno», solo el nombre de la variable).
"""

from __future__ import annotations

import glob
import json
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from importlib import resources

__all__ = ["AgenteDetectado", "Confianza", "EvidenciaDetectada", "NoDeterminado", "cargar_catalogo", "detectar_agentes"]


class Confianza(Enum):
    ALTA = "high"
    POTENCIAL = "potential"
    HIPOTESIS = "hypothesis"


@dataclass(frozen=True, slots=True)
class EvidenciaDetectada:
    ambito: str  # "proyecto", "usuario" o "entorno"
    ruta: str  # el archivo o carpeta que existe (o, en «entorno», el NOMBRE de la variable)
    fuerte: bool
    verificada: bool


@dataclass(frozen=True, slots=True)
class AgenteDetectado:
    id: str  # el del catálogo (``claude-code``)
    nombre: str
    confianza: Confianza
    marco: bool  # un marco (gentle-ai, BMAD): se instala sobre un agente, no es un agente
    sobre: tuple[str, ...]  # ids de los agentes sobre los que está instalado el marco
    evidencia: tuple[EvidenciaDetectada, ...]
    analizado: bool  # AgentReach analiza su alcance (tiene adaptador); si no, solo se dice que está configurado


@dataclass(frozen=True, slots=True)
class NoDeterminado:
    """Un rastro compartido (p. ej. ``AGENTS.md``) que no dice cuál de varios agentes lo usa."""

    ruta: str
    candidatos: tuple[str, ...]  # nombres de los agentes que lo leen


# agentes con adaptador: AgentReach analiza qué puede alcanzar (los demás solo se reconocen como configurados)
ANALIZADOS = frozenset({"claude-code", "opencode"})
MARCOS = frozenset({"gentle-ai", "bmad"})
# entradas del catálogo que no son agentes aparte: sus rastros ya cuentan para el agente al que pertenecen
OMITIDOS = frozenset({"claude-code-agente-personalizado", "opencode-agente-personalizado"})
# nombres que lo usan muchos agentes (o ninguno en particular): nunca identifican a uno
COMPARTIDOS = frozenset({"agents.md", "agent.md", ".mcp.json", ".vscode", ".github", ".env", ".gemini", ".agents", ".idea", "conventions.md",
                         "gemini.md"})
_TIPOS_QUE_NO_CUENTAN = ("datos", "estado", "secretos", "gestionada", "plugins")
# variables de entorno propias de un agente (solo el NOMBRE; nunca el valor): (nombre o prefijo, es prefijo, fuerte)
_ENTORNO = {
    "gemini-cli": (("GEMINI_CLI_HOME", False, True),),
    "aider": (("AIDER_", True, True),),
    "goose": (("GOOSE_", True, True),),
    "qwen-code": (("QWEN_", True, False),),
}
_MAX_EVIDENCIA = 12  # evidencias que se muestran por agente
_LIMITE_COINCIDENCIAS = 3  # cuántos archivos que coinciden con un patrón se anotan como evidencia


def cargar_catalogo() -> list[dict]:
    texto = resources.files("agentreach.data").joinpath("catalogo-agentes.json").read_text(encoding="utf-8")
    datos = json.loads(texto)
    return datos if isinstance(datos, list) else []


def _marcadores(ruta: str) -> str:
    """``<nombre>`` y ``<modo>`` del catálogo son comodines."""
    salida, dentro = [], False
    for c in ruta:
        if c == "<":
            dentro = True
            salida.append("*")
        elif c == ">":
            dentro = False
        elif not dentro:
            salida.append(c)
    return "".join(salida)


def _variantes(ruta: str) -> list[str]:
    """``archivo.json(c)`` del catálogo quiere decir ``archivo.json`` y ``archivo.jsonc``."""
    return [ruta[:-3], ruta[:-3] + "c"] if ruta.endswith("(c)") else [ruta]


def _coincidencias(patron: str) -> list[str]:
    """Los nombres que existen para ``patron`` (con comodines) sin abrir nada. Una carpeta solo cuenta si es carpeta."""
    exige_carpeta = patron.endswith(("/", "\\"))
    patron = patron.rstrip("/\\")
    try:
        if any(c in patron for c in "*?["):
            encontrados = [r for r in glob.glob(patron) if os.path.lexists(r)]
        else:
            encontrados = [patron] if os.path.lexists(patron) else []
        if exige_carpeta:
            encontrados = [r for r in encontrados if os.path.isdir(r)]
    except (OSError, ValueError):
        return []
    return sorted(encontrados)[:_LIMITE_COINCIDENCIAS]


def _normal(ruta: str) -> str:
    return ruta.replace("\\", "/").strip().rstrip("/").lower()


def _es_ruta(texto: str) -> bool:
    return bool(texto) and not texto.startswith("(") and "no verificado" not in texto and "no documentado" not in texto


def _relativa_a_home(destino: str, home: str) -> str:
    """La ruta de ``destino`` respecto a la carpeta personal; si está en otra unidad de disco, la ruta entera."""
    try:
        return os.path.relpath(destino, home)
    except ValueError:  # Windows: dos unidades distintas (C: y D:) no tienen ruta relativa
        return os.path.normpath(destino)


def _usuario(entrada: dict, home: str, sistema: str) -> str | None:
    ruta = entrada.get("ruta", "")
    if not _es_ruta(ruta):
        return None
    if ruta.startswith("%USERPROFILE%"):
        return home + ruta[len("%USERPROFILE%"):]
    if ruta.startswith("~"):
        return home + ruta[1:]
    if ruta.startswith("%APPDATA%"):
        base = os.environ.get("APPDATA", "")
        return base + ruta[len("%APPDATA%"):] if base else None
    return None  # rutas del sistema (ProgramData, /etc): es configuración gestionada, no del usuario


def _lista_usuario(agente: dict, sistema: str) -> list[dict]:
    clave = "windows" if sistema == "win32" else ("macos" if sistema == "darwin" else "linux")
    return list((agente.get("usuario") or {}).get(clave) or [])


def _cuenta(tipo: str) -> bool:
    return not any(p in (tipo or "").lower() for p in _TIPOS_QUE_NO_CUENTAN)


def _carpeta_de_nivel_superior(ruta: str, base: str) -> str:
    relativa = os.path.relpath(ruta, base).replace("\\", "/")
    return relativa.split("/")[0].lower()


def detectar_agentes(
    proyecto: str, home: str, env: Mapping[str, str] | None = None, sistema: str | None = None, catalogo: list[dict] | None = None,
    leer_usuario: bool = True,
) -> tuple[tuple[AgenteDetectado, ...], tuple[NoDeterminado, ...]]:
    """Los agentes configurados (todos, cada uno con su evidencia y confianza, sin elegir un «principal») y los rastros compartidos
    que no permiten decidir. Solo existencia de archivos y nombres de variables."""
    sistema = sistema or sys.platform
    env = os.environ if env is None else env
    catalogo = cargar_catalogo() if catalogo is None else catalogo
    proyecto = os.path.abspath(proyecto)
    home = os.path.abspath(home) if home and os.path.isabs(home) else ""
    # un nombre débil que aparece en varios agentes es compartido: no identifica a ninguno
    conteo: dict[str, int] = {}
    for a in catalogo:
        for e in a.get("proyecto") or []:
            if e.get("fuerza") == "debil":
                conteo[_normal(e.get("ruta", ""))] = conteo.get(_normal(e.get("ruta", "")), 0) + 1
    compartidos = COMPARTIDOS | {k for k, n in conteo.items() if n >= 2}
    # un rastro débil de un agente que es firma FUERTE de otro (p. ej. CLAUDE.md en la lista de Copilot) no lo identifica
    fuertes_de: dict[str, set[str]] = {}
    for a in catalogo:
        for e in a.get("proyecto") or []:
            if e.get("fuerza") == "fuerte":
                fuertes_de.setdefault(_normal(e.get("ruta", "")), set()).add(a.get("id", ""))

    detectados: list[AgenteDetectado] = []
    for a in catalogo:
        ident = a.get("id", "")
        if not ident or ident in OMITIDOS:
            continue
        evidencia: list[EvidenciaDetectada] = []
        for e in a.get("proyecto") or []:
            ruta = e.get("ruta", "")
            if not _es_ruta(ruta) or not _cuenta(e.get("tipo", "")) or _normal(ruta) in COMPARTIDOS:
                continue  # los nombres compartidos NUNCA identifican a un agente, ni siquiera marcados como fuertes
            fuerte = e.get("fuerza") == "fuerte"
            if not fuerte and (_normal(ruta) in compartidos or (fuertes_de.get(_normal(ruta), set()) - {ident})):
                continue  # un rastro débil compartido (o que es firma fuerte de otro agente) no identifica a este
            if ident in MARCOS and (e.get("tipo") or "").lower() == "habilidad":
                fuerte = False  # una habilidad sola no basta para un marco: necesita su huella propia
            for variante in _variantes(ruta):
                for r in _coincidencias(os.path.join(proyecto, _marcadores(variante).replace("/", os.sep))):
                    evidencia.append(EvidenciaDetectada("proyecto", r, fuerte, bool(e.get("verificada"))))
        if home and leer_usuario:  # sin el permiso de segundo nivel no se mira nada de la carpeta personal
            for e in _lista_usuario(a, sistema):
                destino = _usuario(e, home, sistema)
                if destino is None or not _cuenta(e.get("tipo", "")) or _normal(_relativa_a_home(destino, home)) in compartidos:
                    continue
                tipo = (e.get("tipo") or "").lower()
                fuerte = ident not in MARCOS and not tipo.startswith("carpeta") and "obsoleto" not in tipo
                for variante in _variantes(destino):
                    for r in _coincidencias(os.path.normpath(_marcadores(variante))):
                        evidencia.append(EvidenciaDetectada("usuario", r, fuerte, bool(e.get("verificada"))))
        for nombre, prefijo, fuerte in _ENTORNO.get(ident, ()):
            for variable in sorted(env):
                if (variable.startswith(nombre) if prefijo else variable == nombre):
                    evidencia.append(EvidenciaDetectada("entorno", variable, fuerte, True))
                    break
        if not evidencia:
            continue
        fuertes = [x for x in evidencia if x.fuerte]
        if any(x.verificada for x in fuertes):
            confianza = Confianza.ALTA
        elif fuertes:
            confianza = Confianza.POTENCIAL
        else:
            confianza = Confianza.HIPOTESIS
        if ident in MARCOS and confianza is Confianza.HIPOTESIS:
            continue  # sin su huella propia, un marco no se afirma
        detectados.append(AgenteDetectado(ident, a.get("nombre", ident), confianza, ident in MARCOS, (), _resumir(evidencia), ident in ANALIZADOS))
    detectados = _unificar_copilot(detectados)
    detectados = _marcos_sobre(detectados, catalogo, proyecto, home)
    return tuple(detectados), _no_determinados(detectados, catalogo, proyecto)


COPILOT_VSCODE, COPILOT_CLI, COPILOT_UNO = "copilot-vscode", "copilot-cli", "github-copilot"
NOMBRE_COPILOT_UNO = "GitHub Copilot (VS Code o su línea de comandos)"


def _es_senal_compartida_de_copilot(e: EvidenciaDetectada) -> bool:
    """``.github/copilot-instructions.md`` y ``.github/instructions/**.instructions.md`` los leen a la vez Copilot en VS Code y su CLI."""
    if e.ambito != "proyecto":
        return False
    ruta = _normal(e.ruta)
    return ruta.endswith("/.github/copilot-instructions.md") or ("/.github/instructions/" in ruta and ruta.endswith(".instructions.md"))


def _unificar_copilot(detectados: list[AgenteDetectado]) -> list[AgenteDetectado]:
    """Una señal compartida nunca afirma un agente concreto (regla del catálogo). Si lo único de Copilot es esa señal, se reconoce UN
    agente («GitHub Copilot (VS Code o su línea de comandos)»), no dos; si solo una superficie tiene señales propias, esa queda y la otra
    (que solo tenía la compartida) se descarta; si las dos tienen señales propias, quedan las dos."""
    por_id = {d.id: d for d in detectados}
    v, c = por_id.get(COPILOT_VSCODE), por_id.get(COPILOT_CLI)
    if not (v or c):
        return detectados
    propias = {i: any(not _es_senal_compartida_de_copilot(e) for e in a.evidencia) for i, a in por_id.items() if i in (COPILOT_VSCODE, COPILOT_CLI)}
    con_propias = [i for i, ok in propias.items() if ok]
    if len(con_propias) == 2:
        return detectados
    if len(con_propias) == 1:  # solo una superficie tiene señales propias: la otra era solo la compartida
        quitar = COPILOT_CLI if con_propias[0] == COPILOT_VSCODE else COPILOT_VSCODE
        return [d for d in detectados if d.id != quitar]
    orden = {Confianza.ALTA: 0, Confianza.POTENCIAL: 1, Confianza.HIPOTESIS: 2}
    partes = [a for a in (v, c) if a is not None]
    uno = AgenteDetectado(
        COPILOT_UNO, NOMBRE_COPILOT_UNO, min((a.confianza for a in partes), key=orden.get), False, (),  # type: ignore[arg-type]
        _resumir([e for a in partes for e in a.evidencia]), False)
    salida: list[AgenteDetectado] = []
    for d in detectados:
        if d.id == COPILOT_VSCODE:
            salida.append(uno)
        elif d.id != COPILOT_CLI:
            salida.append(d)
    return salida


def _resumir(evidencia: list[EvidenciaDetectada]) -> tuple[EvidenciaDetectada, ...]:
    """Sin repetidos, primero lo fuerte y de proyecto, y a lo sumo ``_MAX_EVIDENCIA`` entradas por agente."""
    unicas = list(dict.fromkeys(evidencia))
    unicas.sort(key=lambda x: (not x.fuerte, x.ambito != "proyecto"))
    return tuple(unicas[:_MAX_EVIDENCIA])


def _marcos_sobre(detectados: list[AgenteDetectado], catalogo: list[dict], proyecto: str, home: str) -> list[AgenteDetectado]:
    """Cada marco, «instalado sobre» los agentes detectados cuyas carpetas toca (p. ej. ``.claude/skills/bmad-*`` → Claude Code)."""
    carpetas: dict[str, set[str]] = {}
    for a in catalogo:
        if a.get("id") in MARCOS or a.get("id") in OMITIDOS:
            continue
        for e in a.get("proyecto") or []:
            ruta = _normal(e.get("ruta", ""))
            if "/" in ruta and not ruta.startswith(("*", "_")):
                carpetas.setdefault(ruta.split("/")[0], set()).add(a["id"])
    ids = {d.id for d in detectados if not d.marco}
    salida = []
    for d in detectados:
        if d.marco:
            tocados: set[str] = set()
            for x in d.evidencia:
                base = proyecto if x.ambito == "proyecto" else home
                if base and x.ambito != "entorno" and os.path.isabs(x.ruta):
                    tocados |= carpetas.get(_carpeta_de_nivel_superior(x.ruta, base), set())
            d = AgenteDetectado(d.id, d.nombre, d.confianza, True, tuple(sorted(tocados & ids)), d.evidencia, False)
        salida.append(d)
    return salida


def _no_determinados(detectados: list[AgenteDetectado], catalogo: list[dict], proyecto: str) -> tuple[NoDeterminado, ...]:
    """Un rastro compartido (``AGENTS.md``) sin ningún agente claro: se dice «no determinado» con los candidatos, no se adivina."""
    if any(d.confianza is Confianza.ALTA and not d.marco for d in detectados):
        return ()
    salida = []
    for nombre in ("AGENTS.md",):
        ruta = os.path.join(proyecto, nombre)
        if os.path.lexists(ruta):
            candidatos = tuple(a["nombre"] for a in catalogo if a.get("id") not in OMITIDOS and a.get("id") not in MARCOS and any(
                _normal(e.get("ruta", "")) == _normal(nombre) for e in a.get("proyecto") or []))
            if candidatos:
                salida.append(NoDeterminado(ruta, candidatos))
    return tuple(salida)
