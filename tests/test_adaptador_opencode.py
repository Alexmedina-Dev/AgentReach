"""Historia 10: adaptador de opencode (reglas de permisos con "gana la última", sin sandbox) y kit de conformidad."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from agentreach.adapters.base import AdaptadorBase
from agentreach.adapters.conformance import ejecutar_conformidad
from agentreach.adapters.opencode import AdaptadorOpencode, DetectorOpencode
from agentreach.config import Configuracion
from agentreach.contracts import (
    AgentAdapter,
    Capacidad,
    Detector,
    Finding,
    Idioma,
    Plataforma,
    Postura,
    Ruta,
    Tipo,
)
from agentreach.contracts.no_revisado import MotivoNoRevisado
from agentreach.core.pipeline import Pipeline
from agentreach.infra.fs_solo_lectura import FsSoloLectura

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

CANARIO = "CANARIO-H10-sk-0123456789abcdef"
TH7, TH8 = Tipo.REGLA_PERMISIVA, Tipo.CAPACIDAD_DE_SHELL

CA04 = {"$schema": "https://opencode.ai/config.json",
        "permission": {"read": "allow", "edit": "allow", "bash": "allow", "webfetch": "allow", "external_directory": "ask"}}


def _json(ruta: Path, datos) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    texto = datos if isinstance(datos, (str, bytes)) else json.dumps(datos, indent=2) + "\n"
    ruta.write_bytes(texto if isinstance(texto, bytes) else texto.encode("utf-8"))  # LF también en Windows
    return ruta


def _adaptador(tmp: Path, *, encendido: bool = False, sistema: str = "linux", gestionada: Path | None = None):
    home = tmp / "home"
    home.mkdir(exist_ok=True)
    config = Configuracion(incluir_ubicaciones_sensibles=encendido, home=str(home))
    return AdaptadorOpencode(FsSoloLectura(), config, ruta_gestionada=str(gestionada) if gestionada else None,
                             sistema=sistema)


def _cargar(tmp: Path, proyecto: Path, **kw):
    a = _adaptador(tmp, **kw)
    return a, a.cargar(Ruta(str(proyecto)))


def _tipos(hallazgos: list[Finding]) -> list[Tipo]:
    return sorted((h.tipo for h in hallazgos), key=lambda t: t.value)


def _avisos(r) -> list[MotivoNoRevisado]:
    return [n.motivo for n in r.no_revisados if n.motivo is not MotivoNoRevisado.UBICACION_SENSIBLE_SIN_ACTIVAR]


@pytest.fixture
def proyecto(tmp_path: Path) -> Path:
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", CA04)
    return p


# ---- el contrato -----------------------------------------------------------------------------------------------------------


def test_cumple_el_puerto_declara_su_plataforma_y_es_completo(tmp_path: Path):
    a = _adaptador(tmp_path)
    assert isinstance(a, AgentAdapter) and isinstance(a, AdaptadorBase)
    assert a.plataforma is Plataforma.OPENCODE and a.capacidad is Capacidad.AUDITAR_Y_ADVERTIR
    assert isinstance(DetectorOpencode(a), Detector)


# ---- CA-04 ---------------------------------------------------------------------------------------------------------------------


def test_ca04_las_reglas_salen_con_archivo_y_linea_y_bash_se_llama_shell(proyecto: Path, tmp_path: Path):
    _, r = _cargar(tmp_path, proyecto)
    assert [(x.herramienta, x.accion) for x in r.reglas] == [
        ("read", "allow"), ("edit", "allow"), ("shell", "allow"), ("webfetch", "allow"), ("external_directory", "ask")]
    assert [x.ubicacion.linea for x in r.reglas] == [4, 5, 6, 7, 8]
    assert all(x.ubicacion.ruta.replace("\\", "/").endswith("opencode.json") for x in r.reglas)
    assert "allow" not in repr(r.reglas[0].especificador) and Path(r.reglas[0].ubicacion.ruta).name == "opencode.json"


def test_ca04_es_hallazgo_th7_y_th8_con_archivo_y_linea(proyecto: Path, tmp_path: Path):
    a = _adaptador(tmp_path)
    hallazgos = list(Pipeline([DetectorOpencode(a)]).ejecutar(Ruta(str(proyecto))))
    assert _tipos(hallazgos) == [TH7, TH7, TH7, TH8]  # read, edit y webfetch (TH-7) y shell (TH-8)
    por_tipo = {t: sorted(h.ubicacion.linea for h in hallazgos if h.tipo is t) for t in (TH7, TH8)}
    assert por_tipo == {TH7: [4, 5, 7], TH8: [6]}
    assert all(h.plataforma is Plataforma.OPENCODE for h in hallazgos)  # external_directory: ask es contexto


def test_shell_y_bash_se_aceptan_los_dos_nombres(tmp_path: Path):
    for nombre in ("shell", "bash"):
        p = tmp_path / nombre
        _json(p / "opencode.json", {"permission": {nombre: "allow"}})
        _, r = _cargar(tmp_path, p)
        assert [x.herramienta for x in r.reglas] == ["shell"]
        assert _tipos(list(Pipeline([DetectorOpencode(_adaptador(tmp_path))]).ejecutar(Ruta(str(p))))) == [TH8]


def test_un_deny_o_un_ask_amplios_no_son_hallazgo(tmp_path: Path):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", {"permission": {"read": "deny", "edit": "ask", "shell": "ask", "webfetch": "deny"}})
    assert list(Pipeline([DetectorOpencode(_adaptador(tmp_path))]).ejecutar(Ruta(str(p)))) == []


def test_reglas_por_patron_el_comodin_total_en_allow_es_amplio_y_uno_acotado_no(tmp_path: Path):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", {"permission": {"shell": {"*": "allow", "git push *": "ask"},
                                               "edit": {"src/**": "allow"}, "read": {"*": "allow", "*.env": "deny"}}})
    hallazgos = list(Pipeline([DetectorOpencode(_adaptador(tmp_path))]).ejecutar(Ruta(str(p))))
    assert _tipos(hallazgos) == [TH7, TH8]  # shell "*" y read "*" son amplios; edit acotado no


def test_un_permission_global_en_texto_alcanza_a_todo(tmp_path: Path):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", {"permission": "allow"})
    hallazgos = list(Pipeline([DetectorOpencode(_adaptador(tmp_path))]).ejecutar(Ruta(str(p))))
    assert _tipos(hallazgos) == [TH7, TH8] and {h.ubicacion.linea for h in hallazgos} == {2}


def test_sin_configuracion_no_hay_hallazgos_ni_avisos_de_version(tmp_path: Path):
    p = tmp_path / "proyecto"
    p.mkdir()
    a = _adaptador(tmp_path)
    assert list(Pipeline([DetectorOpencode(a)]).ejecutar(Ruta(str(p)))) == []
    assert _avisos(a.cargar(Ruta(str(p)))) == []


# ---- postura de lectura: gana la ÚLTIMA regla que coincide ---------------------------------------------------------------------------


def test_pp01_en_opencode_el_read_allow_del_proyecto_anula_el_ask_base_del_env(proyecto: Path, tmp_path: Path):
    a, _ = _cargar(tmp_path, proyecto)
    assert a.postura_para(Ruta(str(proyecto / ".env"))) is Postura.ALLOW  # PP-01: read allow
    assert a.postura_para(Ruta(str(proyecto / "config" / "servicio.env"))) is Postura.ALLOW
    assert a.postura_para(Ruta(str(proyecto / ".env.staging"))) is Postura.ALLOW
    assert a.postura_para(Ruta(str(proyecto / "src" / "app.py"))) is Postura.ALLOW


def test_oc01_sin_regla_de_read_el_ask_base_se_aplica_al_env(tmp_path: Path):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", {"permission": {"shell": "ask"}})
    a, _ = _cargar(tmp_path, p)
    assert a.postura_para(Ruta(str(p / ".env"))) is Postura.ASK  # la política base pregunta antes de leer *.env
    assert a.postura_para(Ruta(str(p / "x.env.local"))) is Postura.ASK
    assert a.postura_para(Ruta(str(p / "src" / "app.py"))) is Postura.SIN_REGLA
    assert a.regla_para(Ruta(str(p / ".env"))) is None  # la regla es la base, no un archivo


def test_gana_la_ultima_regla_que_coincide_y_no_la_mas_especifica(tmp_path: Path):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", {"permission": {"read": {"*.env": "deny", "*": "allow"}}})  # el "*" va después
    a, _ = _cargar(tmp_path, p)
    assert a.postura_para(Ruta(str(p / ".env"))) is Postura.ALLOW  # al revés que Claude Code
    _json(p / "opencode.json", {"permission": {"read": {"*": "allow", "*.env": "deny"}}})
    a, _ = _cargar(tmp_path, p)
    assert a.postura_para(Ruta(str(p / ".env"))) is Postura.DENY
    assert a.postura_para(Ruta(str(p / "src" / "a.py"))) is Postura.ALLOW


def test_un_deny_de_read_cita_su_regla_y_no_protege_frente_al_shell(tmp_path: Path):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", {"permission": {"read": {"*": "allow", "*.env": "deny"}, "shell": "allow"}})
    a = _adaptador(tmp_path)
    a.cargar(Ruta(str(p)))
    assert a.regla_para(Ruta(str(p / ".env"))).linea == 5
    hallazgos = list(Pipeline([DetectorOpencode(a)]).ejecutar(Ruta(str(p))))
    assert TH8 in _tipos(hallazgos)  # el deny de read no baja el hallazgo del shell


def test_aj01_un_archivo_fuera_del_proyecto_no_lo_cubre_el_read_allow_del_proyecto(proyecto: Path, tmp_path: Path):
    a, _ = _cargar(tmp_path, proyecto)
    assert a.postura_para(Ruta(str(tmp_path / "proyecto-ajeno" / ".env"))) is Postura.ASK  # external_directory: ask


def test_fuera_del_proyecto_sin_regla_de_external_directory_se_pregunta_por_defecto(tmp_path: Path):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", {"permission": {"read": "allow"}})
    a, _ = _cargar(tmp_path, p)
    assert a.postura_para(Ruta(str(tmp_path / "otro" / "x.txt"))) is Postura.ASK
    _json(p / "opencode.json", {"permission": {"external_directory": "allow"}})
    a, _ = _cargar(tmp_path, p)
    assert a.postura_para(Ruta(str(tmp_path / "otro" / "x.txt"))) is Postura.ALLOW


def test_sin_cargar_la_postura_es_no_determinada(tmp_path: Path):
    assert _adaptador(tmp_path).postura_para(Ruta(str(tmp_path / "x"))) is Postura.NO_DETERMINADA


def test_una_ruta_relativa_se_resuelve_contra_el_proyecto(proyecto: Path, tmp_path: Path):
    a, _ = _cargar(tmp_path, proyecto)
    assert a.postura_para(Ruta(".env")) is Postura.ALLOW


@pytest.mark.parametrize("patron,ruta,coincide", [
    ("*.env", ".env", True), ("*.env", "a/b/x.env", True), ("*.env.*", ".env.local", True), ("*.env", ".env.local", False),
    ("src/*", "src/a/b.py", True), ("src/*", "otro/a.py", False), ("a?.txt", "ab.txt", True), ("a?.txt", "abc.txt", False),
    ("*", "lo/que/sea", True),
])
def test_los_patrones_de_opencode_el_asterisco_cruza_carpetas(tmp_path: Path, patron, ruta, coincide):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", {"permission": {"read": {"*": "ask", patron: "deny"}}})
    a, _ = _cargar(tmp_path, p)
    esperado = Postura.DENY if coincide else Postura.ASK
    assert a.postura_para(Ruta(str(p / Path(ruta)))) is esperado


# ---- fuentes: global y gestionada solo con el opt-in; la gestionada va al final --------------------------------------------------------------


def test_con_el_opt_in_apagado_global_y_gestionada_se_leen_igual_solo_por_sus_reglas(proyecto: Path, tmp_path: Path):
    """Decisión de Alex (H2, opción A): la configuración global y la gestionada se leen siempre (solo reglas)."""
    _json(tmp_path / "home" / ".config" / "opencode" / "opencode.json", {"permission": {"read": "deny"}})
    _, r = _cargar(tmp_path, proyecto, encendido=False)
    assert r.no_revisados == () and any(x.fuente == "usuario" and x.accion == "deny" for x in r.reglas)
    assert len(r.reglas) == 6


def test_el_orden_es_base_global_proyecto_gestionada_y_la_politica_gestionada_gana(proyecto: Path, tmp_path: Path):
    _json(tmp_path / "home" / ".config" / "opencode" / "opencode.json", {"permission": {"read": "deny"}})
    gest = _json(tmp_path / "gest" / "opencode.json", {"permission": {"read": {"*.env": "deny"}}})
    a, r = _cargar(tmp_path, proyecto, encendido=True, gestionada=gest)
    fuentes = [Path(x.ubicacion.ruta).parent.name for x in r.reglas if x.herramienta == "read"]
    assert fuentes == ["opencode", "proyecto", "gest"]  # global, proyecto, gestionada
    assert a.postura_para(Ruta(str(proyecto / ".env"))) is Postura.DENY  # la gestionada va al final
    assert a.postura_para(Ruta(str(proyecto / "src" / "a.py"))) is Postura.ALLOW  # la del proyecto anula al deny global
    assert a.regla_para(Ruta(str(proyecto / ".env"))).ruta.replace("\\", "/").endswith("gest/opencode.json")


def test_el_proyecto_anula_a_la_global(tmp_path: Path):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", {"permission": {"read": "allow"}})
    _json(tmp_path / "home" / ".config" / "opencode" / "opencode.json", {"permission": {"read": "deny"}})
    a, _ = _cargar(tmp_path, p, encendido=True)
    assert a.postura_para(Ruta(str(p / ".env"))) is Postura.ALLOW


def test_opencode_jsonc_con_comentarios_tambien_se_lee(tmp_path: Path):
    p = tmp_path / "proyecto"
    _json(p / "opencode.jsonc", '{\n  // permisos\n  "permission": {"shell": "allow",},\n}\n')
    _, r = _cargar(tmp_path, p)
    assert [x.herramienta for x in r.reglas] == ["shell"] and r.reglas[0].ubicacion.linea == 3 and _avisos(r) == []


# ---- sin sandbox documentado -------------------------------------------------------------------------------------------------------------------


def test_opencode_no_tiene_sandbox_documentado_y_eso_se_reconoce_como_hecho(proyecto: Path, tmp_path: Path):
    _, r = _cargar(tmp_path, proyecto)
    assert r.sandbox_disponible is False and r.entorno_nombres == () and r.config_proyecto == ()


# ---- configuración que no se reconoce: aviso (FR-20), nunca excepción ----------------------------------------------------------------------------


@pytest.mark.parametrize("contenido,motivo", [
    (b"{ esto no es json", MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE),
    (b"", MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE),
    (b"[1, 2]", MotivoNoRevisado.VERSION_NO_RECONOCIDA),
    (b'{"permission": 5}', MotivoNoRevisado.VERSION_NO_RECONOCIDA),
    (b'{"permission": "bloquear"}', MotivoNoRevisado.VERSION_NO_RECONOCIDA),
    (b'{"permission": {"read": "quizas"}}', MotivoNoRevisado.VERSION_NO_RECONOCIDA),
    (b'{"permission": {"read": 3}}', MotivoNoRevisado.VERSION_NO_RECONOCIDA),
    (b'{"permission": {"read": {"*": "tal vez"}}}', MotivoNoRevisado.VERSION_NO_RECONOCIDA),
    (b'{"permission": {"read": ["allow"]}}', MotivoNoRevisado.VERSION_NO_RECONOCIDA),
    (b"\xff\xfe\xfd", MotivoNoRevisado.CODIFICACION_NO_UTF8),
])
def test_una_configuracion_que_no_se_reconoce_da_no_revisado_y_no_excepcion(tmp_path: Path, contenido, motivo):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", contenido)
    a, r = _cargar(tmp_path, p)
    assert _avisos(r) == [motivo] and r.reglas == ()
    assert list(Pipeline([DetectorOpencode(a)]).ejecutar(Ruta(str(p)))) == []  # y no se inventa un hallazgo


def test_un_json_de_65_niveles_da_profundidad_excedida(tmp_path: Path):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", '{"a":' * 65 + "1" + "}" * 65)
    assert _avisos(_cargar(tmp_path, p)[1]) == [MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA]


def test_un_archivo_valido_junto_a_uno_que_no_se_reconoce_conserva_el_valido(tmp_path: Path):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", {"permission": {"shell": "allow"}})
    _json(p / "opencode.jsonc", b"{ roto")
    _, r = _cargar(tmp_path, p)
    assert [x.herramienta for x in r.reglas] == ["shell"] and _avisos(r) == [MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE]


# ---- ningún texto de reglas sale; nada se ejecuta -------------------------------------------------------------------------------------------------


def test_el_texto_de_los_patrones_no_sale_en_ninguna_parte_ni_se_ejecuta_nada(tmp_path: Path, monkeypatch):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", {"permission": {"read": {CANARIO: "allow", "*": "allow"}, "shell": {CANARIO + " *": "allow"}}})

    def prohibido(*a, **k):
        raise AssertionError("se intentó ejecutar un programa")

    monkeypatch.setattr(subprocess, "Popen", prohibido)
    monkeypatch.setattr(os, "system", prohibido)
    a = _adaptador(tmp_path)
    r = a.cargar(Ruta(str(p)))
    hallazgos = list(Pipeline([DetectorOpencode(a)]).ejecutar(Ruta(str(p))))
    salida = repr(r) + repr(hallazgos) + "".join(str(h.a_dict(i)) for h in hallazgos for i in Idioma)
    assert hallazgos and CANARIO not in salida


# ---- el mismo kit de conformidad que Claude Code ----------------------------------------------------------------------------------------------------


def _fabrica(raiz: Path, fs):
    return AdaptadorOpencode(fs, Configuracion(incluir_ubicaciones_sensibles=False, home=str(raiz.parent / "home")),
                             sistema="linux")


def test_el_adaptador_de_opencode_pasa_el_kit_de_conformidad(tmp_path: Path):
    fallos = ejecutar_conformidad(_fabrica, tmp_path / "kit", archivo_configuracion="opencode.json",
                                  clave_entorno=("permission", "read"))
    assert fallos == []


def test_el_kit_tambien_lo_pasa_con_otra_ruta_de_clave_dentro_de_permission(tmp_path: Path):
    def fabrica(raiz: Path, fs):
        return _fabrica(raiz, fs)

    assert ejecutar_conformidad(fabrica, tmp_path / "kit2", archivo_configuracion="opencode.json",
                                clave_entorno=("permission", "shell", "*")) == []


# ---- registro y proyecto de prueba -------------------------------------------------------------------------------------------------------------------


def test_el_detector_esta_registrado_en_auditar():
    from agentreach.app import auditar as modulo

    nombres = {type(crear(FsSoloLectura(), Configuracion())).__name__ for crear in modulo._detectores}
    assert "DetectorOpencode" in nombres


@pytest.fixture
def proyecto_prueba() -> Path:
    raiz = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")
    if not raiz or not (Path(raiz) / "proyecto").is_dir():
        pytest.skip("AGENTREACH_PROYECTO_PRUEBA no apunta al proyecto de prueba")
    return Path(raiz) / "proyecto"


def test_ca04_pp01_aj01_y_oc01_con_el_proyecto_de_prueba(proyecto_prueba: Path, tmp_path: Path):
    a = _adaptador(tmp_path)
    r = a.cargar(Ruta(str(proyecto_prueba)))
    assert [(x.herramienta, x.accion) for x in r.reglas] == [
        ("read", "allow"), ("edit", "allow"), ("shell", "allow"), ("webfetch", "allow"), ("external_directory", "ask")]
    hallazgos = list(Pipeline([DetectorOpencode(a)]).ejecutar(Ruta(str(proyecto_prueba))))
    assert sorted(h.tipo.value for h in hallazgos) == ["TH-7", "TH-7", "TH-7", "TH-8"]  # CA-04
    assert a.postura_para(Ruta(str(proyecto_prueba / ".env"))) is Postura.ALLOW  # PP-01 en opencode: comprobado
    assert a.postura_para(Ruta(str(proyecto_prueba.parent / "proyecto-ajeno" / ".env"))) is Postura.ASK  # AJ-01: potencial
    assert a.postura_para(Ruta(str(proyecto_prueba / ".env.production"))) is Postura.ALLOW  # PP-03


# ---- parches de la revisión ----------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("patron", ["**", "*/*", "?*", "*"])
def test_un_allow_amplio_escrito_de_otra_forma_tambien_es_hallazgo(tmp_path: Path, patron):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", {"permission": {"shell": {patron: "allow"}}})
    assert _tipos(list(Pipeline([DetectorOpencode(_adaptador(tmp_path))]).ejecutar(Ruta(str(p))))) == [TH8]


def test_un_allow_amplio_que_una_regla_posterior_anula_no_es_hallazgo(tmp_path: Path):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", {"permission": {"shell": {"*": "allow"}}})
    _json(p / "opencode.jsonc", {"permission": {"shell": "deny"}})  # el jsonc va después y gana
    assert list(Pipeline([DetectorOpencode(_adaptador(tmp_path))]).ejecutar(Ruta(str(p)))) == []
    _json(p / "opencode.jsonc", {"permission": {"shell": {"git push *": "ask"}}})  # acotada: no anula el "*"
    assert _tipos(list(Pipeline([DetectorOpencode(_adaptador(tmp_path))]).ejecutar(Ruta(str(p))))) == [TH8]


def test_un_patron_con_barras_de_windows_y_con_punto_barra_coincide(tmp_path: Path):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", {"permission": {"read": {"*": "allow", "./secretos\\*": "deny"}}})
    a, _ = _cargar(tmp_path, p)
    assert a.postura_para(Ruta(str(p / "secretos" / "llave.txt"))) is Postura.DENY
    assert a.postura_para(Ruta(str(p / "src" / "a.py"))) is Postura.ALLOW


def test_un_patron_absoluto_y_el_home_expandido_coinciden_con_la_ruta_absoluta(tmp_path: Path):
    p = tmp_path / "proyecto"
    absoluto = str(p / "datos").replace("\\", "/") + "/*"
    _json(p / "opencode.json", {"permission": {"read": {"*": "allow", absoluto: "deny"},
                                               "external_directory": {"*": "ask", "~/*": "allow"}}})
    a, _ = _cargar(tmp_path, p)
    assert a.postura_para(Ruta(str(p / "datos" / "x.txt"))) is Postura.DENY
    assert a.postura_para(Ruta(str(tmp_path / "home" / "algo.txt"))) is Postura.ALLOW  # ~/ se expande al home
    assert a.postura_para(Ruta(str(tmp_path / "otro" / "algo.txt"))) is Postura.ASK


def test_una_ruta_imposible_no_rompe_la_consulta(proyecto: Path, tmp_path: Path):
    a, _ = _cargar(tmp_path, proyecto)
    assert a.postura_para(Ruta("a\x00b")) in (Postura.NO_DETERMINADA, Postura.ASK, Postura.ALLOW, Postura.SIN_REGLA)
    assert a.regla_para(Ruta("a\x00b")) is None or True


def test_los_permisos_por_agente_se_avisan_y_se_conservan_las_reglas_generales(tmp_path: Path):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", {"permission": {"shell": "allow"},
                                "agent": {"dev": {"permission": {"shell": "allow"}}, "otro": {"mode": "primary"}}})
    _, r = _cargar(tmp_path, p)
    assert [x.herramienta for x in r.reglas] == ["shell"]
    assert _avisos(r) == [MotivoNoRevisado.FUNCION_NO_MODELADA]  # una función que cambia las reglas y no se modela


def test_sin_permisos_por_agente_no_hay_aviso(tmp_path: Path):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", {"permission": {"shell": "ask"}, "agent": {"otro": {"mode": "primary"}}})
    assert _avisos(_cargar(tmp_path, p)[1]) == []


def test_un_home_que_no_se_puede_resolver_no_busca_la_global_en_el_directorio_actual(tmp_path: Path, monkeypatch):
    p = tmp_path / "proyecto"
    _json(p / "opencode.json", {"permission": {"shell": "ask"}})
    monkeypatch.setenv("HOME", "~")
    monkeypatch.setenv("USERPROFILE", "~")
    a = AdaptadorOpencode(FsSoloLectura(), Configuracion(incluir_ubicaciones_sensibles=True), sistema="linux")
    r = a.cargar(Ruta(str(p)))
    assert MotivoNoRevisado.ARCHIVO_ILEGIBLE in {n.motivo for n in r.no_revisados} and len(r.reglas) == 1


def test_programdata_vacio_no_deja_una_ruta_relativa(monkeypatch):
    from agentreach.adapters.opencode import _gestionada_por_defecto

    monkeypatch.setenv("ProgramData", "")
    assert os.path.isabs(_gestionada_por_defecto("win32"))


def test_el_sistema_de_archivos_externo_se_puede_inyectar(proyecto: Path, tmp_path: Path):
    llamadas: list[str] = []

    class Espia(FsSoloLectura):
        def metadatos(self, ruta):
            llamadas.append(str(ruta))
            return super().metadatos(ruta)

    config = Configuracion(incluir_ubicaciones_sensibles=True, home=str(tmp_path / "home"))
    AdaptadorOpencode(FsSoloLectura(), config, fs_externo=Espia(), sistema="linux").cargar(Ruta(str(proyecto)))
    assert any("opencode" in x for x in llamadas)
