"""Historia 42: «Cómo leer este reporte», en corto.

A la vista solo la frase corta de cada uno de los 4 términos (los tres niveles y el camino de alcance) y la introducción, con un
máximo de 80 palabras; el detalle va plegado en «Ver más» con el texto del catálogo sin cambios. El catálogo y los datos no se tocan.

Sin navegador se prueba el contenido y el código de la plantilla; con Playwright (si está instalado) se prueba también lo que se ve.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from test_reporte_html import BLOQUE, datos, finding, html_de

pytestmark = pytest.mark.sin_tope_por_nombre

RAIZ = Path(__file__).resolve().parent.parent
PLANTILLA = (RAIZ / "src" / "agentreach" / "reporting" / "plantilla_reporte.html").read_text(encoding="utf-8")
COPIA = (RAIZ / "docs" / "reporte-html" / "plantilla.html").read_text(encoding="utf-8")
MAX_PALABRAS = 80


def _how_open() -> list[str]:
    return re.findall(r"'([a-z_]+)'", re.search(r"HOW_OPEN=\[(.*?)\]", PLANTILLA).group(1))  # type: ignore[union-attr]


def _glosario() -> dict:
    return json.loads(BLOQUE.search(html_de(datos([finding()]))).group(1))["glossary"]  # type: ignore[union-attr]


def _palabras(texto: str) -> int:
    return len(texto.split())


@pytest.mark.parametrize("idioma", ["es", "en"])
def test_a_la_vista_hay_a_lo_sumo_80_palabras(idioma):
    """La introducción más la frase corta de los 4 términos: lo único visible por defecto."""
    lead = re.search(rf"\b{idioma}:\{{skip:[^\n]*?howLead:'([^']*)'", PLANTILLA).group(1)  # type: ignore[union-attr]
    terminos = {t["id"]: t for t in _glosario()["terms"]}
    ids = _how_open()
    assert len(ids) == 4
    total = _palabras(lead) + sum(_palabras(terminos[i]["line"][idioma]) for i in ids)
    assert total <= MAX_PALABRAS, f"{total} palabras a la vista en «{idioma}»"


def test_el_detalle_sigue_en_los_datos_sin_cambios():
    """Nada se pierde: «Qué es», «Qué significa» y «Qué puedes hacer» de los 4 términos siguen en el glosario, en ES y EN."""
    terminos = {t["id"]: t for t in _glosario()["terms"]}
    for i in _how_open():
        for campo in ("line", "what_is", "means", "to_do"):
            for idioma in ("es", "en"):
                assert terminos[i][campo][idioma].strip(), (i, campo, idioma)


def test_la_etiqueta_ver_mas_esta_en_los_dos_diccionarios_de_la_plantilla():
    assert "howMore:'See more'" in PLANTILLA and "howMore:'Ver más'" in PLANTILLA


def test_cada_termino_a_la_vista_lleva_un_ver_mas_nativo_y_conserva_su_id():
    codigo = PLANTILLA[PLANTILLA.index("function renderHowto"):PLANTILLA.index("function renderLimits")]
    assert "<details class=\"more\"" in codigo and "<summary>'+esc(T_.howMore)+'<span class=\"sr\">" in codigo
    assert "id=\"term-'+x.id+'\"" in codigo  # los enlaces de la Historia 36 apuntarán a estos ids
    assert "openMore" in codigo  # un «Ver más» abierto sobrevive al cambio de idioma


def test_en_papel_solo_se_abre_la_seccion_y_no_el_detalle():
    antes = PLANTILLA[PLANTILLA.index("window.addEventListener('beforeprint'"):PLANTILLA.index("window.addEventListener('afterprint'")]
    assert "querySelectorAll('#howDetails')" in antes and "#howto details" not in antes


def test_la_copia_de_la_plantilla_es_identica():
    assert PLANTILLA == COPIA


# ---- con navegador (solo si Playwright y un navegador están disponibles) ----------------------------------------------------

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


def _abrir(navegador, tmp_path: Path):
    archivo = tmp_path / "r.html"
    archivo.write_text(html_de(datos([finding()])), encoding="utf-8")
    pg = navegador.new_context(viewport={"width": 1280, "height": 900}).new_page()
    errores: list[str] = []
    pg.on("pageerror", lambda e: errores.append(str(e)))
    pg.goto(archivo.as_uri())
    pg.wait_for_timeout(250)
    return pg, errores


@pytest.mark.parametrize("idioma", ["es", "en"])
def test_en_el_navegador_se_ven_pocas_palabras_y_el_ver_mas_despliega_el_detalle(navegador, tmp_path, idioma):
    pg, errores = _abrir(navegador, tmp_path)
    pg.click(f"[data-lang={idioma}]")
    assert not errores
    # texto de ayuda a la vista: lo que queda al quitar los controles «Ver más» (y su detalle), los plegados y los encabezados
    visible = pg.evaluate(
        """() => { const c = document.querySelector('#howDetails').cloneNode(true);
        c.querySelectorAll('details.more, details.fold, h3.other, summary').forEach(n => n.remove());
        return c.textContent; }"""
    )
    assert _palabras(visible) <= MAX_PALABRAS
    assert pg.locator("#howto details.more").count() == 4 and pg.locator("#howto details.more[open]").count() == 0
    etiqueta = {"es": "Ver más", "en": "See more"}[idioma]
    assert pg.locator("#howto details.more >> nth=0 >> summary").inner_text().startswith(etiqueta)  # la etiqueta sigue al idioma
    primero = pg.locator("#howto details.more >> nth=0")
    primero.locator("summary").click()
    assert primero.evaluate("d => d.open") is True and primero.locator("dt").count() == 3


def test_ver_mas_abierto_se_conserva_al_cambiar_de_idioma_y_en_papel_no_se_abre(navegador, tmp_path):
    pg, _ = _abrir(navegador, tmp_path)
    pg.locator("#howto details.more >> nth=1").evaluate("d => d.open = true")
    pg.click("[data-lang=es]")
    assert pg.locator("#howto details.more[open]").count() == 1
    pg.evaluate("window.dispatchEvent(new Event('beforeprint'))")
    assert pg.locator("#howto details.more[open]").count() == 1  # solo el que la persona abrió
    assert pg.locator("#howto details.fold[open]").count() == 0
    pg.evaluate("window.dispatchEvent(new Event('afterprint'))")
    assert pg.locator("#howto details.more[open]").count() == 1 and pg.locator("#howto > details[open]").count() == 1  # se restaura lo de la persona
    pg.click("[data-lang=en]")  # y una segunda impresión, tras volver a pintar la sección, sigue funcionando
    pg.evaluate("window.dispatchEvent(new Event('beforeprint'))")
    assert pg.locator("#howto > details[open]").count() == 1
    pg.evaluate("window.dispatchEvent(new Event('afterprint'))")


@pytest.mark.parametrize("idioma", ["es", "en"])
def test_cada_frase_corta_lleva_su_etiqueta_antes_de_los_dos_puntos(idioma):
    """La vista corta pone en negrita lo que va antes de los dos puntos (p. ej. «Comprobado:»); si una frase no lo trae, antepone el nombre."""
    terminos = {t["id"]: t for t in _glosario()["terms"]}
    for i in _how_open():
        linea = terminos[i]["line"][idioma]
        etiqueta, _, resto = linea.partition(":")
        assert resto and 0 < len(etiqueta) <= 30, (i, idioma, linea)
