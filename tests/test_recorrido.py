"""Historia 2: recorrido del proyecto y enlaces que salen (solo lectura, sin entrar a los enlaces)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from agentreach.collectors.enlaces import PREFIJO_NT, DetectorEnlaces, recorrer
from agentreach.contracts import Detector, Finding, ReadOnlyFs, Ruta, Tipo
from agentreach.core.pipeline import Pipeline
from agentreach.infra.fs_solo_lectura import ArchivoNoLegible, FsSoloLectura

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

CANARIO = "CANARIO-EN02-sk_live_" + "0123456789abcdef"


def _enlace_de_carpeta(enlace: Path, destino: Path) -> bool:
    """Crea una junction (Windows, sin administrador) o un symlink; False si el entorno no deja."""
    try:
        if sys.platform == "win32":
            import _winapi

            _winapi.CreateJunction(str(destino), str(enlace))
        else:
            os.symlink(destino, enlace, target_is_directory=True)
        return True
    except (OSError, NotImplementedError, AttributeError):
        return False


@pytest.fixture
def escenario(tmp_path: Path):
    proyecto = tmp_path / "proyecto"
    destino = tmp_path / "destino-enlace"
    proyecto.mkdir()
    destino.mkdir()
    (proyecto / "README.md").write_text("hola", encoding="utf-8")
    (proyecto / "src").mkdir()
    (proyecto / "src" / "app.py").write_text("x = 1", encoding="utf-8")
    (destino / "credentials.json").write_text(f'{{"k": "{CANARIO}"}}', encoding="utf-8")
    if not _enlace_de_carpeta(proyecto / "enlace-externo", destino):
        pytest.skip("el entorno no permite crear enlaces de carpeta")
    return proyecto, destino


def _todo_el_texto(recorrido, hallazgos) -> str:
    return repr(recorrido) + repr(hallazgos) + "".join(h.ubicacion.ruta for h in hallazgos)


def test_el_sistema_de_archivos_cumple_el_puerto_y_no_tiene_escritura():
    fs = FsSoloLectura()
    assert isinstance(fs, ReadOnlyFs)
    for nombre in dir(fs):
        assert not any(p in nombre.lower() for p in ("write", "escribir", "delete", "borrar", "remove", "mkdir"))


def test_reporta_el_enlace_con_su_destino_y_no_entra(escenario):
    proyecto, destino = escenario
    recorrido = recorrer(FsSoloLectura(), Ruta(str(proyecto)))
    assert [os.path.basename(e.ruta) for e in recorrido.enlaces] == ["enlace-externo"]
    def canon(r: str) -> str:
        return os.path.normcase(os.path.realpath(r)).removeprefix(PREFIJO_NT)

    assert canon(recorrido.enlaces[0].destino) == canon(str(destino))
    nombres = {os.path.basename(a.ruta) for a in recorrido.archivos}
    assert {"README.md", "app.py"} <= nombres
    assert "credentials.json" not in nombres  # EN-02: lo de detrás no se lista


def test_el_canario_de_detras_del_enlace_no_aparece_en_ninguna_salida(escenario):
    proyecto, _ = escenario
    fs = FsSoloLectura()
    detector = DetectorEnlaces(fs)
    hallazgos = Pipeline([detector]).ejecutar(Ruta(str(proyecto)))
    recorrido = recorrer(fs, Ruta(str(proyecto)))
    assert CANARIO not in _todo_el_texto(recorrido, hallazgos)
    assert "sk_live" not in _todo_el_texto(recorrido, hallazgos)


def test_el_detector_entrega_un_hallazgo_th6_solo_del_enlace(escenario):
    proyecto, _ = escenario
    detector = DetectorEnlaces(FsSoloLectura())
    assert isinstance(detector, Detector)
    hallazgos = Pipeline([detector]).ejecutar(Ruta(str(proyecto)))
    assert len(hallazgos) == 1  # EN-01 sí; EN-02 (credentials.json detrás) no
    h = hallazgos[0]
    assert isinstance(h, Finding) and h.tipo is Tipo.ENLACE_FUERA_DEL_PROYECTO
    assert h.ubicacion.ruta.endswith("enlace-externo")
    assert len(detector.enlaces) == 1


def test_un_ciclo_de_enlaces_no_cuelga(tmp_path: Path):
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    (proyecto / "a.txt").write_text("a", encoding="utf-8")
    if not _enlace_de_carpeta(proyecto / "bucle", proyecto):  # apunta a su propia carpeta
        pytest.skip("el entorno no permite crear enlaces de carpeta")
    recorrido = recorrer(FsSoloLectura(), Ruta(str(proyecto)))
    assert [os.path.basename(a.ruta) for a in recorrido.archivos] == ["a.txt"]
    assert recorrido.enlaces == ()  # el destino está dentro del proyecto: no sale de él
    assert DetectorEnlaces(FsSoloLectura()).detectar(Ruta(str(proyecto))) == []


def test_una_ruta_de_red_unc_es_no_revisada_sin_tocarla():
    class FsQueNoDebeTocarse:
        def listar(self, carpeta):
            raise AssertionError("se tocó una ruta de red")

        def metadatos(self, ruta):
            raise AssertionError("se tocó una ruta de red")

        def leer_texto(self, ruta):
            raise AssertionError("se tocó una ruta de red")

    recorrido = recorrer(FsQueNoDebeTocarse(), Ruta(r"\\servidor\recurso\proyecto"))
    assert recorrido.archivos == ()
    assert recorrido.no_revisadas == (r"\\servidor\recurso\proyecto",)


def test_archivo_gigante_se_salta_y_binario_no_se_lee(tmp_path: Path):
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    (proyecto / "binario.bin").write_bytes(b"MZ\x00\x00" + CANARIO.encode())
    with (proyecto / "gigante.log").open("wb") as f:
        f.truncate(2 * 1024 * 1024)
    (proyecto / "normal.txt").write_text("ok", encoding="utf-8")
    fs = FsSoloLectura()
    recorrido = recorrer(fs, Ruta(str(proyecto)))
    assert [os.path.basename(o) for o in recorrido.omitidos] == ["gigante.log"]
    for nombre in ("binario.bin", "gigante.log"):
        with pytest.raises(ArchivoNoLegible) as info:
            fs.leer_texto(Ruta(str(proyecto / nombre)))
        assert CANARIO not in str(info.value)
    assert fs.leer_texto(Ruta(str(proyecto / "normal.txt"))) == "ok"


def test_metadatos_de_ruta_inexistente_es_none(tmp_path: Path):
    assert FsSoloLectura().metadatos(Ruta(str(tmp_path / "nada"))) is None


# Casos del proyecto de prueba (se omiten si no está la variable de entorno) --------------------


@pytest.fixture
def proyecto_prueba() -> Path:
    raiz = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")
    if not raiz or not (Path(raiz) / "proyecto").is_dir():
        pytest.skip("AGENTREACH_PROYECTO_PRUEBA no apunta al proyecto de prueba")
    return Path(raiz)


def test_en01_en02_no02_no05_con_el_proyecto_de_prueba(proyecto_prueba: Path):
    proyecto = proyecto_prueba / "proyecto"
    detector = DetectorEnlaces(FsSoloLectura())
    hallazgos = Pipeline([detector]).ejecutar(Ruta(str(proyecto)))
    nombres = {os.path.basename(h.ubicacion.ruta) for h in hallazgos}
    assert "enlace-externo" in nombres  # EN-01
    assert "enlace-denegado" in nombres  # enlace con regla deny: igual que EN-01
    assert all(h.tipo is Tipo.ENLACE_FUERA_DEL_PROYECTO for h in hallazgos)
    assert not any("credentials.json" in h.ubicacion.ruta for h in hallazgos)  # EN-02
    assert not any(n in {"cola", "hooks"} for n in nombres)  # NO-02 y NO-05
    recorrido = recorrer(FsSoloLectura(), Ruta(str(proyecto)))
    assert "credentials.json" not in {os.path.basename(a.ruta) for a in recorrido.archivos}
    assert "sk_live" not in _todo_el_texto(recorrido, hallazgos)


def test_en03_enlace_simbolico_solo_si_el_entorno_lo_creo(proyecto_prueba: Path):
    simbolico = proyecto_prueba / "proyecto" / "enlace-simbolico"
    if not simbolico.is_symlink():
        pytest.skip("EN-03: el enlace simbólico no existe en este entorno")
    hallazgos = DetectorEnlaces(FsSoloLectura()).detectar(Ruta(str(proyecto_prueba / "proyecto")))
    assert any(h.ubicacion.ruta.endswith("enlace-simbolico") for h in hallazgos)
