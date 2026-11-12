"""Historia 28: permiso en dos niveles. Primera pregunta: leer ESTA carpeta. Segunda, aparte: ver las reglas de los agentes fuera del proyecto
(carpeta personal, configuración gestionada y ``opencode.json`` de las carpetas padre). Con N, no se abre NI SE LISTA nada fuera del proyecto,
los niveles que dependen de las reglas quedan en «potencial» y el reporte dice por qué.

Esta prueba NO lleva la marca ``sin_tope_por_nombre``.
"""

from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest

from agentreach import cli
from agentreach.app.auditar import auditar
from agentreach.config import Configuracion
from agentreach.contracts import Motivo, MotivoNoRevisado, Nivel, Plataforma, Tipo
from test_reporte_html import ESQUEMA, _validar, json_de

AHORA = datetime(2026, 11, 11, 9, 0, 0)

CERCANO = ("AgentReach necesita ver las reglas de tus agentes en tu carpeta personal (solo las reglas, nunca los valores). "
           "Sin ellas no puede decidir bien los niveles. ¿Se permite? (S/N) ")
FORMAL = CERCANO.replace("tus agentes en tu carpeta", "sus agentes en su carpeta")
INGLES = ("AgentReach needs to see the rules of your agents in your home folder (only the rules, never the values). "
          "Without them it cannot decide the levels properly. Is this allowed? (Y/N) ")


# ---- la vigilancia: ¿se abrió o se listó algo fuera del proyecto? --------------------------------------------------------------------

VIGILANCIA: dict = {"activa": False, "prohibidas": [], "permitidas": [], "vistas": []}


def _gancho(evento: str, args: tuple) -> None:
    if not VIGILANCIA["activa"] or evento not in ("open", "os.listdir", "os.scandir", "glob.glob"):
        return
    destino = args[0] if args else None
    if not isinstance(destino, (str, bytes, os.PathLike)):
        return
    ruta = os.path.normcase(os.path.abspath(os.fsdecode(destino)))
    if any(ruta == p or ruta.startswith(p + os.sep) for p in VIGILANCIA["permitidas"]):
        return
    if any(ruta == p or ruta.startswith(p + os.sep) for p in VIGILANCIA["prohibidas"]) or ruta in VIGILANCIA["exactas"]:
        VIGILANCIA["vistas"].append(f"{evento}: {ruta}")


sys.addaudithook(_gancho)  # inerte mientras ``activa`` sea falso


class Vigilar:
    def __init__(self, prohibidas, permitidas, exactas=()):
        norma = lambda lista: [os.path.normcase(os.path.abspath(str(x))) for x in lista]
        self.datos = {"prohibidas": norma(prohibidas), "permitidas": norma(permitidas), "exactas": set(norma(exactas))}

    def __enter__(self):
        VIGILANCIA.update(self.datos, activa=True, vistas=[])
        return VIGILANCIA["vistas"]

    def __exit__(self, *a):
        VIGILANCIA["activa"] = False


@pytest.fixture
def mundo(tmp_path: Path) -> dict:
    """Un repositorio (con ``.git`` y un ``opencode.json`` de reglas) que contiene el proyecto, una carpeta personal con configuración de
    Claude Code, de opencode y del propio AgentReach, y una configuración gestionada."""
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    proyecto = repo / "proyecto"
    proyecto.mkdir()
    casa = tmp_path / "casa"
    gestionada = tmp_path / "programas"
    (casa / ".claude").mkdir(parents=True)
    (casa / ".config" / "opencode").mkdir(parents=True)
    (casa / ".agentreach").mkdir()
    gestionada.mkdir()
    (proyecto / ".env").write_text("STRIPE_SECRET_KEY=x\n", encoding="utf-8")
    (proyecto / "opencode.json").write_text(json.dumps({"permission": {"read": "allow"}}), encoding="utf-8")
    (repo / "opencode.json").write_text(json.dumps({"permission": {"read": {"*.env": "deny"}}}), encoding="utf-8")  # del repositorio (padre)
    (casa / ".claude" / "settings.json").write_text(json.dumps({"permissions": {"deny": ["Read(./.env)"]}}), encoding="utf-8")
    (casa / ".config" / "opencode" / "opencode.json").write_text(json.dumps({"permission": {"read": {"*.env": "deny"}}}), encoding="utf-8")
    (casa / ".agentreach" / "config.toml").write_text("incluir_ubicaciones_sensibles = false\n", encoding="utf-8")
    for nombre in (".ssh", ".aws"):
        (casa / nombre).mkdir()
    (casa / ".cursor" / "agents").mkdir(parents=True)
    return {"repo": repo, "proyecto": proyecto, "casa": casa, "gestionada": gestionada, "tmp": tmp_path}


def afuera(mundo) -> dict:
    """Lo que está fuera del proyecto y NO se puede abrir ni listar sin el permiso de segundo nivel."""
    return {"prohibidas": [mundo["casa"], mundo["gestionada"]],
            "exactas": [mundo["repo"], mundo["repo"] / "opencode.json", mundo["repo"] / "opencode.jsonc", mundo["repo"] / ".git",
                        mundo["tmp"]],
            "permitidas": [mundo["proyecto"], mundo["casa"] / "AgentReach-reportes"]}


def correr(mundo, respuestas, *extra, textos=None):
    cola = list(respuestas)

    def preguntar(texto: str) -> str:
        if textos is not None:
            textos.append(texto)
        return cola.pop(0) if cola else "n"

    return cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--sin-reporte-html", *extra], ahora=lambda: AHORA,
                    preguntar=preguntar)


@pytest.fixture(autouse=True)
def entorno_de_programas(mundo, monkeypatch):
    for nombre in ("HOME", "USERPROFILE"):  # la «carpeta personal» real de la prueba (donde está ~/.agentreach/config.toml)
        monkeypatch.setenv(nombre, str(mundo["casa"]))
    for nombre in ("ProgramFiles", "ProgramData", "APPDATA", "LOCALAPPDATA"):
        monkeypatch.setenv(nombre, str(mundo["gestionada"]))
    monkeypatch.setattr("agentreach.adapters.claude_code._gestionada_por_defecto", lambda sistema: str(mundo["gestionada"] / "managed-settings.json"))
    monkeypatch.setattr("agentreach.adapters.opencode._gestionada_por_defecto", lambda sistema: str(mundo["gestionada"] / "opencode.json"))


# ---- el texto y el orden de las preguntas -----------------------------------------------------------------------------------------------


def test_el_texto_de_la_segunda_pregunta_en_espanol_cercano_y_formal_y_en_ingles(mundo):
    for extra, esperado in (((), CERCANO), (("--tono", "formal"), FORMAL), (("--idioma", "en"), INGLES)):
        textos: list[str] = []
        correr(mundo, ["y" if "--idioma" in extra else "s"] * 2, *extra, textos=textos)
        assert " ".join(textos[1].split()) == esperado.strip() and textos[1].endswith(") "), extra


def test_son_dos_preguntas_separadas_y_la_segunda_solo_si_la_primera_fue_si(mundo):
    textos: list[str] = []
    correr(mundo, ["s", "s"], textos=textos)
    assert len(textos) == 2 and "lea esta carpeta" in textos[0] and "reglas de tus agentes" in textos[1]
    textos.clear()
    assert correr(mundo, ["n", "s"], textos=textos) == 2 and len(textos) == 1  # sin permiso para la carpeta no hay segunda pregunta


@pytest.mark.parametrize("invalida", ["", "si", "yes", "y", " s", "1"])
def test_en_la_segunda_pregunta_lo_que_no_es_s_o_n_se_repite_y_tras_tres_intentos_cuenta_como_n(mundo, invalida, capsys):
    textos: list[str] = []
    correr(mundo, ["s", invalida, invalida, invalida], textos=textos)
    assert len(textos) == 4 and "no se leerá nada fuera del proyecto" in " ".join(capsys.readouterr().err.split())


def test_en_ingles_la_segunda_acepta_y_Y_n_N_y_no_s(mundo):
    textos: list[str] = []
    correr(mundo, ["y", "s", "S", "Y"], "--idioma", "en", textos=textos)
    assert len(textos) == 4  # la «s» y la «S» no valen en inglés; la «Y» sí


# ---- con S: se leen las reglas de fuera ------------------------------------------------------------------------------------------------


def test_con_s_se_abren_la_configuracion_de_usuario_y_las_reglas_de_las_carpetas_padre(mundo):
    with Vigilar(**afuera(mundo)) as vistas:
        assert correr(mundo, ["s", "s"]) in (0, 1)
    abiertos = " ".join(vistas)
    assert "settings.json" in abiertos.replace("\\", "/") and "opencode.json" in abiertos and ".agentreach" in abiertos  # la vigilancia ve


def test_con_s_los_niveles_usan_las_reglas_de_fuera(mundo):
    res = auditar(str(mundo["proyecto"]), Configuracion(home=str(mundo["casa"]), lectura_fuera=True))
    claude = [h for h in res.hallazgos if h.tipo is Tipo.CREDENCIAL_EN_ARCHIVO and h.plataforma is Plataforma.CLAUDE_CODE]
    assert claude and all(h.motivo is Motivo.REGLA_DENY for h in claude)  # el deny de ~/.claude/settings.json se ve
    assert not any(n.motivo is MotivoNoRevisado.SIN_PERMISO_FUERA_DEL_PROYECTO for n in res.no_revisados)


# ---- con N: nada fuera del proyecto ---------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("respuesta", ["n", "N"])
def test_con_n_no_se_abre_ni_se_lista_nada_fuera_de_la_carpeta(mundo, respuesta):
    with Vigilar(**afuera(mundo)) as vistas:
        assert correr(mundo, ["s", respuesta]) in (0, 1)
    assert vistas == [], vistas


def test_con_n_tampoco_con_el_opt_in_de_ubicaciones_sensibles_ni_con_todas_las_opciones(mundo):
    with Vigilar(**afuera(mundo)) as vistas:
        correr(mundo, ["s", "n"], "--incluir-ubicaciones-sensibles", "--detalle")
        correr(mundo, ["s", "n"], "--incluir-ubicaciones-sensibles", "--formato", "html", "--salida", str(mundo["tmp"] / "r.html"))
    assert vistas == [], vistas


def test_con_n_el_archivo_global_de_agentreach_tampoco_se_abre(mundo):
    (mundo["casa"] / ".agentreach" / "config.toml").write_text("esto no es [toml", encoding="utf-8")
    with Vigilar(**afuera(mundo)) as vistas:
        correr(mundo, ["s", "n"])
    assert vistas == []
    with Vigilar(**afuera(mundo)) as vistas:  # con S sí se lee (y avisa que no se pudo leer)
        correr(mundo, ["s", "s"])
    assert any("config.toml" in v for v in vistas)


def test_con_n_no_se_deduce_ningun_agente_de_la_carpeta_personal(mundo):
    res = auditar(str(mundo["proyecto"]), Configuracion(home=str(mundo["casa"]), lectura_fuera=False))
    assert all(e.ambito != "usuario" for a in res.agentes for e in a.evidencia)
    con = auditar(str(mundo["proyecto"]), Configuracion(home=str(mundo["casa"]), lectura_fuera=True))
    assert any(e.ambito == "usuario" for a in con.agentes for e in a.evidencia)  # con permiso sí (control)


def test_con_n_los_niveles_que_dependen_de_las_reglas_quedan_en_potencial_y_dicen_por_que(mundo):
    res = auditar(str(mundo["proyecto"]), Configuracion(home=str(mundo["casa"]), lectura_fuera=False))
    for plataforma in (Plataforma.CLAUDE_CODE, Plataforma.OPENCODE):
        hallazgos = [h for h in res.hallazgos if h.tipo is Tipo.CREDENCIAL_EN_ARCHIVO and h.plataforma is plataforma]
        assert hallazgos and all(h.nivel is Nivel.POTENCIAL and h.motivo is Motivo.NO_DETERMINADO for h in hallazgos), plataforma
    motivos = {n.motivo for _, c in res.contextos for n in c.causas_no_determinado}
    assert MotivoNoRevisado.SIN_PERMISO_FUERA_DEL_PROYECTO in motivos


def test_con_n_el_reporte_de_terminal_dice_por_que_y_como_cambiarlo(mundo, monkeypatch, capsys):
    correr(mundo, ["s", "n"])
    texto = " ".join(capsys.readouterr().out.split())
    assert "POR QUÉ HAY NIVELES" in texto and "No se leyeron las reglas de fuera del proyecto (no se dio permiso)" in texto
    assert "~/.claude/settings.json" in texto and "responde S a la segunda pregunta" in texto


def test_con_n_el_html_dice_por_que_y_cumple_el_esquema(mundo):
    destino = mundo["tmp"] / "r.html"
    correr(mundo, ["s", "n"], "--formato", "html", "--salida", str(destino))
    datos = json_de(destino.read_text(encoding="utf-8"))
    _validar(datos, ESQUEMA)
    claude = next(a for a in datos["agents"] if a["id"] == "claude_code")
    assert any(x["reason"] == "sin_permiso_fuera_del_proyecto" for x in claude["not_determined"])
    assert "sin_permiso_fuera_del_proyecto" in datos["catalog"]["no_review"]
    assert any(f["reason"] == "no_determinado" for f in claude["findings"])


def test_con_n_y_en_ingles_el_aviso_y_la_explicacion(mundo, capsys):
    correr(mundo, ["y", "n"], "--idioma", "en")
    capturado = capsys.readouterr()
    assert "Nothing outside the project will be read" in capturado.err
    assert "The rules outside the project were not read (permission was not given)" in " ".join(capturado.out.split())


def test_sin_terminal_no_hay_ninguna_pregunta_ni_lectura(mundo, monkeypatch, capsys):
    monkeypatch.setattr(cli, "_interactivo", cli._interactivo.__wrapped__ if hasattr(cli._interactivo, "__wrapped__") else (lambda: False))
    monkeypatch.setattr(sys, "stdin", io.StringIO())
    with Vigilar(**afuera(mundo)) as vistas:
        assert cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"])], preguntar=lambda t: pytest.fail("no debía preguntar")) == 2
    assert vistas == []
