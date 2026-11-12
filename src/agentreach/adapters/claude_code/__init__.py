"""Adaptador de Claude Code (Historia 9): reglas de permisos, entorno, sandbox y definiciones de agente.

Capacidad: *auditar y advertir* (no bloquea nada). Lee, solo en lectura y con la lectura segura, la
configuración de Claude Code de cuatro niveles: gestionada, local, del proyecto y de usuario. Las dos
últimas fuentes fuera del proyecto (usuario y gestionada) se leen SIEMPRE, solo por sus reglas (decisión H2,
opción A); del bloque ``env`` de esas fuentes no se lee nada.

Las reglas ``allow``/``ask``/``deny`` son CONTEXTO del campo "reglas del agente", no hallazgo propio
(decisión del 2026-11-09). Solo son hallazgo la ausencia de sandbox en Windows nativo (TH-10, CA-02) y las
definiciones de agente (TH-11, CA-05). Del bloque ``env`` solo salen los nombres. AgentReach no ejecuta
Claude Code, así que no ve qué versión hay instalada (FR-21).
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Iterable
from dataclasses import dataclass

from agentreach.adapters.base import (
    CasoConfigProyecto,
    DefinicionAgente,
    Regla,
    ResultadoAdaptador,
)
from agentreach.adapters.claude_code.reglas import (
    PRECEDENCIA_ACCION,
    PRECEDENCIA_FUENTE,
    coincide,
    parsear_regla,
    patron_indeterminable,
)
from agentreach.config import Configuracion
from agentreach.contracts import (
    Ajeno,
    ArchivoNoLegible,
    Capacidad,
    Etiqueta,
    Finding,
    Linea,
    Location,
    Metadatos,
    Motivo,
    MotivoNoRevisado,
    Nivel,
    NoRevisado,
    Plataforma,
    Postura,
    Proveedor,
    ReadOnlyFs,
    Ruta,
    Tipo,
    etiqueta,
    limpiar_ruta,
)
from agentreach.infra.fs_solo_lectura import FsSoloLectura, carpeta_que_es_archivo
from agentreach.infra.lectura_segura import revisar_profundidad_json
from agentreach.infra.localizador import localizar_clave

_VARIABLE_LIMPIEZA = "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB"
_VERDADEROS = ("1", "true", "yes", "on")
_SALTO = "\n"
_MAX_NOMBRE_ENTORNO = 100


def _gestionada_por_defecto(sistema: str) -> str:
    """[SUPUESTO] lugar de la configuración gestionada según el sistema (documentación de Claude Code)."""
    if sistema == "win32":
        return os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "ClaudeCode", "managed-settings.json")
    if sistema == "darwin":
        return "/Library/Application Support/ClaudeCode/managed-settings.json"
    return "/etc/claude-code/managed-settings.json"


@dataclass(frozen=True, slots=True)
class _Fuente:
    nombre: str  # "gestionada", "local", "proyecto" o "usuario"
    ruta: str
    externa: bool  # fuera del proyecto: usa el sistema de archivos sin raíz


class AdaptadorClaudeCode:
    """Implementa ``AgentAdapter`` y ``AdaptadorBase``. ``cargar`` lee todo; las demás consultas usan lo cargado."""

    plataforma = Plataforma.CLAUDE_CODE
    capacidad = Capacidad.AUDITAR_Y_ADVERTIR

    def __init__(self, fs: ReadOnlyFs, config: Configuracion, *, ruta_gestionada: str | None = None,
                 sistema: str | None = None) -> None:
        self._fs = fs
        self._externo: ReadOnlyFs = FsSoloLectura()  # usuario y gestionada están fuera del proyecto
        self._config = config
        self._sistema = sistema or sys.platform
        self._gestionada = ruta_gestionada or _gestionada_por_defecto(self._sistema)
        self._proyecto = ""
        self._home = ""
        self._resultado: ResultadoAdaptador | None = None

    # ---- carga ---------------------------------------------------------------------------------------------

    def cargar(self, proyecto: Ruta) -> ResultadoAdaptador:
        self._proyecto = os.path.abspath(proyecto)
        encendido = self._config.incluir_ubicaciones_sensibles  # solo gobierna lo que NO son reglas (los agentes del usuario)
        casa = self._config.home or os.path.expanduser("~")
        self._home = os.path.abspath(casa) if os.path.isabs(casa) else ""  # una ruta relativa podría caer dentro del proyecto auditado
        pendientes: list[NoRevisado] = []
        antes = 0  # todo lo que se anote desde aquí (incluida la falta de carpeta personal) deja las reglas incompletas
        # Decisión de Alex (H2, opción A): la configuración gestionada y la del usuario se leen SIEMPRE, solo por sus reglas
        # (de ``env`` solo salen los nombres, nunca los valores): sin ellas el nivel de un archivo no se puede decidir bien.
        fuera = self._config.lectura_fuera  # Historia 28: sin el permiso de segundo nivel no se abre NI SE LISTA nada fuera del proyecto
        fuentes: list[_Fuente] = [
            _Fuente("local", os.path.join(self._proyecto, ".claude", "settings.local.json"), False),
            _Fuente("proyecto", os.path.join(self._proyecto, ".claude", "settings.json"), False),
        ]
        if fuera:
            fuentes.insert(0, _Fuente("gestionada", self._gestionada, True))
            if self._home:
                fuentes.append(_Fuente("usuario", os.path.join(self._home, ".claude", "settings.json"), True))
            else:  # sin carpeta personal utilizable no se busca la configuración de usuario en el directorio actual
                pendientes.append(NoRevisado(Ruta("~/.claude"), MotivoNoRevisado.ARCHIVO_ILEGIBLE))
            fuentes[1:1] = self._fragmentos_gestionados(pendientes)
        else:  # las reglas de fuera del proyecto no se leen: se dice cuáles, y los niveles que dependen de ellas quedan en potencial
            sin_permiso = MotivoNoRevisado.SIN_PERMISO_FUERA_DEL_PROYECTO
            pendientes.append(NoRevisado(Ruta(os.path.join(self._home, ".claude", "settings.json") if self._home else "~/.claude/settings.json"), sin_permiso))
            pendientes.append(NoRevisado(Ruta(self._gestionada), sin_permiso))

        reglas: list[Regla] = []
        nombres: dict[str, None] = {}
        limpieza: bool | None = None  # lo decide la fuente de mayor precedencia que define la variable
        casos: list[CasoConfigProyecto] = []
        for fuente in fuentes:
            leido = self._leer_configuracion(fuente, pendientes)
            if leido is None:
                continue
            datos, texto = leido
            reglas += self._extraer_reglas(fuente, datos, texto, pendientes)
            for clave in self._claves_que_cambian_lo_que_se_lee(datos):  # algo que altera qué puede leer el agente y que aquí no se modela
                pendientes.append(NoRevisado(Ruta(fuente.ruta), MotivoNoRevisado.FUNCION_NO_MODELADA, clave=clave))
            if fuente.nombre in ("local", "proyecto"):  # la configuración DEL proyecto
                entorno = datos.get("env") or {}  # (de usuario y gestionada se leen solo las reglas: nunca el bloque env, decisión H2)
                for nombre in entorno:  # solo los nombres, sin caracteres de control y con largo acotado
                    nombres.setdefault(limpiar_ruta(str(nombre))[:_MAX_NOMBRE_ENTORNO])
                if limpieza is None and _VARIABLE_LIMPIEZA in entorno:
                    limpieza = str(entorno[_VARIABLE_LIMPIEZA]).strip().lower() in _VERDADEROS
                casos += self._casos_del_proyecto(fuente, datos, texto)  # lo que se ejecuta solo
        incompletas = len(pendientes) > antes  # una fuente de reglas existe y no se leyó o no se entendió: no se sabe qué reglas hay
        for r in reglas:  # un patrón que no se interpreta se dice (el nivel ya baja cuando alcanza al archivo)
            if r.herramienta == "Read" and r.especificador is not None and patron_indeterminable(r.especificador.strip()):
                nota = NoRevisado(Ruta(r.ubicacion.ruta), MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE,
                                  clave=f"permissions.{r.accion}" if r.accion in ("allow", "ask", "deny") else "permissions")
                if nota not in pendientes:
                    pendientes.append(nota)
        causas = tuple(pendientes[antes:])  # lo que dejó reglas sin entender (antes de agregar los agentes del usuario)
        agentes = self._agentes(pendientes, encendido and fuera)
        self._resultado = ResultadoAdaptador(
            reglas=tuple(reglas),
            entorno_nombres=tuple(nombres),
            limpieza_de_entorno=bool(limpieza),
            agentes=agentes,
            config_proyecto=tuple(casos),
            sandbox_disponible=False if self._sistema == "win32" else None,  # Windows nativo: sin sandbox
            no_revisados=tuple(pendientes),
            reglas_incompletas=incompletas,
            causas_no_determinado=causas,
        )
        return self._resultado

    def _fs_de(self, fuente_externa: bool) -> ReadOnlyFs:
        return self._externo if fuente_externa else self._fs

    def _metadatos(self, fs: ReadOnlyFs, ruta: str, pendientes: list[NoRevisado]) -> Metadatos | None:
        try:
            return fs.metadatos(Ruta(ruta))
        except (OSError, ValueError, ArchivoNoLegible):  # una ruta rara no rompe la carga
            pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.ARCHIVO_ILEGIBLE))
            return None

    def _leer_texto(self, fs: ReadOnlyFs, ruta: str, pendientes: list[NoRevisado]) -> str | None:
        try:
            return fs.leer_texto(Ruta(ruta))
        except (ArchivoNoLegible, OSError, ValueError) as error:
            motivo = getattr(error, "motivo", None) or MotivoNoRevisado.ARCHIVO_ILEGIBLE
            pendientes.append(NoRevisado(Ruta(ruta), motivo))
            return None

    def _leer_configuracion(self, fuente: _Fuente, pendientes: list[NoRevisado]) -> tuple[dict, str] | None:
        """El JSON de un archivo de configuración, o ``None`` (con su ``NoRevisado``). Nunca lanza."""
        fs = self._fs_de(fuente.externa)
        if self._metadatos(fs, fuente.ruta, pendientes) is None:
            if os.path.lexists(fuente.ruta):  # existe pero no se pudo consultar (permiso): no es «no existe»
                pendientes.append(NoRevisado(Ruta(fuente.ruta), MotivoNoRevisado.ARCHIVO_ILEGIBLE))
            else:
                impedido = carpeta_que_es_archivo(fuente.ruta)
                if impedido is not None:  # p. ej. ``.claude`` es un archivo: no se sabe qué configuración hay detrás
                    pendientes.append(NoRevisado(Ruta(impedido), MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE))
            return None  # si no existe: es lo normal
        texto = self._leer_texto(fs, fuente.ruta, pendientes)
        if texto is None:
            return None
        ruta = Ruta(fuente.ruta)
        excedido = revisar_profundidad_json(ruta, texto)
        if excedido is not None:
            pendientes.append(excedido)
            return None
        try:
            datos = json.loads(texto)
        except (ValueError, RecursionError):
            pendientes.append(NoRevisado(ruta, MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE))
            return None
        if not self._con_forma_conocida(datos):
            pendientes.append(NoRevisado(ruta, MotivoNoRevisado.VERSION_NO_RECONOCIDA))
            return None
        return datos, texto

    def _fragmentos_gestionados(self, pendientes: list[NoRevisado]) -> list[_Fuente]:
        """``managed-settings.d/*.json`` junto al archivo gestionado, en orden alfabético (la documentación los combina)."""
        carpeta = os.path.join(os.path.dirname(self._gestionada), "managed-settings.d")
        try:
            nombres = sorted(n for n in os.listdir(carpeta) if n.lower().endswith(".json"))
        except (FileNotFoundError, NotADirectoryError):
            return []  # no existe: es lo normal
        except OSError:  # existe y no se pudo listar (permiso): puede traer reglas deny, no es «no existe»
            pendientes.append(NoRevisado(Ruta(carpeta), MotivoNoRevisado.ARCHIVO_ILEGIBLE))
            return []
        return [_Fuente("gestionada", os.path.join(carpeta, n), True) for n in nombres]

    @staticmethod
    def _claves_que_cambian_lo_que_se_lee(datos: dict) -> list[str]:
        """Claves (solo sus nombres, de una lista fija) que alteran qué puede leer el agente y no se interpretan: un hook ``PreToolUse``
        (puede bloquear una lectura), el sandbox de archivos y la política que ignora las reglas del proyecto."""
        claves = []
        hooks = datos.get("hooks")
        if isinstance(hooks, dict) and hooks.get("PreToolUse"):
            claves.append("hooks.PreToolUse")
        if "sandbox" in datos:
            claves.append("sandbox")
        if datos.get("allowManagedPermissionRulesOnly"):
            claves.append("allowManagedPermissionRulesOnly")
        return claves

    @staticmethod
    def _con_forma_conocida(datos: object) -> bool:
        """La forma que este adaptador entiende; otra cosa es una versión que no reconoce."""
        if not isinstance(datos, dict):
            return False
        permisos = datos.get("permissions", {})
        if not isinstance(permisos, dict):
            return False
        for accion in PRECEDENCIA_ACCION:
            lista = permisos.get(accion, [])
            if not isinstance(lista, list) or not all(isinstance(x, str) for x in lista):
                return False
        return isinstance(datos.get("env", {}), dict) and isinstance(datos.get("hooks", {}), (dict, list))

    # ---- reglas, casos del proyecto, agentes ------------------------------------------------------------------

    @staticmethod
    def _linea(texto: str, *ruta_clave: str | int) -> int | Linea:
        return localizar_clave(texto, "json", tuple(ruta_clave)) or Linea.NO_DETERMINADA

    def _extraer_reglas(self, fuente: _Fuente, datos: dict, texto: str, pendientes: list[NoRevisado]) -> list[Regla]:
        reglas: list[Regla] = []
        permisos = datos.get("permissions", {})
        for accion in PRECEDENCIA_ACCION[::-1]:  # allow, ask, deny
            for i, bruto in enumerate(permisos.get(accion, [])):
                partes = parsear_regla(bruto)
                if partes is None:
                    if bruto.strip():  # una regla con texto que no se entiende no se descarta en silencio
                        pendientes.append(NoRevisado(Ruta(fuente.ruta), MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE))
                    continue
                herramienta, especificador = partes
                ubicacion = Location(Ruta(fuente.ruta), self._linea(texto, "permissions", accion, i))
                reglas.append(Regla(accion, herramienta, ubicacion, especificador, fuente.nombre))
        return reglas

    def _casos_del_proyecto(self, fuente: _Fuente, datos: dict, texto: str) -> list[CasoConfigProyecto]:
        casos: list[CasoConfigProyecto] = []

        def caso(clave: str, *ruta_clave: str) -> None:
            casos.append(CasoConfigProyecto(clave, Location(Ruta(fuente.ruta), self._linea(texto, *ruta_clave))))

        hooks = datos.get("hooks")
        if (isinstance(hooks, dict) and any(hooks.values())) or (isinstance(hooks, list) and hooks):
            caso("hooks", "hooks")
        if datos.get("enableAllProjectMcpServers") is True:
            caso("mcp", "enableAllProjectMcpServers")
        elif isinstance(datos.get("enabledMcpjsonServers"), list) and any(
            isinstance(x, str) and x.strip() for x in datos["enabledMcpjsonServers"]
        ):
            caso("mcp", "enabledMcpjsonServers")  # aprueba servidores del proyecto por su nombre
        if "ANTHROPIC_BASE_URL" in (datos.get("env") or {}):
            caso("base_url", "env", "ANTHROPIC_BASE_URL")
        if (datos.get("permissions") or {}).get("defaultMode") == "bypassPermissions":
            caso("salto_de_permisos", "permissions", "defaultMode")
        return casos

    def _agentes(self, pendientes: list[NoRevisado], encendido: bool) -> tuple[DefinicionAgente, ...]:
        # [SUPUESTO] cómo se descubre un agente: .claude/agents del proyecto y, con el opt-in, el del usuario
        carpetas = [(self._fs, os.path.join(self._proyecto, ".claude", "agents"))]
        if encendido:
            carpetas.append((self._externo, os.path.join(self._home, ".claude", "agents")))
        agentes: list[DefinicionAgente] = []
        for fs, carpeta in carpetas:
            meta = self._metadatos(fs, carpeta, pendientes)
            if meta is None:
                continue
            if meta.es_enlace or not meta.es_carpeta:
                pendientes.append(NoRevisado(meta.ruta, MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR))
                continue
            try:
                entradas = list(fs.listar(meta.ruta_real or meta.ruta))
            except (OSError, ArchivoNoLegible, ValueError):
                pendientes.append(NoRevisado(meta.ruta, MotivoNoRevisado.ARCHIVO_ILEGIBLE))
                continue
            for entrada in entradas:
                if not os.path.basename(entrada.ruta).lower().endswith(".md") or entrada.es_carpeta and not entrada.es_enlace:
                    continue
                if entrada.es_enlace or not entrada.es_regular:
                    pendientes.append(NoRevisado(entrada.ruta, MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR))
                    continue
                texto = self._leer_texto(fs, entrada.ruta_real or entrada.ruta, pendientes)
                if texto is not None:
                    agentes.append(_leer_agente(entrada.ruta, texto))
        return tuple(sorted(agentes, key=lambda a: a.ruta))

    # ---- consultas sobre lo cargado -----------------------------------------------------------------------------

    def _reglas_que_alcanzan(self, ruta: Ruta) -> tuple[list[Regla], bool]:
        """Las reglas ``Read`` que alcanzan a ``ruta`` y si alguna no se pudo interpretar (entonces no se sabe si alcanza)."""
        if self._resultado is None:
            return [], False
        ignorar = self._sistema in ("win32", "darwin")  # sistemas que no distinguen mayúsculas
        if not os.path.isabs(ruta):
            ruta = Ruta(os.path.join(self._proyecto, ruta))
        alcanzan: list[Regla] = []
        indeterminado = False
        for r in self._resultado.reglas:
            if r.herramienta != "Read":
                continue
            if r.especificador is None:  # "Read" sin especificador: alcanza a todos los archivos
                alcanzan.append(r)
                continue
            veredicto = coincide(r.especificador, ruta, self._proyecto, self._home, r.fuente, ignorar)
            if veredicto is None:
                indeterminado = True
            elif veredicto:
                alcanzan.append(r)
        return alcanzan, indeterminado

    def _regla_ganadora(self, ruta: Ruta) -> tuple[Regla | None, bool]:
        """La regla que decide (la acción más fuerte y, entre iguales, la fuente de mayor precedencia) y si hubo dudas."""
        alcanzan, indeterminado = self._reglas_que_alcanzan(ruta)
        for accion in PRECEDENCIA_ACCION:
            de_la_accion = [r for r in alcanzan if r.accion == accion]
            if de_la_accion:
                return min(de_la_accion, key=lambda r: PRECEDENCIA_FUENTE.index(r.fuente)), indeterminado
        return None, indeterminado

    def postura_para(self, ruta: Ruta) -> Postura:
        """Postura de lectura de ``ruta``: deny, ask, allow o sin regla; ``NO_DETERMINADA`` si no se sabe qué reglas hay.

        Regla de la Historia 11b: si no se entiende un archivo de configuración (o un patrón), el nivel nunca es «comprobado».
        """
        if self._resultado is None or self._resultado.reglas_incompletas:
            return Postura.NO_DETERMINADA
        ganadora, indeterminado = self._regla_ganadora(ruta)
        if ganadora is not None and ganadora.accion == "deny":
            return Postura.DENY  # un deny entendido manda aunque otra regla no se entienda
        if indeterminado:
            return Postura.NO_DETERMINADA
        if ganadora is None:
            return Postura.SIN_REGLA
        return {"deny": Postura.DENY, "ask": Postura.ASK, "allow": Postura.ALLOW}[ganadora.accion]

    def regla_para(self, ruta: Ruta) -> Location | None:
        """Archivo y línea de la regla que decide la postura de ``ruta`` (campo "reglas del agente")."""
        ganadora = self._regla_ganadora(ruta)[0] if self._resultado is not None else None
        return ganadora.ubicacion if ganadora else None


def _leer_agente(ruta: Ruta, texto: str) -> DefinicionAgente:
    """Nombre y herramientas de un agente desde su encabezado ``---``. El cuerpo se descarta."""
    lineas = texto.removeprefix(chr(0xFEFF)).split(_SALTO)
    nombre: str | None = None
    herramientas: list[str] = []
    linea_herramientas: int | Linea = Linea.NO_DETERMINADA
    tiene_tools = False
    if lineas and lineas[0].strip() == "---":
        en_herramientas = False
        for numero, linea in enumerate(lineas[1:], start=2):
            if linea.strip() == "---":
                break
            clave, separador, valor = linea.partition(":")
            if separador and not linea.startswith((" ", "\t", "-")):
                en_herramientas = False
                clave = clave.strip().lower()
                valor = valor.strip().strip("'\"")
                if clave == "name":
                    try:
                        nombre = etiqueta(valor)
                    except ValueError:
                        nombre = None
                elif clave == "tools":
                    linea_herramientas = numero
                    valor = valor.removeprefix("[").removesuffix("]")  # lista entre corchetes: [Read, Edit]
                    herramientas += [t.strip().strip("'\"") for t in valor.split(",") if t.strip()]
                    en_herramientas = not valor
                    tiene_tools = True
            elif en_herramientas and linea.strip().startswith("-"):
                herramientas.append(linea.strip().lstrip("-").strip().strip("'\""))
    return DefinicionAgente(ruta, nombre, tuple(herramientas), linea_herramientas, hereda_todas=not tiene_tools)


class DetectorClaudeCode:
    """Detector de lo que el adaptador sí considera hallazgo propio: TH-10 (sandbox) y TH-11 (agentes).

    ``resultado`` y ``no_revisados`` quedan con lo de la última llamada a ``detectar``.
    """

    def __init__(self, adaptador: AdaptadorClaudeCode) -> None:
        self._adaptador = adaptador
        self.resultado: ResultadoAdaptador = ResultadoAdaptador()
        self.no_revisados: tuple[NoRevisado, ...] = ()

    @property
    def adaptador(self):  # el mismo que ya cargó la configuración: el evaluador le pregunta la postura
        return self._adaptador

    def detectar(self, proyecto: Ruta) -> Iterable[Finding]:
        self.resultado = self._adaptador.cargar(proyecto)
        self.no_revisados = self.resultado.no_revisados
        hallazgos: list[Finding] = []
        if self.resultado.sandbox_disponible is False:  # CA-02: nivel máximo potencial (no se ve la versión)
            hallazgos.append(_hallazgo(Location(Ruta("(Windows nativo)")), Tipo.PLATAFORMA_SIN_SANDBOX, None))
        for agente in self.resultado.agentes:  # CA-05
            hallazgos.append(_hallazgo(Location(agente.ruta, agente.linea_herramientas), Tipo.DEFINICION_DE_AGENTE, agente.nombre))
        return hallazgos


def _hallazgo(ubicacion: Location, tipo: Tipo, agente: str | None) -> Finding:
    return Finding(
        ubicacion=ubicacion,
        tipo=tipo,
        proveedor=Proveedor.NO_APLICA,
        nivel=Nivel.HIPOTESIS,  # provisional: la Historia 11 calcula el nivel (potencial como máximo)
        motivo=Motivo.NO_DETERMINADO,
        ajeno_a_tarea=Ajeno.NO_DETERMINADO,
        plataforma=Plataforma.CLAUDE_CODE,
        agente=Etiqueta(agente) if agente else Etiqueta("sin-agente"),
        postura=Postura.NO_DETERMINADA,
    )
