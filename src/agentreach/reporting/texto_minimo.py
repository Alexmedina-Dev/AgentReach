"""Reporte de texto provisional (Historia 5b). La Historia 13 lo reemplaza por ``reporting/texto.py``.

Muestra ubicación, tipo, nivel (el real, de la Historia 11) y agente; nunca valores ni explicaciones.
"""

from __future__ import annotations

from collections.abc import Iterable

from agentreach.contracts import Finding, NoRevisado, Tipo

AVISO = (
    "Reporte provisional: sin explicaciones ni 'qué hacer' y sin el motivo del nivel; "
    "el reporte completo llega con la Historia 13"
)

NOMBRES_TIPO: dict[Tipo, str] = {
    Tipo.CREDENCIAL_EN_ARCHIVO: "credencial en archivo",
    Tipo.CLAVE_PRIVADA_SSH: "clave privada SSH",
    Tipo.CREDENCIALES_DE_NUBE: "credenciales de nube",
    Tipo.ENLACE_FUERA_DEL_PROYECTO: "enlace que sale del proyecto",
    Tipo.SECRETO_DE_ALTO_PODER: "secreto de alto poder",
    Tipo.VARIABLE_DE_ENTORNO: "variable de entorno",
}


def _ubicacion(h: Finding) -> str:
    linea = h.ubicacion.linea
    if isinstance(linea, int):
        return f"{h.ubicacion.ruta}:{linea}"
    return f"{h.ubicacion.ruta} (línea no determinada)"


def _clave(h: Finding) -> tuple[str, int, str]:
    linea = h.ubicacion.linea
    return (h.ubicacion.ruta, linea if isinstance(linea, int) else 2**31, h.tipo.value)


def formatear(
    hallazgos: Iterable[Finding], no_revisados: Iterable[NoRevisado], archivos_mirados: int
) -> str:
    """Texto completo del reporte. Orden estable: por ruta y línea. Todo texto sale limpio."""
    hallazgos = sorted(hallazgos, key=_clave)
    no_revisados = sorted(no_revisados, key=lambda n: (n.ruta, n.motivo.value))
    lineas = ["Hallazgos"]
    for h in hallazgos:
        nombre = NOMBRES_TIPO.get(h.tipo, h.tipo.name.lower().replace("_", " "))
        agente = f" [{h.agente}]" if h.agente and h.agente != "sin-agente" else ""
        lineas.append(f"  {_ubicacion(h)}  {h.tipo.value} {nombre}  {h.nivel.value}{agente}")
    if not hallazgos:
        lineas.append("  (ninguno)")
    lineas.append("No se pudo revisar")
    for n in no_revisados:
        lineas.append(f"  {n.ruta}  {n.motivo.value}")
    if not no_revisados:
        lineas.append("  (nada)")
    lineas.append(
        f"Resumen: {archivos_mirados} archivos mirados, {len(hallazgos)} hallazgos, "
        f"{len(no_revisados)} no revisados. {AVISO}"
    )
    return "\n".join(lineas)  # las rutas ya llegan limpias desde Location y NoRevisado


__all__ = ["AVISO", "NOMBRES_TIPO", "formatear"]
