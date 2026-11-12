"""El reporte HTML cumple el contraste (4,5 texto normal; 3 texto grande y bordes de controles) medido sobre píxeles reales.

Se omite si no hay ``playwright`` o un navegador. Para correrla: ``uv run --with playwright pytest tests/test_contraste_html.py``
(Edge viene con Windows; si no, ``playwright install chromium``).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
sync_api = pytest.importorskip("playwright.sync_api")
from contraste_html import datos_sinteticos, medir_estado, pagina

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

PANTALLAS = (("escritorio", 1440, 900), ("movil", 390, 844))
TEMAS = ("dark", "light")
# (conjunto de datos, vista): con 20 hallazgos el grafo es interactivo; con 100 el diagrama es el resumen estático
ESTADOS = (("n20", "graph"), ("n20", "list"), ("n20", "table"), ("n20", "print"), ("n100", "graph"), ("n100", "list"))


@pytest.fixture(scope="module")
def navegador():
    with sync_api.sync_playwright() as p:
        for canal in ("msedge", None):
            try:
                nav = p.chromium.launch(channel=canal, headless=True) if canal else p.chromium.launch(headless=True)
                break
            except Exception:  # noqa: BLE001 - sin ese navegador, se prueba el siguiente
                nav = None
        if nav is None:
            pytest.skip("no hay un navegador (Edge o Chromium) para medir")
        yield nav
        nav.close()


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("pantalla", PANTALLAS, ids=[p[0] for p in PANTALLAS])
def test_contraste_sobre_pixeles_reales(navegador, tmp_path: Path, tema, pantalla):
    nombre, ancho, alto = pantalla
    archivos = {}
    for clave, n in (("n20", 20), ("n100", 100)):
        archivos[clave] = tmp_path / f"{clave}.html"
        archivos[clave].write_text(pagina(datos_sinteticos(n)), encoding="utf-8")
    ayudante = navegador.new_context().new_page()
    fallos, medidas = [], 0
    for clave, vista in ESTADOS:
        ctx = navegador.new_context(viewport={"width": ancho, "height": alto}, color_scheme=tema)
        pg = ctx.new_page()
        pg.goto(archivos[clave].as_uri())
        pg.wait_for_timeout(250)
        pg.evaluate(f"window.__ar.setTheme('{tema}')")
        pg.evaluate(f"window.__ar.setView('{vista}')")
        pg.wait_for_timeout(150)
        f, m = medir_estado(pg, ayudante, f"{nombre}/{tema}/{clave}/{vista}")
        fallos += f
        medidas += m
        ctx.close()
    assert medidas > 100, f"se midieron muy pocas cosas ({medidas})"
    assert not fallos, "\n".join(f"{x['estado']} {x['clase']} {x['min']}<{x['exigido']} «{x['texto']}» {x['etiqueta']}" for x in fallos[:40]) + f"\n({len(fallos)} fallos de {medidas} medidas)"
