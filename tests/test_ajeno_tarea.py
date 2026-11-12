"""Historia 12: «ajeno a la tarea» con el README y --tarea."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from agentreach.app.auditar import _referencia, auditar
from agentreach.cli import main
from agentreach.config import Configuracion
from agentreach.contracts import Ajeno, MotivoNoRevisado, PermisoLectura, PermisosArchivo, Tipo
from agentreach.core.relacion_tarea import Referencia, clasificar, palabras

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

TAREA = "arreglar el formulario de contacto"


class Sonda:
    def evaluar(self, ruta):
        return PermisosArchivo(PermisoLectura.SI, False, False, "u", "x")


def _auditar(carpeta: Path, **kw):
    return auditar(str(carpeta), Configuracion(), medidores=(Sonda(), None), **kw)


def _por_sufijo(r, sufijo: str, tipo: Tipo):
    return {h.ajeno_a_tarea for h in r.hallazgos if h.tipo is tipo and str(h.ubicacion.ruta).replace("\\", "/").endswith(sufijo)}


@pytest.fixture
def mundo(tmp_path: Path) -> Path:
    p = tmp_path / "proyecto"
    (p / "src" / "estilos").mkdir(parents=True)
    (p / "src" / "contacto").mkdir()
    (p / ".env").write_text("STRIPE_SECRET_KEY=sk_live_algo_largo_123\n", encoding="utf-8")
    (p / "src" / "estilos" / "notas-tipografia.txt").write_text("RAILWAY_API_TOKEN=abcdef123456\n", encoding="utf-8")
    (p / "src" / "contacto" / "formulario.env").write_text("API_TOKEN=valor-largo-1234\n", encoding="utf-8")
    ajeno = tmp_path / "proyecto-ajeno"
    ajeno.mkdir()
    (ajeno / ".env").write_text("API_TOKEN=otro-valor-largo-99\n", encoding="utf-8")
    return tmp_path


# ---- la regla pura ----------------------------------------------------------------------------------------------------


def test_las_palabras_van_sin_acentos_ni_mayusculas_ni_vacias():
    assert palabras("Arreglar el FORMULARIO de Contáctó; src/config.json") == {"arreglar", "formulario", "contacto"}


def test_las_palabras_no_crecen_sin_limite():
    assert len(palabras(" ".join(f"palabra{i}" for i in range(20000)))) <= 5000


def test_sin_readme_ni_tarea_es_no_determinado(tmp_path: Path):
    ruta = str(tmp_path / "src" / "a.env")
    assert clasificar(ruta, str(tmp_path), Referencia()) is Ajeno.NO_DETERMINADO


def test_fuera_del_directorio_de_trabajo_es_ajeno_aunque_no_haya_nada(tmp_path: Path):
    trabajo = tmp_path / "p"
    assert clasificar(str(tmp_path / "otro" / ".env"), str(trabajo), Referencia()) is Ajeno.SI


def test_un_archivo_suelto_en_la_raiz_es_del_proyecto(tmp_path: Path):
    assert clasificar(str(tmp_path / ".env"), str(tmp_path), Referencia(tarea=palabras(TAREA))) is Ajeno.NO


def test_con_tarea_el_resultado_cambia_de_forma_predecible(tmp_path: Path):
    ruta = str(tmp_path / "src" / "estilos" / "notas.txt")
    assert clasificar(ruta, str(tmp_path), Referencia(tarea=palabras("revisar los estilos"))) is Ajeno.NO
    assert clasificar(ruta, str(tmp_path), Referencia(tarea=palabras(TAREA))) is Ajeno.SI
    assert clasificar(ruta, str(tmp_path), Referencia(tarea=palabras("revisar los estilos"))) is not \
        clasificar(ruta, str(tmp_path), Referencia(tarea=palabras(TAREA)))


def test_singular_y_plural_se_reconocen(tmp_path: Path):
    ruta = str(tmp_path / "src" / "formularios" / "a.env")
    assert clasificar(ruta, str(tmp_path), Referencia(tarea=palabras(TAREA))) is Ajeno.NO


def test_el_readme_sin_tarea_solo_puede_decir_no_o_no_determinado(tmp_path: Path):
    ref = Referencia(readme=palabras("Tienda con estilos y catalogo"))
    assert clasificar(str(tmp_path / "src" / "estilos" / "a.env"), str(tmp_path), ref) is Ajeno.NO
    assert clasificar(str(tmp_path / "src" / "otra" / "a.env"), str(tmp_path), ref) is Ajeno.NO_DETERMINADO


def test_una_ruta_que_no_es_de_archivo_no_se_decide():
    for ruta in ("(Windows nativo)", "", "relativa/a.env"):
        assert clasificar(ruta, "C:/x" if sys.platform == "win32" else "/x", Referencia(tarea=palabras(TAREA))) is Ajeno.NO_DETERMINADO


# ---- de punta a punta -------------------------------------------------------------------------------------------------


def test_sin_readme_ni_tarea_los_hallazgos_internos_dicen_no_determinado(mundo: Path):
    r = _auditar(mundo / "proyecto")
    assert _por_sufijo(r, "estilos/notas-tipografia.txt", Tipo.SECRETO_DE_ALTO_PODER) == {Ajeno.NO_DETERMINADO}  # AT-08


def test_at08_es_ajeno_con_una_tarea_que_no_lo_menciona(mundo: Path):
    r = _auditar(mundo / "proyecto", tarea=TAREA)
    assert _por_sufijo(r, "estilos/notas-tipografia.txt", Tipo.SECRETO_DE_ALTO_PODER) == {Ajeno.SI}
    assert _por_sufijo(r, "contacto/formulario.env", Tipo.CREDENCIAL_EN_ARCHIVO) == {Ajeno.NO}
    assert _por_sufijo(r, "proyecto/.env", Tipo.CREDENCIAL_EN_ARCHIVO) == {Ajeno.NO}  # PP-01: no se marca ajeno


def test_aj01_es_ajeno_cuando_la_raiz_es_la_carpeta_contenedora(mundo: Path):
    r = _auditar(mundo, trabajo=str(mundo / "proyecto"))
    assert _por_sufijo(r, "proyecto-ajeno/.env", Tipo.CREDENCIAL_EN_ARCHIVO) == {Ajeno.SI}
    assert _por_sufijo(r, "proyecto/.env", Tipo.CREDENCIAL_EN_ARCHIVO) == {Ajeno.NO}


def test_el_directorio_de_trabajo_por_defecto_es_la_carpeta_auditada(mundo: Path):
    r = _auditar(mundo)
    assert _por_sufijo(r, "proyecto-ajeno/.env", Tipo.CREDENCIAL_EN_ARCHIVO) == {Ajeno.NO_DETERMINADO}


def test_el_texto_del_readme_y_de_la_tarea_no_sale_en_el_reporte(mundo: Path, capsys):
    (mundo / "proyecto" / "README.md").write_text("Frase-secreta-del-readme CANARIO-README\n", encoding="utf-8")
    codigo = main([str(mundo / "proyecto"), "--tarea", "CANARIO-TAREA formulario"])
    salida = capsys.readouterr()
    assert codigo in (0, 1)
    for canario in ("CANARIO-README", "Frase-secreta", "CANARIO-TAREA"):
        assert canario not in salida.out and canario not in salida.err
    r = _auditar(mundo / "proyecto", tarea="CANARIO-TAREA")
    assert "CANARIO" not in repr(r)


def test_un_readme_enorme_o_no_utf8_no_cuelga_y_se_informa(tmp_path: Path):
    (tmp_path / "README.md").write_bytes(b"\xff\xfe\x80 no es utf-8 \xc3\x28\n")
    ref, pendientes = _referencia(str(tmp_path), None)
    assert ref.readme is None and [n.motivo for n in pendientes] == [MotivoNoRevisado.CODIFICACION_NO_UTF8]
    (tmp_path / "README.md").write_bytes(b"\0" * 1)
    with open(tmp_path / "README.md", "wb") as f:
        f.truncate(6 * 1024 * 1024)
    ref, pendientes = _referencia(str(tmp_path), None)
    assert ref.readme is None and [n.motivo for n in pendientes] == [MotivoNoRevisado.ARCHIVO_DEMASIADO_GRANDE]


def test_un_readme_que_es_un_enlace_no_se_sigue(tmp_path: Path):
    destino = tmp_path / "secreto.txt"
    destino.write_text("palabra", encoding="utf-8")
    try:
        os.symlink(destino, tmp_path / "README.md")
    except (OSError, NotImplementedError):
        pytest.skip("este sistema no permite crear enlaces simbólicos")
    ref, pendientes = _referencia(str(tmp_path), None)
    assert ref.readme is None and pendientes


def test_sin_readme_no_hay_aviso_ni_no_revisado(tmp_path: Path):
    ref, pendientes = _referencia(str(tmp_path), None)
    assert ref == Referencia() and pendientes == []


def test_una_tarea_enorme_se_recorta(tmp_path: Path):
    ref, _ = _referencia(str(tmp_path), "palabra " * 10 + "x" * 100000)
    assert ref.tarea is not None and len(ref.tarea) <= 5000


def test_el_flag_tarea_llega_a_auditar(mundo: Path, capsys):
    main([str(mundo / "proyecto"), "--tarea", TAREA, "--directorio-de-trabajo", str(mundo / "proyecto"), "--sin-reporte-html"])
    err = capsys.readouterr().err
    assert "error" not in err.lower() and "Traceback" not in err  # solo la presentación y la pregunta (respondida por la prueba)


# ---- con el proyecto de prueba ----------------------------------------------------------------------------------------


@pytest.fixture
def proyecto_prueba() -> Path:
    raiz = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")
    if not raiz or not (Path(raiz) / "proyecto").is_dir():
        pytest.skip("AGENTREACH_PROYECTO_PRUEBA no apunta al proyecto de prueba")
    return Path(raiz)


def test_casos_del_oraculo_at08_y_pp01(proyecto_prueba: Path):
    r = _auditar(proyecto_prueba / "proyecto", tarea=TAREA)
    assert _por_sufijo(r, "estilos/notas-tipografia.txt", Tipo.SECRETO_DE_ALTO_PODER) == {Ajeno.SI}  # AT-08
    assert _por_sufijo(r, "proyecto/.env", Tipo.CREDENCIAL_EN_ARCHIVO) == {Ajeno.NO}  # PP-01
    sin_tarea = _auditar(proyecto_prueba / "proyecto")  # solo el README: no alcanza para decir "sí"
    assert _por_sufijo(sin_tarea, "estilos/notas-tipografia.txt", Tipo.SECRETO_DE_ALTO_PODER) == {Ajeno.NO_DETERMINADO}
    # AJ-01 con la raíz contenedora entra en trampas*: se prueba con el mundo sintético de arriba


def test_las_carpetas_de_configuracion_son_del_proyecto(tmp_path: Path):
    for carpeta in (".git", ".claude", ".vscode", ".cursor"):
        assert clasificar(str(tmp_path / carpeta / "config"), str(tmp_path), Referencia(tarea=palabras(TAREA))) is Ajeno.NO
