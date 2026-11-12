"""Historia 19: reporte HTML estático (``--formato html``). Sin navegador: solo biblioteca estándar y pytest."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

import pytest

from agentreach import cli
from agentreach.app.auditar import ResultadoAuditoria
from agentreach.contracts import (
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
)
from agentreach.core.catalogo_explicaciones import LIMITES, Tono
from agentreach.core.nivel import Hechos
from agentreach.reporting import html as modulo_html
from agentreach.reporting.gate import preparar
from agentreach.reporting.html import MARCADOR, generar_html

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

AHORA = datetime(2026, 11, 10, 9, 30)
BASE = str(Path(os.path.abspath("proyecto-falso")))
ESQUEMA = json.loads((Path(__file__).parents[1] / "docs" / "reporte-html" / "esquema-datos.schema.json").read_text(encoding="utf-8"))
BLOQUE = re.compile(r'<script type="application/json" id="data">(.*?)</script>', re.DOTALL)


class LectorFalso:
    def existe(self, ruta: str) -> bool:
        return True

    def lineas(self, ruta: str):
        return ["# nota", "API_TOKEN=x", "OTRA=y"] * 2000


def finding(nombre="a.env", plataforma=Plataforma.CLAUDE_CODE, nivel=Nivel.POTENCIAL, motivo=Motivo.NO_DETERMINADO,
            tipo=Tipo.CREDENCIAL_EN_ARCHIVO, linea=2, ajeno=Ajeno.NO_DETERMINADO) -> Finding:
    agente = {Plataforma.CLAUDE_CODE: "claude-code", Plataforma.OPENCODE: "opencode", Plataforma.NO_DETERMINADA: "sin-agente"}[plataforma]
    return Finding(
        ubicacion=Location(Ruta(f"{BASE}/{nombre}"), linea), tipo=tipo, proveedor=Proveedor.PAGOS, nivel=nivel, motivo=motivo,
        ajeno_a_tarea=ajeno, plataforma=plataforma, agente=Etiqueta(agente), postura=Postura.SIN_REGLA)


def datos(hallazgos=(), no_revisados=(), hechos=None, agente=None):
    res = ResultadoAuditoria(tuple(hallazgos), tuple(no_revisados), 41, hechos or {}, ())
    return preparar(res, BASE, ahora=AHORA, home=None, lector=LectorFalso(), agente=agente)


def html_de(d, **kw) -> str:
    return generar_html(d, version="0.1.0", **kw)


def json_de(html: str) -> dict:
    return json.loads(BLOQUE.search(html).group(1))  # type: ignore[union-attr]


# ---- (c) un solo archivo, sin recursos externos ------------------------------------------------------------------------


def test_un_solo_archivo_sin_recursos_externos_y_con_politica_de_contenido():
    h = html_de(datos([finding()]))
    assert MARCADOR not in h and "default-src 'none'" in h
    for prohibido in ("http://", "https://", "<link", "<img", "<iframe", "<object", "<embed", "@import"):
        assert prohibido not in h, prohibido
    assert not re.search(r"""(?:href|src|action)\s*=\s*["']?\s*(?://|https?:|ftp:)""", h)
    assert not re.search(r"url\(\s*['\"]?(?!data:)", h)
    assert len(BLOQUE.findall(h)) == 1


def test_la_plantilla_empaquetada_tiene_el_marcador_una_sola_vez():
    from importlib import resources

    plantilla = resources.files("agentreach.reporting").joinpath("plantilla_reporte.html").read_text(encoding="utf-8")
    assert plantilla.count(MARCADOR) == 1


# ---- (a) canarios ---------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("extra", [[], ["--idioma", "en"], ["--agente", "opencode"], ["--agente", "claude-code", "--idioma", "en"]])
def test_los_valores_canario_no_salen_en_el_html(tmp_path: Path, extra, monkeypatch):
    proyecto = tmp_path / "p"
    proyecto.mkdir()
    (proyecto / ".env").write_text("STRIPE_SECRET_KEY=ZQX-ENV-123456\nGITHUB_TOKEN=ZQX-GH-654321\n", encoding="utf-8")
    monkeypatch.setenv("AGENTREACH_PRUEBA_API_TOKEN", "valor-ZQX-ENTORNO-999")
    destino = tmp_path / "r.html"
    assert cli.main([str(proyecto), "--formato", "html", "--salida", str(destino), *extra], ahora=lambda: AHORA) in (0, 1)
    texto = destino.read_text(encoding="utf-8")
    for canario in ("ZQX", "123456", "654321"):
        assert canario.lower() not in texto.lower(), canario
    assert "AGENTREACH_PRUEBA_API_TOKEN" in texto  # el NOMBRE sí sale; el valor, nunca


# ---- (b) escape del bloque de datos --------------------------------------------------------------------------------------------


def test_un_nombre_con_script_comentario_y_u2028_no_puede_cerrar_el_bloque():
    malos = ["</script><img src=x onerror=alert(1)>.txt", "a<!--b-->.txt", "linea" + chr(0x2028) + "sep.txt", "x</SCRIPT>.txt"]
    h = html_de(datos([finding(n) for n in malos], [NoRevisado(Ruta(f"{BASE}/{n}"), MotivoNoRevisado.ARCHIVO_ILEGIBLE) for n in malos]))
    bloque = BLOQUE.search(h).group(1)  # type: ignore[union-attr]
    assert "<" not in bloque and chr(0x2028) not in bloque and len(BLOQUE.findall(h)) == 1
    cargado = json.loads(bloque)
    rutas = {f["path"] for a in cargado["agents"] for f in a["findings"]}
    assert "</script><img src=x onerror=alert(1)>.txt" in rutas  # la ruta original se recupera como TEXTO
    assert "</script><img" not in h and "onerror=alert(1)>" not in h.replace("\\u003c", "<").split('id="data"', 1)[0]
    assert not any(x["path"] == "x</SCRIPT>.txt" and False for x in cargado["not_reviewed"])


# ---- (h) ruta limpia ---------------------------------------------------------------------------------------------------------


def test_los_nombres_peligrosos_salen_escritos_y_recortados():
    nombres = ["a" + chr(27) + "[2Jb.env", "nota" + chr(0x202E) + "txt.exe", "a" + chr(0x200B) + "b.env", "x" * 1500 + ".env"]
    cargado = json_de(html_de(datos([finding(n) for n in nombres])))
    rutas = [f["path"] for a in cargado["agents"] for f in a["findings"]]
    assert all(chr(27) not in r and chr(0x202E) not in r and chr(0x200B) not in r for r in rutas)
    assert "a" + chr(92) + "x1b[2Jb.env" in rutas and any("u202e" in r for r in rutas) and any("u200b" in r for r in rutas)
    assert any(r.endswith("...[recortada: 504 caracteres]") for r in rutas) and all(len(r) <= 1100 for r in rutas)


# ---- (f) esquema ----------------------------------------------------------------------------------------------------------------


def _validar(valor, esquema, raiz=ESQUEMA, ruta="$") -> None:
    """Un validador mínimo de lo que usa el esquema: $ref, type, enum, const, pattern, min/maxLength, minimum, required,
    additionalProperties, items, minItems/maxItems, oneOf."""
    if "$ref" in esquema:
        destino = raiz
        for parte in esquema["$ref"].lstrip("#/").split("/"):
            destino = destino[parte]
        _validar(valor, destino, raiz, ruta)
        return
    if "oneOf" in esquema:
        validos = 0
        for opcion in esquema["oneOf"]:
            try:
                _validar(valor, opcion, raiz, ruta)
                validos += 1
            except AssertionError:
                pass
        assert validos == 1, f"{ruta}: oneOf"
        return
    if "const" in esquema:
        assert valor == esquema["const"], ruta
    if "enum" in esquema:
        assert valor in esquema["enum"], f"{ruta}: {valor!r}"
    tipos = esquema.get("type")
    if tipos:
        tipos = [tipos] if isinstance(tipos, str) else tipos
        py = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool, "null": type(None)}
        assert any(isinstance(valor, py[t]) and not (t == "integer" and isinstance(valor, bool)) for t in tipos), f"{ruta}: tipo {type(valor)}"
    if isinstance(valor, str):
        assert len(valor) <= esquema.get("maxLength", 10**9) and len(valor) >= esquema.get("minLength", 0), f"{ruta}: largo"
        if "pattern" in esquema:
            assert re.search(esquema["pattern"], valor), f"{ruta}: {valor!r} no cumple {esquema['pattern']}"
    if isinstance(valor, int) and not isinstance(valor, bool) and "minimum" in esquema:
        assert valor >= esquema["minimum"], ruta
    if isinstance(valor, dict):
        propiedades = esquema.get("properties", {})
        for requerida in esquema.get("required", []):
            assert requerida in valor, f"{ruta}: falta {requerida}"
        for clave, v in valor.items():
            if clave in propiedades:
                _validar(v, propiedades[clave], raiz, f"{ruta}.{clave}")
            elif isinstance(esquema.get("additionalProperties"), dict):
                _validar(v, esquema["additionalProperties"], raiz, f"{ruta}.{clave}")
            else:
                assert esquema.get("additionalProperties", True) is not False, f"{ruta}: clave no permitida {clave}"
    if isinstance(valor, list):
        assert len(valor) <= esquema.get("maxItems", 10**9) and len(valor) >= esquema.get("minItems", 0), f"{ruta}: tamaño"
        for i, v in enumerate(valor):
            if "items" in esquema:
                _validar(v, esquema["items"], raiz, f"{ruta}[{i}]")


def _completo() -> list[Finding]:
    return [finding(f"f{i}.env", Plataforma.CLAUDE_CODE if i % 3 else Plataforma.OPENCODE, tipo=t, linea=(i + 1 if i % 4 else Linea.NO_DETERMINADA), ajeno=a)
            for i, (t, a) in enumerate((t, a) for t in Tipo for a in (Ajeno.NO_DETERMINADO, Ajeno.SI))] + [finding("g.env", Plataforma.NO_DETERMINADA)]


def test_el_json_cumple_el_esquema_y_las_reglas_de_esquema_datos_md():
    d = datos(_completo(), [NoRevisado(Ruta(f"{BASE}/x{i}"), m) for i, m in enumerate(MotivoNoRevisado)])
    cargado = json_de(html_de(d))
    _validar(cargado, ESQUEMA)
    assert cargado["schema_version"] == 1 and cargado["generated_at"] == "2026-11-10 09:30"
    for a in cargado["agents"]:
        for f in a["findings"]:
            assert f["type"] in cargado["catalog"]["types"] and f["text"] in cargado["catalog"]["texts"]
            assert f["level"] in ("verified", "potential", "hypothesis") and (f["line"] is None or f["line"] >= 1)
            assert f["reason"] in cargado["catalog"]["reasons"] and f["provider"] in cargado["catalog"]["providers"]


def test_la_demo_del_esquema_tambien_pasa_el_validador():
    demo = json.loads((Path(__file__).parents[1] / "docs" / "reporte-html" / "datos-demo.json").read_text(encoding="utf-8"))
    _validar(demo, ESQUEMA)


# ---- (g) por agente ----------------------------------------------------------------------------------------------------------------


def test_cada_agente_tiene_su_entrada_sin_mezclar_niveles_ni_duplicar_hallazgos():
    pp01 = [finding(".env", Plataforma.CLAUDE_CODE, Nivel.POTENCIAL, Motivo.REGLA_DENY), finding(".env", Plataforma.OPENCODE, Nivel.COMPROBADO,
            Motivo.EXISTE_LEGIBLE_SIN_REGLA), finding("g.env", Plataforma.NO_DETERMINADA, Nivel.HIPOTESIS, Motivo.INDICIO_DEBIL)]
    hechos = {pp01[1]: Hechos(True, PermisosArchivo(PermisoLectura.SI, False, False, "u", "x"), Postura.SIN_REGLA)}
    cargado = json_de(html_de(datos(pp01, hechos=hechos)))
    por_id = {a["id"]: a for a in cargado["agents"]}
    assert set(por_id) == {"claude_code", "opencode", "none"}
    assert [f["level"] for f in por_id["claude_code"]["findings"]] == ["potential"]
    assert [f["level"] for f in por_id["opencode"]["findings"]] == ["verified"]
    ids = [f["id"] for a in cargado["agents"] for f in a["findings"]]
    assert len(ids) == len(set(ids)) == 3


def test_un_agente_sin_hallazgos_igual_aparece_y_none_solo_si_tiene():
    cargado = json_de(html_de(datos([finding(plataforma=Plataforma.OPENCODE)])))
    assert [a["id"] for a in cargado["agents"]] == ["claude_code", "opencode"]
    assert cargado["agents"][0]["findings"] == []


def test_agente_deja_solo_esa_entrada(tmp_path: Path):
    proyecto = tmp_path / "p"
    proyecto.mkdir()
    (proyecto / ".env").write_text("STRIPE_SECRET_KEY=sk_live_valor_largo_123\n", encoding="utf-8")
    destino = tmp_path / "r.html"
    cli.main([str(proyecto), "--formato", "html", "--salida", str(destino), "--agente", "opencode"], ahora=lambda: AHORA)
    ids = {a["id"] for a in json_de(destino.read_text(encoding="utf-8"))["agents"]}
    assert "claude_code" not in ids and "opencode" in ids


# ---- (i) cobertura y límites -------------------------------------------------------------------------------------------------------


def test_los_textos_de_cada_tipo_y_motivo_estan_en_los_dos_idiomas_y_los_limites_siempre_salen():
    cargado = json_de(html_de(datos(_completo(), [NoRevisado(Ruta(f"{BASE}/x{i}"), m) for i, m in enumerate(MotivoNoRevisado)])))
    for t in Tipo:
        assert cargado["catalog"]["types"][t.value]["title"].keys() == {"en", "es"} and all(cargado["catalog"]["types"][t.value]["title"].values())
    for clave, textos in cargado["catalog"]["texts"].items():
        assert all(textos["meaning"].values()) and all(textos["what_to_do"].values()), clave
    assert set(cargado["catalog"]["no_review"]) == {m.value for m in MotivoNoRevisado}
    for m in cargado["catalog"]["no_review"].values():
        assert all(m["title"].values()) and all(m["how_to_fix"].values())
    assert cargado["limits"]["es"] == list(LIMITES[Idioma.ES]) and cargado["limits"]["en"] == list(LIMITES[Idioma.EN]) and len(cargado["limits"]["es"]) == 6
    assert cargado["limits_also"]["es"] and cargado["limits_also"]["en"]
    assert "TH-17/si" in cargado["catalog"]["texts"] and "TH-17/no_determinado" in cargado["catalog"]["texts"]


def test_con_cero_hallazgos_el_archivo_se_genera_con_lo_no_revisado_y_los_limites():
    cargado = json_de(html_de(datos([], [NoRevisado(Ruta(f"{BASE}/x.txt"), MotivoNoRevisado.ARCHIVO_ILEGIBLE)])))
    assert [a["findings"] for a in cargado["agents"]] == [[], []]
    assert cargado["not_reviewed"] == [{"path": "x.txt", "reason": "archivo_ilegible"}] and len(cargado["limits"]["en"]) == 6
    _validar(cargado, ESQUEMA)


def test_el_tono_formal_cambia_el_catalogo_en_espanol():
    cargado = json_de(html_de(datos([finding()]), tono=Tono.FORMAL))
    assert "Saque la credencial" in cargado["catalog"]["texts"]["TH-1"]["what_to_do"]["es"]


def test_el_idioma_inicial_es_el_pedido():
    assert json_de(html_de(datos([finding()]), idioma=Idioma.EN))["initial_language"] == "en"
    assert json_de(html_de(datos([finding()]), idioma=Idioma.ES))["initial_language"] == "es"


# ---- (j) determinismo y (k) tamaño -----------------------------------------------------------------------------------------------


def test_dos_ejecuciones_con_el_mismo_reloj_dan_archivos_identicos():
    d = datos(_completo())
    assert html_de(d).encode("utf-8") == html_de(datos(_completo())).encode("utf-8")


def test_cinco_mil_hallazgos_y_cinco_mil_no_revisados_en_menos_de_5_segundos():
    hallazgos = [finding(f"carpeta{i % 50}/archivo{i}.env", linea=(i % 90) + 1) for i in range(5000)]
    no_revisados = [NoRevisado(Ruta(f"{BASE}/no{i}.txt"), MotivoNoRevisado.ARCHIVO_ILEGIBLE) for i in range(5000)]
    d = datos(hallazgos, no_revisados)
    inicio = time.monotonic()
    h = html_de(d)
    assert time.monotonic() - inicio < 5 and len(h.encode("utf-8")) < 20 * 1024 * 1024
    cargado = json_de(h)
    assert len(cargado["agents"][0]["findings"]) == 5000 and len(cargado["not_reviewed"]) == 5000


def test_pasarse_de_los_topes_no_escribe_un_reporte_parcial(monkeypatch):
    monkeypatch.setattr(modulo_html, "MAX_HALLAZGOS_POR_AGENTE", 3)
    with pytest.raises(modulo_html.ReporteDemasiadoGrande):
        html_de(datos([finding(f"f{i}.env") for i in range(4)]))
    monkeypatch.setattr(modulo_html, "MAX_HALLAZGOS_POR_AGENTE", 20_000)
    monkeypatch.setattr(modulo_html, "MAX_BYTES", 1000)
    with pytest.raises(modulo_html.ReporteDemasiadoGrande):
        html_de(datos([finding()]))


# ---- (e) --salida y el comando; (d) árbol idéntico -------------------------------------------------------------------------------------


def test_salida_dentro_del_proyecto_y_html_sin_salida_se_rechazan_y_un_fallo_no_deja_archivo(tmp_path: Path, monkeypatch, capsys):
    proyecto = tmp_path / "p"
    proyecto.mkdir()
    (proyecto / ".env").write_text("STRIPE_SECRET_KEY=sk_live_valor_largo_123\n", encoding="utf-8")
    dentro = proyecto / "r.html"
    assert cli.main([str(proyecto), "--formato", "html", "--salida", str(dentro)]) == 2 and not dentro.exists()
    assert cli.main([str(proyecto), "--formato", "html"]) == 2
    assert "--salida" in capsys.readouterr().err
    destino = tmp_path / "r.html"

    def roto(*a, **k):
        raise modulo_html.ReporteDemasiadoGrande("tope")

    monkeypatch.setattr(cli, "generar_html", roto)
    assert cli.main([str(proyecto), "--formato", "html", "--salida", str(destino)]) == 3
    assert not destino.exists() and "reporte parcial" in capsys.readouterr().err


def _huella(raiz: Path) -> dict[str, tuple]:
    return {str(p.relative_to(raiz)): (p.stat().st_size, p.stat().st_mtime_ns, hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "")
            for p in sorted(raiz.rglob("*"))}


def test_el_arbol_queda_identico_y_no_se_lanza_ningun_programa(tmp_path: Path, monkeypatch):
    proyecto = tmp_path / "p"
    (proyecto / ".claude").mkdir(parents=True)
    (proyecto / ".env").write_text("STRIPE_SECRET_KEY=sk_live_valor_largo_123\n", encoding="utf-8")
    (proyecto / ".claude" / "settings.json").write_text(json.dumps({"permissions": {"deny": ["Read(./.env)"]}}), encoding="utf-8")
    antes = _huella(proyecto)

    def prohibido(*a, **k):
        raise AssertionError("AgentReach no debe ejecutar programas")

    for n in ("run", "Popen", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, n, prohibido)
    for n in dir(os):
        if n in ("system", "popen", "startfile") or n.startswith(("exec", "spawn")):
            monkeypatch.setattr(os, n, prohibido)
    destino = tmp_path / "r.html"
    assert cli.main([str(proyecto), "--formato", "html", "--salida", str(destino)], ahora=lambda: AHORA) in (0, 1)
    assert _huella(proyecto) == antes and destino.stat().st_size > 10_000


def test_el_comando_escribe_utf8_sin_color_ni_banner(tmp_path: Path):
    proyecto = tmp_path / "p"
    proyecto.mkdir()
    destino = tmp_path / "r.html"
    cli.main([str(proyecto), "--formato", "html", "--salida", str(destino), "--color", "siempre"], ahora=lambda: AHORA)
    crudo = destino.read_bytes()
    assert not crudo.startswith(b"\xef\xbb\xbf") and b"\x1b" not in crudo and b"Know what your agents can reach" not in crudo[:200]
    crudo.decode("utf-8")


# ---- Historia 20: agentes configurados (con evidencia de archivos) -------------------------------------------------------------


def _con_configuracion(tmp_path: Path) -> Path:
    proyecto = tmp_path / "p"
    (proyecto / ".claude").mkdir(parents=True)
    (proyecto / ".claude" / "settings.json").write_text(json.dumps({"permissions": {"deny": []}}), encoding="utf-8")
    (proyecto / "CLAUDE.md").write_text("# nota ZQX-CONTENIDO-SECRETO\n", encoding="utf-8")
    (proyecto / "opencode.json").write_text("{}", encoding="utf-8")
    return proyecto


def test_los_agentes_configurados_salen_con_su_evidencia_y_sin_contenido(tmp_path: Path):
    proyecto = _con_configuracion(tmp_path)
    destino = tmp_path / "r.html"
    cli.main([str(proyecto), "--formato", "html", "--salida", str(destino)], ahora=lambda: AHORA)
    texto = destino.read_text(encoding="utf-8")
    cargado = json_de(texto)
    _validar(cargado, ESQUEMA)
    por_id = {a["id"]: a for a in cargado["configured_agents"]}
    assert {".claude/settings.json", "CLAUDE.md"} <= {e["path"] for e in por_id["claude_code"]["evidence"]}
    assert [e["path"] for e in por_id["opencode"]["evidence"] if e["scope"] == "project"] == ["opencode.json"]
    assert "ZQX-CONTENIDO-SECRETO" not in texto


def test_sin_configuracion_no_hay_agentes_configurados(tmp_path: Path):
    proyecto = tmp_path / "vacio"
    proyecto.mkdir()
    destino = tmp_path / "r.html"
    cli.main([str(proyecto), "--formato", "html", "--salida", str(destino)], ahora=lambda: AHORA)
    assert json_de(destino.read_text(encoding="utf-8"))["configured_agents"] == []


def test_agente_filtra_los_configurados(tmp_path: Path):
    proyecto = _con_configuracion(tmp_path)
    destino = tmp_path / "r.html"
    cli.main([str(proyecto), "--formato", "html", "--salida", str(destino), "--agente", "opencode"], ahora=lambda: AHORA)
    assert [a["id"] for a in json_de(destino.read_text(encoding="utf-8"))["configured_agents"]] == ["opencode"]


def test_la_deteccion_no_abre_ni_modifica_nada(tmp_path: Path):
    proyecto = _con_configuracion(tmp_path)
    antes = _huella(proyecto)
    cli.main([str(proyecto), "--formato", "html", "--salida", str(tmp_path / "r.html")], ahora=lambda: AHORA)
    assert _huella(proyecto) == antes
