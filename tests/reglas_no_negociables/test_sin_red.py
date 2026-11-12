"""FR-2: sin red por defecto. Con la red vigilada (gancho de auditoría) la auditoría termina con el mismo resultado."""

from __future__ import annotations

import ast
import socket
from pathlib import Path

import pytest

from agentreach import cli
from conftest import INTENTOS, ViolacionDeRegla, auditoria_completa

MODULOS_DE_RED = {"socket", "_socket", "ssl", "http", "urllib3", "requests", "httpx", "ftplib", "smtplib", "telnetlib", "xmlrpc",
                  "asyncio", "aiohttp", "websocket", "websockets", "imaplib", "poplib", "socketserver", "selectors"}


def test_la_auditoria_completa_da_el_mismo_resultado_sin_red(raiz_prueba: Path, request):
    con_red = auditoria_completa(raiz_prueba, "--detalle")  # la red existe, pero AgentReach no la usa
    assert con_red[0] in (0, 1) and "Reporte de revisión" in con_red[1]
    request.getfixturevalue("sin_red")  # a partir de aquí, cualquier evento de socket falla la prueba
    assert auditoria_completa(raiz_prueba, "--detalle") == con_red  # mismo código, mismo reporte, mismos errores


def test_el_doctor_y_la_ayuda_tampoco_usan_la_red(raiz_prueba: Path, sin_red, capsys):
    assert cli.main(["doctor", str(raiz_prueba / "proyecto")]) in (0, 1)
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    with pytest.raises(SystemExit):
        cli.main(["--version"])
    capsys.readouterr()


def test_el_gancho_ve_cada_via_de_red(sin_red):
    """La propia vigilancia se prueba: crear sockets, resolver nombres o preguntar el nombre del equipo falla en el acto."""
    import _socket

    vias = [
        lambda: socket.socket(),
        lambda: _socket.socket(),
        lambda: socket.getaddrinfo("example.invalid", 80),
        lambda: socket.gethostbyname("example.invalid"),
        lambda: socket.getnameinfo(("127.0.0.1", 80), 0),
        lambda: socket.gethostname(),
        lambda: socket.create_connection(("127.0.0.1", 9)),
    ]
    for via in vias:
        with pytest.raises(ViolacionDeRegla):
            try:
                via()
            except Exception:  # noqa: BLE001 - un `except Exception` del producto no debe poder tragarse la trampa
                pytest.fail("se tragó la trampa")
    assert len(INTENTOS) >= len(vias)
    INTENTOS.clear()


def test_el_producto_no_importa_ningun_modulo_de_red():
    """Estática: ningún módulo del producto importa algo que hable por la red (``urllib.parse`` solo trocea texto)."""
    raiz = Path(cli.__file__).resolve().parents[1]
    for archivo in raiz.rglob("*.py"):
        for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
            nombres = [a.name for a in nodo.names] if isinstance(nodo, ast.Import) else (
                [nodo.module or ""] if isinstance(nodo, ast.ImportFrom) else [])
            for nombre in nombres:
                if nombre in ("urllib.parse", "urllib"):
                    continue  # (``from urllib import parse`` también es solo texto)
                assert nombre.split(".")[0] not in MODULOS_DE_RED, f"{archivo.name} importa {nombre}"
            if isinstance(nodo, ast.Call) and getattr(nodo.func, "id", "") == "__import__":
                pytest.fail(f"{archivo.name} usa __import__: no se puede comprobar qué importa")


def test_una_ruta_de_red_no_se_sigue_y_sale_como_no_revisada(sin_red):
    """Las rutas UNC se reportan como «ruta de red» sin tocarlas (leer metadatos de un recurso compartido ya es red)."""
    from agentreach.contracts import MotivoNoRevisado
    from agentreach.infra.lectura_segura import leer_seguro

    resultado = leer_seguro(r"\\servidor-que-no-existe\compartido\.env")  # type: ignore[arg-type]
    assert getattr(resultado, "motivo", None) is MotivoNoRevisado.RUTA_DE_RED
