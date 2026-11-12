"""Historias 21 y 22: AgentReach es una herramienta de terminal que opera una persona.

Flujo: sin terminal interactiva no lee nada (y no existe un ``--permitir``); banner mediano con aire, qué es y qué hace; pregunta
de lectura (solo s, S, n y N cuentan; lo demás se vuelve a preguntar y tras tres intentos se sale sin leer); resumen corto por nivel
con lo más urgente (``--detalle`` para el listado completo); reporte HTML en ``AgentReach-reportes`` (fuera de la carpeta revisada);
pregunta de abrirlo en el navegador (misma regla, recordada) y ``--abrir``.

Las pruebas comunes (``tests/conftest.py``) responden por la persona; aquí se usan las preguntas y la terminal de verdad.
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import pytest

from agentreach import cli
from agentreach.cli import _interactivo as INTERACTIVO_REAL
from agentreach.cli import reportes
from agentreach.reporting.marca import LEMA

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

AHORA = datetime(2026, 11, 10, 15, 30, 5)
INVALIDAS = ["", " ", "si", "sí", "SI", "y", "yes", "no", "NO", "ss", " s", "s ", "1", "cualquier cosa"]


class Tty(io.StringIO):
    encoding = "utf-8"

    def isatty(self) -> bool:
        return True


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    for nombre in ("NO_COLOR", "TERM", "COLORTERM", "AGENTREACH_IDIOMA", "AGENTREACH_TONO", "AGENTREACH_NO_BANNER", "AGENTREACH_ASCII"):
        monkeypatch.delenv(nombre, raising=False)
    monkeypatch.setattr(cli, "activar_vt", lambda *a: True)
    monkeypatch.setattr(cli, "idioma_regional", lambda: "es")
    monkeypatch.setattr(cli.shutil, "get_terminal_size", lambda fallback=(80, 24): os.terminal_size((100, 24)))
    monkeypatch.setattr(cli, "_interactivo", INTERACTIVO_REAL)  # la detección real de la terminal (las pruebas comunes la fingen)
    monkeypatch.setattr(cli, "_resumen_corto_por_defecto", True)
    monkeypatch.setattr(cli, "_crear_reporte_por_defecto", True)


@pytest.fixture
def mundo(tmp_path: Path) -> dict:
    casa = tmp_path / "casa"
    casa.mkdir()
    proyecto = tmp_path / "proyecto"
    (proyecto / "b").mkdir(parents=True)
    for ruta in (".env", "b/.env", "b/.env.local", "c.env"):
        (proyecto / ruta).write_text("STRIPE_SECRET_KEY=sk_live_valor_largo_123\n", encoding="utf-8")
    return {"casa": casa, "proyecto": proyecto}


@pytest.fixture
def navegador(monkeypatch) -> list[str]:
    abiertos: list[str] = []
    monkeypatch.setattr(cli, "abrir_navegador", lambda ruta: abiertos.append(ruta) or True)
    return abiertos


def plano(texto: str) -> str:
    """Sin colores y con las líneas partidas por el ancho de nuevo unidas: para buscar frases."""
    return " ".join(re.sub(chr(27) + r"\[[0-9;]*m", "", texto).split())


def terminal(monkeypatch) -> io.StringIO:
    """Una persona delante: entrada y salida son una terminal."""
    salida = Tty()
    monkeypatch.setattr(sys, "stdin", Tty())
    monkeypatch.setattr(sys, "stdout", salida)
    return salida


def es_pregunta_de_reglas(texto: str) -> bool:
    return "AgentReach necesita ver las reglas" in texto or "AgentReach needs to see the rules" in texto


def correr(argv, respuestas=(), preguntas=None, reglas=None, preguntas_reglas=None):
    """Responde las preguntas por orden. La de las reglas de fuera del proyecto (segundo nivel) se contesta aparte (por defecto, que sí) y
    no se cuenta en ``preguntas``. En inglés, una «s» de los textos viejos se lee como «y»."""
    cola = list(respuestas)
    cola_reglas = list(reglas) if reglas is not None else None

    def preguntar(texto: str) -> str:
        ingles = "(Y/N)" in texto
        if es_pregunta_de_reglas(texto):
            if preguntas_reglas is not None:
                preguntas_reglas.append(texto)
            respuesta = cola_reglas.pop(0) if cola_reglas else ("y" if ingles else "s")
            return respuesta
        if preguntas is not None:
            preguntas.append(texto)
        if not cola:
            raise AssertionError(f"se preguntó algo inesperado: {texto!r}")
        respuesta = cola.pop(0)
        return {"s": "y", "S": "Y"}.get(respuesta, respuesta) if ingles else respuesta

    return cli.main(argv, ahora=lambda: AHORA, preguntar=preguntar)


def no_preguntar(texto: str) -> str:
    raise AssertionError(f"no debía preguntar: {texto!r}")


def sin_leer(monkeypatch) -> None:
    monkeypatch.setattr(cli, "auditar", lambda *a, **k: pytest.fail("se leyó algo sin autorización"))


def reportes_de(casa: Path) -> list[Path]:
    carpeta = casa / reportes.CARPETA
    return sorted(carpeta.glob("*.html")) if carpeta.is_dir() else []


def args_de(mundo, *extra: str) -> list[str]:
    return [str(mundo["proyecto"]), "--home", str(mundo["casa"]), *extra]


# ---- sin terminal interactiva no se lee nada --------------------------------------------------------------------------------------


def test_sin_terminal_no_lee_nada_ni_pregunta_y_dice_por_que(mundo, monkeypatch, capsys):
    sin_leer(monkeypatch)  # stdin y stdout de pytest no son una terminal
    assert cli.main(args_de(mundo), preguntar=no_preguntar) == 2
    capturado = capsys.readouterr()
    assert "sin una terminal interactiva no lee nada" in " ".join(capturado.err.split()) and capturado.out == ""
    assert reportes_de(mundo["casa"]) == []


@pytest.mark.parametrize("extra", [["--salida", "x.txt"], ["--abrir"], ["--sin-reporte-html"], ["--detalle"], ["--formato", "html", "--salida", "x.html"],
                                   ["--idioma", "en"], ["--agente", "opencode"], ["--no-banner"], ["--estricto"]])
def test_ninguna_opcion_permite_leer_sin_terminal(mundo, monkeypatch, capsys, extra, tmp_path):
    sin_leer(monkeypatch)
    extra = [str(tmp_path / e) if e.endswith((".txt", ".html")) else e for e in extra]
    assert cli.main(args_de(mundo, *extra), preguntar=no_preguntar) == 2
    assert not (tmp_path / "x.txt").exists() and not (tmp_path / "x.html").exists()


def test_solo_una_de_las_dos_no_basta(mundo, monkeypatch):
    sin_leer(monkeypatch)
    monkeypatch.setattr(sys, "stdin", Tty())  # entrada sí, salida redirigida
    assert cli.main(args_de(mundo), preguntar=no_preguntar) == 2
    monkeypatch.setattr(sys, "stdin", io.StringIO())
    monkeypatch.setattr(sys, "stdout", Tty())  # salida sí, entrada redirigida
    assert cli.main(args_de(mundo), preguntar=no_preguntar) == 2


def test_no_existe_un_permiso_para_saltarse_la_pregunta(mundo, monkeypatch):
    opciones = {o for accion in cli.construir_parser()._actions for o in accion.option_strings}
    assert not opciones & {"--permitir", "--si", "--yes", "--sí", "--forzar", "--force", "-y", "--no-preguntar", "--confirmar"}
    sin_leer(monkeypatch)
    with pytest.raises(SystemExit):
        cli.main(args_de(mundo, "--permitir"))  # un flag que no existe es un error de argumentos, no un permiso


def test_ni_el_entorno_ni_los_argumentos_responden_por_la_persona(mundo, monkeypatch):
    """El único punto de sustitución es un atributo del módulo, que solo el código de pruebas toca."""
    for nombre in ("AGENTREACH_PERMITIR", "AGENTREACH_SI", "AGENTREACH_YES", "AGENTREACH_PREGUNTAR", "CI", "AGENTREACH_PRUEBAS"):
        monkeypatch.setenv(nombre, "1")
    sin_leer(monkeypatch)
    assert cli.main(args_de(mundo), preguntar=no_preguntar) == 2


# ---- banner, qué es y qué hace --------------------------------------------------------------------------------------------------


def test_banner_mediano_con_aire_y_luego_que_es_que_hace_y_que_no(mundo, monkeypatch, capsys):
    salida = terminal(monkeypatch)
    correr(args_de(mundo, "--no-abrir"), respuestas=["n"])
    texto = salida.getvalue()
    assert texto.startswith("\n\n\n") and "▄▀▀▀▄" in texto.split("\n")[3] and "█   █  ███  █████" not in texto  # tres en blanco, mediano
    err = capsys.readouterr().err
    assert "audita, en solo lectura" in err and "Qué hace:" in err and "Qué no hace:" in err
    err = " ".join(err.split())
    assert "no cambia nada del proyecto" in err and "no usa la red" in err and "no ejecuta los programas del proyecto" in err
    assert "no muestra valores de secretos" in err
    assert "solo guarda el reporte fuera de la carpeta revisada, y solo abre el navegador con permiso" in err.lower()


def test_sin_banner_igual_se_explica_y_se_pide_permiso(mundo, monkeypatch, capsys):
    terminal(monkeypatch)
    preguntas: list[str] = []
    correr(args_de(mundo, "--no-banner"), respuestas=["n"], preguntas=preguntas)
    assert "Qué no hace:" in capsys.readouterr().err and len(preguntas) == 1


def test_la_ayuda_muestra_el_banner_grande(monkeypatch):
    salida = terminal(monkeypatch)
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    texto = salida.getvalue()
    assert "█   █  ███  █████" in texto and LEMA in texto and "--abrir" in texto and "--sin-reporte-html" in texto


# ---- la pregunta de leer: solo s, S, n y N -------------------------------------------------------------------------------------


@pytest.mark.parametrize("respuesta", ["s", "S"])
def test_s_y_S_autorizan_la_lectura(mundo, monkeypatch, respuesta):
    terminal(monkeypatch)
    assert correr(args_de(mundo, "--no-abrir"), respuestas=[respuesta]) == 1


@pytest.mark.parametrize("respuesta", ["n", "N"])
def test_n_y_N_no_leen_nada(mundo, monkeypatch, capsys, respuesta):
    terminal(monkeypatch)
    sin_leer(monkeypatch)
    assert correr(args_de(mundo), respuestas=[respuesta]) == 2
    assert "No se leyó nada" in capsys.readouterr().err and reportes_de(mundo["casa"]) == []


def test_la_pregunta_muestra_la_carpeta_y_pide_s_o_n(mundo, monkeypatch):
    terminal(monkeypatch)
    preguntas: list[str] = []
    correr(args_de(mundo, "--no-abrir"), respuestas=["s"], preguntas=preguntas)
    assert str(mundo["proyecto"]) in preguntas[0] and "(S/N)" in preguntas[0] and "(s/n)" not in preguntas[0]


@pytest.mark.parametrize("invalida", INVALIDAS)
def test_lo_que_no_es_s_o_n_no_decide_y_se_vuelve_a_preguntar(mundo, monkeypatch, invalida, capsys):
    terminal(monkeypatch)
    preguntas: list[str] = []
    assert correr(args_de(mundo, "--no-abrir"), respuestas=[invalida, "s"], preguntas=preguntas) == 1
    assert len(preguntas) == 2 and "Solo se acepta S o N" in capsys.readouterr().err


@pytest.mark.parametrize("invalida", INVALIDAS)
def test_tres_intentos_invalidos_salen_sin_leer(mundo, monkeypatch, invalida, capsys):
    terminal(monkeypatch)
    sin_leer(monkeypatch)
    preguntas: list[str] = []
    assert correr(args_de(mundo), respuestas=[invalida] * 3, preguntas=preguntas) == 2
    assert len(preguntas) == 3 and "después de 3 intentos" in capsys.readouterr().err and reportes_de(mundo["casa"]) == []


def test_una_respuesta_valida_en_el_tercer_intento_cuenta(mundo, monkeypatch):
    terminal(monkeypatch)
    assert correr(args_de(mundo, "--no-abrir"), respuestas=["", "x", "S"]) == 1


def test_la_entrada_cerrada_no_autoriza(mundo, monkeypatch):
    terminal(monkeypatch)
    sin_leer(monkeypatch)

    def cerrada(texto: str) -> str:
        raise EOFError

    assert cli.main(args_de(mundo), preguntar=cerrada) == 2


def test_la_carpeta_personal_y_la_raiz_llevan_una_advertencia_en_la_misma_pregunta(mundo, monkeypatch):
    terminal(monkeypatch)
    monkeypatch.chdir(mundo["casa"])
    preguntas: list[str] = []
    assert correr(["--home", str(mundo["casa"])], respuestas=["n"], preguntas=preguntas) == 2
    assert len(preguntas) == 1 and "ATENCIÓN" in preguntas[0] and "la carpeta personal" in preguntas[0]
    monkeypatch.chdir(os.path.abspath(os.sep))
    preguntas.clear()
    correr(["--home", str(mundo["casa"])], respuestas=["n"], preguntas=preguntas)
    assert "la raíz de un disco" in preguntas[0]
    preguntas.clear()
    correr(args_de(mundo), respuestas=["n"], preguntas=preguntas)
    assert "ATENCIÓN" not in preguntas[0]


def test_sin_ruta_revisa_la_carpeta_actual_despues_de_preguntar(mundo, monkeypatch, capsys):
    terminal(monkeypatch)
    monkeypatch.chdir(mundo["proyecto"])
    preguntas: list[str] = []
    assert correr(["--home", str(mundo["casa"]), "--sin-reporte-html"], respuestas=["s"], preguntas=preguntas) == 1
    assert str(mundo["proyecto"]) in preguntas[0]


def test_en_ingles_la_pregunta_y_los_avisos(mundo, monkeypatch, capsys):
    terminal(monkeypatch)
    preguntas: list[str] = []
    correr(args_de(mundo, "--idioma", "en", "--no-abrir"), respuestas=["", "s"], preguntas=preguntas)
    assert "Is AgentReach allowed to read this folder?" in preguntas[0] and "(Y/N)" in preguntas[0]
    err = capsys.readouterr().err
    assert "Only Y or N is accepted" in err and "What it does not do:" in err


# ---- el resumen corto y --detalle ---------------------------------------------------------------------------------------------


def test_la_terminal_muestra_un_resumen_corto_con_lo_mas_urgente_y_no_el_listado(mundo, monkeypatch):
    salida = terminal(monkeypatch)
    correr(args_de(mundo, "--no-abrir", "--sin-reporte-html"), respuestas=["s"])
    texto = salida.getvalue()
    assert "RESUMEN" in texto and "LO MÁS URGENTE  (3 de " in texto
    urgentes = texto.split("LO MÁS URGENTE")[1].split("Esto cubre solo")[0]
    assert urgentes.count("COMPROBADO") == 3  # exactamente tres
    assert "Qué significa" not in texto and "Nivel y por qué" not in texto and "TH-1" not in texto  # no se vuelca el listado
    assert "--detalle" in texto
    assert "Esto cubre solo lo que AgentReach pudo revisar" in plano(texto) and "no significa que lo demás sea seguro" in plano(texto).lower()
    assert len(texto.splitlines()) < 60


def test_detalle_muestra_el_listado_completo_con_codigos(mundo, monkeypatch):
    salida = terminal(monkeypatch)
    correr(args_de(mundo, "--detalle", "--no-abrir", "--sin-reporte-html"), respuestas=["s"])
    texto = salida.getvalue()
    assert "Qué significa" in texto and "TH-1" in texto and "LO MÁS URGENTE" not in texto
    for ruta in (".env", "c.env"):
        assert ruta in texto


def test_con_salida_el_archivo_lleva_el_listado_completo(mundo, monkeypatch, tmp_path):
    terminal(monkeypatch)
    destino = tmp_path / "r.txt"
    assert correr(args_de(mundo, "--salida", str(destino)), respuestas=["s"]) == 1
    texto = destino.read_text(encoding="utf-8")
    assert "Qué significa" in texto and "LO MÁS URGENTE" not in texto


def test_sin_hallazgos_dice_que_no_encontro_nada_en_lo_que_pudo_revisar_y_nunca_seguro(tmp_path, monkeypatch):
    casa = tmp_path / "casa"
    casa.mkdir()
    vacio = tmp_path / "vacio"
    vacio.mkdir()
    from agentreach.app.auditar import ResultadoAuditoria

    monkeypatch.setattr(cli, "auditar", lambda *a, **k: ResultadoAuditoria((), (), 12))  # nada encontrado
    salida = terminal(monkeypatch)
    correr([str(vacio), "--home", str(casa), "--no-abrir", "--sin-reporte-html"], respuestas=["s"])
    texto = plano(salida.getvalue())
    assert "No se encontró nada en lo que se pudo revisar" in texto
    assert "seguro" not in texto.lower().replace("no significa que lo demás sea seguro", "")  # solo para negarlo


def test_el_resumen_en_ingles(mundo, monkeypatch):
    salida = terminal(monkeypatch)
    correr(args_de(mundo, "--idioma", "en", "--no-abrir", "--sin-reporte-html"), respuestas=["s"])
    assert "MOST URGENT  (3 of " in plano(salida.getvalue()).replace("MOST URGENT (", "MOST URGENT  (") and "does not mean the rest is safe" in plano(salida.getvalue())


# ---- el reporte HTML ---------------------------------------------------------------------------------------------------------------


def test_crea_el_reporte_html_fuera_de_la_carpeta_y_dice_donde_y_que_se_vera(mundo, monkeypatch):
    salida = terminal(monkeypatch)
    correr(args_de(mundo, "--no-abrir"), respuestas=["s"])
    [archivo] = reportes_de(mundo["casa"])
    assert archivo.name == "agentreach-20261110-153005-proyecto.html" and not str(archivo).startswith(str(mundo["proyecto"]))
    assert not any(p.name.endswith(".html") for p in mundo["proyecto"].rglob("*"))
    texto = salida.getvalue()
    assert f"Reporte HTML guardado en: {archivo}" in " ".join(texto.split()) and "el resumen por nivel, la lista de hallazgos y la tabla" in " ".join(texto.split())
    html = archivo.read_text(encoding="utf-8")
    assert "sk_live_valor_largo_123" not in html and '"schema_version":1' in html


def test_el_reporte_nunca_pisa_uno_anterior(mundo, monkeypatch):
    terminal(monkeypatch)
    for _ in range(3):
        correr(args_de(mundo, "--no-abrir"), respuestas=["s"])
    assert [p.name for p in reportes_de(mundo["casa"])] == [
        "agentreach-20261110-153005-proyecto-2.html", "agentreach-20261110-153005-proyecto-3.html", "agentreach-20261110-153005-proyecto.html"]


def test_con_salida_o_sin_reporte_html_no_se_crea_nada_en_la_carpeta_personal(mundo, monkeypatch, tmp_path):
    terminal(monkeypatch)
    correr(args_de(mundo, "--sin-reporte-html"), respuestas=["s", "n"])
    correr(args_de(mundo, "--salida", str(tmp_path / "r.txt")), respuestas=["s"])
    correr(args_de(mundo, "--formato", "html", "--salida", str(tmp_path / "r.html")), respuestas=["s"])
    assert not (mundo["casa"] / reportes.CARPETA).exists()


def test_si_la_carpeta_de_reportes_cae_dentro_de_la_revisada_no_se_escribe_y_se_dice(mundo, monkeypatch, capsys):
    terminal(monkeypatch)
    casa_dentro = mundo["proyecto"] / "casa"
    casa_dentro.mkdir()
    antes = sorted(p.name for p in mundo["proyecto"].rglob("*"))
    assert correr([str(mundo["proyecto"]), "--home", str(casa_dentro), "--no-abrir"], respuestas=["s"]) == 1
    assert sorted(p.name for p in mundo["proyecto"].rglob("*")) == antes
    assert "AgentReach no escribe ahí" in capsys.readouterr().err


def test_si_agentreach_reportes_es_un_enlace_no_se_escribe_a_traves_de_el(mundo, tmp_path, monkeypatch, capsys):
    destino = tmp_path / "otro"
    destino.mkdir()
    try:
        os.symlink(destino, mundo["casa"] / reportes.CARPETA, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("este sistema no permite crear enlaces simbólicos")
    terminal(monkeypatch)
    correr(args_de(mundo, "--no-abrir"), respuestas=["s"])
    assert list(destino.iterdir()) == [] and "enlace" in capsys.readouterr().err


def test_un_fallo_al_escribir_no_cambia_el_codigo_de_salida(mundo, monkeypatch, capsys):
    terminal(monkeypatch)
    monkeypatch.setattr(reportes.os, "makedirs", lambda *a, **k: (_ for _ in ()).throw(OSError("disco lleno")))
    assert correr(args_de(mundo, "--no-abrir"), respuestas=["s"]) == 1
    assert "no se pudo escribir el archivo" in capsys.readouterr().err


def test_en_ingles_el_aviso_del_reporte(mundo, monkeypatch):
    salida = terminal(monkeypatch)
    correr(args_de(mundo, "--idioma", "en", "--no-abrir"), respuestas=["s"])
    assert "HTML report saved at:" in salida.getvalue() and "summary by level" in salida.getvalue()


# ---- abrir en el navegador -------------------------------------------------------------------------------------------------------


def test_la_pregunta_de_abrir_se_hace_una_vez_y_la_respuesta_se_recuerda(mundo, monkeypatch, navegador):
    terminal(monkeypatch)
    preguntas: list[str] = []
    correr(args_de(mundo), respuestas=["s", "s"], preguntas=preguntas)
    assert len(preguntas) == 2 and preguntas[1] == "¿Abrir el reporte en el navegador? (S/N) "
    [primero] = reportes_de(mundo["casa"])
    assert navegador == [str(primero)]
    preferencias = mundo["casa"] / reportes.CARPETA / "preferencias.json"
    assert json.loads(preferencias.read_text(encoding="utf-8")) == {"abrir_en_navegador": True}
    preguntas.clear()  # la segunda vez solo pregunta lo de leer; lo de abrir ya está decidido
    cli.main(args_de(mundo), ahora=lambda: datetime(2026, 11, 10, 15, 31, 0), preguntar=lambda t: preguntas.append(t) or "s")
    # la segunda vez solo pregunta lo de leer y lo de las reglas; lo de abrir ya está decidido
    assert len(preguntas) == 2 and "lea esta carpeta" in preguntas[0] and es_pregunta_de_reglas(preguntas[1]) and len(navegador) == 2


@pytest.mark.parametrize("respuesta", ["n", "N"])
def test_n_y_N_no_abren_y_se_recuerdan(mundo, monkeypatch, navegador, respuesta):
    terminal(monkeypatch)
    correr(args_de(mundo), respuestas=["s", respuesta])
    assert navegador == []
    guardado = json.loads((mundo["casa"] / reportes.CARPETA / "preferencias.json").read_text(encoding="utf-8"))
    assert guardado == {"abrir_en_navegador": False}


@pytest.mark.parametrize("respuesta", ["s", "S"])
def test_s_y_S_abren(mundo, monkeypatch, navegador, respuesta):
    terminal(monkeypatch)
    correr(args_de(mundo), respuestas=["s", respuesta])
    assert len(navegador) == 1


@pytest.mark.parametrize("invalida", INVALIDAS)
def test_al_abrir_lo_que_no_es_s_o_n_se_vuelve_a_preguntar(mundo, monkeypatch, navegador, invalida):
    terminal(monkeypatch)
    preguntas: list[str] = []
    correr(args_de(mundo), respuestas=["s", invalida, "s"], preguntas=preguntas)
    assert len(preguntas) == 3 and len(navegador) == 1


@pytest.mark.parametrize("invalida", INVALIDAS)
def test_al_abrir_tres_intentos_invalidos_ni_abren_ni_recuerdan(mundo, monkeypatch, navegador, invalida, capsys):
    terminal(monkeypatch)
    preguntas: list[str] = []
    assert correr(args_de(mundo), respuestas=["s", invalida, invalida, invalida], preguntas=preguntas) == 1
    assert len(preguntas) == 4 and navegador == []
    assert not (mundo["casa"] / reportes.CARPETA / "preferencias.json").exists()
    assert "no se abrió el reporte ni se recordó nada" in " ".join(capsys.readouterr().err.split())


def test_abrir_abre_sin_preguntar_lo_de_abrir_y_no_recuerda_nada(mundo, monkeypatch, navegador):
    terminal(monkeypatch)
    preguntas: list[str] = []
    correr(args_de(mundo, "--abrir"), respuestas=["s"], preguntas=preguntas)
    assert len(preguntas) == 1 and len(navegador) == 1 and navegador[0].endswith(".html")
    assert not (mundo["casa"] / reportes.CARPETA / "preferencias.json").exists()


def test_no_abrir_no_abre_ni_pregunta_lo_de_abrir(mundo, monkeypatch, navegador):
    terminal(monkeypatch)
    preguntas: list[str] = []
    correr(args_de(mundo, "--no-abrir"), respuestas=["s"], preguntas=preguntas)
    assert len(preguntas) == 1 and navegador == []


def test_una_preferencia_ilegible_se_ignora_y_se_vuelve_a_preguntar(mundo, monkeypatch, navegador):
    carpeta = mundo["casa"] / reportes.CARPETA
    carpeta.mkdir()
    (carpeta / "preferencias.json").write_text("esto no es json", encoding="utf-8")
    terminal(monkeypatch)
    preguntas: list[str] = []
    correr(args_de(mundo), respuestas=["s", "s"], preguntas=preguntas)
    assert len(preguntas) == 2 and len(navegador) == 1


def test_si_el_navegador_no_abre_se_avisa_y_el_codigo_no_cambia(mundo, monkeypatch, capsys):
    terminal(monkeypatch)
    monkeypatch.setattr(cli, "abrir_navegador", lambda ruta: False)
    assert correr(args_de(mundo, "--abrir"), respuestas=["s"]) == 1
    assert "no se pudo abrir el navegador" in capsys.readouterr().err


def test_el_navegador_recibe_un_archivo_local_y_nada_si_no_existe(tmp_path, monkeypatch):
    from agentreach.infra import navegador as modulo

    visto: list[str] = []
    monkeypatch.setattr(modulo.webbrowser, "open", lambda url: visto.append(url) or True)
    archivo = tmp_path / "r.html"
    archivo.write_text("x", encoding="utf-8")
    assert modulo.abrir(str(archivo)) is True and visto[0].startswith("file:///") and visto[0].endswith("r.html")
    assert modulo.abrir(str(tmp_path / "no-existe.html")) is False and len(visto) == 1
