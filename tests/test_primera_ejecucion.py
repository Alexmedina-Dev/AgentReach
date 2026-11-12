"""Historia 5b: primera ejecución completa. Se llama a ``main(argv)`` sin lanzar procesos."""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

import pytest

from agentreach import cli
from agentreach.app.auditar import ResultadoAuditoria
from agentreach.cli import main
from agentreach.contracts import (
    Ajeno,
    Etiqueta,
    Finding,
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
from agentreach.reporting.texto_minimo import formatear

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

# Los canarios se arman en la prueba: ningún literal con forma de secreto.
CANARIO = "".join(chr(c) for c in (67, 78, 82, 45, 53, 66)) + "-0001-" + "x" * 8
CANARIO_EXTERNO = "CNR-5B-EXTERNO-" + "".join(chr(c) for c in (90, 90, 57)) * 4
TOKEN_NPM = "".join(chr(c) for c in (110, 112, 109)) + "-falso-" + "q" * 10
GRANDE = 5 * 1024 * 1024 + 1


def _huella(raiz: Path, ignorar: tuple[str, ...] = ()) -> dict[str, tuple[int, int, str]]:
    """Rutas, tamaños, marcas de modificación y huella del contenido (sin seguir enlaces)."""
    salida: dict[str, tuple[int, int, str]] = {}
    for base, carpetas, archivos in os.walk(raiz, followlinks=False):
        carpetas[:] = [c for c in carpetas if not c.startswith(ignorar)]  # no se entra
        for nombre in sorted(carpetas + archivos):
            ruta = os.path.join(base, nombre)
            st = os.lstat(ruta)
            digest = ""
            if os.path.isfile(ruta) and not os.path.islink(ruta):
                try:
                    digest = hashlib.sha256(Path(ruta).read_bytes()).hexdigest()
                except OSError:
                    digest = "ilegible"  # p. ej. PP-03, con lectura negada a propósito
            salida[ruta] = (st.st_size, st.st_mtime_ns, digest)
    return salida


def _enlace_a_carpeta(destino: Path, enlace: Path) -> bool:
    try:
        import _winapi  # solo en Windows: junction real

        _winapi.CreateJunction(str(destino), str(enlace))
        return True
    except (ImportError, OSError, AttributeError):
        pass
    try:
        os.symlink(destino, enlace, target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        return False


@pytest.fixture
def mundo(tmp_path: Path) -> dict[str, Path]:
    externo = tmp_path / "externo"
    externo.mkdir()
    (externo / "secreto.txt").write_text(f"dato={CANARIO_EXTERNO}\n", encoding="utf-8")
    p = tmp_path / "proyecto"
    p.mkdir()
    (p / ".env").write_text(f"# nota\nANTHROPIC_API_KEY={CANARIO}\n", encoding="utf-8")
    (p / ".env.example").write_text("ANTHROPIC_API_KEY=changeme\n", encoding="utf-8")
    with open(p / "enorme.env", "wb") as f:
        f.truncate(GRANDE)
    (p / "notas.txt").write_bytes(b"\xff\xfe\x80 no es utf-8 \xc3\x28\n")
    assert _enlace_a_carpeta(externo, p / "enlace-externo")
    home = tmp_path / "home-falso"
    (home / ".ssh").mkdir(parents=True)
    (home / ".ssh" / "id_falsa").write_text("clave falsa\n", encoding="utf-8")
    (home / ".ssh" / "id_falsa.pub").write_text("publica\n", encoding="utf-8")
    (home / ".aws").mkdir()
    (home / ".aws" / "config").write_text("[default]\nregion=eu\n", encoding="utf-8")
    (home / ".npmrc").write_text(f"_authToken={TOKEN_NPM}\n", encoding="utf-8")
    return {"raiz": tmp_path, "proyecto": p, "home": home}


def _correr(capsys, *args: str) -> tuple[int, str, str]:
    codigo = main([*args, "--sin-reporte-html"])  # sin escribir en la carpeta personal
    capturado = capsys.readouterr()
    return codigo, capturado.out, capturado.err


def test_reporte_de_la_carpeta_sintetica(mundo, capsys):
    codigo, salida, error = _correr(capsys, str(mundo["proyecto"]), "--detalle")
    assert codigo == 1  # desde la Historia 11 hay hallazgos comprobados (el .env legible)
    assert re.search(r"línea 2 · Credencial en un archivo", salida) and "Código del catálogo: TH-1" in salida
    assert ".env.example" not in salida
    assert "archivo_demasiado_grande" in salida and "codificacion_no_utf8" in salida
    assert "TH-6" in salida  # el enlace se reporta, nunca lo de detrás
    for canario in (CANARIO, CANARIO_EXTERNO):
        assert canario not in salida and canario not in error
    assert "RESUMEN" in salida and "QUÉ NO PUDO REVISAR AGENTREACH" in salida


def test_solo_lectura_arbol_identico_y_sin_archivos_nuevos(mundo, capsys):
    antes = _huella(mundo["raiz"])
    _correr(capsys, str(mundo["proyecto"]))
    assert _huella(mundo["raiz"]) == antes


def test_sin_ejecutar_programas(mundo, capsys, monkeypatch):
    import subprocess

    def prohibido(*a, **k):
        raise AssertionError("AgentReach no debe ejecutar programas")

    for n in ("run", "Popen", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, n, prohibido)
    for n in dir(os):
        if n in ("system", "popen", "startfile") or n.startswith(("exec", "spawn")):
            monkeypatch.setattr(os, n, prohibido)
    codigo, _, _ = _correr(capsys, str(mundo["proyecto"]))
    assert codigo in (0, 1)  # 1: hay comprobados; lo que importa es que no se lanzó ningún programa


def test_opt_in_de_ubicaciones_sensibles(mundo, capsys):
    home = str(mundo["home"])
    _, sin, _ = _correr(capsys, str(mundo["proyecto"]), "--home", home, "--detalle")
    assert "home-falso" not in sin
    for ubicacion in ("~/.ssh", "~/.aws", "~/.npmrc"):
        assert ubicacion in sin
    assert "ubicacion_sensible_sin_activar" in sin
    _, con, _ = _correr(capsys, str(mundo["proyecto"]), "--home", home, "--incluir-ubicaciones-sensibles", "--detalle")
    assert "id_falsa" in con and "TH-2" in con
    assert ".npmrc" in con and "TH-1" in con
    assert "id_falsa.pub" not in con
    assert "region" not in con
    assert "ubicacion_sensible_sin_activar" not in con
    assert TOKEN_NPM not in con


def test_salida_estable_y_ruta_con_controles_limpia(mundo, capsys):
    uno = _correr(capsys, str(mundo["proyecto"]))
    dos = _correr(capsys, str(mundo["proyecto"]))
    assert uno == dos
    # En Windows no se pueden crear nombres con caracteres de control: se comprueba el formato.
    sucio = NoRevisado(Ruta("a\x1b[2Jb.txt"), MotivoNoRevisado.ARCHIVO_ILEGIBLE)
    texto = formatear((), (sucio,), 0)
    assert "\x1b" not in texto and "ab.txt" in texto.replace("[2J", "")


def test_carpeta_inexistente_da_codigo_2(mundo, capsys):
    codigo, salida, error = _correr(capsys, str(mundo["raiz"] / "no-existe"))
    assert codigo == 2 and salida == "" and "error:" in error
    codigo, _, _ = _correr(capsys, str(mundo["proyecto"] / ".env"))  # un archivo, no una carpeta
    assert codigo == 2


def test_hallazgo_comprobado_sin_hechos_se_corrige_y_no_da_codigo_1(mundo, capsys, monkeypatch):
    falso = Finding(
        ubicacion=Location(Ruta("falso.env")), tipo=Tipo.CREDENCIAL_EN_ARCHIVO,
        proveedor=Proveedor.DESCONOCIDO, nivel=Nivel.COMPROBADO, motivo=Motivo.NO_DETERMINADO,
        ajeno_a_tarea=Ajeno.NO_DETERMINADO, plataforma=Plataforma.NO_DETERMINADA,
        agente=Etiqueta("sin-agente"), postura=Postura.NO_DETERMINADA,
    )
    monkeypatch.setattr(cli, "auditar", lambda carpeta, config, **kw: ResultadoAuditoria((falso,), (), 1))
    codigo, salida, _ = _correr(capsys, str(mundo["proyecto"]))
    # un "comprobado" sin hechos que lo sostengan se corrige hacia abajo antes de imprimir: no cuenta para el código
    assert codigo == 0 and "Se bajó de comprobado a potencial" in salida


def test_cada_detector_pasa_por_la_tuberia(mundo, monkeypatch):
    from agentreach.app import auditar as modulo
    from agentreach.config import Configuracion
    from agentreach.core.pipeline import Pipeline

    vistos: list[str] = []
    original = Pipeline.ejecutar

    def espia(self, proyecto):
        vistos.extend(type(d).__name__ for d in self.detectores)
        return original(self, proyecto)

    monkeypatch.setattr(Pipeline, "ejecutar", espia)
    modulo.auditar(str(mundo["proyecto"]), Configuracion())
    assert vistos == [
        "DetectorEnlaces", "DetectorCredencialesArchivos", "DetectorGit", "DetectorContexto",
        "DetectorDespliegue", "DetectorInvisibles", "DetectorClaudeCode", "DetectorOpencode", "DetectorConfigEjecutaSola",
        "DetectorInstruccionesFuera",
        "DetectorUbicacionesUsuario",
        "DetectorEntorno",
    ]


# --- (f) proyecto de prueba real, solo lectura ---

_PRUEBA = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")


@pytest.mark.skipif(not _PRUEBA, reason="AGENTREACH_PROYECTO_PRUEBA no está definida")
def test_proyecto_de_prueba_real(capsys):
    raiz = Path(_PRUEBA)
    proyecto = raiz / "proyecto"
    antes = _huella(proyecto)  # solo la carpeta auditada: nunca se abre trampas*
    codigo, salida, error = _correr(capsys, str(proyecto), "--detalle")
    assert codigo == 1  # hay comprobados reales (PP-04, PP-05, GT-01, PA-01)
    texto = salida.replace("\\", "/")
    for esperado in (".env:2", ".env:7", ".env.production", ".env.staging", ".env.local",
                     "servicio-rastreado.env", "exportacion-abierta.env",
                     "notas-tipografia.txt", "enlace-externo"):
        assert esperado in texto, esperado
    assert ".env.example" not in texto
    assert not re.search(r"CNR0\d\d", salida + error)  # marcadores canario CNR001 a CNR023
    assert not (raiz / "trampas" / "PWNED.txt").exists()
    _, con, _ = _correr(capsys, str(proyecto), "--home", str(raiz / "home-falso"),
                        "--incluir-ubicaciones-sensibles", "--detalle")
    assert "TH-2" in con and "TH-3" in con and ".npmrc" in con
    assert ".pub" not in con
    assert _huella(proyecto) == antes


@pytest.mark.skipif(
    not (_PRUEBA and os.environ.get("AGENTREACH_PRUEBA_RAIZ")),
    reason="la corrida sobre la raíz entra en trampas*: solo con AGENTREACH_PRUEBA_RAIZ=1",
)
def test_segunda_corrida_sobre_la_raiz(capsys):
    codigo, salida, error = _correr(capsys, str(_PRUEBA))
    assert codigo in (0, 1) and not re.search(r"CNR0\d\d", salida + error)
