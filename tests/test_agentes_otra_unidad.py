"""La detección de agentes no se rompe si la carpeta personal y una ruta del usuario están en unidades distintas."""

from __future__ import annotations

import os

from agentreach.app import agentes


def test_ruta_en_otra_unidad_no_rompe(monkeypatch) -> None:
    def sin_ruta_relativa(destino: str, inicio: str) -> str:
        raise ValueError(f"path is on mount 'C:', start on mount 'D:' ({destino}, {inicio})")

    monkeypatch.setattr(os.path, "relpath", sin_ruta_relativa)
    resultado = agentes._relativa_a_home(os.path.join("C:", os.sep, "datos", "agente.json"), os.path.join("D:", os.sep, "casa"))
    assert resultado == os.path.normpath(os.path.join("C:", os.sep, "datos", "agente.json"))


def test_ruta_dentro_de_la_carpeta_personal_sigue_siendo_relativa(tmp_path) -> None:
    destino = tmp_path / ".config" / "agente.json"
    assert agentes._relativa_a_home(str(destino), str(tmp_path)) == os.path.join(".config", "agente.json")
