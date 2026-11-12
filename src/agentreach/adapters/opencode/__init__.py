"""Adaptador de opencode (Historia 10): reglas de permisos de ``opencode.json`` con "gana la última".

Capacidad: *auditar y advertir*. Lee, solo en lectura y con la lectura segura, la configuración de
opencode: la global (``~/.config/opencode``), la del proyecto (``opencode.json`` y ``opencode.jsonc``) y la
gestionada (``%ProgramData%\\opencode``). Global y gestionada están fuera del proyecto, así que solo se
leen con el opt-in de la Historia 5; sin él salen como ``NoRevisado(ubicacion_sensible_sin_activar)``
[SUPUESTO, igual que el adaptador de Claude Code].

Cómo decide opencode (PRD, pregunta 25 cerrada el 2026-11-09): combina las reglas EN ORDEN y usa la
**última que coincide**, no la más específica; el orden es base, global, proyecto y gestionada. Es lo
opuesto a Claude Code (donde ``deny`` gana a ``ask`` y a ``allow``). La base pregunta antes de leer
``*.env`` y ``*.env.*``; un ``read: allow`` posterior lo anula. Un archivo FUERA del proyecto lo gobierna
``external_directory`` (pregunta por defecto). El permiso de ejecutar comandos se llama ``shell`` y antes
``bash``: se aceptan los dos y se guarda como ``shell``. Un ``deny`` de ``read`` o ``edit`` no protege
frente al shell: no baja ningún hallazgo (``SECURITY.md``: el sistema de permisos "no es un sandbox").

Hallazgo propio (reglas que DEBILITAN la protección, nivel máximo potencial): un ``allow`` amplio de
``read``, ``edit`` o ``webfetch`` (TH-7) o de ``shell`` (TH-8). Una regla ``ask``/``deny`` o acotada y
``external_directory`` son contexto. Del texto de los patrones nada sale: solo archivo y línea.
Se reconoce que no hay sandbox documentado, pero eso es un hecho del resultado, no un hallazgo
(el oráculo solo pide TH-10 para Claude Code en Windows nativo).

Una configuración que no se reconoce (JSON roto, forma o valor desconocidos) da ``NoRevisado`` con motivo
``configuracion_no_interpretable`` o ``version_no_reconocida``, nunca una excepción. No se prueba contra una
instalación real de opencode (no está en este equipo): se asume 2.x.
"""

from __future__ import annotations

import os
import re
import sys
from collections.abc import Iterable

from agentreach.adapters.base import CasoConfigProyecto, Regla, ResultadoAdaptador
from agentreach.adapters.claude_code.reglas import relativa_a
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
)
from agentreach.infra.fs_solo_lectura import FsSoloLectura, carpeta_que_es_archivo
from agentreach.infra.json_con_comentarios import (
    JsoncNoInterpretable,
    ProfundidadExcedida,
    parsear_jsonc,
)
from agentreach.infra.localizador import localizar_clave

_ACCIONES = ("allow", "ask", "deny")
_BASE_READ = (("*.env", "ask"), ("*.env.*", "ask"), ("*.env.example", "allow"))  # la política base pregunta antes de leer los .env
_TH7 = {"read", "edit", "webfetch"}
_PREFIJOS_HOME = ("~/", "$HOME/")
_MAPA_POSTURA = {"allow": Postura.ALLOW, "ask": Postura.ASK, "deny": Postura.DENY}


def _gestionada_por_defecto(sistema: str) -> str:
    """[SUPUESTO] lugar de la configuración gestionada según el sistema."""
    if sistema == "win32":
        return os.path.join(os.environ.get("ProgramData") or r"C:\ProgramData", "opencode", "opencode.json")
    if sistema == "darwin":
        return "/Library/Application Support/opencode/opencode.json"
    return "/etc/opencode/opencode.json"


_SINONIMOS = {"bash": "shell", "task": "subagent", "write": "edit", "patch": "edit"}  # nombres de 1.x que 2.x renombró


def _nombre_de_herramienta(clave: str) -> str:
    return _SINONIMOS.get(clave, clave)  # el permiso de comandos se llamó bash antes de shell, y task antes de subagent


def _patron_a_regex(patron: str, ignorar_mayusculas: bool) -> re.Pattern[str]:
    """En opencode ``*`` es cualquier cosa (también ``/``) y ``?`` un carácter; se compara la ruta entera."""
    patron = patron.replace("\\", "/").removeprefix("./")  # barras de Windows y "./" del proyecto
    cuerpo = "".join(".*" if c == "*" else "." if c == "?" else re.escape(c) for c in patron)
    return re.compile(cuerpo, re.IGNORECASE if ignorar_mayusculas else 0)


class _Fuente:
    __slots__ = ("externa", "nombre", "rutas")

    def __init__(self, nombre: str, rutas: list[str], externa: bool) -> None:
        self.nombre, self.rutas, self.externa = nombre, rutas, externa


class AdaptadorOpencode:
    """Implementa ``AgentAdapter`` y ``AdaptadorBase``. ``cargar`` lee todo; las demás consultas usan lo cargado."""

    plataforma = Plataforma.OPENCODE
    capacidad = Capacidad.AUDITAR_Y_ADVERTIR

    def __init__(self, fs: ReadOnlyFs, config: Configuracion, *, ruta_gestionada: str | None = None,
                 sistema: str | None = None, fs_externo: ReadOnlyFs | None = None) -> None:
        self._fs = fs
        self._externo: ReadOnlyFs = fs_externo or FsSoloLectura()  # global y gestionada están fuera del proyecto
        self._config = config
        self._sistema = sistema or sys.platform
        self._gestionada = ruta_gestionada or _gestionada_por_defecto(self._sistema)
        self._proyecto = ""
        self._home = ""
        self._resultado: ResultadoAdaptador | None = None
        self._marcas: set[str] = set()  # "1.x" o "2.x" según la forma de cada archivo leído
        self._leidos = 0  # archivos de configuración que existían y se leyeron
        self._casos: list[CasoConfigProyecto] = []  # hechos de la configuración DEL proyecto que lanzan un programa (MCP local)

    # ---- carga ---------------------------------------------------------------------------------------------

    def cargar(self, proyecto: Ruta) -> ResultadoAdaptador:
        self._proyecto = os.path.abspath(proyecto)
        casa = self._config.home or os.path.expanduser("~")
        self._home = os.path.abspath(casa) if os.path.isabs(casa) else ""
        pendientes: list[NoRevisado] = []
        fuentes: list[_Fuente] = []
        carpeta_global: str | None = None  # la carpeta de configuración del usuario, si hay carpeta personal utilizable
        # Decisión de Alex (H2, opción A): la configuración global (del usuario) y la gestionada se leen solo por sus reglas, y desde la
        # Historia 28 solo con el permiso de segundo nivel (``lectura_fuera``): sin él no se abre ni se lista nada fuera del proyecto.
        fuera = self._config.lectura_fuera
        if not fuera:
            sin_permiso = MotivoNoRevisado.SIN_PERMISO_FUERA_DEL_PROYECTO
            pendientes.append(NoRevisado(Ruta(os.path.join(self._home, ".config", "opencode", "opencode.json") if self._home
                                              else "~/.config/opencode/opencode.json"), sin_permiso))
            pendientes.append(NoRevisado(Ruta(self._gestionada), sin_permiso))
            pendientes.append(NoRevisado(Ruta("(carpetas por encima del proyecto: opencode.json)"), sin_permiso))
        elif not self._home:  # sin carpeta personal utilizable no se busca la global en el directorio actual
            pendientes.append(NoRevisado(Ruta("~/.config/opencode"), MotivoNoRevisado.ARCHIVO_ILEGIBLE))
        else:
            xdg = os.environ.get("XDG_CONFIG_HOME") or ""
            base = xdg if os.path.isabs(xdg) else os.path.join(self._home, ".config")
            carpeta = carpeta_global = os.path.join(base, "opencode")
            fuentes.append(_Fuente("usuario", [os.path.join(carpeta, "opencode.json"), os.path.join(carpeta, "opencode.jsonc")], True))
            appdata = os.environ.get("APPDATA") or ""
            if self._sistema == "win32" and os.path.isabs(appdata):  # respaldo de Windows de la ruta global
                carpeta_w = os.path.join(appdata, "opencode")
                fuentes.append(_Fuente("usuario", [os.path.join(carpeta_w, "opencode.json"), os.path.join(carpeta_w, "opencode.jsonc")], True))
            alterna = os.environ.get("OPENCODE_CONFIG") or ""
            if os.path.isabs(alterna):  # un archivo de configuración que la persona señala por variable de entorno
                fuentes.append(_Fuente("usuario", [alterna], True))
        for padre in (self._carpetas_padre() if fuera else []):  # del más lejano al más cercano: gana la última regla
            fuentes.append(_Fuente("proyecto", [os.path.join(padre, "opencode.json"), os.path.join(padre, "opencode.jsonc")], True))
        fuentes.append(_Fuente("proyecto", [os.path.join(self._proyecto, "opencode.json"),
                                            os.path.join(self._proyecto, "opencode.jsonc")], False))
        gestionada = [self._gestionada]
        if self._gestionada.endswith(".json"):
            gestionada.append(self._gestionada + "c")  # también ``opencode.jsonc``
        if fuera:
            fuentes.append(_Fuente("gestionada", gestionada, True))
        carpeta_local = os.path.join(self._proyecto, ".opencode")
        fuentes.insert(
            [f.nombre for f in fuentes].index("proyecto") + 1,  # ``.opencode/`` manda sobre el ``opencode.json`` de la raíz
            _Fuente("proyecto", [os.path.join(carpeta_local, "opencode.json"), os.path.join(carpeta_local, "opencode.jsonc")], False),
        )
        self._marcas, self._casos, self._leidos = set(), [], 0
        self._agentes_con_permisos(carpeta_local, self._fs, pendientes)
        if carpeta_global is not None:  # los agentes globales (~/.config/opencode/agents) también se cargan (documentación de opencode)
            self._agentes_con_permisos(carpeta_global, self._externo, pendientes)
        reglas: list[Regla] = []
        for fuente in fuentes:  # el orden importa: gana la última regla que coincide
            for ruta in fuente.rutas:
                reglas += self._reglas_de(fuente, ruta, pendientes)
        self._resultado = ResultadoAdaptador(
            reglas=tuple(reglas),
            sandbox_disponible=False,  # opencode no documenta un sandbox: su sistema de permisos "no es un sandbox"
            no_revisados=tuple(pendientes),
            reglas_incompletas=bool(pendientes),  # una fuente de reglas no se leyó o no se entendió (H1 y H4): no se sabe qué hay
            config_proyecto=tuple(self._casos),
            esquema=self._esquema(),
            causas_no_determinado=tuple(pendientes),
        )
        return self._resultado

    def _carpetas_padre(self) -> list[str]:
        """Carpetas por encima del proyecto hasta la raíz del repositorio (la que tiene ``.git``), de la más lejana a la más cercana.

        opencode busca su ``opencode.json`` hacia arriba hasta la raíz del repo; sin ``.git`` arriba no hay raíz que alcanzar
        y no se mira nada fuera del proyecto. Solo se comprueba que ``.git`` exista (``lexists``): no se abre ni se ejecuta git.
        """
        padres: list[str] = []
        actual = self._proyecto
        if os.path.lexists(os.path.join(actual, ".git")):
            return []  # el proyecto ya es la raíz
        while True:
            superior = os.path.dirname(actual)
            if superior == actual:
                return []  # se llegó a la raíz del disco sin encontrar un repositorio
            padres.append(superior)
            if os.path.lexists(os.path.join(superior, ".git")):
                return list(reversed(padres))
            actual = superior

    def _fs_de(self, externa: bool) -> ReadOnlyFs:
        return self._externo if externa else self._fs

    def _metadatos(self, fs: ReadOnlyFs, ruta: str, pendientes: list[NoRevisado]) -> Metadatos | None:
        try:
            return fs.metadatos(Ruta(ruta))
        except (OSError, ValueError, ArchivoNoLegible):  # una ruta rara no rompe la carga
            pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.ARCHIVO_ILEGIBLE))
            return None

    def _reglas_de(self, fuente: _Fuente, ruta: str, pendientes: list[NoRevisado]) -> list[Regla]:
        """Las reglas de un archivo, o ``[]`` con su ``NoRevisado``. Nunca lanza."""
        fs = self._fs_de(fuente.externa)
        if self._metadatos(fs, ruta, pendientes) is None:
            if os.path.lexists(ruta):  # existe pero no se pudo consultar (permiso): no es «no existe»
                pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.ARCHIVO_ILEGIBLE))
            else:
                impedido = carpeta_que_es_archivo(ruta)
                if impedido is not None:  # p. ej. ``.opencode`` es un archivo: no se sabe qué configuración hay detrás
                    pendientes.append(NoRevisado(Ruta(impedido), MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE))
            return []  # si no existe: es lo normal
        try:
            texto = fs.leer_texto(Ruta(ruta))
        except (ArchivoNoLegible, OSError, ValueError) as error:
            pendientes.append(NoRevisado(Ruta(ruta), getattr(error, "motivo", None) or MotivoNoRevisado.ARCHIVO_ILEGIBLE))
            return []
        try:
            datos = parsear_jsonc(texto, rechazar_repetidas=True)  # una clave repetida: cada lector se queda con otra
        except ProfundidadExcedida:
            pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA))
            return []
        except JsoncNoInterpretable as error:
            pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE, clave=getattr(error, "clave", "")))
            return []
        reglas = self._extraer(fuente, ruta, datos, texto) if isinstance(datos, dict) else None
        if reglas is None:  # una forma o un valor que este adaptador no conoce: otra versión del esquema
            pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.VERSION_NO_RECONOCIDA))
            return []
        for clave in self._funciones_no_modeladas(datos):
            # permisos por agente, ``tools`` y ``mode`` (esquema 1.x): cambian qué puede leer el agente y no se modelan (H4 y H5):
            # se conservan las reglas generales y se avisa (con la clave, sin valores); el nivel queda sin determinar
            pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.FUNCION_NO_MODELADA, clave=clave))
        return reglas

    @staticmethod
    def _funciones_no_modeladas(datos: dict) -> list[str]:
        """Los NOMBRES (de una lista fija: nunca texto del archivo) de lo que cambia qué puede leer el agente y no se modela."""
        claves = [k for k in ("tools", "mode", "plugin", "plugins") if k in datos]  # plugin(s): código con la autoridad del usuario
        experimental = datos.get("experimental")
        if isinstance(experimental, dict) and "policies" in experimental:
            claves.append("experimental.policies")
        for clave in ("agent", "agents"):
            agentes = datos.get(clave)
            if not isinstance(agentes, dict):
                continue
            propios = [a for a in agentes.values() if isinstance(a, dict)]
            if any("permission" in a or "permissions" in a for a in propios):
                claves.append(f"{clave}.*.permission" + ("s" if any("permissions" in a for a in propios) else ""))
            if any("tools" in a for a in propios):
                claves.append(f"{clave}.*.tools")
        return claves

    @staticmethod
    def _linea(texto: str, *ruta_clave: str) -> int | Linea:
        return localizar_clave(texto, "jsonc", tuple(ruta_clave)) or Linea.NO_DETERMINADA

    def _extraer(self, fuente: _Fuente, ruta: str, datos: dict, texto: str) -> list[Regla] | None:
        """Las reglas en el orden del archivo, o ``None`` si algo no se reconoce (todo o nada por archivo)."""
        self._leidos += 1
        self._marcar(fuente, ruta, datos, texto)
        permiso = datos.get("permission")
        lista = datos.get("permissions")
        extra: list[Regla] = []
        if lista is not None:  # esquema 2.x: lista ordenada de {action, resource, effect}
            extra = self._reglas_de_lista(fuente, ruta, lista, texto)
            if extra is None:  # type: ignore[comparison-overlap]
                return None
        if permiso is None:
            return extra

        def regla(accion: str, herramienta: str, patron: str | None, *clave: str) -> Regla:
            return Regla(accion, herramienta, Location(Ruta(ruta), self._linea(texto, *clave)), patron, fuente.nombre)

        if isinstance(permiso, str):  # "permission": "allow" alcanza a todas las acciones
            return [regla(permiso, "*", None, "permission"), *extra] if permiso in _ACCIONES else None
        if not isinstance(permiso, dict):
            return None
        reglas: list[Regla] = []
        for clave, valor in permiso.items():
            herramienta = _nombre_de_herramienta(str(clave))
            if isinstance(valor, str):
                if valor not in _ACCIONES:
                    return None
                reglas.append(regla(valor, herramienta, None, "permission", clave))
            elif isinstance(valor, dict):
                for patron, accion in valor.items():
                    if not isinstance(accion, str) or accion not in _ACCIONES:
                        return None
                    reglas.append(regla(accion, herramienta, str(patron), "permission", clave, patron))
            else:
                return None
        return [*reglas, *extra]  # la forma 1.x primero: la 2.x la acepta y la traduce «en memoria», como fuente secundaria

    def _reglas_de_lista(self, fuente: _Fuente, ruta: str, lista: object, texto: str) -> list[Regla] | None:
        """Las reglas de ``permissions`` (2.x), en el orden de la lista, o ``None`` si alguna entrada no se reconoce."""
        if not isinstance(lista, list):
            return None
        reglas: list[Regla] = []
        for i, e in enumerate(lista):
            if not isinstance(e, dict) or e.get("effect") not in _ACCIONES or not isinstance(e.get("action"), str):
                return None
            recurso = e.get("resource")
            if recurso is not None and not isinstance(recurso, str):
                return None
            ubicacion = Location(Ruta(ruta), self._linea_lista(texto, i))
            reglas.append(Regla(e["effect"], _nombre_de_herramienta(e["action"]), ubicacion, recurso, fuente.nombre))
        return reglas

    @staticmethod
    def _linea_lista(texto: str, indice: int) -> int | Linea:
        return localizar_clave(texto, "jsonc", ("permissions", indice)) or Linea.NO_DETERMINADA

    # ---- esquema, MCP y agentes con permisos propios --------------------------------------------------------------------------

    def _marcar(self, fuente: _Fuente, ruta: str, datos: dict, texto: str) -> None:
        """Anota por la forma del archivo si es esquema 1.x o 2.x (no hay versión dentro del archivo) y recoge los servidores MCP locales."""
        if (isinstance(datos.get("permissions"), list) and datos["permissions"]) or any(k in datos for k in ("agents", "plugins", "commands", "providers", "update")):
            self._marcas.add("2.x")
        if (isinstance(datos.get("permission"), str) or (isinstance(datos.get("permission"), dict) and datos["permission"])) or any(
                k in datos for k in ("agent", "plugin", "command", "provider", "autoupdate", "tools", "mode")):
            self._marcas.add("1.x")
        mcp = datos.get("mcp")
        if isinstance(mcp, dict):
            servidores = mcp.get("servers")
            if isinstance(servidores, dict) and "type" not in servidores and all(isinstance(v, dict) for v in servidores.values()):  # 2.x: mcp.servers.<nombre>, ``disabled`` apaga
                self._marcas.add("2.x")
                lista, apaga = servidores, lambda s: s.get("disabled") is True
                prefijo: tuple[str, ...] = ("mcp", "servers")
            else:  # 1.x: mcp.<nombre>, ``enabled: false`` apaga
                if any(isinstance(v, dict) and "type" in v for v in mcp.values()):
                    self._marcas.add("1.x")
                lista, apaga = mcp, lambda s: s.get("enabled") is False
                prefijo = ("mcp",)
            if fuente.nombre == "proyecto":
                self._servidores_locales(ruta, texto, lista, apaga, prefijo)

    def _servidores_locales(self, ruta: str, texto: str, servidores: dict, apaga, prefijo: tuple[str, ...]) -> None:
        for nombre, s in servidores.items():
            if not isinstance(s, dict) or apaga(s):
                continue
            if s.get("type") == "local" or isinstance(s.get("command"), (list, str)):  # arranca un programa al abrir la carpeta
                self._casos.append(CasoConfigProyecto("mcp", Location(Ruta(ruta), self._linea(texto, *prefijo, str(nombre)))))

    def _agentes_con_permisos(self, carpeta_base: str, fs: ReadOnlyFs, pendientes: list[NoRevisado]) -> None:
        """Un agente de ``<base>/agent(s)/*.md`` con ``permission(s)``/``tools`` en su encabezado cambia lo que puede leer: no se modela."""
        for nombre in ("agent", "agents", "mode", "modes"):
            carpeta = os.path.join(carpeta_base, nombre)

            def ilegible(error: OSError, carpeta: str = carpeta) -> None:  # una carpeta que existe y no se pudo listar no es «no existe»
                if not isinstance(error, (FileNotFoundError, NotADirectoryError)):
                    pendientes.append(NoRevisado(Ruta(getattr(error, "filename", None) or carpeta), MotivoNoRevisado.ARCHIVO_ILEGIBLE))

            try:
                archivos = sorted(
                    os.path.join(raiz, f)
                    for raiz, _, fs_ in os.walk(carpeta, followlinks=False, onerror=ilegible) for f in fs_ if f.lower().endswith(".md"))
            except OSError as error:
                ilegible(error)
                continue
            for ruta in archivos:
                try:
                    texto = fs.leer_texto(Ruta(ruta))
                except (ArchivoNoLegible, OSError, ValueError) as error:
                    pendientes.append(NoRevisado(Ruta(ruta), getattr(error, "motivo", None) or MotivoNoRevisado.ARCHIVO_ILEGIBLE))
                    continue
                m = re.match(r"\A\s*---\r?\n(.*?)\r?\n---", texto.removeprefix(chr(0xFEFF)), re.DOTALL)
                clave = re.search(r"(?m)^\s*[\"']?(permission|permissions|tools)[\"']?\s*:", m.group(1)) if m else None
                if clave:
                    pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.FUNCION_NO_MODELADA, clave=clave.group(1)))

    def _esquema(self) -> str:
        """``1.x`` o ``2.x`` si todos los archivos coinciden; ``ambiguo`` si se mezclan o ninguna clave lo decide."""
        if self._leidos == 0:
            return ""  # sin ningún archivo de opencode no hay esquema que decir (el peor caso rige igual para lo que depende de la versión)
        return next(iter(self._marcas)) if len(self._marcas) == 1 else "ambiguo"

    # ---- consultas sobre lo cargado -----------------------------------------------------------------------------

    def _expandir(self, patron: str) -> str:
        patron = patron.replace("\\", "/") if patron[:1] in ("~", "$") else patron  # ~\* y $HOME\* se escriben así en Windows
        casa = self._home.replace("\\", "/").rstrip("/")
        for solo in ("~", "$HOME", "${HOME}"):
            if patron == solo:
                return casa
            if patron.startswith(solo + "/"):
                return casa + "/" + patron[len(solo) + 1:]
        return patron

    def _ultima_coincidencia(self, candidatas: tuple[str, ...], herramientas: tuple[str, ...], con_base: bool) -> tuple[str | None, Regla | None]:
        """La acción de la ÚLTIMA regla que coincide (base, global, proyecto, gestionada) y la regla si es de un archivo.

        ``candidatas`` son las formas de la ruta que un patrón puede nombrar (relativa al proyecto y absoluta).
        """
        ignorar = self._sistema in ("win32", "darwin")  # sistemas que no distinguen mayúsculas
        accion: str | None = None
        origen: Regla | None = None
        if con_base:
            for patron, a in _BASE_READ:
                if any(_patron_a_regex(patron, ignorar).fullmatch(c) for c in candidatas):
                    accion, origen = a, None
        for r in self._resultado.reglas if self._resultado else ():
            if r.herramienta not in herramientas:
                continue
            if r.especificador is None or any(
                _patron_a_regex(self._expandir(r.especificador), ignorar).fullmatch(c) for c in candidatas
            ):
                accion, origen = r.accion, r
        return accion, origen

    def _decidir(self, ruta: Ruta) -> tuple[str | None, Regla | None]:
        if self._resultado is None:
            return None, None
        try:
            absoluta = os.path.abspath(ruta if os.path.isabs(ruta) else os.path.join(self._proyecto, ruta))
        except ValueError:  # una ruta con caracteres imposibles
            return None, None
        posix = absoluta.replace("\\", "/")
        relativa = relativa_a(absoluta, self._proyecto)
        if relativa is None:  # fuera del proyecto: lo gobierna external_directory
            accion, origen = self._ultima_coincidencia((posix,), ("external_directory", "*"), False)
            # sin regla escrita: 1.x pregunta (ask) y 2.x lo permite (allow); sin saber la versión se toma el peor caso (allow)
            accion = accion or ("ask" if self._resultado.esquema == "1.x" else "allow")
            lectura, origen_lectura = self._ultima_coincidencia((posix,), ("read", "*"), True)  # también rige read (y la base de los .env)
            peso = {"allow": 0, "ask": 1, "deny": 2}
            if lectura is not None and peso[lectura] > peso[accion]:
                return lectura, origen_lectura
            return accion, origen
        return self._ultima_coincidencia((relativa, posix), ("read", "*"), True)

    def postura_para(self, ruta: Ruta) -> Postura:
        """Postura de lectura de ``ruta``: la de la última regla que coincide; sin regla de ningún tipo, sin regla."""
        if self._resultado is None or self._resultado.reglas_incompletas:
            return Postura.NO_DETERMINADA  # regla de la 11b: si no se entiende un archivo de configuración, no hay «comprobado»
        accion, _ = self._decidir(ruta)
        if accion is None:
            return Postura.SIN_REGLA
        return _MAPA_POSTURA[accion]

    def regla_para(self, ruta: Ruta) -> Location | None:
        """Archivo y línea de la regla que decide; ``None`` si decide la política base (no hay archivo que citar)."""
        _, origen = self._decidir(ruta)
        return origen.ubicacion if origen else None


class DetectorOpencode:
    """Hallazgo propio solo cuando una regla DEBILITA la protección: allow amplio de read/edit/webfetch (TH-7) o shell (TH-8).

    ``resultado`` y ``no_revisados`` quedan con lo de la última llamada a ``detectar``.
    """

    def __init__(self, adaptador: AdaptadorOpencode) -> None:
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
        reglas = self.resultado.reglas
        for i, regla in enumerate(reglas):
            if regla.accion != "allow" or not _es_amplia(regla):
                continue
            if any(
                posterior.accion != "allow" and _es_amplia(posterior)
                and posterior.herramienta in (regla.herramienta, "*")
                for posterior in reglas[i + 1:]
            ):
                continue  # gana la última: una regla posterior ask/deny amplia la anula y ya no debilita nada
            if regla.herramienta in _TH7 or regla.herramienta == "*":
                hallazgos.append(_hallazgo(regla.ubicacion, Tipo.REGLA_PERMISIVA))
            if regla.herramienta in ("shell", "*"):
                hallazgos.append(_hallazgo(regla.ubicacion, Tipo.CAPACIDAD_DE_SHELL))
        for caso in self.resultado.config_proyecto:  # servidores MCP locales del proyecto: arrancan un programa al abrir la carpeta
            if caso.clave == "mcp":
                hallazgos.append(_hallazgo(caso.ubicacion, Tipo.HOOK_O_MCP_DE_COMANDO))
        return hallazgos


def _es_amplia(regla: Regla) -> bool:
    """Alcanza a cualquier ruta: sin patrón, o un patrón que acepta todo (``*``, ``**``, ``*/*``...)."""
    if regla.especificador is None:
        return True
    patron = _patron_a_regex(regla.especificador, False)  # amplia = acepta todas estas formas (``x/*`` o ``*z`` no lo son)
    return all(patron.fullmatch(c) for c in ("x/y/z", "q/w", "C:/x/y"))


def _hallazgo(ubicacion: Location, tipo: Tipo) -> Finding:
    return Finding(
        ubicacion=ubicacion,
        tipo=tipo,
        proveedor=Proveedor.NO_APLICA,
        nivel=Nivel.HIPOTESIS,  # provisional: la Historia 11 calcula el nivel (potencial como máximo)
        motivo=Motivo.NO_DETERMINADO,
        ajeno_a_tarea=Ajeno.NO_DETERMINADO,
        plataforma=Plataforma.OPENCODE,
        agente=Etiqueta("sin-agente"),
        postura=Postura.NO_DETERMINADA,
    )
