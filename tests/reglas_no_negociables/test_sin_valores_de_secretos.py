"""FR-3: ningún valor de secreto sale jamás. Prueba canario: cada secreto falso lleva un marcador (CNR001 a CNR024)."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import pytest

from agentreach import cli
from conftest import AHORA, MARCADOR, auditoria_completa

MODALIDADES = [
    [],
    ["--detalle"],
    ["--ascii"],
    ["--idioma", "en"],
    ["--idioma", "en", "--detalle", "--ascii"],
    ["--color", "siempre"],
    ["--tono", "formal", "--detalle"],
    ["--agente", "opencode"],
    ["--agente", "claude-code", "--detalle"],
    ["--tarea", "arreglar el formulario de contacto"],
    ["--ancho", "20", "--detalle"],  # el ajuste de línea nunca debe partir un valor en dos para esconderlo
]
CLAVES_JSON = ("private_key", "client_secret", "password", "api_key", "token", "secret", "access_key")


def _valores_de(archivo: Path, texto: str) -> set[str]:
    valores: set[str] = set()
    nombre = archivo.name.lower()
    if nombre.endswith(".json"):
        try:
            datos = json.loads(texto)
        except ValueError:
            datos = {}
        pendientes = [datos]
        while pendientes:
            x = pendientes.pop()
            if isinstance(x, dict):
                for k, v in x.items():
                    if isinstance(v, str) and any(c in k.lower() for c in CLAVES_JSON):
                        valores.add(v)
                    else:
                        pendientes.append(v)
            elif isinstance(x, list):
                pendientes.extend(x)
    for linea in texto.splitlines():
        if linea.lstrip().startswith(("#", ";", "//")):
            continue
        valores.update(m for m in re.findall(r"://[^:@/\s]+:([^@/\s]+)@", linea))  # claves en direcciones de git
        if "=" in linea and (nombre.startswith(".env") or nombre.endswith(".env") or nombre in (".npmrc", "credentials")):
            valores.add(re.split(r"\s+#", linea.split("=", 1)[1].strip())[0].strip().strip("\"'"))
    return {v for v in valores if len(v) >= 8}


def inventario(raiz: Path) -> tuple[set[str], set[str], list[str]]:
    """(valores reales, marcadores, archivos que no se pudieron leer) de los secretos falsos del proyecto de prueba."""
    valores: set[str] = set()
    marcadores: set[str] = set()
    ilegibles: list[str] = []
    for archivo in raiz.rglob("*"):
        if not archivo.is_file() or archivo.suffix in (".py", ".pyc", ".md", ".example", ".sample", ".template"):
            continue  # (las plantillas con valores de relleno como "changeme" no son secretos)
        try:
            texto = archivo.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            if archivo.name.startswith(".env"):
                ilegibles.append(archivo.name)  # PP-03: lectura negada por la ACL
            continue
        valores |= _valores_de(archivo, texto)
        marcadores |= {m.upper() for m in MARCADOR.findall(texto)}
    return valores, marcadores, ilegibles


def prohibidos_de(valores: set[str], marcadores: set[str]) -> set[str]:
    """Cada valor y cada marcador, tal cual, en minúsculas y en base64 (así viaja una clave dentro de un JSON de credenciales)."""
    salida: set[str] = set()
    for v in valores | marcadores:
        salida |= {v, v.lower(), base64.b64encode(v.encode()).decode().rstrip("=")}
    return {s for s in salida if len(s) >= 6}


@pytest.fixture
def variables_con_canario(monkeypatch):
    """Variables de entorno con valores falsos (CNR020 y CNR021): solo sus nombres pueden aparecer, nunca sus valores."""
    monkeypatch.setenv("AGENTREACH_PRUEBA_API_TOKEN", "valor-CNR020-que-no-debe-salir")
    monkeypatch.setenv("AGENTREACH_PRUEBA_DB_PASSWORD", "valor-CNR021-que-no-debe-salir")


def sin_secretos(texto: str, prohibidos: set[str]) -> None:
    """Sin espacios ni saltos de línea: un ajuste de línea no puede esconder un valor partido en dos."""
    junto = re.sub(r"\s+", "", texto)
    encontrado = MARCADOR.search(junto)
    assert encontrado is None, f"salió el marcador {encontrado.group(0)}"  # type: ignore[union-attr]
    for valor in prohibidos:
        assert re.sub(r"\s+", "", valor) not in junto, "salió un valor de secreto (o una variante suya)"


def test_el_inventario_del_proyecto_de_prueba_es_completo(raiz_prueba: Path):
    valores, marcadores, ilegibles = inventario(raiz_prueba)
    assert len(valores) >= 12 and len(marcadores) >= 15
    assert ilegibles == [".env.production"]  # PP-03 (lectura negada): su secreto no se puede inventariar, y lo dice la prueba
    assert any("BEGIN RSA PRIVATE KEY" in v and "Q05SMD" in v for v in valores)  # credentials.json: el marcador CNR016 va en base64
    assert {"CNR003", "CNR004", "CNR005"} <= marcadores


@pytest.mark.parametrize("extra", MODALIDADES, ids=lambda e: " ".join(e) or "defecto")
def test_ningun_marcador_ni_valor_sale_en_pantalla_ni_en_errores(raiz_prueba: Path, tempdir_vacio, variables_con_canario, extra):
    prohibidos = prohibidos_de(*inventario(raiz_prueba)[:2])
    codigo, salida, error = auditoria_completa(raiz_prueba, *extra)
    assert codigo in (0, 1) and "AGENTREACH" in salida  # (con --ascii el título sale sin tilde)
    sin_secretos(salida, prohibidos)
    sin_secretos(error, prohibidos)
    assert list(tempdir_vacio.iterdir()) == []  # ni en archivos temporales


@pytest.mark.parametrize("idioma", ["es", "en"])
def test_ningun_valor_sale_en_el_archivo_de_salida_ni_en_el_doctor(raiz_prueba: Path, tmp_path: Path, variables_con_canario, capsys, idioma):
    prohibidos = prohibidos_de(*inventario(raiz_prueba)[:2])
    destino = tmp_path / "reporte.txt"
    assert cli.main([str(raiz_prueba), "--home", str(raiz_prueba / "home-falso"), "--incluir-ubicaciones-sensibles", "--detalle",
                     "--idioma", idioma, "--salida", str(destino)], ahora=lambda: AHORA) in (0, 1)
    sin_secretos(destino.read_text(encoding="utf-8"), prohibidos)
    cli.main(["doctor", str(raiz_prueba / "proyecto"), "--idioma", idioma])
    capturado = capsys.readouterr()
    sin_secretos(capturado.out + capturado.err, prohibidos)


@pytest.mark.parametrize("idioma", ["es", "en"])
def test_ningun_valor_sale_ni_con_un_error_forzado(raiz_prueba: Path, monkeypatch, capsys, variables_con_canario, idioma):
    prohibidos = prohibidos_de(*inventario(raiz_prueba)[:2])

    def explota(*a, **k):
        raise RuntimeError("falla con el valor CNR001-secreto-de-prueba dentro del mensaje")

    for destino in ("generar", "preparar", "auditar"):
        with monkeypatch.context() as m:
            m.setattr(cli, destino, explota)
            assert cli.main([str(raiz_prueba / "proyecto"), "--idioma", idioma], ahora=lambda: AHORA) == 3
            capturado = capsys.readouterr()
            assert capturado.out == ""  # nada de un reporte parcial
            assert ("Error interno" in capturado.err) or ("internal error" in capturado.err)
            sin_secretos(capturado.out + capturado.err, prohibidos)
            assert "Traceback" not in capturado.err and "falla con el valor" not in capturado.err


def test_el_modelo_del_hallazgo_no_tiene_donde_guardar_un_valor():
    """El hallazgo no tiene ningún campo de texto libre: lo único textual son rutas y etiquetas cortas (FR-3, por diseño)."""
    import dataclasses
    import enum
    import typing

    from agentreach.contracts import Etiqueta, Finding, Location, Ruta, RutaReal

    permitidos = {Ruta, RutaReal, Etiqueta, Location, int, bool, type(None)}
    for nombre, anotacion in typing.get_type_hints(Finding).items():
        for t in (typing.get_args(anotacion) or (anotacion,)):
            assert t in permitidos or (isinstance(t, type) and issubclass(t, enum.Enum)), f"{nombre}: {t}"
    assert not [c for c in dataclasses.fields(Finding) if c.type is str]


def test_el_detector_de_canarios_funciona():
    """La propia prueba se prueba: un marcador, un valor real, su minúscula, su base64 o un valor partido en dos líneas hacen fallar."""
    valor = "hunter2-largo-valor"
    prohibidos = prohibidos_de({valor}, {"CNR016"})
    for texto in ("todo bien hasta aquí CNR007 y ya", f"el valor es {valor}", f"el valor es {valor.upper().lower()}",
                  "clave: " + base64.b64encode(valor.encode()).decode().rstrip("="), "partido hunter2-\nlargo-valor",
                  "marcador en minuscula cnr016"):
        with pytest.raises(AssertionError):
            sin_secretos(texto, prohibidos)
    sin_secretos("nada que ocultar", prohibidos)
    assert base64.b64encode(b"CNR016").decode() == "Q05SMDE2"  # el caso real de credentials.json
