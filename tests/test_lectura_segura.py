"""Historia 4b: lectura segura única y "no se pudo revisar" con motivo de lista cerrada."""

from __future__ import annotations

import ast
import builtins
import io
import os
import stat
import sys
from pathlib import Path

import pytest

from agentreach.collectors.archivos_repo import DetectorCredencialesArchivos
from agentreach.collectors.enlaces import recorrer
from agentreach.contracts import ArchivoNoLegible, Ruta
from agentreach.contracts.no_revisado import MotivoNoRevisado, NoRevisado
from agentreach.infra.fs_solo_lectura import FsSoloLectura
from agentreach.infra.lectura_segura import (
    PROFUNDIDAD_MAXIMA,
    TOPE_BYTES,
    leer_seguro,
    revisar_profundidad_json,
)

CANARIO = "CANARIO-H4B-sk_live_" + "aa11bb22cc33dd44"
RAIZ_FUENTES = Path(__file__).resolve().parents[1] / "src" / "agentreach"


def _sin_abrir(monkeypatch) -> list[str]:
    """Hace fallar cualquier apertura de archivo y devuelve la lista de intentos (debe quedar vacía)."""
    intentos: list[str] = []

    def vigilar(original):
        def envoltura(ruta, *a, **k):
            intentos.append(str(ruta))
            raise AssertionError("se abrió un archivo que no debía abrirse")

        return envoltura

    monkeypatch.setattr(builtins, "open", vigilar(builtins.open))
    monkeypatch.setattr(io, "open", vigilar(io.open))
    monkeypatch.setattr(os, "open", vigilar(os.open))
    return intentos


def _enlace_de_carpeta(enlace: Path, destino: Path) -> bool:
    try:
        if sys.platform == "win32":
            import _winapi

            _winapi.CreateJunction(str(destino), str(enlace))
        else:
            os.symlink(destino, enlace, target_is_directory=True)
        return True
    except (OSError, NotImplementedError, AttributeError):
        return False


# (a) casos que salen como NoRevisado con el motivo correcto -----------------------------------------


def test_archivo_normal_devuelve_su_texto(tmp_path: Path):
    f = tmp_path / "a.env"
    f.write_bytes(b"X=1\n")  # bytes: write_text cambiaría el salto de línea en Windows
    assert leer_seguro(Ruta(str(f))) == "X=1\n"


def test_acepta_la_marca_bom_del_inicio(tmp_path: Path):
    f = tmp_path / "a.env"
    f.write_bytes(b"\xef\xbb\xbfX=1\n")
    assert leer_seguro(Ruta(str(f))) == "X=1\n"


def test_cinco_mb_mas_un_byte_es_demasiado_grande_sin_abrirlo(tmp_path: Path, monkeypatch):
    f = tmp_path / "grande.log"
    with f.open("wb") as h:
        h.truncate(TOPE_BYTES + 1)
    intentos = _sin_abrir(monkeypatch)
    r = leer_seguro(Ruta(str(f)))
    assert isinstance(r, NoRevisado) and r.motivo is MotivoNoRevisado.ARCHIVO_DEMASIADO_GRANDE
    assert intentos == []


def test_exactamente_cinco_mb_se_lee(tmp_path: Path):
    f = tmp_path / "justo.txt"
    f.write_bytes(b"a" * TOPE_BYTES)
    assert isinstance(leer_seguro(Ruta(str(f))), str)


def test_bytes_que_no_son_utf8_dan_codificacion_no_utf8(tmp_path: Path):
    f = tmp_path / "raro.env"
    f.write_bytes(b"X=\xff\xfe\xfd")
    r = leer_seguro(Ruta(str(f)))
    assert isinstance(r, NoRevisado) and r.motivo is MotivoNoRevisado.CODIFICACION_NO_UTF8


def test_un_lstat_falso_que_dice_tuberia_no_se_abre(tmp_path: Path, monkeypatch):
    f = tmp_path / "canal"
    f.write_text("x", encoding="utf-8")

    def lstat_falso(ruta):
        base = os.lstat(ruta)
        return os.stat_result((stat.S_IFIFO | 0o644, *tuple(base)[1:]))

    intentos = _sin_abrir(monkeypatch)
    r = leer_seguro(Ruta(str(f)), lstat=lstat_falso)
    assert isinstance(r, NoRevisado) and r.motivo is MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR
    assert intentos == []


def test_una_junction_no_se_sigue_ni_se_abre(tmp_path: Path, monkeypatch):
    destino = tmp_path / "destino"
    destino.mkdir()
    (destino / "secreto.env").write_text(f"X={CANARIO}", encoding="utf-8")
    enlace = tmp_path / "enlace"
    if not _enlace_de_carpeta(enlace, destino):
        pytest.skip("el entorno no permite crear enlaces de carpeta")
    intentos = _sin_abrir(monkeypatch)
    r = leer_seguro(Ruta(str(enlace)))
    assert isinstance(r, NoRevisado) and r.motivo is MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR
    assert intentos == [] and CANARIO not in repr(r)


def test_ruta_de_red_y_archivo_que_no_existe(tmp_path: Path):
    red = leer_seguro(Ruta("\\\\servidor\\recurso\\a.env"))
    assert isinstance(red, NoRevisado) and red.motivo is MotivoNoRevisado.RUTA_DE_RED
    falta = leer_seguro(Ruta(str(tmp_path / "no-existe.env")))
    assert isinstance(falta, NoRevisado) and falta.motivo is MotivoNoRevisado.ARCHIVO_ILEGIBLE


def test_una_carpeta_no_es_archivo_regular(tmp_path: Path):
    r = leer_seguro(Ruta(str(tmp_path)))
    assert isinstance(r, NoRevisado) and r.motivo is MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR


# (b) profundidad de JSON --------------------------------------------------------------------------------


def _json_anidado(niveles: int) -> str:
    return '{"a":' * niveles + "1" + "}" * niveles


def test_json_de_65_niveles_excede_la_profundidad():
    r = revisar_profundidad_json(Ruta("c.json"), _json_anidado(PROFUNDIDAD_MAXIMA + 1))
    assert isinstance(r, NoRevisado) and r.motivo is MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA


def test_json_de_64_niveles_y_corchetes_dentro_de_cadenas_no_excede():
    assert revisar_profundidad_json(Ruta("c.json"), _json_anidado(PROFUNDIDAD_MAXIMA)) is None
    assert revisar_profundidad_json(Ruta("c.json"), '{"a": "[[[[[[[{{{{{"}') is None


def test_la_profundidad_maxima_es_64():
    assert PROFUNDIDAD_MAXIMA == 64


# (c) motivos: solo razones de imposibilidad, nunca niveles ni sospechas ----------------------------------


def test_los_motivos_son_la_lista_cerrada_y_no_hablan_de_niveles():
    assert {m.value for m in MotivoNoRevisado} == {
        "ubicacion_sensible_sin_activar", "archivo_ilegible", "archivo_demasiado_grande",
        "no_es_archivo_regular", "codificacion_no_utf8", "profundidad_excedida", "ruta_de_red",
        "configuracion_no_interpretable", "version_no_reconocida", "historial_git_fase2", "funcion_no_modelada", "sin_permiso_fuera_del_proyecto",
    }
    prohibidas = ("comprobado", "potencial", "hipotesis", "sospech", "riesgo", "malicios", "peligro")
    for m in MotivoNoRevisado:
        assert not any(p in m.value or p in m.name.lower() for p in prohibidas), m


# (d) un motivo fuera de la lista falla -------------------------------------------------------------------


@pytest.mark.parametrize("motivo", ["archivo_sospechoso", "archivo_ilegible", None, 3])
def test_motivo_fuera_de_la_lista_falla(motivo):
    with pytest.raises(TypeError):
        NoRevisado(Ruta("a"), motivo)  # type: ignore[arg-type]  # ni siquiera el texto válido sin enum


def test_no_revisado_limpia_la_ruta_y_es_inmutable():
    n = NoRevisado(Ruta("a\x1b[2Jb"), MotivoNoRevisado.ARCHIVO_ILEGIBLE)
    assert "\x1b" not in n.ruta
    with pytest.raises(AttributeError):
        n.ruta = "otra"  # type: ignore[misc]


# (e) ningún lector de collectors/ abre archivos por su cuenta ----------------------------------------------


def _llamadas_que_abren(arbol: ast.AST) -> list[str]:
    prohibidas = {"open", "fdopen", "read_text", "read_bytes", "urlopen"}
    encontradas = []
    for n in ast.walk(arbol):
        if isinstance(n, ast.Call):
            f = n.func
            nombre = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
            if nombre in prohibidas:
                encontradas.append(nombre)
    return encontradas


def test_collectors_no_abre_archivos_fuera_de_lectura_segura():
    for archivo in (RAIZ_FUENTES / "collectors").rglob("*.py"):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        assert _llamadas_que_abren(arbol) == [], archivo.name


def test_la_prueba_de_apertura_detecta_un_open():
    assert _llamadas_que_abren(ast.parse("open('a'); Path('b').read_text(); os.fdopen(3)")) == [
        "open", "read_text", "fdopen",
    ]


def test_el_sistema_de_archivos_lee_solo_con_leer_seguro():
    arbol = ast.parse((RAIZ_FUENTES / "infra" / "fs_solo_lectura.py").read_text(encoding="utf-8"))
    assert _llamadas_que_abren(arbol) == []


# FsSoloLectura traduce el motivo y los detectores informan lo que no pudieron revisar -------------------------


def test_leer_texto_lanza_archivo_no_legible_con_su_motivo(tmp_path: Path):
    f = tmp_path / "raro.env"
    f.write_bytes(b"\xff\xfe")
    with pytest.raises(ArchivoNoLegible) as info:
        FsSoloLectura().leer_texto(Ruta(str(f)))
    assert info.value.motivo is MotivoNoRevisado.CODIFICACION_NO_UTF8


def test_el_recorrido_informa_lo_que_no_reviso_con_motivo(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    with (p / "grande.log").open("wb") as h:
        h.truncate(2 * 1024 * 1024)
    r = recorrer(FsSoloLectura(), Ruta(str(p)))
    assert r.omitidos  # el campo anterior sigue igual (Historia 2)
    assert [n.motivo for n in r.no_revisados] == [MotivoNoRevisado.ARCHIVO_DEMASIADO_GRANDE]
    red = recorrer(FsSoloLectura(), Ruta("\\\\servidor\\recurso\\p"))
    assert [n.motivo for n in red.no_revisados] == [MotivoNoRevisado.RUTA_DE_RED]


def test_el_detector_informa_no_revisados_en_vez_de_saltar_en_silencio(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    (p / "notas.txt").write_bytes(b"\xff\xfe\xfd")  # texto que no es UTF-8
    (p / ".env").write_bytes(b"API_TOKEN=" + CANARIO.encode() + b"\xff")
    detector = DetectorCredencialesArchivos(FsSoloLectura())
    hallazgos = list(detector.detectar(Ruta(str(p))))
    motivos = sorted(n.motivo.value for n in detector.no_revisados)
    assert motivos == ["codificacion_no_utf8", "codificacion_no_utf8"]
    assert CANARIO not in repr(detector.no_revisados) + repr(hallazgos)


def test_el_detector_informa_json_demasiado_anidado(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    (p / "credentials.json").write_text(_json_anidado(PROFUNDIDAD_MAXIMA + 1), encoding="utf-8")
    detector = DetectorCredencialesArchivos(FsSoloLectura())
    detector.detectar(Ruta(str(p)))
    assert [n.motivo for n in detector.no_revisados] == [MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA]


# Parches de la revisión ----------------------------------------------------------------------------------------


def test_fuera_del_proyecto_no_se_etiqueta_como_ilegible():
    from agentreach.contracts import FueraDelProyecto

    assert FueraDelProyecto("x").motivo is MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR


def test_json_demasiado_anidado_conserva_el_hallazgo_por_nombre(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    (p / "credentials.json").write_text(_json_anidado(PROFUNDIDAD_MAXIMA + 1), encoding="utf-8")
    detector = DetectorCredencialesArchivos(FsSoloLectura())
    assert len(list(detector.detectar(Ruta(str(p))))) == 1  # igual que un archivo ilegible
    assert len(detector.no_revisados) == 1


def test_la_lista_de_no_revisados_no_queda_desactualizada(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    (p / "notas.txt").write_bytes(b"\xff\xfe\xfd")
    detector = DetectorCredencialesArchivos(FsSoloLectura())
    detector.detectar(Ruta(str(p)))
    assert len(detector.no_revisados) == 1
    (p / "notas.txt").write_text("hola", encoding="utf-8")
    detector.detectar(Ruta(str(p)))
    assert detector.no_revisados == ()


def test_un_enlace_interno_no_seguido_se_informa(tmp_path: Path):
    p = tmp_path / "proyecto"
    (p / "real").mkdir(parents=True)
    if not _enlace_de_carpeta(p / "atajo", p / "real"):
        pytest.skip("el entorno no permite crear enlaces de carpeta")
    r = recorrer(FsSoloLectura(), Ruta(str(p)))
    assert r.enlaces == ()  # no sale del proyecto: no es hallazgo
    assert [n.motivo for n in r.no_revisados] == [MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR]
