"""Reporte HTML estático (Historia 19): rellena ``plantilla_reporte.html`` con los datos de la compuerta.

Solo biblioteca estándar. Recibe ``DatosReporte`` (lo que deja pasar ``gate.py``): nunca un ``Finding`` ni un archivo del proyecto,
así que el JSON no puede llevar un valor de secreto ni una ruta real. La forma del JSON es la de ``docs/reporte-html/esquema-datos.md``
(versión 1); los textos para personas salen de los catálogos fijos en español e inglés (nunca de un modelo de lenguaje). El resultado
es un solo archivo, sin recursos externos y con una política de contenido que prohíbe la red.
"""

from __future__ import annotations

import json
from importlib import resources

from agentreach.contracts import (
    Ajeno,
    Idioma,
    Motivo,
    Nivel,
    Plataforma,
    Postura,
    Tipo,
    texto_de_motivo,
)
from agentreach.core.catalogo_explicaciones import (
    AJENO,
    LIMITES,
    LIMITES_TAMBIEN,
    POSTURA,
    PROVEEDOR,
    TITULO_MOTIVO,
    TITULO_TIPO,
    Tono,
    como_resolver,
    que_hacer,
    que_significa,
)
from agentreach.core.catalogo_terminos import FICHAS, etiquetas, nombre
from agentreach.reporting.gate import AgenteConfiguradoVista, DatosReporte, HallazgoVista
from agentreach.reporting.texto import aviso_de_secretos

__all__ = ["MARCADOR", "MAX_BYTES", "MAX_HALLAZGOS_POR_AGENTE", "generar_html"]

MARCADOR = "__AGENTREACH_" + "DATA__"  # el marcador de la plantilla (aquí partido, para que no aparezca dos veces en el código)
MAX_HALLAZGOS_POR_AGENTE = 20_000
MAX_BYTES = 20 * 1024 * 1024
VERSION_ESQUEMA = 1
_NIVEL = {Nivel.COMPROBADO: "verified", Nivel.POTENCIAL: "potential", Nivel.HIPOTESIS: "hypothesis"}
_PREFIJO = {Plataforma.CLAUDE_CODE: "cc", Plataforma.OPENCODE: "oc", Plataforma.NO_DETERMINADA: "na"}
_ID = {Plataforma.CLAUDE_CODE: "claude_code", Plataforma.OPENCODE: "opencode", Plataforma.NO_DETERMINADA: "none"}
_NOMBRE = {
    Plataforma.CLAUDE_CODE: "Claude Code",
    Plataforma.OPENCODE: "opencode",
    Plataforma.NO_DETERMINADA: {"en": "Not tied to a specific agent", "es": "Sin agente específico"},
}


class ReporteDemasiadoGrande(ValueError):
    """Se pasó de 20 000 hallazgos por agente o de 20 MB: no se escribe un reporte parcial (código de salida 3)."""


def _i18n(texto) -> dict[str, str]:
    """``{"en": ..., "es": ...}`` a partir de una función que da el texto en cada idioma."""
    return {"en": texto(Idioma.EN), "es": texto(Idioma.ES)}


def _clave_de_texto(h: HallazgoVista) -> str:
    """La clave de ``catalog.texts``: el código del tipo; el de TH-17 cambia con «ajeno a la tarea» (con «no» sirve el código solo)."""
    if h.tipo is Tipo.SECRETO_DE_ALTO_PODER and h.ajeno is not Ajeno.NO:
        return f"{h.tipo.value}/{h.ajeno.value}"
    return h.tipo.value


def _orden(h: HallazgoVista) -> tuple:
    return (h.nivel.prioridad, h.ruta, h.linea is None, h.linea or 0, int(h.tipo.value.split("-")[1]))


def _hallazgo(h: HallazgoVista, indice: int) -> dict:
    return {
        "id": f"{_PREFIJO[h.plataforma]}-{indice}",
        "path": h.ruta,
        "line": h.linea,
        "type": h.tipo.value,
        "provider": h.proveedor.value,
        "level": _NIVEL[h.nivel],
        "reason": h.motivo.value,
        "unrelated": h.ajeno.value,
        "agent": None if h.agente in (None, "sin-agente") else h.agente,
        "posture": h.postura.value,
        "rule": h.regla,
        "source_verified": h.fuente_verificada,
        "text": _clave_de_texto(h),
    }


def _agentes(d: DatosReporte, agente: Plataforma | None) -> list[dict]:
    entradas: list[dict] = []
    orden = (Plataforma.CLAUDE_CODE, Plataforma.OPENCODE, Plataforma.NO_DETERMINADA)
    for plataforma in orden:
        if agente is not None and plataforma not in (agente, Plataforma.NO_DETERMINADA):
            continue  # --agente: solo ese agente (y lo que no depende de ninguno)
        propios = sorted((h for h in d.hallazgos if h.plataforma is plataforma), key=_orden)
        if plataforma is Plataforma.NO_DETERMINADA and not propios:
            continue  # «sin agente específico» solo sale si tiene hallazgos
        if len(propios) > MAX_HALLAZGOS_POR_AGENTE:
            raise ReporteDemasiadoGrande(f"más de {MAX_HALLAZGOS_POR_AGENTE} hallazgos de un agente")
        reglas = [
            {
                "posture": r.postura.value if r.postura in (Postura.ALLOW, Postura.ASK, Postura.DENY) else "no_determinada",
                "tool": r.herramienta,
                "location": r.ubicacion,
            }
            for r in d.reglas
            if r.plataforma is plataforma
        ]
        entradas.append({
            "id": _ID[plataforma],
            "name": _NOMBRE[plataforma],
            "env_cleaning": plataforma in d.limpieza_de_entorno,
            "rules": reglas,
            "not_determined": [  # por qué hay niveles «no determinado»: archivo y clave que no se interpreta (nunca un valor)
                {"path": c.ruta, "key": c.clave, "reason": c.motivo.value} for c in d.causas if c.plataforma is plataforma
            ] if any(h.plataforma is plataforma and h.motivo is Motivo.NO_DETERMINADO for h in d.hallazgos) else [],
            "findings": [_hallazgo(h, i) for i, h in enumerate(propios)],
        })
    return entradas


_AMBITO = {"proyecto": "project", "usuario": "user", "entorno": "environment"}


def _configurados(d: DatosReporte) -> list[dict]:
    """Agentes CONFIGURADOS («configurado», nunca «ejecutado»), cada uno con los archivos que lo muestran y con cuánta confianza."""
    def entrada(c: AgenteConfiguradoVista) -> dict:
        return {
            "id": c.id.replace("-", "_"),
            "name": c.nombre,
            "kind": "framework" if c.marco else "agent",
            "confidence": c.confianza,
            "analyzed": c.analizado,
            "on": list(c.sobre),
            "evidence": [{"scope": _AMBITO.get(a, "project"), "path": r} for a, r in c.evidencia],
        }

    return [entrada(c) for c in d.configurados]


def _catalogo(d: DatosReporte, tono: Tono) -> dict:
    """Solo las entradas que se usan (no los 20 tipos si hay 3): con cientos de hallazgos del mismo tipo el archivo no se multiplica."""
    usados = list(d.hallazgos)
    tipos = {h.tipo for h in usados}
    return {
        "types": {t.value: {"title": _i18n(lambda i, t=t: TITULO_TIPO[t][i])} for t in sorted(tipos, key=lambda t: t.value)},
        "texts": {
            _clave_de_texto(h): {
                "meaning": _i18n(lambda i, h=h: que_significa(h.tipo, h.ajeno, i, tono)),
                "what_to_do": _i18n(lambda i, h=h: que_hacer(h.tipo, i, tono)),
            }
            for h in usados
        },
        "reasons": {m.value: _i18n(lambda i, m=m: texto_de_motivo(m, i)) for m in {h.motivo for h in usados}},
        "providers": {p.value: _i18n(lambda i, p=p: PROVEEDOR[p][i]) for p in {h.proveedor for h in usados}},
        "postures": {p.value: _i18n(lambda i, p=p: POSTURA[p][i]) for p in set(Postura)},
        "unrelated": {a.value: _i18n(lambda i, a=a: AJENO[a][i]) for a in Ajeno},
        "no_review": {
            m.value: {"title": _i18n(lambda i, m=m: TITULO_MOTIVO[m][i]), "how_to_fix": _i18n(lambda i, m=m: como_resolver(m, i, tono))}
            for m in {n.motivo for n in d.no_revisados} | {c.motivo for c in d.causas}
        },
    }


def _glosario(tono: Tono) -> dict:
    """«Cómo leer este reporte» (Historia 33): las 12 fichas del catálogo de términos, en español (con el tono elegido) e inglés.

    Los textos viajan en los datos y no en la plantilla porque el tono (tú o usted) lo decide quien genera el reporte.
    """
    def i18n(texto) -> dict[str, str]:  # texto(idioma, tono) -> str
        return {"en": texto(Idioma.EN), "es": texto(Idioma.ES)}

    def rotulos(n: int) -> dict[str, str]:
        return {"en": etiquetas(Idioma.EN, tono)[n], "es": etiquetas(Idioma.ES, tono)[n]}

    return {
        "labels": {"what_is": rotulos(0), "means": rotulos(1), "to_do": rotulos(2)},
        "terms": [
            {
                "id": t.value,
                "name": i18n(lambda i, t=t: nombre(t, i)),
                "line": i18n(lambda i, f=f: f.linea.de(i, tono)),
                "what_is": i18n(lambda i, f=f: f.que_es.de(i, tono)),
                "means": i18n(lambda i, f=f: f.que_significa.de(i, tono)),
                "to_do": i18n(lambda i, f=f: f.que_hacer.de(i, tono)),
            }
            for t, f in FICHAS.items()
        ],
    }


def construir_datos(d: DatosReporte, *, tono: Tono = Tono.CERCANO, version: str = "0.0.0", agente: Plataforma | None = None) -> dict:
    """El objeto del esquema 1. Todo sale de ``DatosReporte``; nada se lee de un archivo del proyecto."""
    return {
        "schema_version": VERSION_ESQUEMA,
        "tool": "AgentReach",
        "tool_version": version,
        "generated_at": d.fecha.strftime("%Y-%m-%d %H:%M"),
        "folder": d.carpeta,
        "files_looked_at": d.archivos_mirados,
        "secrets_notice": _i18n(aviso_de_secretos),
        "agents": _agentes(d, agente),
        "configured_agents": _configurados(d),
        "undetermined_traces": [{"path": r.ruta, "candidates": list(r.candidatos)} for r in d.sin_decidir],
        "catalog": _catalogo(d, tono),
        "not_reviewed": [{"path": n.ruta, "reason": n.motivo.value} for n in dict.fromkeys(d.no_revisados)],
        "limits": {"en": list(LIMITES[Idioma.EN]), "es": list(LIMITES[Idioma.ES])},
        "limits_also": _i18n(lambda i: LIMITES_TAMBIEN[i]),
        "glossary": _glosario(tono),
    }


def _a_json_seguro(datos: dict) -> str:
    """JSON compacto donde ningún ``<`` (ni U+2028/U+2029) puede cerrar el bloque ``<script>`` ni abrir un comentario HTML."""
    texto = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
    return texto.replace("<", "\\u003c").replace(chr(0x2028), "\\u2028").replace(chr(0x2029), "\\u2029")


def _plantilla() -> str:
    return resources.files("agentreach.reporting").joinpath("plantilla_reporte.html").read_text(encoding="utf-8")


def generar_html(
    d: DatosReporte, *, idioma: Idioma = Idioma.ES, tono: Tono = Tono.CERCANO, version: str = "0.0.0", agente: Plataforma | None = None
) -> str:
    """El HTML completo como una cadena (un solo archivo). Lanza ``ReporteDemasiadoGrande`` si se pasa de los topes.

    ``idioma`` es el idioma INICIAL del archivo: el lector puede cambiarlo con los botones EN y ES sin volver a generar.
    """
    datos = construir_datos(d, tono=tono, version=version, agente=agente)
    datos["initial_language"] = idioma.value  # el idioma con que se abre el archivo (la plantilla sigue dejando cambiarlo)
    plantilla = _plantilla()
    if plantilla.count(MARCADOR) != 1:
        raise ValueError("la plantilla no tiene el marcador de datos exactamente una vez")
    html = plantilla.replace(MARCADOR, _a_json_seguro(datos))
    if len(html.encode("utf-8")) > MAX_BYTES:
        raise ReporteDemasiadoGrande("el archivo pasaría de 20 MB")
    return html
