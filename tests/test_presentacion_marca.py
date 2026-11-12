"""Historia 13c: banner de marca, doctor, tema, tono, sin emojis, --version y --agente.

Las pruebas llaman a ``main(argv)`` con una terminal simulada y con todo lo que lanza procesos reemplazado por funciones que fallan.
"""

from __future__ import annotations

import io
import os
import re
import sys
from pathlib import Path

import pytest

from agentreach import cli
from agentreach.app.auditar import ResultadoAuditoria
from agentreach.app.doctor import FRASE_FINAL, Entorno, Estado, codigo_de_salida, comprobar
from agentreach.contracts import (
    CATALOGO_EXPLICACIONES,
    Ajeno,
    Etiqueta,
    Finding,
    Idioma,
    Location,
    Motivo,
    MotivoNoRevisado,
    Nivel,
    Plataforma,
    Postura,
    Proveedor,
    Ruta,
    Tipo,
)
from agentreach.core.catalogo_explicaciones import (
    COMO_RESOLVER_FORMAL,
    EXPLICACIONES_FORMAL,
    Tono,
    como_resolver,
    que_hacer,
    que_significa,
)
from agentreach.reporting import formato
from agentreach.reporting.formato import Color, resolver_tema
from agentreach.reporting.marca import LEMA, Tamano, banner, debe_mostrarse, tamano_efectivo

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

ESC = chr(27)
SGR24 = re.compile(ESC + r"\[38;2;(\d+);(\d+);(\d+)m")


class Tty(io.StringIO):
    """Una consola de mentira: dice ser una terminal y tiene la codificación que se le pida."""

    encoding = "utf-8"

    def isatty(self) -> bool:
        return True


class TtyCp437(Tty):
    encoding = "cp437"


@pytest.fixture(autouse=True)
def entorno_limpio(monkeypatch):
    """Sin variables que cambien el banner, el color o el idioma; sin lanzar procesos; consola de 80 columnas."""
    for nombre in ("NO_COLOR", "TERM", "COLORTERM", "WT_SESSION", "TERM_PROGRAM", "COLORFGBG", "AGENTREACH_IDIOMA", "AGENTREACH_TEMA",
                   "AGENTREACH_TONO", "AGENTREACH_NO_BANNER", "AGENTREACH_ASCII"):
        monkeypatch.delenv(nombre, raising=False)
    monkeypatch.setattr(cli, "activar_vt", lambda *a: True)
    monkeypatch.setattr(cli, "idioma_regional", lambda: "es")
    monkeypatch.setattr(cli.shutil, "get_terminal_size", lambda fallback=(80, 24): os.terminal_size((80, 24)))

    def prohibido(*a, **k):
        raise AssertionError("AgentReach no debe lanzar procesos")

    import subprocess

    for n in ("run", "Popen", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, n, prohibido)
    for n in dir(os):
        if n in ("system", "popen", "startfile") or n.startswith(("exec", "spawn")):
            monkeypatch.setattr(os, n, prohibido)


def en_terminal(monkeypatch, clase=Tty) -> io.StringIO:
    salida = clase()
    monkeypatch.setattr(sys, "stdout", salida)
    return salida


def correr(monkeypatch, argv: list[str], clase=Tty) -> tuple[int, str]:
    salida = en_terminal(monkeypatch, clase)
    codigo = cli.main(argv)
    return codigo, salida.getvalue()


def ayuda(monkeypatch, extra: list[str] | None = None, clase=Tty) -> str:
    """El texto de ``--help`` en una terminal (sale con SystemExit)."""
    salida = en_terminal(monkeypatch, clase)
    with pytest.raises(SystemExit):
        cli.main([*(extra or []), "--help"])
    return salida.getvalue()


def primera(texto: str) -> str:
    """La primera línea con contenido (el banner va después de una línea en blanco)."""
    return next(linea for linea in texto.splitlines() if linea.strip())


def sin_color(texto: str) -> str:
    return re.sub(ESC + r"\[[0-9;]*m", "", texto)


@pytest.fixture
def proyecto(tmp_path: Path) -> Path:
    (tmp_path / ".env").write_text("STRIPE_SECRET_KEY=sk_live_algo_largo_123\n", encoding="utf-8")
    return tmp_path


# ---- (a) los tres tamaños y su respaldo ASCII -----------------------------------------------------------------------------


def test_los_tres_tamanos_salen_en_una_terminal(monkeypatch, proyecto):
    grande = ayuda(monkeypatch)  # --help: el banner grande
    assert LEMA in grande and "█" in grande and len(grande.strip().splitlines()) >= 6
    _, mediano = correr(monkeypatch, ["doctor", str(proyecto)])
    assert "▀" in mediano and "█" in mediano and "█   █  ███  █████" not in mediano  # el mediano no es el grande
    assert mediano.startswith("\n\n\n") and not mediano.startswith("\n\n\n\n")  # tres líneas en blanco antes del banner
    _, revision = correr(monkeypatch, [str(proyecto)])  # la revisión también lleva el mediano, con su aire
    assert revision.startswith("\n\n\n") and "▀" in revision.splitlines()[3] and "█   █  ███  █████" not in revision
    assert "Reporte de revisión" in revision


@pytest.mark.parametrize("tamano", list(Tamano))
def test_la_version_ascii_solo_tiene_caracteres_ascii(tamano):
    lineas = banner(tamano, "0.1.0", ascii_=True)
    assert lineas and all(linea.isascii() for linea in lineas)
    assert any(not linea.isascii() for linea in banner(tamano, "0.1.0"))  # la versión Unicode sí usa símbolos de dibujo


def test_con_ascii_la_terminal_recibe_solo_ascii_en_el_banner(monkeypatch, proyecto):
    _, salida = correr(monkeypatch, [str(proyecto), "--ascii"])
    assert salida.isascii() and "A G E N T   R E A C H" in sin_color(salida) and salida.startswith("\n\n\n+---")


def test_el_tamano_baja_si_no_cabe():
    assert tamano_efectivo(Tamano.GRANDE, 80, True) is Tamano.GRANDE
    assert tamano_efectivo(Tamano.GRANDE, 50, True) is Tamano.MINIMO
    assert tamano_efectivo(Tamano.MEDIANO, 39, True) is None
    assert all(len(linea) <= 72 for t in (Tamano.GRANDE, Tamano.MEDIANO) for linea in banner(t, "0.1.0"))  # el máximo permitido
    assert all(len(linea) <= 72 for linea in banner(Tamano.MEDIANO, "0.1.0", ascii_=True))


# ---- (b) cuándo NO sale ------------------------------------------------------------------------------------------------------


def test_el_banner_no_sale_con_la_salida_redirigida(proyecto, capsys):
    cli.main([str(proyecto), "--sin-reporte-html"])
    assert LEMA not in capsys.readouterr().out
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    assert LEMA not in capsys.readouterr().out


def test_el_banner_no_sale_con_no_color_ni_no_banner_ni_variable_ni_salida(monkeypatch, proyecto, tmp_path):
    monkeypatch.setenv("NO_COLOR", "1")
    assert LEMA not in correr(monkeypatch, [str(proyecto)])[1]
    monkeypatch.delenv("NO_COLOR")
    assert LEMA not in correr(monkeypatch, [str(proyecto), "--no-banner"])[1]
    monkeypatch.setenv("AGENTREACH_NO_BANNER", "1")
    assert LEMA not in correr(monkeypatch, [str(proyecto)])[1]
    monkeypatch.delenv("AGENTREACH_NO_BANNER")
    monkeypatch.setenv("TERM", "dumb")
    assert LEMA not in correr(monkeypatch, [str(proyecto)])[1]
    monkeypatch.delenv("TERM")
    destino = tmp_path.parent / (tmp_path.name + "-reporte.txt")
    codigo, en_pantalla = correr(monkeypatch, [str(proyecto), "--salida", str(destino)])
    assert codigo in (0, 1) and LEMA not in en_pantalla and LEMA not in destino.read_text(encoding="utf-8")


def test_el_banner_no_sale_con_json_que_aun_no_existe(monkeypatch, proyecto, capsys):
    codigo, salida = correr(monkeypatch, [str(proyecto), "--json"])
    assert codigo == 2 and LEMA not in salida and "--json" in capsys.readouterr().err


def test_debe_mostrarse_solo_en_una_terminal_interactiva():
    assert debe_mostrarse(True, {}, False, False, False, 80)
    assert not debe_mostrarse(False, {}, False, False, False, 80)
    assert not debe_mostrarse(True, {}, False, False, False, 39)
    assert not debe_mostrarse(True, {"NO_COLOR": "1"}, False, False, False, 80)


# ---- (c) colores exactos ---------------------------------------------------------------------------------------------------


def test_los_colores_de_24_bits_son_exactamente_los_de_la_marca(monkeypatch, proyecto):
    monkeypatch.setenv("COLORTERM", "truecolor")
    # Historia 29: sin tema el logo ya no supone fondo oscuro; los colores de marca exactos son los de fondo oscuro
    _, salida = correr(monkeypatch, [str(proyecto), "--tema", "oscuro"])
    colores = {tuple(int(n) for n in m.groups()) for m in SGR24.finditer(primera(salida))}
    assert (0xEA, 0xF4, 0xF2) in colores  # AGENT #EAF4F2
    assert (0x3D, 0xF5, 0xD0) in colores  # REACH #3DF5D0
    grande = ayuda(monkeypatch, ["--tema", "oscuro"])
    assert (0xEA, 0xF4, 0xF2) in {tuple(int(n) for n in m.groups()) for m in SGR24.finditer(grande)}


def test_en_16_colores_se_usa_el_mas_cercano_documentado(monkeypatch, proyecto):
    _, salida = correr(monkeypatch, [str(proyecto), "--tema", "oscuro"])  # Historia 29: sin tema ya no es blanco/cian brillante
    linea = primera(salida)
    assert ESC + "[97m" in linea and ESC + "[96m" in linea  # blanco y cian brillantes
    assert not SGR24.search(linea)


# ---- (d) doctor -------------------------------------------------------------------------------------------------------------


def _marcas(texto: str) -> list[str]:
    return [linea for linea in sin_color(texto).splitlines() if re.match(r"\s+(\[ok\]|\[!\]|\[!!\]|√|▲|■)", linea)]


@pytest.mark.parametrize("idioma", ["es", "en"])
def test_doctor_muestra_siete_comprobaciones_y_la_frase_final(monkeypatch, proyecto, idioma):
    codigo, salida = correr(monkeypatch, ["doctor", str(proyecto), "--idioma", idioma])
    assert codigo == 0
    assert len(_marcas(salida)) == 7
    assert FRASE_FINAL[Idioma(idioma)] in salida
    assert "Código de salida: 0" in salida or "Exit code: 0" in salida


def test_doctor_sale_1_si_alguna_comprobacion_falla(monkeypatch, proyecto, tmp_path):
    assert correr(monkeypatch, ["doctor", str(proyecto)], TtyCp437)[0] == 1  # una consola cp437 no escribe los símbolos
    assert correr(monkeypatch, ["doctor", str(tmp_path / "no-existe")])[0] == 1  # sin permiso de lectura (o sin carpeta)


def _entorno(**cambios) -> Entorno:
    datos = dict(python=(3, 13, 0), carpeta=str(Path.cwd()), carpeta_indicada=False, codificacion="utf-8", es_terminal=True,  # noqa: C408
                 columnas=80, env={}, plataforma="linux", color=Color.DE_16, color_activado=True, idioma=Idioma.ES,
                 origen_idioma="regional")
    datos.update(cambios)
    return Entorno(**datos)


def test_cada_comprobacion_puede_fallar_o_avisar():
    assert codigo_de_salida(comprobar(_entorno())) == 0
    assert codigo_de_salida(comprobar(_entorno(python=(3, 11, 9)))) == 1
    assert codigo_de_salida(comprobar(_entorno(codificacion="ascii"))) == 1
    assert codigo_de_salida(comprobar(_entorno(codificacion="cp437"))) == 1  # no escribe ■ ▲ ◊ ○ √ →
    assert codigo_de_salida(comprobar(_entorno(plataforma="win32", color=Color.NINGUNO, color_activado=False))) == 1  # sin color
    avisos = comprobar(_entorno(columnas=50, color=Color.NINGUNO, env={"NO_COLOR": "1"}, codificacion="cp1252"))
    assert any(r.estado is Estado.AVISO for r in avisos)  # la codificación cp1252 y el poco ancho avisan
    assert codigo_de_salida(avisos) == 1  # cp1252 no escribe ■ ▲ ◊ ○ √ →: eso sí es una falla
    assert [r.clave for r in comprobar(_entorno())] == ["python", "permisos", "codificacion", "color", "unicode", "idioma", "ancho"]


def test_los_avisos_no_cuentan_para_el_codigo():
    resultados = comprobar(_entorno(columnas=50, color=Color.NINGUNO, env={"NO_COLOR": "1"}))
    assert [r.estado for r in resultados if r.clave in ("color", "ancho")] == [Estado.AVISO, Estado.AVISO]
    assert codigo_de_salida(resultados) == 0


def _huella(raiz: Path) -> dict[str, tuple[int, float, bytes]]:
    return {str(p): (p.stat().st_size, p.stat().st_mtime, p.read_bytes() if p.is_file() else b"") for p in raiz.rglob("*")}


def test_doctor_no_escribe_ni_lanza_nada(monkeypatch, proyecto):
    antes = _huella(proyecto)
    abiertos: list[str] = []
    real = open

    def espia(archivo, modo="r", *a, **k):
        if any(c in str(modo) for c in "wax+"):
            abiertos.append(f"{archivo}:{modo}")
        return real(archivo, modo, *a, **k)

    monkeypatch.setattr("builtins.open", espia)
    assert correr(monkeypatch, ["doctor", str(proyecto)])[0] == 0
    assert abiertos == [] and _huella(proyecto) == antes


# ---- (e) tema ---------------------------------------------------------------------------------------------------------------


def test_tema_gana_a_la_variable_y_esta_a_colorfgbg():
    assert resolver_tema("claro", {"AGENTREACH_TEMA": "oscuro", "COLORFGBG": "15;0"}) is True
    assert resolver_tema("oscuro", {"AGENTREACH_TEMA": "claro", "COLORFGBG": "0;15"}) is False
    assert resolver_tema(None, {"AGENTREACH_TEMA": "claro", "COLORFGBG": "15;0"}) is True
    assert resolver_tema("auto", {"COLORFGBG": "0;15"}) is True  # auto usa COLORFGBG
    assert resolver_tema(None, {}) is False  # si no se sabe, oscuro
    assert resolver_tema("raro", {"COLORFGBG": "0;15"}) is True  # un valor que no se entiende: se pasa a la fuente siguiente
    assert resolver_tema("auto", {"AGENTREACH_TEMA": "claro", "COLORFGBG": "15;0"}) is False  # una opción explícita corta la cascada
    assert resolver_tema(None, {"AGENTREACH_TEMA": "raro", "COLORFGBG": "0;15"}) is True


def _luminancia(hexa: str) -> float:
    def canal(c: int) -> float:
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (int(hexa[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def contraste(a: str, b: str) -> float:
    """Fórmula de contraste de la WCAG: (L1 + 0,05) / (L2 + 0,05) con L1 la mayor luminancia."""
    la, lb = sorted((_luminancia(a), _luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def test_cada_color_cumple_el_contraste_minimo_de_4_5_a_1():
    for rol, (oscuro, claro, *_) in formato._PALETA.items():
        assert contraste(oscuro, "000000") >= 4.5, (rol, "fondo oscuro")
        # Historia 29: las letras grandes de REACH sobre blanco piden 3:1 (no 4,5:1), el mínimo del logo; el resto, 4,5:1
        assert contraste(claro, "FFFFFF") >= (3.0 if rol == "marca_reach" else 4.5), (rol, "fondo claro")


def test_con_fondo_claro_sale_la_variante_clara(monkeypatch, proyecto):
    monkeypatch.setenv("COLORTERM", "truecolor")
    monkeypatch.setenv("COLORFGBG", "0;15")
    _, salida = correr(monkeypatch, [str(proyecto)])
    colores = {tuple(int(n) for n in m.groups()) for m in SGR24.finditer(salida)}
    assert (0x0B, 0x11, 0x14) in colores and (0x09, 0xA8, 0x88) in colores  # banner claro (Historia 29: colores nuevos)
    assert (0xEA, 0xF4, 0xF2) not in colores  # #EAF4F2 sobre blanco no se vería
    _, oscuro = correr(monkeypatch, [str(proyecto), "--tema", "oscuro"])
    assert (0xEA, 0xF4, 0xF2) in {tuple(int(n) for n in m.groups()) for m in SGR24.finditer(oscuro)}


# ---- (f) tono ---------------------------------------------------------------------------------------------------------------

TU = re.compile(r"\b(tú|tu|tus|ti|contigo)\b", re.IGNORECASE)
USTED = re.compile(r"\busted(es)?\b", re.IGNORECASE)


def _textos_es(tono: Tono) -> list[str]:
    from agentreach.app import doctor
    from agentreach.reporting import texto as modulo

    salida: list[str] = []
    for tipo in Tipo:
        salida += [que_hacer(tipo, Idioma.ES, tono)] + [que_significa(tipo, a, Idioma.ES, tono) for a in Ajeno]
    salida += [como_resolver(m, Idioma.ES, tono) for m in MotivoNoRevisado]
    for clave, por in modulo._T.items():
        salida.append(modulo._T_FORMAL.get(clave, por[Idioma.ES]) if tono is Tono.FORMAL else por[Idioma.ES])
    cercano, formal = zip(*doctor._CONSEJOS_ES.values(), strict=True)
    salida += list(formal if tono is Tono.FORMAL else cercano)
    salida += [t[Idioma.ES] for t in cli._ERROR.values()]
    return salida


def test_en_formal_ningun_texto_en_espanol_usa_tu_ni_tus():
    for t in _textos_es(Tono.FORMAL):
        assert not TU.search(t), t


def test_en_cercano_ningun_texto_usa_usted():
    for t in _textos_es(Tono.CERCANO):
        assert not USTED.search(t), t


def test_en_formal_hay_usted_y_en_cercano_hay_tu_en_los_textos_que_cambian():
    formal = " ".join(_textos_es(Tono.FORMAL))
    assert "usted" in formal and "Revise" in formal and not re.search(r"\bRevisa\b", formal)
    cercano = " ".join(_textos_es(Tono.CERCANO))
    assert re.search(r"\bRevisa\b", cercano) and not re.search(r"\bRevise\b", cercano)


def test_ambos_tonos_cubren_todos_los_tipos_y_motivos_en_los_dos_idiomas():
    assert set(EXPLICACIONES_FORMAL) == set(Tipo) == set(CATALOGO_EXPLICACIONES)
    assert set(COMO_RESOLVER_FORMAL) == set(MotivoNoRevisado)
    for tono in Tono:
        for idioma in Idioma:
            for tipo in Tipo:
                assert que_hacer(tipo, idioma, tono).strip() and que_significa(tipo, Ajeno.NO_DETERMINADO, idioma, tono).strip()
            for motivo in MotivoNoRevisado:
                assert como_resolver(motivo, idioma, tono).strip()
    for tipo in Tipo:  # en inglés el tono no cambia el pronombre: el texto es el mismo
        assert que_hacer(tipo, Idioma.EN, Tono.FORMAL) == que_hacer(tipo, Idioma.EN, Tono.CERCANO)


def test_la_opcion_y_la_variable_eligen_el_tono(monkeypatch, proyecto, capsys):
    cli.main([str(proyecto), "--tono", "formal"])
    formal = capsys.readouterr().out
    assert "ejecute con --detalle" in formal and "en su carpeta personal" in formal and "en tu carpeta personal" not in formal
    cli.main([str(proyecto)])
    assert "ejecuta con --detalle" in capsys.readouterr().out
    monkeypatch.setenv("AGENTREACH_TONO", "formal")
    cli.main([str(proyecto)])
    assert "ejecute con --detalle" in capsys.readouterr().out
    cli.main([str(proyecto), "--tono", "cercano"])  # la opción gana a la variable
    assert "ejecuta con --detalle" in capsys.readouterr().out


def test_el_doctor_tambien_tiene_los_dos_tonos(monkeypatch, proyecto):
    monkeypatch.setattr(cli.shutil, "get_terminal_size", lambda fallback=(80, 24): os.terminal_size((50, 24)))
    _, cercano = correr(monkeypatch, ["doctor", str(proyecto)])
    assert "Agranda" in cercano
    _, formal = correr(monkeypatch, ["doctor", str(proyecto), "--tono", "formal"])
    assert "Agrande" in formal and not TU.search(formal)


# ---- (g) sin emojis ---------------------------------------------------------------------------------------------------------

PERMITIDOS = set("■▲◊○√→·█▀▄")


def _hay_emoji(texto: str) -> bool:
    for c in texto:
        n = ord(c)
        if c in PERMITIDOS:
            continue
        if 0x1F000 <= n <= 0x1FAFF or 0x2600 <= n <= 0x27BF or 0x2B00 <= n <= 0x2BFF or n in (0xFE0F, 0x200D):
            return True
    return False


def test_ninguna_salida_lleva_emojis_y_todo_simbolo_tiene_respaldo_ascii(monkeypatch, proyecto, capsys):
    for argv in ([str(proyecto)], ["doctor", str(proyecto)], [str(proyecto), "--detalle", "--idioma", "en"]):
        _, salida = correr(monkeypatch, argv)
        assert not _hay_emoji(salida)
        _, ascii_ = correr(monkeypatch, [*argv, "--ascii"])
        assert ascii_.isascii()  # respaldo ASCII de cada símbolo
    cli.main([str(proyecto)])
    assert not _hay_emoji(capsys.readouterr().out)


# ---- (h) --version ----------------------------------------------------------------------------------------------------------


def test_version_es_una_sola_linea_estable(capsys, monkeypatch):
    with pytest.raises(SystemExit) as salida:
        cli.main(["--version"])
    assert salida.value.code == 0
    texto = capsys.readouterr().out
    assert re.fullmatch(r"agentreach \d+\.\d+\.\d+\n", texto)
    en_terminal(monkeypatch)
    with pytest.raises(SystemExit):
        cli.main(["--version"])
    assert LEMA not in sys.stdout.getvalue() and ESC not in sys.stdout.getvalue()  # sin banner ni color


# ---- (i) --agente ---------------------------------------------------------------------------------------------------------


def _finding(plataforma: Plataforma, nombre: str) -> Finding:
    return Finding(
        ubicacion=Location(Ruta(os.path.abspath(f"proyecto-falso/{nombre}")), 2), tipo=Tipo.CREDENCIAL_EN_ARCHIVO,
        proveedor=Proveedor.PAGOS, nivel=Nivel.POTENCIAL, motivo=Motivo.REGLA_DENY if plataforma is Plataforma.CLAUDE_CODE
        else Motivo.NO_DETERMINADO, ajeno_a_tarea=Ajeno.NO_DETERMINADO, plataforma=plataforma,
        agente=Etiqueta(plataforma.value.replace("_", "-")), postura=Postura.SIN_REGLA)


def _resultado_dos_agentes() -> ResultadoAuditoria:
    from agentreach.adapters.base import Regla, ResultadoAdaptador

    reglas = {p: ResultadoAdaptador(reglas=(Regla("deny", "Read", Location(Ruta(os.path.abspath(f"proyecto-falso/{p.value}.json")), 3), None),))
              for p in (Plataforma.CLAUDE_CODE, Plataforma.OPENCODE)}
    return ResultadoAuditoria(
        (_finding(Plataforma.CLAUDE_CODE, ".env"), _finding(Plataforma.OPENCODE, ".env")), (), 3, {},
        tuple(reglas.items()))


def test_agente_limita_hallazgos_y_reglas_a_ese_agente(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "auditar", lambda carpeta, config, **kw: _resultado_dos_agentes())
    cli.main([str(tmp_path), "--agente", "opencode"])
    solo_opencode = capsys.readouterr().out
    assert "opencode" in solo_opencode and "Claude Code" not in solo_opencode and "claude-code.json" not in solo_opencode
    cli.main([str(tmp_path), "--agente", "claude-code"])
    solo_claude = capsys.readouterr().out
    assert "Claude Code" in solo_claude and "opencode" not in solo_claude.replace("opencode.json", "")
    cli.main([str(tmp_path)])
    ambos = capsys.readouterr().out
    assert "AGENTE: Claude Code" in ambos and "AGENTE: opencode" in ambos  # una sección por agente


def test_un_agente_desconocido_da_codigo_2(tmp_path, capsys):
    with pytest.raises(SystemExit) as salida:
        cli.main([str(tmp_path), "--agente", "otro"])
    assert salida.value.code == 2 and "Traceback" not in capsys.readouterr().err


@pytest.fixture
def proyecto_prueba() -> Path:
    raiz = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")
    if not raiz or not (Path(raiz) / "proyecto").is_dir():
        pytest.skip("AGENTREACH_PROYECTO_PRUEBA no apunta al proyecto de prueba")
    return Path(raiz) / "proyecto"


@pytest.mark.skipif(sys.platform != "win32", reason="las sondas reales del permiso son de Windows")
def test_pp01_sale_en_ambos_agentes_como_hallazgos_distintos_sin_mezclar_niveles(proyecto_prueba, capsys):
    cli.main([str(proyecto_prueba), "--ancho", "100"])
    salida = capsys.readouterr().out
    claude = salida[salida.index("\nAGENTE: Claude Code\n-") + 2:]
    claude = claude[: claude.index("\nAGENTE: opencode\n-")]
    opencode = salida[salida.index("\nAGENTE: opencode\n-") + 2:]
    opencode = opencode[: opencode.index("\nSIN AGENTE")]
    assert re.search(r"(?m)^\.env$", claude) and re.search(r"(?m)^\.env$", opencode)  # PP-01 en las dos secciones
    assert "Claude Code" not in opencode and "opencode ·" not in claude
    solo = cli.main([str(proyecto_prueba), "--agente", "opencode", "--ancho", "100"])
    assert solo in (0, 1) and "Claude Code" not in capsys.readouterr().out.replace("Claude Code", "", 0)


# ---- parches de la revisión ----------------------------------------------------------------------------------------------


def test_sin_carpeta_el_banner_respeta_ascii_color_y_tema(monkeypatch):
    monkeypatch.setenv("COLORTERM", "truecolor")
    ascii_ = ayuda(monkeypatch, ["--ascii"])
    marca = ascii_.split("usage:")[0]  # el banner (la ayuda en español lleva tildes)
    assert marca.isascii() and "#" in marca and LEMA in marca
    sin = ayuda(monkeypatch, ["--color", "nunca"])
    assert ESC not in sin and LEMA in sin
    claro = ayuda(monkeypatch, ["--tema", "claro"])
    colores = {tuple(int(n) for n in m.groups()) for m in SGR24.finditer(claro)}
    assert (0x0B, 0x11, 0x14) in colores and (0xEA, 0xF4, 0xF2) not in colores  # nada invisible sobre fondo claro
    assert LEMA not in ayuda(monkeypatch, ["--no-banner"])


def test_la_ayuda_respeta_no_banner_y_las_opciones(monkeypatch):
    salida = en_terminal(monkeypatch)
    with pytest.raises(SystemExit):
        cli.main(["--no-banner", "--help"])
    assert LEMA not in salida.getvalue() and "--tono" in salida.getvalue()
    salida = en_terminal(monkeypatch)
    with pytest.raises(SystemExit):
        cli.main(["--help", "--ascii"])
    assert LEMA in salida.getvalue() and "█" not in salida.getvalue()


def test_en_16_colores_con_fondo_claro_no_se_usa_blanco_sobre_blanco(monkeypatch, proyecto):
    monkeypatch.setenv("COLORFGBG", "0;15")
    _, salida = correr(monkeypatch, [str(proyecto)])
    linea = primera(salida)
    assert ESC + "[30m" in linea and ESC + "[36m" in linea and ESC + "[97m" not in linea
    _, oscuro = correr(monkeypatch, [str(proyecto), "--tema", "oscuro"])
    assert ESC + "[97m" in primera(oscuro)


def test_doctor_con_salida_escribe_el_archivo_sin_banner_ni_color_y_la_rechaza_dentro_de_la_carpeta(monkeypatch, tmp_path):
    carpeta = tmp_path / "c"
    carpeta.mkdir()
    fuera = tmp_path / "doctor.txt"
    codigo, pantalla = correr(monkeypatch, ["doctor", str(carpeta), "--salida", str(fuera)])
    texto = fuera.read_text(encoding="utf-8")
    assert codigo == 0 and pantalla == "" and LEMA not in texto and ESC not in texto and FRASE_FINAL[Idioma.ES] in texto
    assert correr(monkeypatch, ["doctor", str(carpeta), "--salida", str(carpeta / "d.txt")])[0] == 2


def test_las_opciones_antes_del_subcomando_no_lo_rompen(monkeypatch, proyecto):
    for argv in (["--tono", "formal", "doctor", str(proyecto)], ["--idioma", "en", "doctor", str(proyecto)]):
        codigo, salida = correr(monkeypatch, argv)
        assert codigo == 0 and "doctor" not in salida.split("\n")[-2].lower() or len(_marcas(salida)) == 7
        assert len(_marcas(salida)) == 7
    assert cli._comando(["--tono", "formal", "doctor", "x"]) == ("doctor", ["--tono", "formal", "x"])
    assert cli._comando(["--home", "doctor"]) == ("audit", ["--home", "doctor"])  # «doctor» aquí es el valor de --home


def test_el_banner_se_adapta_al_ancho(monkeypatch, proyecto):
    assert tamano_efectivo(Tamano.GRANDE, 62, True) is Tamano.GRANDE  # el grande mide 61
    assert tamano_efectivo(Tamano.MEDIANO, 62, True) is Tamano.MINIMO  # el mediano con versión mide 69
    assert tamano_efectivo(Tamano.MEDIANO, 70, True) is Tamano.MEDIANO
    estrecho = banner(Tamano.MINIMO, "0.1.0", ancho=45)[0]
    assert LEMA not in estrecho and len(estrecho) <= 44 and LEMA in banner(Tamano.MINIMO, "0.1.0", ancho=80)[0]


def test_debe_mostrarse_cubre_cada_condicion_que_lo_apaga():
    base = (True, {}, False, False, False, 80)
    assert debe_mostrarse(*base)
    assert not debe_mostrarse(True, {"TERM": "dumb"}, False, False, False, 80)
    assert not debe_mostrarse(True, {"AGENTREACH_NO_BANNER": "1"}, False, False, False, 80)
    assert not debe_mostrarse(True, {"AGENTREACH_NO_BANNER": "yes"}, False, False, False, 80)
    assert not debe_mostrarse(True, {}, True, False, False, 80)  # --no-banner
    assert not debe_mostrarse(True, {}, False, True, False, 80)  # --json
    assert not debe_mostrarse(True, {}, False, False, True, 80)  # --salida


def test_redirigido_no_hay_banner_grande_ni_bloques_ni_lema(proyecto, capsys):
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    cli.main(["doctor", str(proyecto)])
    cli.main([str(proyecto), "--sin-reporte-html"])
    salida = capsys.readouterr().out
    assert LEMA not in salida and "█" not in salida and "▀" not in salida


def test_doctor_con_color_nunca_dice_el_motivo_real(monkeypatch, proyecto):
    _, salida = correr(monkeypatch, ["doctor", str(proyecto), "--color", "nunca"])
    assert "--color nunca" in salida and "no es una terminal" not in salida


def test_doctor_con_stdout_sin_codificacion_o_sin_directorio_actual_no_da_traza(monkeypatch, tmp_path):
    class SinCodificacion(io.StringIO):
        encoding = None

        def isatty(self):
            return True

    monkeypatch.setattr(sys, "stdout", SinCodificacion())
    assert cli.main(["doctor", str(tmp_path)]) == 0  # una consola sin codificación declarada se toma como UTF-8
    salida = en_terminal(monkeypatch)

    def roto():
        raise FileNotFoundError

    monkeypatch.setattr(os, "getcwd", roto)
    assert cli.main(["doctor"]) == 1 and "FALLO" in salida.getvalue()  # sin directorio actual: falla de permisos, no traza


def test_la_ayuda_no_da_traza_con_una_consola_ascii(monkeypatch):
    class Ascii(io.StringIO):
        encoding = "ascii"

        def isatty(self):
            return False

    monkeypatch.setattr(sys, "stdout", Ascii())
    with pytest.raises(SystemExit) as salida:
        cli.main(["--help"])
    assert salida.value.code == 0


def test_agente_filtra_tambien_el_conteo_de_correcciones(monkeypatch, tmp_path, capsys):
    (tmp_path / ".env").write_text("API_TOKEN=valor-largo-123" + chr(10), encoding="utf-8")
    ubicacion = Location(Ruta(str(tmp_path / ".env")), 1)
    base = {"ubicacion": ubicacion, "tipo": Tipo.CREDENCIAL_EN_ARCHIVO, "proveedor": Proveedor.PAGOS, "ajeno_a_tarea": Ajeno.NO_DETERMINADO,
            "postura": Postura.SIN_REGLA}
    falso = Finding(**base, nivel=Nivel.COMPROBADO, motivo=Motivo.EXISTE_LEGIBLE_SIN_REGLA, plataforma=Plataforma.CLAUDE_CODE,
                    agente=Etiqueta("claude-code"))  # un comprobado sin hechos: se corrige
    sano = Finding(**base, nivel=Nivel.POTENCIAL, motivo=Motivo.NO_DETERMINADO, plataforma=Plataforma.OPENCODE, agente=Etiqueta("opencode"))
    monkeypatch.setattr(cli, "auditar", lambda carpeta, config, **kw: ResultadoAuditoria((falso, sano), (), 3))
    cli.main([str(tmp_path), "--agente", "opencode"])
    assert "Autocomprobación" not in capsys.readouterr().out  # la corrección era de Claude Code
    cli.main([str(tmp_path), "--agente", "claude-code"])
    assert "Se bajó de comprobado a potencial" in capsys.readouterr().out
