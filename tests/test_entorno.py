"""Historia 6: variables de entorno con nombre de credencial. Solo se inventarían NOMBRES, nunca valores."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

from agentreach.collectors.entorno import DetectorEntorno
from agentreach.contracts import Detector, EnvView, Finding, Idioma, Proveedor, Ruta, Tipo
from agentreach.core.pipeline import Pipeline
from agentreach.infra.env_view import EnvVistaProceso

CANARIO = "CANARIO-H6-sk_live_" + "5544332211ffeedd"
RAIZ = Path(__file__).resolve().parents[1]
FUENTES = RAIZ / "src" / "agentreach"


class EntornoFalso:
    """Entorno inyectado. Si alguien pide un valor, la prueba falla: el puerto solo da nombres."""

    def __init__(self, **variables: str) -> None:
        self._variables = variables

    def nombres(self) -> Iterable[str]:
        return list(self._variables)

    def __getitem__(self, nombre: str) -> str:
        raise AssertionError("se pidió el valor de una variable")

    def values(self):  # pragma: no cover
        raise AssertionError("se pidieron los valores del entorno")

    items = get = copy = values


def _detectar(env: EnvView) -> list[Finding]:
    return Pipeline([DetectorEntorno(env)]).ejecutar(Ruta("proyecto"))


def _texto(hallazgos: list[Finding]) -> str:
    return repr(hallazgos) + "".join(str(h.a_dict(i)) for h in hallazgos for i in Idioma)


# (a) el valor no aparece en ninguna salida ----------------------------------------------------------------


def test_el_valor_canario_no_aparece_en_la_salida():
    env = EntornoFalso(AGENTREACH_PRUEBA_API_TOKEN=CANARIO, AGENTREACH_PRUEBA_DB_PASSWORD=CANARIO)
    hallazgos = _detectar(env)
    assert len(hallazgos) == 2
    assert CANARIO not in _texto(hallazgos) and "sk_live" not in _texto(hallazgos)


def test_con_el_entorno_real_el_valor_tampoco_aparece(monkeypatch):
    monkeypatch.setenv("AGENTREACH_PRUEBA_API_KEY", CANARIO)
    hallazgos = _detectar(EnvVistaProceso())
    assert any("AGENTREACH_PRUEBA_API_KEY" in h.ubicacion.ruta for h in hallazgos)
    assert CANARIO not in _texto(hallazgos)


# (b) las variables sin forma de credencial se ignoran -----------------------------------------------------------


def test_variables_sin_forma_de_credencial_se_ignoran():
    env = EntornoFalso(PATH="a", HOME="b", NODE_ENV="production", USERNAME="x", LANG="es", COMPUTERNAME="pc")
    assert _detectar(env) == []


def test_nombres_con_forma_de_credencial_se_reconocen_con_su_proveedor():
    env = EntornoFalso(ANTHROPIC_API_KEY="x", GITHUB_TOKEN="x", STRIPE_SECRET_KEY="x", DATABASE_URL="x",
                       AGENTREACH_PRUEBA_DB_PASSWORD="x", PATH="x")
    por_nombre = {h.ubicacion.ruta: h for h in _detectar(env)}
    assert set(por_nombre) == {
        "entorno:ANTHROPIC_API_KEY", "entorno:GITHUB_TOKEN", "entorno:STRIPE_SECRET_KEY",
        "entorno:DATABASE_URL", "entorno:AGENTREACH_PRUEBA_DB_PASSWORD",
    }
    assert por_nombre["entorno:ANTHROPIC_API_KEY"].proveedor is Proveedor.IA
    assert por_nombre["entorno:GITHUB_TOKEN"].proveedor is Proveedor.CODIGO
    assert por_nombre["entorno:AGENTREACH_PRUEBA_DB_PASSWORD"].proveedor is Proveedor.BASE_DE_DATOS
    assert all(h.tipo is Tipo.VARIABLE_DE_ENTORNO for h in por_nombre.values())


def test_nombres_repetidos_dan_un_solo_hallazgo_y_las_mayusculas_son_variables_distintas():
    class Env:
        def nombres(self):
            return ["API_TOKEN", "API_TOKEN", "Api_Token"]  # en Linux, Api_Token es otra variable

    assert sorted(h.ubicacion.ruta for h in _detectar(Env())) == ["entorno:API_TOKEN", "entorno:Api_Token"]


def test_nombres_que_solo_difieren_en_caracteres_de_control_dan_un_solo_hallazgo():
    class Env:
        def nombres(self):
            return ["API_TOKEN", "API_TOKEN\x1b", "API_TOKEN\x07"]

    assert len(_detectar(Env())) == 1


def test_una_vista_de_entorno_mal_hecha_no_tumba_el_detector():
    class SinNombres:
        def nombres(self):
            return None

    class ConBasura:
        def nombres(self):
            return [None, 3, "API_TOKEN"]

    assert _detectar(SinNombres()) == []
    assert len(_detectar(ConBasura())) == 1


def test_nombres_de_base_de_datos_sin_credencial_se_ignoran_y_el_proveedor_es_estricto():
    env = EntornoFalso(DATABASE_NAME="x", DATABASE_HOST="x", DB_HOST="x", DB_PORT="x", DB_PASSIVE_MODE="x",
                       ADB_USER="x")
    assert _detectar(env) == []
    h = {h.ubicacion.ruta: h for h in _detectar(EntornoFalso(DB_PASS="x", DATABASE_PASSWORD="x", MY_DB_USER_TOKEN="x"))}
    assert h["entorno:DB_PASS"].proveedor is Proveedor.BASE_DE_DATOS
    assert h["entorno:DATABASE_PASSWORD"].proveedor is Proveedor.BASE_DE_DATOS


def test_un_nombre_con_caracteres_de_control_sale_limpio():
    class Env:
        def nombres(self):
            return ["API_TOKEN\x1b[2J"]

    hallazgos = _detectar(Env())
    assert len(hallazgos) == 1 and "\x1b" not in hallazgos[0].ubicacion.ruta


def test_la_linea_no_aplica_y_se_marca_como_no_determinada():
    h = _detectar(EntornoFalso(API_TOKEN="x"))[0]
    assert h.ubicacion.linea_determinada is False


# (c) se lee con una lista de nombres, nunca el entorno entero ---------------------------------------------------


def test_el_detector_cumple_el_puerto_y_el_adaptador_tambien():
    assert isinstance(DetectorEntorno(EntornoFalso()), Detector)
    assert isinstance(EnvVistaProceso(), EnvView)


def test_la_vista_del_proceso_solo_da_nombres_en_una_lista(monkeypatch):
    monkeypatch.setenv("AGENTREACH_PRUEBA_UNO", CANARIO)
    nombres = EnvVistaProceso().nombres()
    assert isinstance(nombres, list) and all(isinstance(n, str) for n in nombres)
    assert "AGENTREACH_PRUEBA_UNO" in nombres and CANARIO not in nombres


def _llamadas_y_atributos(ruta: Path) -> tuple[set[str], set[str]]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    llamadas, atributos = set(), set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Call):
            f = n.func
            llamadas.add(f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else "")
        if isinstance(n, ast.Attribute):
            atributos.add(n.attr)
    return llamadas, atributos


def test_env_view_no_vuelca_ni_pide_valores_del_entorno():
    llamadas, atributos = _llamadas_y_atributos(FUENTES / "infra" / "env_view.py")
    assert not {"items", "values", "copy", "getenv", "get", "dict", "environb", "getenvb", "expandvars"} & (
        llamadas | atributos
    )


def test_entorno_py_no_toca_os_ni_archivos_ni_leer_seguro():
    ruta = FUENTES / "collectors" / "entorno.py"
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    importados = set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            importados |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            importados.add(n.module or "")
            importados |= {a.name for a in n.names}
    assert not {"os", "sys", "subprocess", "leer_seguro", "lectura_segura"} & {i.split(".")[-1] for i in importados}
    llamadas, _ = _llamadas_y_atributos(ruta)
    assert not {"open", "read_text", "read_bytes", "environ", "getenv"} & llamadas


# EV-01: sin las variables no hay nada; con ellas (solo en el proceso hijo) salen exactamente los dos nombres ---


_CODIGO_HIJO = (
    "import sys; sys.path.insert(0, sys.argv[1])\n"
    "from agentreach.collectors.entorno import DetectorEntorno\n"
    "from agentreach.infra.env_view import EnvVistaProceso\n"
    "hs = DetectorEntorno(EnvVistaProceso()).detectar('p')\n"
    "print(sorted(h.ubicacion.ruta for h in hs if h.ubicacion.ruta.startswith('entorno:AGENTREACH_PRUEBA_')))\n"
)


def _hijo(variables: dict[str, str]) -> str:
    entorno = {k: v for k, v in os.environ.items() if not k.startswith("AGENTREACH_PRUEBA_")}
    entorno.update(variables)  # existen solo en el proceso hijo, como con --con-entorno
    r = subprocess.run(
        [sys.executable, "-c", _CODIGO_HIJO, str(RAIZ / "src")],
        capture_output=True, text=True, check=False, env=entorno,
    )
    assert r.returncode == 0, r.stderr  # el diagnóstico del hijo no se pierde
    assert CANARIO not in r.stdout + r.stderr
    return r.stdout.strip()


def test_ev01_sin_las_variables_no_se_reporta_nada():
    assert _hijo({}) == "[]"


def test_ev01_con_las_variables_salen_exactamente_los_dos_nombres():
    salida = _hijo({"AGENTREACH_PRUEBA_API_TOKEN": CANARIO, "AGENTREACH_PRUEBA_DB_PASSWORD": CANARIO})
    assert salida == "['entorno:AGENTREACH_PRUEBA_API_TOKEN', 'entorno:AGENTREACH_PRUEBA_DB_PASSWORD']"
    assert "AGENTREACH_PRUEBA_" not in os.environ  # no quedó nada en este proceso


def test_el_generador_declara_las_mismas_dos_variables():
    texto = (RAIZ / "pruebas" / "generar_proyecto_prueba.py").read_text(encoding="utf-8")
    assert '"AGENTREACH_PRUEBA_API_TOKEN"' in texto and '"AGENTREACH_PRUEBA_DB_PASSWORD"' in texto
