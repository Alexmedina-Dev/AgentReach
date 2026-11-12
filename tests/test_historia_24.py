"""Historia 24: reconocer los agentes CONFIGURADOS con el catálogo de firmas (``docs/agentes-catalogo/catalogo-agentes.json``)."""

from __future__ import annotations

import io
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest

from agentreach import cli
from agentreach.app.agentes import Confianza, cargar_catalogo, detectar_agentes
from test_reporte_html import ESQUEMA, _validar, json_de

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

AHORA = datetime(2026, 11, 10, 15, 30, 5)
RAIZ = Path(__file__).parents[1]


@pytest.fixture
def mundo(tmp_path: Path) -> dict:
    casa = tmp_path / "casa"
    casa.mkdir()
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    return {"casa": casa, "proyecto": proyecto, "tmp": tmp_path}


def poner(base: Path, *rutas: str) -> None:
    for r in rutas:
        destino = base / r
        if r.endswith("/"):
            destino.mkdir(parents=True, exist_ok=True)
        else:
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text("x", encoding="utf-8")


def detectar(mundo, env=None):
    agentes, sin_decidir = detectar_agentes(str(mundo["proyecto"]), str(mundo["casa"]), env or {}, sys.platform)
    return {a.id: a for a in agentes}, sin_decidir


# ---- el catálogo ---------------------------------------------------------------------------------------------------------------------


def test_el_catalogo_del_paquete_es_el_de_docs():
    assert (RAIZ / "src/agentreach/data/catalogo-agentes.json").read_bytes() == (RAIZ / "docs/agentes-catalogo/catalogo-agentes.json").read_bytes()
    assert len(cargar_catalogo()) == 22


# ---- firmas fuertes, débiles y compartidas ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("ruta, agente", [
    (".cursor/rules/a.mdc", "cursor"), (".windsurfrules", "windsurf"), (".clinerules/", "cline"), (".kiro/steering/", "kiro"),
    (".roorules", "roo-code"), (".codex/config.toml", "codex-cli"), (".gemini/settings.json", "gemini-cli"),
    (".aider.conf.yml", "aider"), ("QWEN.md", "qwen-code"), (".opencode/opencode.json", "opencode"), ("opencode.jsonc", "opencode"), (".github/agents/a.agent.md", "copilot-vscode"),
    ("CLAUDE.md", "claude-code"), ("opencode.json", "opencode"), (".claude/settings.json", "claude-code"),
])
def test_una_firma_fuerte_verificada_da_confianza_alta(mundo, ruta, agente):
    poner(mundo["proyecto"], ruta)
    agentes, _ = detectar(mundo)
    assert agente in agentes and agentes[agente].confianza is Confianza.ALTA and not agentes[agente].marco


@pytest.mark.parametrize("ruta", ["AGENTS.md", ".mcp.json", ".vscode/", ".github/", ".env", ".gemini/", ".agents/", ".idea/", "GEMINI.md",
                                  "CONVENTIONS.md", "AGENT.md", ".aider.chat.history.md"])
def test_los_nombres_compartidos_o_de_historial_jamas_identifican_a_un_agente(mundo, ruta):
    poner(mundo["proyecto"], ruta)
    agentes, _ = detectar(mundo)
    assert agentes == {}, ruta


@pytest.mark.parametrize("ruta, agente", [(".codex/", "codex-cli")])
def test_la_carpeta_propia_sin_su_archivo_de_configuracion_es_solo_un_indicio(mundo, ruta, agente):
    poner(mundo["proyecto"], ruta)
    agentes, _ = detectar(mundo)
    assert agentes[agente].confianza is Confianza.HIPOTESIS


def test_agents_md_solo_es_no_determinado_con_la_lista_de_candidatos(mundo):
    poner(mundo["proyecto"], "AGENTS.md")
    agentes, sin_decidir = detectar(mundo)
    assert agentes == {} and len(sin_decidir) == 1
    assert {"OpenAI Codex CLI", "Cursor", "opencode", "Claude Code"} <= set(sin_decidir[0].candidatos)


def test_agents_md_con_un_agente_claro_ya_no_es_indeterminado(mundo):
    poner(mundo["proyecto"], "AGENTS.md", ".codex/config.toml")
    agentes, sin_decidir = detectar(mundo)
    assert list(agentes) == ["codex-cli"] and sin_decidir == ()


def test_varios_agentes_se_reportan_todos_sin_elegir_uno(mundo):
    poner(mundo["proyecto"], "CLAUDE.md", "opencode.json", ".cursor/rules/a.mdc", ".windsurfrules")
    agentes, _ = detectar(mundo)
    assert set(agentes) == {"claude-code", "opencode", "cursor", "windsurf"}
    assert {i for i, a in agentes.items() if a.analizado} == {"claude-code", "opencode"}  # solo estos dos tienen adaptador


def test_una_firma_fuerte_sin_fuente_verificada_tiene_tope_potencial(mundo):
    poner(mundo["proyecto"], ".aiderignore")  # fuerte pero «verificada: false» en el catálogo
    agentes, _ = detectar(mundo)
    assert agentes["aider"].confianza is Confianza.POTENCIAL


def test_el_historial_no_cuenta_como_configuracion_ni_se_menciona(mundo):
    poner(mundo["proyecto"], ".aider.chat.history.md", ".aider.input.history")
    agentes, _ = detectar(mundo)
    assert agentes == {}


def test_el_claude_md_no_hace_que_copilot_parezca_configurado(mundo):
    poner(mundo["proyecto"], "CLAUDE.md")
    agentes, _ = detectar(mundo)
    assert list(agentes) == ["claude-code"]


# ---- marcos ---------------------------------------------------------------------------------------------------------------------------


def test_un_marco_se_reporta_instalado_sobre_el_agente_cuya_carpeta_toca(mundo):
    poner(mundo["proyecto"], "_bmad/", ".claude/skills/bmad-x/SKILL.md", "CLAUDE.md")
    agentes, _ = detectar(mundo)
    assert agentes["bmad"].marco and agentes["bmad"].sobre == ("claude-code",) and agentes["bmad"].confianza is Confianza.ALTA
    assert not agentes["claude-code"].marco


def test_una_habilidad_sola_no_basta_para_afirmar_un_marco(mundo):
    poner(mundo["proyecto"], ".claude/skills/bmad-x/SKILL.md")
    agentes, _ = detectar(mundo)
    assert "bmad" not in agentes and "claude-code" in agentes  # la habilidad es de Claude Code; el marco necesita su huella propia


# ---- usuario y entorno -----------------------------------------------------------------------------------------------------------------------


def test_la_configuracion_del_usuario_se_reporta_con_su_ambito(mundo):
    poner(mundo["casa"], ".claude/settings.json")
    agentes, _ = detectar(mundo)
    assert agentes["claude-code"].confianza is Confianza.ALTA
    assert {e.ambito for e in agentes["claude-code"].evidencia} == {"usuario"}


def test_una_carpeta_del_usuario_sola_es_un_indicio(mundo):
    poner(mundo["casa"], ".kiro/")  # una carpeta sola, sin sus archivos
    agentes, _ = detectar(mundo)
    assert agentes["kiro"].confianza is Confianza.HIPOTESIS


def test_los_secretos_el_estado_y_los_datos_del_usuario_no_cuentan(mundo):
    poner(mundo["casa"], ".claude.json", ".claude/projects/", ".claude/history.jsonl")
    agentes, _ = detectar(mundo)
    assert "claude-code" not in agentes or all("history" not in e.ruta and e.ruta.endswith(".claude.json") is False for e in agentes["claude-code"].evidencia)


def test_las_variables_de_entorno_dan_su_nombre_nunca_su_valor(mundo):
    agentes, _ = detectar(mundo, {"AIDER_DARK_MODE": "ZQX-VALOR-SECRETO", "GOOSE_PROVIDER": "x", "PATH": "y", "GEMINI_API_KEY": "k"})
    assert agentes["aider"].evidencia[0].ruta == "AIDER_DARK_MODE" and agentes["aider"].evidencia[0].ambito == "entorno"
    assert "goose" in agentes and "gemini-cli" not in agentes  # GEMINI_API_KEY la usa cualquier cliente de Gemini
    assert "ZQX-VALOR-SECRETO" not in repr(agentes)


def test_sin_nada_no_hay_agentes(mundo):
    agentes, sin_decidir = detectar(mundo)
    assert agentes == {} and sin_decidir == ()


def test_detectar_no_abre_el_contenido_de_nada(mundo):
    poner(mundo["proyecto"], "CLAUDE.md", ".cursor/rules/a.mdc", "_bmad/", ".claude/settings.json", "opencode.json")
    poner(mundo["casa"], ".claude/settings.json")
    abiertos: list[str] = []

    def gancho(evento, args):
        if evento == "open" and isinstance(args[0], (str, bytes, os.PathLike)) and str(mundo["tmp"]) in str(args[0]):
            abiertos.append(str(args[0]))

    sys.addaudithook(gancho)  # inerte fuera de esta prueba: solo anota archivos de la carpeta temporal
    detectar(mundo)
    assert abiertos == []


# ---- el reporte ---------------------------------------------------------------------------------------------------------------------------


def _html(mundo, *extra: str) -> dict:
    destino = mundo["tmp"] / f"r{len(extra)}.html"
    assert cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--formato", "html", "--salida", str(destino), *extra],
                    ahora=lambda: AHORA) in (0, 1)
    return json_de(destino.read_text(encoding="utf-8"))


def test_el_json_del_html_trae_agentes_marcos_y_rastros_sin_decidir(mundo):
    poner(mundo["proyecto"], "CLAUDE.md", ".cursor/rules/a.mdc", "_bmad/", ".claude/skills/bmad-x/SKILL.md")
    datos = _html(mundo)
    _validar(datos, ESQUEMA)
    por_id = {c["id"]: c for c in datos["configured_agents"]}
    assert por_id["claude_code"]["analyzed"] is True and por_id["claude_code"]["confidence"] == "high"
    assert por_id["cursor"]["analyzed"] is False and por_id["cursor"]["kind"] == "agent"
    assert por_id["bmad"]["kind"] == "framework" and por_id["bmad"]["on"] == ["Claude Code"]
    assert datos["undetermined_traces"] == []


def test_agents_md_solo_sale_como_rastro_no_determinado(mundo):
    poner(mundo["proyecto"], "AGENTS.md")
    datos = _html(mundo)
    _validar(datos, ESQUEMA)
    assert datos["configured_agents"] == [] and datos["undetermined_traces"][0]["path"] == "AGENTS.md"
    assert "Cursor" in datos["undetermined_traces"][0]["candidates"]


def test_agente_filtra_y_el_entorno_no_filtra_valores(mundo, monkeypatch):
    poner(mundo["proyecto"], "CLAUDE.md", "opencode.json", ".cursor/rules/a.mdc")
    monkeypatch.setenv("AIDER_SECRETO", "ZQX-VALOR")
    todos = {c["id"] for c in _html(mundo)["configured_agents"]}
    assert {"claude_code", "opencode", "cursor", "aider"} <= todos
    solo = {c["id"] for c in _html(mundo, "--agente", "opencode")["configured_agents"]}
    assert solo == {"opencode"}
    destino = mundo["tmp"] / "r0.html"
    assert "ZQX-VALOR" not in destino.read_text(encoding="utf-8") and "AIDER_SECRETO" in destino.read_text(encoding="utf-8")


def _terminal(mundo, *extra: str) -> str:
    salida = io.StringIO()
    anterior = sys.stdout
    sys.stdout = salida
    try:
        cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--no-banner", *extra], ahora=lambda: AHORA)
    finally:
        sys.stdout = anterior
    return " ".join(salida.getvalue().split())


def test_la_terminal_dice_configurado_nunca_ejecutado(mundo):
    poner(mundo["proyecto"], "CLAUDE.md", ".cursor/rules/a.mdc", "_bmad/", ".claude/skills/bmad-x/SKILL.md")
    texto = _terminal(mundo)
    assert "AGENTES CONFIGURADOS" in texto and "no sabe si se ejecutó" in texto
    assert "Claude Code · configurado" in texto and "Cursor · configurado — AgentReach aún no analiza qué puede alcanzar" in texto
    assert "BMAD (BMad Method) · configurado — marco instalado sobre Claude Code" in texto
    assert "ejecutado:" not in texto.lower() and "se ejecutó" not in texto.lower().replace("no sabe si se ejecutó", "")


def test_la_terminal_con_detalle_lista_la_evidencia_y_en_ingles(mundo):
    poner(mundo["proyecto"], "CLAUDE.md")
    assert "proyecto:" in _terminal(mundo, "--detalle") and "CLAUDE.md" in _terminal(mundo, "--detalle")
    ingles = _terminal(mundo, "--idioma", "en")
    assert "CONFIGURED AGENTS" in ingles and "does not mean the agent has run" in ingles and "Claude Code · configured" in ingles


def test_agents_md_solo_dice_no_determinado_en_la_terminal(mundo):
    poner(mundo["proyecto"], "AGENTS.md")
    texto = _terminal(mundo)
    assert "No determinado:" in texto and "lo leen varios agentes" in texto


def test_sin_agentes_no_hay_seccion(mundo):
    assert "AGENTES CONFIGURADOS" not in _terminal(mundo)


# ---- la plantilla: el selector solo lleva los agentes que se analizan ---------------------------------------------------------------


@pytest.fixture(scope="module")
def navegador():
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as p:
        nav = None
        for canal in ("msedge", None):
            try:
                nav = p.chromium.launch(channel=canal, headless=True) if canal else p.chromium.launch(headless=True)
                break
            except Exception:  # noqa: BLE001, S112
                continue
        if nav is None:
            pytest.skip("no hay un navegador para probar")
        yield nav
        nav.close()


def test_en_el_navegador_los_no_analizados_se_listan_pero_no_entran_al_selector(mundo, navegador):
    poner(mundo["proyecto"], "CLAUDE.md", ".cursor/rules/a.mdc", "_bmad/", ".claude/skills/bmad-x/SKILL.md")
    destino = mundo["tmp"] / "n.html"
    assert cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--formato", "html", "--salida", str(destino)],
                    ahora=lambda: AHORA) in (0, 1)
    pg = navegador.new_context().new_page()
    errores: list[str] = []
    pg.on("pageerror", lambda e: errores.append(str(e)))
    pg.goto(destino.as_uri())
    pg.wait_for_timeout(300)
    cfg = pg.inner_text("#cfg")
    assert "Cursor" in cfg and "configurado" in cfg and "todavía no analiza" in cfg
    assert "marco instalado sobre Claude Code" in cfg and "ejecutado" not in cfg.lower()
    selector = pg.inner_text("#agentTabs") if pg.locator("#agentTabs").count() else pg.inner_text(".tabs")
    assert "Claude Code" in selector and "Cursor" not in selector and "BMAD" not in selector
    assert not errores


# ---- Historia 26: GitHub Copilot, un solo agente cuando la única señal es compartida ------------------------------------------------


def test_copilot_instructions_solo_es_un_agente_y_no_dos(mundo):
    poner(mundo["proyecto"], ".github/copilot-instructions.md")
    agentes, _ = detectar(mundo)
    assert list(agentes) == ["github-copilot"]
    uno = agentes["github-copilot"]
    assert uno.nombre == "GitHub Copilot (VS Code o su línea de comandos)" and uno.confianza is Confianza.ALTA and not uno.analizado
    assert [os.path.basename(e.ruta) for e in uno.evidencia] == ["copilot-instructions.md"]


def test_las_instrucciones_por_ruta_tambien_son_compartidas(mundo):
    poner(mundo["proyecto"], ".github/instructions/x.instructions.md")
    agentes, _ = detectar(mundo)
    assert list(agentes) == ["github-copilot"]


def test_con_una_senal_propia_de_vscode_queda_solo_vscode(mundo):
    poner(mundo["proyecto"], ".github/copilot-instructions.md", ".github/agents/a.agent.md")
    agentes, _ = detectar(mundo)
    assert list(agentes) == ["copilot-vscode"]  # la compartida no afirma a la CLI


def test_con_una_senal_propia_de_la_cli_queda_solo_la_cli(mundo):
    poner(mundo["proyecto"], ".github/copilot-instructions.md")
    poner(mundo["casa"], ".copilot/config.json")
    agentes, _ = detectar(mundo)
    assert list(agentes) == ["copilot-cli"]


def test_con_senales_propias_de_las_dos_quedan_las_dos(mundo):
    poner(mundo["proyecto"], ".github/agents/a.agent.md")
    poner(mundo["casa"], ".copilot/config.json")
    agentes, _ = detectar(mundo)
    assert set(agentes) == {"copilot-vscode", "copilot-cli"}


def test_otros_agentes_no_se_tocan_al_unificar_copilot(mundo):
    poner(mundo["proyecto"], ".github/copilot-instructions.md", "CLAUDE.md", ".cursor/rules/a.mdc")
    agentes, _ = detectar(mundo)
    assert set(agentes) == {"github-copilot", "claude-code", "cursor"}


def test_el_json_y_la_terminal_muestran_un_solo_copilot(mundo):
    poner(mundo["proyecto"], ".github/copilot-instructions.md")
    datos = _html(mundo)
    _validar(datos, ESQUEMA)
    assert [c["id"] for c in datos["configured_agents"]] == ["github_copilot"]
    assert datos["configured_agents"][0]["name"] == "GitHub Copilot (VS Code o su línea de comandos)"
    texto = _terminal(mundo)
    assert texto.count("GitHub Copilot") == 1 and "GitHub Copilot (VS Code o su línea de comandos) · configurado" in texto
