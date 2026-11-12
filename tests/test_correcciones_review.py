"""Correcciones de la revisión independiente de las historias 1 a 3 (A1, A2 y medios).

Las pruebas que miden comportamiento observable están en ``test_comportamiento_lectura_y_permisos.py``.
Las marcadas "GUARDA DE REGRESIÓN" fijan detalles internos (parámetros ``raiz``, ``ruta_real``,
``pasa_por_enlace``, funciones privadas): sirven para que no se pierda la corrección, pero no
demuestran por sí solas el comportamiento.
"""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest

from agentreach.collectors.enlaces import recorrer
from agentreach.contracts import ArchivoNoLegible, FueraDelProyecto, Metadatos, Ruta, limpiar_ruta
from agentreach.contracts.rutas import es_ruta_de_red, tiene_nombre_reservado
from agentreach.infra.fs_solo_lectura import FsSoloLectura

CANARIO = "CANARIO-REVIEW-sk_live_" + "0123456789abcdef"
solo_windows = pytest.mark.skipif(sys.platform != "win32", reason="solo Windows")


def _enlace_de_carpeta(enlace: Path, destino: Path) -> bool:
    try:
        if sys.platform == "win32":
            import _winapi

            _winapi.CreateJunction(str(destino), str(enlace))
        else:
            os.symlink(destino, enlace, target_is_directory=True)
        return True
    except (OSError, NotImplementedError, AttributeError):
        return False


# --- A1: enlace en una carpeta intermedia -------------------------------------------------------


@pytest.fixture
def con_enlace_intermedio(tmp_path: Path):
    proyecto, fuera = tmp_path / "proyecto", tmp_path / "fuera"
    proyecto.mkdir()
    fuera.mkdir()
    (fuera / "secreto.env").write_text(f"K={CANARIO}", encoding="utf-8")
    (proyecto / "normal.txt").write_text("ok", encoding="utf-8")
    if not _enlace_de_carpeta(proyecto / "enl", fuera):
        pytest.skip("el entorno no permite crear enlaces de carpeta")
    return proyecto


# GUARDA DE REGRESIÓN: usa el parámetro raiz.
def test_a1_no_lee_a_traves_de_un_enlace_intermedio_con_raiz(con_enlace_intermedio: Path):
    fs = FsSoloLectura(str(con_enlace_intermedio))
    with pytest.raises(FueraDelProyecto) as info:
        fs.leer_texto(Ruta(str(con_enlace_intermedio / "enl" / "secreto.env")))
    assert CANARIO not in str(info.value)
    assert fs.leer_texto(Ruta(str(con_enlace_intermedio / "normal.txt"))) == "ok"


def test_a1_sin_raiz_tambien_rechaza_el_enlace_intermedio(con_enlace_intermedio: Path):
    with pytest.raises(ArchivoNoLegible) as info:
        FsSoloLectura().leer_texto(Ruta(str(con_enlace_intermedio / "enl" / "secreto.env")))
    assert isinstance(info.value, FueraDelProyecto)


def test_a1_ruta_con_punto_punto_que_sale_se_rechaza(tmp_path: Path):
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    (tmp_path / "otro.txt").write_text(CANARIO, encoding="utf-8")
    with pytest.raises(FueraDelProyecto):
        FsSoloLectura(str(proyecto)).leer_texto(Ruta(str(proyecto / ".." / "otro.txt")))


# --- A2 y M: sonda de Windows -------------------------------------------------------------------


@pytest.fixture
def sonda():
    if sys.platform != "win32":
        pytest.skip("solo Windows")
    from agentreach.infra.sonda_windows import SondaWindows

    return SondaWindows()


@solo_windows
@pytest.mark.parametrize(
    "ruta",
    ["NUL", "CON", "nul.txt", r"C:\NUL", r"C:\temp\COM1", r"C:\temp\lpt9.log", r"\\.\C:",
     r"\\.\NUL", r"relativa\archivo.env", "archivo.env", r"\\servidor\recurso\a.env"],
)
def test_a2_nombres_de_dispositivo_y_rutas_no_absolutas_son_no_determinado(sonda, ruta):
    r = sonda.evaluar(Ruta(ruta))
    assert r.permiso.value == "no_determinado"
    assert r.ambiguo is True and r.abierto_a_todos is False


@solo_windows
def test_a2_una_carpeta_no_es_archivo_salvo_que_se_pida(sonda, tmp_path: Path):
    assert sonda.evaluar(Ruta(str(tmp_path))).permiso.value == "no_determinado"
    assert sonda.evaluar(Ruta(str(tmp_path)), permitir_carpeta=True).permiso.value == "si"


@solo_windows
def test_a2_una_ruta_inexistente_o_con_nulo_no_es_comprobada(sonda, tmp_path: Path):
    assert sonda.evaluar(Ruta(str(tmp_path / "no-existe"))).permiso.value == "no_determinado"
    assert sonda.evaluar(Ruta("C:\\a\x00b")).permiso.value == "no_determinado"


def test_a2_nombres_reservados_se_reconocen_con_y_sin_extension():
    for nombre in ("NUL", "nul.txt", "COM1", "com9.x", "LPT1", "CON", "PRN", "AUX.log", "NUL ."):
        assert tiene_nombre_reservado(nombre), nombre
    for nombre in ("COM10", "console.txt", "nulo", "auxiliar.env", "CONFIG"):
        assert not tiene_nombre_reservado(nombre), nombre


# GUARDA DE REGRESIÓN: usa el campo pasa_por_enlace.
@solo_windows
def test_m_la_sonda_avisa_si_la_ruta_pasa_por_una_junction(sonda, tmp_path: Path):
    destino = tmp_path / "destino"
    destino.mkdir()
    (destino / "a.env").write_text("X=1", encoding="utf-8")
    if not _enlace_de_carpeta(tmp_path / "enl", destino):
        pytest.skip("el entorno no permite crear enlaces de carpeta")
    r = sonda.evaluar(Ruta(str(tmp_path / "enl" / "a.env")))
    assert r.pasa_por_enlace is True and r.ambiguo is True
    directo = sonda.evaluar(Ruta(str(destino / "a.env")))
    assert directo.pasa_por_enlace is False


# --- M1: Unicode engañoso -----------------------------------------------------------------------


def test_m1_limpiar_ruta_quita_direccion_ancho_cero_y_formato():
    peligrosos = [chr(c) for c in (*range(0x202A, 0x202F), *range(0x2066, 0x206A),
                                   0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x200E, 0x00AD, 0x2028, 0x2029)]
    for c in peligrosos:
        assert limpiar_ruta(f"a{c}b.txt") == "ab.txt", hex(ord(c))
    assert limpiar_ruta("reporte\u202etxt.exe") == "reportetxt.exe"
    assert limpiar_ruta("acción-ñ.md") == "acción-ñ.md"


# --- M2: ruta mostrada y ruta usada separadas ---------------------------------------------------


# GUARDA DE REGRESIÓN: usa el campo ruta_real.
@pytest.mark.skipif(sys.platform == "win32", reason="Windows no admite controles en nombres")
def test_m2_una_carpeta_con_caracter_de_control_se_recorre_con_su_ruta_real(tmp_path: Path):
    proyecto = tmp_path / "proyecto"
    rara = proyecto / "a\x07b"
    rara.mkdir(parents=True)
    (rara / "x.txt").write_text("x", encoding="utf-8")
    recorrido = recorrer(FsSoloLectura(), Ruta(str(proyecto)))
    assert [os.path.basename(a.ruta) for a in recorrido.archivos] == ["x.txt"]
    assert recorrido.no_revisadas == ()
    assert "\x07" not in recorrido.archivos[0].ruta
    assert "\x07" in (recorrido.archivos[0].ruta_real or "")


# GUARDA DE REGRESIÓN: usa el campo ruta_real.
def test_m2_metadatos_separan_ruta_mostrada_y_real(tmp_path: Path):
    f = tmp_path / "a.txt"
    f.write_text("x", encoding="utf-8")
    m = FsSoloLectura().metadatos(Ruta(str(f)))
    assert isinstance(m, Metadatos) and m.ruta_real == str(f)


# GUARDA DE REGRESIÓN: usa la función privada _sale_del_proyecto.
def test_m2_el_destino_del_enlace_se_evalua_sin_limpiar(tmp_path: Path):
    from agentreach.collectors.enlaces import _sale_del_proyecto

    raiz = os.path.normcase(os.path.realpath(tmp_path / "proy"))
    # limpio parece "../proy" (dentro del vecino), pero el original lleva un carácter de control
    enlace = Metadatos(
        ruta=Ruta(str(tmp_path / "proy" / "l")), tamano=0, es_carpeta=True, es_enlace=True,
        destino_enlace=Ruta("../proy"), ruta_real=str(tmp_path / "proy" / "l"),
        destino_real="../proy\x7f",
    )
    assert _sale_del_proyecto(enlace, raiz) is True


# --- M3: tubería, tamaño y apertura -------------------------------------------------------------


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="solo POSIX")
def test_m3_una_tuberia_con_nombre_no_bloquea(tmp_path: Path):
    tuberia = tmp_path / "t.env"
    os.mkfifo(tuberia)
    assert not stat.S_ISREG(os.lstat(tuberia).st_mode)
    with pytest.raises(ArchivoNoLegible):
        FsSoloLectura().leer_texto(Ruta(str(tuberia)))


# GUARDA DE REGRESIÓN: simula con getsize; ver la prueba por comportamiento.
def test_m3_el_archivo_que_crece_no_se_devuelve(tmp_path: Path, monkeypatch):
    from agentreach.infra import fs_solo_lectura as modulo

    f = tmp_path / "g.txt"
    f.write_text("a" * 100, encoding="utf-8")
    monkeypatch.setattr(modulo, "LIMITE_BYTES", 10)  # el tamaño de lstat/getsize ya no basta
    monkeypatch.setattr(modulo.os.path, "getsize", lambda _r: 5)  # simula que creció después
    with pytest.raises(ArchivoNoLegible):
        FsSoloLectura().leer_texto(Ruta(str(f)))


# --- M4: rutas de red ---------------------------------------------------------------------------


def test_m4_unc_es_de_red_sin_consultar():
    assert es_ruta_de_red(r"\\servidor\recurso\x")
    assert es_ruta_de_red("//servidor/recurso")


@solo_windows
def test_m4_una_unidad_de_red_se_trata_como_de_red(monkeypatch):
    import ctypes

    class _K32:
        @staticmethod
        def GetDriveTypeW(_u):
            return 4  # DRIVE_REMOTE

    monkeypatch.setattr(ctypes, "WinDLL", lambda *_a, **_k: _K32())
    assert es_ruta_de_red(r"Z:\proyecto") is True


# GUARDA DE REGRESIÓN: usa la función privada _sale_del_proyecto.
@solo_windows
def test_m4_no_se_llama_realpath_sobre_destinos_de_red(monkeypatch):
    from agentreach.collectors import enlaces

    llamadas: list[str] = []
    monkeypatch.setattr(enlaces.os.path, "realpath", lambda r: llamadas.append(r) or r)
    enlace = Metadatos(
        ruta=Ruta(r"C:\p\l"), tamano=0, es_carpeta=True, es_enlace=True,
        destino_enlace=Ruta(r"\\srv\x"), ruta_real=r"C:\p\l", destino_real=r"\\srv\x",
    )
    assert enlaces._sale_del_proyecto(enlace, r"c:\p") is True
    assert llamadas == []
