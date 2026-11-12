"""Historia 13: reporte completo (contenido), autocomprobación, idiomas, detalle y códigos de salida."""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path

import pytest

from agentreach import cli
from agentreach.adapters.base import Regla, ResultadoAdaptador
from agentreach.app.auditar import ResultadoAuditoria
from agentreach.contracts import (
    CATALOGO_EXPLICACIONES,
    Ajeno,
    Etiqueta,
    Finding,
    Idioma,
    Linea,
    Location,
    Motivo,
    MotivoNoRevisado,
    Nivel,
    NoRevisado,
    PermisoLectura,
    PermisosArchivo,
    Plataforma,
    Postura,
    Proveedor,
    Ruta,
    Tipo,
    texto_de_motivo,
)
from agentreach.core.autocomprobacion import RazonCorreccion, autocomprobar
from agentreach.core.catalogo_explicaciones import (
    AJENO,
    COMO_RESOLVER,
    LIMITES,
    LIMITES_TAMBIEN,
    NIVEL,
    POSTURA,
    PROVEEDOR,
    TITULO_MOTIVO,
    TITULO_TIPO,
    que_significa,
)
from agentreach.core.nivel import Hechos
from agentreach.reporting.gate import LectorSeguro, preparar, ruta_visible
from agentreach.reporting.texto import generar

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

AHORA = datetime(2026, 11, 9, 16, 40)
BASE = str(Path(os.path.abspath("proyecto-falso")))


class LectorFalso:
    def __init__(self, existe=True, lineas: list[str] | None = None) -> None:
        self._existe, self._lineas = existe, lineas if lineas is not None else ["# nota", "API_TOKEN=x", "OTRA=y"] * 40

    def existe(self, ruta: str) -> bool:
        return self._existe

    def lineas(self, ruta: str):
        return self._lineas


def finding(tipo=Tipo.CREDENCIAL_EN_ARCHIVO, nivel=Nivel.POTENCIAL, motivo=Motivo.NO_DETERMINADO, nombre="a.env", linea=2,
            **extra) -> Finding:
    datos = {
        "ubicacion": Location(Ruta(f"{BASE}/{nombre}"), linea), "tipo": tipo, "proveedor": Proveedor.PAGOS,
        "nivel": nivel, "motivo": motivo, "ajeno_a_tarea": Ajeno.NO_DETERMINADO, "plataforma": Plataforma.CLAUDE_CODE,
        "agente": Etiqueta("claude-code"), "postura": Postura.SIN_REGLA,
    }
    datos.update(extra)
    return Finding(**datos)


def bueno() -> tuple[Finding, Hechos]:
    h = Hechos(True, PermisosArchivo(PermisoLectura.SI, False, False, "u", "x"), Postura.SIN_REGLA)
    return finding(nivel=Nivel.COMPROBADO, motivo=Motivo.EXISTE_LEGIBLE_SIN_REGLA), h


def resultado(hallazgos=(), no_revisados=(), hechos=None, contextos=()) -> ResultadoAuditoria:
    return ResultadoAuditoria(tuple(hallazgos), tuple(no_revisados), 41, hechos or {}, tuple(contextos))


def texto(res: ResultadoAuditoria, idioma=Idioma.ES, detalle=False, lector=None, estricto=False, ancho=80) -> str:
    datos = preparar(res, BASE, ahora=AHORA, estricto=estricto, home=None, lector=lector or LectorFalso())
    return generar(datos, idioma, detalle=detalle, ancho=ancho)


def plano(texto: str) -> str:
    """El texto con los saltos de línea del ajuste convertidos en un espacio (para buscar frases)."""
    return re.sub(r"\s+", " ", texto)


def todos_los_motivos() -> list[NoRevisado]:
    return [NoRevisado(Ruta(f"{BASE}/x{i}.txt"), m) for i, m in enumerate(MotivoNoRevisado)]


# ---- (a) cobertura de los catálogos --------------------------------------------------------------------------------------


def test_cada_tipo_motivo_proveedor_postura_nivel_y_ajeno_tiene_sus_textos_en_los_dos_idiomas():
    for idioma in Idioma:
        for tipo in Tipo:
            assert TITULO_TIPO[tipo][idioma].strip()
            assert all(t.strip() for t in CATALOGO_EXPLICACIONES[tipo][idioma])
        for motivo in MotivoNoRevisado:
            assert TITULO_MOTIVO[motivo][idioma].strip() and COMO_RESOLVER[motivo][idioma].strip()
        for m in Motivo:
            assert texto_de_motivo(m, idioma).strip()
        assert {p for p in Proveedor} == set(PROVEEDOR) and all(PROVEEDOR[p][idioma] or p is Proveedor.NO_APLICA for p in Proveedor)
        assert all(POSTURA[p][idioma] for p in Postura) and all(NIVEL[n][idioma] for n in Nivel)
        assert all(AJENO[a][idioma] for a in Ajeno)
    assert len(Tipo) == 20 and len(MotivoNoRevisado) == 12


# ---- (b) determinismo ---------------------------------------------------------------------------------------------------


def test_el_mismo_hallazgo_con_el_mismo_reloj_da_siempre_el_mismo_texto():
    f, h = bueno()
    assert texto(resultado([f], hechos={f: h})) == texto(resultado([f], hechos={f: h}))


def test_dos_ejecuciones_del_comando_con_el_mismo_reloj_dan_el_mismo_texto(tmp_path: Path, capsys):
    (tmp_path / ".env").write_text("STRIPE_SECRET_KEY=sk_live_algo_largo_123\n", encoding="utf-8")
    cli.main([str(tmp_path)], ahora=lambda: AHORA)
    uno = capsys.readouterr().out
    cli.main([str(tmp_path)], ahora=lambda: AHORA)
    assert uno == capsys.readouterr().out and "2026-11-09 16:40" in uno


# ---- (c) nombres con caracteres de control ------------------------------------------------------------------------------


def test_un_nombre_con_caracteres_peligrosos_sale_escrito_con_la_nota_y_nunca_borrado():
    f = finding(nombre="nota\u202etxt.exe.env")
    salida = texto(resultado([f]))
    assert "nota\\u202etxt.exe.env" in salida and "\u202e" not in salida
    assert "se muestran escritos como \\uXXXX" in plano(salida)
    assert ruta_visible(f"{BASE}/a\x1b[2Jb", BASE, None)[0] == "a\\x1b[2Jb"
    assert ruta_visible(f"{BASE}/a\nb", BASE, None) == ("a\\nb", True)
    assert ruta_visible(f"{BASE}/a\U000e0041b", BASE, None)[0] == "a\\U000e0041b"
    assert ruta_visible(f"{BASE}/" + "x" * 1500, BASE, None)[0].endswith("...[recortada: 500 caracteres]")


def test_en_la_salida_no_queda_ningun_escape_ni_salto_inventado():
    f = finding(nombre="a\x1b]0;titulo\x07\nlinea falsa\r.env")
    salida = texto(resultado([f]))
    assert "\x1b" not in salida and "\x07" not in salida and "\r" not in salida
    assert not any(linea.startswith("linea falsa") for linea in salida.splitlines())


# ---- (d) comandos peligrosos --------------------------------------------------------------------------------------------

PROHIBIDOS = ("gh auth status", "dotnet user-secrets list", "az account get-access-token", "aws configure list")


def test_ningun_texto_sugiere_un_comando_que_imprime_secretos():
    textos = [t for por in CATALOGO_EXPLICACIONES.values() for par in por.values() for t in par]
    textos += [t for por in COMO_RESOLVER.values() for t in por.values()]
    for idioma in Idioma:
        textos.append(texto(resultado(no_revisados=todos_los_motivos()), idioma, detalle=True))
    for t in textos:
        assert not any(p in t for p in PROHIBIDOS)


# ---- (e) --salida -------------------------------------------------------------------------------------------------------


def test_salida_dentro_del_proyecto_se_rechaza_y_fuera_se_escribe_en_utf8(tmp_path: Path, capsys):
    proyecto = tmp_path / "p"
    proyecto.mkdir()
    (proyecto / ".env").write_text("STRIPE_SECRET_KEY=sk_live_algo_largo_123\n", encoding="utf-8")
    dentro = proyecto / "reporte.txt"
    assert cli.main([str(proyecto), "--salida", str(dentro)]) == 2
    assert not dentro.exists() and "--salida" in capsys.readouterr().err
    fuera = tmp_path / "reporte.txt"
    codigo = cli.main([str(proyecto), "--salida", str(fuera)], ahora=lambda: AHORA)
    assert codigo in (0, 1) and capsys.readouterr().out == ""
    datos = fuera.read_bytes()
    assert not datos.startswith(b"\xef\xbb\xbf") and "revisión".encode() in datos and b"\x1b" not in datos


# ---- (f) sin hallazgos --------------------------------------------------------------------------------------------------


def test_un_proyecto_sin_hallazgos_lista_igualmente_lo_revisado_y_lo_no_revisado(tmp_path: Path, capsys, monkeypatch):
    # en Windows toda auditoría real trae TH-10 (sin sandbox): se prueba con un resultado vacío
    monkeypatch.setattr(cli, "auditar", lambda carpeta, config, **kw: ResultadoAuditoria((), (), 3))
    assert cli.main([str(tmp_path), "--idioma", "es"], ahora=lambda: AHORA) == 0
    salida = capsys.readouterr().out
    assert "SIN HALLAZGOS" in salida and "no significa que el agente no pueda hacer daño" in plano(salida)
    assert "archivos mirados" in salida and "QUÉ NO PUDO REVISAR AGENTREACH" in salida
    assert "(nada en esta carpeta)" in salida and LIMITES[Idioma.ES][0][:40] in plano(salida)


# ---- (g) GT-02 -----------------------------------------------------------------------------------------------------------


def test_el_historial_de_git_sale_en_no_se_pudo_revisar_y_nunca_con_valores(tmp_path: Path, capsys):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text('[remote "o"]\n\turl = https://ana:CANARIO-GIT-9f2k8x@host.invalid/x.git\n', encoding="utf-8")
    for detalle in ([], ["--detalle"]):
        cli.main([str(tmp_path), *detalle], ahora=lambda: AHORA)
        salida = capsys.readouterr().out
        assert "Historial de git (llega en una fase futura)" in salida
        assert "CANARIO" not in salida and "9f2k8x" not in salida
    assert "historial_git_fase2" in salida  # con --detalle sale el identificador


# ---- (h) sección B ------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("idioma", list(Idioma))
def test_la_seccion_de_limites_sale_siempre_con_los_seis_limites_y_lo_que_tampoco_se_revisa(idioma):
    salida = texto(resultado(), idioma)
    assert len(LIMITES[idioma]) == 6
    for limite in LIMITES[idioma]:
        assert limite in salida.replace("\n    ", " ").replace("\n   ", " ") or limite[:40] in salida
    assert LIMITES_TAMBIEN[idioma][:30] in salida


# ---- (i) la ayuda -------------------------------------------------------------------------------------------------------


def test_la_ayuda_no_ofrece_ejecutar_programas():
    ayuda = cli.construir_parser().format_help()
    assert "permitir-git" not in ayuda and "ejecutar" not in ayuda.replace("ejecuta con", "").lower().replace("ejecutará", "")
    for opcion in ("--detalle", "--idioma", "--color", "--ascii", "--salida", "--estricto", "--ancho", "--tarea"):
        assert opcion in ayuda


# ---- (j) autocomprobación -----------------------------------------------------------------------------------------------


def _razones(auto) -> set[RazonCorreccion]:
    return {c.razon for c in auto.correcciones}


def test_un_comprobado_sin_un_hecho_baja_en_lugar_de_imprimirse_como_comprobado():
    f, h = bueno()
    malos = {
        "sin permiso": Hechos(True, PermisosArchivo(PermisoLectura.NO, False, False, "u", "x"), Postura.SIN_REGLA),
        "con deny": Hechos(True, h.permiso, Postura.DENY),
        "sin archivo": Hechos(False, h.permiso, Postura.SIN_REGLA),
    }
    for nombre, hechos in malos.items():
        auto = autocomprobar([f], {f: hechos}, LectorFalso(existe=True))
        assert auto.hallazgos[0].nivel is Nivel.POTENCIAL and RazonCorreccion.INVARIANTE_VIOLADA in _razones(auto), nombre
    sin_hechos = autocomprobar([f], {}, LectorFalso())
    assert sin_hechos.hallazgos[0].nivel is Nivel.POTENCIAL


def test_un_potencial_sin_motivo_y_un_comprobado_sin_fuente_se_corrigen():
    sin_motivo = finding(nivel=Nivel.POTENCIAL, motivo=Motivo.EXISTE_LEGIBLE_SIN_REGLA)
    por_nombre = finding(Tipo.SECRETO_DE_ALTO_PODER, nivel=Nivel.COMPROBADO, motivo=Motivo.EXISTE_LEGIBLE_SIN_REGLA)
    auto = autocomprobar([sin_motivo, por_nombre], {}, LectorFalso())
    assert all(h.nivel is Nivel.POTENCIAL for h in auto.hallazgos)
    assert all(h.motivo in (Motivo.NO_DETERMINADO,) for h in auto.hallazgos)
    assert len(auto.correcciones) == 2


def test_la_salida_de_un_comprobado_falso_no_dice_comprobado_y_el_codigo_es_0():
    f, _ = bueno()
    datos = preparar(resultado([f]), BASE, ahora=AHORA, lector=LectorFalso())
    assert datos.codigo_de_salida == 0 and all(h.nivel is not Nivel.COMPROBADO for h in datos.hallazgos)
    salida = generar(datos, Idioma.ES)
    assert "■ COMPROBADO (" not in salida and "Se bajó de comprobado a potencial" in salida  # Historia 32: dice cuál y a qué nivel


def test_un_archivo_borrado_baja_de_nivel_y_lo_dice():
    f, h = bueno()
    auto = autocomprobar([f], {f: h}, LectorFalso(existe=False))
    assert auto.hallazgos[0].nivel is Nivel.POTENCIAL and not isinstance(auto.hallazgos[0].ubicacion.linea, int)
    assert RazonCorreccion.ARCHIVO_YA_NO_EXISTE in _razones(auto)
    potencial = finding()
    assert autocomprobar([potencial], {}, LectorFalso(existe=False)).hallazgos[0].nivel is Nivel.HIPOTESIS


def test_una_linea_que_no_contiene_la_clave_sale_como_linea_no_determinada():
    f, h = bueno()
    ok = autocomprobar([f], {f: h}, LectorFalso(lineas=["x", "API_TOKEN=lo-que-sea"]))
    assert ok.hallazgos[0].ubicacion.linea == 2 and not ok.correcciones
    for lineas in (["x", "una linea sin nada"], ["x"], ["x", "# API_TOKEN=comentada"], None):
        auto = autocomprobar([f], {f: h}, LectorFalso(lineas=lineas) if lineas is not None else _LectorQueNoPuede())
        assert auto.hallazgos[0].ubicacion.linea is Linea.NO_DETERMINADA, lineas
        assert auto.hallazgos[0].nivel is Nivel.COMPROBADO  # solo la línea se retira
        assert _razones(auto) == {RazonCorreccion.LINEA_NO_CONFIRMADA}


class _LectorQueNoPuede(LectorFalso):
    def lineas(self, ruta: str):
        return None


def test_un_archivo_con_nombre_de_caracteres_raros_se_reabre_por_la_ruta_real(tmp_path: Path):
    nombre = "clave\u202e.env"
    try:
        (tmp_path / nombre).write_text("API_TOKEN=valor\n", encoding="utf-8")
    except OSError:
        pytest.skip("este sistema no permite ese nombre de archivo")
    f = finding(nombre="x.env", linea=1, ubicacion=Location(Ruta(str(tmp_path / nombre)), 1))
    assert f.ubicacion.ruta != f.ubicacion.ruta_real  # la limpia perdió el carácter; la real no
    auto = autocomprobar([f], {}, LectorSeguro())
    assert auto.hallazgos[0].ubicacion.linea == 1  # se reabrió y la línea se confirmó
    assert RazonCorreccion.ARCHIVO_YA_NO_EXISTE not in _razones(auto)


# ---- (k) cómo resolverlo ------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("idioma", list(Idioma))
def test_cada_motivo_tiene_como_resolverlo_y_la_ubicacion_sensible_sugiere_el_flag_correcto(idioma):
    salida = texto(resultado(no_revisados=todos_los_motivos()), idioma)
    for motivo in MotivoNoRevisado:
        assert COMO_RESOLVER[motivo][idioma][:30] in salida
    sensible = texto(resultado(no_revisados=[NoRevisado(Ruta("~/.ssh"), MotivoNoRevisado.UBICACION_SENSIBLE_SIN_ACTIVAR)]), idioma)
    assert "--incluir-ubicaciones-sensibles" in sensible
    assert "SIN HALLAZGOS" in sensible or "NO FINDINGS" in sensible  # no hay hallazgos...
    assert re.search(r"(?m)^\s*(○|\[-\]) ", sensible)  # ...y la ubicación sensible va como no revisada, nunca como revisada
    assert "revisado" not in TITULO_MOTIVO[MotivoNoRevisado.UBICACION_SENSIBLE_SIN_ACTIVAR][Idioma.ES].lower().replace("sin", "")


# ---- (l) un hallazgo visto no es un "no revisado" -----------------------------------------------------------------------


def test_un_archivo_legible_da_hallazgo_o_nada_pero_no_un_no_revisado(tmp_path: Path):
    from agentreach.app.auditar import auditar
    from agentreach.config import Configuracion

    (tmp_path / ".env").write_text("STRIPE_SECRET_KEY=sk_live_algo_largo_123\n", encoding="utf-8")
    (tmp_path / "notas.txt").write_text("nada de interes\n", encoding="utf-8")
    r = auditar(str(tmp_path), Configuracion())
    assert not [n for n in r.no_revisados if n.ruta.endswith((".env", "notas.txt"))]
    assert any(h.tipo is Tipo.CREDENCIAL_EN_ARCHIVO for h in r.hallazgos)


# ---- (m) hipótesis ------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("idioma, rotulo", [(Idioma.ES, "Sugerencias, no accesos comprobados"),
                                            (Idioma.EN, "Suggestions, not verified access")])
def test_las_hipotesis_llevan_su_rotulo(idioma, rotulo):
    f = finding(Tipo.CONTEXTO_SOSPECHOSO, Nivel.HIPOTESIS, Motivo.INDICIO_DEBIL, "AGENTS.md")
    assert rotulo in texto(resultado([f]), idioma)


# ---- (n) códigos solo con --detalle -------------------------------------------------------------------------------------


def _con_de_todo() -> ResultadoAuditoria:
    f = finding(Tipo.CONTEXTO_SOSPECHOSO, Nivel.HIPOTESIS, Motivo.INDICIO_DEBIL, "AGENTS.md")
    g = finding(motivo=Motivo.REGLA_DENY)
    return resultado([f, g], todos_los_motivos())


@pytest.mark.parametrize("idioma", list(Idioma))
def test_sin_detalle_no_hay_codigos_ni_identificadores_y_con_detalle_si(idioma):
    res = _con_de_todo()
    compacto, detallado = texto(res, idioma), texto(res, idioma, detalle=True)
    assert not re.search(r"TH-\d", compacto)
    assert not any(m.value in compacto for m in MotivoNoRevisado)
    assert not any(m.value in compacto for m in Motivo)
    assert re.search(r"TH-\d", detallado) and all(m.value in detallado for m in MotivoNoRevisado)
    assert Motivo.REGLA_DENY.value in detallado


# ---- (o) idioma ---------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("regional, esperado", [("es", Idioma.ES), ("en", Idioma.EN), ("fr", Idioma.ES), (None, Idioma.ES)])
def test_el_idioma_sale_de_la_regional_y_cae_en_espanol(monkeypatch, regional, esperado):
    monkeypatch.delenv("AGENTREACH_IDIOMA", raising=False)
    monkeypatch.setattr(cli, "idioma_regional", lambda: regional)
    assert cli.resolver_idioma("auto") is esperado


def test_idioma_gana_a_la_variable_y_esta_a_la_regional(monkeypatch):
    monkeypatch.setattr(cli, "idioma_regional", lambda: "en")
    monkeypatch.setenv("AGENTREACH_IDIOMA", "es")
    assert cli.resolver_idioma("auto") is Idioma.ES  # la variable gana a la regional
    assert cli.resolver_idioma("en") is Idioma.EN  # la opción gana a la variable
    monkeypatch.setenv("AGENTREACH_IDIOMA", "fr")
    assert cli.resolver_idioma("auto") is Idioma.ES  # algo que no se entiende: español


def test_el_comando_imprime_en_ingles_con_idioma_en(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr(cli, "auditar", lambda carpeta, config, **kw: ResultadoAuditoria((), (), 3))
    cli.main([str(tmp_path), "--idioma", "en"], ahora=lambda: AHORA)
    salida = capsys.readouterr().out
    assert "Review report" in salida and "NO FINDINGS" in salida and "Exit code: 0" in salida


# ---- (p) códigos de salida ----------------------------------------------------------------------------------------------


def test_codigos_de_salida(tmp_path: Path, capsys, monkeypatch):
    vacia = tmp_path / "vacia"
    vacia.mkdir()
    assert cli.main([str(vacia)]) == 0
    assert "Código de salida: 0" in capsys.readouterr().out
    f, h = bueno()
    comprobado = ResultadoAuditoria((f,), (), 1, {f: h}, ())
    monkeypatch.setattr(cli, "auditar", lambda carpeta, config, **kw: comprobado)
    monkeypatch.setattr("agentreach.reporting.gate.LectorSeguro", LectorFalso)
    assert cli.main([str(vacia)]) == 1
    assert "Código de salida: 1 (hay hallazgos comprobados)" in capsys.readouterr().out
    assert cli.main([str(tmp_path / "no-existe")]) == 2
    err = capsys.readouterr().err
    assert "error:" in err and "Traceback" not in err

    def roto(*a, **k):
        raise RuntimeError("falla forzada")

    monkeypatch.setattr(cli, "auditar", roto)
    assert cli.main([str(vacia)]) == 3
    capturado = capsys.readouterr()
    assert capturado.out == "" and "no se muestra un reporte parcial" in capturado.err and "Traceback" not in capturado.err


def test_estricto_da_1_con_entradas_no_revisadas(tmp_path: Path, capsys, monkeypatch):
    sin_comprobados = ResultadoAuditoria((), (NoRevisado(Ruta(f"{BASE}/x"), MotivoNoRevisado.ARCHIVO_ILEGIBLE),), 1)
    monkeypatch.setattr(cli, "auditar", lambda carpeta, config, **kw: sin_comprobados)
    assert cli.main([str(tmp_path)]) == 0
    capsys.readouterr()
    assert cli.main([str(tmp_path), "--estricto"]) == 1
    assert "--estricto" in capsys.readouterr().out


def test_el_atajo_y_audit_son_lo_mismo(tmp_path: Path, capsys):
    cli.main([str(tmp_path)], ahora=lambda: AHORA)
    uno = capsys.readouterr().out
    cli.main(["audit", str(tmp_path)], ahora=lambda: AHORA)
    assert uno == capsys.readouterr().out


def test_una_tuberia_cerrada_no_da_traza(tmp_path: Path, monkeypatch):
    class Cerrada:
        encoding = "utf-8"

        def write(self, texto):
            raise BrokenPipeError

        def flush(self):
            pass

    monkeypatch.setattr(sys, "stdout", Cerrada())
    assert cli.main([str(tmp_path)]) == 0


# ---- (q) los textos -----------------------------------------------------------------------------------------------------


def test_ningun_texto_usa_usted_y_las_palabras_dificiles_van_con_su_explicacion():
    for por in CATALOGO_EXPLICACIONES.values():
        for par in por.values():
            for t in par:
                assert not re.search(r"\busted\b|\bsu(s)?\s+usuario", t, re.IGNORECASE), t
    for tipo, por in CATALOGO_EXPLICACIONES.items():
        todo_es = " ".join(por[Idioma.ES])
        if re.search(r"\brot(a|ar|e)\w*", todo_es):
            assert "cambiarla por una nueva y desactivar la vieja" in todo_es, tipo
        if "gestor de secretos" in todo_es:
            assert "programa que guarda claves cifradas" in todo_es
        if "Unicode" in todo_es:
            assert "estándar" in todo_es
        if "shell" in todo_es:
            assert "línea de comandos" in todo_es
        if "hook" in todo_es:
            assert "comando que" in todo_es or "comandos que" in todo_es
        assert "mínimo privilegio" not in todo_es and not re.search(r"\bask\b|\bdeny\b", todo_es)
        todo_en = " ".join(por[Idioma.EN])
        assert not re.search(r"\bobey\b|\bvulnerable\b|\bwill run\b", todo_en) and not re.search(r"obedecerá|es vulnerable", todo_es)


def test_el_texto_de_th17_cambia_con_el_campo_ajeno():
    textos = {a: que_significa(Tipo.SECRETO_DE_ALTO_PODER, a, Idioma.ES) for a in Ajeno}
    assert "sin relación con la tarea" in textos[Ajeno.SI]
    assert "sin relación con la tarea" not in textos[Ajeno.NO] and "sin relación" not in textos[Ajeno.NO_DETERMINADO]
    assert "No se puede saber" in textos[Ajeno.NO_DETERMINADO]
    assert len(set(textos.values())) == 3


# ---- (r) reglas del agente como contexto ---------------------------------------------------------------------------------


def test_las_reglas_y_las_medidas_del_agente_salen_como_contexto_con_archivo_y_linea():
    regla = Regla("deny", "Read", Location(Ruta(f"{BASE}/.claude/settings.json"), 13), "./.env")
    contexto = ResultadoAdaptador(reglas=(regla,), limpieza_de_entorno=True)
    salida = texto(resultado([finding()], contextos=[(Plataforma.CLAUDE_CODE, contexto)]))
    assert "REGLAS DE LOS AGENTES (contexto)" in salida
    assert "lo bloquea (solo por regla) · Read · .claude/settings.json:13" in salida
    assert "quita las credenciales del entorno" in salida
    assert "./.env" not in salida  # el especificador de la regla no se muestra


# ---- con el proyecto de prueba ------------------------------------------------------------------------------------------


@pytest.fixture
def proyecto_prueba() -> Path:
    raiz = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")
    if not raiz or not (Path(raiz) / "proyecto").is_dir():
        pytest.skip("AGENTREACH_PROYECTO_PRUEBA no apunta al proyecto de prueba")
    return Path(raiz) / "proyecto"


def _agente(salida: str, nombre: str) -> str:
    """La sección de un agente: del título «AGENTE: nombre» al siguiente agente o a «qué no pudo revisar»."""
    inicio = salida.index(f"\nAGENTE: {nombre}\n-")  # el título con su subrayado (el del resumen va con sangría)
    resto = salida[inicio + 2:]  # sin el salto ni la «A» del propio título
    fin = re.search(r"(?m)^(?:AGENTE: |SIN AGENTE|QUÉ NO PUDO)", resto)
    return resto[: fin.start()] if fin else resto


def _seccion(salida: str, titulo: str) -> str:
    inicio = re.search(rf"(?m)^\S+ {titulo} \(\d+\)$", salida)
    assert inicio, titulo
    resto = salida[inicio.end():]
    fin = re.search(r"(?m)^(?:\S+ (?:COMPROBADO|POTENCIAL|HIPÓTESIS) \(\d+\)|QUÉ NO PUDO)", resto)
    return resto[: fin.start()] if fin else resto


@pytest.mark.skipif(sys.platform != "win32", reason="las sondas reales del permiso son de Windows")
def test_casos_del_oraculo_pp01_ca01_ca04_y_gt02(proyecto_prueba: Path, capsys):
    cli.main([str(proyecto_prueba), "--ancho", "100", "--idioma", "es"], ahora=lambda: AHORA)
    salida = capsys.readouterr().out
    assert "CNR0" not in salida  # ningún marcador canario
    claude, opencode = _agente(salida, "Claude Code"), _agente(salida, "opencode")  # una sección por agente, sin mezclar niveles
    potencial, comprobado = _seccion(claude, "POTENCIAL"), _seccion(opencode, "COMPROBADO")
    # PP-01: un hallazgo por agente (Claude Code: potencial por política; opencode: comprobado, el read: allow gana)
    en_potencial = re.search(r"(?ms)^\.env\n(.*?)(?=^\S)", potencial)
    assert en_potencial and "Claude Code" in en_potencial.group(1) and "Protegido por política del agente" in en_potencial.group(1)
    en_comprobado = re.search(r"(?ms)^\.env\n(.*?)(?=^\S)", comprobado)
    assert en_comprobado and "opencode" in en_comprobado.group(1) and "Claude Code" not in en_comprobado.group(1)
    # CA-01: la regla aparece con archivo y línea dentro de «reglas del agente», no como hallazgo
    assert re.search(r"lo bloquea \(solo por regla\) · Read · \.claude/settings\.json:\d+", salida)
    assert "regla en .claude/settings.json" in plano(salida)
    # CA-04: opencode permisivo sale como hallazgo potencial
    assert "Regla del agente demasiado permisiva" in _seccion(opencode, "POTENCIAL")  # es regla de opencode
    # GT-02: el historial de git va a «no se pudo revisar»
    assert "Historial de git (llega en una fase futura)" in salida


# ---- parches de la revisión ----------------------------------------------------------------------------------------


def test_el_nombre_de_una_herramienta_de_regla_se_escribe_no_se_imprime():
    regla = Regla("allow", "Read" + chr(27) + "[2J" + chr(0x202E), Location(Ruta(f"{BASE}/opencode.json"), 4), None)
    salida = texto(resultado([finding()], contextos=[(Plataforma.OPENCODE, ResultadoAdaptador(reglas=(regla,)))]))
    assert chr(27) not in salida and chr(0x202E) not in salida
    assert "Read\\x1b[2J\\u202e" in salida


def test_lo_que_el_recorrido_no_pudo_revisar_llega_al_reporte(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("agentreach.collectors.enlaces.MAX_PROFUNDIDAD", 2)
    from agentreach.app.auditar import auditar
    from agentreach.config import Configuracion

    profunda = tmp_path
    for n in range(5):  # más niveles de los que el recorrido admite (aquí, 2)
        profunda = profunda / f"n{n}"
    profunda.mkdir(parents=True)
    (profunda / "x.txt").write_text("x", encoding="utf-8")
    r = auditar(str(tmp_path), Configuracion())
    assert any(n.motivo is MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA for n in r.no_revisados)


def test_el_resumen_cuenta_lo_mismo_que_lista_y_no_confunde_dos_nombres_limpios():
    a = NoRevisado(Ruta(f"{BASE}/x.txt"), MotivoNoRevisado.ARCHIVO_ILEGIBLE)
    datos = preparar(resultado(no_revisados=[a, a]), BASE, ahora=AHORA, lector=LectorFalso())
    assert len(datos.no_revisados) == 1


def test_una_carpeta_llamada_tilde_no_se_confunde_con_la_carpeta_personal():
    assert ruta_visible(f"{BASE}/~/x.env", BASE, None)[0] == "./~/x.env"
    assert ruta_visible(f"{BASE}/a.env", BASE, None)[0] == "a.env"


@pytest.mark.parametrize("ancho", [40, 60, 80])
def test_ninguna_linea_pasa_del_ancho_salvo_una_ruta_entera(ancho):
    f = finding(nombre="mi carpeta con espacios/sub dir/mi archivo con nombre largo.env", motivo=Motivo.REGLA_DENY)
    salida = texto(resultado([f], todos_los_motivos()), detalle=True, ancho=ancho)
    for linea in salida.splitlines():
        assert len(linea) <= ancho - 1 or " " not in linea.strip() or "/" in linea or "\\" in linea, linea
    assert "mi carpeta con espacios/sub dir/mi archivo con nombre largo.env" in salida  # entera, en una línea


def test_con_ascii_no_queda_ningun_caracter_fuera_de_ascii():
    f = finding(motivo=Motivo.REGLA_DENY)
    datos = preparar(resultado([f], todos_los_motivos()), BASE, ahora=AHORA, home=None, lector=LectorFalso())
    for idioma in Idioma:
        assert generar(datos, idioma, detalle=True, ascii_=True).isascii()


def test_dos_hallazgos_sin_linea_repiten_la_explicacion_en_lugar_de_decir_linea_interrogante():
    a = finding(linea=Linea.NO_DETERMINADA)
    b = finding(linea=Linea.NO_DETERMINADA)
    salida = texto(resultado([a, b]))
    assert "línea ?" not in salida and salida.count("Qué significa:") == 2


def test_igual_que_no_se_usa_si_el_texto_cambia_con_ajeno():
    a = finding(Tipo.SECRETO_DE_ALTO_PODER, linea=1, ajeno_a_tarea=Ajeno.SI)
    b = finding(Tipo.SECRETO_DE_ALTO_PODER, linea=3, ajeno_a_tarea=Ajeno.NO)
    assert "igual que el hallazgo" not in texto(resultado([a, b]))


def test_el_orden_dentro_de_una_linea_es_numerico_th2_antes_que_th10():
    a = finding(Tipo.PLATAFORMA_SIN_SANDBOX, linea=1)
    b = finding(Tipo.CLAVE_PRIVADA_SSH, linea=1)
    salida = texto(resultado([a, b]))
    assert salida.index("Llave privada") < salida.index("Sin caja de aislamiento")


def test_los_errores_de_argumentos_salen_en_el_idioma_elegido_sin_traza(capsys, monkeypatch):
    monkeypatch.setenv("AGENTREACH_IDIOMA", "en")
    with pytest.raises(SystemExit) as salida:
        cli.main(["--ancho", "x", "carpeta"])
    assert salida.value.code == 2
    err = capsys.readouterr().err
    assert err.startswith("argument error:") and "Traceback" not in err


def test_un_error_al_leer_la_configuracion_da_3_y_no_traza(tmp_path: Path, capsys, monkeypatch):
    def rota(args):
        raise RuntimeError("falla")

    monkeypatch.setattr(cli, "_configuracion", rota)
    assert cli.main([str(tmp_path)]) == 3
    assert "no se muestra un reporte parcial" in capsys.readouterr().err


def test_salida_rechaza_enlaces_duros_y_rutas_que_pasan_por_la_carpeta(tmp_path: Path):
    p = tmp_path / "p"
    p.mkdir()
    secreto = p / "dato.txt"
    secreto.write_text("x", encoding="utf-8")
    duro = tmp_path / "duro.txt"
    try:
        os.link(secreto, duro)
    except (OSError, NotImplementedError):
        pytest.skip("este sistema no permite enlaces duros")
    assert cli._dentro(str(duro), str(p)) is True  # abrirlo con "w" truncaría un archivo del proyecto
    assert cli._dentro(str(p / "sub" / ".." / "r.txt"), str(p)) is True
    assert cli._dentro(str(tmp_path / "nuevo.txt"), str(p)) is False


def test_todos_los_textos_fijos_evitan_usted():
    from agentreach.reporting import texto as modulo

    todos = [t for por in modulo._T.values() for t in por.values()]
    todos += [t for por in COMO_RESOLVER.values() for t in por.values()]
    todos += [t for por in cli._ERROR.values() for t in por.values()]
    todos += [t for por in TITULO_MOTIVO.values() for t in por.values()]
    for t in todos:
        assert not re.search(r"\busted\b|\bindique\b|\brevíselo\b|\bejecútelo\b", t, re.IGNORECASE), t
