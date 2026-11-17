"""Historia 46: lo que sale de `.claude/settings*.json` es de Claude Code; `.mcp.json` sigue «sin agente»."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from agentreach import cli
from test_reporte_html import ESQUEMA, _validar, json_de

pytestmark = pytest.mark.sin_tope_por_nombre

AHORA = datetime(2026, 11, 12, 10, 0, 0)
HOOKS = {"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "python x.py"}]}]}}
MCP = {"mcpServers": {"local": {"command": "python", "args": ["x"]}}}


@pytest.fixture
def mundo(tmp_path: Path) -> dict:
    casa, proyecto = tmp_path / "casa", tmp_path / "proyecto"
    casa.mkdir()
    proyecto.mkdir()
    return {"casa": casa, "proyecto": proyecto, "tmp": tmp_path}


def _escribir(mundo, relativa: str, contenido) -> None:
    destino = mundo["proyecto"] / relativa
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(contenido, indent=2) + "\n", encoding="utf-8")


def _html(mundo, *extra: str) -> dict:
    destino = mundo["tmp"] / f"r{len(extra)}.html"
    assert cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--formato", "html", "--salida", str(destino), *extra],
                    ahora=lambda: AHORA) in (0, 1)
    datos = json_de(destino.read_text(encoding="utf-8"))
    _validar(datos, ESQUEMA)
    return datos


def _rutas(datos: dict, id_agente: str) -> list[str]:
    por_id = {a["id"]: a for a in datos["agents"]}
    if id_agente not in por_id:
        return []
    return [f["path"].replace("\\", "/").rsplit("/", 1)[-1] for f in por_id[id_agente]["findings"] if f["type"] in ("TH-14", "TH-15")]


def test_th14_de_settings_json_sale_en_claude_code_y_no_sin_agente(mundo):
    _escribir(mundo, ".claude/settings.json", HOOKS)
    datos = _html(mundo)
    assert _rutas(datos, "claude_code") == ["settings.json"]
    assert _rutas(datos, "none") == []


def test_th14_de_mcp_json_sigue_sin_agente_y_el_de_settings_en_claude_code(mundo):
    _escribir(mundo, ".claude/settings.json", HOOKS)
    _escribir(mundo, ".mcp.json", MCP)
    datos = _html(mundo)
    assert _rutas(datos, "claude_code") == ["settings.json"]
    assert _rutas(datos, "none") == [".mcp.json"]


def test_con_agente_opencode_no_sale_el_de_claude_pero_si_el_de_mcp_json(mundo):
    _escribir(mundo, ".claude/settings.json", HOOKS)
    _escribir(mundo, ".mcp.json", MCP)
    datos = _html(mundo, "--agente", "opencode")
    assert _rutas(datos, "claude_code") == []
    assert ".mcp.json" in _rutas(datos, "none")
    assert all("settings.json" not in _rutas(datos, a["id"]) for a in datos["agents"])


def test_solo_settings_json_da_pestana_de_claude_code_con_su_hallazgo(mundo):
    _escribir(mundo, ".claude/settings.json", HOOKS)
    datos = _html(mundo)
    assert [c["id"] for c in datos["configured_agents"]] == ["claude_code"]
    # Que opencode NO salga cuando no está configurado es de la Historia 40 (PR aparte); aquí solo se exige la pestaña de Claude Code.
    assert "claude_code" in [a["id"] for a in datos["agents"]]


def test_th15_de_settings_local_sale_en_claude_code(mundo):
    _escribir(mundo, ".claude/settings.local.json", {"permissions": {"defaultMode": "bypassPermissions"}})
    datos = _html(mundo)
    assert _rutas(datos, "claude_code") == ["settings.local.json"] and _rutas(datos, "none") == []
