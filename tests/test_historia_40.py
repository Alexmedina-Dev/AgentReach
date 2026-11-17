"""Historia 40: un agente que no está en la carpeta ni en el equipo no aparece (terminal, HTML y código de salida)."""

from __future__ import annotations

import io
import sys
from datetime import datetime
from pathlib import Path

import pytest

from agentreach import cli
from agentreach.app.agentes import AgenteDetectado, Confianza, EvidenciaDetectada
from agentreach.app.auditar import ResultadoAuditoria
from agentreach.contracts import Motivo, Nivel, PermisoLectura, PermisosArchivo, Plataforma, Postura
from agentreach.core.nivel import Hechos
from agentreach.reporting.gate import plataformas_mostradas, preparar
from test_historia_24 import poner
from test_reporte_html import BASE, ESQUEMA, LectorFalso, _validar, finding, json_de

pytestmark = pytest.mark.sin_tope_por_nombre

AHORA = datetime(2026, 11, 12, 10, 0, 0)
ACLARACION = "analizados sin señales de configuración"


@pytest.fixture
def mundo(tmp_path: Path) -> dict:
    casa, proyecto = tmp_path / "casa", tmp_path / "proyecto"
    casa.mkdir()
    proyecto.mkdir()
    return {"casa": casa, "proyecto": proyecto, "tmp": tmp_path}


def _terminal(mundo, *extra: str) -> str:
    salida = io.StringIO()
    anterior = sys.stdout
    sys.stdout = salida
    try:
        cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--no-banner", *extra], ahora=lambda: AHORA)
    finally:
        sys.stdout = anterior
    return " ".join(salida.getvalue().split())


def _html(mundo, *extra: str) -> dict:
    destino = mundo["tmp"] / f"r{len(extra)}.html"
    assert cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--formato", "html", "--salida", str(destino), *extra],
                    ahora=lambda: AHORA) in (0, 1)
    datos = json_de(destino.read_text(encoding="utf-8"))
    _validar(datos, ESQUEMA)
    return datos


def _ids(datos: dict) -> list[str]:
    return [a["id"] for a in datos["agents"]]


def _con_env(mundo, *rutas: str) -> None:
    poner(mundo["proyecto"], ".env", *rutas)


def _html_sin_permiso(mundo, nombre: str) -> dict:
    """Responde «s» a la primera pregunta y «n» a la segunda (reglas del usuario)."""
    destino = mundo["tmp"] / nombre
    respuestas = iter(["s", "n"])
    cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--formato", "html", "--salida", str(destino)],
             ahora=lambda: AHORA, preguntar=lambda _t: next(respuestas, "n"))
    return json_de(destino.read_text(encoding="utf-8"))


# ---- matriz: terminal y HTML ----------------------------------------------------------------------------------------------


def test_solo_claude_code_detectado_no_muestra_nada_de_opencode(mundo):
    _con_env(mundo, ".claude/settings.json")
    texto = _terminal(mundo, "--detalle")
    assert "opencode" not in texto.lower()
    assert ACLARACION not in texto
    datos = _html(mundo)
    assert "opencode" not in _ids(datos) and "claude_code" in _ids(datos)
    assert all("no_signals" not in a for a in datos["agents"])


def test_solo_opencode_detectado_no_muestra_claude_code(mundo):
    _con_env(mundo, "opencode.json")
    texto = _terminal(mundo, "--detalle")
    assert "AGENTE: Claude Code" not in texto and ACLARACION not in texto
    assert "claude_code" not in _ids(_html(mundo))


def test_con_los_dos_detectados_salen_los_dos_sin_aclaracion(mundo):
    _con_env(mundo, ".claude/settings.json", "opencode.json")
    datos = _html(mundo)
    assert _ids(datos)[:2] == ["claude_code", "opencode"] and all("no_signals" not in a for a in datos["agents"])
    assert ACLARACION not in _terminal(mundo)


def test_ninguno_detectado_muestra_los_dos_con_la_aclaracion(mundo):
    _con_env(mundo)
    texto = _terminal(mundo)
    assert f"Agentes {ACLARACION}: Claude Code, opencode" in texto
    assert "AGENTES CONFIGURADOS" not in texto and "Según los archivos de configuración" not in texto
    por_id = {a["id"]: a for a in _html(mundo)["agents"]}
    assert por_id["claude_code"]["no_signals"] is True and por_id["opencode"]["no_signals"] is True


def test_agente_pedido_y_no_detectado_se_muestra_con_la_aclaracion(mundo):
    _con_env(mundo, ".claude/settings.json")
    texto = _terminal(mundo, "--agente", "opencode")
    assert f"Agentes {ACLARACION}: opencode" in texto and "Claude Code" not in texto
    por_id = {a["id"]: a for a in _html(mundo, "--agente", "opencode")["agents"]}
    assert "claude_code" not in por_id and por_id["opencode"]["no_signals"] is True


def test_agente_pedido_y_detectado_va_como_siempre_sin_aclaracion(mundo):
    _con_env(mundo, "opencode.json")
    assert ACLARACION not in _terminal(mundo, "--agente", "opencode")
    por_id = {a["id"]: a for a in _html(mundo, "--agente", "opencode")["agents"]}
    assert "no_signals" not in por_id["opencode"]


def test_una_firma_debil_basta_para_tener_pestana(mundo):
    _con_env(mundo, ".worktreeinclude")  # firma débil de Claude Code: solo un indicio (hipótesis)
    datos = _html(mundo)
    por_id = {c["id"]: c for c in datos["configured_agents"]}
    assert por_id["claude_code"]["confidence"] == "hypothesis"
    assert "claude_code" in _ids(datos) and "opencode" not in _ids(datos)


def test_sin_permiso_de_reglas_del_usuario_solo_cuenta_el_proyecto(mundo):
    (mundo["casa"] / ".claude").mkdir()
    (mundo["casa"] / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
    _con_env(mundo, "opencode.json")
    assert "claude_code" not in _ids(_html_sin_permiso(mundo, "n.html"))


def test_sin_permiso_y_sin_senales_en_el_proyecto_salen_los_dos_con_la_aclaracion(mundo):
    (mundo["casa"] / ".claude").mkdir()
    (mundo["casa"] / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
    _con_env(mundo)
    por_id = {a["id"]: a for a in _html_sin_permiso(mundo, "n2.html")["agents"]}
    assert por_id["claude_code"]["no_signals"] and por_id["opencode"]["no_signals"]


# ---- la compuerta y el código de salida -----------------------------------------------------------------------------------


def _agente(id_: str, nombre: str) -> AgenteDetectado:
    return AgenteDetectado(id_, nombre, Confianza.ALTA, False, (), (EvidenciaDetectada("proyecto", "x", True, True),), True)


def test_la_funcion_de_plataformas_mostradas():
    cc, oc = _agente("claude-code", "Claude Code"), _agente("opencode", "opencode")
    assert plataformas_mostradas((cc,), None) == (frozenset({Plataforma.CLAUDE_CODE}), frozenset())
    assert plataformas_mostradas((cc, oc), None)[0] == {Plataforma.CLAUDE_CODE, Plataforma.OPENCODE}
    todas = frozenset({Plataforma.CLAUDE_CODE, Plataforma.OPENCODE})
    assert plataformas_mostradas((), None) == (todas, todas)
    assert plataformas_mostradas((cc,), Plataforma.OPENCODE) == (frozenset({Plataforma.OPENCODE}), frozenset({Plataforma.OPENCODE}))


def _datos(agentes):
    comprobado = finding(".env", Plataforma.OPENCODE, Nivel.COMPROBADO, Motivo.EXISTE_LEGIBLE_SIN_REGLA)
    hechos = {comprobado: Hechos(True, PermisosArchivo(PermisoLectura.SI, False, False, "u", "x"), Postura.SIN_REGLA)}
    res = ResultadoAuditoria((comprobado, finding("a.env", Plataforma.CLAUDE_CODE, Nivel.POTENCIAL)), (), 3, hechos, (), tuple(agentes))
    return preparar(res, BASE, ahora=AHORA, home=None, lector=LectorFalso())


def test_un_comprobado_de_un_agente_oculto_no_cuenta_para_el_codigo_de_salida():
    oculto = _datos([_agente("claude-code", "Claude Code")])
    assert all(h.plataforma is not Plataforma.OPENCODE for h in oculto.hallazgos) and oculto.codigo_de_salida == 0
    visible = _datos([_agente("claude-code", "Claude Code"), _agente("opencode", "opencode")])
    assert any(h.nivel is Nivel.COMPROBADO for h in visible.hallazgos) and visible.codigo_de_salida == 1


def test_ningun_detectado_no_oculta_a_nadie():
    d = _datos([])
    assert {h.plataforma for h in d.hallazgos} == {Plataforma.CLAUDE_CODE, Plataforma.OPENCODE}
    assert d.sin_senales == {Plataforma.CLAUDE_CODE, Plataforma.OPENCODE}


# ---- lo que ve la persona en el navegador (se omite si no hay Playwright ni un navegador) ----------------------------------


@pytest.fixture(scope="module")
def navegador():
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as p:
        nav = None
        for canal in ("msedge", None):
            try:
                nav = p.chromium.launch(channel=canal, headless=True) if canal else p.chromium.launch(headless=True)
                break
            except Exception:  # noqa: BLE001 - sin ese navegador, se prueba el siguiente
                nav = None
        if nav is None:
            pytest.skip("no hay un navegador (Edge o Chromium) para probar")
        yield nav
        nav.close()


def _abrir(navegador, mundo, nombre: str):
    destino = mundo["tmp"] / nombre
    assert cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--formato", "html", "--salida", str(destino)],
                    ahora=lambda: AHORA) in (0, 1)
    pg = navegador.new_context(viewport={"width": 1280, "height": 900}).new_page()
    errores: list[str] = []
    pg.on("pageerror", lambda e: errores.append(str(e)))
    pg.goto(destino.as_uri())
    pg.wait_for_timeout(250)
    return pg, errores


def test_en_el_navegador_ninguno_detectado_muestra_las_dos_pestanas_y_la_nota_en_los_dos_idiomas(navegador, mundo):
    _con_env(mundo)
    pg, errores = _abrir(navegador, mundo, "nav1.html")
    tabs = pg.inner_text("#tabs")
    assert "Claude Code" in tabs and "opencode" in tabs
    for boton in ("opencode", "Claude Code"):  # la nota sale en la pestaña de cada agente
        pg.click(f"#tabs .tab:has-text('{boton}')")
        pg.click("[data-lang=es]")
        assert "Analizado sin señales de configuración en lo que AgentReach pudo revisar." in pg.inner_text("#agentnote")
        pg.click("[data-lang=en]")
        assert "Analyzed without configuration signals in what AgentReach could check." in pg.inner_text("#agentnote")
    assert not errores


def test_en_el_navegador_un_agente_detectado_no_lleva_la_nota(navegador, mundo):
    _con_env(mundo, ".claude/settings.json")
    pg, errores = _abrir(navegador, mundo, "nav2.html")
    assert "opencode" not in pg.inner_text("#tabs") and "Claude Code" in pg.inner_text("#tabs")
    for idioma in ("es", "en"):
        pg.click(f"[data-lang={idioma}]")
        nota = pg.inner_text("#agentnote")
        assert "Analizado sin señales" not in nota and "Analyzed without configuration signals" not in nota
    assert not errores
