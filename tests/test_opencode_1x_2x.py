"""Historia 10b: el adaptador de opencode entiende los dos esquemas (1.x, la 1.19.0 de Alex, y 2.x).

Casos OC-02 a OC-08 de ``research/opencode-1x-frente-a-2x.md``. El esquema se decide por la FORMA de los archivos: no prueba la
versión instalada (la 2.x acepta archivos 1.x), y lo que depende de la versión toma el peor caso cuando no se sabe.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentreach.adapters.opencode import AdaptadorOpencode
from agentreach.app.auditar import auditar
from agentreach.cli import main
from agentreach.config import Configuracion
from agentreach.contracts import (
    Motivo,
    Nivel,
    PermisoLectura,
    PermisosArchivo,
    Plataforma,
    Postura,
    Ruta,
    Tipo,
)
from agentreach.infra.fs_solo_lectura import FsSoloLectura

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

LEGIBLE = PermisosArchivo(PermisoLectura.SI, False, False, "usuario", "icacls x")
COMPROBADO = {(Nivel.COMPROBADO, Motivo.EXISTE_LEGIBLE_SIN_REGLA)}
DENY = {(Nivel.POTENCIAL, Motivo.REGLA_DENY)}
ASK = {(Nivel.POTENCIAL, Motivo.REGLA_ASK)}
NO_DETERMINADO = {(Nivel.POTENCIAL, Motivo.NO_DETERMINADO)}


class Sonda:
    def evaluar(self, ruta):
        return LEGIBLE


def _proyecto(tmp_path: Path, opencode: str | dict | None = None, nombre: str = "opencode.json") -> Path:
    p = tmp_path / "proyecto"
    p.mkdir(parents=True, exist_ok=True)
    (p / ".env").write_text("STRIPE_SECRET_KEY=sk_live_valor_largo_123\n", encoding="utf-8")
    if opencode is not None:
        (p / nombre).parent.mkdir(parents=True, exist_ok=True)
        (p / nombre).write_text(opencode if isinstance(opencode, str) else json.dumps(opencode), encoding="utf-8")
    return p


def _auditar(p: Path):
    casa = p.parent / "casa"
    casa.mkdir(exist_ok=True)
    return auditar(str(p), Configuracion(home=str(casa)), medidores=(Sonda(), None))


def _env(res):
    return {(h.nivel, h.motivo) for h in res.hallazgos if h.tipo is Tipo.CREDENCIAL_EN_ARCHIVO and h.agente == "opencode"}


def _adaptador(p: Path) -> AdaptadorOpencode:
    a = AdaptadorOpencode(FsSoloLectura(str(p)), Configuracion(home=str(p.parent / "casa")))
    a.cargar(Ruta(str(p)))
    return a


def _tipos(res, tipo: Tipo, plataforma=None):
    return [h for h in res.hallazgos if h.tipo is tipo and (plataforma is None or h.plataforma is plataforma)]


# ---- permisos: la forma 1.x (objeto) y la 2.x (lista) -------------------------------------------------------------------------------


def test_oc02_esquema_1x_permission_objeto_con_bash(tmp_path: Path):
    p = _proyecto(tmp_path, {"permission": {"read": {"*.env": "allow"}, "bash": "allow"}})
    res = _auditar(p)
    assert _env(res) == COMPROBADO  # el read: allow anula el ask base (PP-04)
    assert _tipos(res, Tipo.CAPACIDAD_DE_SHELL)  # CA-04: bash allow
    assert _adaptador(p).cargar(Ruta(str(p))).esquema == "1.x"


def test_oc03_esquema_2x_permissions_lista_con_shell(tmp_path: Path):
    p = _proyecto(tmp_path, {"permissions": [
        {"action": "read", "resource": "*.env", "effect": "allow"},
        {"action": "shell", "resource": "*", "effect": "allow"}]})
    res = _auditar(p)
    assert _env(res) == COMPROBADO
    assert _tipos(res, Tipo.CAPACIDAD_DE_SHELL)  # el mismo hallazgo que en 1.x: si solo se conociera `bash`, sería una omisión
    assert _adaptador(p).cargar(Ruta(str(p))).esquema == "2.x"


def test_en_la_lista_2x_gana_la_ultima_regla_que_coincide(tmp_path: Path):
    p = _proyecto(tmp_path, {"permissions": [
        {"action": "read", "resource": "*.env", "effect": "allow"},
        {"action": "read", "resource": "*.env", "effect": "deny"}]})
    assert _env(_auditar(p)) == DENY
    p2 = _proyecto(tmp_path / "otro", {"permissions": [
        {"action": "read", "resource": "*.env", "effect": "deny"},
        {"action": "read", "resource": "*.env", "effect": "allow"}]})
    assert _env(_auditar(p2)) == COMPROBADO


@pytest.mark.parametrize("entrada", [{"action": "read", "resource": "*.env"}, {"action": "read", "effect": "quizas"}, "texto", {"effect": "deny"}])
def test_una_entrada_2x_que_no_se_reconoce_deja_el_nivel_no_determinado(tmp_path: Path, entrada):
    p = _proyecto(tmp_path, {"permissions": [entrada]})
    assert _env(_auditar(p)) == NO_DETERMINADO


def test_permissions_que_no_es_una_lista_no_se_reconoce(tmp_path: Path):
    assert _env(_auditar(_proyecto(tmp_path, {"permissions": {"read": "deny"}}))) == NO_DETERMINADO


def test_las_dos_formas_a_la_vez_se_combinan_la_1x_primero(tmp_path: Path):
    p = _proyecto(tmp_path, {"permission": {"read": {"*.env": "allow"}},
                             "permissions": [{"action": "read", "resource": "*.env", "effect": "deny"}]})
    assert _env(_auditar(p)) == DENY  # la lista 2.x se evalúa después


@pytest.mark.parametrize("viejo, tipo", [("write", Tipo.REGLA_PERMISIVA), ("patch", Tipo.REGLA_PERMISIVA), ("bash", Tipo.CAPACIDAD_DE_SHELL)])
def test_los_nombres_de_1x_se_reconocen_como_los_de_2x(tmp_path: Path, viejo: str, tipo: Tipo):
    p = _proyecto(tmp_path, {"permission": {viejo: "allow"}})
    assert _tipos(_auditar(p), tipo)


# ---- external_directory: 1.x pregunta, 2.x permite, sin saber la versión el peor caso -------------------------------------------------


def _fuera(tmp_path: Path) -> Ruta:
    fuera = tmp_path / "fuera" / "secreto.txt"
    fuera.parent.mkdir(parents=True)
    fuera.write_text("x", encoding="utf-8")
    return Ruta(str(fuera))


def test_oc04_external_directory_por_defecto_segun_el_esquema(tmp_path: Path):
    destino = _fuera(tmp_path)
    p1 = _proyecto(tmp_path / "a", {"permission": {"read": "allow"}})
    assert _adaptador(p1).postura_para(destino) is Postura.ASK  # 1.x: ask
    p2 = _proyecto(tmp_path / "b", {"permissions": [{"action": "read", "resource": "*", "effect": "allow"}]})
    assert _adaptador(p2).postura_para(destino) is Postura.ALLOW  # 2.x: allow
    p3 = _proyecto(tmp_path / "c", {})  # una configuración sin ninguna clave que decida
    a3 = _adaptador(p3)
    assert a3.cargar(Ruta(str(p3))).esquema == "ambiguo" and a3.postura_para(destino) is Postura.ALLOW  # el peor caso


def test_una_regla_escrita_de_external_directory_manda_en_las_dos_versiones(tmp_path: Path):
    destino = _fuera(tmp_path)
    p = _proyecto(tmp_path, {"permission": {"external_directory": "ask"}})
    assert _adaptador(p).postura_para(destino) is Postura.ASK
    p2 = _proyecto(tmp_path / "d", {"permissions": [{"action": "external_directory", "resource": "*", "effect": "deny"}]})
    assert _adaptador(p2).postura_para(destino) is Postura.DENY


def test_el_esquema_mezclado_es_ambiguo(tmp_path: Path):
    p = _proyecto(tmp_path, {"permission": {"read": "allow"}, "permissions": [{"action": "read", "resource": "*", "effect": "allow"}]})
    assert _adaptador(p).cargar(Ruta(str(p))).esquema == "ambiguo"


def test_sin_ningun_archivo_de_opencode_no_hay_esquema_que_decir(tmp_path: Path):
    p = _proyecto(tmp_path)
    assert _adaptador(p).cargar(Ruta(str(p))).esquema == ""


# ---- .opencode/ ----------------------------------------------------------------------------------------------------------------------


def test_oc05_opencode_jsonc_con_comentarios_y_comas_finales_se_lee(tmp_path: Path):
    p = _proyecto(tmp_path, '// política del proyecto\n{\n  "permission": {\n    "read": { "*.env": "deny", }, // no se leen\n  },\n}\n',
                  ".opencode/opencode.jsonc")
    assert _env(_auditar(p)) == DENY


def test_la_carpeta_opencode_manda_sobre_el_archivo_de_la_raiz(tmp_path: Path):
    p = _proyecto(tmp_path, {"permission": {"read": {"*.env": "allow"}}})
    (p / ".opencode").mkdir()
    (p / ".opencode" / "opencode.json").write_text(json.dumps({"permission": {"read": {"*.env": "deny"}}}), encoding="utf-8")
    assert _env(_auditar(p)) == DENY


def test_un_agente_con_permisos_propios_en_su_encabezado_no_se_modela(tmp_path: Path):
    p = _proyecto(tmp_path, {"permission": {"read": {"*.env": "allow"}}})
    agente = p / ".opencode" / "agent" / "revisor.md"
    agente.parent.mkdir(parents=True)
    agente.write_text("---" + chr(10) + "description: revisa" + chr(10) + "tools:" + chr(10) + "  read: false" + chr(10) + "---" + chr(10) + "Texto" + chr(10),
                      encoding="utf-8")
    assert _env(_auditar(p)) == NO_DETERMINADO
    agente.write_text("---" + chr(10) + "description: revisa" + chr(10) + "---" + chr(10) + "Texto" + chr(10), encoding="utf-8")
    assert _env(_auditar(p)) == COMPROBADO  # sin permisos ni herramientas propios no hay nada que no se modele


# ---- MCP -----------------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("datos, lanza", [
    ({"mcp": {"x": {"type": "local", "command": ["npx", "-y", "paquete"]}}}, True),  # 1.x
    ({"mcp": {"servers": {"x": {"type": "local", "command": ["npx", "-y", "paquete"]}}}}, True),  # 2.x
    ({"mcp": {"x": {"type": "local", "command": ["npx"], "enabled": False}}}, False),  # 1.x apagado
    ({"mcp": {"servers": {"x": {"type": "local", "command": ["npx"], "disabled": True}}}}, False),  # 2.x apagado
    ({"mcp": {"x": {"type": "remote", "url": "https://ejemplo.invalid/mcp"}}}, False),  # remoto: no arranca un programa
    ({"mcp": {"servers": {"x": {"type": "remote", "url": "https://ejemplo.invalid/mcp"}}}}, False),
])
def test_oc06_un_servidor_mcp_local_es_un_programa_que_arranca_solo(tmp_path: Path, datos, lanza):
    res = _auditar(_proyecto(tmp_path, datos))
    mcp = _tipos(res, Tipo.HOOK_O_MCP_DE_COMANDO, plataforma=Plataforma.OPENCODE)
    assert bool(mcp) is lanza
    assert all(h.nivel is Nivel.POTENCIAL for h in mcp)  # no se ve la versión ni si la persona aceptó el servidor


# ---- la regla de la 11b sigue valiendo ----------------------------------------------------------------------------------------------


def test_oc08_una_configuracion_ambigua_se_dice_y_no_miente(tmp_path: Path, capsys):
    p = _proyecto(tmp_path, {"model": "proveedor/modelo"})
    assert main([str(p), "--ancho", "100"]) in (0, 1)
    salida = " ".join(capsys.readouterr().out.split())
    assert "No se pudo determinar la versión de opencode; se asume el peor caso (2.x)" in salida


def test_el_reporte_dice_el_esquema_detectado(tmp_path: Path, capsys):
    p = _proyecto(tmp_path, {"permission": {"read": {"*.env": "allow"}}})
    main([str(p), "--ancho", "100", "--idioma", "en"])
    assert "Configuration (version 1.x) detected" in " ".join(capsys.readouterr().out.split())
    p2 = _proyecto(tmp_path / "dos", {"permissions": [{"action": "read", "resource": "*.env", "effect": "allow"}]})
    main([str(p2), "--ancho", "100"])
    assert "Configuración (versión 2.x) detectada" in " ".join(capsys.readouterr().out.split())


# ---- correcciones de la revisión de la 10b ---------------------------------------------------------------------------------


def _postura(p: Path, ruta: Path) -> Postura:
    return _adaptador(p).postura_para(Ruta(str(ruta)))


def _resultado(p: Path):
    a = AdaptadorOpencode(FsSoloLectura(str(p)), Configuracion(home=str(p.parent / "casa")))
    return a.cargar(Ruta(str(p)))


def test_fuera_del_proyecto_tambien_rige_read(tmp_path: Path):
    p = _proyecto(tmp_path, {"permissions": [{"action": "read", "resource": "*.env", "effect": "deny"}]})
    ajeno = tmp_path / "otro" / ".env"
    ajeno.parent.mkdir()
    ajeno.write_text("A=1\n", encoding="utf-8")
    assert _postura(p, ajeno) in (Postura.DENY, Postura.ASK)  # nunca ALLOW («comprobado»)


def test_agents_plugins_y_policies_de_2x_no_se_modelan(tmp_path: Path):
    for extra in ({"agents": {"r": {"permissions": []}}}, {"plugins": ["x"]}, {"plugin": ["x"]}, {"experimental": {"policies": []}}):
        p = _proyecto(tmp_path / str(len(str(extra))), {"permissions": [{"action": "read", "resource": "*", "effect": "allow"}], **extra})
        r = _resultado(p)
        assert any(n.motivo.value == "funcion_no_modelada" for n in r.no_revisados), extra


def test_un_agente_md_en_subcarpeta_y_con_comillas_se_marca(tmp_path: Path):
    p = _proyecto(tmp_path, {"permission": {"read": "allow"}})
    d = p / ".opencode" / "agents" / "team"
    d.mkdir(parents=True)
    (d / "a.md").write_text('---\ndescription: a --- b\n"permission":\n  read: deny\n---\ncuerpo\n', encoding="utf-8")
    assert any(n.motivo.value == "funcion_no_modelada" for n in _resultado(p).no_revisados)


def test_permission_vacio_es_esquema_ambiguo_y_mcp_con_comando_en_cadena_se_reporta(tmp_path: Path):
    assert _resultado(_proyecto(tmp_path, {"permission": {}})).esquema == "ambiguo"
    p = _proyecto(tmp_path / "m", {"mcp": {"a": {"command": "npx", "args": ["x"]}}})
    assert len(_resultado(p).config_proyecto) == 1


def test_opencode_json_de_una_carpeta_padre_hasta_la_raiz_del_repo_se_lee(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / "opencode.json").write_text(json.dumps({"permission": {"read": {"*.env": "deny"}}}), encoding="utf-8")
    sub = repo / "sub"
    sub.mkdir()
    (sub / ".env").write_text("A=1\n", encoding="utf-8")
    assert _adaptador(sub).postura_para(Ruta(str(sub / ".env"))) is Postura.DENY


def test_sin_raiz_de_repo_no_se_mira_fuera_del_proyecto_y_el_del_proyecto_gana(tmp_path: Path):
    ajeno = tmp_path / "otro"
    ajeno.mkdir()
    (ajeno / "opencode.json").write_text(json.dumps({"permission": {"read": {"*.env": "deny"}}}), encoding="utf-8")
    p = ajeno / "p"
    p.mkdir()
    (p / ".env").write_text("A=1\n", encoding="utf-8")
    assert _adaptador(p).postura_para(Ruta(str(p / ".env"))) is not Postura.DENY  # sin .git arriba: no hay raíz de repo
    repo = tmp_path / "r2"
    (repo / ".git").mkdir(parents=True)
    (repo / "opencode.json").write_text(json.dumps({"permission": {"read": {"*.env": "deny"}}}), encoding="utf-8")
    q = repo / "q"
    q.mkdir()
    (q / "opencode.json").write_text(json.dumps({"permission": {"read": {"*.env": "allow"}}}), encoding="utf-8")
    (q / ".env").write_text("A=1\n", encoding="utf-8")
    assert _adaptador(q).postura_para(Ruta(str(q / ".env"))) is Postura.ALLOW


def test_el_respaldo_de_appdata_en_windows_se_lee(tmp_path: Path, monkeypatch):
    appdata = tmp_path / "AppData"
    (appdata / "opencode").mkdir(parents=True)
    (appdata / "opencode" / "opencode.json").write_text(json.dumps({"permission": {"read": {"*.env": "deny"}}}), encoding="utf-8")
    monkeypatch.setenv("APPDATA", str(appdata))
    p = _proyecto(tmp_path / "x", {"permission": {}})
    (p / ".env").write_text("A=1\n", encoding="utf-8")
    a = AdaptadorOpencode(FsSoloLectura(str(p)), Configuracion(home=str(p.parent / "casa")), sistema="win32")
    a.cargar(Ruta(str(p)))
    assert a.postura_para(Ruta(str(p / ".env"))) is Postura.DENY
