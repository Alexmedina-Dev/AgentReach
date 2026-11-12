import pytest

"""Prueba de humo: la CLI arranca y devuelve la versión."""

import os
import subprocess
import sys

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)


def _run(*args: str, cwd=None, env=None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "agentreach", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False, cwd=cwd, env={**os.environ, **(env or {}), "PYTHONIOENCODING": "utf-8"}
    )


def test_version():
    r = _run("--version")
    assert r.returncode == 0
    assert r.stdout.startswith("agentreach ")


def _entorno(casa) -> dict:
    return {**os.environ, "USERPROFILE": str(casa), "HOME": str(casa), "AGENTREACH_IDIOMA": "es"}


def test_sin_terminal_interactiva_el_comando_real_no_lee_nada(tmp_path):
    """El comando de verdad (``python -m agentreach``) con la entrada y la salida redirigidas: no lee nada, con o sin ruta."""
    casa = tmp_path / "casa"
    casa.mkdir()
    carpeta = tmp_path / "proyecto"
    carpeta.mkdir()
    (carpeta / ".env").write_text("STRIPE_SECRET_KEY=sk_live_algo_largo_123\n", encoding="utf-8")
    for argumentos in ([], [str(carpeta)], ["--salida", str(tmp_path / "r.txt")], ["--abrir"]):
        r = _run(*argumentos, cwd=carpeta, env=_entorno(casa))
        assert r.returncode == 2 and r.stdout == "" and "sin una terminal interactiva no lee nada" in " ".join(r.stderr.split())
        assert "Traceback" not in r.stderr
    assert not (tmp_path / "r.txt").exists() and not (casa / "AgentReach-reportes").exists()
