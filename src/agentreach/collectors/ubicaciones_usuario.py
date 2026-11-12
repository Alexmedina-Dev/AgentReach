"""Ubicaciones sensibles del usuario: ``~/.ssh``, ``~/.aws`` y ``~/.npmrc`` (TH-2, TH-3, TH-1).

Reglas:

- Opt-in, apagado por defecto. Con el opt-in apagado NO se toca el disco: cada ubicación sale como
  ``NoRevisado`` con el motivo ``ubicacion_sensible_sin_activar``, nombrada ``~/.ssh`` (sin revelar
  la carpeta personal real), para que no se confunda con "sin hallazgos".
- Solo metadatos: nombre, tipo y permisos. Nunca se abre ni se lee un archivo.
- Antes de pedir tamaño o permisos de una entrada se comprueba su tipo: un enlace, una tubería o un
  dispositivo sale como ``NoRevisado`` (``no_es_archivo_regular``) y no se sigue.
- Lo que activa esto viene de la configuración (flag o archivo global), nunca del proyecto auditado:
  el parámetro ``proyecto`` de ``detectar`` no se usa.

El nivel de cada hallazgo es provisional (hipótesis): la Historia 11 lo calcula con los permisos
que quedan en ``permisos``.
"""

from __future__ import annotations

import os
from collections.abc import Iterable

from agentreach.config import Configuracion
from agentreach.contracts import (
    Ajeno,
    Certeza,
    Etiqueta,
    Finding,
    FsProbe,
    Location,
    Metadatos,
    Motivo,
    MotivoNoRevisado,
    Nivel,
    NoRevisado,
    PermisosArchivo,
    Plataforma,
    Postura,
    Proveedor,
    ReadOnlyFs,
    Ruta,
    Tipo,
)

# En ~/.ssh casi todo archivo regular puede ser una clave privada (los nombres no son estándar:
# ``github``, ``id_rsa.bak``). Solo se descartan los que se sabe que son públicos o de configuración.
_SSH_NO_SECRETOS = frozenset({
    "config", "known_hosts", "known_hosts.old", "authorized_keys", "authorized_keys2",
    "environment", "rc", "allowed_signers",
})


def _es_clave_privada_ssh(nombre: str) -> bool:
    n = nombre.lower()
    if n.endswith(".pub"):  # clave pública: HF-02, no se reporta
        return False
    return n not in _SSH_NO_SECRETOS


class DetectorUbicacionesUsuario:
    """``no_revisados`` y ``permisos`` quedan con lo de la última llamada a ``detectar``."""

    def __init__(self, fs: ReadOnlyFs, config: Configuracion, sonda: FsProbe | None = None) -> None:
        self._fs = fs
        self._config = config
        self._sonda = sonda
        self.no_revisados: tuple[NoRevisado, ...] = ()
        self.permisos: dict[str, PermisosArchivo] = {}

    def detectar(self, proyecto: Ruta) -> Iterable[Finding]:
        self.no_revisados = ()
        self.permisos = {}
        if not self._config.incluir_ubicaciones_sensibles:
            self.no_revisados = tuple(
                NoRevisado(Ruta(nombre), MotivoNoRevisado.UBICACION_SENSIBLE_SIN_ACTIVAR)
                for nombre in ("~/.ssh", "~/.aws", "~/.npmrc")
            )
            return []
        if not self._config.lectura_fuera:  # sin el permiso de segundo nivel no se mira nada de la carpeta personal, ni sus metadatos
            self.no_revisados = (NoRevisado(Ruta("~"), MotivoNoRevisado.SIN_PERMISO_FUERA_DEL_PROYECTO),)
            return []
        home = self._config.home or os.path.expanduser("~")
        hallazgos: list[Finding] = []
        pendientes: list[NoRevisado] = []
        if not os.path.isabs(home) or self._metadatos(Ruta(home), pendientes) is None:
            # sin carpeta personal utilizable: no es "sin hallazgos", es que no se pudo mirar
            self.no_revisados = (NoRevisado(Ruta("~"), MotivoNoRevisado.ARCHIVO_ILEGIBLE),)
            return []
        hallazgos += self._carpeta(os.path.join(home, ".ssh"), pendientes, _es_clave_privada_ssh,
                                   Tipo.CLAVE_PRIVADA_SSH, Proveedor.SSH)
        hallazgos += self._carpeta(os.path.join(home, ".aws"), pendientes, lambda n: n.lower() == "credentials",
                                   Tipo.CREDENCIALES_DE_NUBE, Proveedor.NUBE)
        hallazgos += self._archivo(os.path.join(home, ".npmrc"), pendientes,
                                   Tipo.CREDENCIAL_EN_ARCHIVO, Proveedor.CODIGO)
        self.no_revisados = tuple(pendientes)
        return hallazgos

    def _carpeta(self, ruta: str, pendientes: list[NoRevisado], es_secreto, tipo: Tipo, proveedor: Proveedor) -> list[Finding]:
        carpeta = self._metadatos(Ruta(ruta), pendientes)
        if carpeta is None:
            return []  # no existe (o ya se informó): nada que decir
        if carpeta.es_enlace or not carpeta.es_carpeta:
            pendientes.append(NoRevisado(carpeta.ruta, MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR))
            return []
        hallazgos: list[Finding] = []
        try:
            entradas = list(self._fs.listar(carpeta.ruta_real or carpeta.ruta))
        except OSError:
            pendientes.append(NoRevisado(carpeta.ruta, MotivoNoRevisado.ARCHIVO_ILEGIBLE))
            return []
        for entrada in entradas:
            if not self._es_archivo_regular(entrada, pendientes):
                continue  # el tipo se comprobó ANTES de pedir permisos
            if es_secreto(os.path.basename(entrada.ruta)):
                hallazgos.append(self._hallazgo(entrada, tipo, proveedor))
        return hallazgos

    def _archivo(self, ruta: str, pendientes: list[NoRevisado], tipo: Tipo, proveedor: Proveedor) -> list[Finding]:
        entrada = self._metadatos(Ruta(ruta), pendientes)
        if entrada is None:
            return []
        if entrada.es_carpeta and not entrada.es_enlace:  # un .npmrc que es carpeta: no se mira
            pendientes.append(NoRevisado(entrada.ruta, MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR))
            return []
        if not self._es_archivo_regular(entrada, pendientes):
            return []
        return [self._hallazgo(entrada, tipo, proveedor)]

    def _metadatos(self, ruta: Ruta, pendientes: list[NoRevisado]) -> Metadatos | None:
        try:
            return self._fs.metadatos(ruta)
        except OSError:
            pendientes.append(NoRevisado(ruta, MotivoNoRevisado.ARCHIVO_ILEGIBLE))
            return None

    @staticmethod
    def _es_archivo_regular(entrada: Metadatos, pendientes: list[NoRevisado]) -> bool:
        """True solo para un archivo regular. Un enlace o un archivo raro se informa; una carpeta se ignora."""
        if entrada.es_enlace:
            pendientes.append(NoRevisado(entrada.ruta, MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR))
            return False
        if entrada.es_carpeta:
            return False
        if not entrada.es_regular:  # tubería, dispositivo...
            pendientes.append(NoRevisado(entrada.ruta, MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR))
            return False
        return True

    def _hallazgo(self, entrada: Metadatos, tipo: Tipo, proveedor: Proveedor) -> Finding:
        if self._sonda is not None:
            real = entrada.ruta_real or entrada.ruta
            evaluar = getattr(self._sonda, "evaluar", None)  # una sonda sin ``evaluar`` no aporta permisos
            if evaluar is not None:
                try:
                    self.permisos[entrada.ruta] = evaluar(Ruta(real))
                except OSError:
                    pass  # sin permisos medidos: el hallazgo se mantiene; el nivel lo decide la Historia 11
        return Finding(
            ubicacion=Location(entrada.ruta),
            tipo=tipo,
            proveedor=proveedor,
            nivel=Nivel.HIPOTESIS,
            motivo=Motivo.NO_DETERMINADO,
            ajeno_a_tarea=Ajeno.NO_DETERMINADO,
            plataforma=Plataforma.NO_DETERMINADA,
            agente=Etiqueta("sin-agente"),
            postura=Postura.NO_DETERMINADA,
            certeza=Certeza.DUDOSA,  # solo metadatos: no se sabe qué hay dentro (HF-05: ~/.npmrc es potencial, no comprobado)
        )
