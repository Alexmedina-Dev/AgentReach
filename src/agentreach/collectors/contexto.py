"""Archivos de contexto del agente con patrones de texto simples sospechosos (TH-5).

Busca ``CLAUDE.md`` y ``AGENTS.md`` (en cualquier carpeta del proyecto, menos ``.git`` y
``node_modules``) y los lee SOLO con la lectura segura. Cuatro grupos de patrones simples, en español
e inglés: anular las reglas, leer un secreto, enviar algo a una dirección web y ocultárselo a la
persona. Se reporta cuando coinciden **al menos dos grupos distintos**: una frase suelta como "ignora
las instrucciones anteriores" no basta. No es análisis de intención: solo texto simple.

Del contenido solo se conserva la línea de la primera coincidencia: el texto sospechoso, la dirección y
los nombres de archivo que cita nunca salen en un objeto ni en un mensaje. El nivel es provisional
(hipótesis, y así se queda: la Historia 11 no lo sube).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from agentreach.collectors.enlaces import recorrer
from agentreach.collectors.instrucciones_fuera import NOMBRES_INSTRUCCIONES
from agentreach.contracts import (
    Ajeno,
    ArchivoNoLegible,
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

_SALTO = re.compile(r"\r\n|\r|\n")  # los mismos saltos que el resto del programa
_NOMBRES = {n.lower() for n in NOMBRES_INSTRUCCIONES}
_EXCLUIDAS = {".git", "node_modules"}

_GRUPOS: dict[str, re.Pattern[str]] = {
    "anular": re.compile(
        r"\bignor\w*\s+(?:todas\s+|cualquier\s+)?(?:las\s+|los\s+|tus\s+)?(?:instrucciones|reglas|permisos|restricciones)"
        r"|\bignore\s+(?:all\s+|any\s+)?(?:the\s+|your\s+)?(?:previous\s+|prior\s+|above\s+|earlier\s+|system\s+)?"
        r"(?:instructions|rules|prompts?|permissions)"
        r"|\bdisregard\s+.{0,30}(?:instructions|rules)|\bolvida\s+(?:las\s+)?(?:instrucciones|reglas)"
        r"|(?:desactiva\w*|disable|bypass)\s+.{0,20}(?:permisos|permissions|seguridad|safety)"
    ),
    "leer_secreto": re.compile(
        r"\b(?:lee|leer|lea|read|cat|abre|abrir|open|print|muestra)\b.{0,40}"
        r"(?:\.env\b|credenciales|credentials|secrets?\b|secretos?\b|id_rsa|\.ssh|\.aws|tokens?\b)"
    ),
    "enviar_url": re.compile(
        r"\b(?:envia\w*|enviar|send|post|upload|sube|subir|exfiltrat\w*|curl|wget)\b.{0,80}https?://"
    ),
    "ocultar": re.compile(
        r"\bsin\s+avisar|\bsin\s+que\s+(?:el\s+)?usuario|without\s+(?:telling|notifying|asking)"
        r"|\bdo\s+not\s+(?:tell|inform|mention)|\bdon'?t\s+(?:tell|mention)|\bno\s+(?:se\s+lo\s+)?(?:digas|menciones|avises)\b"
        r"|\bno\s+avis\w*\s+al\s+usuario"
    ),
}


_MAX_LINEA = 4000  # una línea enorme no puede hacer trabajar de más a las expresiones
_VENTANA = 3  # una instrucción partida en varias líneas seguidas también se ve


def _normalizar(linea: str) -> str:
    """Minúsculas y sin acentos, para que "Lée" y "envíalo" coincidan con los patrones."""
    descompuesta = unicodedata.normalize("NFKD", linea[:_MAX_LINEA].lower())
    # sin acentos y sin caracteres de formato invisibles (ancho cero, etc.) que partirían una palabra
    return "".join(c for c in descompuesta if not unicodedata.combining(c) and unicodedata.category(c) != "Cf")


def _linea_sospechosa(texto: str) -> int | None:
    """Línea de la primera coincidencia si hay al menos dos grupos distintos; si no, ``None``."""
    primera: dict[str, int] = {}
    lineas = [_normalizar(linea) for linea in _SALTO.split(texto)]
    for grupo, patron in _GRUPOS.items():
        # primero línea por línea (así se cita la línea exacta); la ventana solo ve lo que cruza líneas
        for i, linea in enumerate(lineas):
            if patron.search(linea):
                primera[grupo] = i + 1
                break
        else:
            for i in range(len(lineas)):
                if patron.search(" ".join(lineas[i:i + _VENTANA])):
                    primera[grupo] = i + 1
                    break
    return min(primera.values()) if len(primera) >= 2 else None


class DetectorContexto:
    """``no_revisados`` queda con lo que no se pudo leer en la última llamada."""

    def __init__(self, fs: ReadOnlyFs) -> None:
        self._fs = fs
        self.no_revisados: tuple[NoRevisado, ...] = ()

    def detectar(self, proyecto: Ruta) -> Iterable[Finding]:
        self.no_revisados = ()
        hallazgos: list[Finding] = []
        pendientes: list[NoRevisado] = []
        recorrido = recorrer(self._fs, proyecto)
        for omitido in recorrido.omitidos:  # demasiado grande para leerlo: no es "sin patrones"
            partes = omitido.replace("\\", "/").split("/")
            if partes[-1].lower() in _NOMBRES and not _EXCLUIDAS & set(partes[:-1]):
                pendientes.append(NoRevisado(Ruta(omitido), MotivoNoRevisado.ARCHIVO_DEMASIADO_GRANDE))
        for archivo in recorrido.archivos:
            partes = archivo.ruta.replace("\\", "/").split("/")
            if partes[-1].lower() not in _NOMBRES or _EXCLUIDAS & set(partes[:-1]):
                continue
            real = Ruta(archivo.ruta_real if archivo.ruta_real is not None else archivo.ruta)
            try:
                texto = self._fs.leer_texto(real)
            except (ArchivoNoLegible, OSError) as error:
                pendientes.append(NoRevisado(archivo.ruta, getattr(error, "motivo", None) or MotivoNoRevisado.ARCHIVO_ILEGIBLE))
                continue  # no es "sin patrones": se informa
            linea = _linea_sospechosa(texto)
            del texto  # el contenido no sobrevive al análisis
            if linea is not None:
                hallazgos.append(_hallazgo(archivo.ruta, linea))
        self.no_revisados = tuple(pendientes)
        return hallazgos


def _hallazgo(ruta: str, linea: int) -> Finding:
    return Finding(
        ubicacion=Location(Ruta(ruta), linea),
        tipo=Tipo.CONTEXTO_SOSPECHOSO,
        proveedor=Proveedor.NO_APLICA,
        nivel=Nivel.HIPOTESIS,
        motivo=Motivo.INDICIO_DEBIL,
        ajeno_a_tarea=Ajeno.NO_DETERMINADO,
        plataforma=Plataforma.NO_DETERMINADA,
        agente=Etiqueta("sin-agente"),
        postura=Postura.NO_DETERMINADA,
    )

