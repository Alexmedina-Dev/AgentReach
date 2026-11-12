"""FR-26: límites duros de lectura. Archivos hostiles: ninguno cuelga, falla ni produce un hallazgo; todos salen con su motivo."""

from __future__ import annotations

import os
import stat
import sys
import threading
from pathlib import Path

import pytest

from agentreach.app.auditar import auditar
from agentreach.config import Configuracion
from agentreach.contracts import MotivoNoRevisado
from agentreach.infra.lectura_segura import leer_seguro

CINCO_MB_MAS_UNO = 5 * 1024 * 1024 + 1
LIMITE_DE_TIEMPO = 60  # segundos: una tubería real que colgara no deja la prueba esperando para siempre

_RASTREO: dict[str, object] = {"raiz": None, "fuera": []}


def _normal(ruta: object) -> str:
    texto = os.path.normcase(os.path.realpath(os.fspath(ruta)))  # type: ignore[arg-type]
    return texto.removeprefix("\\\\?\\")  # el prefijo de rutas largas de Windows


def _pasa_por_leer_seguro() -> bool:
    """¿La pila que llamó pasa por la función ``leer_seguro`` del módulo del producto? (sin ``inspect.stack``: es lento)"""
    marco = sys._getframe(2)
    while marco is not None:
        if marco.f_code.co_name == "leer_seguro" and marco.f_code.co_filename.endswith("lectura_segura.py"):
            return True
        marco = marco.f_back
    return False


def _espia(evento: str, args: tuple) -> None:
    """Gancho de auditoría: ve TODA apertura (``open``, ``io``, ``Path.read_text``, ``os.open``...) y exige pasar por ``leer_seguro``."""
    raiz = _RASTREO["raiz"]
    if raiz is None or evento != "open" or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    try:
        if _normal(args[0]).startswith(str(raiz)) and not _pasa_por_leer_seguro():
            _RASTREO["fuera"].append(str(args[0]))  # type: ignore[union-attr]
    except (TypeError, ValueError, OSError):
        pass


sys.addaudithook(_espia)


def _crear_enlace(destino: Path, enlace: Path) -> bool:
    try:
        import _winapi

        _winapi.CreateJunction(str(destino), str(enlace))
        return True
    except (ImportError, OSError, AttributeError):
        pass
    try:
        os.symlink(destino, enlace, target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        return False


def _json_anidado(niveles: int) -> str:
    texto = "1"
    for _ in range(niveles):
        texto = '{"a":' + texto + "}"
    return texto


@pytest.fixture
def hostil(tmp_path: Path) -> Path:
    """Una carpeta con los archivos hostiles que el proyecto de prueba no trae (se generan aquí)."""
    p = tmp_path / "hostil"
    (p / ".claude").mkdir(parents=True)
    with open(p / "grande.txt", "wb") as f:
        f.truncate(CINCO_MB_MAS_UNO)  # 5 MB más un byte
    (p / "no_utf8.txt").write_bytes(b"\xff\xfe\x80 no es utf-8 \xc3\x28\n")
    (p / ".claude" / "settings.json").write_text(_json_anidado(65), encoding="utf-8")  # 65 niveles de JSON
    (p / "tuberia.txt").write_text("simulada", encoding="utf-8")
    (p / "normal.txt").write_text("nada de interes\n", encoding="utf-8")
    return p


def _auditar_vigilado(carpeta: Path, monkeypatch) -> tuple[object, list[str]]:
    """Audita con el espía de aperturas puesto, la tubería simulada y un tope de tiempo real (un hilo con ``join``)."""
    lstat_real = os.lstat

    def lstat_falso(ruta, *a, **k):
        real = lstat_real(ruta, *a, **k)
        if os.path.basename(str(ruta)) == "tuberia.txt":  # una tubería simulada: el tipo dice FIFO, no archivo regular
            campos = list(real)
            campos[0] = stat.S_IFIFO | 0o644
            return os.stat_result(campos)
        return real

    monkeypatch.setattr(os, "lstat", lstat_falso)
    # ``leer_seguro`` recibe su ``lstat`` por parámetro justo para esto (solo en pruebas): se inyecta también el falso
    monkeypatch.setitem(leer_seguro.__kwdefaults__, "lstat", lstat_falso)
    _RASTREO["raiz"], _RASTREO["fuera"] = _normal(carpeta), []
    resultado: list[object] = []
    errores: list[BaseException] = []

    def trabajo() -> None:
        try:
            resultado.append(auditar(str(carpeta), Configuracion()))
        except BaseException as error:  # noqa: BLE001 - se informa abajo; un hilo no propaga solo
            errores.append(error)

    hilo = threading.Thread(target=trabajo, daemon=True)
    hilo.start()
    hilo.join(LIMITE_DE_TIEMPO)
    fuera = list(_RASTREO["fuera"])  # type: ignore[arg-type]
    _RASTREO["raiz"] = None
    assert not hilo.is_alive(), f"la auditoría pasó de {LIMITE_DE_TIEMPO} s: algo se colgó"
    assert not errores, f"la auditoría lanzó {errores[0]!r}"
    return resultado[0], fuera


def _motivo_de(resultado, nombre: str) -> set[MotivoNoRevisado]:
    return {n.motivo for n in resultado.no_revisados if str(n.ruta).replace("\\", "/").endswith(nombre)}


def test_los_archivos_hostiles_salen_como_no_revisados_con_su_motivo(hostil: Path, monkeypatch):
    resultado, fuera = _auditar_vigilado(hostil, monkeypatch)
    assert _motivo_de(resultado, "grande.txt") == {MotivoNoRevisado.ARCHIVO_DEMASIADO_GRANDE}
    assert _motivo_de(resultado, "no_utf8.txt") == {MotivoNoRevisado.CODIFICACION_NO_UTF8}
    assert MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA in _motivo_de(resultado, "settings.json")
    assert _motivo_de(resultado, "tuberia.txt") == {MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR}
    assert not fuera, f"se abrió sin leer_seguro: {fuera}"  # ningún lector llamó a open fuera de leer_seguro


def test_ningun_archivo_hostil_produce_un_hallazgo(hostil: Path, monkeypatch):
    resultado, _ = _auditar_vigilado(hostil, monkeypatch)
    hostiles = ("grande.txt", "no_utf8.txt", "settings.json", "tuberia.txt")
    for h in resultado.hallazgos:
        assert not str(h.ubicacion.ruta).replace("\\", "/").endswith(hostiles), h.tipo
    assert resultado.archivos_mirados >= 1  # el archivo normal sí se miró


def test_un_json_de_64_niveles_se_acepta_y_uno_de_65_no(tmp_path: Path, monkeypatch):
    """El límite es de 64 niveles: en el borde, uno pasa y el siguiente se reporta."""
    for niveles, esperado in ((64, False), (65, True)):
        p = tmp_path / f"json{niveles}"
        (p / ".claude").mkdir(parents=True)
        (p / ".claude" / "settings.json").write_text(_json_anidado(niveles), encoding="utf-8")
        resultado, _ = _auditar_vigilado(p, monkeypatch)
        reportado = MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA in _motivo_de(resultado, "settings.json")
        assert reportado is esperado, niveles


def test_un_archivo_justo_en_el_limite_de_5_mb_no_se_reporta_como_demasiado_grande():
    """El tope es de 5 MB: ``leer_seguro`` rechaza lo que pasa de ahí, no lo que mide exactamente eso."""
    from agentreach.infra import lectura_segura

    assert lectura_segura.TOPE_BYTES == 5 * 1024 * 1024 and CINCO_MB_MAS_UNO == lectura_segura.TOPE_BYTES + 1
    assert lectura_segura.PROFUNDIDAD_MAXIMA == 64


def test_una_junction_hostil_no_se_sigue_ni_cuelga(hostil: Path, tmp_path: Path, monkeypatch):
    afuera = tmp_path / "afuera"
    afuera.mkdir()
    (afuera / "secreto.env").write_text("API_TOKEN=valor-largo-123\n", encoding="utf-8")
    if not _crear_enlace(afuera, hostil / "enlace-afuera") or not _crear_enlace(hostil, hostil / "enlace-ciclo"):
        if sys.platform == "win32":
            pytest.fail("en Windows una junction siempre se puede crear: la prueba no puede saltarse")
        pytest.skip("este sistema no permite crear enlaces simbólicos")
    resultado, fuera = _auditar_vigilado(hostil, monkeypatch)
    assert not fuera
    rutas = {str(h.ubicacion.ruta).replace("\\", "/") for h in resultado.hallazgos}
    assert not any(r.endswith("secreto.env") for r in rutas)  # lo de detrás del enlace nunca se leyó
    assert any(h.tipo.value == "TH-6" for h in resultado.hallazgos)  # el enlace que sale se reporta, sin entrar
    assert _motivo_de(resultado, "enlace-ciclo") <= {MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR}


def test_el_espia_de_aperturas_ve_cualquier_via(hostil: Path):
    """La propia vigilancia se prueba: ``Path.read_text``, ``io.open`` y ``io.FileIO`` sobre la carpeta se anotan."""
    import io

    _RASTREO["raiz"], _RASTREO["fuera"] = _normal(hostil), []
    try:
        (hostil / "normal.txt").read_text()
        open(hostil / "normal.txt").close()
        io.FileIO(hostil / "normal.txt").close()
        open(hostil / "normal.txt").close()
        assert len(_RASTREO["fuera"]) >= 4  # type: ignore[arg-type]
        _RASTREO["fuera"] = []
        assert isinstance(leer_seguro(str(hostil / "normal.txt")), str)  # type: ignore[arg-type]
        assert _RASTREO["fuera"] == []  # por ``leer_seguro`` sí se puede
    finally:
        _RASTREO["raiz"] = None


def test_el_proyecto_de_prueba_completo_y_la_carpeta_hostil_terminan_sin_excepcion(raiz_prueba: Path, hostil: Path, monkeypatch):
    """El proyecto de prueba completo como entrada, vigilado por el mismo espía; y la carpeta hostil aparte."""
    resultado, fuera = _auditar_vigilado(raiz_prueba, monkeypatch)
    assert not fuera, f"se abrió sin leer_seguro: {fuera[:3]}"  # en todo el proyecto, no solo en la carpeta hostil
    assert resultado.archivos_mirados > 30
    otro, _ = _auditar_vigilado(hostil, monkeypatch)
    assert len(otro.no_revisados) >= 4
