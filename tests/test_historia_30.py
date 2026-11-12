"""Historia 30: todo lo que imprime la CLI (bienvenida, las dos preguntas de permiso, avisos, «Reporte HTML guardado en…» y la pregunta de abrir)
sale por el mismo ajuste de palabras que el reporte, con el ancho real de la terminal. El texto no cambia, solo dónde se corta.

Se recorre el flujo completo con una ``preguntar`` falsa que registra cada texto de pregunta y se comprueba toda la salida que NO es el cuerpo
del reporte (ese ya tiene su propio ajuste, con mínimo de 60 columnas): stderr, el texto de cada pregunta y lo que se escribe tras el reporte.
"""

from __future__ import annotations

import io
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest

from agentreach import cli
from agentreach.cli import _interactivo as INTERACTIVO_REAL
from agentreach.cli import reportes
from agentreach.contracts import Idioma
from agentreach.core.catalogo_explicaciones import Tono

pytestmark = [pytest.mark.sin_tope_por_nombre, pytest.mark.terminal_real]

CR = chr(10)
AHORA = datetime(2026, 11, 11, 9, 0, 0)
ANCHOS = (30, 60, 80, 100, 140)
COMBINACIONES = [(Idioma.ES, "cercano"), (Idioma.ES, "formal"), (Idioma.EN, "cercano"), (Idioma.EN, "formal")]


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
    monkeypatch.setattr(cli, "_interactivo", INTERACTIVO_REAL)
    monkeypatch.setattr(cli, "_resumen_corto_por_defecto", True)
    monkeypatch.setattr(cli, "_crear_reporte_por_defecto", True)
    monkeypatch.setattr(cli, "abrir_navegador", lambda ruta: True)


def _mundo(tmp_path: Path) -> dict:
    casa = tmp_path / "casa"
    casa.mkdir()
    # una carpeta con un nombre largo y sin espacios: la ruta es una ficha más larga que cualquier ancho
    proyecto = tmp_path / ("proyecto-con-un-nombre-muy-largo-y-sin-ningun-espacio-" + "x" * 40)
    proyecto.mkdir()
    (proyecto / ".env").write_text("STRIPE_SECRET_KEY=sk_live_valor_largo_123\n", encoding="utf-8")
    return {"casa": casa, "proyecto": proyecto}


def _fichas(texto: str) -> list[str]:
    return texto.split()


def _correr(monkeypatch, argv: list[str], columnas: int) -> tuple[int, str, str, list[str]]:
    salida, errores = Tty(), Tty()
    monkeypatch.setattr(sys, "stdin", Tty())
    monkeypatch.setattr(sys, "stdout", salida)
    monkeypatch.setattr(sys, "stderr", errores)
    monkeypatch.setattr(cli.shutil, "get_terminal_size", lambda fallback=(80, 24): os.terminal_size((columnas, 24)))
    preguntas: list[str] = []

    def preguntar(texto: str) -> str:
        preguntas.append(texto)
        return "y" if "(Y/N)" in texto else "s"

    codigo = cli.main(argv, ahora=lambda: AHORA, preguntar=preguntar)
    return codigo, salida.getvalue(), errores.getvalue(), preguntas


def _comprobar_lineas(texto: str, columnas: int, donde: str) -> None:
    limite = max(min(max(columnas, 20), 100) - 1, 20)
    for linea in texto.split(CR):
        linea = linea.rstrip()  # el espacio final de una pregunta es donde queda el cursor
        assert len(linea) <= limite or len(linea.split()) == 1, f"{donde}: línea de {len(linea)} columnas (tope {limite}): {linea!r}"


def _plano(texto: str) -> str:
    """Método de las Design Notes: unir las líneas con un espacio y colapsar espacios. Si una palabra se hubiera partido, sobraría un espacio."""
    return " ".join(texto.split())


@pytest.mark.parametrize("idioma,tono", COMBINACIONES)
@pytest.mark.parametrize("columnas", ANCHOS)
def test_flujo_completo_respeta_el_ancho_y_no_parte_palabras(tmp_path, monkeypatch, columnas, idioma, tono):
    mundo = _mundo(tmp_path)
    ruta = str(mundo["proyecto"])
    argv = [ruta, "--home", str(mundo["casa"]), "--no-banner", "--idioma", idioma.value, "--tono", tono]
    _, salida, errores, preguntas = _correr(monkeypatch, argv, columnas)
    E = {k: v[idioma] for k, v in cli._ERROR.items()}

    assert len(preguntas) == 3  # leer la carpeta, las reglas de fuera y abrir el reporte
    esperadas = [E["pregunta_leer"].format(ruta=ruta, aviso=""), cli._PREGUNTA_REGLAS[(idioma, Tono(tono))], E["pregunta_abrir"]]
    for n, (texto, original) in enumerate(zip(preguntas, esperadas, strict=True)):
        _comprobar_lineas(texto, columnas, f"pregunta {n + 1}")
        assert _plano(texto) == _plano(original), f"pregunta {n + 1} cambió o se partió una palabra"
        assert texto.endswith(("(S/N) ", "(Y/N) ")), repr(texto)
    assert any(linea.strip() == ruta for linea in preguntas[0].split(CR))  # la ruta larga queda entera en su línea

    _comprobar_lineas(errores, columnas, "stderr")
    assert _plano(errores) == _plano(" ".join(E[k] for k in ("intro_que", "intro_hace", "intro_no_hace")))

    marcador = E["reporte_donde"].split("{ruta}")[0].strip()
    assert marcador in salida, "el aviso de reporte guardado no salió"
    cola = salida[salida.index(marcador):]
    carpeta = mundo["casa"] / reportes.CARPETA
    [html] = list(carpeta.glob("*.html"))
    esperado = " ".join([E["reporte_donde"].format(ruta=html), E["reporte_que"],
                         E["respuesta_guardada"].format(ruta=carpeta / "preferencias.json")])
    _comprobar_lineas(cola, columnas, "stdout tras el reporte")
    assert _plano(cola) == _plano(esperado)


@pytest.mark.parametrize("columnas", ANCHOS)
def test_pregunta_con_aviso_de_carpeta_personal_ajusta_cada_linea(tmp_path, monkeypatch, columnas):
    mundo = _mundo(tmp_path)
    ruta = str(mundo["casa"])
    _, _, _, preguntas = _correr(monkeypatch, [ruta, "--home", ruta, "--no-banner", "--sin-reporte-html"], columnas)
    texto = preguntas[0]
    assert "ATENCIÓN" in texto and texto.endswith("(S/N) ")
    limite = max(min(max(columnas, 20), 100) - 1, 20)
    for linea in texto.split("\n"):
        assert len(linea.rstrip()) <= limite or len(linea.split()) == 1, repr(linea)
    assert " ".join(texto.split()).startswith("¿Se permite que AgentReach lea esta carpeta?")
    assert " ".join(texto.split()).endswith("puede tardar y mirar muchos archivos. (S/N)")


@pytest.mark.parametrize("idioma,tono", COMBINACIONES)
@pytest.mark.parametrize("columnas", (30, 60, 140))
def test_el_texto_no_cambia_solo_donde_se_corta(tmp_path, monkeypatch, columnas, idioma, tono):
    mundo = _mundo(tmp_path)
    _, _, _, preguntas = _correr(
        monkeypatch, [str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--no-banner", "--idioma", idioma.value, "--tono", tono,
                      "--sin-reporte-html"], columnas)
    assert " ".join(preguntas[1].split()) == cli._PREGUNTA_REGLAS[(idioma, Tono(tono))].strip()
    # «(S/N)» nunca queda solo en una línea nueva en la pregunta de las reglas: va con la palabra anterior
    assert not any(linea.strip() in ("(S/N)", "(Y/N)") for linea in preguntas[1].split("\n"))


def test_ancho_pedido_con_la_opcion_manda_y_nunca_baja_de_20(tmp_path, monkeypatch):
    mundo = _mundo(tmp_path)
    _, _, errores, _ = _correr(monkeypatch, [str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--no-banner", "--ancho", "5",
                                              "--sin-reporte-html"], 200)
    assert all(len(linea) <= 20 or len(linea.split()) == 1 for linea in errores.split("\n"))


# ---- salidas tempranas, fallos del ajuste, U+00A0 real y vigilancia del «un solo punto» --------------------------------------------------


def _salida_temprana(caso: str, mundo: dict, tmp_path: Path) -> list[str]:
    existente = tmp_path / "ya-existe.txt"
    existente.write_text("x", encoding="utf-8")
    proyecto = str(mundo["proyecto"])
    return {
        "bandera_desconocida": ["--esta-bandera-no-existe"],
        "json": [proyecto, "--json"],
        "carpeta_inexistente": [str(tmp_path / "no-existe")],
        "salida_existente": [proyecto, "--salida", str(existente)],
        "doctor_salida_existente": ["doctor", "--salida", str(existente)],
        "html_sin_salida": [proyecto, "--formato", "html"],
    }[caso]


CASOS_TEMPRANOS = ["bandera_desconocida", "json", "carpeta_inexistente", "salida_existente", "doctor_salida_existente", "html_sin_salida"]


def _correr_temprano(monkeypatch, argv: list[str], columnas: int) -> tuple[int, str]:
    errores = Tty()
    monkeypatch.setattr(sys, "stdin", Tty())
    monkeypatch.setattr(sys, "stdout", Tty())
    monkeypatch.setattr(sys, "stderr", errores)
    monkeypatch.setattr(cli.shutil, "get_terminal_size", lambda fallback=(80, 24): os.terminal_size((columnas, 24)))
    try:
        codigo = cli.main(argv, ahora=lambda: AHORA, preguntar=lambda t: "s")
    except SystemExit as salida:  # los errores de argumentos salen con SystemExit(2)
        codigo = salida.code
    return codigo, errores.getvalue()


@pytest.mark.parametrize("caso", CASOS_TEMPRANOS)
def test_los_mensajes_cortos_de_salida_temprana_respetan_30_columnas(tmp_path, monkeypatch, caso):
    mundo = _mundo(tmp_path)
    codigo, errores = _correr_temprano(monkeypatch, _salida_temprana(caso, mundo, tmp_path), 30)
    assert codigo == 2 and errores.strip(), caso
    for linea in errores.split(CR):
        assert len(linea) <= 29 or len(linea.split()) == 1, f"{caso}: {linea!r}"


@pytest.mark.parametrize("caso", ["bandera_desconocida", "json"])
def test_si_el_ajuste_falla_el_mensaje_sale_igual_y_el_codigo_no_cambia(tmp_path, monkeypatch, caso):
    mundo = _mundo(tmp_path)
    argv = _salida_temprana(caso, mundo, tmp_path)
    codigo_normal, normal = _correr_temprano(monkeypatch, argv, 140)

    def roto(texto):
        raise RuntimeError("fallo del ajuste")

    monkeypatch.setattr(cli, "_texto", roto)
    codigo, errores = _correr_temprano(monkeypatch, argv, 140)
    assert codigo == codigo_normal == 2 and "Traceback" not in errores
    assert _plano(errores) == _plano(normal) and errores.strip()


def test_un_u00a0_real_de_una_ruta_sale_intacto(monkeypatch):
    monkeypatch.setattr(cli.shutil, "get_terminal_size", lambda fallback=(80, 24): os.terminal_size((40, 24)))
    ruta = "C:/carpeta\u00a0con\u00a0espacio-duro/y-mas"
    texto = f"¿Se permite que AgentReach lea esta carpeta?\n  {ruta}\nATENCIÓN: es la carpeta personal. ¿Se permite? (S/N) "
    resultado = cli._texto(texto)
    assert ruta in resultado and "\ue000" not in resultado
    assert resultado.endswith("(S/N) ")


def test_ningun_print_suelto_en_la_cli_todo_pasa_por_decir():
    """«Un solo punto»: solo ``_decir`` puede llamar a ``print``. Excepciones legítimas: ninguna."""
    import ast

    fuente = Path(cli.__file__).read_text(encoding="utf-8")
    arbol = ast.parse(fuente)
    sueltos: list[int] = []

    def visitar(nodo, funcion: str | None) -> None:
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcion = nodo.name
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name) and nodo.func.id == "print" and funcion != "_decir":
            sueltos.append(nodo.lineno)
        for hijo in ast.iter_child_nodes(nodo):
            visitar(hijo, funcion)

    visitar(arbol, None)
    assert sueltos == [], f"print( fuera de _decir en las líneas {sueltos}: usa _decir(...)"
