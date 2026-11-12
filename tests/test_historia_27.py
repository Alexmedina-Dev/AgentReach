"""Historia 27: (1) las preguntas muestran (S/N) —en inglés (Y/N)— y solo cuentan esas letras; (2) una variable o clave reconocida SOLO por su
nombre nunca pasa de «potencial», en ningún agente (incluido opencode: PP-01a a PP-01f del oráculo).

Esta prueba NO lleva la marca ``sin_tope_por_nombre``: ve el tope real.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from agentreach import cli
from agentreach.app.auditar import auditar
from agentreach.config import Configuracion
from agentreach.contracts import Motivo, Nivel, Plataforma, Tipo
from agentreach.core.politica import BASE_POR_TIPO, NIVEL_MAXIMO, Base

AHORA = datetime(2026, 11, 11, 9, 0, 0)


@pytest.fixture
def mundo(tmp_path: Path) -> dict:
    casa = tmp_path / "casa"
    casa.mkdir()
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    (proyecto / ".env").write_text("ANTHROPIC_API_KEY=x\nSTRIPE_SECRET_KEY=x\nGITHUB_TOKEN=x\nRAILWAY_TOKEN=x\nDATABASE_URL=x\nJWT_SECRET=x\n", encoding="utf-8")
    (proyecto / ".env.local").write_text("GITHUB_TOKEN=x\n", encoding="utf-8")
    return {"casa": casa, "proyecto": proyecto}


def credenciales(res, plataforma: Plataforma):
    return [h for h in res.hallazgos if h.tipo is Tipo.CREDENCIAL_EN_ARCHIVO and h.plataforma is plataforma]


# ---- (2) el tope por nombre ----------------------------------------------------------------------------------------------------------


def test_el_tope_real_de_las_credenciales_por_nombre_es_potencial():
    assert NIVEL_MAXIMO[Tipo.CREDENCIAL_EN_ARCHIVO] is Nivel.POTENCIAL
    for tipo in (Tipo.CLAVE_PRIVADA_SSH, Tipo.CREDENCIALES_DE_NUBE, Tipo.SECRETO_DE_ALTO_PODER, Tipo.VARIABLE_DE_ENTORNO):
        assert NIVEL_MAXIMO[tipo] is not Nivel.COMPROBADO, tipo  # todo lo que se reconoce por nombre: nunca comprobado


def test_ningun_tipo_con_base_por_nombre_o_credencial_llega_a_comprobado():
    for tipo, base in BASE_POR_TIPO.items():
        if base is Base.POR_NOMBRE:
            assert NIVEL_MAXIMO[tipo] is not Nivel.COMPROBADO, tipo


@pytest.mark.parametrize("plataforma", [Plataforma.CLAUDE_CODE, Plataforma.OPENCODE])
def test_sin_reglas_una_credencial_por_nombre_es_potencial_en_cada_agente(mundo, plataforma):
    res = auditar(str(mundo["proyecto"]), Configuracion(home=str(mundo["casa"])))
    hallazgos = credenciales(res, plataforma)
    assert len(hallazgos) == 7 and all(h.nivel is Nivel.POTENCIAL for h in hallazgos)
    # lo explica: sin fuente verificada (solo el nombre); en opencode, sin reglas, la política base pregunta antes de leer un .env
    esperado = {Motivo.SIN_FUENTE_VERIFICADA} if plataforma is Plataforma.CLAUDE_CODE else {Motivo.REGLA_ASK}
    assert {h.motivo for h in hallazgos} == esperado


def test_en_opencode_con_read_allow_tambien_potencial_pp01a_a_pp01f(mundo):
    """El caso que quedaba como diferencia aceptada: opencode con ``read: allow`` daba comprobado a PP-01a..f."""
    (mundo["proyecto"] / "opencode.json").write_text(json.dumps({"permission": {"read": "allow", "edit": "allow"}}), encoding="utf-8")
    res = auditar(str(mundo["proyecto"]), Configuracion(home=str(mundo["casa"])))
    hallazgos = credenciales(res, Plataforma.OPENCODE)
    assert hallazgos and all(h.nivel is Nivel.POTENCIAL for h in hallazgos)
    assert not any(h.nivel is Nivel.COMPROBADO for h in res.hallazgos if h.tipo is Tipo.CREDENCIAL_EN_ARCHIVO)


def test_con_una_regla_deny_sigue_diciendo_por_que(mundo):
    (mundo["proyecto"] / ".claude").mkdir()
    (mundo["proyecto"] / ".claude" / "settings.json").write_text(json.dumps({"permissions": {"deny": ["Read(./.env)"]}}), encoding="utf-8")
    res = auditar(str(mundo["proyecto"]), Configuracion(home=str(mundo["casa"])))
    claude = {h.ubicacion.ruta.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]: h for h in credenciales(res, Plataforma.CLAUDE_CODE)}
    assert claude[".env"].motivo is Motivo.REGLA_DENY and claude[".env.local"].motivo is Motivo.SIN_FUENTE_VERIFICADA


def test_un_proyecto_solo_con_credenciales_por_nombre_sale_con_codigo_0(mundo, monkeypatch, capsys):
    monkeypatch.setattr(cli, "_crear_reporte_por_defecto", False)
    assert cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"])], ahora=lambda: AHORA) == 0
    texto = " ".join(capsys.readouterr().out.split())
    assert "COMPROBADO" not in texto and "POTENCIAL" in texto


def test_lo_que_se_determina_por_el_texto_sigue_pudiendo_ser_comprobado(tmp_path):
    """El tope es solo para lo reconocido por nombre: un git que ejecuta programas es un hecho del texto y sigue comprobado."""
    from agentreach.contracts import Tipo as T

    assert NIVEL_MAXIMO[T.GIT_EJECUTA_PROGRAMAS] is Nivel.COMPROBADO and NIVEL_MAXIMO[T.TEXTO_INVISIBLE] is Nivel.COMPROBADO


# ---- (1) las preguntas ---------------------------------------------------------------------------------------------------------------


def preguntar_y_registrar(respuestas: list[str], textos: list[str]):
    cola = list(respuestas)

    def preguntar(texto: str) -> str:
        textos.append(texto)
        return cola.pop(0) if cola else "n"

    return preguntar


@pytest.mark.parametrize("idioma, sufijo", [("es", "(S/N) "), ("en", "(Y/N) ")])
def test_las_tres_preguntas_muestran_las_letras_en_mayuscula(mundo, idioma, sufijo, monkeypatch):
    monkeypatch.setattr(cli, "_crear_reporte_por_defecto", True)
    textos: list[str] = []
    si = "s" if idioma == "es" else "y"
    cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--idioma", idioma], ahora=lambda: AHORA,
             preguntar=preguntar_y_registrar([si, si, "n"], textos))
    assert len(textos) == 3 and all(t.endswith(sufijo) for t in textos), textos
    assert "(s/n)" not in " ".join(textos) and "(s/N)" not in " ".join(textos)


@pytest.mark.parametrize("respuesta, vale", [("s", True), ("S", True), ("n", True), ("N", True), ("y", False), ("Y", False), ("", False),
                                              ("si", False), ("sí", False), ("yes", False), (" s", False)])
def test_en_espanol_solo_cuentan_s_S_n_y_N(mundo, respuesta, vale):
    textos: list[str] = []
    cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--sin-reporte-html"], ahora=lambda: AHORA,
             preguntar=preguntar_y_registrar([respuesta, respuesta, respuesta], textos))
    primeras = [t for t in textos if "lea esta carpeta" in t]
    assert len(primeras) == (1 if vale else 3)  # una letra válida decide en el acto; lo demás se vuelve a preguntar tres veces


@pytest.mark.parametrize("respuesta, vale", [("y", True), ("Y", True), ("n", True), ("N", True), ("s", False), ("S", False), ("", False),
                                              ("yes", False), ("si", False)])
def test_en_ingles_solo_cuentan_y_Y_n_y_N(mundo, respuesta, vale):
    textos: list[str] = []
    cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--sin-reporte-html", "--idioma", "en"], ahora=lambda: AHORA,
             preguntar=preguntar_y_registrar([respuesta, respuesta, respuesta], textos))
    primeras = [t for t in textos if "allowed to read this folder" in t]
    assert len(primeras) == (1 if vale else 3)
