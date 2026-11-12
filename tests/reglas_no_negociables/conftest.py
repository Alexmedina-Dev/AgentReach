"""Piezas comunes de las pruebas de las reglas no negociables (Historia 14).

Las cinco reglas: solo lectura (FR-1), sin red (FR-2), sin valores de secretos (FR-3), sin ejecutar programas externos y límites
duros de lectura (FR-26). Todas auditan el proyecto de prueba completo (``AGENTREACH_PROYECTO_PRUEBA``).

La vigilancia usa un **gancho de auditoría** de Python (``sys.addaudithook``): ve cualquier vía (``open``, ``io.FileIO``, ``_io``,
``os.*``, ``socket.*``, ``subprocess``...), no solo los nombres que se parchean. Un intento lanza ``ViolacionDeRegla``, que hereda de
``BaseException`` para que ningún ``except Exception`` del producto la pueda tragar, y además queda anotado en ``INTENTOS``: la
prueba falla al terminar si la lista no está vacía.
"""

from __future__ import annotations

import hashlib
import io
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from agentreach import cli

AHORA = datetime(2026, 11, 9, 16, 40)
MARCADOR = re.compile(r"cnr0\d\d", re.IGNORECASE)  # cada secreto falso del proyecto de prueba lleva uno (CNR001 a CNR024)


class ViolacionDeRegla(BaseException):
    """Un intento de escribir, usar la red o lanzar un programa. ``BaseException``: ningún ``except Exception`` la traga."""


INTENTOS: list[str] = []
ACTIVAS: set[str] = set()
PERMITIDAS: list[str] = []  # carpetas donde SÍ se puede escribir mientras la vigilancia está activa (p. ej. AgentReach-reportes)


def _permitida(ruta) -> bool:
    try:
        destino = os.path.normcase(os.path.abspath(os.fsdecode(ruta)))
    except (TypeError, ValueError):
        return False
    return any(destino == p or destino.startswith(p + os.sep) for p in PERMITIDAS)

_EVENTOS_ESCRITURA = {
    "os.mkdir", "os.remove", "os.rename", "os.rmdir", "os.chmod", "os.truncate", "os.symlink", "os.link", "os.utime", "os.chown",
    "shutil.copyfile", "shutil.copymode", "shutil.copystat", "shutil.copytree", "shutil.move", "shutil.rmtree", "tempfile.mkstemp",
    "tempfile.mkdtemp", "os.mkfifo", "os.mknod", "winreg.SetValue", "winreg.CreateKey",
}
_EVENTOS_PROCESO = {"subprocess.Popen", "os.system", "os.exec", "os.spawn", "os.posix_spawn", "os.startfile", "os.fork",
                    "msvcrt.open_osfhandle"}
_ESCRIBE = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND


def _gancho(evento: str, args: tuple) -> None:
    if not ACTIVAS:
        return
    motivo = None
    if "escritura" in ACTIVAS:
        if evento in _EVENTOS_ESCRITURA:
            if not (args and isinstance(args[0], (str, bytes, os.PathLike)) and _permitida(args[0])):
                motivo = f"escritura: {evento}"
        elif (evento == "open" and isinstance(args[0], (str, bytes, os.PathLike)) and str(args[0]) != os.devnull
              and not _permitida(args[0])):
            modo, banderas = (args[1] if len(args) > 1 else None), (args[2] if len(args) > 2 else 0)
            if (isinstance(banderas, int) and banderas & _ESCRIBE) or (isinstance(modo, str) and any(c in modo for c in "wax+")):
                motivo = f"escritura: open {args[0]!r} modo={modo!r}"
    if motivo is None and "red" in ACTIVAS and (evento.startswith("socket.") or evento in ("urllib.Request", "http.client.connect")):
        motivo = f"red: {evento}"
    if motivo is None and "proceso" in ACTIVAS and evento in _EVENTOS_PROCESO:
        motivo = f"proceso: {evento}"
    if motivo is not None:
        INTENTOS.append(motivo)
        raise ViolacionDeRegla(motivo)


sys.addaudithook(_gancho)  # un gancho no se puede quitar: queda inerte mientras ACTIVAS esté vacío


def _vigilar(monkeypatch, regla: str):
    INTENTOS.clear()
    ACTIVAS.add(regla)
    yield
    ACTIVAS.discard(regla)
    intentos, _ = list(INTENTOS), INTENTOS.clear()
    assert not intentos, f"se violó una regla no negociable: {intentos}"


@pytest.fixture
def raiz_prueba() -> Path:
    raiz = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")
    if not raiz or not (Path(raiz) / "proyecto").is_dir():
        mensaje = "AGENTREACH_PROYECTO_PRUEBA no apunta al proyecto de prueba"
        if os.environ.get("CI") or os.environ.get("AGENTREACH_EXIGIR_PRUEBAS"):
            pytest.fail(mensaje)  # en CI estas pruebas son bloqueantes: saltarlas en silencio las vaciaría
        pytest.skip(mensaje)
    return Path(raiz)


class Terminal(io.StringIO):
    """No es una terminal: así el reporte sale sin banner ni color y se puede comparar byte a byte."""

    encoding = "utf-8"

    def isatty(self) -> bool:
        return False


def auditoria_completa(raiz: Path, *extra: str) -> tuple[int, str, str]:
    """``agentreach`` sobre la carpeta contenedora (trampas incluidas) y la carpeta personal falsa, con el opt-in."""
    salida, error = Terminal(), Terminal()
    anterior = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = salida, error
    try:
        codigo = cli.main(
            [str(raiz), "--home", str(raiz / "home-falso"), "--incluir-ubicaciones-sensibles", "--ancho", "100", *extra],
            ahora=lambda: AHORA,
        )
    finally:
        sys.stdout, sys.stderr = anterior
    return codigo, salida.getvalue(), error.getvalue()


def instantanea(raiz: Path) -> dict[str, tuple]:
    """Cada archivo y carpeta con tamaño, marcas de tiempo, atributos de Windows y huella de contenido (sin seguir enlaces)."""
    resultado: dict[str, tuple] = {}
    pendientes = [raiz]
    while pendientes:
        carpeta = pendientes.pop()
        with os.scandir(carpeta) as entradas:
            for e in entradas:
                st = e.stat(follow_symlinks=False)
                relativa = os.path.relpath(e.path, raiz)
                atributos = getattr(st, "st_file_attributes", 0)
                es_carpeta = e.is_dir(follow_symlinks=False) and not atributos & 0x400  # una junction no se recorre
                if es_carpeta:
                    resultado[relativa] = ("carpeta", st.st_mtime_ns, st.st_ctime_ns, atributos)
                    pendientes.append(Path(e.path))
                    continue
                huella = None
                if e.is_file(follow_symlinks=False):
                    try:
                        huella = hashlib.sha256(Path(e.path).read_bytes()).hexdigest()
                    except OSError:
                        huella = "ilegible"  # p. ej. PP-03: lectura negada por la ACL
                resultado[relativa] = ("archivo", st.st_size, st.st_mtime_ns, st.st_ctime_ns, atributos, huella)
    return resultado


@pytest.fixture
def tempdir_vacio(tmp_path: Path, monkeypatch) -> Path:
    """Los archivos temporales irían aquí: debe seguir vacío (AgentReach no crea nada fuera del sistema de archivos que mira)."""
    carpeta = tmp_path / "temporales"
    carpeta.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(carpeta))
    return carpeta


@pytest.fixture
def sin_escrituras(monkeypatch):
    """Cualquier intento de escribir, crear, borrar, renombrar o cambiar permisos falla la prueba en el acto."""
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    yield from _vigilar(monkeypatch, "escritura")


@pytest.fixture
def escritura_solo_en(sin_escrituras):
    """Como ``sin_escrituras``, pero deja escribir dentro de las carpetas que la prueba indique (y en ninguna otra parte)."""
    PERMITIDAS.clear()

    def permitir(*carpetas) -> None:
        PERMITIDAS.extend(os.path.normcase(os.path.abspath(str(c))) for c in carpetas)

    yield permitir
    PERMITIDAS.clear()


@pytest.fixture
def sin_red(monkeypatch):
    """Crear un socket, resolver un nombre o conectar falla la prueba en el acto."""
    yield from _vigilar(monkeypatch, "red")


@pytest.fixture
def sin_procesos(monkeypatch):
    """Todo lo que lanza un programa externo falla la prueba en el acto."""
    yield from _vigilar(monkeypatch, "proceso")
