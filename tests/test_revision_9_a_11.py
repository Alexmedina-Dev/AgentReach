"""Revisión independiente de las historias 9 a 11 (2026-11-10): lo que cada parche debe seguir cumpliendo."""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from agentreach.adapters.claude_code import AdaptadorClaudeCode
from agentreach.adapters.claude_code.reglas import coincide
from agentreach.adapters.opencode import AdaptadorOpencode, _es_amplia
from agentreach.app.auditar import auditar
from agentreach.config import Configuracion
from agentreach.contracts import (
    MotivoNoRevisado,
    Nivel,
    PermisoLectura,
    PermisosArchivo,
    Postura,
    Ruta,
    Tipo,
)
from agentreach.infra.fs_solo_lectura import FsSoloLectura

LEGIBLE = PermisosArchivo(PermisoLectura.SI, False, False, "usuario", "icacls x")


class Sonda:
    def evaluar(self, ruta):
        return LEGIBLE


def _json(ruta: Path, datos) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(datos if isinstance(datos, str) else json.dumps(datos), encoding="utf-8")
    return ruta


def _proyecto(tmp_path: Path) -> Path:
    p = tmp_path / "proyecto"
    p.mkdir()
    (p / ".env").write_text("STRIPE_SECRET_KEY=sk_live_valor_largo_123\n", encoding="utf-8")
    return p


def _opencode(p: Path, casa: Path) -> AdaptadorOpencode:
    casa.mkdir(exist_ok=True)
    a = AdaptadorOpencode(FsSoloLectura(str(p)), Configuracion(home=str(casa)))
    a.cargar(Ruta(str(p)))
    return a


def _claude(p: Path, casa: str, gestionada: Path | None = None) -> AdaptadorClaudeCode:
    ruta = str(gestionada or p.parent / "gest" / "managed-settings.json")
    a = AdaptadorClaudeCode(FsSoloLectura(str(p)), Configuracion(home=casa), ruta_gestionada=ruta)
    a.cargar(Ruta(str(p)))
    return a


# ---- opencode: dónde vive la configuración del usuario -------------------------------------------------------------------------
def test_xdg_config_home_absoluta_es_la_carpeta_global_de_opencode(tmp_path: Path, monkeypatch):
    p, xdg = _proyecto(tmp_path), tmp_path / "xdg"
    _json(xdg / "opencode" / "opencode.json", {"permission": {"read": {"*.env": "deny"}}})
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    a = _opencode(p, tmp_path / "casa")
    assert a.postura_para(Ruta(str(p / ".env"))) is Postura.DENY
    assert a.regla_para(Ruta(str(p / ".env"))).ruta.replace("\\", "/").startswith(str(xdg).replace("\\", "/"))


def test_xdg_config_home_relativa_se_ignora(tmp_path: Path, monkeypatch):
    p = _proyecto(tmp_path)
    _json(tmp_path / "rel" / "opencode" / "opencode.json", {"permission": {"read": {"*.env": "deny"}}})
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", "rel")
    assert _opencode(p, tmp_path / "casa").postura_para(Ruta(str(p / ".env"))) is Postura.ASK  # solo la base de opencode


def test_opencode_config_apunta_a_otro_archivo_de_reglas(tmp_path: Path, monkeypatch):
    p = _proyecto(tmp_path)
    otro = _json(tmp_path / "mis-reglas.json", {"permission": {"read": {"*.env": "deny"}}})
    monkeypatch.setenv("OPENCODE_CONFIG", str(otro))
    assert _opencode(p, tmp_path / "casa").postura_para(Ruta(str(p / ".env"))) is Postura.DENY


def test_opencode_config_relativa_se_ignora(tmp_path: Path, monkeypatch):
    p = _proyecto(tmp_path)
    _json(tmp_path / "mis-reglas.json", {"permission": {"read": {"*.env": "deny"}}})
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENCODE_CONFIG", "mis-reglas.json")
    assert _opencode(p, tmp_path / "casa").postura_para(Ruta(str(p / ".env"))) is Postura.ASK


# ---- opencode: fuera del proyecto rigen external_directory Y read -----------------------------------------------------------
def test_fuera_del_proyecto_un_deny_de_read_gana_a_un_external_directory_allow(tmp_path: Path):
    p = _proyecto(tmp_path)
    fuera = tmp_path / "otro"
    fuera.mkdir()
    (fuera / ".env").write_text("A=1\n", encoding="utf-8")
    _json(p / "opencode.json", {"permission": {"external_directory": "allow", "read": {"*.env": "deny"}}})
    a = _opencode(p, tmp_path / "casa")
    assert a.postura_para(Ruta(str(fuera / ".env"))) is Postura.DENY
    assert a.regla_para(Ruta(str(fuera / ".env"))) is not None


def test_fuera_del_proyecto_la_base_de_los_env_pregunta_aunque_external_directory_permita(tmp_path: Path):
    p = _proyecto(tmp_path)
    fuera = tmp_path / "otro"
    fuera.mkdir()
    (fuera / ".env").write_text("A=1\n", encoding="utf-8")
    _json(p / "opencode.json", {"permission": {"external_directory": "allow"}})
    assert _opencode(p, tmp_path / "casa").postura_para(Ruta(str(fuera / ".env"))) is Postura.ASK


# ---- opencode: _es_amplia y agentes globales ----------------------------------------------------------------------------------
@pytest.mark.parametrize("patron,amplia", [(None, True), ("*", True), ("**", True), ("*/*", True), ("x/*", False), ("*z", False),
                                           ("*/z", False), ("src/*", False), ("*.env", False)])
def test_es_amplia_solo_si_acepta_cualquier_ruta(patron, amplia):
    assert _es_amplia(SimpleNamespace(especificador=patron)) is amplia


@pytest.mark.parametrize("carpeta", ["agents", "agent"])
def test_un_agente_global_de_opencode_con_permisos_deja_el_nivel_sin_determinar(tmp_path: Path, carpeta: str):
    p, casa = _proyecto(tmp_path), tmp_path / "casa"
    _json(casa / ".config" / "opencode" / carpeta / "equipo" / "revisor.md", "---\npermissions:\n  - action: read\n---\ncuerpo\n")
    a = _opencode(p, casa)
    assert any(n.motivo is MotivoNoRevisado.FUNCION_NO_MODELADA and n.ruta.endswith("revisor.md") for n in a._resultado.no_revisados)
    assert a.postura_para(Ruta(str(p / ".env"))) is Postura.NO_DETERMINADA


def test_una_carpeta_de_agentes_de_opencode_ilegible_no_cuenta_como_inexistente(tmp_path: Path, monkeypatch):
    p = _proyecto(tmp_path)
    (p / ".opencode" / "agents").mkdir(parents=True)
    real = os.scandir

    def falla(ruta="."):
        if str(ruta).replace("\\", "/").endswith(".opencode/agents"):
            raise PermissionError(13, "denegado", str(ruta))
        return real(ruta)

    monkeypatch.setattr(os, "scandir", falla)
    a = _opencode(p, tmp_path / "casa")
    assert a._resultado.reglas_incompletas
    assert a.postura_para(Ruta(str(p / ".env"))) is Postura.NO_DETERMINADA


# ---- Claude Code: sin carpeta personal y carpetas ilegibles -------------------------------------------------------------------
def test_sin_carpeta_personal_utilizable_las_reglas_de_claude_code_quedan_incompletas(tmp_path: Path):
    p = _proyecto(tmp_path)
    a = _claude(p, casa="relativa/no/sirve")
    assert a._resultado.reglas_incompletas
    assert a.postura_para(Ruta(str(p / ".env"))) is Postura.NO_DETERMINADA


def test_un_patron_con_tilde_sin_carpeta_personal_no_se_adivina(tmp_path: Path):
    p = _proyecto(tmp_path)
    assert coincide("~/.env", str(p / ".env"), str(p), "", "proyecto", False) is None


def test_managed_settings_d_ilegible_no_cuenta_como_inexistente(tmp_path: Path, monkeypatch):
    p = _proyecto(tmp_path)
    gest = tmp_path / "gest" / "managed-settings.json"
    (gest.parent / "managed-settings.d").mkdir(parents=True)
    real = os.listdir

    def falla(ruta="."):
        if str(ruta).replace("\\", "/").endswith("managed-settings.d"):
            raise PermissionError(13, "denegado", str(ruta))
        return real(ruta)

    monkeypatch.setattr(os, "listdir", falla)
    a = _claude(p, casa=str(tmp_path / "casa"), gestionada=gest)
    assert a._resultado.reglas_incompletas
    assert any(n.ruta.endswith("managed-settings.d") for n in a._resultado.no_revisados)
    assert a.postura_para(Ruta(str(p / ".env"))) is Postura.NO_DETERMINADA


# ---- git: lo que viene de un include es dudoso también para las credenciales del remoto (GT-13) ---------------------------------
def _remotos(tmp_path: Path, config: str, extra: str | None = None):
    p = _proyecto(tmp_path)
    (p / ".git").mkdir()
    (p / ".git" / "config").write_text(config, encoding="utf-8")
    if extra is not None:
        (p / ".git" / "extra").write_text(extra, encoding="utf-8")
    casa = tmp_path / "casa"
    casa.mkdir()
    res = auditar(str(p), Configuracion(home=str(casa)), medidores=(Sonda(), None))
    return {h.nivel for h in res.hallazgos if h.tipo is Tipo.GIT_REMOTO_SOSPECHOSO}


_REMOTO = '[remote "o"]\n\turl = https://ana:s3cr3t-LARGO-9f2k@host.invalid/x.git\n'


def test_control_una_credencial_literal_en_el_remoto_del_config_principal_es_comprobada(tmp_path: Path):
    assert _remotos(tmp_path, _REMOTO) == {Nivel.COMPROBADO}


def test_una_credencial_literal_en_el_remoto_de_un_include_es_dudosa(tmp_path: Path):
    assert _remotos(tmp_path, "[include]\n\tpath = extra\n", _REMOTO) == {Nivel.POTENCIAL}
