"""Pruebas de los contratos del hallazgo (Historia 1). Todos los "secretos" son datos falsos."""

import ast
import dataclasses
import json
import typing
from enum import Enum
from pathlib import Path

import pytest

from agentreach.contracts import (
    CAMPOS_HALLAZGO,
    CATALOGO_EXPLICACIONES,
    Ajeno,
    Etiqueta,
    Finding,
    Idioma,
    Linea,
    Location,
    Motivo,
    Nivel,
    Plataforma,
    Postura,
    Proveedor,
    Ruta,
    RutaReal,
    Tipo,
    fuente_verificada,
    limpiar_ruta,
    ordenar,
)
from agentreach.contracts import finding as modulo_finding
from agentreach.contracts.ports import (
    AgentAdapter,
    Capacidad,
    Detector,
    EnvView,
    FsProbe,
    PermisoLectura,
    ReadOnlyFs,
)

CANARIO = "CANARIO-sk_live_" + "0123456789abcdef"


def hallazgo(
    nivel: Nivel = Nivel.COMPROBADO,
    tipo: Tipo = Tipo.CREDENCIAL_EN_ARCHIVO,
    ruta: str = "proyecto/.env",
    linea: int | Linea = 3,
    **extra: typing.Any,
) -> Finding:
    datos: dict[str, typing.Any] = {
        "ubicacion": Location(Ruta(ruta), linea),
        "tipo": tipo,
        "proveedor": Proveedor.PAGOS,
        "nivel": nivel,
        "motivo": Motivo.EXISTE_LEGIBLE_SIN_REGLA,
        "ajeno_a_tarea": Ajeno.NO_DETERMINADO,
        "plataforma": Plataforma.OPENCODE,
        "agente": Etiqueta("dev-alex"),
        "postura": Postura.SIN_REGLA,
    }
    datos.update(extra)
    return Finding(**datos)


# (a) ocho campos y ningún texto libre ---------------------------------------------------------


def test_el_hallazgo_tiene_sus_ocho_campos():
    assert len(CAMPOS_HALLAZGO) == 8
    campos = {c.name for c in dataclasses.fields(Finding)}
    h = hallazgo()
    for nombre in CAMPOS_HALLAZGO:
        assert nombre in campos or callable(getattr(h, nombre)), nombre


def _tipos_de(anotacion: typing.Any) -> list[typing.Any]:
    """Aplana ``A | B | None`` en sus tipos simples."""
    if typing.get_origin(anotacion) in (typing.Union, type(int | str)):
        return [t for a in typing.get_args(anotacion) for t in _tipos_de(a)]
    return [anotacion]


def _campos_de_texto_sin_etiquetar(clase: type) -> list[str]:
    permitidos = {int, bool, type(None), Ruta, RutaReal, Etiqueta, Location}
    malos = []
    for nombre, anotacion in typing.get_type_hints(clase).items():
        for t in _tipos_de(anotacion):
            es_enum = isinstance(t, type) and issubclass(t, Enum)
            if not es_enum and t not in permitidos:
                malos.append(f"{clase.__name__}.{nombre}: {t}")
    return malos


def test_ningun_campo_es_texto_libre():
    assert _campos_de_texto_sin_etiquetar(Finding) == []
    assert _campos_de_texto_sin_etiquetar(Location) == []


def test_la_deteccion_de_texto_libre_funciona():
    @dataclasses.dataclass
    class Malo:
        valor: str

    assert _campos_de_texto_sin_etiquetar(Malo) != []


def test_ningun_campo_se_llama_como_un_valor_secreto():
    prohibidos = ("valor", "value", "secret", "secreto", "contenido", "content", "password", "token")
    for clase in (Finding, Location):
        for campo in dataclasses.fields(clase):
            assert not any(p in campo.name.lower() for p in prohibidos), campo.name


# (b) tipos y fuente verificada ----------------------------------------------------------------


def test_existen_los_20_tipos_del_catalogo():
    assert [t.value for t in Tipo] == [f"TH-{n}" for n in range(1, 21)]


def test_cada_tipo_tiene_explicacion_en_los_dos_idiomas():
    for tipo in Tipo:
        for idioma in Idioma:
            significa, hacer = CATALOGO_EXPLICACIONES[tipo][idioma]
            assert significa.strip() and hacer.strip()


def test_tipo_sin_indicador_cuenta_como_sin_fuente_verificada(monkeypatch):
    monkeypatch.setitem(modulo_finding.FUENTE_VERIFICADA, Tipo.CLAVE_PRIVADA_SSH, True)
    assert fuente_verificada(Tipo.CLAVE_PRIVADA_SSH) is True
    monkeypatch.delitem(modulo_finding.FUENTE_VERIFICADA, Tipo.CLAVE_PRIVADA_SSH)
    assert fuente_verificada(Tipo.CLAVE_PRIVADA_SSH) is False


# (c) rutas con escapes de terminal ------------------------------------------------------------


@pytest.mark.parametrize(
    "sucia",
    [
        "proyecto/\x1b[2Jlimpio.txt",
        "proyecto/\x1b[31mrojo\x1b[0m.txt",
        "proyecto/\x1b]0;titulo falso\x07limpio.txt",
        "proyecto/\x1b]8;;http://x\x1b\\limpio.txt",
        "proyecto/\x07\x08limpio.txt\x00",
    ],
)
def test_ruta_con_escapes_sale_limpia(sucia):
    limpia = limpiar_ruta(sucia)
    assert "\x1b" not in limpia
    assert all(ord(c) >= 0x20 and ord(c) != 0x7F for c in limpia)
    assert limpia.endswith(("limpio.txt", "rojo.txt"))
    # También limpia al crear la ubicación, por cualquier vía.
    assert Location(Ruta(sucia), 1).ruta == limpia


# (d) el núcleo no importa adaptadores, infraestructura ni reporte -----------------------------


def test_core_no_importa_adapters_infra_ni_reporting():
    raiz = Path(__file__).resolve().parents[1] / "src" / "agentreach"
    prohibidos = {"adapters", "infra", "reporting"}
    for archivo in (raiz / "core").rglob("*.py"):
        for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
            if isinstance(nodo, ast.Import):
                nombres = [a.name for a in nodo.names]
            elif isinstance(nodo, ast.ImportFrom):
                nombres = [("." * nodo.level) + (nodo.module or "")]
                if nodo.level:  # import relativo: "from .. import adapters"
                    nombres += [("." * nodo.level) + (nodo.module or "") + "." + a.name
                                for a in nodo.names]
            else:
                continue
            for nombre in nombres:
                partes = nombre.replace("agentreach.", "").lstrip(".").split(".")
                assert partes[0] not in prohibidos, f"{archivo.name} importa {nombre}"


# Creación, inmutabilidad, ubicación -----------------------------------------------------------


def test_creacion_y_textos_del_catalogo():
    h = hallazgo()
    assert h.ubicacion.ruta == "proyecto/.env"
    assert h.ubicacion.linea == 3
    assert "credencial" in h.que_significa(Idioma.ES)
    assert "credential" in h.que_significa(Idioma.EN)
    assert h.que_hacer(Idioma.ES) != h.que_hacer(Idioma.EN)


def test_inmutable_y_con_slots():
    h = hallazgo()
    with pytest.raises(dataclasses.FrozenInstanceError):
        h.nivel = Nivel.HIPOTESIS  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        h.ubicacion.linea = 9  # type: ignore[misc]
    assert not hasattr(h, "__dict__")
    assert not hasattr(h.ubicacion, "__dict__")


def test_linea_no_determinada_es_explicita():
    ubic = Location(Ruta("opencode.json"))
    assert ubic.linea is Linea.NO_DETERMINADA
    assert not ubic.linea_determinada
    assert ubic.a_dict()["linea"] == "linea no determinada"


@pytest.mark.parametrize("mala", [0, -1, True, "7", 1.5])
def test_linea_invalida_se_rechaza(mala):
    with pytest.raises((TypeError, ValueError)):
        Location(Ruta("a"), mala)


def test_etiqueta_invalida_se_rechaza():
    with pytest.raises(ValueError):
        hallazgo(agente=Etiqueta("clave=" + CANARIO + " y mas texto"))


# Orden por nivel ------------------------------------------------------------------------------


def test_orden_por_nivel():
    h1 = hallazgo(Nivel.HIPOTESIS, ruta="a")
    h2 = hallazgo(Nivel.COMPROBADO, ruta="z")
    h3 = hallazgo(Nivel.POTENCIAL, ruta="m")
    assert [h.nivel for h in ordenar([h1, h2, h3])] == [
        Nivel.COMPROBADO,
        Nivel.POTENCIAL,
        Nivel.HIPOTESIS,
    ]


def test_orden_estable_por_ruta_y_linea_no_determinada_al_final():
    a = hallazgo(ruta="x", linea=Linea.NO_DETERMINADA)
    b = hallazgo(ruta="x", linea=2)
    c = hallazgo(ruta="x", linea=10)
    assert ordenar([a, c, b]) == [b, c, a]


# Serialización --------------------------------------------------------------------------------


def test_serializacion_a_dict_json_y_idiomas():
    h = hallazgo(regla=Location(Ruta("opencode.json")), postura=Postura.DENY)
    d = h.a_dict(Idioma.EN)
    json.dumps(d)  # solo tipos simples
    assert d["nivel"] == "comprobado"
    assert d["tipo"] == "TH-1"
    assert d["ubicacion"] == {"ruta": "proyecto/.env", "linea": 3}
    assert d["regla"]["linea"] == "linea no determinada"
    assert d["que_significa"] == h.que_significa(Idioma.EN)
    assert hallazgo().a_dict()["regla"] is None
    assert d["fuente_verificada"] is False


# Canario --------------------------------------------------------------------------------------


def test_el_canario_no_aparece_en_ninguna_salida(tmp_path):
    """Un detector falso lee un .env con un secreto canario y solo conserva el tipo y la línea."""
    env = tmp_path / ".env"
    env.write_text(f"STRIPE_SECRET_KEY={CANARIO}\n", encoding="utf-8")
    linea = next(
        i for i, texto in enumerate(env.read_text(encoding="utf-8").splitlines(), 1)
        if texto.startswith("STRIPE_SECRET_KEY=")
    )
    h = hallazgo(ruta=".env", linea=linea)
    salidas = [repr(h), str(h), repr(h.ubicacion), json.dumps(h.a_dict())]
    salidas += [json.dumps(h.a_dict(i), ensure_ascii=False) for i in Idioma]
    salidas += [h.que_significa(i) + h.que_hacer(i) + h.texto_motivo(i) for i in Idioma]
    salidas.append(repr(dataclasses.asdict(h)))
    for salida in salidas:
        assert CANARIO not in salida
        assert "sk_live" not in salida


def test_el_catalogo_no_contiene_valores_con_forma_de_secreto():
    for por_idioma in CATALOGO_EXPLICACIONES.values():
        for textos in por_idioma.values():
            for texto in textos:
                assert "sk_live" not in texto and "=" not in texto


# Puertos --------------------------------------------------------------------------------------


def test_puertos_son_protocolos_verificables():
    class SondaFalsa:
        def permiso_lectura(self, ruta: Ruta) -> PermisoLectura:
            return PermisoLectura.NO_DETERMINADO

    class EntornoFalso:
        def nombres(self):
            return ["AGENTREACH_PRUEBA_API_TOKEN"]

    class AdaptadorFalso:
        plataforma = Plataforma.OPENCODE
        capacidad = Capacidad.SOLO_AUDITAR

        def postura_para(self, ruta: Ruta) -> Postura:
            return Postura.NO_DETERMINADA

    assert isinstance(SondaFalsa(), FsProbe)
    assert isinstance(EntornoFalso(), EnvView)
    assert isinstance(AdaptadorFalso(), AgentAdapter)
    assert not isinstance(object(), ReadOnlyFs)


def test_los_puertos_no_exponen_metodos_de_escritura_ni_de_valores():
    prohibidos = ("write", "escribir", "delete", "borrar", "remove", "valor", "value", "get_env")
    for puerto in (ReadOnlyFs, EnvView, FsProbe):
        for nombre in dir(puerto):
            if not nombre.startswith("_"):
                assert not any(p in nombre.lower() for p in prohibidos), nombre


# Tubería mínima -------------------------------------------------------------------------------


class _DetectorFijo:
    def __init__(self, *hallazgos: Finding) -> None:
        self._hallazgos = hallazgos

    def detectar(self, proyecto: Ruta):
        return list(self._hallazgos)


class _DetectorRoto:
    def detectar(self, proyecto: Ruta):
        raise ValueError("fallo interno")


def test_tuberia_sin_detectores_devuelve_lista_vacia():
    from agentreach.core.pipeline import Pipeline

    assert Pipeline().ejecutar(Ruta("proyecto")) == []


def test_tuberia_reune_y_ordena_los_hallazgos_de_varios_detectores():
    from agentreach.core.pipeline import Pipeline

    potencial = hallazgo(Nivel.POTENCIAL, ruta="proyecto/a.env")
    comprobado = hallazgo(Nivel.COMPROBADO, ruta="proyecto/b.env")
    tuberia = Pipeline([_DetectorFijo(potencial)])
    tuberia.registrar(_DetectorFijo(comprobado))
    assert isinstance(_DetectorFijo(), Detector)
    assert tuberia.ejecutar(Ruta("proyecto")) == [comprobado, potencial]


def test_tuberia_no_traga_el_error_de_un_detector():
    from agentreach.core.pipeline import Pipeline

    with pytest.raises(RuntimeError, match="_DetectorRoto") as info:
        Pipeline([_DetectorRoto()]).ejecutar(Ruta("proyecto"))
    assert isinstance(info.value.__cause__, ValueError)


def test_orden_por_tipo_es_numerico():
    th12 = hallazgo(tipo=Tipo.TEXTO_INVISIBLE)
    th2 = hallazgo(tipo=Tipo.CLAVE_PRIVADA_SSH)
    assert ordenar([th12, th2]) == [th2, th12]
