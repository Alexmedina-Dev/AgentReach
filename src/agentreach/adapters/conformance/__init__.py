"""Kit de conformidad: las mismas pruebas para CUALQUIER adaptador (Claude Code, opencode, de terceros).

Se usa así::

    fallos = ejecutar_conformidad(fabrica, carpeta_temporal, archivo_configuracion=".claude/settings.json",
                                  clave_entorno=("env", "UNA_VARIABLE"))
    assert fallos == []

``fabrica(raiz, fs)`` crea el adaptador para el proyecto en ``raiz`` y lo obliga a leer con ``fs`` (el kit
le pasa un sistema de archivos que simula tuberías). El kit escribe archivos de configuración hostiles y
comprueba que el adaptador: (1) nunca lanza una excepción, (2) informa lo que no pudo leer como ``NoRevisado``
con el motivo correcto, y (3) nunca deja el valor de una variable de entorno en su resultado.
El adaptador debe ofrecer ``cargar(proyecto)`` y devolver algo con ``no_revisados`` (ver ``adapters.base``).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from agentreach.contracts import ArchivoNoLegible, ReadOnlyFs, Ruta
from agentreach.contracts.no_revisado import MotivoNoRevisado
from agentreach.infra.fs_solo_lectura import FsSoloLectura

CANARIO = "CANARIO-CONFORMIDAD-sk-9f8e7d6c5b4a3921"
_5_MB = 5 * 1024 * 1024

Fabrica = Callable[[Path, ReadOnlyFs], object]


class _FsConTuberia(FsSoloLectura):
    """Simula que el archivo de configuración es una tubería con nombre: leerlo lanza el motivo correcto."""

    def __init__(self, raiz: str, sufijo: str) -> None:
        super().__init__(raiz)
        self._sufijo = sufijo.replace("\\", "/")

    def leer_texto(self, ruta: Ruta) -> str:
        if ruta.replace("\\", "/").endswith(self._sufijo):
            raise ArchivoNoLegible("tuberia simulada", MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR)
        return super().leer_texto(ruta)


def _anidado(niveles: int) -> bytes:
    return ('{"a":' * niveles + "1" + "}" * niveles).encode("utf-8")


def _con_clave(clave: tuple[str, ...], valor: str) -> bytes:
    datos: dict = {}
    nodo = datos
    for k in clave[:-1]:
        nodo = nodo.setdefault(k, {})
    nodo[clave[-1]] = valor
    return json.dumps(datos).encode("utf-8")


def ejecutar_conformidad(fabrica: Fabrica, raiz: Path, *, archivo_configuracion: str,
                         clave_entorno: tuple[str, ...]) -> list[str]:
    """Lista de fallos de conformidad; vacía si el adaptador cumple todo."""
    if not clave_entorno:
        raise ValueError("clave_entorno no puede estar vacía")
    destino = archivo_configuracion.replace("\\", "/")
    if destino.startswith("/") or ".." in destino.split("/") or ":" in destino:
        raise ValueError("archivo_configuracion debe ser una ruta relativa dentro del proyecto")
    fallos: list[str] = []

    def escenario(nombre: str, contenido: bytes | None, esperados: set[MotivoNoRevisado] | None,
                  tuberia: bool = False, gigante: bool = False) -> None:
        proyecto = raiz / nombre
        archivo = proyecto / destino
        archivo.parent.mkdir(parents=True, exist_ok=True)
        if gigante:
            with archivo.open("wb") as f:
                f.truncate(_5_MB + 1)  # 5 MB más un byte
        elif contenido is not None:
            archivo.write_bytes(contenido)
        fs: ReadOnlyFs = _FsConTuberia(str(proyecto), destino) if tuberia else FsSoloLectura(str(proyecto))
        try:
            resultado = fabrica(proyecto, fs).cargar(Ruta(str(proyecto)))  # type: ignore[attr-defined]
        except Exception as error:  # noqa: BLE001 - justo lo que el kit debe detectar
            fallos.append(f"{nombre}: lanzó una excepción ({type(error).__name__}) en vez de informar un NoRevisado")
            return
        try:  # un adaptador que no cumple el contrato no tumba el kit: se anota como fallo
            if esperados is not None:
                motivos = {n.motivo for n in resultado.no_revisados}
                if not motivos & esperados:
                    fallos.append(f"{nombre}: esperaba un NoRevisado con motivo en {sorted(m.value for m in esperados)} "
                                  f"y salió {sorted(m.value for m in motivos)}")
            if CANARIO in repr(resultado):
                fallos.append(f"{nombre}: el valor de una variable de entorno salió en el resultado")
        except Exception as error:  # noqa: BLE001
            fallos.append(f"{nombre}: el resultado no cumple el contrato ({type(error).__name__})")

    escenario("gigante", None, {MotivoNoRevisado.ARCHIVO_DEMASIADO_GRANDE}, gigante=True)
    escenario("no-utf8", b"\xff\xfe\xfd no es utf-8", {MotivoNoRevisado.CODIFICACION_NO_UTF8})
    escenario("tuberia", b"{}", {MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR}, tuberia=True)
    escenario("json-65-niveles", _anidado(65), {MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA})
    escenario("json-roto", b"{ esto no es json",
              {MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE, MotivoNoRevisado.VERSION_NO_RECONOCIDA})
    escenario("valor-del-entorno", _con_clave(clave_entorno, CANARIO), None)
    return fallos
