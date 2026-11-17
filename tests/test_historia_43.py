"""Historia 43: los filtros de nivel dicen cuál está activo y qué muestran.

Las fichas «Caminos / Comprobado / Potencial / Hipótesis» del reporte HTML: la activa lleva tinte, borde de su color y una marca de
forma (✓); la apagada, borde discontinuo y ○, sin tachar; «Caminos» es un total, no un botón; y una línea dice qué se muestra.

Sin navegador se prueba el código de la plantilla; con Playwright (si está instalado) se prueba también lo que se ve.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from agentreach.contracts import Nivel, Plataforma
from test_reporte_html import datos, finding, html_de

pytestmark = pytest.mark.sin_tope_por_nombre

RAIZ = Path(__file__).resolve().parent.parent
PLANTILLA = (RAIZ / "src" / "agentreach" / "reporting" / "plantilla_reporte.html").read_text(encoding="utf-8")
COPIA = (RAIZ / "docs" / "reporte-html" / "plantilla.html").read_text(encoding="utf-8")


def test_los_textos_nuevos_estan_en_los_dos_diccionarios_y_la_linea_es_aria_live():
    for clave in ("showing:(lv)", "allLevels:'", "lastLevel:'"):
        assert PLANTILLA.count(clave) == 2, clave  # uno en inglés y otro en español
    assert "showingNone" not in PLANTILLA  # el último nivel no se puede apagar: nunca queda «ninguno»
    assert 'id="showing" aria-live="polite"' in PLANTILLA


def test_las_fichas_ya_no_se_tachan_y_el_total_no_es_un_boton():
    css = PLANTILLA[: PLANTILLA.index("</style>")]
    assert not re.search(r"\.kpi[^{]*\{[^}]*line-through", css)
    assert '<div class="kpi total">' in PLANTILLA and "kpi glass total" not in PLANTILLA


def test_la_marca_de_estado_no_depende_solo_del_color():
    css = PLANTILLA[: PLANTILLA.index("</style>")]
    assert re.search(r'\.kpi\[aria-pressed="true"\]::after\{[^}]*✓', css)
    assert re.search(r'\.kpi\[aria-pressed="false"\]::after\{[^}]*○', css)
    assert re.search(r'\.kpi\[aria-pressed="false"\]\{[^}]*dashed', css)


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


def _abrir(navegador, tmp_path: Path, tema: str = "dark", idioma: str = "es"):
    hallazgos = [
        finding("a.env"), finding("b.env"), finding("c.env"),
        finding("d.env", nivel=Nivel.HIPOTESIS),
        finding("o.env", plataforma=Plataforma.OPENCODE),
    ]
    archivo = tmp_path / "r.html"
    archivo.write_text(html_de(datos(hallazgos)), encoding="utf-8")
    pg = navegador.new_context(viewport={"width": 1280, "height": 900}).new_page()
    errores: list[str] = []
    pg.on("pageerror", lambda e: errores.append(str(e)))
    pg.goto(archivo.as_uri())
    pg.wait_for_timeout(250)
    pg.click(f"[data-lang={idioma}]")
    pg.click(f"[data-theme={tema}]")
    pg.wait_for_timeout(100)
    return pg, errores


_ESTADO = """el => ({
  marca: getComputedStyle(el, '::after').content,
  borde: getComputedStyle(el).borderTopStyle,
  tachado: getComputedStyle(el.querySelector('.big')).textDecorationLine,
  pulsado: el.getAttribute('aria-pressed'),
})"""


@pytest.mark.parametrize("tema", ["dark", "light"])
def test_ficha_activa_y_apagada_se_distinguen_por_forma_y_sin_tachar(navegador, tmp_path, tema):
    pg, errores = _abrir(navegador, tmp_path, tema)
    assert not errores
    fichas = pg.locator("#kpis button.kpi")
    assert fichas.count() >= 2
    activa = fichas.nth(0).evaluate(_ESTADO)
    assert activa["pulsado"] == "true" and "✓" in activa["marca"] and activa["tachado"] == "none"
    fichas.nth(0).click()
    apagada = pg.locator("#kpis button.kpi").nth(0).evaluate(_ESTADO)
    assert apagada["pulsado"] == "false" and "○" in apagada["marca"]
    assert apagada["borde"] == "dashed" and apagada["borde"] != activa["borde"]
    assert apagada["tachado"] == "none"  # antes se tachaba y parecía un dato borrado


def test_el_total_no_es_un_boton_ni_tiene_borde(navegador, tmp_path):
    pg, _ = _abrir(navegador, tmp_path)
    total = pg.locator("#kpis .kpi.total")
    assert total.evaluate("el => el.tagName") == "DIV"
    assert total.evaluate("el => getComputedStyle(el).borderTopColor") == "rgba(0, 0, 0, 0)"
    assert total.evaluate("el => getComputedStyle(el).cursor") == "default"


@pytest.mark.parametrize(("idioma", "inicio", "todos", "aviso"), [
    ("es", "Niveles visibles:", "todos los niveles", "Siempre queda un nivel activo"),
    ("en", "Levels shown:", "all levels", "One level always stays on"),
])
def test_la_linea_dice_que_niveles_se_ven_y_el_ultimo_no_se_apaga_y_lo_dice(navegador, tmp_path, idioma, inicio, todos, aviso):
    pg, _ = _abrir(navegador, tmp_path, idioma=idioma)
    texto = pg.inner_text("#showing")
    assert texto.startswith(inicio) and todos in texto
    total = pg.locator("#kpis button.kpi").count()
    for i in range(total - 1):  # se apagan todos menos el último
        pg.locator("#kpis button.kpi").nth(i).click()
    parcial = pg.inner_text("#showing")
    assert parcial.startswith(inicio) and todos not in parcial
    ultima = pg.locator("#kpis button.kpi[aria-pressed=true]")
    assert ultima.count() == 1 and ultima.get_attribute("aria-disabled") == "true" and ultima.get_attribute("title") == aviso
    ultima.click(force=True)  # no se apaga y la ficha sigue activa (Playwright trata aria-disabled como no habilitado)
    assert pg.locator("#kpis button.kpi[aria-pressed=true]").count() == 1


def test_el_foco_se_conserva_al_pulsar_una_ficha_con_el_teclado(navegador, tmp_path):
    pg, _ = _abrir(navegador, tmp_path)
    ficha = pg.locator("#kpis button.kpi").nth(1)
    ficha.focus()
    pg.keyboard.press("Enter")
    assert pg.evaluate("document.activeElement.dataset.lv") == ficha.get_attribute("data-lv")
    assert pg.locator("#kpis button.kpi").nth(1).get_attribute("aria-pressed") == "false"


def test_las_fichas_no_se_desbordan_en_un_movil(navegador, tmp_path):
    pg, _ = _abrir(navegador, tmp_path)
    pg.set_viewport_size({"width": 360, "height": 800})
    pg.wait_for_timeout(100)
    assert pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
    assert pg.locator("#kpis button.kpi").evaluate_all("els => els.every(e => e.scrollWidth <= e.clientWidth + 1)")


def _luminancia(rgb: str) -> float:
    canales = [int(float(v)) for v in re.findall(r"[\d.]+", rgb)[:3]]
    lin = [(c / 255) / 12.92 if c / 255 <= 0.03928 else (((c / 255) + 0.055) / 1.055) ** 2.4 for c in canales]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _contraste(a: str, b: str) -> float:
    la, lb = sorted((_luminancia(a), _luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


@pytest.mark.parametrize("tema", ["dark", "light"])
@pytest.mark.parametrize(("grupo", "atributo"), [
    ("#gLang button", "aria-pressed"), ("#gTheme button", "aria-pressed"),
    ("#gView button", "aria-pressed"), (".tab", "aria-selected"),
])
def test_los_demas_grupos_distinguen_lo_seleccionado_con_contraste(navegador, tmp_path, tema, grupo, atributo):
    """Seleccionado: fondo distinto del de los demás y texto legible (3:1) sobre ese fondo, en tema claro y oscuro."""
    pg, _ = _abrir(navegador, tmp_path, tema)
    botones = pg.locator(grupo)
    assert botones.count() >= 2
    estilos = botones.evaluate_all(
        f"els => els.map(e => ({{sel: e.getAttribute('{atributo}') === 'true', fondo: getComputedStyle(e).backgroundColor, texto: getComputedStyle(e).color}}))"
    )
    sel = [e for e in estilos if e["sel"]]
    resto = [e for e in estilos if not e["sel"]]
    assert len(sel) == 1 and resto
    assert all(sel[0]["fondo"] != r["fondo"] for r in resto), (grupo, tema)
    assert _contraste(sel[0]["texto"], sel[0]["fondo"]) >= 3, (grupo, tema)
