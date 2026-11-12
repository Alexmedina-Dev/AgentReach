"""Historia 3b: los permisos heredados no bajan el nivel; solo denegar, DACL rara o fallos."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from agentreach.contracts import PermisoLectura, Ruta

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

solo_windows = pytest.mark.skipif(sys.platform != "win32", reason="solo Windows")
PROYECTO = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")
con_proyecto = pytest.mark.skipif(not PROYECTO, reason="AGENTREACH_PROYECTO_PRUEBA no definida")


def _icacls(*args: str) -> None:
    """Prepara casos de prueba (solo sobre archivos temporales propios); el producto nunca lo llama."""
    subprocess.run(["icacls", *args], check=True, capture_output=True)


def _yo() -> str:
    return subprocess.run(["whoami"], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def sonda():
    from agentreach.infra.sonda_windows import SondaWindows

    return SondaWindows()


@solo_windows
def test_archivo_temporal_heredado_es_legible_y_no_ambiguo(sonda, tmp_path: Path):
    f = tmp_path / "heredado.env"
    f.write_text("X=1", encoding="utf-8")  # hereda de la carpeta temporal
    r = sonda.evaluar(Ruta(str(f)))
    assert r.permiso is PermisoLectura.SI and r.ambiguo is False and not r.pasa_por_enlace


@solo_windows
def test_regla_denegar_en_temporal_es_ambiguo_y_se_quita(sonda, tmp_path: Path):
    f = tmp_path / "denegado.env"
    f.write_text("X=1", encoding="utf-8")
    _icacls(str(f), "/deny", f"{_yo()}:(RD)")
    try:
        r = sonda.evaluar(Ruta(str(f)))
        assert r.permiso is PermisoLectura.NO and r.ambiguo is True
    finally:
        _icacls(str(f), "/remove:d", _yo())
    r = sonda.evaluar(Ruta(str(f)))
    assert r.permiso is PermisoLectura.SI and r.ambiguo is False


@solo_windows
def test_dacl_protegida_con_permiso_explicito_no_es_ambiguo(sonda, tmp_path: Path):
    f = tmp_path / "protegido.env"
    f.write_text("X=1", encoding="utf-8")
    _icacls(str(f), "/grant", f"{_yo()}:(R)")
    _icacls(str(f), "/inheritance:r")  # quita la herencia y deja solo lo explícito
    r = sonda.evaluar(Ruta(str(f)))
    assert r.permiso is PermisoLectura.SI and r.ambiguo is False


@solo_windows
@con_proyecto
def test_proyecto_prueba_env_staging_heredado_no_es_ambiguo(sonda):
    r = sonda.evaluar(Ruta(str(Path(PROYECTO) / "proyecto" / ".env.staging")))
    assert r.permiso is PermisoLectura.SI and r.ambiguo is False


@solo_windows
@con_proyecto
def test_proyecto_prueba_env_production_con_denegar_es_ambiguo(sonda):
    r = sonda.evaluar(Ruta(str(Path(PROYECTO) / "proyecto" / ".env.production")))
    assert r.ambiguo is True and r.permiso is not PermisoLectura.SI
