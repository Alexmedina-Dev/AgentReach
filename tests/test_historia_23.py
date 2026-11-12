"""Historia 23: arreglos de la revisión de seguridad independiente de la historia 22 (``review-historia-22.md``)."""

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

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

AHORA = datetime(2026, 11, 10, 15, 30, 5)


class Tty(io.StringIO):
    encoding = "utf-8"

    def isatty(self) -> bool:
        return True


@pytest.fixture
def mundo(tmp_path: Path) -> dict:
    casa = tmp_path / "casa"
    casa.mkdir()
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    (proyecto / ".env").write_text("STRIPE_SECRET_KEY=sk_live_valor_largo_123\n", encoding="utf-8")
    return {"casa": casa, "proyecto": proyecto, "tmp": tmp_path}


def sin_leer(monkeypatch) -> None:
    monkeypatch.setattr(cli, "auditar", lambda *a, **k: pytest.fail("se leyó algo"))


def terminal_real(monkeypatch) -> io.StringIO:
    monkeypatch.setattr(cli, "_interactivo", INTERACTIVO_REAL)
    salida = Tty()
    monkeypatch.setattr(sys, "stdin", Tty())
    monkeypatch.setattr(sys, "stdout", salida)
    return salida


# ---- 1. el doctor no lista la carpeta -------------------------------------------------------------------------------------------


def test_el_doctor_no_lista_ni_abre_la_carpeta(mundo, monkeypatch):
    def prohibido(*a, **k):
        raise AssertionError("el doctor no puede listar la carpeta")

    for nombre in ("scandir", "listdir", "walk"):
        monkeypatch.setattr(os, nombre, prohibido)
    assert cli.main(["doctor", str(mundo["proyecto"])]) == 0
    assert cli.main(["doctor", str(mundo["tmp"] / "no-existe")]) == 1  # sin carpeta: falla de permisos, no traza


# ---- 2. --salida no pisa nada ----------------------------------------------------------------------------------------------------


def test_salida_no_pisa_un_archivo_existente_ni_lee_antes(mundo, monkeypatch, capsys):
    destino = mundo["tmp"] / "mi-config.toml"
    destino.write_text("contenido importante", encoding="utf-8")
    sin_leer(monkeypatch)
    preguntas: list[str] = []
    assert cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--salida", str(destino)],
                    preguntar=lambda t: preguntas.append(t) or "s") == 2
    assert destino.read_text(encoding="utf-8") == "contenido importante" and preguntas == []  # ni siquiera se preguntó
    assert "ya existe" in capsys.readouterr().err


def test_salida_crea_el_archivo_nuevo_y_una_segunda_vez_se_niega(mundo, capsys):
    destino = mundo["tmp"] / "r.txt"
    args = [str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--salida", str(destino), "--sin-reporte-html"]
    assert cli.main(args) == 1 and destino.exists()
    primero = destino.read_bytes()
    assert cli.main(args) == 2 and destino.read_bytes() == primero
    assert "ya existe" in capsys.readouterr().err


def test_doctor_salida_tampoco_pisa(mundo, capsys):
    destino = mundo["tmp"] / "d.txt"
    destino.write_text("antes", encoding="utf-8")
    assert cli.main(["doctor", str(mundo["proyecto"]), "--salida", str(destino)]) == 2
    assert destino.read_text(encoding="utf-8") == "antes" and "ya existe" in capsys.readouterr().err
    nuevo = mundo["tmp"] / "d2.txt"
    assert cli.main(["doctor", str(mundo["proyecto"]), "--salida", str(nuevo)]) == 0 and nuevo.exists()
    assert cli.main(["doctor", str(mundo["proyecto"]), "--salida", str(nuevo)]) == 2


def test_salida_hacia_un_enlace_existente_tampoco_se_sigue(mundo, capsys):
    objetivo = mundo["tmp"] / "objetivo.txt"
    objetivo.write_text("no tocar", encoding="utf-8")
    enlace = mundo["tmp"] / "enlace.txt"
    try:
        os.symlink(objetivo, enlace)
    except (OSError, NotImplementedError):
        pytest.skip("este sistema no permite crear enlaces simbólicos")
    assert cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"]), "--salida", str(enlace)]) == 2
    assert objetivo.read_text(encoding="utf-8") == "no tocar"


# ---- 3. la preferencia no se escribe a través de un enlace ---------------------------------------------------------------------------


def test_la_preferencia_no_se_escribe_a_traves_de_un_enlace_duro(mundo):
    carpeta = mundo["casa"] / reportes.CARPETA
    carpeta.mkdir()
    ajeno = mundo["tmp"] / "ajeno.json"
    ajeno.write_text('{"x": 1}', encoding="utf-8")
    try:
        os.link(ajeno, carpeta / "preferencias.json")
    except (OSError, NotImplementedError):
        pytest.skip("este sistema no permite enlaces duros")
    assert reportes.guardar_preferencia(str(mundo["casa"]), str(mundo["proyecto"]), True) is None
    assert ajeno.read_text(encoding="utf-8") == '{"x": 1}'


def test_la_preferencia_normal_si_se_guarda(mundo):
    assert reportes.guardar_preferencia(str(mundo["casa"]), str(mundo["proyecto"]), False) is not None
    assert reportes.leer_preferencia(str(mundo["casa"]), str(mundo["proyecto"])) is False


# ---- 4. ruta real y carpeta que contiene la personal ------------------------------------------------------------------------------


def test_si_la_ruta_es_un_enlace_la_pregunta_muestra_tambien_la_ruta_real(mundo, monkeypatch):
    enlace = mundo["tmp"] / "enlace"
    try:
        os.symlink(mundo["proyecto"], enlace, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("este sistema no permite crear enlaces simbólicos")
    terminal_real(monkeypatch)
    preguntas: list[str] = []
    cli.main([str(enlace), "--home", str(mundo["casa"])], preguntar=lambda t: preguntas.append(t) or "n")
    assert str(enlace) in preguntas[0] and "ruta real" in preguntas[0] and str(mundo["proyecto"].resolve()) in preguntas[0]


def test_una_carpeta_que_contiene_la_personal_lleva_la_advertencia(mundo, monkeypatch):
    terminal_real(monkeypatch)
    preguntas: list[str] = []
    cli.main([str(mundo["tmp"]), "--home", str(mundo["casa"])], preguntar=lambda t: preguntas.append(t) or "n")
    assert "ATENCIÓN" in preguntas[0] and "contiene la carpeta personal" in preguntas[0]
    preguntas.clear()
    cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"])], preguntar=lambda t: preguntas.append(t) or "n")
    assert "ATENCIÓN" not in preguntas[0]


# ---- 5. Ctrl+C --------------------------------------------------------------------------------------------------------------------


def test_ctrl_c_en_la_pregunta_sale_limpio_sin_leer(mundo, monkeypatch, capsys):
    terminal_real(monkeypatch)
    sin_leer(monkeypatch)

    def interrumpida(texto: str) -> str:
        raise KeyboardInterrupt

    assert cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"])], preguntar=interrumpida) == 130
    err = capsys.readouterr().err
    assert "Cancelado por la persona (Ctrl+C)" in err and "Traceback" not in err


def test_ctrl_c_durante_la_revision_tampoco_deja_traza(mundo, monkeypatch, capsys):
    terminal_real(monkeypatch)

    def interrumpida(*a, **k):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "auditar", interrumpida)
    assert cli.main([str(mundo["proyecto"]), "--home", str(mundo["casa"])], preguntar=lambda t: "s") == 130
    assert "Traceback" not in capsys.readouterr().err and reportes_vacios(mundo["casa"])


def reportes_vacios(casa: Path) -> bool:
    return not (casa / reportes.CARPETA).exists()


# ---- 6. la terminal se comprueba antes de mirar la carpeta -------------------------------------------------------------------------


def test_sin_terminal_ni_se_comprueba_si_la_carpeta_existe(mundo, monkeypatch, capsys):
    monkeypatch.setattr(cli, "_interactivo", INTERACTIVO_REAL)  # pytest no es una terminal
    vistas: list[str] = []
    real = os.path.isdir
    monkeypatch.setattr(os.path, "isdir", lambda p: vistas.append(str(p)) or real(p))
    assert cli.main([str(mundo["tmp"] / "no-existe"), "--salida", str(mundo["tmp"] / "x.txt")]) == 2
    err = capsys.readouterr().err
    assert "sin una terminal interactiva" in " ".join(err.split()) and "no existe" not in err
    assert not any("no-existe" in v for v in vistas)


def test_la_ruta_real_se_muestra_cuando_difiere_sin_necesitar_enlaces(mundo, monkeypatch):
    """Igual que la de enlaces, pero simulando que el sistema resuelve la ruta escrita a otra (así corre también sin privilegios)."""
    escrita = str(mundo["proyecto"])
    destino = str(mundo["tmp"] / "destino-real")
    real = os.path.realpath
    monkeypatch.setattr(os.path, "realpath", lambda p, **k: destino if os.path.abspath(str(p)) == os.path.abspath(escrita) else real(p, **k))
    terminal_real(monkeypatch)
    preguntas: list[str] = []
    cli.main([escrita, "--home", str(mundo["casa"])], preguntar=lambda t: preguntas.append(t) or "n")
    assert escrita in preguntas[0] and f"(ruta real: {destino})" in " ".join(preguntas[0].split())
