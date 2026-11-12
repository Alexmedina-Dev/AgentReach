"""Compuerta del reporte (FR-23, FR-3): lo único que llega al texto es lo que esta pieza deja pasar.

``preparar`` recibe el resultado de la auditoría, corre la autocomprobación (reabre los archivos citados) y entrega
``DatosReporte``: vistas con una lista blanca de campos. Una vista no tiene dónde guardar un valor de secreto ni el
texto de un archivo, y las rutas ya van como texto visible (relativas, con ``/`` y con los caracteres peligrosos
escritos). ``texto.py`` solo conoce estas vistas, nunca un ``Finding``.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from agentreach.contracts import (
    Ajeno,
    Finding,
    Location,
    Motivo,
    MotivoNoRevisado,
    Nivel,
    NoRevisado,
    Plataforma,
    Postura,
    Proveedor,
    Tipo,
    fuente_verificada,
)
from agentreach.core.autocomprobacion import RazonCorreccion, autocomprobar
from agentreach.core.nivel import Hechos
from agentreach.infra.lectura_segura import leer_seguro
from agentreach.reporting.limpieza import escribir_peligrosos

__all__ = ["AgenteConfiguradoVista", "CausaVista", "CorreccionVista", "DatosReporte", "HallazgoVista", "NoRevisadoVista", "RastroSinDecidirVista", "ReglaVista", "codigo_de_salida", "preparar", "ruta_visible"]

_SALTO = re.compile(r"\r\n|\r|\n")


@dataclass(frozen=True, slots=True)
class HallazgoVista:
    ruta: str  # visible: relativa a la carpeta, con "/" y con los caracteres peligrosos escritos
    linea: int | None  # None: línea no determinada
    tipo: Tipo
    proveedor: Proveedor
    nivel: Nivel
    motivo: Motivo
    ajeno: Ajeno
    plataforma: Plataforma
    agente: str | None
    postura: Postura
    regla: str | None  # "archivo:línea" de la regla que decide, visible
    fuente_verificada: bool


@dataclass(frozen=True, slots=True)
class NoRevisadoVista:
    ruta: str
    motivo: MotivoNoRevisado


@dataclass(frozen=True, slots=True)
class ReglaVista:
    plataforma: Plataforma
    postura: Postura
    herramienta: str
    ubicacion: str


@dataclass(frozen=True, slots=True)
class CausaVista:
    """Por qué un nivel puede salir «no determinado»: el archivo y la CLAVE que AgentReach no interpreta (nunca un valor)."""

    plataforma: Plataforma
    ruta: str
    motivo: MotivoNoRevisado
    clave: str = ""


@dataclass(frozen=True, slots=True)
class AgenteConfiguradoVista:
    """Un agente CONFIGURADO (no «ejecutado»): los archivos que lo muestran (rutas limpias, sin contenido) y con cuánta confianza."""

    id: str  # el del catálogo (``claude-code``)
    nombre: str
    confianza: str  # "high", "potential" o "hypothesis" (esta última se muestra como «indicio»)
    marco: bool  # un marco (gentle-ai, BMAD): está instalado SOBRE otros agentes
    sobre: tuple[str, ...]  # nombres de los agentes sobre los que está el marco
    analizado: bool  # AgentReach analiza su alcance; si no, solo se dice que está configurado
    evidencia: tuple[tuple[str, str], ...]  # (ámbito: proyecto|usuario|entorno, ruta visible o nombre de la variable)


@dataclass(frozen=True, slots=True)
class RastroSinDecidirVista:
    """Un rastro compartido (``AGENTS.md``) que no dice cuál de varios agentes lo usa."""

    ruta: str
    candidatos: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CorreccionVista:
    """Un hallazgo que la autocomprobación corrigió: cuál es (tipo y ruta, nunca valores) y de qué nivel a cuál pasó."""

    tipo: Tipo
    ruta: str  # visible
    razon: RazonCorreccion
    nivel_antes: Nivel | None
    nivel_despues: Nivel | None


@dataclass(frozen=True, slots=True)
class DatosReporte:
    carpeta: str  # la ruta absoluta, ya visible
    fecha: datetime
    archivos_mirados: int
    hallazgos: tuple[HallazgoVista, ...]
    no_revisados: tuple[NoRevisadoVista, ...]
    reglas: tuple[ReglaVista, ...]
    limpieza_de_entorno: frozenset[Plataforma]
    esquemas: tuple[tuple[Plataforma, str], ...]  # opencode: «1.x», «2.x» o «ambiguo»
    correcciones: tuple[CorreccionVista, ...]
    hallazgos_corregidos: int
    hubo_nombres_escritos: bool
    codigo_de_salida: int
    configurados: tuple[AgenteConfiguradoVista, ...] = ()  # agentes con archivos de configuración (no es «ejecutado»)
    causas: tuple[CausaVista, ...] = ()  # por qué hay niveles «no determinado» (archivo y clave, sin valores)
    sin_decidir: tuple[RastroSinDecidirVista, ...] = ()  # rastros compartidos que no permiten decir qué agente es


class LectorSeguro:
    """Reabre archivos con ``leer_seguro`` (tope, sin seguir enlaces, UTF-8 estricto). Solo para la autocomprobación."""

    def existe(self, ruta: str) -> bool:
        return os.path.lexists(ruta)

    def lineas(self, ruta: str) -> list[str] | None:
        texto = leer_seguro(ruta)  # type: ignore[arg-type]
        if isinstance(texto, NoRevisado):
            return None
        return _SALTO.split(texto.removeprefix(chr(0xFEFF)))


def ruta_visible(ruta: str, carpeta: str, home: str | None) -> tuple[str, bool]:
    """Ruta para mostrar: relativa a la carpeta con ``/``, ``~`` si está en la carpeta personal, o tal cual. Con peligros escritos."""
    texto = ruta
    if os.path.isabs(ruta):
        for base, prefijo in ((carpeta, ""), (home, "~/")):
            if not base:
                continue
            try:
                a, b = os.path.normcase(os.path.abspath(ruta)), os.path.normcase(os.path.abspath(base))
                if os.path.commonpath([a, b]) == b:
                    resto = os.path.relpath(os.path.abspath(ruta), os.path.abspath(base))
                    resto = resto.replace("\\", "/") if os.sep == "\\" else resto  # en POSIX una barra invertida es parte del nombre
                    texto = prefijo + ("" if resto == "." else resto)
                    if not prefijo and texto.startswith("~"):
                        texto = "./" + texto  # un "~" del proyecto no se confunde con la carpeta personal
                    break
            except ValueError:  # otra unidad de disco
                continue
    return escribir_peligrosos(texto)


def codigo_de_salida(hallazgos: tuple[Finding, ...] | tuple[HallazgoVista, ...], hay_no_revisados: bool, estricto: bool) -> int:
    """0 sin comprobados; 1 con alguno (o, con ``--estricto``, con entradas no revisadas). El 2 y el 3 los pone el comando."""
    if any(h.nivel is Nivel.COMPROBADO for h in hallazgos):
        return 1
    return 1 if estricto and hay_no_revisados else 0


def preparar(
    resultado,
    carpeta: str,
    *,
    ahora: datetime,
    estricto: bool = False,
    home: str | None = None,
    lector: object | None = None,
    agente: Plataforma | None = None,
) -> DatosReporte:
    """Autocomprueba y arma las vistas. ``resultado`` es un ``ResultadoAuditoria``."""
    carpeta = os.path.abspath(carpeta)
    hechos: Mapping[Finding, Hechos] = getattr(resultado, "hechos", {})
    revisado = autocomprobar(resultado.hallazgos, hechos, lector or LectorSeguro())  # type: ignore[arg-type]
    visibles = [c for c in revisado.correcciones if agente is None or c.plataforma in (agente, Plataforma.NO_DETERMINADA)]
    escritos = False

    def ver(ubicacion: Location) -> str:
        nonlocal escritos
        texto, cambio = ruta_visible(str(ubicacion.ruta_real or ubicacion.ruta), carpeta, home)
        escritos = escritos or cambio
        return texto

    hallazgos: list[HallazgoVista] = []
    for h in revisado.hallazgos:
        if agente is not None and h.plataforma not in (agente, Plataforma.NO_DETERMINADA):
            continue  # --agente: nada de los otros agentes
        linea = h.ubicacion.linea if isinstance(h.ubicacion.linea, int) else None
        regla = f"{ver(h.regla)}:{h.regla.linea}" if h.regla and isinstance(h.regla.linea, int) else (ver(h.regla) if h.regla else None)
        hallazgos.append(HallazgoVista(
            ver(h.ubicacion), linea, h.tipo, h.proveedor, h.nivel, h.motivo, h.ajeno_a_tarea, h.plataforma,
            h.agente, h.postura, regla, fuente_verificada(h.tipo),
        ))
    no_revisados: list[NoRevisadoVista] = []
    for n in resultado.no_revisados:
        texto, cambio = ruta_visible(str(n.ruta_real or n.ruta), carpeta, home)
        escritos = escritos or cambio
        vista = NoRevisadoVista(texto, n.motivo)
        if vista not in no_revisados:  # lo que se cuenta es lo que se lista
            no_revisados.append(vista)
    reglas: list[ReglaVista] = []
    limpieza: set[Plataforma] = set()
    esquemas: list[tuple[Plataforma, str]] = []
    causas: list[CausaVista] = []
    for plataforma, contexto in getattr(resultado, "contextos", ()):
        if agente is not None and plataforma is not agente:
            continue
        if contexto.limpieza_de_entorno:
            limpieza.add(plataforma)
        for c in getattr(contexto, "causas_no_determinado", ()):
            if c.motivo is MotivoNoRevisado.UBICACION_SENSIBLE_SIN_ACTIVAR:
                continue
            texto_c, cambio_c = ruta_visible(str(c.ruta_real or c.ruta), carpeta, home)
            escritos = escritos or cambio_c
            causa = CausaVista(plataforma, texto_c, c.motivo, c.clave)
            if causa not in causas:
                causas.append(causa)
        if getattr(contexto, "esquema", ""):
            esquemas.append((plataforma, contexto.esquema))
        for r in contexto.reglas:
            postura = {"allow": Postura.ALLOW, "ask": Postura.ASK, "deny": Postura.DENY}.get(r.accion, Postura.NO_DETERMINADA)
            linea = r.ubicacion.linea
            lugar = ver(r.ubicacion) + (f":{linea}" if isinstance(linea, int) else "")
            herramienta, cambio_h = escribir_peligrosos(str(r.herramienta))  # la clave viene de un archivo: se escribe, no se imprime
            escritos = escritos or cambio_h
            reglas.append(ReglaVista(plataforma, postura, herramienta, lugar))
    configurados = []
    por_id = {a.id: a for a in getattr(resultado, "agentes", ())}
    filtro = {Plataforma.CLAUDE_CODE: "claude-code", Plataforma.OPENCODE: "opencode"}.get(agente) if agente is not None else None
    for a in por_id.values():
        if filtro is not None and a.id != filtro and not (a.marco and filtro in a.sobre):
            continue  # --agente: solo ese agente (y los marcos instalados sobre él)
        pruebas = []
        for e in a.evidencia:
            if e.ambito == "entorno":
                texto_e, cambio_e = escribir_peligrosos(e.ruta)
            else:
                texto_e, cambio_e = ruta_visible(e.ruta, carpeta, home)
            escritos = escritos or cambio_e
            pruebas.append((e.ambito, texto_e))
        configurados.append(AgenteConfiguradoVista(
            a.id, escribir_peligrosos(a.nombre)[0], a.confianza.value, a.marco, tuple(por_id[s].nombre for s in a.sobre if s in por_id),
            a.analizado, tuple(pruebas)))
    sin_decidir = []
    for r in getattr(resultado, "sin_decidir", ()):
        texto_r, cambio_r = ruta_visible(r.ruta, carpeta, home)
        escritos = escritos or cambio_r
        sin_decidir.append(RastroSinDecidirVista(texto_r, tuple(r.candidatos)))
    correcciones: list[CorreccionVista] = []
    for c in visibles:
        vista_c = CorreccionVista(c.tipo, ver(c.ubicacion), c.razon, c.nivel_antes, c.nivel_despues)
        if not any((v.tipo, v.ruta, v.nivel_antes, v.nivel_despues) == (vista_c.tipo, vista_c.ruta, vista_c.nivel_antes, vista_c.nivel_despues)
                   for v in correcciones):  # un hallazgo corregido por dos reglas es un solo aviso
            correcciones.append(vista_c)
    carpeta_visible, cambio = escribir_peligrosos(carpeta)
    return DatosReporte(
        carpeta=carpeta_visible,
        fecha=ahora,
        archivos_mirados=resultado.archivos_mirados,
        hallazgos=tuple(hallazgos),
        no_revisados=tuple(no_revisados),
        reglas=tuple(reglas),
        limpieza_de_entorno=frozenset(limpieza),
        esquemas=tuple(esquemas),
        correcciones=tuple(correcciones),
        hallazgos_corregidos=len({(c.ubicacion, c.tipo) for c in visibles}),
        hubo_nombres_escritos=escritos or cambio,
        codigo_de_salida=codigo_de_salida(tuple(hallazgos), bool(no_revisados), estricto),
        configurados=tuple(configurados),
        sin_decidir=tuple(sin_decidir),
        causas=tuple(causas),
    )
