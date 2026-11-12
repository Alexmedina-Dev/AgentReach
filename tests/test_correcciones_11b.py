"""Historia 11b: correcciones H1 a H4 de la revisión de las historias 9 a 11, con pruebas de punta a punta.

Regla nueva: si no se entiende un archivo de configuración, el nivel nunca es «comprobado» (FR-5, SM-1).
H1: configuración del agente ilegible. H2 (opción A de Alex): la configuración del usuario y la gestionada se leen siempre, solo por
sus reglas. H3: los patrones ``Read(...)`` siguen la sintaxis gitignore que documenta Claude Code. H4: permisos por agente de opencode.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from agentreach.app.auditar import auditar
from agentreach.config import Configuracion
from agentreach.contracts import (
    Motivo,
    Nivel,
    PermisoLectura,
    PermisosArchivo,
    Plataforma,
    Postura,
    Tipo,
)

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

LEGIBLE = PermisosArchivo(PermisoLectura.SI, False, False, "usuario", "icacls x")


class Sonda:
    def evaluar(self, ruta):
        return LEGIBLE


def _json(ruta: Path, datos) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    return ruta


def _proyecto(tmp_path: Path) -> Path:
    p = tmp_path / "proyecto"
    p.mkdir()
    (p / ".env").write_text("STRIPE_SECRET_KEY=sk_live_valor_largo_123\n", encoding="utf-8")
    return p


def _auditar(p: Path, home: Path | None = None):
    casa = home or p.parent / "casa-vacia"
    casa.mkdir(exist_ok=True)
    return auditar(str(p), Configuracion(home=str(casa)), medidores=(Sonda(), None))


def _env(res, agente: str, sufijo: str = "/.env"):
    return [h for h in res.hallazgos if h.tipo is Tipo.CREDENCIAL_EN_ARCHIVO and h.agente == agente
            and str(h.ubicacion.ruta).replace("\\", "/").endswith(sufijo)]


def _niveles(hs) -> set[tuple[Nivel, Motivo]]:
    return {(h.nivel, h.motivo) for h in hs}


NO_DETERMINADO = {(Nivel.POTENCIAL, Motivo.NO_DETERMINADO)}
DENY = {(Nivel.POTENCIAL, Motivo.REGLA_DENY)}
COMPROBADO = {(Nivel.COMPROBADO, Motivo.EXISTE_LEGIBLE_SIN_REGLA)}


# ---- el control: sin configuración rota el .env sale comprobado, y con un deny entendido, potencial -----------------------------


def test_control_sin_configuracion_comprobado_y_con_un_deny_entendido_potencial(tmp_path: Path):
    p = _proyecto(tmp_path)
    assert _niveles(_env(_auditar(p), "claude-code")) == COMPROBADO
    _json(p / ".claude" / "settings.json", {"permissions": {"deny": ["Read(./.env)"]}})
    assert _niveles(_env(_auditar(p), "claude-code")) == DENY


# ---- H1: configuración del agente ilegible ------------------------------------------------------------------------------------


def _romper(p: Path, como: str) -> None:
    destino = p / ".claude" / "settings.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    buena = json.dumps({"permissions": {"deny": ["Read(./.env)"]}})
    if como == "comentario":
        destino.write_text("// un comentario\n" + buena, encoding="utf-8")
    elif como == "cortado":
        destino.write_text(buena[:25], encoding="utf-8")
    elif como == "utf8_invalido":
        destino.write_bytes(b'{"permissions": {"deny": ["Read(./.env)"]}} \xff\xfe\x80')
    elif como == "elemento_no_texto":
        destino.write_text(json.dumps({"permissions": {"deny": ["Read(./.env)", 5]}}), encoding="utf-8")
    elif como == "enorme":
        with open(destino, "wb") as f:
            f.write(buena.encode())
            f.truncate(5 * 1024 * 1024 + 1)
    elif como == "forma_rara":
        destino.write_text(json.dumps({"permissions": ["no", "es", "un", "objeto"]}), encoding="utf-8")
    elif como == "profundo":
        destino.write_text('{"a":' * 70 + "1" + "}" * 70, encoding="utf-8")
    else:
        raise AssertionError(como)


@pytest.mark.parametrize("como", ["comentario", "cortado", "utf8_invalido", "elemento_no_texto", "enorme", "forma_rara", "profundo"])
def test_h1_una_configuracion_de_claude_code_ilegible_nunca_deja_el_env_comprobado(tmp_path: Path, como: str):
    p = _proyecto(tmp_path)
    _romper(p, como)
    res = _auditar(p)
    assert _niveles(_env(res, "claude-code")) == NO_DETERMINADO, como
    assert any(n.ruta.endswith("settings.json") for n in res.no_revisados)  # y además se dice qué no se pudo revisar


def test_h1_un_hecho_de_git_no_depende_de_la_configuracion_del_agente_pero_una_credencial_en_el_remoto_si(tmp_path: Path):
    """Que git ejecute un programa lo dice ``.git/config``: romper un archivo del agente no puede bajar ese hallazgo (sería una
    forma barata de apagar la salida distinta de cero). Una credencial en el remoto sí depende de que el agente pueda leer el archivo."""
    p = _proyecto(tmp_path)
    (p / ".git").mkdir()
    (p / ".git" / "config").write_text(
        "[core]" + chr(10) + chr(9) + "fsmonitor = ./senuelo.cmd" + chr(10) + '[remote "o"]' + chr(10) + chr(9)
        + "url = https://ana:s3cr3t-LARGO-9f2k@host.invalid/x.git" + chr(10), encoding="utf-8")
    _romper(p, "cortado")
    res = _auditar(p)
    git = [h for h in res.hallazgos if h.tipo is Tipo.GIT_EJECUTA_PROGRAMAS]
    assert git and all(h.nivel is Nivel.COMPROBADO for h in git)
    remoto = [h for h in res.hallazgos if h.tipo is Tipo.GIT_REMOTO_SOSPECHOSO and h.agente == "claude-code"]
    assert remoto and all(h.nivel is Nivel.POTENCIAL for h in remoto)


def test_h1_lo_que_el_agente_carga_solo_no_depende_de_las_reglas_de_lectura(tmp_path: Path):
    """Texto invisible en un archivo de instrucciones: un hecho de los bytes que ninguna regla de lectura cambia (AT-01, AT-09)."""
    p = _proyecto(tmp_path)
    (p / "CLAUDE.md").write_text("Instrucciones\u200b normales\n", encoding="utf-8")
    _romper(p, "cortado")
    invisibles = [h for h in _auditar(p).hallazgos if h.tipo is Tipo.TEXTO_INVISIBLE]
    assert invisibles and all(h.nivel is Nivel.COMPROBADO for h in invisibles)


@pytest.mark.parametrize("como", ["truncado", "utf8_invalido", "accion_desconocida", "forma_rara"])
def test_h1_una_configuracion_de_opencode_ilegible_nunca_deja_el_env_comprobado(tmp_path: Path, como: str):
    p = _proyecto(tmp_path)
    destino = p / "opencode.json"
    if como == "truncado":
        destino.write_text('{"permission": {"read": {"*.env": "den', encoding="utf-8")
    elif como == "utf8_invalido":
        destino.write_bytes(b'{"permission": {"read": "deny"}} \xff\xfe')
    elif como == "accion_desconocida":
        destino.write_text(json.dumps({"permission": {"read": "quizas"}}), encoding="utf-8")
    else:
        destino.write_text(json.dumps({"permission": 7}), encoding="utf-8")
    res = _auditar(p)
    assert _niveles(_env(res, "opencode")) == NO_DETERMINADO, como


def test_la_regla_en_un_proyecto_sin_agentes_configurados_no_cambia_nada(tmp_path: Path):
    """Sin ningún archivo de configuración no hay nada que no se entienda: sigue la tabla de siempre."""
    p = _proyecto(tmp_path)
    res = _auditar(p)
    assert _niveles(_env(res, "claude-code")) == COMPROBADO
    assert _niveles(_env(res, "opencode")) == {(Nivel.POTENCIAL, Motivo.REGLA_ASK)}  # la política base de opencode pregunta por *.env


# ---- H2 (opción A): usuario y gestionada se leen siempre ---------------------------------------------------------------------


def test_h2_un_deny_en_la_configuracion_del_usuario_baja_el_nivel_sin_activar_nada(tmp_path: Path):
    p = _proyecto(tmp_path)
    casa = tmp_path / "casa"
    _json(casa / ".claude" / "settings.json", {"permissions": {"deny": ["Read(//**/.env)"]},
                                              "env": {"MI_VARIABLE": "valor-CANARIO-777"}})
    res = _auditar(p, casa)  # sin el opt-in de ubicaciones sensibles
    assert _niveles(_env(res, "claude-code")) == DENY
    assert "CANARIO-777" not in repr(res) and "valor-CANARIO" not in repr(res)  # del bloque env nunca salen los valores


def test_h2_un_ask_del_usuario_baja_a_potencial_con_su_motivo(tmp_path: Path):
    p = _proyecto(tmp_path)
    casa = tmp_path / "casa"
    _json(casa / ".claude" / "settings.json", {"permissions": {"ask": ["Read(.env)"]}})
    assert _niveles(_env(_auditar(p, casa), "claude-code")) == {(Nivel.POTENCIAL, Motivo.REGLA_ASK)}


def test_h2_una_regla_barra_del_usuario_se_ancla_en_su_carpeta_de_claude_no_en_el_proyecto(tmp_path: Path):
    """Documentación de permisos: ``Read(/secrets/**)`` en la configuración de usuario bloquea ``~/.claude/secrets``, no el proyecto."""
    p = _proyecto(tmp_path)
    (p / "secrets").mkdir()
    (p / "secrets" / "k.env").write_text("API_TOKEN=valor-largo-1234\n", encoding="utf-8")
    casa = tmp_path / "casa"
    _json(casa / ".claude" / "settings.json", {"permissions": {"deny": ["Read(/secrets/**)"]}})
    assert _niveles(_env(_auditar(p, casa), "claude-code", "/secrets/k.env")) == COMPROBADO


def test_h2_un_deny_en_la_configuracion_global_de_opencode_manda_sobre_el_allow_del_proyecto_anterior(tmp_path: Path):
    p = _proyecto(tmp_path)
    casa = tmp_path / "casa"
    _json(casa / ".config" / "opencode" / "opencode.json", {"permission": {"read": "deny"}})
    res = _auditar(p, casa)
    assert _niveles(_env(res, "opencode")) == DENY


@pytest.mark.skipif(sys.platform != "win32", reason="la ruta de la configuración gestionada de Windows")
def test_h2_la_configuracion_gestionada_se_lee_y_manda(tmp_path: Path, monkeypatch):
    p = _proyecto(tmp_path)
    programas = tmp_path / "programas"
    _json(programas / "ClaudeCode" / "managed-settings.json", {"permissions": {"deny": ["Read(//**/.env)"]}})
    _json(programas / "opencode" / "opencode.json", {"permission": {"read": "deny"}})
    monkeypatch.setenv("ProgramFiles", str(programas))
    monkeypatch.setenv("ProgramData", str(programas))
    res = _auditar(p)
    assert _niveles(_env(res, "claude-code")) == DENY
    assert _niveles(_env(res, "opencode")) == DENY


def test_h2_una_configuracion_de_usuario_ilegible_tambien_baja_el_nivel(tmp_path: Path):
    p = _proyecto(tmp_path)
    casa = tmp_path / "casa"
    destino = casa / ".claude" / "settings.json"
    destino.parent.mkdir(parents=True)
    destino.write_text('{"permissions": {"deny": ["Read(//**/.env)"', encoding="utf-8")  # cortado
    assert _niveles(_env(_auditar(p, casa), "claude-code")) == NO_DETERMINADO


# ---- H3: los patrones Read siguen gitignore -----------------------------------------------------------------------------------


def _con_patron(tmp_path: Path, patron: str, sufijo: str, crear: str | None = None):
    p = _proyecto(tmp_path)
    if crear:
        destino = p / crear
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text("API_TOKEN=valor-largo-1234\n", encoding="utf-8")
    _json(p / ".claude" / "settings.json", {"permissions": {"deny": [patron]}})
    return _niveles(_env(_auditar(p), "claude-code", sufijo))


@pytest.mark.parametrize("patron, crear, sufijo, esperado", [
    ("Read(*.env)", "config/prod.env", "/config/prod.env", DENY),  # sin barra: cualquier profundidad
    ("Read(.env)", "sub/.env", "/sub/.env", DENY),
    ("Read(**/.env)", "a/b/.env", "/a/b/.env", DENY),
    ("Read(secrets/**)", "a/secrets/x.env", "/a/secrets/x.env", DENY),  # una sola carpeta: cualquier profundidad (deny)
    ("Read(src/componentes/**)", "otro/src/componentes/x.env", "/otro/src/componentes/x.env", COMPROBADO),  # varios segmentos: anclado
    ("Read(src/componentes/**)", "src/componentes/x.env", "/src/componentes/x.env", DENY),
    ("Read(./.en[v])", None, "/.env", NO_DETERMINADO),  # clase de caracteres: no se interpreta
    ("Read()", None, "/.env", NO_DETERMINADO),  # vacío
    ("Read(.\\sec\\**)", None, "/.env", NO_DETERMINADO),  # barras de Windows: en gitignore la barra invertida escapa
    ("Read(!sample.env)", None, "/.env", NO_DETERMINADO),  # negación
    ("Read({a,b}.env)", None, "/.env", NO_DETERMINADO),  # llaves
])
def test_h3_semantica_de_los_patrones_read(tmp_path: Path, patron, crear, sufijo, esperado):
    assert _con_patron(tmp_path, patron, sufijo, crear) == esperado


def test_h3_un_deny_entendido_manda_aunque_otro_patron_no_se_entienda(tmp_path: Path):
    p = _proyecto(tmp_path)
    _json(p / ".claude" / "settings.json", {"permissions": {"deny": ["Read(./.en[v])", "Read(./.env)"]}})
    assert _niveles(_env(_auditar(p), "claude-code")) == DENY


@pytest.mark.skipif(sys.platform != "win32", reason="rutas con unidad de Windows")
@pytest.mark.parametrize("forma", ["minuscula", "con_dos_puntos"])
def test_h3_un_patron_absoluto_de_windows_acepta_las_dos_formas(tmp_path: Path, forma: str):
    p = _proyecto(tmp_path)
    unidad = os.path.splitdrive(str(p))[0][0]
    patron = f"Read(//{unidad.lower()}/**/.env)" if forma == "minuscula" else f"Read(//{unidad.upper()}:/**/.env)"
    _json(p / ".claude" / "settings.json", {"permissions": {"deny": [patron]}})
    assert _niveles(_env(_auditar(p), "claude-code")) == DENY


def test_h3_las_reglas_que_no_son_read_no_bajan_el_nivel(tmp_path: Path):
    """Un ``deny Edit`` o ``deny Bash(cat .env)`` no protege la lectura (FR-6: el sistema de permisos no es un sandbox)."""
    p = _proyecto(tmp_path)
    _json(p / ".claude" / "settings.json", {"permissions": {"deny": ["Edit(./.env)", "Bash(cat .env)"]}})
    assert _niveles(_env(_auditar(p), "claude-code")) == COMPROBADO


# ---- H4: permisos por agente de opencode ----------------------------------------------------------------------------------------


def test_h4_un_permiso_por_agente_de_opencode_deja_el_nivel_no_determinado(tmp_path: Path):
    p = _proyecto(tmp_path)
    _json(p / "opencode.json", {"permission": {"read": {"*.env": "allow"}},
                                "agent": {"revisor": {"permission": {"read": {"*.env": "deny"}}}}})
    res = _auditar(p)
    assert _niveles(_env(res, "opencode")) == NO_DETERMINADO
    assert _niveles(_env(res, "claude-code")) == COMPROBADO  # Claude Code no depende de ese archivo
    assert any(n.ruta.endswith("opencode.json") for n in res.no_revisados)


def test_h4_sin_permiso_por_agente_el_allow_del_proyecto_sigue_dando_comprobado(tmp_path: Path):
    p = _proyecto(tmp_path)
    _json(p / "opencode.json", {"permission": {"read": {"*.env": "allow"}}, "agent": {"revisor": {"model": "x"}}})
    assert _niveles(_env(_auditar(p), "opencode")) == COMPROBADO  # PP-04: el read: allow anula el ask base


# ---- la regla, a nivel del evaluador ---------------------------------------------------------------------------------------------


def test_la_regla_general_ningun_hecho_de_archivo_o_de_bytes_llega_a_comprobado_con_reglas_incompletas():
    from agentreach.contracts import Ajeno, Etiqueta, Finding, Location, Proveedor, Ruta
    from agentreach.core.evaluador import Evaluador

    class Incompleto:
        plataforma = Plataforma.CLAUDE_CODE

        def postura_para(self, ruta):
            return Postura.NO_DETERMINADA  # lo que devuelven los adaptadores con reglas incompletas

        def regla_para(self, ruta):
            return None

    for tipo in (Tipo.CREDENCIAL_EN_ARCHIVO, Tipo.ENLACE_FUERA_DEL_PROYECTO, Tipo.GIT_REMOTO_SOSPECHOSO):
        candidato = Finding(
            ubicacion=Location(Ruta(os.path.abspath("x.env")), 1), tipo=tipo, proveedor=Proveedor.DESCONOCIDO, nivel=Nivel.HIPOTESIS,
            motivo=Motivo.NO_DETERMINADO, ajeno_a_tarea=Ajeno.NO_DETERMINADO, plataforma=Plataforma.NO_DETERMINADA,
            agente=Etiqueta("sin-agente"), postura=Postura.NO_DETERMINADA)
        salida = Evaluador(Sonda(), None, [Incompleto()], lambda r: True).evaluar([candidato])
        assert all(h.nivel is not Nivel.COMPROBADO for h in salida), tipo


# ---- coincide: tres estados -------------------------------------------------------------------------------------------------------


def test_coincide_devuelve_none_si_no_se_puede_interpretar(tmp_path: Path):
    from agentreach.adapters.claude_code.reglas import coincide

    p = str(tmp_path / "p")
    f = str(tmp_path / "p" / ".env")
    for patron in ("", "   ", "!x", "a[b]", "{a,b}", "a\\b"):
        assert coincide(patron, f, p, str(tmp_path), "proyecto", True) is None, patron
    assert coincide("./.env", f, p, str(tmp_path), "proyecto", True) is True
    assert coincide("./otro", f, p, str(tmp_path), "proyecto", True) is False
    assert coincide("/algo", f, p, str(tmp_path), "gestionada", True) is None  # a dónde se ancla una regla gestionada no está documentado


# ---- parches de la revisión ----------------------------------------------------------------------------------------------------


def test_opencode_tools_mode_y_la_carpeta_local_dejan_el_nivel_no_determinado(tmp_path: Path):
    for nombre, datos in (("tools", {"tools": {"read": False}}), ("mode", {"mode": {"build": {"tools": {"read": False}}}}),
                          ("agent_tools", {"agent": {"x": {"tools": {"read": False}}}})):
        p = tmp_path / nombre / "proyecto"
        p.mkdir(parents=True)
        (p / ".env").write_text("STRIPE_SECRET_KEY=sk_live_valor_largo_123\n", encoding="utf-8")
        _json(p / "opencode.json", {"permission": {"read": {"*.env": "allow"}}, **datos})
        assert _niveles(_env(_auditar(p), "opencode")) == NO_DETERMINADO, nombre
    p = tmp_path / "local" / "proyecto"
    p.mkdir(parents=True)
    (p / ".env").write_text("STRIPE_SECRET_KEY=sk_live_valor_largo_123\n", encoding="utf-8")
    _json(p / "opencode.json", {"permission": {"read": {"*.env": "allow"}}})
    agente = p / ".opencode" / "agent" / "revisor.md"
    agente.parent.mkdir(parents=True)
    agente.write_text("---" + chr(10) + "permission:" + chr(10) + "  read: deny" + chr(10) + "---" + chr(10) + "Texto del agente" + chr(10), encoding="utf-8")  # permisos por agente: no se modelan
    res = _auditar(p)
    assert _niveles(_env(res, "opencode")) == NO_DETERMINADO


def test_el_bloque_env_del_usuario_no_se_lee_ni_sus_nombres_ni_la_limpieza(tmp_path: Path):
    p = _proyecto(tmp_path)
    casa = tmp_path / "casa"
    _json(casa / ".claude" / "settings.json", {"env": {"CLAUDE_CODE_SUBPROCESS_ENV_SCRUB": "1", "MI_SECRETO_PROD": "valor-CANARIO-9"}})
    from agentreach.adapters.claude_code import AdaptadorClaudeCode
    from agentreach.infra.fs_solo_lectura import FsSoloLectura

    r = AdaptadorClaudeCode(FsSoloLectura(str(p)), Configuracion(home=str(casa))).cargar(__import__("agentreach").contracts.Ruta(str(p)))
    assert r.entorno_nombres == () and r.limpieza_de_entorno is False and "CANARIO" not in repr(r)


@pytest.mark.parametrize("clave", [{"hooks": {"PreToolUse": [{"matcher": "Read", "hooks": []}]}}, {"sandbox": {"filesystem": {"denyRead": ["."]}}},
                                   {"allowManagedPermissionRulesOnly": True}])
def test_las_claves_que_cambian_lo_que_se_lee_dejan_el_nivel_no_determinado(tmp_path: Path, clave):
    p = _proyecto(tmp_path)
    _json(p / ".claude" / "settings.json", clave)
    assert _niveles(_env(_auditar(p), "claude-code")) == NO_DETERMINADO


def test_los_fragmentos_de_la_configuracion_gestionada_se_leen(tmp_path: Path):
    from agentreach.adapters.claude_code import AdaptadorClaudeCode
    from agentreach.contracts import Ruta
    from agentreach.infra.fs_solo_lectura import FsSoloLectura

    p = _proyecto(tmp_path)
    gest = tmp_path / "gest" / "managed-settings.json"
    _json(gest.parent / "managed-settings.d" / "10-politica.json", {"permissions": {"deny": ["Read(//**/.env)"]}})
    a = AdaptadorClaudeCode(FsSoloLectura(str(p)), Configuracion(home=str(tmp_path / "c")), ruta_gestionada=str(gest))
    r = a.cargar(Ruta(str(p)))
    assert any(x.fuente == "gestionada" and x.accion == "deny" for x in r.reglas)
    assert a.postura_para(Ruta(str(p / ".env"))) is Postura.DENY


def test_un_patron_que_no_se_interpreta_se_dice_en_no_revisados_con_su_archivo(tmp_path: Path):
    p = _proyecto(tmp_path)
    _json(p / ".claude" / "settings.json", {"permissions": {"deny": ["Read(./.en[v])"]}})
    res = _auditar(p)
    assert any(n.ruta.endswith("settings.json") and n.motivo.value == "configuracion_no_interpretable" for n in res.no_revisados)


def test_una_configuracion_a_la_que_no_se_puede_acceder_no_cuenta_como_inexistente(tmp_path: Path, monkeypatch):
    """Un ``settings.json`` que existe pero cuya consulta falla (permiso) deja el nivel sin determinar."""
    from agentreach.infra.fs_solo_lectura import FsSoloLectura

    p = _proyecto(tmp_path)
    _json(p / ".claude" / "settings.json", {"permissions": {"deny": ["Read(./.env)"]}})
    real = FsSoloLectura.metadatos

    def con_permiso_denegado(self, ruta):
        if str(ruta).endswith("settings.json"):
            return None  # lo que hace metadatos() ante un OSError (EACCES)
        return real(self, ruta)

    monkeypatch.setattr(FsSoloLectura, "metadatos", con_permiso_denegado)
    assert _niveles(_env(_auditar(p), "claude-code")) == NO_DETERMINADO


def test_el_patron_se_compara_tambien_por_la_ruta_real(tmp_path: Path):
    from agentreach.adapters.claude_code.reglas import coincide

    real = tmp_path / "real"
    real.mkdir()
    (real / ".env").write_text("X=1", encoding="utf-8")
    enlace = tmp_path / "proyecto"
    try:
        os.symlink(real, enlace, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("este sistema no permite crear enlaces simbólicos")
    assert coincide("./.env", str(enlace / ".env"), str(real), str(tmp_path), "proyecto", True) is True


def test_un_home_relativo_no_se_toma_como_la_carpeta_del_usuario(tmp_path: Path):
    from agentreach.adapters.claude_code import AdaptadorClaudeCode
    from agentreach.contracts import Ruta
    from agentreach.infra.fs_solo_lectura import FsSoloLectura

    p = _proyecto(tmp_path)
    _json(p / "~" / ".claude" / "settings.json", {"permissions": {"deny": ["Read(//**/.env)"]}})  # el proyecto no se hace pasar por el usuario
    r = AdaptadorClaudeCode(FsSoloLectura(str(p)), Configuracion(home="~")).cargar(Ruta(str(p)))
    assert not any(x.fuente == "usuario" for x in r.reglas)


def test_lo_que_el_agente_ejecuta_o_carga_solo_sale_una_vez_y_sin_postura_de_lectura(tmp_path: Path):
    p = _proyecto(tmp_path)
    (p / ".git").mkdir()
    (p / ".git" / "config").write_text("[core]\n\tfsmonitor = ./senuelo.cmd\n", encoding="utf-8")
    git = [h for h in _auditar(p).hallazgos if h.tipo is Tipo.GIT_EJECUTA_PROGRAMAS]
    assert len(git) == 1 and git[0].postura is Postura.SIN_REGLA and git[0].nivel is Nivel.COMPROBADO
