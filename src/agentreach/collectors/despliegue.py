"""Scripts de despliegue reconocidos SOLO por el nombre del archivo (TH-9). Nunca se lee su contenido.

Un script como ``deploy.sh`` o ``deploy.ps1`` es algo que el agente podría lanzar y que publicaría
cambios. El nombre es lo único que se mira: no se abre el archivo. ``.github/workflows/deploy.yml``
no es un script (es un archivo de flujo de trabajo), ``.git`` y ``node_modules`` no se recorren, y
``redeploy.sh`` o ``deploy.md`` tampoco cuentan. El nivel máximo es hipótesis (decidido por Alex).
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from agentreach.collectors.enlaces import recorrer
from agentreach.contracts import (
    Ajeno,
    Etiqueta,
    Finding,
    Location,
    Motivo,
    MotivoNoRevisado,
    Nivel,
    NoRevisado,
    Plataforma,
    Postura,
    Proveedor,
    ReadOnlyFs,
    Ruta,
    Tipo,
)

_NOMBRE = re.compile(r"^(?:deploy|despliegue)(?:[._-].*)?\.(?:sh|ps1|bat|cmd)$", re.IGNORECASE)
_EXCLUIDAS = {".git", "node_modules"}


class DetectorDespliegue:
    """No lee nada de los archivos; ``no_revisados`` solo trae las carpetas que el recorrido no pudo recorrer."""

    def __init__(self, fs: ReadOnlyFs) -> None:
        self._fs = fs
        self.no_revisados: tuple[NoRevisado, ...] = ()

    def detectar(self, proyecto: Ruta) -> Iterable[Finding]:
        self.no_revisados = ()
        hallazgos: list[Finding] = []
        recorrido = recorrer(self._fs, proyecto)  # solo metadatos: no se abre nada
        # el tamaño no importa para un nombre: un script enorme sigue siendo un script de despliegue
        rutas = [a.ruta for a in recorrido.archivos if a.es_regular] + list(recorrido.omitidos)
        # carpetas que no se pudieron recorrer: no es "sin scripts". Un archivo enorme no cuenta: se reconoce por nombre.
        self.no_revisados = tuple(n for n in recorrido.no_revisados if n.motivo is not MotivoNoRevisado.ARCHIVO_DEMASIADO_GRANDE)
        for ruta in rutas:
            partes = ruta.replace("\\", "/").split("/")
            if _EXCLUIDAS & set(partes[:-1]) or not _NOMBRE.match(partes[-1]):
                continue
            hallazgos.append(
                Finding(
                    ubicacion=Location(Ruta(ruta)),
                    tipo=Tipo.SCRIPT_DE_DESPLIEGUE,
                    proveedor=Proveedor.DESPLIEGUE,
                    nivel=Nivel.HIPOTESIS,
                    motivo=Motivo.INDICIO_DEBIL,
                    ajeno_a_tarea=Ajeno.NO_DETERMINADO,
                    plataforma=Plataforma.NO_DETERMINADA,
                    agente=Etiqueta("sin-agente"),
                    postura=Postura.NO_DETERMINADA,
                )
            )
        return hallazgos
