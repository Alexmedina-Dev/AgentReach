"""Historia 3: permisos del sistema en Windows, leídos con ctypes sin abrir el archivo."""

from __future__ import annotations

import ast
import builtins
import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agentreach.contracts import FsProbe, PermisoLectura, PermisosArchivo, Ruta

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

solo_windows = pytest.mark.skipif(sys.platform != "win32", reason="solo Windows")

RAIZ_FUENTES = Path(__file__).resolve().parents[1] / "src" / "agentreach"


def _icacls(*args: str) -> None:
    """Prepara casos de prueba. Es la PRUEBA la que llama a icacls, nunca el producto."""
    subprocess.run(["icacls", *args], check=True, capture_output=True)


def _quien_soy() -> str:
    return subprocess.run(["whoami"], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def sonda():
    from agentreach.infra.sonda_windows import SondaWindows

    return SondaWindows()


@pytest.fixture
def archivo(tmp_path: Path) -> Path:
    f = tmp_path / ".env.staging"
    f.write_text("CLAVE=valor-falso", encoding="utf-8")
    return f


@solo_windows
def test_cumple_el_puerto_y_da_usuario_y_comando_de_verificacion(sonda, archivo):
    assert isinstance(sonda, FsProbe)
    r = sonda.evaluar(Ruta(str(archivo)))
    assert isinstance(r, PermisosArchivo)
    assert r.usuario and r.usuario.lower().split("\\")[-1] == _quien_soy().lower().split("\\")[-1]
    assert r.comando_verificacion == f'icacls "{archivo}"'  # texto para la persona; no se ejecuta


@solo_windows
def test_pp04_permiso_normal_es_legible_y_no_abierto_a_todos(sonda, archivo):
    r = sonda.evaluar(Ruta(str(archivo)))
    assert r.permiso is PermisoLectura.SI
    assert r.abierto_a_todos is False and r.ambiguo is False
    assert sonda.permiso_lectura(Ruta(str(archivo))) is PermisoLectura.SI


@solo_windows
def test_pp03_lectura_negada_da_no_legible(sonda, archivo):
    _icacls(str(archivo), "/deny", f"{_quien_soy()}:(R)")
    r = sonda.evaluar(Ruta(str(archivo)))
    assert r.permiso is PermisoLectura.NO
    assert r.ambiguo is True  # se deduce de la negativa, no de leer la ACL
    assert r.usuario


@solo_windows
def test_pa01_entrada_propia_para_todos_es_abierto_e_inequivoco(sonda, archivo):
    _icacls(str(archivo), "/grant", "*S-1-1-0:(R)")
    r = sonda.evaluar(Ruta(str(archivo)))
    assert r.permiso is PermisoLectura.SI
    assert r.abierto_a_todos is True and r.ambiguo is False


@solo_windows
def test_permiso_para_todos_heredado_es_abierto_y_no_ambiguo(sonda, tmp_path: Path):
    carpeta = tmp_path / "heredada"
    carpeta.mkdir()
    _icacls(str(carpeta), "/grant", "*S-1-1-0:(OI)(CI)(R)")
    hijo = carpeta / "datos.env"
    hijo.write_text("X=1", encoding="utf-8")  # hereda la entrada de la carpeta
    r = sonda.evaluar(Ruta(str(hijo)))
    assert r.abierto_a_todos is True and r.ambiguo is False


@solo_windows
def test_todos_con_regla_de_denegar_es_ambiguo(sonda, archivo):
    _icacls(str(archivo), "/grant", "*S-1-1-0:(R)")
    _icacls(str(archivo), "/deny", f"{_quien_soy()}:(W)")
    r = sonda.evaluar(Ruta(str(archivo)))
    assert r.abierto_a_todos is True and r.ambiguo is True


@solo_windows
def test_archivo_inexistente_es_no_determinado_y_ambiguo(sonda, tmp_path: Path):
    r = sonda.evaluar(Ruta(str(tmp_path / "no-existe.env")))
    assert r.permiso is PermisoLectura.NO_DETERMINADO and r.ambiguo is True


# (a) no se abre el archivo medido ---------------------------------------------------------------


@solo_windows
def test_no_se_abre_el_archivo_medido(sonda, archivo, monkeypatch):
    objetivo = os.path.normcase(os.path.abspath(archivo))

    def vigilar(original):
        def envoltura(ruta, *a, **k):
            if isinstance(ruta, (str, bytes, os.PathLike)) and (
                os.path.normcase(os.path.abspath(os.fsdecode(ruta))) == objetivo
            ):
                raise AssertionError("se abrió el archivo medido")
            return original(ruta, *a, **k)

        return envoltura

    monkeypatch.setattr(builtins, "open", vigilar(builtins.open))
    monkeypatch.setattr(io, "open", vigilar(io.open))
    monkeypatch.setattr(os, "open", vigilar(os.open))
    assert sonda.evaluar(Ruta(str(archivo))).permiso is PermisoLectura.SI


# (c) no se lanza icacls ni ningún programa --------------------------------------------------------


@solo_windows
def test_no_se_lanza_ningun_programa(sonda, archivo, monkeypatch):
    def prohibido(*a, **k):
        raise AssertionError("se intentó lanzar un programa")

    monkeypatch.setattr(subprocess, "Popen", prohibido)
    monkeypatch.setattr(os, "system", prohibido)
    monkeypatch.setattr(os, "popen", prohibido)
    sonda.evaluar(Ruta(str(archivo)))


@pytest.mark.parametrize("nombre", ["sonda_windows.py", "sonda_posix.py"])
def test_el_codigo_de_las_sondas_no_importa_modulos_de_procesos(nombre):
    arbol = ast.parse((RAIZ_FUENTES / "infra" / nombre).read_text(encoding="utf-8"))
    prohibidos = {"subprocess", "multiprocessing", "pty", "shlex"}
    importados = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            importados |= {a.name.split(".")[0] for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.add(nodo.module.split(".")[0])
    assert not importados & prohibidos
    llamadas = {
        n.func.attr for n in ast.walk(arbol) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
    }
    assert not llamadas & {"system", "popen", "Popen", "startfile", "execv", "spawnl"}


# POSIX: modo y propietario (sin pruebas obligatorias; se omite en Windows) ------------------------


@pytest.mark.skipif(sys.platform == "win32", reason="solo POSIX")
def test_posix_devuelve_modo_y_propietario(tmp_path: Path):
    from agentreach.infra.sonda_posix import SondaPosix

    f = tmp_path / "a.env"
    f.write_text("X=1", encoding="utf-8")
    f.chmod(0o644)
    r = SondaPosix().evaluar(Ruta(str(f)))
    assert r.modo == "0o644" and r.propietario is not None
    assert r.abierto_a_todos is True and r.permiso is PermisoLectura.SI


# Casos del proyecto de prueba (se omiten si no está la variable de entorno) -----------------------


@solo_windows
def test_casos_pp03_pp04_pp05_pa01_con_el_proyecto_de_prueba(sonda):
    raiz = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")
    if not raiz or not (Path(raiz) / "proyecto").is_dir():
        pytest.skip("AGENTREACH_PROYECTO_PRUEBA no apunta al proyecto de prueba")
    p = Path(raiz) / "proyecto"
    assert sonda.evaluar(Ruta(str(p / ".env.staging"))).permiso is PermisoLectura.SI  # PP-04
    assert sonda.evaluar(Ruta(str(p / ".env.local"))).permiso is PermisoLectura.SI  # PP-05
    assert sonda.evaluar(Ruta(str(p / ".env.production"))).permiso is PermisoLectura.NO  # PP-03
    abierto = sonda.evaluar(Ruta(str(p / "config" / "exportacion-abierta.env")))  # PA-01
    assert abierto.abierto_a_todos is True and abierto.ambiguo is False
    assert sonda.evaluar(Ruta(str(p / ".env.staging"))).abierto_a_todos is False


def test_comando_posix_no_deja_pasar_inyeccion():
    from agentreach.infra.sonda_posix import _entre_comillas

    assert _entre_comillas("a b") == "'a b'"
    assert _entre_comillas('x"; rm -rf ~; "$(id)') == "'x\"; rm -rf ~; \"$(id)'"
    assert _entre_comillas("it's") == "'it'\\''s'"


@solo_windows
def test_ruta_invalida_no_lanza_excepcion(sonda):
    r = sonda.evaluar(Ruta(r"C:\carpeta\0rara"))
    assert r.permiso is PermisoLectura.NO_DETERMINADO and r.ambiguo is True
