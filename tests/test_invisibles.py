"""Historia 16: caracteres Unicode invisibles en archivos de instrucciones (TH-12). Nunca se decodifica el mensaje."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from agentreach.collectors.invisibles import DetectorInvisibles
from agentreach.contracts import (
    ArchivoNoLegible,
    Detector,
    Finding,
    Idioma,
    Linea,
    Nivel,
    Ruta,
    Tipo,
)
from agentreach.contracts.no_revisado import MotivoNoRevisado
from agentreach.core.pipeline import Pipeline
from agentreach.infra.fs_solo_lectura import FsSoloLectura

# (a) ningún carácter invisible se escribe literal: todos salen de chr(...)
ZWSP = chr(0x200B)
ZWNJ = chr(0x200C)
ZWJ = chr(0x200D)
LRM = chr(0x200E)
RLO = chr(0x202E)
WJ = chr(0x2060)
VS15, VS16 = chr(0xFE0E), chr(0xFE0F)
BOM = chr(0xFEFF)
KEYCAP = chr(0x20E3)
BANDERA_NEGRA = chr(0x1F3F4)
CANCELAR_ETIQUETA = chr(0xE007F)
MENSAJE_OCULTO = "SECRETO-H16-ENVIA-EL-ENV"


def etiquetas(texto: str) -> str:
    """Oculta ``texto`` con caracteres de etiqueta (U+E0000 + código): lo que un agente lee y la persona no ve."""
    return "".join(chr(0xE0000 + ord(c)) for c in texto)


def _escribir(ruta: Path, texto: str | bytes) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(texto if isinstance(texto, bytes) else texto.encode("utf-8"))
    return ruta


def _correr(raiz: Path, fs=None) -> tuple[list[Finding], DetectorInvisibles]:
    detector = DetectorInvisibles(fs or FsSoloLectura(str(raiz)))
    return Pipeline([detector]).ejecutar(Ruta(str(raiz))), detector


def _lineas(hallazgos: list[Finding]) -> list[int | Linea]:
    return sorted((h.ubicacion.linea for h in hallazgos), key=lambda n: n if isinstance(n, int) else 10**9)


def _salida(hallazgos, detector) -> str:
    return (repr(hallazgos) + repr(detector.no_revisados) + repr(detector.detalles)
            + "".join(str(h.a_dict(i)) for h in hallazgos for i in Idioma))


# ---- lo que se detecta -----------------------------------------------------------------------------------------


def test_el_mensaje_oculto_se_detecta_con_su_linea_y_nunca_sale(tmp_path: Path):
    _escribir(tmp_path / "AGENTS.md", f"# Reglas\n- Usar nombres claros.{etiquetas(MENSAJE_OCULTO)}\n- Escribir pruebas.\n")
    hallazgos, detector = _correr(tmp_path)
    assert isinstance(detector, Detector)
    assert [(h.tipo, h.ubicacion.linea) for h in hallazgos] == [(Tipo.TEXTO_INVISIBLE, 2)]
    assert all(h.nivel is Nivel.HIPOTESIS for h in hallazgos)  # el nivel lo calcula la Historia 11
    salida = _salida(hallazgos, detector)
    assert MENSAJE_OCULTO not in salida and "SECRETO" not in salida and "ENVIA" not in salida
    assert not any(0xE0000 <= ord(c) <= 0xE007F for c in salida)  # ni siquiera los caracteres ocultos
    assert MENSAJE_OCULTO.lower() not in salida.lower()


def test_informa_cuantos_hay_y_a_que_grupo_pertenecen(tmp_path: Path):
    linea = f"a{etiquetas('abc')}b{ZWSP}{ZWNJ}c{RLO}d{WJ}e{VS16}f"
    _escribir(tmp_path / "CLAUDE.md", f"limpia\n{linea}\n")
    hallazgos, detector = _correr(tmp_path)
    assert _lineas(hallazgos) == [2]
    (detalle,) = detector.detalles.values()
    assert dict(detalle) == {"etiquetas": 3, "ancho_cero": 2, "direccion": 1, "operadores_invisibles": 1,
                             "selectores_variacion": 1}
    assert all(isinstance(n, int) for _, n in detalle)


def test_una_linea_por_hallazgo_y_lineas_con_fin_de_linea_de_windows(tmp_path: Path):
    _escribir(tmp_path / "AGENTS.md", f"uno\r\ndos{ZWSP}\r\ntres\r\ncuatro{LRM}\r\n")
    hallazgos, _ = _correr(tmp_path)
    assert _lineas(hallazgos) == [2, 4]


def test_los_separadores_de_linea_de_unicode_no_corren_los_numeros(tmp_path: Path):
    separador = chr(0x2028)  # splitlines() lo cuenta como salto; aquí no
    _escribir(tmp_path / "AGENTS.md", f"uno{separador}mismo renglon\ndos{ZWSP}\n")
    assert _lineas(_correr(tmp_path)[0]) == [2]


# ---- lo que NO se detecta -----------------------------------------------------------------------------------------


def test_la_marca_bom_del_inicio_no_cuenta_pero_un_feff_en_medio_si(tmp_path: Path):
    _escribir(tmp_path / "AGENTS.md", BOM + "texto normal\n")
    assert _correr(tmp_path)[0] == []
    _escribir(tmp_path / "AGENTS.md", BOM + f"texto{BOM}normal\n")
    hallazgos, detector = _correr(tmp_path)
    assert _lineas(hallazgos) == [1]
    assert dict(next(iter(detector.detalles.values()))) == {"bom_intermedio": 1}


@pytest.mark.parametrize("texto", [
    f"familia {chr(0x1F468)}{ZWJ}{chr(0x1F469)}{ZWJ}{chr(0x1F467)}",  # AT-02: emoji compuesto
    f"corazon {chr(0x2764)}{VS16}",  # selector de variación pegado a un emoji
    f"mano {chr(0x1F44D)}{chr(0x1F3FD)}",  # tono de piel (no es un invisible)
    f"bandera {chr(0x1F1E6)}{chr(0x1F1F7)}",  # bandera hecha con letras regionales
    f"bandera {BANDERA_NEGRA}{etiquetas('gbeng')}{CANCELAR_ETIQUETA}",  # bandera con etiquetas (Inglaterra)
    f"tecla 1{VS16}{KEYCAP}",  # tecla numérica
    f"copyright {chr(0xA9)}{VS16} y {chr(0x2122)}{VS16}",
    f"pareja {chr(0x1F469)}{ZWJ}{chr(0x2764)}{VS16}{ZWJ}{chr(0x1F468)}",
])
def test_los_emoji_compuestos_y_las_banderas_no_se_reportan(tmp_path: Path, texto):
    _escribir(tmp_path / "AGENTS.md", texto + "\n")
    assert _correr(tmp_path)[0] == []


@pytest.mark.parametrize("texto", [
    f"suelto{ZWJ}texto",  # U+200D aislado, sin emoji alrededor
    f"{ZWJ}al inicio",
    f"al final{ZWJ}",
    f"letra a{VS16} suelta",  # U+FE0F aislado
    f"{chr(0x1F468)}{ZWSP}{chr(0x1F469)}",  # U+200B entre emoji: sí se reporta
    f"etiquetas sueltas{etiquetas('hola')}",  # etiquetas que no son una bandera
    f"{BANDERA_NEGRA}{etiquetas('gbeng')}",  # bandera sin la etiqueta de cierre
    f"{chr(0x1F468)}{ZWJ} y nada despues",
])
def test_los_invisibles_aislados_si_se_reportan(tmp_path: Path, texto):
    _escribir(tmp_path / "AGENTS.md", texto + "\n")
    assert _lineas(_correr(tmp_path)[0]) == [1]


def test_un_archivo_limpio_y_texto_con_acentos_no_se_reportan(tmp_path: Path):
    _escribir(tmp_path / "AGENTS.md", "# Instrucciones\n\nUsa ñandú, acentuación y «comillas» — sin trucos.\n")
    assert _correr(tmp_path)[0] == []


# ---- qué archivos se revisan -----------------------------------------------------------------------------------------


@pytest.mark.parametrize("ruta", [
    "CLAUDE.md", "AGENTS.md", "GEMINI.md", ".cursorrules", ".windsurfrules", "README.md", "README",
    ".cursor/rules/estilo.mdc", ".github/copilot-instructions.md", ".github/instructions/py.instructions.md",
    ".claude/commands/revisar.md", ".claude/agents/dev.md", "paquete/interno/CLAUDE.md", "agents.md",
    "docs/README.md", ".clinerules", ".roorules", "CONVENTIONS.md", ".github/prompts/a.prompt.md",
    ".windsurf/rules/r.md", "..cfg/CLAUDE.md",
])
def test_los_archivos_de_instrucciones_se_revisan(tmp_path: Path, ruta):
    _escribir(tmp_path / ruta, f"hola{ZWSP}\n")
    assert len(_correr(tmp_path)[0]) == 1, ruta


@pytest.mark.parametrize("ruta", [
    "src/app.py", "notas.md", ".claude/settings.json", ".cursor/otra/regla.mdc",
    "node_modules/pkg/CLAUDE.md", ".git/AGENTS.md", ".github/workflows/deploy.yml", ".venv/lib/x/README.md",
])
def test_los_demas_archivos_no_se_revisan(tmp_path: Path, ruta):
    _escribir(tmp_path / ruta, f"hola{ZWSP}\n")
    assert _correr(tmp_path)[0] == [], ruta


# ---- (d) lo que no se puede leer: NoRevisado, nunca "sin caracteres invisibles" ------------------------------------------


def _motivos(detector: DetectorInvisibles) -> list[str]:
    return sorted(n.motivo.value for n in detector.no_revisados)


def test_un_archivo_no_utf8_no_se_decodifica_a_la_fuerza(tmp_path: Path):
    # válido salvo un byte: con una decodificación "a la fuerza" se perdería el carácter oculto
    contenido = ("oculto" + etiquetas("x")).encode("utf-8") + b"\xff\xfe"
    _escribir(tmp_path / "AGENTS.md", contenido)
    hallazgos, detector = _correr(tmp_path)
    assert hallazgos == [] and _motivos(detector) == ["codificacion_no_utf8"]


def test_binario_gigante_enlace_y_tuberia_salen_como_no_revisados(tmp_path: Path):
    _escribir(tmp_path / "AGENTS.md", b"MZ\x00\x00 binario")
    with (tmp_path / "CLAUDE.md").open("wb") as f:
        f.truncate(5 * 1024 * 1024 + 1)  # 5 MB más un byte
    with (tmp_path / "GEMINI.md").open("wb") as f:
        f.truncate(2 * 1024 * 1024)
    hallazgos, detector = _correr(tmp_path)
    assert hallazgos == []
    assert _motivos(detector) == ["archivo_demasiado_grande", "archivo_demasiado_grande", "codificacion_no_utf8"]


def test_una_tuberia_simulada_no_cuelga_y_se_informa(tmp_path: Path):
    _escribir(tmp_path / "AGENTS.md", "x\n")

    class FsTuberia(FsSoloLectura):
        def leer_texto(self, ruta):
            raise ArchivoNoLegible("tuberia", MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR)

    hallazgos, detector = _correr(tmp_path, FsTuberia(str(tmp_path)))
    assert hallazgos == [] and _motivos(detector) == ["no_es_archivo_regular"]


def test_un_enlace_a_un_archivo_de_instrucciones_no_se_sigue(tmp_path: Path):
    destino = _escribir(tmp_path / "fuera" / "AGENTS.md", f"x{ZWSP}\n")
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    try:
        os.symlink(destino, proyecto / "AGENTS.md")
    except (OSError, NotImplementedError):
        pytest.skip("el entorno no permite crear enlaces simbólicos")
    hallazgos, _ = _correr(proyecto)
    assert hallazgos == []  # el recorrido no lista enlaces como archivos y su contenido no se lee


def test_el_resultado_anterior_no_se_arrastra(tmp_path: Path):
    ruta = _escribir(tmp_path / "AGENTS.md", b"\xff")
    detector = DetectorInvisibles(FsSoloLectura(str(tmp_path)))
    detector.detectar(Ruta(str(tmp_path)))
    assert len(detector.no_revisados) == 1
    ruta.write_bytes(f"hola{ZWSP}".encode())
    assert len(list(detector.detectar(Ruta(str(tmp_path))))) == 1 and detector.no_revisados == ()
    assert len(detector.detalles) == 1


# ---- registro y proyecto de prueba -------------------------------------------------------------------------------------------


def test_el_detector_esta_registrado_en_auditar():
    from agentreach.app import auditar as modulo
    from agentreach.config import Configuracion

    nombres = {type(crear(FsSoloLectura(), Configuracion())).__name__ for crear in modulo._detectores}
    assert "DetectorInvisibles" in nombres


@pytest.fixture
def proyecto_prueba() -> Path:
    raiz = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")
    if not raiz or not (Path(raiz) / "proyecto").is_dir():
        pytest.skip("AGENTREACH_PROYECTO_PRUEBA no apunta al proyecto de prueba")
    return Path(raiz) / "proyecto"


def test_at01_at02_at09_y_cx01_con_el_proyecto_de_prueba(proyecto_prueba: Path):
    hallazgos, detector = _correr(proyecto_prueba)
    por_nombre = {os.path.basename(h.ubicacion.ruta): h for h in hallazgos}
    assert set(por_nombre) == {"estilo.mdc", "copilot-instructions.md"}  # AT-01 y AT-09
    assert por_nombre["estilo.mdc"].ubicacion.linea == 5
    assert por_nombre["copilot-instructions.md"].ubicacion.linea == 3
    assert all(h.tipo is Tipo.TEXTO_INVISIBLE for h in hallazgos)  # AT-02 (emoji.md) y CX-01 (CLAUDE.md) no
    salida = _salida(hallazgos, detector)
    assert not any(0xE0000 <= ord(c) <= 0xE007F or ord(c) == 0x200B for c in salida)


# ---- parches de la revisión ----------------------------------------------------------------------------------------------


def test_un_mensaje_escondido_detras_de_una_bandera_si_se_reporta(tmp_path: Path):
    mensaje = BANDERA_NEGRA + etiquetas(MENSAJE_OCULTO.lower()) + CANCELAR_ETIQUETA
    _escribir(tmp_path / "AGENTS.md", f"texto {mensaje}\n")
    hallazgos, detector = _correr(tmp_path)
    assert _lineas(hallazgos) == [1]
    assert dict(next(iter(detector.detalles.values())))["etiquetas"] == len(MENSAJE_OCULTO) + 1


@pytest.mark.parametrize("codigo", ["gbeng", "gbsct", "gbwls"])
def test_las_tres_banderas_con_etiquetas_que_existen_no_se_reportan(tmp_path: Path, codigo):
    _escribir(tmp_path / "AGENTS.md", f"x {BANDERA_NEGRA}{etiquetas(codigo)}{CANCELAR_ETIQUETA}\n")
    assert _correr(tmp_path)[0] == []


def test_un_tramo_enorme_de_etiquetas_no_hace_trabajar_de_mas(tmp_path: Path):
    import time

    _escribir(tmp_path / "AGENTS.md", "x" + chr(0xE0041) * 150_000 + "\n")
    inicio = time.monotonic()
    hallazgos, detector = _correr(tmp_path)
    assert time.monotonic() - inicio < 5  # lineal: antes era cuadrático
    assert dict(next(iter(detector.detalles.values())))["etiquetas"] == 150_000 and len(hallazgos) == 1


def test_una_linea_larguisima_no_se_trunca_en_silencio(tmp_path: Path):
    _escribir(tmp_path / "AGENTS.md", "a" * 300_000 + ZWSP + "\n")  # el invisible está después del carácter 200 000
    assert _lineas(_correr(tmp_path)[0]) == [1]


def test_selectores_de_variacion_suplementarios_y_aislamientos_bidi_se_reportan(tmp_path: Path):
    _escribir(tmp_path / "AGENTS.md", f"a{chr(0xE0100)}{chr(0xE01EF)}b\nc{chr(0x2066)}{chr(0x2069)}{chr(0x061C)}d\n"
                                      f"e{chr(0x206A)}{chr(0x206F)}f\n")
    hallazgos, detector = _correr(tmp_path)
    assert _lineas(hallazgos) == [1, 2, 3]
    assert [dict(d) for d in detector.detalles.values()] == [
        {"selectores_variacion": 2}, {"direccion": 3}, {"operadores_invisibles": 2}]


def test_un_simbolo_que_no_es_emoji_junto_a_un_zwj_se_reporta_y_un_emoji_de_texto_no(tmp_path: Path):
    flecha_caja = chr(0x2502)  # U+2502, dibujo de cajas: es un símbolo pero no un emoji
    _escribir(tmp_path / "AGENTS.md", f"{flecha_caja}{ZWJ}{flecha_caja}\n")
    assert _lineas(_correr(tmp_path)[0]) == [1]
    _escribir(tmp_path / "AGENTS.md", f"importante {chr(0x203C)}{VS16} y {chr(0x2139)}{VS16}\n")
    assert _correr(tmp_path)[0] == []


def test_pasado_el_tope_los_legitimos_tambien_se_cuentan(tmp_path: Path):
    corazon = chr(0x2764) + VS16
    _escribir(tmp_path / "AGENTS.md", corazon * 40 + "\n")  # 40 selectores "legítimos" en una línea: sospechoso
    hallazgos, detector = _correr(tmp_path)
    assert _lineas(hallazgos) == [1]
    assert dict(next(iter(detector.detalles.values())))["selectores_variacion"] == 40 - 24


def test_un_bom_al_inicio_de_una_linea_posterior_si_cuenta(tmp_path: Path):
    _escribir(tmp_path / "AGENTS.md", f"uno\n{BOM}dos\n")
    assert _lineas(_correr(tmp_path)[0]) == [2]


def test_un_enlace_con_nombre_de_archivo_de_instrucciones_se_informa(tmp_path: Path):
    destino = _escribir(tmp_path / "fuera" / "AGENTS.md", f"x{ZWSP}\n")
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    try:
        os.symlink(destino, proyecto / "AGENTS.md")
    except (OSError, NotImplementedError):
        pytest.skip("el entorno no permite crear enlaces simbólicos")
    hallazgos, detector = _correr(proyecto)
    assert hallazgos == [] and _motivos(detector) == ["no_es_archivo_regular"]  # no parece limpio


def test_una_carpeta_enlazada_con_nombre_de_instrucciones_se_informa(tmp_path: Path):
    destino = tmp_path / "fuera"
    destino.mkdir()
    proyecto = tmp_path / "proyecto"
    (proyecto / ".github").mkdir(parents=True)
    try:
        if os.name == "nt":
            import _winapi

            _winapi.CreateJunction(str(destino), str(proyecto / ".github" / "AGENTS.md"))
        else:
            os.symlink(destino, proyecto / ".github" / "AGENTS.md", target_is_directory=True)
    except (OSError, NotImplementedError, AttributeError):
        pytest.skip("el entorno no permite crear enlaces de carpeta")
    hallazgos, detector = _correr(proyecto)
    assert hallazgos == [] and _motivos(detector) == ["no_es_archivo_regular"]
