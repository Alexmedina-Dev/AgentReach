"""Sonda de permisos para Linux y macOS: modo y propietario desde los metadatos, sin abrir el archivo.

Sin pruebas obligatorias en el MVP. No lanza programas.
"""

from __future__ import annotations

import getpass
import os
import stat

from agentreach.contracts import PermisoLectura, PermisosArchivo, Ruta


def _entre_comillas(ruta: str) -> str:
    """Comillas simples a mano: dentro de ellas el intérprete no expande ``$``, comillas ni acentos graves."""
    return "'" + ruta.replace("'", "'\\''") + "'"


def _es_ambiguo(ruta: str) -> bool:
    """Un enlace en el camino se mide por su destino, y root lee todo: no se afirma con certeza."""
    try:
        return os.path.realpath(ruta) != os.path.abspath(ruta) or (hasattr(os, "geteuid") and os.geteuid() == 0)
    except OSError:
        return True


class SondaPosix:
    """Implementa ``FsProbe``: ``os.access`` consulta el permiso con la llamada del sistema, sin abrir."""

    def evaluar(self, ruta: Ruta) -> PermisosArchivo:
        try:
            usuario = getpass.getuser()
        except (OSError, KeyError):
            usuario = ""
        comando = "ls -l " + _entre_comillas(str(ruta))
        try:
            st = os.stat(ruta)
        except OSError:
            return PermisosArchivo(PermisoLectura.NO_DETERMINADO, False, True, usuario, comando)
        legible = os.access(ruta, os.R_OK)
        return PermisosArchivo(
            permiso=PermisoLectura.SI if legible else PermisoLectura.NO,
            abierto_a_todos=bool(st.st_mode & stat.S_IROTH),
            ambiguo=_es_ambiguo(ruta),
            usuario=usuario,
            comando_verificacion=comando,
            modo=oct(stat.S_IMODE(st.st_mode)),
            propietario=str(st.st_uid),
        )

    def permiso_lectura(self, ruta: Ruta) -> PermisoLectura:
        return self.evaluar(ruta).permiso
