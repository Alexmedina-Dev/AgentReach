"""Reconocimiento de archivos de credenciales y de variables con nombre de credencial.

Del contenido conserva solo (tipo, proveedor, línea): el valor se evalúa de paso y se descarta.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum

from agentreach.collectors.detector.patrones import (
    clasificar_nombre,
    valor_es_referencia,
    valor_es_relleno,
)
from agentreach.contracts import Linea, Proveedor, Tipo
from agentreach.infra.localizador import localizar_clave


class ClaseArchivo(Enum):
    ENV = "env"
    NPMRC = "npmrc"
    CREDENCIALES_JSON = "credenciales_json"
    TEXTO = "texto"  # solo se miran variables de alto poder con valor literal


@dataclass(frozen=True, slots=True)
class Candidato:
    tipo: Tipo
    proveedor: Proveedor
    linea: int | Linea


_PLANTILLAS = (".example", ".sample", ".template", ".dist", ".tpl", ".defaults")
_EXTENSIONES_TEXTO = (
    ".txt", ".md", ".py", ".js", ".ts", ".json", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".sh",
    ".ps1", ".bat", ".cmd", ".properties", ".conf", ".rst",
)
_ASIGNACION = re.compile(r"^\s*(?:export\s+|set\s+|\$env:)?([A-Za-z_][A-Za-z0-9_.\-]*)\s*[=:]\s*(.*)$")
_CLAVES_JSON = ("private_key", "client_secret", "password", "api_key", "token")


def clase_de_archivo(ruta: str, proyecto: str = "") -> ClaseArchivo | None:
    """Clasifica por nombre o ruta. Las plantillas (``.env.example``) no cuentan.

    Las carpetas excluidas (``.git``, ``node_modules``) se buscan solo DENTRO del proyecto: donde
    esté el proyecto en el disco no cambia lo que se revisa.
    """
    relativa = ruta[len(proyecto):] if proyecto and ruta.startswith(proyecto) else ruta
    partes = relativa.replace("\\", "/").split("/")
    nombre = partes[-1].lower()
    if ".git" in partes[:-1] or "node_modules" in partes[:-1]:
        return None
    if nombre.endswith(_PLANTILLAS):
        return None
    if nombre == ".env" or nombre.startswith(".env.") or nombre.endswith(".env"):
        return ClaseArchivo.ENV
    if nombre == ".npmrc":
        return ClaseArchivo.NPMRC
    if nombre == "credentials.json":
        return ClaseArchivo.CREDENCIALES_JSON
    if nombre.endswith(_EXTENSIONES_TEXTO):
        return ClaseArchivo.TEXTO
    return None


def candidato_por_nombre(clase: ClaseArchivo) -> Candidato | None:
    """Archivo conocido que no se pudo leer: se reporta por su nombre, sin línea."""
    if clase is ClaseArchivo.TEXTO:
        return None
    return Candidato(Tipo.CREDENCIAL_EN_ARCHIVO, Proveedor.DESCONOCIDO, Linea.NO_DETERMINADA)


_SALTO = re.compile(r"\r\n|\r|\n")  # los mismos saltos que reconoce el localizador


def analizar(clase: ClaseArchivo, texto: str) -> list[Candidato]:
    """Candidatos de un archivo ya leído. El ``texto`` no sale de esta función."""
    texto = texto.removeprefix("﻿")  # BOM de archivos guardados en Windows
    if clase is ClaseArchivo.ENV:
        return _analizar_env(texto)
    if clase is ClaseArchivo.TEXTO:
        return _analizar_texto(texto)
    if clase is ClaseArchivo.NPMRC:
        return _analizar_npmrc(texto)
    return _analizar_json(texto)


def _asignaciones(texto: str) -> Iterator[tuple[int, str, str]]:
    for numero, linea in enumerate(_SALTO.split(texto), start=1):
        if linea.lstrip().startswith(("#", "//", ";")):
            continue
        m = _ASIGNACION.match(linea)
        if m:
            yield numero, m.group(1), m.group(2)


def _analizar_env(texto: str) -> list[Candidato]:
    repeticiones: dict[str, int] = {}
    for _, nombre, _ in _asignaciones(texto):
        repeticiones[nombre] = repeticiones.get(nombre, 0) + 1
    salida: list[Candidato] = []
    for numero, nombre, valor in _asignaciones(texto):
        clase = clasificar_nombre(nombre)
        if clase is None or valor_es_relleno(valor) or valor_es_referencia(valor):
            continue
        linea: int | Linea = numero
        if repeticiones[nombre] > 1:  # el localizador no adivina si la clave está repetida
            linea = localizar_clave(texto, "env", (nombre,)) or Linea.NO_DETERMINADA
        salida.append(Candidato(Tipo.CREDENCIAL_EN_ARCHIVO, clase.proveedor, linea))
    # variable repetida: la línea no se determina y los duplicados idénticos se reducen a uno
    return list(dict.fromkeys(salida))


def _analizar_texto(texto: str) -> list[Candidato]:
    salida: list[Candidato] = []
    for numero, nombre, valor in _asignaciones(texto):
        clase = clasificar_nombre(nombre)
        if clase is None or not clase.alto_poder:
            continue
        if valor_es_relleno(valor) or valor_es_referencia(valor):
            continue
        salida.append(Candidato(Tipo.SECRETO_DE_ALTO_PODER, clase.proveedor, numero))
    return salida


def _analizar_npmrc(texto: str) -> list[Candidato]:
    salida: list[Candidato] = []
    for numero, linea in enumerate(_SALTO.split(texto), start=1):
        if linea.lstrip().startswith(("#", ";")):
            continue
        if ("_auth" in linea.lower() or "_password" in linea.lower()) and "=" in linea:
            valor = linea.split("=", 1)[1]
            if not valor_es_relleno(valor) and not valor_es_referencia(valor):
                salida.append(Candidato(Tipo.CREDENCIAL_EN_ARCHIVO, Proveedor.CODIGO, numero))
    return salida


def _analizar_json(texto: str) -> list[Candidato]:
    for clave in _CLAVES_JSON:
        linea = localizar_clave(texto, "json", (clave,))
        if linea is not None:
            return [Candidato(Tipo.CREDENCIAL_EN_ARCHIVO, Proveedor.NUBE, linea)]
    return []
