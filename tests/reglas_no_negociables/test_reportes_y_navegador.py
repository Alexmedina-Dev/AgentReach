"""Historia 21: lo único que AgentReach escribe además de ``--salida`` (``AgentReach-reportes`` en la carpeta personal) y lo único que
le pide al sistema (abrir el reporte en el navegador, con permiso y después de revisar). Todo lo demás sigue prohibido.

Regla precisada:
  1. Dentro de la carpeta revisada AgentReach no crea, cambia ni borra nada, nunca.
  2. Fuera de ella solo escribe (a) el archivo de ``--salida`` y (b) ``<carpeta personal>/AgentReach-reportes/`` (reportes y
     ``preferencias.json``), nunca a través de un enlace y nunca pisando un reporte anterior.
  3. No lanza programas durante la revisión. Solo al terminar, y solo con permiso de la persona (``--abrir`` o un «s» a la
     pregunta), le pide al sistema abrir ese archivo ``.html`` local con el navegador. Sin red.
"""

from __future__ import annotations

import ast
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest

from agentreach import cli
from agentreach.app.auditar import auditar
from agentreach.config import Configuracion
from conftest import AHORA, INTENTOS, Terminal, instantanea

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

HTML_AHORA = datetime(2026, 11, 10, 15, 30, 5)


@pytest.fixture(autouse=True)
def con_reporte(monkeypatch):
    """Estas pruebas SÍ crean el reporte en AgentReach-reportes (las comunes lo apagan para no escribir en la carpeta personal)."""
    monkeypatch.setattr(cli, "_crear_reporte_por_defecto", True)


@pytest.fixture
def mundo(tmp_path: Path) -> dict:
    casa = tmp_path / "casa"
    casa.mkdir()
    proyecto = tmp_path / "proyecto"
    (proyecto / ".claude").mkdir(parents=True)
    (proyecto / ".env").write_text("STRIPE_SECRET_KEY=sk_live_valor_largo_123\n", encoding="utf-8")
    (proyecto / ".claude" / "settings.json").write_text('{"permissions": {"deny": []}}', encoding="utf-8")
    return {"casa": casa, "proyecto": proyecto, "reportes": casa / "AgentReach-reportes"}


def _arbol(raiz: Path) -> dict[str, tuple]:
    """Nombres, tamaños, marcas y contenido de los ARCHIVOS (de las carpetas, solo los nombres: Windows actualiza la hora de una carpeta
    con retraso, y una carpeta recién creada por la prueba podría cambiar sin que nadie la toque)."""
    resultado: dict[str, tuple] = {}
    for p in sorted(raiz.rglob("*")):
        clave = str(p.relative_to(raiz))
        resultado[clave] = ("archivo", p.stat().st_size, p.stat().st_mtime_ns, p.read_bytes()) if p.is_file() else ("carpeta",)
    return resultado


def _correr(argv: list[str]) -> tuple[int, str]:
    salida, error = Terminal(), Terminal()
    anterior = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = salida, error
    try:
        codigo = cli.main(argv, ahora=lambda: HTML_AHORA)
    finally:
        sys.stdout, sys.stderr = anterior
    return codigo, error.getvalue()


def test_solo_se_escribe_en_agentreach_reportes_y_el_proyecto_queda_identico(mundo, escritura_solo_en):
    escritura_solo_en(mundo["reportes"])
    antes = _arbol(mundo["proyecto"])
    codigo, _ = _correr([str(mundo["proyecto"]), "--home", str(mundo["casa"])])
    assert codigo == 1 and _arbol(mundo["proyecto"]) == antes
    assert [p.name for p in mundo["reportes"].glob("*.html")] == ["agentreach-20261110-153005-proyecto.html"]
    assert not INTENTOS


def test_escribir_en_otro_lugar_si_se_detecta(mundo, escritura_solo_en):
    """La propia vigilancia: lo permitido es SOLO la carpeta indicada."""
    from conftest import ViolacionDeRegla

    escritura_solo_en(mundo["reportes"])
    mundo["reportes"].mkdir()
    (mundo["reportes"] / "ok.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ViolacionDeRegla):
        (mundo["casa"] / "otro.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ViolacionDeRegla):
        (mundo["proyecto"] / "otro.txt").write_text("x", encoding="utf-8")
    INTENTOS.clear()


@pytest.fixture
def casa_dentro(mundo) -> Path:
    dentro = mundo["proyecto"] / "casa"  # la «carpeta personal» queda DENTRO de lo revisado
    dentro.mkdir()
    return dentro


def test_con_la_carpeta_personal_dentro_de_lo_revisado_no_se_escribe_nada(mundo, casa_dentro, sin_escrituras):
    antes = _arbol(mundo["proyecto"])
    codigo, err = _correr([str(mundo["proyecto"]), "--home", str(casa_dentro)])
    assert codigo == 1 and _arbol(mundo["proyecto"]) == antes and not INTENTOS
    assert "no se creó el reporte HTML" in err


def test_la_revision_no_lanza_programas_ni_abre_el_navegador_sin_permiso(mundo, sin_procesos, monkeypatch):
    abiertos: list[str] = []
    monkeypatch.setattr(cli, "abrir_navegador", lambda ruta: abiertos.append(ruta) or True)
    codigo, _ = _correr([str(mundo["proyecto"]), "--home", str(mundo["casa"])])
    assert codigo == 1 and abiertos == [] and not INTENTOS  # ni siquiera pidió abrir: sin terminal y sin --abrir


def test_la_auditoria_misma_nunca_pide_abrir_nada(mundo, monkeypatch):
    abiertos: list[str] = []
    monkeypatch.setattr(cli, "abrir_navegador", lambda ruta: abiertos.append(ruta) or True)
    auditar(str(mundo["proyecto"]), Configuracion(home=str(mundo["casa"])))
    assert abiertos == [] and not mundo["reportes"].exists()  # auditar() no escribe ni abre: eso solo lo hace la línea de comandos


def test_con_abrir_pide_abrir_un_html_local_de_agentreach_reportes_y_nada_mas(mundo, monkeypatch):
    abiertos: list[str] = []
    monkeypatch.setattr(cli, "abrir_navegador", lambda ruta: abiertos.append(ruta) or True)
    assert _correr([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--abrir"])[0] == 1
    [ruta] = abiertos
    assert Path(ruta).parent == mundo["reportes"] and ruta.endswith(".html")


def test_el_navegador_solo_lo_importa_infra_navegador_y_solo_lo_llama_el_reporte_html():
    """Estática: ``webbrowser`` solo en ``infra/navegador.py``; ``abrir_navegador`` se llama solo desde ``_reporte_html``."""
    raiz = Path(cli.__file__).resolve().parents[1]
    for archivo in raiz.rglob("*.py"):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            importa = (isinstance(nodo, ast.Import) and any(a.name.split(".")[0] == "webbrowser" for a in nodo.names)) or (
                isinstance(nodo, ast.ImportFrom) and (nodo.module or "").split(".")[0] == "webbrowser")
            assert not importa or archivo.name == "navegador.py", f"{archivo.name} importa webbrowser"
    cli_fuente = ast.parse((raiz / "cli" / "__init__.py").read_text(encoding="utf-8"))
    for funcion in [n for n in ast.walk(cli_fuente) if isinstance(n, ast.FunctionDef)]:
        llamadas = {getattr(n.func, "id", getattr(n.func, "attr", "")) for n in ast.walk(funcion) if isinstance(n, ast.Call)}
        assert ("abrir_navegador" not in llamadas) or funcion.name == "_reporte_html", f"{funcion.name} abre el navegador"
    for archivo in raiz.rglob("*.py"):
        if archivo.name in ("navegador.py",) or archivo.parent.name == "cli":
            continue
        texto = archivo.read_text(encoding="utf-8")
        assert "abrir_navegador" not in texto and "infra.navegador" not in texto, f"{archivo.name} usa el navegador"


def test_con_el_proyecto_de_prueba_solo_se_escribe_el_reporte(raiz_prueba: Path, mundo, escritura_solo_en):
    escritura_solo_en(mundo["reportes"])
    antes = instantanea(raiz_prueba)
    salida, error = Terminal(), Terminal()
    anterior = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = salida, error
    try:
        codigo = cli.main([str(raiz_prueba), "--home", str(mundo["casa"]), "--ancho", "100"], ahora=lambda: AHORA)
    finally:
        sys.stdout, sys.stderr = anterior
    assert codigo in (0, 1) and instantanea(raiz_prueba) == antes and not INTENTOS
    assert len(list(mundo["reportes"].glob("*.html"))) == 1
    assert not os.path.exists(raiz_prueba / "AgentReach-reportes")
