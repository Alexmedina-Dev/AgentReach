"""Historia 13b: ancho, color, símbolos, codificación y limpieza al imprimir del reporte de terminal."""

from __future__ import annotations

import io
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import pytest

from agentreach import cli
from agentreach.app.auditar import ResultadoAuditoria
from agentreach.contracts import (
    Ajeno,
    Etiqueta,
    Finding,
    Idioma,
    Location,
    Motivo,
    MotivoNoRevisado,
    Nivel,
    NoRevisado,
    Plataforma,
    Postura,
    Proveedor,
    Ruta,
    Tipo,
)
from agentreach.reporting.formato import (
    RESET,
    Color,
    ajustar,
    ancho_de_trabajo,
    ancho_visible,
    decidir_color,
    fondo_claro,
    pintar,
    preparar_salida,
    ultima_comprobacion,
)
from agentreach.reporting.gate import HallazgoVista, NoRevisadoVista, preparar, ruta_visible
from agentreach.reporting.texto import generar

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

AHORA = datetime(2026, 11, 9, 16, 40)
BASE = str(Path(os.path.abspath("proyecto-falso")))
ESC = chr(27)
SGR = re.compile(ESC + r"\[[0-9;]*m")


class LectorFalso:
    def existe(self, ruta: str) -> bool:
        return True

    def lineas(self, ruta: str):
        return ["# nota", "API_TOKEN=x", "OTRA=y"] * 40


def finding(nombre="a.env", nivel=Nivel.POTENCIAL, motivo=Motivo.NO_DETERMINADO, tipo=Tipo.CREDENCIAL_EN_ARCHIVO, linea=2) -> Finding:
    return Finding(
        ubicacion=Location(Ruta(f"{BASE}/{nombre}"), linea), tipo=tipo, proveedor=Proveedor.PAGOS, nivel=nivel, motivo=motivo,
        ajeno_a_tarea=Ajeno.NO_DETERMINADO, plataforma=Plataforma.CLAUDE_CODE, agente=Etiqueta("claude-code"),
        postura=Postura.SIN_REGLA,
    )


def variado() -> ResultadoAuditoria:
    hallazgos = [
        finding("mi carpeta con espacios/sub dir/mi archivo con nombre bastante largo.env", Nivel.POTENCIAL, Motivo.REGLA_DENY),
        finding("日本語/ファイル.env", Nivel.POTENCIAL, Motivo.EXISTE_NO_LEGIBLE),
        finding("AGENTS.md", Nivel.HIPOTESIS, Motivo.INDICIO_DEBIL, Tipo.CONTEXTO_SOSPECHOSO),
    ]
    no_revisados = [NoRevisado(Ruta(f"{BASE}/x{i}.txt"), m) for i, m in enumerate(MotivoNoRevisado)]
    return ResultadoAuditoria(tuple(hallazgos), tuple(no_revisados), 41)


def datos(res=None):
    return preparar(res or variado(), BASE, ahora=AHORA, home=None, lector=LectorFalso())


# ---- (a) ancho --------------------------------------------------------------------------------------------------------


def test_el_ancho_visible_cuenta_dos_para_los_caracteres_anchos_y_cero_para_los_que_se_pegan():
    assert ancho_visible("abc") == 3 and ancho_visible("日本語") == 6 and ancho_visible("e" + chr(0x301)) == 1


def test_el_ancho_de_trabajo_va_de_60_a_100():
    assert [ancho_de_trabajo(n) for n in (20, 60, 80, 140)] == [60, 60, 80, 100]


@pytest.mark.parametrize("ancho", [40, 60, 80, 140])
def test_ninguna_linea_pasa_del_ancho_menos_uno_salvo_una_ruta_entera(ancho):
    d = datos()
    rutas = {d.carpeta, *(h.ruta for h in d.hallazgos), *(n.ruta for n in d.no_revisados)}
    for idioma in Idioma:
        for detalle in (False, True):
            for linea in generar(d, idioma, detalle=detalle, ancho=ancho).splitlines():
                if ancho_visible(linea) > max(ancho - 1, 20):
                    assert any(r in linea for r in rutas) or " " not in linea.strip(), (ancho, linea)


@pytest.mark.parametrize("ancho", [40, 60, 80, 140])
def test_ninguna_palabra_queda_partida(ancho):
    d = datos()
    ancho_sin_ajuste = generar(d, Idioma.ES, ancho=10_000)
    ajustado = generar(d, Idioma.ES, ancho=ancho)
    assert ajustado.split() == ancho_sin_ajuste.split()  # las mismas palabras, en el mismo orden


def test_ajustar_no_parte_palabras_ni_guiones_y_usa_sangria_francesa():
    lineas = ajustar("--incluir-ubicaciones-sensibles y mas palabras para forzar el corte de linea", 30, 2, 4)
    assert lineas[0].startswith("  --incluir-ubicaciones-sensibles") and all(linea.startswith("    ") for linea in lineas[1:])
    assert all(len(linea) <= 29 or " " not in linea.strip() for linea in lineas)
    assert " ".join(" ".join(lineas).split()) == "--incluir-ubicaciones-sensibles y mas palabras para forzar el corte de linea"


def test_un_nombre_de_ancho_doble_no_descuadra_el_ajuste():
    lineas = ajustar("日本語 " * 20, 30)
    assert all(ancho_visible(linea) <= 29 for linea in lineas)


# ---- (b) color --------------------------------------------------------------------------------------------------------


def test_decidir_color_sigue_la_prioridad_del_diseno():
    sin = {}
    assert decidir_color("nunca", True, {"COLORTERM": "truecolor"}, "linux", True) is Color.NINGUNO
    assert decidir_color("auto", True, {"NO_COLOR": "1"}, "linux", True) is Color.NINGUNO
    assert decidir_color("auto", False, sin, "linux", True) is Color.NINGUNO  # no es una terminal
    assert decidir_color("auto", True, {"TERM": "dumb"}, "linux", True) is Color.NINGUNO
    assert decidir_color("auto", True, sin, "win32", False) is Color.NINGUNO  # no se pudo activar el modo de secuencias
    assert decidir_color("auto", True, sin, "win32", True) is Color.DE_16  # sin señal de 24 bits: 16 colores
    assert decidir_color("siempre", False, sin, "linux", False) is Color.DE_16  # --color siempre aunque no sea una terminal
    for señal in ({"COLORTERM": "truecolor"}, {"COLORTERM": "24bit"}, {"WT_SESSION": "x"}, {"TERM_PROGRAM": "vscode"}):
        assert decidir_color("auto", True, señal, "linux", True) is Color.DE_24_BITS
    assert decidir_color("auto", True, {"NO_COLOR": ""}, "linux", True) is Color.DE_16  # vacío no cuenta


def test_cada_linea_pintada_termina_en_reset_y_sin_color_el_texto_es_identico():
    d = datos()
    plano = generar(d, Idioma.ES, ancho=80)
    for color in (Color.DE_24_BITS, Color.DE_16):
        pintado = generar(d, Idioma.ES, ancho=80, color=color)
        assert SGR.sub("", pintado) == plano
        for linea in pintado.splitlines():
            if ESC in linea:
                assert linea.endswith(RESET), linea
    assert ESC not in plano


def test_con_color_apagado_no_sale_ningun_esc_aunque_haya_nombres_peligrosos():
    res = ResultadoAuditoria((finding("a" + ESC + "[2Jb.env"),), (), 3)
    assert ESC not in generar(datos(res), Idioma.ES)


def test_cli_color_siempre_pinta_y_nunca_no(tmp_path: Path, capsys):
    (tmp_path / ".env").write_text("STRIPE_SECRET_KEY=sk_live_algo_largo_123\n", encoding="utf-8")
    cli.main([str(tmp_path), "--color", "siempre"], ahora=lambda: AHORA)
    con = capsys.readouterr().out
    assert ESC in con and all(linea.endswith(RESET) for linea in con.splitlines() if ESC in linea)
    cli.main([str(tmp_path), "--color", "nunca"], ahora=lambda: AHORA)
    assert ESC not in capsys.readouterr().out
    cli.main([str(tmp_path)], ahora=lambda: AHORA)  # la salida capturada no es una terminal
    assert ESC not in capsys.readouterr().out


def test_no_color_apaga_el_color_en_el_comando(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    cli.main([str(tmp_path), "--color", "auto"], ahora=lambda: AHORA)
    assert ESC not in capsys.readouterr().out


# ---- (c) símbolo y palabra ------------------------------------------------------------------------------------------------


def test_con_color_apagado_cada_nivel_muestra_su_palabra_en_los_dos_idiomas():
    res = variado()
    f = finding(nivel=Nivel.COMPROBADO, motivo=Motivo.EXISTE_LEGIBLE_SIN_REGLA)
    d = datos(ResultadoAuditoria((*res.hallazgos, f), res.no_revisados, 41))
    for palabras, idioma in ((("POTENCIAL", "HIPÓTESIS"), Idioma.ES), (("POTENTIAL", "HYPOTHESIS"), Idioma.EN)):
        salida = generar(d, idioma)
        assert all(p in salida for p in palabras)


def test_en_modo_ascii_ningun_simbolo_sale_del_ascii():
    d = datos()
    salida = generar(d, Idioma.ES, ascii_=True)
    assert salida.isascii() and "[!]" in salida and "[?]" in salida and "[-]" in salida and "->" in salida
    solo_simbolos = generar(d, Idioma.ES, simbolos_ascii=True)
    assert not any(c in solo_simbolos for c in "■▲◊○√→") and "revisión" in solo_simbolos  # las tildes se conservan
    assert all(c in generar(d, Idioma.ES) for c in "▲◊○") and "[!]" not in generar(d, Idioma.ES)


def test_la_variante_de_fondo_claro_se_usa_con_colorfgbg_claro():
    assert fondo_claro({"COLORFGBG": "0;15"}) and fondo_claro({"COLORFGBG": "0;7"})
    assert not fondo_claro({"COLORFGBG": "15;0"}) and not fondo_claro({}) and not fondo_claro({"COLORFGBG": "x"})
    oscuro = pintar("  ■ COMPROBADO", "comprobado", Color.DE_24_BITS, claro=False)
    claro = pintar("  ■ COMPROBADO", "comprobado", Color.DE_24_BITS, claro=True)
    assert "255;107;107" in oscuro and "179;32;26" in claro
    assert pintar("  x", "comprobado", Color.DE_16).startswith("  " + ESC + "[91m")


def test_no_se_pinta_el_fondo_ni_se_emite_nada_que_no_sea_color():
    d = datos()
    pintado = generar(d, Idioma.ES, color=Color.DE_24_BITS)
    secuencias = set(SGR.findall(pintado))
    assert all(s.startswith(ESC + "[38;2;") or s == RESET for s in secuencias)  # solo primer plano


# ---- (d) codificación -----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("codificacion", ["cp437", "cp1252"])
def test_una_consola_cp437_o_cp1252_no_lanza_unicodeencodeerror(codificacion):
    flujo = io.TextIOWrapper(io.BytesIO(), encoding=codificacion, errors="strict")
    cli._escribir(flujo, generar(datos(), Idioma.ES))  # símbolos y tildes que la codificación no tiene
    flujo.flush()


def test_preparar_salida_pasa_a_utf8_y_no_falla_con_un_stringio_ni_un_flujo_cerrado():
    flujo = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    preparar_salida(flujo)
    assert flujo.encoding == "utf-8" and flujo.errors == "replace"
    preparar_salida(io.StringIO())
    cerrado = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    cerrado.close()
    preparar_salida(cerrado)


def test_importar_el_comando_no_llama_a_reconfigure(monkeypatch):
    import importlib

    llamadas: list[str] = []

    class Espia(io.StringIO):
        def reconfigure(self, **kw):
            llamadas.append("reconfigure")

    monkeypatch.setattr(sys, "stdout", Espia())
    monkeypatch.setattr(sys, "stderr", Espia())
    importlib.reload(cli)
    assert llamadas == []


def test_un_nombre_con_una_mitad_de_par_sustituto_sale_escrito():
    assert ruta_visible(f"{BASE}/a" + chr(0xDC80) + "b.env", BASE, None)[0] == "a" + chr(92) + "udc80b.env"


# ---- (e) limpieza al imprimir ---------------------------------------------------------------------------------------------

PELIGROSOS = [
    "a" + ESC + "[2Jb.env",
    "a" + ESC + "]0;titulo" + chr(7) + "b.env",
    "a\nlinea falsa.env",
    "a\rb.env",
    "nota" + chr(0x202E) + "txt.exe",
    "a" + chr(0x200B) + "b.env",
    "a" + chr(0xE0041) + "b.env",
]


@pytest.mark.parametrize("nombre", PELIGROSOS)
def test_los_nombres_peligrosos_salen_escritos_sin_esc_ajenos_ni_saltos_inventados(nombre):
    res = ResultadoAuditoria((finding(nombre),), (NoRevisado(Ruta(f"{BASE}/{nombre}"), MotivoNoRevisado.ARCHIVO_ILEGIBLE),), 3)
    for color in (Color.NINGUNO, Color.DE_24_BITS):
        salida = generar(datos(res), Idioma.ES, color=color)
        sin_color = SGR.sub("", salida)
        assert ESC not in sin_color and chr(7) not in sin_color and "\r" not in sin_color
        assert not any(linea.startswith("linea falsa") for linea in sin_color.splitlines())
        assert "se muestran escritos como" in " ".join(sin_color.split())
        assert chr(0x202E) not in sin_color and chr(0x200B) not in sin_color and chr(0xE0041) not in sin_color


def test_la_segunda_barrera_escribe_lo_peligroso_aunque_la_vista_no_lo_haya_hecho():
    vista = HallazgoVista(
        "a" + ESC + "[2J" + chr(0x202E) + ".env", 2, Tipo.CREDENCIAL_EN_ARCHIVO, Proveedor.PAGOS, Nivel.POTENCIAL,
        Motivo.NO_DETERMINADO, Ajeno.NO_DETERMINADO, Plataforma.CLAUDE_CODE, "claude-code", Postura.SIN_REGLA, None, False)
    base = datos(ResultadoAuditoria((), (), 1))
    import dataclasses

    sucio = dataclasses.replace(
        base, hallazgos=(vista,), carpeta="C:/x" + ESC + "[0m", hubo_nombres_escritos=False,
        no_revisados=(NoRevisadoVista("b" + chr(0x2028) + ".txt", MotivoNoRevisado.ARCHIVO_ILEGIBLE),))
    salida = generar(sucio, Idioma.ES)
    assert ESC not in salida and chr(0x202E) not in salida and chr(0x2028) not in salida
    assert chr(92) + "x1b" in salida and chr(92) + "u202e" in salida and "se muestran escritos como" in " ".join(salida.split())


def test_la_ultima_comprobacion_deja_solo_los_esc_de_color_propios():
    propio = ESC + "[38;2;1;2;3mhola" + RESET
    assert ultima_comprobacion(propio) == propio
    assert ultima_comprobacion(propio + ESC + "[2J" + ESC + "]0;x" + chr(7)) == propio + "[2J]0;x"  # el BEL también sale
    assert ESC not in ultima_comprobacion("x" + ESC + "cy")


def test_un_nombre_de_1500_caracteres_sale_recortado_con_la_marca():
    salida = generar(datos(ResultadoAuditoria((finding("x" * 1500 + ".env"),), (), 3)), Idioma.ES)
    assert salida.count("...[recortada: 504 caracteres]") >= 1 and "x" * 1500 not in salida  # 1504 de nombre: la marca dice 504, una sola vez


# ---- (f) canarios ---------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("extra", [[], ["--detalle"], ["--ascii"], ["--idioma", "en"], ["--color", "siempre", "--detalle"],
                                   ["--idioma", "en", "--ascii", "--detalle"]])
def test_los_valores_canario_no_salen_en_ninguna_modalidad(tmp_path: Path, capsys, extra):
    (tmp_path / ".env").write_text("STRIPE_SECRET_KEY=CANARIO-ENV-123456\nGITHUB_TOKEN=CANARIO-GH-654321\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("Texto CANARIO-README del proyecto\n", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text('[remote "o"]\n\turl = https://ana:CANARIO-URL-9f2k8x@host.invalid/x.git\n', encoding="utf-8")
    cli.main([str(tmp_path), "--tarea", "CANARIO-TAREA algo", *extra], ahora=lambda: AHORA)
    capturado = capsys.readouterr()
    for canario in ("CANARIO", "123456", "654321", "9f2k8x"):
        assert canario not in capturado.out and canario not in capturado.err


# ---- (g) tuberías ---------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("error", [BrokenPipeError(), OSError(22, "Invalid argument")])
def test_cerrar_la_salida_antes_de_tiempo_no_da_traza_y_conserva_el_codigo(tmp_path: Path, monkeypatch, error):
    f = finding(nivel=Nivel.COMPROBADO, motivo=Motivo.EXISTE_LEGIBLE_SIN_REGLA)
    from agentreach.contracts import PermisoLectura, PermisosArchivo
    from agentreach.core.nivel import Hechos

    hechos = Hechos(True, PermisosArchivo(PermisoLectura.SI, False, False, "u", "x"), Postura.SIN_REGLA)
    comprobado = ResultadoAuditoria((f,), (), 1, {f: hechos}, ())
    monkeypatch.setattr(cli, "auditar", lambda carpeta, config, **kw: comprobado)
    monkeypatch.setattr("agentreach.reporting.gate.LectorSeguro", LectorFalso)

    class Cerrada:
        encoding = "utf-8"

        def isatty(self):
            return False

        def write(self, texto):
            raise error

        def flush(self):
            pass

    monkeypatch.setattr(sys, "stdout", Cerrada())
    assert cli.main([str(tmp_path)]) == 1  # el código sigue siendo el calculado


# ---- parches de la revisión ----------------------------------------------------------------------------------------


def test_una_ruta_con_espacios_dentro_de_una_frase_no_se_parte():
    from agentreach.adapters.base import Regla, ResultadoAdaptador

    regla = Regla("deny", "Read", Location(Ruta(f"{BASE}/mi carpeta con espacios/.claude/settings.json"), 3), None)
    res = ResultadoAuditoria((finding(),), (), 3, {}, ((Plataforma.CLAUDE_CODE, ResultadoAdaptador(reglas=(regla,))),))
    salida = generar(datos(res), Idioma.ES, ancho=40)
    assert "mi carpeta con espacios/.claude/settings.json:3" in salida  # entera, en una sola línea


def test_con_detalle_la_ubicacion_larga_va_entera_en_su_propia_linea():
    nombre = "carpeta-larga-numero-uno/carpeta-larga-numero-dos/archivo-con-nombre-largo.env"
    salida = generar(datos(ResultadoAuditoria((finding(nombre),), (), 3)), Idioma.ES, detalle=True, ancho=60)
    lineas = salida.splitlines()
    i = next(n for n, linea in enumerate(lineas) if linea.strip() == "Ubicación:")
    assert lineas[i + 1].strip() == nombre + ":2"


def test_la_ultima_comprobacion_quita_secuencias_de_color_ajenas_y_controles_de_8_bits():
    ajena = "a" + ESC + "[41mb" + ESC + "[8mc" + chr(0x9B) + "2J" + chr(0x9D) + "x" + chr(7)
    assert ultima_comprobacion(ajena) == "a[41mb[8mc2Jx"
    assert ultima_comprobacion("uno" + chr(10) + "dos") == "uno" + chr(10) + "dos"


def test_activar_vt_nunca_lanza():
    from agentreach.reporting.formato import activar_vt

    assert activar_vt() in (True, False)


def test_los_errores_de_argumentos_escriben_los_caracteres_peligrosos(capsys):
    with pytest.raises(SystemExit):
        cli.main(["a", "b", ESC + "[2J"])
    err = capsys.readouterr().err
    assert ESC not in err and chr(92) + "x1b" in err


def test_cerrar_la_tuberia_de_verdad_no_deja_traza(tmp_path: Path):
    import subprocess

    for n in range(30):
        (tmp_path / f"c{n}.env").write_text("STRIPE_SECRET_KEY=sk_live_algo_largo_123" + chr(10), encoding="utf-8")
    # el comando de verdad no lee sin terminal: se llama a ``main`` con las ayudas de pruebas, pero con una tubería real
    codigo = ("from agentreach import cli; cli._interactivo = lambda: True; cli._preguntar_por_defecto = lambda t: 's'; "
              "cli._crear_reporte_por_defecto = False; import sys; sys.exit(cli.main([sys.argv[1], '--detalle']))")
    p = subprocess.Popen([sys.executable, "-c", codigo, str(tmp_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.stdout.close()  # quien lee cierra antes de tiempo
    err = p.stderr.read()
    p.stderr.close()
    p.wait(timeout=120)
    assert b"Traceback" not in err and p.returncode in (0, 1)


def test_un_error_de_escritura_que_no_es_tuberia_sale_como_error_interno(tmp_path: Path, monkeypatch, capsys):
    class Llena:
        encoding = "utf-8"

        def isatty(self):
            return False

        def write(self, texto):
            raise OSError(28, "No space left on device")

        def flush(self):
            pass

    monkeypatch.setattr(sys, "stdout", Llena())
    assert cli.main([str(tmp_path)]) == 3
