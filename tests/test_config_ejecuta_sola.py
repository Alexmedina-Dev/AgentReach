"""Historia 17: configuración del proyecto que se ejecuta sola (hooks, MCP de comando, saltar permisos, tareas)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from agentreach.adapters.claude_code import AdaptadorClaudeCode
from agentreach.collectors.config_ejecuta_sola import DetectorConfigEjecutaSola
from agentreach.config import Configuracion
from agentreach.contracts import Detector, Finding, Idioma, Nivel, Ruta, Tipo
from agentreach.contracts.no_revisado import MotivoNoRevisado
from agentreach.core.pipeline import Pipeline
from agentreach.infra.fs_solo_lectura import FsSoloLectura
from agentreach.infra.json_con_comentarios import (
    JsoncNoInterpretable,
    ProfundidadExcedida,
    limpiar_jsonc,
    parsear_jsonc,
)

CANARIO = "CANARIO-H17-sk-live-0123456789abcdef"
TH14, TH15, TH16 = Tipo.HOOK_O_MCP_DE_COMANDO, Tipo.SALTO_DE_PERMISOS, Tipo.TAREA_AL_ABRIR_CARPETA


def _escribir(ruta: Path, contenido) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if not isinstance(contenido, (str, bytes)):
        contenido = json.dumps(contenido, indent=2) + "\n"
    ruta.write_bytes(contenido if isinstance(contenido, bytes) else contenido.encode("utf-8"))  # LF también en Windows
    return ruta


def _detector(tmp: Path, fs=None) -> DetectorConfigEjecutaSola:
    fs = fs or FsSoloLectura()
    config = Configuracion(incluir_ubicaciones_sensibles=False, home=str(tmp / "home"))
    return DetectorConfigEjecutaSola(fs, AdaptadorClaudeCode(fs, config, sistema="linux"))


def _auditar(proyecto: Path, fs=None) -> tuple[list[Finding], DetectorConfigEjecutaSola]:
    detector = _detector(proyecto.parent, fs)
    return Pipeline([detector]).ejecutar(Ruta(str(proyecto))), detector


def _tipos(hallazgos: list[Finding]) -> list[Tipo]:
    return sorted((h.tipo for h in hallazgos), key=lambda t: t.value)


def _salida(hallazgos, detector) -> str:
    return (repr(hallazgos) + repr(detector.no_revisados) + repr(detector.rotulos)
            + "".join(str(h.a_dict(i)) for h in hallazgos for i in Idioma))


def _avisos(detector) -> list:
    """Los NoRevisado de verdad, sin los dos fijos de "ubicación sensible sin activar"."""
    return [n for n in detector.no_revisados if n.motivo is not MotivoNoRevisado.UBICACION_SENSIBLE_SIN_ACTIVAR]


def _rotulo(detector, h: Finding) -> str:
    return "+".join(detector.rotulos[(h.ubicacion.ruta, h.ubicacion.linea, h.tipo.value)])


def _nombre(h: Finding) -> str:
    return os.path.basename(h.ubicacion.ruta)


# ---- el lector propio de JSON con comentarios -----------------------------------------------------------------------


def test_el_lector_acepta_comentarios_y_comas_finales():
    texto = '{\n  // línea\n  "a": 1, /* bloque */\n  "b": [1, 2,],\n  "c": {"d": 3,},\n}\n'
    assert parsear_jsonc(texto) == {"a": 1, "b": [1, 2], "c": {"d": 3}}


def test_las_barras_dentro_de_cadenas_no_son_comentarios():
    texto = '{"url": "https://ejemplo.invalid/a//b", "c": "/* no */", "d": "coma,}"}'
    assert parsear_jsonc(texto) == {"url": "https://ejemplo.invalid/a//b", "c": "/* no */", "d": "coma,}"}


def test_limpiar_conserva_los_saltos_de_linea_para_que_las_lineas_no_se_corran():
    texto = '{\n// uno\n"a": 1, /* dos\ntres */ "b": 2,\n}'
    assert limpiar_jsonc(texto).count("\n") == texto.count("\n")


@pytest.mark.parametrize("texto", ['{"a": 1 /* sin cerrar', "{'a': 1}", '{"a": }', "{a: 1}", "", "no es json", '{"a": 1} {'])
def test_lo_que_no_se_puede_interpretar_da_error_propio_y_no_otra_excepcion(texto):
    with pytest.raises(JsoncNoInterpretable):
        parsear_jsonc(texto)


def test_el_error_no_copia_texto_del_archivo():
    with pytest.raises(JsoncNoInterpretable) as info:
        parsear_jsonc('{"clave": "' + CANARIO + '" /* roto')
    assert CANARIO not in str(info.value) and CANARIO not in repr(info.value)


def test_la_profundidad_maxima_es_64_y_cuenta_sin_mirar_cadenas_ni_comentarios():
    assert parsear_jsonc('{"a":' * 64 + "1" + "}" * 64)
    with pytest.raises(ProfundidadExcedida):
        parsear_jsonc('{"a":' * 65 + "1" + "}" * 65)
    assert parsear_jsonc('{"a": "[[[[[[[[", /* {{{{{{ */ "b": 1}') == {"a": "[[[[[[[[", "b": 1}


# ---- AT-04: hooks -------------------------------------------------------------------------------------------------------


HOOKS = {"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": f"python senuelo.py {CANARIO}"}]}]}}


def test_at04_hooks_en_settings_json_dan_th14_con_su_linea_y_el_rotulo(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".claude" / "settings.json", HOOKS)
    hallazgos, detector = _auditar(p)
    assert isinstance(detector, Detector) and _tipos(hallazgos) == [TH14]
    (h,) = hallazgos
    assert _nombre(h) == "settings.json" and h.ubicacion.linea == 2  # la línea de "hooks"
    assert _rotulo(detector, h) == "hooks"
    assert all(h.nivel is Nivel.HIPOTESIS for h in hallazgos)


def test_hooks_vacios_no_se_reportan(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".claude" / "settings.json", {"hooks": {}, "permissions": {"allow": ["Read(./src/**)"]}})
    assert _auditar(p)[0] == []


# ---- AT-05: servidores MCP de comando en .mcp.json -------------------------------------------------------------------------


def test_at05_un_servidor_mcp_de_comando_da_th14(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".mcp.json", {"mcpServers": {"local": {"command": "python", "args": [CANARIO]},
                                               "remoto": {"type": "http", "url": "https://ejemplo.invalid/mcp"},
                                               "sse": {"type": "sse", "url": "https://ejemplo.invalid/sse"}}})
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH14] and _nombre(hallazgos[0]) == ".mcp.json"
    assert hallazgos[0].ubicacion.linea == 4  # la línea de "command" del servidor local
    assert _rotulo(detector, hallazgos[0]) == "mcp"


def test_dos_servidores_de_comando_dan_dos_hallazgos_con_su_linea(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".mcp.json", {"mcpServers": {"a": {"command": "x"}, "b": {"type": "stdio", "command": "y"}}})
    hallazgos, _ = _auditar(p)
    assert len(hallazgos) == 2 and len({h.ubicacion.linea for h in hallazgos}) == 2


def test_mcp_json_con_comentarios_y_comas_finales_se_lee(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".mcp.json", '{\n  // servidores\n  "mcpServers": {\n    "a": {"command": "x",}, /* fin */\n  },\n}\n')
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH14] and hallazgos[0].ubicacion.linea == 4 and _avisos(detector) == []


# ---- AT-12 y enabledMcpjsonServers --------------------------------------------------------------------------------------------


def test_at12_enable_all_project_mcp_servers_true_da_th14_y_false_no(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".claude" / "settings.json", {"enableAllProjectMcpServers": True})
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH14] and _rotulo(detector, hallazgos[0]) == "mcp"
    _escribir(p / ".claude" / "settings.json", {"enableAllProjectMcpServers": False})
    assert _auditar(p)[0] == []


def test_enabled_mcpjson_servers_con_nombres_da_th14(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".claude" / "settings.json", {"enabledMcpjsonServers": ["local"]})
    assert _tipos(_auditar(p)[0]) == [TH14]
    _escribir(p / ".claude" / "settings.json", {"enabledMcpjsonServers": []})
    assert _auditar(p)[0] == []


# ---- AT-06: saltar permisos ------------------------------------------------------------------------------------------------------


def test_at06_bypass_permissions_en_settings_local_da_th15(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".claude" / "settings.local.json", {"permissions": {"defaultMode": "bypassPermissions"}})
    hallazgos, _ = _auditar(p)
    assert _tipos(hallazgos) == [TH15] and _nombre(hallazgos[0]) == "settings.local.json"
    assert hallazgos[0].ubicacion.linea == 3
    _escribir(p / ".claude" / "settings.local.json", {"permissions": {"defaultMode": "acceptEdits"}})
    assert _auditar(p)[0] == []


def test_la_bandera_dangerously_skip_permissions_se_encuentra_sin_copiar_el_texto(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".vscode" / "tasks.json", '{"version": "2.0.0", "tasks": [\n{"label": "x", '
                                            f'"command": "claude --dangerously-skip-permissions -p {CANARIO}"}}]}}\n')
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH15] and hallazgos[0].ubicacion.linea == 2
    assert CANARIO not in _salida(hallazgos, detector) and "--dangerously" not in _salida(hallazgos, detector)


# ---- AT-07: tareas al abrir la carpeta --------------------------------------------------------------------------------------------


TAREAS = {"version": "2.0.0", "tasks": [
    {"label": "preparar", "type": "shell", "command": f"python senuelo.py {CANARIO}",
     "runOptions": {"runOn": "folderOpen"}, "presentation": {"reveal": "never"}},
    {"label": "manual", "type": "shell", "command": "echo hola"},
]}


def test_at07_una_tarea_con_run_on_folder_open_da_th16(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".vscode" / "tasks.json", TAREAS)
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH16] and hallazgos[0].ubicacion.linea == 9
    assert CANARIO not in _salida(hallazgos, detector)


def test_una_tarea_sin_run_on_folder_open_no_se_reporta(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".vscode" / "tasks.json", {"version": "2.0.0", "tasks": [{"label": "a", "runOptions": {"runOn": "default"}}]})
    assert _auditar(p)[0] == []


def test_tasks_json_con_comentarios_al_estilo_de_vs_code(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".vscode" / "tasks.json", '{\n  // tareas\n  "tasks": [\n    {"label": "a", "runOptions": {"runOn": "folderOpen"},},\n  ],\n}\n')
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH16] and hallazgos[0].ubicacion.linea == 4 and _avisos(detector) == []


# ---- (d) ajustes de VS Code ---------------------------------------------------------------------------------------------------------


def test_chat_tools_auto_approve_true_da_th15_con_un_archivo_de_ejemplo(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".vscode" / "settings.json", {"chat.tools.autoApprove": True})
    hallazgos, _ = _auditar(p)
    assert _tipos(hallazgos) == [TH15] and hallazgos[0].ubicacion.linea == 2
    _escribir(p / ".vscode" / "settings.json", {"chat.tools.autoApprove": False})
    assert _auditar(p)[0] == []


def test_allow_automatic_tasks_on_es_un_freno_desactivado_th16_y_th15(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".vscode" / "settings.json", {"task.allowAutomaticTasks": "on"})
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH15, TH16]
    assert {_rotulo(detector, h) for h in hallazgos} == {"freno_desactivado"}
    for valor in ("off", "auto"):
        _escribir(p / ".vscode" / "settings.json", {"task.allowAutomaticTasks": valor})
        assert _auditar(p)[0] == []


# ---- controles: CA-01 y CA-04 no dan estos hallazgos ---------------------------------------------------------------------------------


def test_reglas_de_permisos_y_opencode_no_son_configuracion_que_se_ejecuta_sola(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".claude" / "settings.json", {"permissions": {"allow": ["Bash(git status)"], "deny": ["Read(./.env)"]},
                                                "env": {"CLAUDE_CODE_SUBPROCESS_ENV_SCRUB": "1"}})
    _escribir(p / "opencode.json", {"permission": {"read": "allow", "bash": "allow"}})
    hallazgos, detector = _auditar(p)
    assert hallazgos == [] and detector.rotulos == {}


def test_sin_ninguno_de_los_archivos_no_hay_nada_que_decir(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    hallazgos, detector = _auditar(p)
    assert hallazgos == []
    assert {n.motivo for n in detector.no_revisados} <= {MotivoNoRevisado.UBICACION_SENSIBLE_SIN_ACTIVAR}


# ---- (a) el valor no sale, (b) nada se ejecuta -----------------------------------------------------------------------------------------


def _prohibir_programas(monkeypatch) -> None:
    def prohibido(*a, **k):
        raise AssertionError("se intentó ejecutar un programa")

    monkeypatch.setattr(subprocess, "Popen", prohibido)
    monkeypatch.setattr(subprocess, "run", prohibido)
    monkeypatch.setattr(os, "system", prohibido)
    monkeypatch.setattr(os, "popen", prohibido)
    monkeypatch.setattr(os, "startfile", prohibido, raising=False)
    for familia in ("execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp", "execvpe",
                    "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe"):
        monkeypatch.setattr(os, familia, prohibido, raising=False)


def test_el_valor_canario_del_comando_no_sale_y_no_se_ejecuta_nada(tmp_path: Path, monkeypatch):
    p = tmp_path / "proyecto"
    _escribir(p / ".claude" / "settings.json", {**HOOKS, "enableAllProjectMcpServers": True})
    _escribir(p / ".mcp.json", {"mcpServers": {"a": {"command": "python", "args": [CANARIO]}}})
    _escribir(p / ".vscode" / "tasks.json", TAREAS)
    _escribir(p / ".vscode" / "settings.json", {"chat.tools.autoApprove": True, "task.allowAutomaticTasks": "on"})
    _escribir(p / ".claude" / "settings.local.json", {"permissions": {"defaultMode": "bypassPermissions"}})
    _prohibir_programas(monkeypatch)
    hallazgos, detector = _auditar(p)
    assert len(hallazgos) == 8
    salida = _salida(hallazgos, detector)
    assert CANARIO not in salida and "senuelo" not in salida and "python" not in salida


# ---- (c) y (c2): archivos que no se pueden leer ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("contenido,motivo", [
    (b'{"tasks": [ /* sin cerrar', MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE),
    (b"{ esto no es json", MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE),
    (b"\xff\xfe\xfd", MotivoNoRevisado.CODIFICACION_NO_UTF8),
    (('{"a":' * 65 + "1" + "}" * 65).encode(), MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA),
])
@pytest.mark.parametrize("archivo", [".vscode/tasks.json", ".vscode/settings.json", ".mcp.json"])
def test_un_archivo_que_no_se_puede_interpretar_da_no_revisado_y_no_excepcion(tmp_path: Path, archivo, contenido, motivo):
    p = tmp_path / "proyecto"
    _escribir(p / archivo, contenido)
    hallazgos, detector = _auditar(p)
    assert hallazgos == []
    motivos = [n.motivo for n in detector.no_revisados if n.motivo is not MotivoNoRevisado.UBICACION_SENSIBLE_SIN_ACTIVAR]
    assert motivos == [motivo]


def test_un_archivo_gigante_y_una_tuberia_simulada_dan_no_revisado(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    with (p / ".mcp.json").open("wb") as f:
        f.truncate(5 * 1024 * 1024 + 1)
    _escribir(p / ".vscode" / "tasks.json", "{}")

    class FsConTuberia(FsSoloLectura):
        def leer_texto(self, ruta):
            if ruta.replace("\\", "/").endswith("tasks.json"):
                from agentreach.contracts import ArchivoNoLegible

                raise ArchivoNoLegible("tuberia", MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR)
            return super().leer_texto(ruta)

    hallazgos, detector = _auditar(p, FsConTuberia())
    motivos = sorted(n.motivo.value for n in detector.no_revisados
                     if n.motivo is not MotivoNoRevisado.UBICACION_SENSIBLE_SIN_ACTIVAR)
    assert hallazgos == [] and motivos == ["archivo_demasiado_grande", "no_es_archivo_regular"]


def test_una_forma_inesperada_no_rompe(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".mcp.json", {"mcpServers": ["no", "es", "un", "objeto"]})
    _escribir(p / ".vscode" / "tasks.json", {"tasks": {"no": "es una lista"}})
    _escribir(p / ".vscode" / "settings.json", [1, 2, 3])
    hallazgos, detector = _auditar(p)
    assert hallazgos == [] and len([n for n in detector.no_revisados
                                    if n.motivo is MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE]) >= 1


def test_el_resultado_anterior_no_se_arrastra(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".vscode" / "tasks.json", TAREAS)
    detector = _detector(tmp_path)
    assert len(list(detector.detectar(Ruta(str(p))))) == 1 and detector.rotulos
    _escribir(p / ".vscode" / "tasks.json", {"tasks": []})
    assert list(detector.detectar(Ruta(str(p)))) == [] and detector.rotulos == {}


# ---- registro y proyecto de prueba ----------------------------------------------------------------------------------------------------------


def test_el_detector_esta_registrado_en_auditar():
    from agentreach.app import auditar as modulo

    nombres = {type(crear(FsSoloLectura(), Configuracion())).__name__ for crear in modulo._detectores}
    assert "DetectorConfigEjecutaSola" in nombres


@pytest.fixture
def proyecto_prueba() -> Path:
    raiz = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")
    if not raiz or not (Path(raiz) / "proyecto").is_dir():
        pytest.skip("AGENTREACH_PROYECTO_PRUEBA no apunta al proyecto de prueba")
    return Path(raiz) / "proyecto"


def test_at04_at05_at06_at07_at12_con_el_proyecto_de_prueba(proyecto_prueba: Path, monkeypatch):
    _prohibir_programas(monkeypatch)
    hallazgos, detector = _auditar(proyecto_prueba)
    por_archivo = sorted((_nombre(h), h.tipo.value) for h in hallazgos)
    assert por_archivo == [
        (".mcp.json", "TH-14"),  # AT-05
        ("settings.json", "TH-14"),  # AT-04 (hooks)
        ("settings.json", "TH-14"),  # AT-12 (enableAllProjectMcpServers: true)
        ("settings.local.json", "TH-15"),  # AT-06
        ("tasks.json", "TH-16"),  # AT-07
    ]
    assert not [h for h in hallazgos if _nombre(h) == "opencode.json"]  # CA-04 no
    salida = _salida(hallazgos, detector)
    assert "senuelo" not in salida and "trampas" not in salida  # el comando nunca sale
    assert not (proyecto_prueba.parent / "trampas" / "PWNED.txt").exists()
    assert {r for v in detector.rotulos.values() for r in v} >= {"hooks", "mcp"}


# ---- parches de la revisión -------------------------------------------------------------------------------------------------------------


def test_un_bom_y_un_retorno_de_carro_suelto_no_impiden_leer_el_archivo(tmp_path: Path):
    assert parsear_jsonc(chr(0xFEFF) + '{"a": 1}') == {"a": 1}
    assert parsear_jsonc('{"a": 1, // comentario\r"b": 2}') == {"a": 1, "b": 2}  # solo CR: el comentario termina
    p = tmp_path / "proyecto"
    _escribir(p / ".vscode" / "tasks.json", chr(0xFEFF) + '{"tasks": [{"runOptions": {"runOn": "folderOpen"}}]}')
    assert _tipos(_auditar(p)[0]) == [TH16]


def test_dos_casos_en_la_misma_linea_no_se_pisan_los_rotulos(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".claude" / "settings.json", '{"hooks": {"a": [1]}, "enableAllProjectMcpServers": true}')
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH14, TH14]
    (rotulos,) = set(detector.rotulos.values())
    assert rotulos == ("hooks", "mcp")


def test_la_bandera_se_encuentra_aunque_el_archivo_no_se_pueda_interpretar(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".vscode" / "tasks.json", '{ roto\nclaude --dangerously-skip-permissions\n')
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH15] and hallazgos[0].ubicacion.linea == 2
    assert MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE in {n.motivo for n in detector.no_revisados}


def test_una_mencion_de_la_bandera_en_un_comentario_no_cuenta(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".vscode" / "tasks.json", '{\n// nunca usar --dangerously-skip-permissions\n"tasks": []\n}')
    assert _auditar(p)[0] == []


@pytest.mark.parametrize("texto", ["claude --allow-dangerously-skip-permissions", "claude --permission-mode bypassPermissions",
                                   "claude --permission-mode=bypassPermissions"])
def test_variantes_de_la_bandera_que_salta_los_permisos(tmp_path: Path, texto):
    p = tmp_path / "proyecto"
    _escribir(p / ".vscode" / "tasks.json", {"tasks": [{"command": texto}]})
    assert _tipos(_auditar(p)[0]) == [TH15]


def test_auto_aprobar_en_forma_de_objeto(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".vscode" / "settings.json", {"chat.tools.autoApprove": {"terminal": True, "otra": False}})
    assert _tipos(_auditar(p)[0]) == [TH15]
    _escribir(p / ".vscode" / "settings.json", {"chat.tools.autoApprove": {"terminal": False}})
    assert _auditar(p)[0] == []


def test_una_entrada_de_tarea_mal_formada_se_informa(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".vscode" / "tasks.json", {"tasks": ["no soy un objeto", {"runOptions": "tampoco"},
                                                       {"runOptions": {"runOn": "folderOpen"}}]})
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH16]  # la buena se reporta igual
    assert MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE in {n.motivo for n in detector.no_revisados}


def test_el_mcp_de_vs_code_usa_la_clave_servers(tmp_path: Path):
    p = tmp_path / "proyecto"
    _escribir(p / ".vscode" / "mcp.json", {"servers": {"a": {"command": "x"}, "b": {"type": "http", "url": "https://x.invalid"}}})
    hallazgos, detector = _auditar(p)
    assert _tipos(hallazgos) == [TH14] and _nombre(hallazgos[0]) == "mcp.json" and _rotulo(detector, hallazgos[0]) == "mcp"


@pytest.mark.parametrize("lista,esperado", [(["local"], [TH14]), ([], []), ([""], []), (["  ", 3], []), ([None], [])])
def test_enabled_mcpjson_servers_solo_cuenta_con_nombres_de_verdad(tmp_path: Path, lista, esperado):
    p = tmp_path / "proyecto"
    _escribir(p / ".claude" / "settings.json", {"enabledMcpjsonServers": lista})
    assert _tipos(_auditar(p)[0]) == esperado
