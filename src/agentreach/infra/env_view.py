"""Vista del entorno del proceso: SOLO los nombres de las variables, nunca sus valores.

Se recorre la lista de nombres de ``os.environ``. Este módulo no usa ``items``, ``values``, ``copy``,
``get`` ni ``getenv``: el valor de una variable nunca se pide, así que no puede acabar en un objeto.
"""

from __future__ import annotations

import os


class EnvVistaProceso:
    """Implementa el puerto ``EnvView`` con el entorno real del proceso."""

    def nombres(self) -> list[str]:
        return list(os.environ)  # iterar el entorno entrega solo las claves
