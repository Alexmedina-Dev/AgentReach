"""Aislamiento común de las pruebas (Historia 11b).

Desde la decisión H2 (opción A) AgentReach lee SIEMPRE la configuración del usuario (``~/.claude/settings.json``,
``~/.config/opencode``) y la gestionada, solo por sus reglas. Una prueba no puede depender de la configuración real de quien la
corre: cada prueba ve una carpeta personal y una carpeta de programas VACÍAS, salvo que ella misma ponga las suyas.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def entorno_sin_configuracion_real(tmp_path_factory, monkeypatch):
    vacia = tmp_path_factory.mktemp("sin-configuracion-real")
    casa, programas = vacia / "casa", vacia / "programas"
    casa.mkdir()
    programas.mkdir()
    for nombre in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(nombre, str(casa))
    monkeypatch.delenv("HOMEDRIVE", raising=False)
    monkeypatch.delenv("HOMEPATH", raising=False)
    for nombre in ("ProgramFiles", "ProgramData", "APPDATA", "LOCALAPPDATA"):
        monkeypatch.setenv(nombre, str(programas))
    for nombre in ("XDG_CONFIG_HOME", "OPENCODE_CONFIG"):  # sin ellas la configuración global es la de la carpeta personal
        monkeypatch.delenv(nombre, raising=False)
    # En Linux y macOS la configuración gestionada vive en una ruta fija del sistema (/etc/..., /Library/...): se redirige a una vacía.
    from agentreach.adapters.claude_code import _gestionada_por_defecto as de_claude
    from agentreach.adapters.opencode import _gestionada_por_defecto as de_opencode

    for modulo, original in (("agentreach.adapters.claude_code", de_claude), ("agentreach.adapters.opencode", de_opencode)):
        monkeypatch.setattr(f"{modulo}._gestionada_por_defecto",
                            lambda sistema, _original=original: _original(sistema) if sistema == "win32" else str(vacia / "gestionada" / "x.json"))


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "sin_tope_por_nombre: prueba del MOTOR de niveles (reglas, permisos, flujo) con el tope por nombre levantado: "
        "ahí TH-1 puede llegar a «comprobado». Las pruebas del tope real (Historia 27) NO llevan esta marca")
    config.addinivalue_line("markers", "terminal_real: la prueba usa la detección real de la terminal y las preguntas reales (sin las ayudas de pruebas)")


def _respuesta_de_prueba(texto: str) -> str:
    """Abrir el navegador: que no. Todo lo demás (leer la carpeta, las reglas de fuera): que sí (y en inglés, ``y``)."""
    if texto.startswith(("¿Abrir el reporte", "Open the report")):
        return "n"
    return "y" if "(Y/N)" in texto else "s"


@pytest.fixture(autouse=True)
def persona_delante(request, monkeypatch):
    """Las pruebas que no hablan de la terminal ni de las preguntas hacen como si una persona respondiera ``s`` a leer la carpeta y
    ``n`` a abrir el navegador. Desde la Historia 22 AgentReach no lee nada sin terminal interactiva ni permiso, y NO hay opción de
    la línea de comandos que lo salte: esto solo existe aquí, en las pruebas. Las que prueban la terminal y las preguntas
    se marcan con ``terminal_real`` y ven el comportamiento verdadero."""
    if request.node.get_closest_marker("terminal_real"):
        yield
        return
    from agentreach import cli

    monkeypatch.setattr(cli, "_interactivo", lambda: True)
    monkeypatch.setattr(cli, "_resumen_corto_por_defecto", False)  # estas pruebas comparan el reporte completo
    monkeypatch.setattr(cli, "_crear_reporte_por_defecto", False)  # y no escriben en la carpeta personal
    monkeypatch.setattr(cli, "_preguntar_por_defecto", _respuesta_de_prueba)
    monkeypatch.setattr(cli, "abrir_navegador", lambda ruta: True)
    yield


@pytest.fixture(autouse=True)
def tope_por_nombre(request, monkeypatch):
    """Historia 27: una credencial reconocida solo por su NOMBRE nunca pasa de «potencial» (``NIVEL_MAXIMO[TH-1]``). Las pruebas del
    motor de niveles (reglas, permisos, herencia, flujo de la terminal...) usan TH-1 como ejemplo de «comprobado»: llevan la marca
    ``sin_tope_por_nombre`` y ven el tope levantado, para seguir probando el motor. Las del tope mismo no la llevan."""
    if not request.node.get_closest_marker("sin_tope_por_nombre"):
        return
    from agentreach.contracts import Nivel, Tipo
    from agentreach.core import politica

    monkeypatch.setitem(politica.NIVEL_MAXIMO, Tipo.CREDENCIAL_EN_ARCHIVO, Nivel.COMPROBADO)
