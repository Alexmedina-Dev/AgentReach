"""Historia 11c: si no se entiende un archivo de configuración, el nivel nunca es «comprobado». Tres casos que se escapaban:
claves repetidas en ``opencode.json``, patrones ``Read`` con ``./`` repetido o ``..``, y un ``.claude`` (u ``.opencode``) que es un archivo."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentreach.app.auditar import auditar
from agentreach.config import Configuracion
from agentreach.contracts import MotivoNoRevisado, Nivel, Plataforma, Tipo
from agentreach.infra.json_con_comentarios import JsoncNoInterpretable, parsear_jsonc

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)


def _auditar(tmp_path: Path, preparar):
    proyecto = tmp_path / "p"
    proyecto.mkdir(parents=True)
    casa = tmp_path / "casa"
    casa.mkdir()
    (proyecto / ".env").write_text("STRIPE_SECRET_KEY=sk_live_valor_largo_123\n", encoding="utf-8")
    preparar(proyecto)
    return auditar(str(proyecto), Configuracion(home=str(casa)))


def _nivel(res, plataforma: Plataforma) -> set[Nivel]:
    return {h.nivel for h in res.hallazgos if h.tipo is Tipo.CREDENCIAL_EN_ARCHIVO and h.plataforma is plataforma}


def _motivos(res) -> set[tuple[str, str]]:
    return {(n.motivo.value, Path(n.ruta).name) for n in res.no_revisados}


def _claude(regla: str):
    def preparar(p: Path):
        (p / ".claude").mkdir()
        (p / ".claude" / "settings.json").write_text(json.dumps({"permissions": {"deny": [regla]}}), encoding="utf-8")

    return preparar


# ---- patrones Read con ./ repetido o .. -----------------------------------------------------------------------------------------


@pytest.mark.parametrize("patron", ["Read(././.env)", "Read(sub/../.env)", "Read(./sub/../.env)", "Read(../.env)", "Read(a/./.env)",
                                    "Read(./././.env)", "Read(.env/..)"])
def test_un_patron_con_punto_repetido_o_dos_puntos_no_se_interpreta_y_el_nivel_no_es_comprobado(tmp_path, patron):
    res = _auditar(tmp_path, _claude(patron))
    assert Nivel.COMPROBADO not in _nivel(res, Plataforma.CLAUDE_CODE)
    assert ("configuracion_no_interpretable", "settings.json") in _motivos(res)


@pytest.mark.parametrize("patron", ["Read(./.env)", "Read(.env)", "Read(**/.env)", "Read(./sub/.env)", "Read(//c/x/.env)", "Read(~/.env)"])
def test_las_formas_documentadas_siguen_interpretandose(tmp_path, patron):
    res = _auditar(tmp_path, _claude(patron))
    assert ("configuracion_no_interpretable", "settings.json") not in _motivos(res)


def test_el_deny_bien_escrito_sigue_bajando_a_potencial_y_el_ambiguo_tambien(tmp_path):
    assert _nivel(_auditar(tmp_path / "a", _claude("Read(./.env)")), Plataforma.CLAUDE_CODE) == {Nivel.POTENCIAL}
    assert _nivel(_auditar(tmp_path / "b", _claude("Read(././.env)")), Plataforma.CLAUDE_CODE) == {Nivel.POTENCIAL}


# ---- un .claude (u .opencode) que es un archivo ----------------------------------------------------------------------------------


def test_un_claude_que_es_un_archivo_se_dice_y_el_nivel_no_es_comprobado(tmp_path):
    res = _auditar(tmp_path, lambda p: (p / ".claude").write_text("no soy una carpeta", encoding="utf-8"))
    assert Nivel.COMPROBADO not in _nivel(res, Plataforma.CLAUDE_CODE)
    assert ("configuracion_no_interpretable", ".claude") in _motivos(res)


def test_un_opencode_que_es_un_archivo_se_dice_y_el_nivel_de_opencode_no_es_comprobado(tmp_path):
    res = _auditar(tmp_path, lambda p: (p / ".opencode").write_text("no soy una carpeta", encoding="utf-8"))
    assert Nivel.COMPROBADO not in _nivel(res, Plataforma.OPENCODE)
    assert ("configuracion_no_interpretable", ".opencode") in _motivos(res)


def test_una_carpeta_que_no_existe_sigue_siendo_lo_normal(tmp_path):
    res = _auditar(tmp_path, lambda p: None)
    assert ("configuracion_no_interpretable", ".claude") not in _motivos(res)
    assert ("configuracion_no_interpretable", ".opencode") not in _motivos(res)
    assert _nivel(res, Plataforma.CLAUDE_CODE) == {Nivel.COMPROBADO}


def test_un_claude_normal_con_su_settings_no_da_aviso(tmp_path):
    res = _auditar(tmp_path, _claude("Read(./.env)"))
    assert not any(m == "configuracion_no_interpretable" for m, _ in _motivos(res))


# ---- claves repetidas en opencode.json ---------------------------------------------------------------------------------------------


REPETIDAS = [
    '{"permission":{"read":{"*.env":"deny","*.env":"allow"}}}',  # la última gana en un lector, la primera en otro
    '{"permission":{"read":"allow"},"permission":{"read":{"*.env":"deny"}}}',  # la sección completa repetida
    '{"permission":{"read":"deny","read":"allow"}}',
    '{"permission":{"read":{"*.env":"allow"}},"agent":{"a":{"x":1,"x":2}}}',  # repetida en otra parte del archivo
    '{"permission":{"read":{"*":"allow"}},\n // comentario\n "model":"a", "model":"b"}',  # con comentarios (jsonc)
]


@pytest.mark.parametrize("texto", REPETIDAS)
def test_una_clave_repetida_en_opencode_json_no_se_interpreta_y_el_nivel_no_es_comprobado(tmp_path, texto):
    res = _auditar(tmp_path, lambda p: (p / "opencode.json").write_text(texto, encoding="utf-8"))
    assert Nivel.COMPROBADO not in _nivel(res, Plataforma.OPENCODE)
    assert ("configuracion_no_interpretable", "opencode.json") in _motivos(res)


def test_tambien_en_opencode_jsonc_y_en_la_carpeta_opencode(tmp_path):
    def preparar(p: Path):
        (p / ".opencode").mkdir()
        (p / ".opencode" / "opencode.jsonc").write_text('{"permission":{"read":"deny","read":"allow"}}', encoding="utf-8")

    res = _auditar(tmp_path, preparar)
    assert Nivel.COMPROBADO not in _nivel(res, Plataforma.OPENCODE)
    assert ("configuracion_no_interpretable", "opencode.jsonc") in _motivos(res)


def test_el_mismo_nombre_en_objetos_distintos_no_es_repetido(tmp_path):
    texto = '{"permission":{"read":{"*.env":"deny"},"edit":{"*.env":"deny"}},"agent":{"a":{"mode":"x"},"b":{"mode":"y"}}}'
    res = _auditar(tmp_path, lambda p: (p / "opencode.json").write_text(texto, encoding="utf-8"))
    assert ("configuracion_no_interpretable", "opencode.json") not in _motivos(res)


def test_el_lector_solo_rechaza_repetidas_si_se_le_pide():
    assert parsear_jsonc('{"a":1,"a":2}') == {"a": 2}
    with pytest.raises(JsoncNoInterpretable):
        parsear_jsonc('{"a":1,"a":2}', rechazar_repetidas=True)
    assert parsear_jsonc('{"a":{"x":1},"b":{"x":2}}', rechazar_repetidas=True) == {"a": {"x": 1}, "b": {"x": 2}}


def test_el_motivo_existe_y_ya_estaba_en_el_catalogo():
    assert MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE.value == "configuracion_no_interpretable"
