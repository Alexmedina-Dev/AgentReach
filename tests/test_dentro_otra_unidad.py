"""``dentro`` no confunde "otra unidad de disco" con "dentro de la carpeta auditada" (el reporte de un proyecto en D: se escribe en C:)."""

from __future__ import annotations

import os
import sys

import pytest

from agentreach.cli import reportes

solo_windows = pytest.mark.skipif(sys.platform != "win32", reason="las unidades de disco (C:, D:) son de Windows")


@solo_windows
def test_en_otra_unidad_no_esta_dentro(monkeypatch) -> None:
    monkeypatch.setattr(os.path, "realpath", lambda ruta: ruta)  # sin tocar el disco
    assert reportes.dentro(r"C:\Users\ana\AgentReach-reportes\reporte.html", r"D:\proyectos\app") is False


def test_en_la_misma_unidad_sigue_detectando_lo_de_dentro(tmp_path) -> None:
    carpeta = tmp_path / "app"
    carpeta.mkdir()
    assert reportes.dentro(str(carpeta / "salida.txt"), str(carpeta)) is True
    assert reportes.dentro(str(tmp_path / "otra" / "salida.txt"), str(carpeta)) is False
