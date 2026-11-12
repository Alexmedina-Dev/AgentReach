"""Historia 33 en un navegador real: «Cómo leer este reporte» abierta al cargar, plegado conservado, impresión y sin glosario.

Se omite si no hay ``playwright`` o un navegador. Para correrla: ``uv run --with playwright pytest tests/test_historia_33_navegador.py``
(Edge viene con Windows; si no, ``playwright install chromium``).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
sync_api = pytest.importorskip("playwright.sync_api")
from test_reporte_html import BLOQUE, datos, finding, html_de

pytestmark = pytest.mark.sin_tope_por_nombre


@pytest.fixture(scope="module")
def navegador():
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


def _abrir(navegador, tmp_path: Path, html: str):
    archivo = tmp_path / "r.html"
    archivo.write_text(html, encoding="utf-8")
    pg = navegador.new_context(viewport={"width": 1280, "height": 900}).new_page()
    errores: list[str] = []
    pg.on("pageerror", lambda e: errores.append(str(e)))
    pg.goto(archivo.as_uri())
    pg.wait_for_timeout(250)
    return pg, errores


def test_abierta_al_cargar_con_4_fichas_visibles_y_8_plegadas(navegador, tmp_path: Path):
    pg, errores = _abrir(navegador, tmp_path, html_de(datos([finding()])))
    assert not errores
    assert pg.evaluate("document.querySelector('.wrap').firstElementChild.id") == "howto"
    assert pg.evaluate("document.querySelector('#howto').getAttribute('aria-labelledby')") == "howTitle"
    assert pg.evaluate("document.querySelector('#howto > details').open") is True
    assert pg.locator("#howto article.term").count() == 4
    assert pg.locator("#howto details.fold").count() == 8 and pg.locator("#howto details.fold[open]").count() == 0
    assert pg.locator("#howto article.term").first.is_visible()


def test_plegar_y_desplegar_se_conserva_al_cambiar_de_idioma(navegador, tmp_path: Path):
    pg, _ = _abrir(navegador, tmp_path, html_de(datos([finding()])))
    pg.click("[data-lang=es]")
    assert pg.inner_text("#howTitle") == "Cómo leer este reporte"
    pg.locator("#howto details.fold >> nth=0").evaluate("d => d.open = true")
    pg.click("[data-lang=en]")
    assert pg.inner_text("#howTitle") == "How to read this report"
    assert pg.locator("#howto details.fold[open]").count() == 1
    pg.locator("#howto > details").evaluate("d => d.open = false")
    pg.click("[data-lang=es]")
    assert pg.evaluate("document.querySelector('#howto > details').open") is False


def test_beforeprint_abre_todo_y_afterprint_restaura_aunque_beforeprint_se_repita(navegador, tmp_path: Path):
    pg, _ = _abrir(navegador, tmp_path, html_de(datos([finding()])))
    pg.locator("#howto details.fold >> nth=0").evaluate("d => d.open = true")
    pg.evaluate("window.dispatchEvent(new Event('beforeprint')); window.dispatchEvent(new Event('beforeprint'))")
    assert pg.locator("#howto details[open]").count() == 1 + 8  # la sección y los 8 plegados
    pg.evaluate("window.dispatchEvent(new Event('afterprint'))")
    assert pg.locator("#howto > details[open]").count() == 1
    assert pg.locator("#howto details.fold[open]").count() == 1  # solo el que la persona había abierto


def test_sin_glosario_la_seccion_queda_oculta_y_sin_aria(navegador, tmp_path: Path):
    html = html_de(datos([finding()]))
    cargado = json.loads(BLOQUE.search(html).group(1))
    del cargado["glossary"]
    sin = re.sub(r'(<script type="application/json" id="data">).*?(</script>)', lambda m: m.group(1) + json.dumps(cargado) + m.group(2), html, flags=re.DOTALL)
    pg, errores = _abrir(navegador, tmp_path, sin)
    assert not errores
    assert pg.evaluate("document.querySelector('#howto').hidden") is True
    assert pg.evaluate("document.querySelector('#howto').hasAttribute('aria-labelledby')") is False
