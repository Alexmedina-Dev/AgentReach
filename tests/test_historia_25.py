"""Historia 25: decir POR QUÉ un nivel es «no determinado»: el archivo y la clave que AgentReach no interpreta, sin valores, en el reporte
de terminal, en el HTML y en sus exportaciones JSON y CSV."""

from __future__ import annotations

import csv
import io
import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

from agentreach import cli
from agentreach.app.auditar import auditar
from agentreach.config import Configuracion
from agentreach.contracts import Motivo, MotivoNoRevisado, Plataforma
from test_reporte_html import ESQUEMA, _validar, json_de

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

AHORA = datetime(2026, 11, 10, 15, 30, 5)
SECRETO = "ZQX-COMANDO-SECRETO-777"


@pytest.fixture
def mundo(tmp_path: Path) -> dict:
    casa = tmp_path / "casa"
    (casa / ".claude").mkdir(parents=True)
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    (proyecto / ".env").write_text("STRIPE_SECRET_KEY=sk_live_valor_largo_123\n", encoding="utf-8")
    return {"casa": casa, "proyecto": proyecto, "tmp": tmp_path}


def con_hook(mundo, extra: dict | None = None) -> None:
    datos = {"hooks": {"PreToolUse": [{"matcher": "Read", "hooks": [{"type": "command", "command": SECRETO}]}]}, **(extra or {})}
    (mundo["casa"] / ".claude" / "settings.json").write_text(json.dumps(datos), encoding="utf-8")


def correr(mundo, *extra: str) -> tuple[int, str]:
    salida = io.StringIO()
    anterior = sys.stdout
    sys.stdout = salida
    try:
        codigo = cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--no-banner", *extra], ahora=lambda: AHORA)
    finally:
        sys.stdout = anterior
    return codigo, salida.getvalue()


def plano(texto: str) -> str:
    return " ".join(texto.split())


# ---- los datos: el adaptador dice archivo y clave -------------------------------------------------------------------------------------


def test_claude_dice_el_archivo_y_la_clave_del_hook_pretooluse(mundo):
    con_hook(mundo, {"sandbox": {"enabled": True}})
    res = auditar(str(mundo["proyecto"]), Configuracion(home=str(mundo["casa"])))
    [(_, claude)] = [(p, c) for p, c in res.contextos if p is Plataforma.CLAUDE_CODE]
    causas = {(Path(c.ruta).name, c.motivo, c.clave) for c in claude.causas_no_determinado}
    assert ("settings.json", MotivoNoRevisado.FUNCION_NO_MODELADA, "hooks.PreToolUse") in causas
    assert ("settings.json", MotivoNoRevisado.FUNCION_NO_MODELADA, "sandbox") in causas
    assert all(SECRETO not in c.clave and SECRETO not in str(c.ruta) for c in claude.causas_no_determinado)


@pytest.mark.parametrize("texto, clave", [
    ('{"permission":{"read":"deny","read":"allow"}}', "read"),
    ('{"tools":{"x":true}}', "tools"),
    ('{"mode":{"x":1}}', "mode"),
    ('{"plugin":["foo"]}', "plugin"),
    ('{"experimental":{"policies":[]}}', "experimental.policies"),
    ('{"agent":{"a":{"permission":{"read":"deny"}}}}', "agent.*.permission"),
])
def test_opencode_dice_la_clave(mundo, texto, clave):
    (mundo["proyecto"] / "opencode.json").write_text(texto, encoding="utf-8")
    res = auditar(str(mundo["proyecto"]), Configuracion(home=str(mundo["casa"])))
    [(_, oc)] = [(p, c) for p, c in res.contextos if p is Plataforma.OPENCODE]
    assert clave in {c.clave for c in oc.causas_no_determinado}


def test_un_patron_read_que_no_se_interpreta_dice_en_que_lista_esta(mundo):
    (mundo["proyecto"] / ".claude").mkdir()
    (mundo["proyecto"] / ".claude" / "settings.json").write_text(json.dumps({"permissions": {"deny": ["Read(././.env)"]}}), encoding="utf-8")
    res = auditar(str(mundo["proyecto"]), Configuracion(home=str(mundo["casa"])))
    [(_, cc)] = [(p, c) for p, c in res.contextos if p is Plataforma.CLAUDE_CODE]
    assert "permissions.deny" in {c.clave for c in cc.causas_no_determinado}


def test_un_agente_md_dice_la_clave_del_encabezado_pero_no_su_valor(mundo):
    carpeta = mundo["proyecto"] / ".opencode" / "agents"
    carpeta.mkdir(parents=True)
    (carpeta / "a.md").write_text(f"---\ndescription: x\npermission:\n  read: {SECRETO}\n---\n", encoding="utf-8")
    res = auditar(str(mundo["proyecto"]), Configuracion(home=str(mundo["casa"])))
    [(_, oc)] = [(p, c) for p, c in res.contextos if p is Plataforma.OPENCODE]
    assert "permission" in {c.clave for c in oc.causas_no_determinado} and all(SECRETO not in c.clave for c in oc.causas_no_determinado)


def test_la_clave_se_limpia_y_se_acota():
    from agentreach.contracts import NoRevisado, Ruta

    n = NoRevisado(Ruta("x"), MotivoNoRevisado.FUNCION_NO_MODELADA, clave="a" + chr(27) + "[2J" + "b" * 200)
    assert chr(27) not in n.clave and len(n.clave) <= 80


# ---- terminal --------------------------------------------------------------------------------------------------------------------------


def test_la_terminal_nombra_el_archivo_y_la_clave_y_no_el_valor(mundo):
    con_hook(mundo)
    _, texto = correr(mundo)
    assert "POR QUÉ HAY NIVELES «NO DETERMINADO»" in texto
    assert "~/.claude/settings.json" in texto and "(hooks.PreToolUse)" in plano(texto) and "Claude Code (" in texto
    assert "AgentReach no sabe qué decide ese programa" in plano(texto) and "no modela" not in texto  # Historia 32: lenguaje llano
    assert SECRETO not in texto and "matcher" not in texto


def test_tambien_en_detalle_y_en_ingles(mundo):
    con_hook(mundo)
    _, detalle = correr(mundo, "--detalle")
    assert "~/.claude/settings.json" in detalle and "(hooks.PreToolUse)" in plano(detalle)
    _, ingles = correr(mundo, "--idioma", "en")
    assert 'WHY SOME LEVELS ARE "NOT DETERMINED"' in ingles and "(hooks.PreToolUse)" in plano(ingles) and "Undetermined:" in ingles


def test_sin_causa_no_hay_seccion(mundo):
    (mundo["casa"] / ".claude" / "settings.json").write_text(json.dumps({"permissions": {"deny": []}}), encoding="utf-8")
    _, texto = correr(mundo)
    assert "NO DETERMINADO" not in texto


# ---- HTML y exportaciones --------------------------------------------------------------------------------------------------------------


def _json_del_html(mundo, tmp_path: Path, *extra: str) -> dict:
    destino = tmp_path / "r.html"
    assert cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--formato", "html", "--salida", str(destino), *extra],
                    ahora=lambda: AHORA) in (0, 1)
    return json_de(destino.read_text(encoding="utf-8"))


def test_el_json_del_html_trae_archivo_y_clave_y_cumple_el_esquema(mundo, tmp_path):
    con_hook(mundo)
    datos = _json_del_html(mundo, tmp_path)
    _validar(datos, ESQUEMA)
    claude = next(a for a in datos["agents"] if a["id"] == "claude_code")
    assert {"path": "~/.claude/settings.json", "key": "hooks.PreToolUse", "reason": "funcion_no_modelada"} in claude["not_determined"]
    assert "funcion_no_modelada" in datos["catalog"]["no_review"] and SECRETO not in json.dumps(datos)
    assert any(f["reason"] == "no_determinado" for f in claude["findings"])


def test_un_agente_sin_hallazgos_no_determinados_no_lleva_la_lista(mundo, tmp_path):
    con_hook(mundo)
    datos = _json_del_html(mundo, tmp_path)
    for a in datos["agents"]:
        if not any(f["reason"] == "no_determinado" for f in a["findings"]):
            assert a["not_determined"] == []


def test_la_plantilla_muestra_y_exporta_el_por_que():
    from agentreach.reporting.html import _plantilla

    plantilla = _plantilla()
    for esperado in ("not_determined", "ndBecause", "ndNote", "not_determined_by", 'id="ndnote"'):
        assert esperado in plantilla, esperado


def test_el_catalogo_marca_el_motivo():
    assert Motivo.NO_DETERMINADO.value == "no_determinado"


# ---- en el navegador (se omite sin playwright): el «por qué» sale en pantalla y en el JSON y el CSV exportados -----------------------


@pytest.fixture(scope="module")
def navegador():
    """Un navegador real. Es de módulo (se crea ANTES de que las pruebas redirijan HOME y las carpetas de programas, que Edge necesita)."""
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


def test_en_el_navegador_el_por_que_sale_en_el_detalle_y_en_las_exportaciones(mundo, tmp_path, navegador, capsys):
    con_hook(mundo)
    destino = tmp_path / "r.html"
    assert cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--formato", "html", "--salida", str(destino)],
                    ahora=lambda: AHORA) in (0, 1), capsys.readouterr().err
    assert destino.exists(), "el reporte no se escribió"
    pg = navegador.new_context(accept_downloads=True).new_page()
    errores: list[str] = []
    pg.on("pageerror", lambda e: errores.append(str(e)))
    pg.goto(destino.as_uri())
    pg.wait_for_timeout(300)
    nota = pg.inner_text("#ndnote")
    assert "hooks.PreToolUse" in nota and "~/.claude/settings.json" in nota
    pg.evaluate("window.__ar.setView('list')")
    pg.wait_for_timeout(100)
    pg.click("button[data-row]")
    assert "hooks.PreToolUse" in pg.inner_text("#folds")
    with pg.expect_download() as descarga:
        pg.click("button:has-text('JSON')")
    filas = json.loads(Path(descarga.value.path()).read_text(encoding="utf-8"))["findings"]
    assert any("hooks.PreToolUse" in f.get("not_determined_by", "") for f in filas) and SECRETO not in json.dumps(filas)
    with pg.expect_download() as descarga:
        pg.click("button:has-text('CSV')")
    contenido = Path(descarga.value.path()).read_text(encoding="utf-8")
    filas_csv = list(csv.DictReader(io.StringIO(contenido)))
    assert any("hooks.PreToolUse" in f["not_determined_by"] for f in filas_csv) and SECRETO not in contenido
    assert not errores
