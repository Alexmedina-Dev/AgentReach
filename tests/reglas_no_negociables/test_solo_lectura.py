"""FR-1: AgentReach solo lee. El árbol del proyecto de prueba queda idéntico: contenido, tamaño y marcas de modificación."""

from __future__ import annotations

import ast
import io
import os
from pathlib import Path

import pytest

from agentreach import cli
from conftest import AHORA, INTENTOS, ViolacionDeRegla, auditoria_completa, instantanea


def test_el_arbol_del_proyecto_de_prueba_queda_identico(raiz_prueba: Path, tempdir_vacio, sin_escrituras):
    antes = instantanea(raiz_prueba)
    assert len(antes) > 50  # el proyecto completo, trampas incluidas
    codigo, salida, _ = auditoria_completa(raiz_prueba)
    assert codigo in (0, 1) and "Reporte de revisión" in salida
    despues = instantanea(raiz_prueba)
    assert despues == antes  # ni un archivo nuevo, borrado ni cambiado; ni una marca de modificación movida
    assert list(tempdir_vacio.iterdir()) == []  # ni un archivo temporal


def test_la_carpeta_del_proyecto_y_el_doctor_tampoco_escriben(raiz_prueba: Path, tempdir_vacio, sin_escrituras, capsys):
    antes = instantanea(raiz_prueba)
    assert cli.main([str(raiz_prueba / "proyecto"), "--detalle", "--sin-reporte-html"], ahora=lambda: AHORA) in (0, 1)
    assert cli.main(["doctor", str(raiz_prueba / "proyecto")]) in (0, 1)
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    assert instantanea(raiz_prueba) == antes
    assert list(tempdir_vacio.iterdir()) == []
    capsys.readouterr()


def test_el_gancho_ve_cada_via_de_escritura(raiz_prueba: Path, sin_escrituras):
    """La propia vigilancia se prueba: por cualquier vía que se escriba, falla en el acto (y no la traga un ``except Exception``)."""
    import _io

    destino = str(raiz_prueba / "no-debe-existir.txt")
    vias = {
        "open": lambda: open(destino, "w"),  # noqa: SIM115
        "open con mode=": lambda: open(destino, mode="wb"),  # noqa: SIM115
        "io.open": lambda: open(destino, "a"),  # noqa: SIM115
        "_io.open": lambda: _io.open(destino, "w"),
        "io.FileIO": lambda: io.FileIO(destino, "w"),
        "os.open": lambda: os.open(destino, os.O_WRONLY | os.O_CREAT),
        "Path.write_text": lambda: Path(destino).write_text("x"),
        "Path.mkdir": lambda: Path(str(raiz_prueba / "otra")).mkdir(),
        "os.remove": lambda: os.remove(destino),
        "os.rename": lambda: os.rename(destino, destino + "2"),
        "os.chmod": lambda: os.chmod(destino, 0o600),
    }
    for nombre, via in vias.items():
        with pytest.raises(ViolacionDeRegla):
            try:
                via()
            except Exception:  # noqa: BLE001 - lo que haría un `except Exception` del producto: no debe poder tragarse la trampa
                pytest.fail(f"{nombre}: se tragó la trampa")
    assert len(INTENTOS) == len(vias)
    INTENTOS.clear()  # eran intentos a propósito: la prueba no debe fallar al terminar
    assert not Path(destino).exists() and not (raiz_prueba / "otra").exists()


def test_leer_si_esta_permitido(raiz_prueba: Path, sin_escrituras):
    assert (raiz_prueba / "respuestas-esperadas.md").read_bytes()
    with open(raiz_prueba / "respuestas-esperadas.md", "rb") as f:
        assert f.read()
    assert not INTENTOS


def test_el_producto_solo_escribe_donde_la_persona_lo_pide():
    """Estática: abrir para escribir solo ocurre con --salida (``cli/__init__.py``) y en ``AgentReach-reportes`` (``cli/reportes.py``,
    el único lugar que crea una carpeta). Nada más del producto escribe, crea carpetas, borra ni cambia permisos."""
    raiz = Path(cli.__file__).resolve().parents[1]
    prohibidas = {"write_text", "write_bytes", "mkdir", "makedirs", "touch", "unlink", "rmtree", "copyfile", "copytree", "rename",
                  "replace", "symlink_to", "hardlink_to", "chmod"}
    for archivo in raiz.rglob("*.py"):
        if "conformance" in archivo.parts:
            continue  # el kit de conformidad escribe en carpetas temporales de PRUEBA, nunca en el producto
        for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
            if not isinstance(nodo, ast.Call):
                continue
            nombre = getattr(nodo.func, "attr", getattr(nodo.func, "id", ""))
            if nombre == "replace":  # ``str.replace`` no escribe; ``os.replace`` sí
                assert getattr(getattr(nodo.func, "value", None), "id", "") != "os", f"{archivo.name} llama a os.replace"
                continue
            if nombre in ("mkdir", "makedirs"):  # crear la carpeta de reportes: solo ``cli/reportes.py``
                assert archivo.parent.name == "cli" and archivo.name == "reportes.py", f"{archivo.name} llama a {nombre}"
                continue
            assert nombre not in prohibidas, f"{archivo.name} llama a {nombre}"
            modos = [getattr(a, "value", "") for a in nodo.args[1:2]] + [
                getattr(k.value, "value", "") for k in nodo.keywords if k.arg == "mode"]
            if nombre in ("open", "fdopen") and any(any(c in str(m) for c in "wax+") for m in modos):
                assert archivo.parent.name == "cli" and archivo.name in ("__init__.py", "reportes.py"), f"{archivo} abre para escribir"
