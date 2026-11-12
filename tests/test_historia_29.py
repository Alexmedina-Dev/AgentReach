"""Historia 29: el logo se lee en cualquier fondo de terminal (spec-historia-29-colores-legibles-en-cualquier-terminal)."""

from __future__ import annotations

import colorsys
import io
import os
import re
import sys

import pytest

from agentreach import cli
from agentreach.reporting.formato import (
    _PALETA,
    GRIS_UNIVERSAL,
    REACH_UNIVERSAL,
    Color,
    _luminancia,
    colores_de_marca,
    contraste,
    pintar,
    resolver_tema,
    resolver_tema_marca,
)
from agentreach.reporting.marca import Tamano, banner

ESC = chr(27)
SGR24 = re.compile(ESC + r"\[38;2;(\d+);(\d+);(\d+)m")
BLANCO, NEGRO = (255, 255, 255), (0, 0, 0)

FONDOS_REALES = ["FFFFFF", "F2F2F2", "F6F8FA", "FDF6E3", "FBF1C7", "002B36", "000000", "0C0C0C", "282A36", "282C34",
                 "1A1B26", "808080", "000080"]


def rgb(h: str) -> tuple[int, int, int]:
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


class Tty(io.StringIO):
    encoding = "utf-8"

    def isatty(self) -> bool:
        return True


@pytest.fixture(autouse=True)
def entorno_limpio(monkeypatch):
    for nombre in ("NO_COLOR", "TERM", "COLORTERM", "WT_SESSION", "TERM_PROGRAM", "COLORFGBG", "AGENTREACH_IDIOMA",
                   "AGENTREACH_TEMA", "AGENTREACH_TONO", "AGENTREACH_NO_BANNER", "AGENTREACH_ASCII"):
        monkeypatch.delenv(nombre, raising=False)
    monkeypatch.setattr(cli, "activar_vt", lambda *a: True)
    monkeypatch.setattr(cli, "idioma_regional", lambda: "es")
    monkeypatch.setattr(cli.shutil, "get_terminal_size", lambda fallback=(80, 24): os.terminal_size((80, 24)))


def _saturacion(h: str) -> float:
    r, g, b = (v / 255 for v in rgb(h))
    return colorsys.rgb_to_hls(r, g, b)[2]


def _se_distinguen(agent: str, reach: str) -> bool:
    """REACH es de color (saturación HLS >= 0,5) y AGENT casi neutro (<= 0,35), o chocan entre sí (>= 1,5:1)."""
    return (_saturacion(reach) >= 0.5 and _saturacion(agent) <= 0.35) or contraste(rgb(agent), rgb(reach)) >= 1.5


def _banner(salida: str) -> str:
    return chr(10).join(salida.splitlines()[:8])


def correr(monkeypatch, argv: list[str]) -> str:
    salida = Tty()
    monkeypatch.setattr(sys, "stdout", salida)
    cli.main(argv)
    return salida.getvalue()


@pytest.fixture
def proyecto(tmp_path):
    (tmp_path / ".env").write_text("STRIPE_SECRET_KEY=sk_live_algo_largo_123\n", encoding="utf-8")
    return tmp_path


def ayuda(monkeypatch, extra: list[str] | None = None) -> str:
    salida = Tty()
    monkeypatch.setattr(sys, "stdout", salida)
    with pytest.raises(SystemExit):
        cli.main([*(extra or []), "--help"])
    return salida.getvalue()


def colores(texto: str) -> set[tuple[int, int, int]]:
    return {tuple(int(n) for n in m.groups()) for m in SGR24.finditer(texto)}


# ---- función pura -----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("fondo", FONDOS_REALES)
def test_reach_llega_a_3_a_1_y_agent_se_distingue_en_los_fondos_reales(fondo):
    agent, reach = colores_de_marca(rgb(fondo))
    assert reach is not None, fondo
    assert contraste(rgb(reach), rgb(fondo)) >= 3, (fondo, reach)
    assert contraste(rgb(agent), rgb(fondo)) >= 3, (fondo, agent)  # AGENT es el de más contraste de los dos
    assert _se_distinguen(agent, reach), (fondo, agent, reach)


def test_valores_de_referencia():
    assert colores_de_marca(BLANCO)[0] == "0B1114" and contraste(rgb("0B1114"), BLANCO) > 19
    reach_blanco = colores_de_marca(BLANCO)[1]
    assert all(abs(a - b) <= 8 for a, b in zip(rgb(reach_blanco), rgb("08A585"), strict=True))  # ≈ #08A585
    reach_gris = colores_de_marca((128, 128, 128))[1]
    assert all(abs(a - b) <= 16 for a, b in zip(rgb(reach_gris), rgb("6DF8DC"), strict=True))  # ≈ #6DF8DC
    assert colores_de_marca(NEGRO) == ("EAF4F2", "3DF5D0")  # fondo oscuro: sin cambios
    assert colores_de_marca(rgb("0C0C0C")) == ("EAF4F2", "3DF5D0")


def test_barrido_de_una_malla_rgb():
    malla = [(r, g, b) for r in range(0, 256, 17) for g in range(0, 256, 17) for b in range(0, 256, 17)]  # 16^3 = 4096
    assert len(set(malla)) >= 4000
    desconocidos = 0
    for fondo in set(malla):
        agent, reach = colores_de_marca(fondo)
        assert agent in ("EAF4F2", "0B1114")
        if reach is None:  # cae al caso «desconocido»
            desconocidos += 1
            assert 0.1 < _luminancia(fondo) < 0.5, fondo  # solo los fondos de luminancia media no admiten el menta a 3:1
            continue
        assert contraste(rgb(reach), fondo) >= 3, (fondo, reach)
        assert contraste(rgb(agent), fondo) >= 3, (fondo, agent)
        r, g, b = rgb(reach)
        assert g >= r and g >= b, (fondo, reach)  # matiz menta: domina el verde
        assert _se_distinguen(agent, reach), (fondo, agent, reach)
    assert desconocidos < len(set(malla)) / 2  # la mayoría de los fondos sí llega


# ---- tema de tres estados ---------------------------------------------------------------------------------------------


def test_el_tema_tiene_tres_estados_y_la_prioridad_del_spec():
    assert resolver_tema_marca(None, {}) is None
    assert resolver_tema_marca("claro", {"COLORFGBG": "15;0"}) is True
    assert resolver_tema_marca("oscuro", {"AGENTREACH_TEMA": "claro"}) is False
    assert resolver_tema_marca(None, {"AGENTREACH_TEMA": "claro", "COLORFGBG": "15;0"}) is True
    assert resolver_tema_marca("auto", {"AGENTREACH_TEMA": "claro", "COLORFGBG": "15;0"}) is False
    assert resolver_tema_marca(None, {"COLORFGBG": "0;15"}) is True
    assert resolver_tema_marca(None, {"COLORFGBG": "15;0"}) is False
    assert resolver_tema_marca(None, {"COLORFGBG": "raro"}) is None
    assert resolver_tema(None, {}) is False  # el contrato bool se conserva


# ---- logo sin tema (24 bits y 16 colores) ------------------------------------------------------------------------------


@pytest.mark.parametrize("tamano", list(Tamano))
@pytest.mark.parametrize("ascii_", [False, True])
def test_sin_tema_en_24_bits_agent_no_tiene_color_y_reach_es_el_universal(tamano, ascii_):
    lineas = banner(tamano, "1.0", ascii_=ascii_, color=Color.DE_24_BITS, claro=None, ancho=80)
    texto = "\n".join(lineas)
    reach = rgb(REACH_UNIVERSAL)
    assert reach in colores(texto)
    for c in colores(texto):
        if c != reach:  # solo quedan los colores secundarios (versión, lema), que no son del logo
            assert c not in (rgb("EAF4F2"), rgb("3DF5D0"))
    for fondo in (BLANCO, NEGRO):
        assert contraste(reach, fondo) >= 4.5


@pytest.mark.parametrize("tamano", list(Tamano))
def test_sin_tema_en_16_colores_reach_usa_el_cian_normal_y_nunca_97_ni_96(tamano):
    texto = "\n".join(banner(tamano, "1.0", color=Color.DE_16, claro=None, ancho=80))
    assert ESC + "[36m" in texto
    assert ESC + "[97m" not in texto and ESC + "[96m" not in texto


def test_pintar_con_tema_desconocido_deja_agent_sin_secuencia():
    assert pintar("AGENT", "marca_agent", Color.DE_24_BITS, None) == "AGENT"
    assert pintar("AGENT", "marca_agent", Color.DE_16, None) == "AGENT"
    assert pintar("REACH", "marca_reach", Color.DE_16, None) == f"{ESC}[36mREACH{ESC}[0m"


def test_fondo_oscuro_conocido_no_cambia_los_colores():
    texto = "\n".join(banner(Tamano.GRANDE, "1.0", color=Color.DE_24_BITS, claro=False))
    assert {rgb("EAF4F2"), rgb("3DF5D0")} <= colores(texto)


def test_fondo_claro_conocido_usa_agent_oscuro_y_reach_de_3_a_1():
    texto = "\n".join(banner(Tamano.MEDIANO, "1.0", color=Color.DE_24_BITS, claro=True))
    cs = colores(texto)
    assert rgb("0B1114") in cs and rgb("EAF4F2") not in cs
    assert rgb(colores_de_marca(BLANCO)[1]) in cs


# ---- cableado en la CLI -----------------------------------------------------------------------------------------------


def test_la_ayuda_sin_tema_detectable_usa_el_color_universal(monkeypatch):
    monkeypatch.setenv("COLORTERM", "truecolor")
    cs = colores(ayuda(monkeypatch))
    assert rgb(REACH_UNIVERSAL) in cs
    assert rgb("EAF4F2") not in cs and rgb("3DF5D0") not in cs


def test_la_variable_y_colorfgbg_siguen_mandando(monkeypatch):
    monkeypatch.setenv("COLORTERM", "truecolor")
    monkeypatch.setenv("COLORFGBG", "0;15")
    assert rgb("0B1114") in colores(ayuda(monkeypatch))
    assert rgb("EAF4F2") in colores(ayuda(monkeypatch, ["--tema", "oscuro"]))


def test_sin_color_no_hay_banner_ni_esc(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    assert ESC not in ayuda(monkeypatch)


# ---- doctor y revisión sin tema, banner sin tema ----------------------------------------------------------------------


@pytest.mark.parametrize("comando", ["doctor", None])
def test_doctor_y_la_revision_sin_tema_usan_el_color_universal(monkeypatch, proyecto, comando):
    argv = [*(["doctor"] if comando else []), str(proyecto)]
    monkeypatch.setenv("COLORTERM", "truecolor")
    salida = correr(monkeypatch, argv)
    marca = _banner(salida)  # el cuerpo usa 3DF5D0 en el nivel «ok»
    assert rgb(REACH_UNIVERSAL) in colores(marca)
    assert rgb("EAF4F2") not in colores(marca) and rgb("3DF5D0") not in colores(marca)
    monkeypatch.delenv("COLORTERM")
    marca = _banner(correr(monkeypatch, argv))
    assert ESC + "[36m" in marca
    assert ESC + "[97m" not in marca and ESC + "[96m" not in marca


def test_la_paleta_de_marca_es_lo_que_da_colores_de_marca():
    for indice, fondo in ((1, BLANCO), (0, NEGRO)):
        agent, reach = colores_de_marca(fondo)
        assert _PALETA["marca_agent"][indice] == agent
        assert _PALETA["marca_reach"][indice] == reach


@pytest.mark.parametrize("tamano", list(Tamano))
def test_version_y_lema_sin_tema_se_leen_en_blanco_y_en_negro(tamano):
    texto = "\n".join(banner(tamano, "1.0", color=Color.DE_24_BITS, claro=None, ancho=80))
    gris = rgb(GRIS_UNIVERSAL)
    assert gris in colores(texto)
    for c in colores(texto):
        assert c == rgb(REACH_UNIVERSAL) or c == gris, c
    assert contraste(gris, BLANCO) >= 4.5 and contraste(gris, NEGRO) >= 4.5
    assert ESC + "[90m" in "\n".join(banner(tamano, "1.0", color=Color.DE_16, claro=None, ancho=80))
