"""Historia 15: evaluación contra los 67 casos del proyecto de prueba (``respuestas-esperadas.md`` -> ``expected.json``).

Cada caso se clasifica como *coincide*, *falso positivo*, *omisión* o *no aplicable*; los «extra» (hallazgos que ningún caso
espera) se listan aparte. Los casos con nivel distinto por agente (Claude Code y opencode) se evalúan por agente. Ver ``README.md``.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from unittest import mock

import pytest

from agentreach import cli
from agentreach.app.auditar import ResultadoAuditoria, auditar
from agentreach.config import Configuracion
from agentreach.contracts import Finding, MotivoNoRevisado, Nivel, Plataforma

AQUI = Path(__file__).parent
CASOS: list[dict] = json.loads((AQUI / "expected.json").read_text(encoding="utf-8"))
AGENTES = {"claude-code": Plataforma.CLAUDE_CODE, "opencode": Plataforma.OPENCODE}
RANGO = {"comprobado": 0, "potencial": 1, "hipotesis": 2}
VARIABLES_DE_ENTORNO = {"AGENTREACH_PRUEBA_API_TOKEN": "valor-falso-CNR020", "AGENTREACH_PRUEBA_DB_PASSWORD": "valor-falso-CNR021"}


@pytest.fixture(scope="module")
def raiz() -> Path:
    r = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")
    if not r or not (Path(r) / "proyecto").is_dir():
        if os.environ.get("CI") or os.environ.get("AGENTREACH_EXIGIR_PRUEBAS"):
            pytest.fail("AGENTREACH_PROYECTO_PRUEBA no apunta al proyecto de prueba")
        pytest.skip("AGENTREACH_PROYECTO_PRUEBA no apunta al proyecto de prueba")
    return Path(r)


_CACHE: dict[str, ResultadoAuditoria] = {}


def auditoria(raiz: Path, clave: str, opt_in: bool = True) -> ResultadoAuditoria:
    """La auditoría de una de las raíces del oráculo (con memoria: es lo caro). Solo lectura, sin red, sin programas."""
    llave = f"{clave}|{opt_in}"
    if llave not in _CACHE:
        with mock.patch.dict(os.environ, _entorno_sin_credenciales(clave), clear=True):  # el entorno de esta máquina no cuenta
            _CACHE[llave] = _auditar(raiz, clave, opt_in)
    return _CACHE[llave]


def _entorno_sin_credenciales(clave: str) -> dict[str, str]:
    """El entorno del proceso sin variables con nombre de credencial (cada máquina tiene las suyas); EV-01 pone solo las dos del oráculo."""
    from agentreach.collectors.detector.patrones import clasificar_nombre

    entorno = {k: v for k, v in os.environ.items() if clasificar_nombre(k) is None}
    return {**entorno, **(VARIABLES_DE_ENTORNO if clave == "entorno" else {})}


def _auditar(raiz: Path, clave: str, opt_in: bool) -> ResultadoAuditoria:
    config = Configuracion(incluir_ubicaciones_sensibles=opt_in, home=str(raiz / "home-falso"))
    if clave == "contenedora":
        return auditar(str(raiz), config, trabajo=str(raiz / "proyecto"))  # AJ-01: el agente se lanza desde proyecto/
    if clave == "opencode-sin-read":
        return auditar(str(raiz / "proyecto-opencode-sin-read"), config)
    if clave.startswith("trampas-git/"):
        return auditar(str(raiz / clave), Configuracion())
    return auditar(str(raiz / ("proyecto" if clave == "entorno" else clave)), config)  # "entorno": las variables entran en el entorno


def _ruta(h: Finding) -> str:
    return str(h.ubicacion.ruta_real or h.ubicacion.ruta).replace("\\", "/").lower()


def _coincide_ruta(ruta: str, sufijos: list[str]) -> bool:
    for s in sufijos:
        s = s.lower().replace("\\", "/")
        if s.startswith(("(", "entorno:")):
            if ruta == s:
                return True
        elif s.endswith("/"):
            if "/" + s in ruta + "/":
                return True
        elif ruta.endswith("/" + s) or ruta == s:
            return True
    return False


def observados(res: ResultadoAuditoria, caso: dict, agente: str | None) -> list[Finding]:
    """Los hallazgos de ese caso (por ruta, tipo y línea) y, si se pide, solo los de un agente (o los que no dependen de uno)."""
    salida = []
    for h in res.hallazgos:
        if not _coincide_ruta(_ruta(h), caso["rutas"]):
            continue
        if caso.get("tipos") and h.tipo.value not in caso["tipos"]:
            continue
        if caso.get("linea") is not None and h.ubicacion.linea != caso["linea"]:
            continue
        if agente and h.plataforma not in (AGENTES[agente], Plataforma.NO_DETERMINADA):
            continue
        salida.append(h)
    return salida


@dataclass
class Resultado:
    caso: str
    agente: str
    clase: str  # coincide, coincide_aceptado, falso_positivo, omision, no_aplicable
    detalle: str


def clasificar(raiz: Path, caso: dict) -> list[Resultado]:
    esperado = caso["esperado"]
    agentes = list(esperado) if isinstance(esperado, dict) else ["claude-code+opencode"]
    resultados: list[Resultado] = []
    if esperado == "no_debe_existir":
        existe = any((raiz / r).exists() for r in (caso["rutas"][0],))
        return [Resultado(caso["id"], "-", "falso_positivo" if existe else "coincide", "TR-01: ¿apareció el archivo marcador?")]
    if esperado == "no_aplicable":
        return [Resultado(caso["id"], "-", "no_aplicable", caso.get("nota", ""))]
    if caso.get("solo_windows") and sys.platform != "win32":
        return [Resultado(caso["id"], "-", "no_aplicable", "solo Windows")]
    res = auditoria(raiz, caso["raiz"], opt_in=True)
    if esperado == "no_se_pudo_revisar":
        motivo = MotivoNoRevisado(caso["motivo"])
        hay = any(_coincide_ruta(str(n.ruta_real or n.ruta).replace("\\", "/").lower(), caso["rutas"]) and n.motivo is motivo
                  for n in res.no_revisados)
        sin_hallazgo = not observados(res, caso, None)
        clase = "coincide" if hay and sin_hallazgo else ("omision" if not hay else "falso_positivo")
        return [Resultado(caso["id"], "-", clase, f"motivo {motivo.value}: {'sale' if hay else 'no sale'} en no revisados")]
    for agente in agentes:
        h = observados(res, caso, agente if agente in AGENTES else None)
        esp = esperado[agente] if isinstance(esperado, dict) else esperado
        niveles = {x.nivel.value for x in h}
        if esp == "no_se_reporta":
            clase = "coincide" if not h else "falso_positivo"
        elif not h:
            clase = "omision"
        elif niveles == {esp}:
            clase = "coincide"
        elif any(RANGO[n] < RANGO[esp] for n in niveles):
            clase = "falso_positivo"  # un nivel MÁS ALTO que el esperado (p. ej. un «comprobado» falso)
        else:
            clase = "omision"  # un nivel más bajo que el esperado
        if clase != "coincide" and caso.get("aceptado", {}).get(agente) and niveles == {caso["aceptado"][agente]}:
            clase = "coincide_aceptado"
        resultados.append(Resultado(caso["id"], agente, clase, f"esperado {esp}, observado {sorted(niveles) or 'nada'} ({len(h)} hallazgo(s))"))
    return resultados


IDS = [c["id"] for c in CASOS]


# ---- el oráculo mismo --------------------------------------------------------------------------------------------------


def test_expected_json_tiene_los_67_casos_y_las_cifras_del_oraculo():
    assert len(CASOS) == 67 and len(set(IDS)) == 67
    # Cifras tras la decisión de Alex del 2026-11-11 (Historia 27): una variable reconocida solo por su nombre nunca pasa de potencial.
    # El oráculo original daba 18 comprobado, 28 potencial y 2 hipótesis por agente (5 casos TH-1 y AJ-01 pasaron a potencial).
    for agente, esperado in (("claude-code", {"comprobado": 13, "potencial": 33, "hipotesis": 2}),
                             ("opencode", {"comprobado": 13, "potencial": 33, "hipotesis": 2})):
        cuenta = {n: 0 for n in esperado}
        for c in CASOS:
            n = c["esperado"][agente] if isinstance(c["esperado"], dict) else c["esperado"]
            if n in cuenta:
                cuenta[n] += 1
        assert cuenta == esperado, (agente, cuenta)
    assert sum(1 for c in CASOS if c["esperado"] == "no_se_reporta") == 16
    assert sum(1 for c in CASOS if c["esperado"] == "no_se_pudo_revisar") == 1
    for c in CASOS:  # cada caso tiene todo lo que la evaluación necesita
        assert c["rutas"] and c["raiz"] and "esperado" in c


def test_los_ids_son_los_de_respuestas_esperadas_md(raiz: Path):
    texto = (raiz / "respuestas-esperadas.md").read_text(encoding="utf-8")
    del_oraculo = set(re.findall(r"(?m)^\| ([A-Z]{2}-\d\d[a-f]?) \|", texto))
    assert set(IDS) == del_oraculo


# ---- la evaluación -----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("id_caso", IDS)
def test_cada_caso_coincide_con_el_oraculo(raiz: Path, id_caso: str):
    caso = next(c for c in CASOS if c["id"] == id_caso)
    for r in clasificar(raiz, caso):
        assert r.clase in ("coincide", "coincide_aceptado", "no_aplicable"), f"{r.caso} [{r.agente}] {r.clase}: {r.detalle}"
        if r.clase == "coincide_aceptado":
            assert caso.get("explicacion"), f"{r.caso}: una diferencia aceptada necesita su explicación con evidencia"


def test_cero_comprobados_falsos_y_cero_omisiones_de_los_comprobados(raiz: Path):
    falsos, omitidos = [], []
    for caso in CASOS:
        for r in clasificar(raiz, caso):
            if r.clase == "falso_positivo" and "comprobado" in r.detalle.split("observado")[-1]:
                falsos.append(f"{r.caso}[{r.agente}]")
            if r.clase == "omision" and "esperado comprobado" in r.detalle:
                omitidos.append(f"{r.caso}[{r.agente}]")
    assert falsos == [] and omitidos == []


def test_los_extra_son_los_conocidos(raiz: Path):
    """Hallazgos que ningún caso espera. Los de la carpeta contenedora son archivos del oráculo que otros casos cubren desde su propia raíz."""
    res = auditoria(raiz, "proyecto")
    cubiertos = [c for c in CASOS if c["raiz"] == "proyecto"]
    extra = [h for h in res.hallazgos if not any(_coincide_ruta(_ruta(h), c["rutas"]) and (not c.get("tipos") or h.tipo.value in c["tipos"])
                                                for c in cubiertos)]
    assert [(h.tipo.value, _ruta(h).rsplit("/", 1)[-1]) for h in extra] == []  # en proyecto/ no hay ningún hallazgo sin caso


# ---- las condiciones de «terminado cuando» -------------------------------------------------------------------------------


def test_con_las_ubicaciones_sensibles_apagadas_sale_no_se_pudo_revisar_nunca_sin_hallazgos(raiz: Path):
    res = auditoria(raiz, "proyecto", opt_in=False)
    assert any(n.motivo is MotivoNoRevisado.UBICACION_SENSIBLE_SIN_ACTIVAR for n in res.no_revisados)
    for h in res.hallazgos:
        assert "home-falso" not in _ruta(h), "con el opt-in apagado no se mira el home (HF-01, HF-03, HF-05, AT-03, AT-10)"


def test_tr01_el_senuelo_no_corrio(raiz: Path):
    for clave in ("proyecto", "contenedora", "entorno"):
        auditoria(raiz, clave)
    assert not (raiz / "trampas" / "PWNED.txt").exists()


def test_cero_marcadores_canario_en_la_salida(raiz: Path, capsys):
    for agente in ("opencode", "claude-code"):  # primero la configuración de opencode y después la de Claude Code (PRD)
        with mock.patch.dict(os.environ, VARIABLES_DE_ENTORNO):
            codigo = cli.main([str(raiz), "--home", str(raiz / "home-falso"), "--incluir-ubicaciones-sensibles", "--agente", agente,
                               "--detalle", "--ancho", "100"])
        salida = capsys.readouterr()
        assert codigo in (0, 1) and not re.search(r"cnr0\d\d", (salida.out + salida.err).lower().replace(" ", ""))


@pytest.mark.skipif(sys.platform != "win32", reason="el segundo cálculo del permiso es de Windows")
def test_cero_discrepancias_entre_el_permiso_y_su_segundo_calculo_en_los_comprobados(raiz: Path):
    from agentreach.contracts import Ruta
    from agentreach.core.politica import Base, base_de
    from agentreach.core.verificacion_independiente import Confirmacion, confirmar
    from agentreach.infra.sonda_windows import SondaWindows
    from agentreach.infra.verificador_permiso_windows import VerificadorPermisoWindows

    sonda, verificador = SondaWindows(), VerificadorPermisoWindows()
    from agentreach.contracts import Motivo

    # Con el tope por nombre (TH-1 ya no llega a comprobado) se comprueba cada archivo cuyo hecho de permiso decidiría un comprobado:
    # los comprobados de base archivo y los que solo el tope dejó en potencial («sin fuente verificada»).
    comprobados = [h for clave in ("proyecto", "contenedora") for h in auditoria(raiz, clave).hallazgos
                   if base_de(h.tipo) is Base.ARCHIVO
                   and (h.nivel is Nivel.COMPROBADO or h.motivo is Motivo.SIN_FUENTE_VERIFICADA)]
    assert len(comprobados) >= 8
    for h in comprobados:
        resultado = confirmar(sonda, verificador, Ruta(str(h.ubicacion.ruta_real or h.ubicacion.ruta)))
        assert resultado.estado is Confirmacion.CONFIRMADO, (h.tipo.value, _ruta(h), resultado.discrepancias)


def test_ajeno_a_la_tarea_de_at08_y_aj01(raiz: Path):
    from agentreach.contracts import Ajeno

    h = [x for x in auditoria(raiz, "contenedora").hallazgos if _ruta(x).endswith("proyecto-ajeno/.env")]
    assert h and all(x.ajeno_a_tarea is Ajeno.SI for x in h)  # AJ-01
    con_tarea = auditar(str(raiz / "proyecto"), Configuracion(), tarea="arreglar el formulario de contacto")
    at08 = [x for x in con_tarea.hallazgos if _ruta(x).endswith("src/estilos/notas-tipografia.txt")]
    assert at08 and all(x.ajeno_a_tarea is Ajeno.SI for x in at08)  # AT-08


# ---- confirmación desde la fuente primaria (FR-24) ---------------------------------------------------------------------------


def test_el_oraculo_esta_confirmado_desde_la_fuente_primaria_por_otra_persona():
    faltan = [c["id"] for c in CASOS
              if c["esperado"] not in ("no_se_reporta", "no_aplicable", "no_debe_existir")
              and not (c["fuente_primaria"].strip() and c["confirmado_por"].strip())]
    assert faltan == [], f"sin confirmar: {faltan[:5]}..."
    assert all(c["confirmado_por"].strip().lower() not in ("claude", "agentreach", "autor") for c in CASOS)
