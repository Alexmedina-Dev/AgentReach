"""Historia 41: se ve que AgentReach avanza mientras revisa.

Una sola línea por la salida de errores, que se reescribe con ``\\r``: paso X de 12, carpetas y tiempo. Solo con terminal interactiva de
punta a punta; en cualquier otro caso la salida es idéntica a la de siempre. Nunca nombres de archivo ni valores.
"""

from __future__ import annotations

import io
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest

from agentreach import cli
from agentreach.app import auditar as modulo_auditar
from agentreach.contracts import Idioma
from agentreach.reporting.avance import Avance
from agentreach.reporting.formato import Color

pytestmark = [pytest.mark.sin_tope_por_nombre, pytest.mark.terminal_real]

AHORA = datetime(2026, 11, 12, 9, 0, 0)
CANARIO_NOMBRE = "ZQX-NOMBRE-CANARIO"
CANARIO_VALOR = "ZQX-VALOR-CANARIO-987"
TOTAL = len(modulo_auditar._detectores)  # los pasos de la barra son los detectores del registro


class Tty(io.StringIO):
    encoding = "utf-8"

    def isatty(self) -> bool:
        return True


class SinTty(io.StringIO):
    encoding = "utf-8"

    def isatty(self) -> bool:
        return False


class Ascii(Tty):
    encoding = "ascii"


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    for nombre in ("NO_COLOR", "TERM", "COLORTERM", "AGENTREACH_IDIOMA", "AGENTREACH_TONO", "AGENTREACH_NO_BANNER", "AGENTREACH_ASCII"):
        monkeypatch.delenv(nombre, raising=False)
    monkeypatch.setattr(cli, "activar_vt", lambda *a: True)
    monkeypatch.setattr(cli, "idioma_regional", lambda: "es")
    monkeypatch.setattr(cli, "_interactivo", lambda: True)  # la entrada ya se vigila en ``_crear_avance`` con sys.stdin
    monkeypatch.setattr(cli, "_avance_por_defecto", True)
    monkeypatch.setattr(cli, "_crear_reporte_por_defecto", False)
    monkeypatch.setattr(cli, "abrir_navegador", lambda ruta: True)


def _mundo(tmp_path: Path) -> Path:
    casa = tmp_path / "casa"
    casa.mkdir(parents=True)
    proyecto = tmp_path / "proyecto"
    (proyecto / "a" / "b").mkdir(parents=True)
    (proyecto / ".env").write_text(f"STRIPE_SECRET_KEY={CANARIO_VALOR}\n", encoding="utf-8")
    (proyecto / "a" / "b" / f"{CANARIO_NOMBRE}.txt").write_text("hola\n", encoding="utf-8")
    return proyecto


def _correr(monkeypatch, tmp_path, argv=(), *, stdin=None, stdout=None, stderr=None, columnas=80, entorno=None):
    proyecto = _mundo(tmp_path)
    salida, errores = stdout or Tty(), stderr or Tty()
    monkeypatch.setattr(sys, "stdin", stdin or Tty())
    monkeypatch.setattr(sys, "stdout", salida)
    monkeypatch.setattr(sys, "stderr", errores)
    monkeypatch.setattr(cli.shutil, "get_terminal_size", lambda fallback=(80, 24): os.terminal_size((columnas, 24)))
    for k, v in (entorno or {}).items():
        monkeypatch.setenv(k, v)
    codigo = cli.main([str(proyecto), "--home", str(tmp_path / "casa"), "--no-banner", "--idioma", "es", *argv],
                      ahora=lambda: AHORA, preguntar=lambda t: "s")
    return codigo, salida.getvalue(), errores.getvalue()


def _hay_avance(errores: str) -> bool:
    return "\r" in errores and "paso" in errores


# ---- terminal interactiva ------------------------------------------------------------------------------------------------------


def test_en_terminal_la_linea_se_reescribe_con_paso_carpetas_y_se_borra(monkeypatch, tmp_path):
    codigo, salida, errores = _correr(monkeypatch, tmp_path)
    assert codigo in (0, 1)
    assert f"paso 1 de {TOTAL}" in errores and f"paso {TOTAL} de {TOTAL}" in errores
    assert "Evaluando los hallazgos" in errores and "Preparando el reporte" in errores
    assert "carpetas" in errores
    assert errores.rstrip(" ").endswith("\r")  # al terminar, la línea se borró y el cursor quedó al inicio
    ultimo_dibujo = errores.split("\r")[-2]
    assert ultimo_dibujo.strip() == ""  # lo último escrito es el borrado: solo espacios
    assert "\x1b[" in errores and "\x1b[0m" in errores  # con color (24 bits o 16) pinta la línea
    assert "paso" not in salida and "\r" not in salida  # el reporte no lleva restos


def test_el_reporte_es_identico_con_y_sin_avance(monkeypatch, tmp_path):
    _, con, _ = _correr(monkeypatch, tmp_path / "a")
    monkeypatch.setattr(cli, "_avance_por_defecto", False)
    _, sin, _ = _correr(monkeypatch, tmp_path / "b")
    assert con.replace(str(tmp_path / "a"), "RAIZ") == sin.replace(str(tmp_path / "b"), "RAIZ")


# ---- sin avance ----------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("caso", ["stdout_redirigido", "stderr_redirigido", "stdin_redirigido", "salida", "term_dumb"])
def test_fuera_de_una_terminal_interactiva_no_hay_avance(monkeypatch, tmp_path, caso):
    kwargs: dict = {}
    argv: list[str] = []
    if caso == "stdout_redirigido":
        kwargs["stdout"] = SinTty()
    elif caso == "stderr_redirigido":
        kwargs["stderr"] = SinTty()
    elif caso == "stdin_redirigido":
        kwargs["stdin"] = SinTty()
    elif caso == "salida":
        argv = ["--salida", str(tmp_path / "reporte.txt")]
    elif caso == "term_dumb":
        kwargs["entorno"] = {"TERM": "dumb"}
    _, _, errores = _correr(monkeypatch, tmp_path, argv, **kwargs)
    assert "\r" not in errores and "paso" not in errores and "Evaluando" not in errores


def test_con_json_no_hay_avance(monkeypatch, tmp_path):
    codigo, _, errores = _correr(monkeypatch, tmp_path, ["--json"])
    assert codigo == 2 and "\r" not in errores


def test_no_color_deja_el_avance_sin_secuencias(monkeypatch, tmp_path):
    _, _, errores = _correr(monkeypatch, tmp_path, entorno={"NO_COLOR": "1"})
    assert _hay_avance(errores) and "\x1b" not in errores


# ---- ancho, codificación, idioma -----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("columnas", [20, 30, 59, 60, 80, 140])
def test_la_linea_cabe_en_el_ancho_y_no_se_parte(monkeypatch, tmp_path, columnas):
    _, _, errores = _correr(monkeypatch, tmp_path, columnas=columnas, entorno={"NO_COLOR": "1"})
    limite = max(min(max(columnas, 20), 100) - 1, 20)
    dibujos = [t for t in errores.split("\r") if "paso" in t or "Evaluando" in t or "Preparando" in t or f"/{TOTAL}" in t]
    assert dibujos
    for dibujo in dibujos:
        linea = dibujo.split("\n")[0].rstrip()
        assert 0 < len(linea) <= limite, (columnas, linea)


def test_sin_utf8_la_linea_es_ascii(monkeypatch, tmp_path):
    _, _, errores = _correr(monkeypatch, tmp_path, stderr=Ascii(), entorno={"NO_COLOR": "1"})
    dibujos = "".join(t for t in errores.split("\r") if "paso" in t or "Evaluando" in t)
    assert f"paso 1 de {TOTAL}" in dibujos
    assert dibujos.isascii() and "#" in dibujos and "█" not in dibujos


def test_en_ingles_el_catalogo_sale_en_ingles():
    salida = Tty()
    avance = Avance(salida, Idioma.EN, lambda: 80, reloj=iter(range(100)).__next__)
    avance("paso", 3, 12)
    avance("carpetas", 1240, 0)
    avance.cerrar()
    assert "Checking… step 3 of 12" in salida.getvalue() and "1,240 folders" in salida.getvalue()


def test_unidad_formato_en_espanol_con_barra_y_tiempo():
    salida = Tty()
    ahora = [0.0]
    avance = Avance(salida, Idioma.ES, lambda: 100, reloj=lambda: ahora[0])
    avance("paso", 3, 12)
    ahora[0] = 8.4
    avance("carpetas", 1240, 0)
    primera, segunda = salida.getvalue().split("\r")[1:3]
    assert primera.strip() == "Revisando… paso 3 de 12 [██░░░░░░░░] · 0 s"
    assert segunda.strip() == "Revisando… paso 3 de 12 [██░░░░░░░░] · 1 240 carpetas · 8 s"


def test_el_limite_de_actualizacion_no_redibuja_por_cada_carpeta():
    salida = Tty()
    ahora = [0.0]
    avance = Avance(salida, Idioma.ES, lambda: 80, color=Color.NINGUNO, reloj=lambda: ahora[0])
    avance("paso", 1, 12)
    dibujos = salida.getvalue().count("\r")
    for n in range(1, 50):
        avance("carpetas", n, 0)  # el reloj no avanza: ninguna se dibuja
    assert salida.getvalue().count("\r") == dibujos
    ahora[0] = 1.0
    avance("carpetas", 50, 0)
    assert salida.getvalue().count("\r") == dibujos + 1


def test_cerrar_sin_haber_dibujado_no_escribe_nada_y_es_idempotente():
    salida = Tty()
    avance = Avance(salida, Idioma.ES, lambda: 80)
    avance.cerrar()
    avance.cerrar()
    assert salida.getvalue() == ""


# ---- canario, fallos, Ctrl+C ---------------------------------------------------------------------------------------------------


def test_el_avance_no_muestra_nombres_ni_valores(monkeypatch, tmp_path):
    _, _, errores = _correr(monkeypatch, tmp_path)
    dibujos = "".join(t for t in errores.split("\r") if "paso" in t or "Evaluando" in t or "Preparando" in t)
    assert dibujos and CANARIO_VALOR not in errores and CANARIO_NOMBRE not in errores
    assert ".env" not in dibujos and str(tmp_path) not in dibujos


def test_ctrl_c_borra_la_linea_y_sale_con_130(monkeypatch, tmp_path):
    def interrumpe(self, proyecto, al_avanzar=None):
        if al_avanzar is not None:
            al_avanzar(1, TOTAL)
        raise KeyboardInterrupt

    monkeypatch.setattr(modulo_auditar.Pipeline, "ejecutar", interrumpe)
    codigo, _, errores = _correr(monkeypatch, tmp_path)
    assert codigo == 130
    antes, _, mensaje = errores.rpartition("\r")
    assert mensaje.lstrip().startswith(("\nCancel", "Cancel", "\nSe canc", "Se canc")) or "ancel" in mensaje
    assert f"paso 1 de {TOTAL}" in antes
    ultimo_borrado = antes.split("\r")[-1]
    assert ultimo_borrado.strip() == ""  # lo último antes del mensaje es la línea en blanco


def test_un_detector_que_falla_borra_la_linea_antes_del_mensaje_de_error(monkeypatch, tmp_path):
    def falla(self, proyecto, al_avanzar=None):
        if al_avanzar is not None:
            al_avanzar(2, TOTAL)
        raise RuntimeError("El detector X falló")

    monkeypatch.setattr(modulo_auditar.Pipeline, "ejecutar", falla)
    codigo, _, errores = _correr(monkeypatch, tmp_path)
    assert codigo == 3
    antes, _, mensaje = errores.rpartition("\r")
    assert f"paso 2 de {TOTAL}" in antes and antes.split("\r")[-1].strip() == ""
    assert mensaje.strip()  # el mensaje de error sale tras el borrado


def test_auditar_sin_avance_da_el_mismo_resultado_que_con_avance(tmp_path):
    from agentreach.config import Configuracion

    proyecto = _mundo(tmp_path)
    config = Configuracion(home=str(tmp_path / "casa"))
    eventos: list[tuple[str, int, int]] = []
    con = modulo_auditar.auditar(str(proyecto), config, avance=lambda e, a, b: eventos.append((e, a, b)))
    sin = modulo_auditar.auditar(str(proyecto), config)
    assert con.hallazgos == sin.hallazgos and con.no_revisados == sin.no_revisados and con.archivos_mirados == sin.archivos_mirados
    pasos = [(a, b) for e, a, b in eventos if e == "paso"]
    assert pasos == [(n, TOTAL) for n in range(1, 13)]
    assert [e for e, _, _ in eventos if e in ("evaluando", "reporte")] == ["evaluando", "reporte"]
    assert eventos[-1][0] != "carpetas" and eventos.index(("reporte", 0, 0)) > max(i for i, e in enumerate(eventos) if e[0] == "carpetas")
    cantidades = [a for e, a, _ in eventos if e == "carpetas"]
    assert cantidades == sorted(cantidades) and cantidades[-1] >= 3  # carpetas distintas: raíz, a y a/b


# ---- el avance es cosmético: nunca aborta ni cambia la revisión -----------------------------------------------------------------


class FlujoRoto(Tty):
    def write(self, texto):
        raise OSError("cerrado")


class FlujoUnaVez(Tty):
    """Lanza UnicodeEncodeError en la primera escritura y luego escribe normal."""

    def __init__(self):
        super().__init__()
        self.fallos = 0

    def write(self, texto):
        if self.fallos == 0:
            self.fallos += 1
            raise UnicodeEncodeError("ascii", "é", 0, 1, "no")
        return super().write(texto)


class CodificacionDesconocida(Tty):
    encoding = "codificacion-que-no-existe"

    def write(self, texto):
        raise UnicodeEncodeError("ascii", "é", 0, 1, "no")


def test_un_flujo_que_falla_no_lanza_y_apaga_el_avance():
    roto = FlujoRoto()
    avance = Avance(roto, Idioma.ES, lambda: 80)
    avance("paso", 1, TOTAL)
    avance.cerrar()
    avance("paso", 2, TOTAL)  # apagado: no hace nada ni lanza
    assert roto.getvalue() == ""


def test_un_error_de_codificacion_se_reemplaza_y_una_codificacion_desconocida_no_lanza():
    una_vez = FlujoUnaVez()
    avance = Avance(una_vez, Idioma.ES, lambda: 80)
    avance("paso", 1, TOTAL)
    avance.cerrar()
    assert una_vez.fallos == 1 and "paso 1 de" in una_vez.getvalue()
    desconocida = CodificacionDesconocida()
    otro = Avance(desconocida, Idioma.ES, lambda: 80)
    otro("paso", 1, TOTAL)
    otro.cerrar()
    otro("paso", 2, TOTAL)
    assert desconocida.getvalue() == ""


def test_un_fallo_de_columnas_no_aborta_auditar(tmp_path):
    from agentreach.config import Configuracion

    def columnas():
        raise RuntimeError("sin tamaño")

    proyecto = _mundo(tmp_path)
    config = Configuracion(home=str(tmp_path / "casa"))
    salida = Tty()
    avance = Avance(salida, Idioma.ES, columnas)
    con = modulo_auditar.auditar(str(proyecto), config, avance=avance)
    avance.cerrar()
    sin = modulo_auditar.auditar(str(proyecto), config)
    assert con.hallazgos == sin.hallazgos and salida.getvalue() == ""


def test_tiempo_de_mas_de_un_minuto_y_singular_de_carpeta():
    salida = Tty()
    ahora = [0.0]
    avance = Avance(salida, Idioma.ES, lambda: 100, color=Color.NINGUNO, reloj=lambda: ahora[0])
    avance("paso", 1, TOTAL)
    ahora[0] = 61.0
    avance("carpetas", 1, 0)
    assert salida.getvalue().split("\r")[-1].strip().endswith("1 carpeta · 1 min 1 s")


def test_en_ascii_el_millar_no_lleva_separador():
    salida = Tty()
    avance = Avance(salida, Idioma.ES, lambda: 100, ascii_=True, reloj=iter(range(100)).__next__)
    avance("paso", 1, TOTAL)
    avance("carpetas", 1240, 0)
    ultimo = salida.getvalue().split("\r")[-1]
    assert "1240 carpetas" in ultimo and ultimo.isascii()


@pytest.mark.parametrize("fase,texto", [("evaluando", "Evaluando los hallazgos…"), ("reporte", "Preparando el reporte…")])
def test_las_fases_finales_tambien_muestran_las_carpetas(fase, texto):
    salida = Tty()
    ahora = [0.0]
    avance = Avance(salida, Idioma.ES, lambda: 100, color=Color.NINGUNO, reloj=lambda: ahora[0])
    avance("paso", TOTAL, TOTAL)
    ahora[0] = 5.0
    avance("carpetas", 1240, 0)
    avance(fase, 0, 0)
    assert salida.getvalue().split("\r")[-1].strip() == f"{texto} · 1 240 carpetas · 5 s"
