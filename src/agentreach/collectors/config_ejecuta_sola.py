"""Configuración del proyecto que se ejecuta sola o que quita los frenos del agente (TH-14, TH-15, TH-16).

Solo en el proyecto auditado y solo como TEXTO. Marca:

- TH-14: ``hooks`` y ``enableAllProjectMcpServers``/``enabledMcpjsonServers`` de Claude Code (los hechos los
  entrega el adaptador de la Historia 9) y los servidores MCP de tipo comando de ``.mcp.json``.
- TH-15: ``permissions.defaultMode: "bypassPermissions"``, ``--dangerously-skip-permissions`` y, en VS Code,
  ``chat.tools.autoApprove: true`` y ``task.allowAutomaticTasks: "on"`` (un freno desactivado).
- TH-16: tareas de ``.vscode/tasks.json`` con ``runOn: "folderOpen"`` y ``task.allowAutomaticTasks: "on"``.

Informa archivo, línea, clave y tipo. NUNCA copia el comando ni sus argumentos (pueden llevar secretos) ni
abre o ejecuta nada de lo declarado. ``rotulos`` asocia cada hallazgo con su caso ("hooks", "mcp",
"salto_de_permisos", "freno_desactivado"...) para que el reporte use el texto con la versión corregida del
catálogo de la Historia 9. Los archivos con comentarios se leen con el lector propio; lo que no se pueda
interpretar sale como ``NoRevisado``. El nivel es provisional (hipótesis; el máximo es potencial).
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable

from agentreach.adapters.claude_code import AdaptadorClaudeCode
from agentreach.contracts import (
    Ajeno,
    ArchivoNoLegible,
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
from agentreach.infra.json_con_comentarios import (
    JsoncNoInterpretable,
    ProfundidadExcedida,
    limpiar_jsonc,
    parsear_jsonc,
)
from agentreach.infra.localizador import localizar_clave

_BANDERA = re.compile(r"--(?:allow-)?dangerously-skip-permissions|--permission-mode[= ]+bypassPermissions")
_SALTO = re.compile(r"\r\n|\r|\n")
# Los hechos del adaptador de Claude Code → (tipo, rótulo). ANTHROPIC_BASE_URL queda para la fase 2.
_DEL_ADAPTADOR = {
    "hooks": (Tipo.HOOK_O_MCP_DE_COMANDO, "hooks"),
    "mcp": (Tipo.HOOK_O_MCP_DE_COMANDO, "mcp"),
    "salto_de_permisos": (Tipo.SALTO_DE_PERMISOS, "salto_de_permisos"),
}


class DetectorConfigEjecutaSola:
    """``no_revisados`` y ``rotulos`` quedan con lo de la última llamada a ``detectar``."""

    def __init__(self, fs: ReadOnlyFs, adaptador: AdaptadorClaudeCode) -> None:
        self._fs = fs
        self._adaptador = adaptador
        self.no_revisados: tuple[NoRevisado, ...] = ()
        # (ruta, línea, tipo) -> rótulos de los casos que caen ahí (dos casos en la misma línea no se pisan)
        self.rotulos: dict[tuple[str, int | Linea, str], tuple[str, ...]] = {}

    def detectar(self, proyecto: Ruta) -> Iterable[Finding]:
        self.no_revisados = ()
        self.rotulos = {}
        pendientes: list[NoRevisado] = []
        hallazgos: list[Finding] = []
        resultado = self._adaptador.cargar(proyecto)  # Claude Code: hooks, MCP y bypassPermissions
        pendientes.extend(resultado.no_revisados)
        for caso in resultado.config_proyecto:
            if caso.clave in _DEL_ADAPTADOR:
                tipo, rotulo = _DEL_ADAPTADOR[caso.clave]
                hallazgos.append(self._hallazgo(caso.ubicacion.ruta, caso.ubicacion.linea, tipo, rotulo))
        for relativa in (".claude/settings.json", ".claude/settings.local.json"):
            hallazgos += self._bandera(os.path.join(proyecto, *relativa.split("/")), pendientes)
        hallazgos += self._mcp_json(os.path.join(proyecto, ".mcp.json"), pendientes, "mcpServers")
        hallazgos += self._mcp_json(os.path.join(proyecto, ".vscode", "mcp.json"), pendientes, "servers")
        hallazgos += self._tasks(os.path.join(proyecto, ".vscode", "tasks.json"), pendientes)
        hallazgos += self._ajustes_vscode(os.path.join(proyecto, ".vscode", "settings.json"), pendientes)
        self.no_revisados = tuple(pendientes)
        return hallazgos

    # ---- lectura -----------------------------------------------------------------------------------------------------

    def _metadatos(self, ruta: str, pendientes: list[NoRevisado]) -> Metadatos | None:
        try:
            return self._fs.metadatos(Ruta(ruta))
        except (OSError, ValueError, ArchivoNoLegible):
            pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.ARCHIVO_ILEGIBLE))
            return None

    def _texto(self, ruta: str, pendientes: list[NoRevisado], informar: bool = True) -> str | None:
        """Texto con la lectura segura, o ``None`` (con su ``NoRevisado`` si ``informar``). ``None`` también si no existe."""
        if self._metadatos(ruta, pendientes) is None:
            return None
        try:
            return self._fs.leer_texto(Ruta(ruta))
        except (ArchivoNoLegible, OSError, ValueError) as error:
            if informar:
                pendientes.append(NoRevisado(Ruta(ruta), getattr(error, "motivo", None) or MotivoNoRevisado.ARCHIVO_ILEGIBLE))
            return None

    def _json(self, ruta: str, pendientes: list[NoRevisado]) -> tuple[dict | None, str | None]:
        """(objeto, texto) de un JSON con comentarios. Si no se pudo interpretar, ``datos`` es ``None`` (con su
        ``NoRevisado``) pero el ``texto`` queda para buscar la bandera. Si no se pudo leer, ambos son ``None``."""
        texto = self._texto(ruta, pendientes)
        if texto is None:
            return None, None
        try:
            datos = parsear_jsonc(texto)
        except ProfundidadExcedida:
            pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA))
            return None, texto
        except JsoncNoInterpretable:
            pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE))
            return None, texto
        if not isinstance(datos, dict):  # una forma que este lector no conoce
            pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE))
            return None, texto
        return datos, texto

    @staticmethod
    def _linea(texto: str, *ruta_clave: str | int) -> int | Linea:
        return localizar_clave(texto, "jsonc", tuple(ruta_clave)) or Linea.NO_DETERMINADA

    def _hallazgo(self, ruta: str, linea: int | Linea, tipo: Tipo, rotulo: str) -> Finding:
        ubicacion = Location(Ruta(ruta), linea)
        clave = (ubicacion.ruta, ubicacion.linea, tipo.value)
        self.rotulos[clave] = tuple(sorted({*self.rotulos.get(clave, ()), rotulo}))
        return Finding(
            ubicacion=ubicacion,
            tipo=tipo,
            proveedor=Proveedor.NO_APLICA,
            nivel=Nivel.HIPOTESIS,  # provisional: la Historia 11 lo calcula (máximo potencial)
            motivo=Motivo.NO_DETERMINADO,
            ajeno_a_tarea=Ajeno.NO_DETERMINADO,
            plataforma=Plataforma.NO_DETERMINADA,
            agente=Etiqueta("sin-agente"),
            postura=Postura.NO_DETERMINADA,
        )

    # ---- archivos ----------------------------------------------------------------------------------------------------

    def _bandera(self, ruta: str, pendientes: list[NoRevisado], texto: str | None = None) -> list[Finding]:
        """La bandera que salta los permisos, buscada en el texto SIN comentarios (si se puede limpiar).
        Del texto solo se conserva el número de línea."""
        if texto is None:
            texto = self._texto(ruta, pendientes, informar=False)  # el adaptador ya informó si no se pudo leer
        if texto is None:
            return []
        try:
            texto = limpiar_jsonc(texto)  # una mención en un comentario no cuenta
        except JsoncNoInterpretable:
            pass  # no se puede limpiar: se busca en el texto tal cual (ante la duda, se reporta)
        return [self._hallazgo(ruta, n, Tipo.SALTO_DE_PERMISOS, "bandera_salto_de_permisos")
                for n, linea in enumerate(_SALTO.split(texto), start=1) if _BANDERA.search(linea)]

    def _mcp_json(self, ruta: str, pendientes: list[NoRevisado], clave: str) -> list[Finding]:
        datos, texto = self._json(ruta, pendientes)
        if datos is None:
            return self._bandera(ruta, pendientes, texto=texto) if texto is not None else []
        servidores = datos.get(clave, {})
        if not isinstance(servidores, dict):
            pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE))
            return []
        hallazgos: list[Finding] = []
        for nombre, servidor in servidores.items():
            if not isinstance(servidor, dict) or "command" not in servidor:
                continue  # un servidor remoto (url) no arranca un programa en el equipo
            if str(servidor.get("type", "stdio")).lower() not in ("stdio", ""):
                continue
            hallazgos.append(self._hallazgo(ruta, self._linea(texto, clave, nombre, "command"),
                                            Tipo.HOOK_O_MCP_DE_COMANDO, "mcp"))
        return hallazgos + self._bandera(ruta, pendientes, texto=texto)

    def _tasks(self, ruta: str, pendientes: list[NoRevisado]) -> list[Finding]:
        datos, texto = self._json(ruta, pendientes)
        if datos is None:
            return self._bandera(ruta, pendientes, texto=texto) if texto is not None else []
        tareas = datos.get("tasks", [])
        if not isinstance(tareas, list):
            pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE))
            return []
        hallazgos: list[Finding] = []
        malformada = False
        for i, tarea in enumerate(tareas):
            opciones = tarea.get("runOptions") if isinstance(tarea, dict) else None
            if not isinstance(tarea, dict) or (opciones is not None and not isinstance(opciones, dict)):
                malformada = True  # una entrada que no se entiende no se descarta en silencio
                continue
            if isinstance(opciones, dict) and opciones.get("runOn") == "folderOpen":
                hallazgos.append(self._hallazgo(ruta, self._linea(texto, "tasks", i, "runOptions", "runOn"),
                                                Tipo.TAREA_AL_ABRIR_CARPETA, "tarea_al_abrir"))
        if malformada:
            pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE))
        return hallazgos + self._bandera(ruta, pendientes, texto=texto)

    def _ajustes_vscode(self, ruta: str, pendientes: list[NoRevisado]) -> list[Finding]:
        datos, texto = self._json(ruta, pendientes)
        if datos is None:
            return self._bandera(ruta, pendientes, texto=texto) if texto is not None else []
        hallazgos: list[Finding] = []
        aprobar = datos.get("chat.tools.autoApprove")
        if aprobar is True or (isinstance(aprobar, dict) and any(v is True for v in aprobar.values())):
            linea = self._linea(texto, "chat.tools.autoApprove")
            hallazgos.append(self._hallazgo(ruta, linea, Tipo.SALTO_DE_PERMISOS, "auto_aprobar"))
        if datos.get("task.allowAutomaticTasks") == "on":  # el valor por defecto lo desactiva: con "on" se quitó el freno
            linea = self._linea(texto, "task.allowAutomaticTasks")
            hallazgos.append(self._hallazgo(ruta, linea, Tipo.TAREA_AL_ABRIR_CARPETA, "freno_desactivado"))
            hallazgos.append(self._hallazgo(ruta, linea, Tipo.SALTO_DE_PERMISOS, "freno_desactivado"))
        return hallazgos + self._bandera(ruta, pendientes, texto=texto)
