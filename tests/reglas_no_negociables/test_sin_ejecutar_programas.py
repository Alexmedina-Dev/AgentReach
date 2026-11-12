"""AgentReach no ejecuta ningún programa externo (ni git). Los señuelos del proyecto de prueba nunca corren (caso TR-01)."""

from __future__ import annotations

import ast
import os
import subprocess
from pathlib import Path

import pytest

from agentreach import cli
from conftest import INTENTOS, ViolacionDeRegla, auditoria_completa

PROHIBIDOS_LLAMADA = {"system", "popen", "startfile", "run", "Popen", "call", "check_call", "check_output", "getoutput",
                      "getstatusoutput", "ShellExecute", "ShellExecuteW", "ShellExecuteEx", "CreateProcess", "CreateProcessW",
                      "WinExec", "posix_spawn", "posix_spawnp", "fork", "forkpty"}
# Los únicos módulos que usan ``ctypes`` (la sonda de permisos, su segunda vía, el modo de color, el idioma regional y el tipo de unidad).
USAN_CTYPES = {"sonda_windows.py", "verificador_permiso_windows.py", "formato.py", "__init__.py", "rutas.py"}


def test_la_auditoria_completa_termina_igual_sin_poder_lanzar_programas(raiz_prueba: Path, request):
    base = auditoria_completa(raiz_prueba, "--detalle")  # sin la vigilancia: el resultado de referencia
    request.getfixturevalue("sin_procesos")
    vigilado = auditoria_completa(raiz_prueba, "--detalle")
    assert vigilado == base and base[0] in (0, 1)


def test_el_senuelo_de_las_trampas_nunca_corre(raiz_prueba: Path, sin_procesos):
    """TR-01: ``trampas/PWNED.txt`` solo existiría si algo ejecutara el señuelo."""
    for argv in ([], ["--detalle"], ["--idioma", "en"]):
        auditoria_completa(raiz_prueba, *argv)
        assert not (raiz_prueba / "trampas" / "PWNED.txt").exists()
    for hijo in raiz_prueba.rglob("PWNED*"):
        pytest.fail(f"apareció {hijo}: algo ejecutó un señuelo")


def test_el_doctor_y_la_ayuda_no_lanzan_nada(raiz_prueba: Path, sin_procesos, capsys):
    assert cli.main(["doctor", str(raiz_prueba / "proyecto")]) in (0, 1)
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    capsys.readouterr()


def test_el_gancho_ve_cada_via_de_lanzar_programas(sin_procesos):
    """La propia vigilancia se prueba (y ningún ``except Exception`` puede tragarse la trampa)."""
    import nt  # type: ignore[import-not-found]

    vias = [
        lambda: subprocess.run(["cmd", "/c", "echo", "no"], check=False),
        lambda: subprocess.Popen(["cmd", "/c", "echo", "no"]),
        lambda: os.system("echo no"),
        lambda: nt.system("echo no"),
        lambda: os.startfile("no-existe.txt"),
        lambda: os.spawnl(os.P_NOWAIT, "cmd", "cmd"),
        lambda: os.execv("cmd", ["cmd"]),
    ]
    for via in vias:
        with pytest.raises(ViolacionDeRegla):
            try:
                via()
            except Exception:  # noqa: BLE001
                pytest.fail("se tragó la trampa")
    assert len(INTENTOS) == len(vias)
    INTENTOS.clear()


def _fuentes():
    raiz = Path(cli.__file__).resolve().parents[1]
    for archivo in raiz.rglob("*.py"):
        yield archivo, ast.parse(archivo.read_text(encoding="utf-8"))


def test_el_producto_no_contiene_ninguna_via_para_lanzar_programas():
    """Estática: sin ``subprocess`` ni llamadas que lancen procesos, y sin una opción en la ayuda que lo permita."""
    for archivo, arbol in _fuentes():
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                assert all(a.name.split(".")[0] not in ("subprocess", "_winapi", "pty") for a in nodo.names), (
                    f"{archivo.name} importa un módulo que lanza procesos")
            if isinstance(nodo, ast.ImportFrom):
                assert (nodo.module or "").split(".")[0] not in ("subprocess", "_winapi", "pty"), f"{archivo.name} importa subprocess"
            if isinstance(nodo, ast.Call):
                nombre = getattr(nodo.func, "attr", getattr(nodo.func, "id", ""))
                assert nombre not in PROHIBIDOS_LLAMADA, f"{archivo.name} llama a {nombre}"
                assert not (nombre.startswith(("exec", "spawn")) and nombre[4:5] in ("l", "v", "p", "e")), f"{archivo.name} llama a {nombre}"
                assert nombre != "__import__", f"{archivo.name} usa __import__"
    ayuda = cli.construir_parser().format_help().lower()
    assert "permitir-git" not in ayuda and "--ejecutar" not in ayuda and "--exec" not in ayuda


def test_ctypes_solo_lo_usan_los_modulos_de_medicion_y_nunca_para_lanzar_nada():
    """Estática: ``ctypes`` podría llamar a ``system`` de la biblioteca de C; solo lo importan los módulos esperados y sin nombres de proceso."""
    for archivo, arbol in _fuentes():
        importa = any(
            (isinstance(n, ast.Import) and any(a.name.split(".")[0] == "ctypes" for a in n.names))
            or (isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "ctypes")
            for n in ast.walk(arbol)
        )
        if not importa:
            continue
        assert archivo.name in USAN_CTYPES, f"{archivo} importa ctypes y no está en la lista de módulos permitidos"
        textos = {n.value for n in ast.walk(arbol) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        nombres = {getattr(n, "attr", getattr(n, "id", "")) for n in ast.walk(arbol) if isinstance(n, (ast.Attribute, ast.Name))}
        for prohibido in ("msvcrt", "ShellExecuteW", "CreateProcessW", "WinExec", "system", "cdll", "libc"):
            assert prohibido not in nombres and prohibido not in textos, f"{archivo.name} nombra {prohibido}"
