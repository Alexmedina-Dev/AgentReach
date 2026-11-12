"""Historia 32: la terminal explica cada término técnico en lenguaje llano, desde un único catálogo fijo de 11 fichas.

Cubre: el catálogo (cobertura término contra entrada, las tres variantes, líneas de 90 caracteres o menos, palabras prohibidas), cada fila de la
matriz de la spec (niveles, hook, autocomprobación, agentes configurados, «qué hacer», detalle, idiomas y tonos, reporte vacío, ASCII), el tope
de 12 líneas, el ancho 60/80/100 sin palabras partidas y que ningún identificador técnico salga sin su explicación.
"""

from __future__ import annotations

import dataclasses
import io
import json
import os
import re
import sys
from pathlib import Path

import pytest

from agentreach import cli
from agentreach.contracts import Idioma, Motivo, Nivel, Tipo
from agentreach.core.catalogo_explicaciones import Tono
from agentreach.core.catalogo_terminos import FICHAS, Termino, etiquetas, explicacion, linea, nombre
from agentreach.reporting import texto as modulo_texto
from test_reporte import AHORA, BASE, LectorFalso, bueno, finding, preparar, resultado
from test_reporte import texto as texto_de

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

SECRETO = "ZQX-COMANDO-SECRETO-777"
VALOR_ENV = "sk_live_valor_largo_123"
VARIANTES = [(Idioma.ES, Tono.CERCANO), (Idioma.ES, Tono.FORMAL), (Idioma.EN, Tono.CERCANO)]
PROHIBIDAS = re.compile(
    r"\bseguro\b|\bsegura\b|inseguro|sin riesgo|\bsafe\b|\bunsafe\b|no risk|without risk|risk-free|no modela|línea citada|cited line|"
    r"regla de nivel violada|level rule violated|esquema de configuración|configuration schema", re.IGNORECASE)
# Medido con el código de HEAD b4c4763 (antes de la Historia 32): el resumen de la carpeta de prueba (``proyecto``), ancho 80, color nunca,
# con un home de prueba con el hook y el sandbox, bajo el mismo entorno de pytest (conftest): 59 líneas.
LINEAS_DE_HOY = 59


def plano(t: str) -> str:
    return " ".join(t.split())


@pytest.fixture(autouse=True)
def resumen_de_terminal(monkeypatch):
    monkeypatch.setattr(cli, "_resumen_corto_por_defecto", True)  # lo que ve la persona: el resumen, no el listado completo
    monkeypatch.setattr(cli, "_crear_reporte_por_defecto", False)


@pytest.fixture
def mundo(tmp_path: Path) -> dict:
    casa = tmp_path / "casa"
    (casa / ".claude").mkdir(parents=True)
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    (proyecto / ".env").write_text(f"STRIPE_SECRET_KEY={VALOR_ENV}\n", encoding="utf-8")
    return {"casa": casa, "proyecto": proyecto}


def con_hook(mundo, sandbox: bool = False) -> None:
    datos = {"hooks": {"PreToolUse": [{"matcher": "Read", "hooks": [{"type": "command", "command": SECRETO}]}]}}
    if sandbox:
        datos["sandbox"] = {"enabled": True}
    (mundo["casa"] / ".claude" / "settings.json").write_text(json.dumps(datos), encoding="utf-8")


def correr(mundo, *extra: str, carpeta: Path | None = None) -> str:
    salida, anterior = io.StringIO(), sys.stdout
    sys.stdout = salida
    try:
        cli.main([str(carpeta or mundo["proyecto"]), "--home", str(mundo["casa"]), "--no-banner", *extra], ahora=lambda: AHORA)
    finally:
        sys.stdout = anterior
    return salida.getvalue()


# ---- el catálogo ---------------------------------------------------------------------------------------------------------------------


def test_los_doce_terminos_tienen_su_ficha_con_las_tres_variantes():
    assert len(Termino) == 12 and set(FICHAS) == set(Termino)  # término contra entrada, en los dos sentidos
    for termino in Termino:
        for idioma, tono in VARIANTES:
            assert linea(termino, idioma, tono).strip() and nombre(termino, idioma).strip()
            assert all(t.strip() for t in explicacion(termino, idioma, tono)), (termino, idioma, tono)
            assert all(e.strip() for e in etiquetas(idioma, tono))
    # «tú» y «usted» se guardan por separado: el inglés no varía con el tono
    assert linea(Termino.NIVEL_COMPROBADO, Idioma.ES, Tono.CERCANO).endswith("Atiéndelo primero.")
    assert linea(Termino.NIVEL_COMPROBADO, Idioma.ES, Tono.FORMAL).endswith("Atiéndalo primero.")
    assert linea(Termino.NIVEL_COMPROBADO, Idioma.EN, Tono.FORMAL) == linea(Termino.NIVEL_COMPROBADO, Idioma.EN, Tono.CERCANO)


def test_las_lineas_de_terminal_miden_90_o_menos():
    for termino in Termino:
        for idioma, tono in VARIANTES:
            assert len(linea(termino, idioma, tono)) <= 90, (termino, idioma, tono)


def test_ningun_texto_del_catalogo_dice_seguro_ni_jerga_interna():
    for termino in Termino:
        for idioma, tono in VARIANTES:
            todo = " ".join([linea(termino, idioma, tono), nombre(termino, idioma), *explicacion(termino, idioma, tono)])
            assert not PROHIBIDAS.search(todo), (termino, idioma, tono, PROHIBIDAS.search(todo))


def test_potencial_dice_que_no_es_un_riesgo_menor_en_las_tres_variantes():
    for idioma, tono in VARIANTES:
        t = linea(Termino.NIVEL_POTENCIAL, idioma, tono)
        assert "no es un riesgo menor" in t.lower() or "not a lesser risk" in t.lower()


# ---- la matriz de la spec ------------------------------------------------------------------------------------------------------------


def test_niveles_presentes_dicen_su_frase_y_los_ausentes_no(mundo):
    con_hook(mundo)  # todo lo que depende del hook sale potencial; no hay comprobados
    t = plano(correr(mundo))
    assert linea(Termino.NIVEL_POTENCIAL, Idioma.ES) in t and "No es un riesgo menor" in t
    assert "Comprobado: el agente puede llegar" not in t
    assert t.count(linea(Termino.NIVEL_POTENCIAL, Idioma.ES)) == 1


def test_hook_sin_nivel_determinado_explica_con_la_formula_y_la_clave_entre_parentesis(mundo):
    con_hook(mundo)
    crudo = correr(mundo)
    t = plano(crudo)
    assert linea(Termino.NO_DETERMINADO, Idioma.ES) in t
    assert t.count(linea(Termino.HOOK, Idioma.ES)) == 1 and t.count("no es una alarma ni una garantía: es un punto ciego") == 0
    assert t.count("No es una alarma ni una garantía: es un punto ciego") == 1  # una sola explicación
    assert "AgentReach no sabe qué decide ese programa (hooks.PreToolUse)" in t
    assert "no modela" not in t and not PROHIBIDAS.search(t.replace("lo demás sea seguro", ""))
    assert SECRETO not in crudo and VALOR_ENV not in crudo


def test_hook_en_ingles_y_formal(mundo):
    con_hook(mundo)
    ingles = plano(correr(mundo, "--idioma", "en"))
    assert linea(Termino.HOOK, Idioma.EN) in ingles and "Neither an alarm nor a guarantee: a blind spot" in ingles
    assert "(hooks.PreToolUse)" in ingles
    assert linea(Termino.HOOK, Idioma.ES, Tono.FORMAL) in plano(correr(mundo, "--tono", "formal"))


def test_sin_hook_no_hay_explicacion_de_hook_ni_de_no_determinado(mundo):
    t = plano(correr(mundo))
    assert linea(Termino.HOOK, Idioma.ES) not in t and "punto ciego" not in t and "NO DETERMINADO" not in t


def test_agente_configurado_pero_no_analizado_dice_su_frase_una_vez(mundo):
    (mundo["proyecto"] / ".cursor" / "rules").mkdir(parents=True)
    (mundo["proyecto"] / ".cursor" / "rules" / "a.mdc").write_text("x", encoding="utf-8")
    t = plano(correr(mundo))
    assert t.count(linea(Termino.CONFIGURADO_VS_ANALIZADO, Idioma.ES)) == 1
    sin = plano(correr(mundo, carpeta=mundo["casa"].parent))  # sin agentes configurados: la frase no sale
    assert linea(Termino.CONFIGURADO_VS_ANALIZADO, Idioma.ES) not in sin


def _comprobado() -> tuple:
    f, h = bueno()
    return f, h


def test_autocomprobacion_dice_cual_hallazgo_y_a_que_nivel_paso():
    f, _ = _comprobado()
    t = plano(texto_de(resultado([f])))
    assert linea(Termino.AUTOCOMPROBACION, Idioma.ES) in t
    assert "Se bajó de comprobado a potencial: credencial en un archivo, a.env." in t
    assert "línea citada" not in t and "regla de nivel violada" not in t


def test_autocomprobacion_de_linea_no_confirmada_conserva_el_nivel_y_explica_el_lugar():
    f, h = _comprobado()
    t = plano(texto_de(resultado([f], hechos={f: h}), lector=LectorFalso(lineas=["x", "una linea sin nada"])))
    assert "Sigue en comprobado, sin línea: credencial en un archivo, a.env." in t
    assert linea(Termino.LUGAR_NO_CONFIRMADO, Idioma.ES) in t


def test_con_mas_de_tres_correcciones_lista_tres_y_y_n_mas():
    fs = [finding(nivel=Nivel.COMPROBADO, motivo=Motivo.EXISTE_LEGIBLE_SIN_REGLA, nombre=f"a{n}.env") for n in range(5)]
    t = texto_de(resultado(fs))
    assert t.count("Se bajó de comprobado a potencial") == 3 and "y 2 más." in t
    assert plano(texto_de(resultado(fs), detalle=True)).count("Se bajó de comprobado a potencial") == 5  # el detalle las lista todas


def test_si_faltan_los_datos_de_la_correccion_el_aviso_sigue_sin_romperse():
    f, _ = _comprobado()
    datos = preparar(resultado([f]), BASE, ahora=AHORA, lector=LectorFalso())
    sin_detalle = dataclasses.replace(datos, correcciones=())
    t = plano(modulo_texto.generar(sin_detalle))
    assert "Se corrigieron 1 hallazgo(s) antes de imprimir." in t and linea(Termino.AUTOCOMPROBACION, Idioma.ES) in t


def test_lo_mas_urgente_trae_una_linea_que_hacer_por_hallazgo(mundo):
    t = correr(mundo)
    bloque = t[t.index("LO MÁS URGENTE"):]
    flecha = re.escape("->") + "|→"  # sin terminal real los símbolos salen en ASCII
    assert re.search(f"(?:{flecha}) Saca la credencial del proyecto", plano(bloque))
    assert len(re.findall(f"(?:{flecha}) ", bloque)) >= 1


def test_sin_que_hacer_disponible_la_linea_se_omite(mundo, monkeypatch):
    def sin_catalogo(tipo, idioma, tono=Tono.CERCANO):
        raise KeyError(tipo)

    monkeypatch.setattr(modulo_texto, "que_hacer", sin_catalogo)
    t = correr(mundo, "--no-abrir")
    bloque = t[t.index("LO MÁS URGENTE"):]
    assert "LO MÁS URGENTE" in t and "Saca" not in bloque


def test_detalle_agrega_la_explicacion_larga_de_los_terminos_presentes(mundo):
    con_hook(mundo, sandbox=True)
    t = plano(correr(mundo, "--detalle"))
    que_es, que_significa, que_hacer = explicacion(Termino.HOOK, Idioma.ES)
    assert "CÓMO LEER ESTE REPORTE" in t
    assert f"Qué es: {que_es}" in t and f"Qué significa para ti: {que_significa}" in t and f"Qué puedes hacer: {que_hacer}" in t
    assert "Sandbox" in t and "hooks.PreToolUse" in t  # ahí sí pueden verse las claves técnicas
    assert "Nivel comprobado" not in t  # un término ausente no sale


def test_sin_detalle_no_sale_la_explicacion_larga(mundo):
    con_hook(mundo)
    assert "CÓMO LEER ESTE REPORTE" not in correr(mundo) and "Qué significa para ti" not in correr(mundo)


def test_cada_variante_de_idioma_y_tono_sale_completa(mundo):
    (mundo["casa"] / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
    cercano = plano(correr(mundo, "--detalle"))
    formal = plano(correr(mundo, "--detalle", "--tono", "formal"))
    ingles = plano(correr(mundo, "--detalle", "--idioma", "en"))
    ingles_formal = plano(correr(mundo, "--detalle", "--idioma", "en", "--tono", "formal"))
    assert "Atiéndelo primero" in cercano and "Qué significa para ti" in cercano
    assert "Atiéndalo primero" in formal and "Qué significa para usted" in formal and "Qué puede hacer" in formal
    assert "Deal with it first" in ingles and "What it means for you" in ingles and ingles == ingles_formal


def test_reporte_vacio_no_nombra_ningun_termino_ausente():
    t = plano(texto_de(resultado()))
    assert "SIN HALLAZGOS" in t
    for termino in (Termino.NIVEL_COMPROBADO, Termino.NIVEL_POTENCIAL, Termino.NIVEL_HIPOTESIS, Termino.NO_DETERMINADO, Termino.HOOK,
                    Termino.NO_SE_PUDO_REVISAR, Termino.AUTOCOMPROBACION):
        assert linea(termino, Idioma.ES) not in t


@pytest.mark.parametrize("extra", [("--ascii",), ("--ascii", "--detalle"), ("--ascii", "--idioma", "en", "--detalle")])
def test_en_modo_ascii_no_sale_ningun_simbolo_fuera_de_ascii(mundo, extra):
    con_hook(mundo, sandbox=True)
    t = correr(mundo, *extra)
    assert all(ord(c) < 128 for c in t), sorted({c for c in t if ord(c) >= 128})


def test_sin_color_el_texto_es_el_mismo_y_sin_escapes(mundo):
    con_hook(mundo)
    t = correr(mundo, "--color", "nunca")
    assert "\x1b[" not in t and linea(Termino.HOOK, Idioma.ES) in plano(t)


# ---- ancho, tope y sin identificadores sueltos ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("extra", [(), ("--detalle",), ("--idioma", "en"), ("--tono", "formal")])
def test_el_ancho_no_parte_palabras_a_60_80_y_100(mundo, extra):
    con_hook(mundo, sandbox=True)
    por_ancho = {a: correr(mundo, *extra, "--ancho", str(a)) for a in (60, 80, 100)}
    fichas = {a: sorted(t.split()) for a, t in por_ancho.items()}
    assert fichas[60] == fichas[80] == fichas[100]  # ajustar solo mueve saltos: ninguna palabra se parte ni se pierde
    for ancho, t in por_ancho.items():
        for renglon in t.splitlines():
            assert len(renglon) <= ancho or len(renglon.split()) <= 2 or renglon.strip().startswith(("C:", "/", "~")), (ancho, renglon)


def test_ningun_identificador_tecnico_sale_sin_su_explicacion_en_el_resumen(mundo):
    con_hook(mundo, sandbox=True)
    for ancho in (60, 80, 100):
        t = plano(correr(mundo, "--ancho", str(ancho)))
        assert "funcion_no_modelada" not in t and not re.search(r"\bTH-\d+", t)
        claves = re.findall(r"\S+ \(((?:hooks\.\w+)|sandbox)\)", t)
        assert set(claves) == {"hooks.PreToolUse", "sandbox"}  # cada clave va entre paréntesis, después de su frase
        assert len(re.findall(r"hooks\.\w+", t)) == 1
        assert t.count("AgentReach no sabe interpretar esa caja de aislamiento (sandbox)") == 1


def test_el_resumen_crece_como_maximo_12_lineas_en_la_carpeta_de_prueba(tmp_path):
    carpeta = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")
    if not carpeta or not Path(carpeta, "proyecto").is_dir():
        if os.environ.get("CI") or os.environ.get("AGENTREACH_EXIGIR_PRUEBAS"):
            pytest.fail("AGENTREACH_PROYECTO_PRUEBA no apunta al proyecto de prueba")  # en CI el tope de 12 líneas no puede quedar sin vigilar
        pytest.skip("falta AGENTREACH_PROYECTO_PRUEBA")
    casa = tmp_path / "casa"
    (casa / ".claude").mkdir(parents=True)
    (casa / ".claude" / "settings.json").write_text(json.dumps(
        {"hooks": {"PreToolUse": [{"matcher": "Read", "hooks": [{"type": "command", "command": "x"}]}]}, "sandbox": {"enabled": True}}),
        encoding="utf-8")
    t = correr({"casa": casa}, "--ancho", "80", "--color", "nunca", carpeta=Path(carpeta) / "proyecto")
    assert len(t.splitlines()) <= LINEAS_DE_HOY + 12, len(t.splitlines())
    assert "no modela" not in t and "línea citada" not in t and "hook" in t.lower()


def test_el_catalogo_de_hallazgos_ya_no_dice_no_modela():
    from agentreach.core.catalogo_explicaciones import TITULO_MOTIVO

    for textos in TITULO_MOTIVO.values():
        assert not PROHIBIDAS.search(" ".join(textos.values()))


# ---- avisos de autocomprobación por rama y huecos del catálogo ----------------------------------------------------------------------------


def _aviso(nivel_antes, nivel_despues, razon, idioma=Idioma.ES, tono=Tono.CERCANO) -> str:
    from agentreach.core.autocomprobacion import RazonCorreccion
    from agentreach.reporting.gate import CorreccionVista

    datos = preparar(resultado([finding()]), BASE, ahora=AHORA, lector=LectorFalso())
    t = modulo_texto._Texto(datos, idioma, False, 80, False, tono=tono)
    return t._aviso_correccion(CorreccionVista(Tipo.CREDENCIAL_EN_ARCHIVO, "a.env", getattr(RazonCorreccion, razon), nivel_antes, nivel_despues))


@pytest.mark.parametrize("idioma, tono, esperado", [
    (Idioma.ES, Tono.CERCANO, "Se corrigió: credencial en un archivo, a.env."),
    (Idioma.ES, Tono.FORMAL, "Se corrigió: credencial en un archivo, a.env."),
    (Idioma.EN, Tono.CERCANO, "Corrected: credential in a file, a.env."),
])
def test_aviso_sin_nivel_despues_dice_se_corrigio(idioma, tono, esperado):
    assert _aviso(Nivel.COMPROBADO, None, "INVARIANTE_VIOLADA", idioma, tono) == esperado


@pytest.mark.parametrize("idioma, tono, esperado", [
    (Idioma.ES, Tono.CERCANO, "Se bajó a potencial: credencial en un archivo, a.env."),
    (Idioma.ES, Tono.FORMAL, "Se bajó a potencial: credencial en un archivo, a.env."),
    (Idioma.EN, Tono.CERCANO, "Lowered to potential: credential in a file, a.env."),
])
def test_aviso_sin_nivel_antes_dice_se_bajo_a(idioma, tono, esperado):
    assert _aviso(None, Nivel.POTENCIAL, "INVARIANTE_VIOLADA", idioma, tono) == esperado


def test_nivel_igual_solo_dice_sin_linea_si_la_razon_es_la_linea():
    assert _aviso(Nivel.COMPROBADO, Nivel.COMPROBADO, "LINEA_NO_CONFIRMADA") == "Sigue en comprobado, sin línea: credencial en un archivo, a.env."
    assert _aviso(Nivel.COMPROBADO, Nivel.COMPROBADO, "ARCHIVO_YA_NO_EXISTE") == "Se corrigió: credencial en un archivo, a.env."


def test_un_hallazgo_corregido_por_dos_razones_sale_en_un_solo_aviso():
    # sin hechos (invariante violada) y con una línea que no tiene la clave: dos razones, un hallazgo
    f = finding(nivel=Nivel.COMPROBADO, motivo=Motivo.EXISTE_LEGIBLE_SIN_REGLA)
    datos = preparar(resultado([f]), BASE, ahora=AHORA, lector=LectorFalso(lineas=["x", "nada"]))
    assert len(datos.correcciones) == 1 and datos.hallazgos_corregidos == 1
    assert plano(modulo_texto.generar(datos)).count("Se bajó de comprobado a potencial") == 1


def test_todo_tipo_tiene_su_que_hacer_en_es_en_y_formal():
    from agentreach.core.catalogo_explicaciones import que_hacer

    for tipo in Tipo:
        for idioma, tono in VARIANTES:
            assert que_hacer(tipo, idioma, tono).strip(), (tipo, idioma, tono)
