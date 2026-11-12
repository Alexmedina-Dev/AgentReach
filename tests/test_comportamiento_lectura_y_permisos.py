"""Pruebas por comportamiento observable, con la API pública y estable de hoy.

No dependen de nombres internos nuevos (parámetros, funciones privadas ni campos añadidos
después): solo de ``FsSoloLectura``, ``leer_seguro``, ``SondaWindows.evaluar``, ``limpiar_ruta``
y de lo que el sistema operativo hace de verdad.
"""

from __future__ import annotations

import builtins
import os
import sys
from pathlib import Path

import pytest

from agentreach.contracts import Ruta, limpiar_ruta
from agentreach.infra.fs_solo_lectura import FsSoloLectura

try:  # código nuevo: la excepción vive en los contratos
    from agentreach.contracts import ArchivoNoLegible
except ImportError:  # código anterior a las correcciones
    from agentreach.infra.fs_solo_lectura import ArchivoNoLegible
from agentreach.infra.lectura_segura import leer_seguro

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

CANARIO = "CANARIO-COMPORTAMIENTO-sk_live_" + "0123456789abcdef"
solo_windows = pytest.mark.skipif(sys.platform != "win32", reason="solo Windows")


def _fs(raiz: str | None = None) -> FsSoloLectura:
    """``FsSoloLectura(raiz)``; si el constructor no acepta raíz (código viejo), ``FsSoloLectura()``.

    Así una prueba con raíz falla, en el código viejo, por el defecto y no por el constructor.
    """
    if raiz is None:
        return FsSoloLectura()
    try:
        return FsSoloLectura(raiz)
    except TypeError:
        return FsSoloLectura()


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


# --- (1) enlace real en una carpeta intermedia: nunca se devuelve contenido de fuera -------------


@pytest.mark.parametrize("con_raiz", [True, False])
def test_leer_a_traves_de_una_junction_intermedia_nunca_devuelve_contenido(tmp_path: Path, con_raiz: bool):
    proyecto, fuera = tmp_path / "proyecto", tmp_path / "fuera"
    proyecto.mkdir()
    fuera.mkdir()
    (fuera / "secreto.env").write_text(f"K={CANARIO}", encoding="utf-8")
    (proyecto / "normal.txt").write_text("ok", encoding="utf-8")
    if not _enlace_de_carpeta(proyecto / "enl", fuera):
        pytest.skip("el entorno no permite crear enlaces de carpeta")
    fs = _fs(str(proyecto)) if con_raiz else _fs()
    with pytest.raises(ArchivoNoLegible) as info:
        fs.leer_texto(Ruta(str(proyecto / "enl" / "secreto.env")))
    assert CANARIO not in str(info.value)
    # Un archivo normal del proyecto sí se lee (con raíz; sin raíz solo si el entorno no usa enlaces).
    if con_raiz:
        assert fs.leer_texto(Ruta(str(proyecto / "normal.txt"))) == "ok"


def test_punto_punto_que_sale_del_proyecto_no_devuelve_contenido(tmp_path: Path):
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    (tmp_path / "otro.txt").write_text(CANARIO, encoding="utf-8")
    with pytest.raises(ArchivoNoLegible) as info:
        _fs(str(proyecto)).leer_texto(Ruta(str(proyecto / ".." / "otro.txt")))
    assert CANARIO not in str(info.value)


# --- (2) sonda de Windows: nunca comprobada ni abierta para nombres de dispositivo ---------------


def _prohibir_abrir(monkeypatch) -> list[str]:
    llamadas: list[str] = []

    def _no(nombre):
        def f(*a, **k):
            llamadas.append(f"{nombre}{a!r}")
            raise AssertionError(f"{nombre} no debe llamarse")

        return f

    monkeypatch.setattr(builtins, "open", _no("open"))
    monkeypatch.setattr(os, "open", _no("os.open"))
    return llamadas


_DISPOSITIVOS = {"NUL", "CON", "COM1", "PRN", "AUX", "LPT1"}


def _es_dispositivo(valor) -> bool:
    if not isinstance(valor, (str, bytes, os.PathLike)):
        return False
    texto = os.fsdecode(valor)
    if texto.startswith("\\\\.\\"):
        return True
    nombre = texto.replace("/", "\\").rsplit("\\", 1)[-1]
    return nombre.split(".")[0].rstrip(" ").upper() in _DISPOSITIVOS


def _espiar_dispositivos(monkeypatch) -> list[str]:
    """Espía que deja pasar las llamadas y anota las hechas con un nombre de dispositivo."""
    vistas: list[str] = []
    objetivos = ((os, "stat"), (os, "lstat"), (os.path, "exists"), (os.path, "isfile"), (os, "open"), (builtins, "open"))
    for modulo, nombre in objetivos:
        original = getattr(modulo, nombre)

        def espia(*a, _o=original, _n=nombre, **k):
            if a and _es_dispositivo(a[0]):
                vistas.append(f"{_n}({a[0]!r})")
            return _o(*a, **k)

        monkeypatch.setattr(modulo, nombre, espia)
    return vistas


@solo_windows
@pytest.mark.parametrize("ruta", ["NUL", r"\\.\NUL", "CON", "COM1", r"C:\NUL", r"C:\temp\COM1"])
def test_sonda_no_comprueba_ni_abre_nombres_de_dispositivo(monkeypatch, ruta):
    from agentreach.infra.sonda_windows import SondaWindows

    vistas = _espiar_dispositivos(monkeypatch)
    r = SondaWindows().evaluar(Ruta(ruta))
    assert r.permiso.value == "no_determinado"
    assert r.abierto_a_todos is False
    assert r.ambiguo is True
    assert vistas == [], f"se tocó un dispositivo: {vistas}"


@solo_windows
def test_sonda_no_trata_una_carpeta_como_archivo_y_no_abre(monkeypatch, tmp_path: Path):
    from agentreach.infra.sonda_windows import SondaWindows

    llamadas = _prohibir_abrir(monkeypatch)
    r = SondaWindows().evaluar(Ruta(str(tmp_path)))
    assert r.permiso.value == "no_determinado"
    assert r.abierto_a_todos is False
    assert llamadas == []


@solo_windows
def test_sonda_no_abre_un_archivo_normal(monkeypatch, tmp_path: Path):
    from agentreach.infra.sonda_windows import SondaWindows

    f = tmp_path / "a.env"
    f.write_text("X=1", encoding="utf-8")
    llamadas = _prohibir_abrir(monkeypatch)
    r = SondaWindows().evaluar(Ruta(str(f)))
    assert r.permiso.value in {"si", "no", "no_determinado"}
    assert llamadas == []


# --- (3) realpath nunca se llama con rutas de red (UNC) -----------------------------------------


@pytest.mark.parametrize("ruta", [r"\\servidor\recurso\a.env", "//servidor/recurso/a.env"])
def test_realpath_no_se_llama_con_rutas_unc(monkeypatch, tmp_path: Path, ruta):
    original = os.path.realpath
    unc: list[str] = []

    def espia(r, *a, **k):
        if str(r).startswith(("\\\\", "//")):
            unc.append(str(r))
        return original(r, *a, **k)

    monkeypatch.setattr(os.path, "realpath", espia)
    for fs in (_fs(), _fs(str(tmp_path)), _fs(r"\\srv\proyecto")):
        with pytest.raises(ArchivoNoLegible):
            fs.leer_texto(Ruta(ruta))
    assert leer_seguro(Ruta(ruta)).__class__.__name__ == "NoRevisado"
    if sys.platform == "win32":
        from agentreach.infra.sonda_windows import SondaWindows

        SondaWindows().evaluar(Ruta(ruta))
    assert unc == []


# --- (4) archivo que crece durante la lectura ---------------------------------------------------


def test_archivo_que_crece_despues_de_medirlo_se_rechaza(monkeypatch, tmp_path: Path):
    """Archivo real: pequeño al medirlo y grande justo antes de abrirlo (llama a ``leer_texto``)."""
    f = tmp_path / "g.txt"
    f.write_text("ok", encoding="utf-8")
    original = os.open
    crecio: list[bool] = []

    def abrir_tras_crecer(ruta, *a, **k):
        if not crecio and os.path.abspath(os.fsdecode(ruta)) == os.path.abspath(f):
            with open(f, "ab") as g:
                g.write(CANARIO.encode() + b"a" * (2 * 1024 * 1024))
            crecio.append(True)
        return original(ruta, *a, **k)

    monkeypatch.setattr(os, "open", abrir_tras_crecer)
    with pytest.raises(ArchivoNoLegible) as info:
        _fs(str(tmp_path)).leer_texto(Ruta(str(f)))
    assert crecio, "el archivo no llegó a crecer: la prueba no simuló nada"
    assert CANARIO not in str(info.value)


# --- (5) caracteres de dirección, ancho cero y formato -----------------------------------------

_ENGANOSOS = [
    *range(0x202A, 0x202F),  # inicio/fin de dirección de texto (LRE, RLE, PDF, LRO, RLO)
    *range(0x2066, 0x206A),  # aislamientos de dirección (LRI, RLI, FSI, PDI)
    0x200B, 0x200C, 0x200D,  # espacio de ancho cero y uniones
    0x2060,  # unión de palabras
    0xFEFF,  # marca de orden de bytes (BOM)
]


@pytest.mark.parametrize("codigo", _ENGANOSOS, ids=lambda c: f"U+{c:04X}")
def test_limpiar_ruta_quita_caracteres_enganosos(codigo):
    assert limpiar_ruta(f"a{chr(codigo)}b.txt") == "ab.txt"


def test_limpiar_ruta_conserva_texto_normal_y_desarma_el_truco_de_extension():
    assert limpiar_ruta("reporte\u202etxt.exe") == "reportetxt.exe"
    assert limpiar_ruta("acción-ñ.md") == "acción-ñ.md"
