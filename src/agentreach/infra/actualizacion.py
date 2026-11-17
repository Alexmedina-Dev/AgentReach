"""Aviso de versión nueva (Historia 31). Es la ÚNICA parte del producto que usa internet, y nunca durante la revisión.

Reglas (decisión de Alex):
- Solo la llama la línea de comandos, al abrir, como máximo cada 15 días y nunca con ``--formato``, ``--salida`` ni sin terminal.
- Solo HTTPS, con ``github.com`` como dirección fija. La única redirección que se sigue es la que GitHub mismo hace de ``/raw/`` a su
  servidor de archivos (``raw.githubusercontent.com``): cualquier otra se rechaza.
- No envía nada de la persona ni de su carpeta: solo una petición GET con ``User-Agent: AgentReach/<versión>``. Sin cookies ni claves.
- Lee un trozo pequeño de ``pyproject.toml`` y valida el número con una expresión estricta.
- Sin internet, con un error o con algo que no se entiende: devuelve ``None`` sin fallar.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

__all__ = ["COMANDO", "REPOSITORIO", "URL_VERSION", "consultar", "es_mas_nueva", "instalado_con_uv", "instalar", "version_valida"]

REPOSITORIO = "git+https://github.com/Alexmedina-Dev/AgentReach"
COMANDO = ("uv", "tool", "install", "--reinstall", REPOSITORIO)  # el comando exacto que se muestra y, con permiso, se ejecuta
URL_VERSION = "https://github.com/Alexmedina-Dev/AgentReach/raw/main/pyproject.toml"
_HOST_FIJO = "github.com"
_HOST_DE_ARCHIVOS = "raw.githubusercontent.com"  # adonde GitHub redirige sus /raw/ (el mismo propietario, también HTTPS)
_LIMITE_BYTES = 65536
_VERSION = re.compile(r"\A[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,4}(?:\.dev[0-9]{1,4})?\Z")
_LINEA = re.compile(r'^version\s*=\s*"([^"\r\n]{1,32})"\s*$', re.MULTILINE)
_NUCLEO = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")


def version_valida(texto: str) -> bool:
    return bool(_VERSION.match(texto))


def _nucleo(texto: str) -> tuple[int, int, int] | None:
    encontrada = _NUCLEO.match(texto)
    return tuple(int(x) for x in encontrada.group(0).split(".")) if encontrada else None  # type: ignore[return-value]


def es_mas_nueva(ultima: str, actual: str) -> bool:
    """``True`` si ``ultima`` (ya validada) es mayor que ``actual`` en su núcleo ``X.Y.Z``. Si no se entiende alguna, ``False``."""
    a, b = _nucleo(ultima), _nucleo(actual)
    return a is not None and b is not None and version_valida(ultima) and a > b


class _SoloRedireccionDeGitHub(urllib.request.HTTPRedirectHandler):
    """Solo HTTPS, y solo de github.com a su propio servidor de archivos (una vez). Cualquier otro destino se rechaza."""

    max_redirections = 1

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        destino = urllib.parse.urlsplit(newurl)
        if destino.scheme != "https" or destino.hostname not in (_HOST_FIJO, _HOST_DE_ARCHIVOS) or destino.username or destino.port not in (None, 443):
            raise urllib.error.HTTPError(newurl, code, "redirección no permitida", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def consultar(version_actual: str, tiempo: float = 4.0) -> str | None:
    """El número de la última versión (el de ``pyproject.toml`` en ``main``), o ``None`` sin internet, con un error o con un número que no se entiende."""
    try:
        abridor = urllib.request.build_opener(_SoloRedireccionDeGitHub)
        peticion = urllib.request.Request(URL_VERSION, headers={"User-Agent": f"AgentReach/{version_actual}"}, method="GET")
        with abridor.open(peticion, timeout=tiempo) as respuesta:
            if respuesta.status != 200 or urllib.parse.urlsplit(respuesta.geturl()).scheme != "https":
                return None
            cuerpo = respuesta.read(_LIMITE_BYTES).decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001 - sin internet o con cualquier error: en silencio
        return None
    encontrada = _LINEA.search(cuerpo)
    if not encontrada:
        return None
    numero = encontrada.group(1)
    return numero if version_valida(numero) else None


def instalado_con_uv() -> bool:
    """¿AgentReach corre desde un entorno de ``uv tool`` (…/uv/tools/agentreach)? Solo en ese caso se intenta reinstalar."""
    partes = [p.lower() for p in os.path.normpath(sys.prefix).split(os.sep)]
    return any(partes[i:i + 3] == ["uv", "tools", "agentreach"] for i in range(len(partes) - 2)) and shutil.which("uv") is not None


def instalar(tiempo: float = 300.0) -> bool:
    """Ejecuta ``uv tool install --reinstall …`` sin shell y con tiempo límite. ``True`` si terminó bien."""
    uv = shutil.which("uv")
    if uv is None:
        return False
    try:
        terminado = subprocess.run([uv, *COMANDO[1:]], shell=False, timeout=tiempo, capture_output=True, stdin=subprocess.DEVNULL, check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    return terminado.returncode == 0
