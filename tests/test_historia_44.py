"""Historia 44: aviso cuando la carpeta revisada contiene varios proyectos (función pura, terminal, HTML y código de salida)."""

from __future__ import annotations

import dataclasses
import io
import os
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from agentreach import cli
from agentreach.collectors.proyectos_anidados import (
    UMBRAL_PROYECTOS_ANIDADOS,
    contar_proyectos_anidados,
)
from test_reporte_html import ESQUEMA, _validar, datos, finding, html_de, json_de

pytestmark = pytest.mark.sin_tope_por_nombre

AHORA = datetime(2026, 11, 12, 10, 0, 0)
ES = "carpetas que parecen proyectos distintos"
EN = "folders that look like separate projects"


def _contar(raiz: Path, *relativas: str) -> int:
    archivos = [SimpleNamespace(ruta=str(raiz / r)) for r in relativas]
    return contar_proyectos_anidados(archivos, str(raiz))


# ---- función pura (no recorre ni lee contenido; los archivos no existen, solo se resuelve la raíz) ----------------------------------------------------------------------


def test_umbral_es_dos():
    assert UMBRAL_PROYECTOS_ANIDADOS == 2


def test_varios_proyectos_cuenta_cada_carpeta_interna(tmp_path):
    assert _contar(tmp_path, "a/.git/config", "b/.claude/settings.json", "c/.claude/settings.local.json",
                   "d/.opencode/opencode.json", "e/CLAUDE.md", "f/opencode.json", "g/opencode.jsonc") == 7


def test_la_raiz_nunca_cuenta(tmp_path):
    assert _contar(tmp_path, ".git/config", ".claude/settings.json", "CLAUDE.md", "opencode.json") == 0


def test_una_carpeta_con_varias_senales_cuenta_una_vez(tmp_path):
    assert _contar(tmp_path, "a/.git/config", "a/CLAUDE.md", "a/.claude/settings.json") == 1


def test_manifiestos_no_son_senal_monorepo(tmp_path):
    archivos = [".git/config"] + [f"p{i}/package.json" for i in range(10)] + ["q/pyproject.toml"]
    assert _contar(tmp_path, *archivos) == 0


def test_dentro_de_herramientas_no_cuenta(tmp_path):
    assert _contar(tmp_path, "node_modules/x/.git/config", ".claude/algo/CLAUDE.md", ".git/modulos/y/CLAUDE.md",
                   ".opencode/z/opencode.json", "a/node_modules/m/CLAUDE.md") == 0


@pytest.mark.parametrize("carpeta", [".venv", "venv", "vendor", "site-packages", "dist", "target"])
def test_carpetas_de_dependencias_no_cuentan(tmp_path, carpeta):
    assert _contar(tmp_path, f"{carpeta}/lib/x/CLAUDE.md", f"{carpeta}/x/.git/config", f"{carpeta}/o/opencode.json") == 0


def test_dependencias_se_saltan_en_cualquier_nivel_y_sin_mayusculas(tmp_path):
    assert _contar(tmp_path, "packages/x/.venv/lib/CLAUDE.md", "a/.VENV/CLAUDE.md", "b/Vendor/y/.git/config",
                   "c/DIST/opencode.json") == 0


def test_dependencias_no_tapan_proyectos_reales(tmp_path):
    assert _contar(tmp_path, ".venv/lib/x/CLAUDE.md", "a/CLAUDE.md", "b/.git/config", "c/vendor/z/CLAUDE.md") == 2


def test_git_como_archivo_o_config_suelto_no_cuenta(tmp_path):
    assert _contar(tmp_path, "a/.git", "b/config", "c/.claude/otro.json") == 0


def test_rutas_fuera_de_la_raiz_no_cuentan(tmp_path):
    raiz = tmp_path / "uno"
    assert contar_proyectos_anidados([SimpleNamespace(ruta=str(tmp_path / "dos" / "a" / "CLAUDE.md"))], str(raiz)) == 0


@pytest.mark.skipif(os.name != "nt", reason="en Windows las mayúsculas no distinguen")
def test_windows_no_distingue_mayusculas(tmp_path):
    archivos = [SimpleNamespace(ruta=str(tmp_path / "A" / ".GIT" / "CONFIG")), SimpleNamespace(ruta=str(tmp_path / "b" / "claude.md"))]
    assert contar_proyectos_anidados(archivos, str(tmp_path).upper()) == 2


# ---- terminal y HTML ----------------------------------------------------------------------------------------------------------


def _carpeta(tmp_path: Path, *archivos: str, pesado: str | None = None) -> dict:
    casa, proyecto = tmp_path / "casa", tmp_path / "proyecto"
    casa.mkdir(parents=True)
    proyecto.mkdir(parents=True)
    for r in archivos:
        destino = proyecto / r
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text("{}" if r.endswith(".json") else "x", encoding="utf-8")
    if pesado:
        destino = proyecto / pesado
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(b"0" * (1024 * 1024 + 1))
    return {"casa": casa, "proyecto": proyecto, "tmp": tmp_path}


def _terminal(m: dict, *extra: str) -> tuple[int, str]:
    salida = io.StringIO()
    anterior = sys.stdout
    sys.stdout = salida
    try:
        codigo = cli.main([str(m["proyecto"]), "--home", str(m["casa"]), "--no-banner", *extra], ahora=lambda: AHORA)
    finally:
        sys.stdout = anterior
    return codigo, salida.getvalue()


def _html(m: dict, nombre: str = "r.html") -> tuple[int, dict]:
    destino = m["tmp"] / nombre
    codigo = cli.main([str(m["proyecto"]), "--home", str(m["casa"]), "--formato", "html", "--salida", str(destino)], ahora=lambda: AHORA)
    datos = json_de(destino.read_text(encoding="utf-8"))
    _validar(datos, ESQUEMA)
    return codigo, datos


TRES = ("clienteuno/.git/config", "clientedos/.claude/settings.json", "clientetres/CLAUDE.md")


def test_tres_proyectos_avisan_en_terminal_y_html_sin_nombres(tmp_path):
    m = _carpeta(tmp_path, *TRES)
    codigo_t, texto = _terminal(m)
    plano = " ".join(texto.split())
    assert f"contiene 3 {ES}" in plano
    assert plano.index(ES) < plano.index("RESUMEN")  # arriba, antes de los hallazgos
    for nombre in ("clienteuno", "clientedos", "clientetres"):
        assert nombre not in texto
    codigo_h, datos = _html(m)
    assert datos["wide_folder"] == 3
    assert codigo_h == codigo_t
    assert "clienteuno" not in str(datos)


def test_ingles(tmp_path):
    m = _carpeta(tmp_path, *TRES)
    _, texto = _terminal(m, "--idioma", "en")
    assert f"contains 3 {EN}" in " ".join(texto.split())


@pytest.mark.parametrize("archivos", [
    (".git/config",),
    (".git/config", "uno/CLAUDE.md"),
    (".git/config", *[f"p{i}/package.json" for i in range(10)]),
    ("node_modules/x/.git/config", ".claude/algo/CLAUDE.md"),
])
def test_sin_aviso(tmp_path, archivos):
    m = _carpeta(tmp_path, *archivos)
    _, texto = _terminal(m)
    assert ES not in " ".join(texto.split())
    _, datos = _html(m)
    assert "wide_folder" not in datos


def test_archivo_grande_no_cuenta(tmp_path):
    m = _carpeta(tmp_path, "a/CLAUDE.md", pesado="b/CLAUDE.md")
    _, datos = _html(m)
    assert "wide_folder" not in datos


def test_el_aviso_no_cambia_conteos_ni_codigo_de_salida(tmp_path, monkeypatch):
    m = _carpeta(tmp_path, ".env", *TRES)
    cod_con, con = _html(m)
    assert con["wide_folder"] == 3
    monkeypatch.setattr("agentreach.app.auditar.contar_proyectos_anidados", lambda *_: 0)
    cod_sin, sin = _html(m, "r2.html")
    assert "wide_folder" not in sin
    con.pop("wide_folder")
    assert cod_con == cod_sin
    assert {**con, "generated_at": 0} == {**sin, "generated_at": 0}  # niveles, conteos y orden idénticos


@pytest.mark.parametrize("ancho", [20, 40, 59])
def test_terminal_estrecha_parte_por_palabras(tmp_path, ancho):
    m = _carpeta(tmp_path, *TRES)
    _, texto = _terminal(m, "--ancho", str(ancho))
    assert "distintos." in texto.split() and "proyectos" in texto.split()  # ninguna palabra cortada
    assert all(len(ln) <= max(ancho, 60) or " " not in ln.strip() for ln in texto.splitlines())


# ---- umbral de punta a punta ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize(("archivos", "n"), [
    (("uno/CLAUDE.md",), 0),
    (("uno/CLAUDE.md", "dos/.git/config"), 2),
    ((".git/config", "uno/CLAUDE.md"), 0),
    ((".git/config", "uno/CLAUDE.md", "dos/opencode.json"), 2),
])
def test_umbral_de_punta_a_punta(tmp_path, archivos, n):
    m = _carpeta(tmp_path, *archivos)
    _, texto = _terminal(m)
    plano = " ".join(texto.split())
    _, d = _html(m)
    if n:
        assert f"contiene {n} {ES}" in plano
        assert d["wide_folder"] == n
    else:
        assert ES not in plano
        assert "wide_folder" not in d


# ---- en el navegador (se omite si no hay Playwright o navegador) ----------------------------------------------------------


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


def _abrir(navegador, tmp_path: Path, anidados: int):
    d = dataclasses.replace(datos([finding("a.env")]), proyectos_anidados=anidados)
    archivo = tmp_path / "w.html"
    archivo.write_text(html_de(d), encoding="utf-8")
    pg = navegador.new_context(viewport={"width": 1280, "height": 900}).new_page()
    errores: list[str] = []
    pg.on("pageerror", lambda e: errores.append(str(e)))
    pg.goto(archivo.as_uri())
    pg.wait_for_timeout(250)
    return pg, errores


def test_navegador_con_wide_folder_3_el_aviso_se_ve_en_los_dos_idiomas(navegador, tmp_path):
    pg, errores = _abrir(navegador, tmp_path, 3)
    for idioma, frase in (("es", ES), ("en", EN)):
        pg.click(f"[data-lang={idioma}]")
        pg.wait_for_timeout(100)
        assert pg.is_visible("#wide")
        texto = pg.inner_text("#wide")
        assert "3" in texto and frase in texto
        assert "clienteuno" not in texto
    assert not errores


@pytest.mark.parametrize("anidados", [0, 1])
def test_navegador_sin_campo_o_con_dato_invalido_el_aviso_sigue_oculto(navegador, tmp_path, anidados):
    pg, errores = _abrir(navegador, tmp_path, anidados)  # 0: sin campo; 1: wide_folder=1, inválido
    assert not pg.is_visible("#wide")
    pg.click("[data-lang=en]")
    assert not pg.is_visible("#wide")
    assert not errores
