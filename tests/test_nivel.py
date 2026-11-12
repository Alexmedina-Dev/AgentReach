"""Historia 11: cálculo del nivel de confianza, invariantes, contraejemplos y confirmación independiente."""

from __future__ import annotations

import dataclasses
import itertools
import os
import sys
from pathlib import Path

import pytest

from agentreach.contracts import (
    Ajeno,
    Certeza,
    Etiqueta,
    Finding,
    Linea,
    Location,
    Motivo,
    Nivel,
    PermisoLectura,
    PermisosArchivo,
    Plataforma,
    Postura,
    Proveedor,
    Ruta,
    Tipo,
)
from agentreach.core.evaluador import Evaluador
from agentreach.core.invariantes import MOTIVOS_POTENCIAL, Violacion, comprobar
from agentreach.core.nivel import Hechos, calcular
from agentreach.core.politica import BASE_POR_TIPO, NIVEL_MAXIMO, Base, base_de, es_mayor, maximo_de
from agentreach.core.verificacion_independiente import Confirmacion

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

# ---- piezas falsas -----------------------------------------------------------------------------------------------------


def permisos(permiso=PermisoLectura.SI, abierto=False, ambiguo=False) -> PermisosArchivo:
    return PermisosArchivo(permiso, abierto, ambiguo, "usuario", "icacls ruta")


class SondaFalsa:
    def __init__(self, resultado: PermisosArchivo | None = None, error: Exception | None = None) -> None:
        self.resultado, self.error, self.llamadas = resultado or permisos(), error, 0

    def evaluar(self, ruta: Ruta) -> PermisosArchivo:
        self.llamadas += 1
        if self.error is not None:
            raise self.error
        return self.resultado


class AdaptadorFalso:
    def __init__(self, plataforma: Plataforma, postura: Postura = Postura.SIN_REGLA, regla: Location | None = None) -> None:
        self.plataforma, self._postura, self._regla = plataforma, postura, regla

    def postura_para(self, ruta: Ruta) -> Postura:
        return self._postura

    def regla_para(self, ruta: Ruta) -> Location | None:
        return self._regla


def hechos(**cambios) -> Hechos:
    """Hechos de un archivo comprobable: existe, legible, sin regla, sin ambigüedad."""
    base = Hechos(existe=True, permiso=permisos(), postura=Postura.SIN_REGLA)
    return dataclasses.replace(base, **cambios)


def candidato(tipo: Tipo = Tipo.CREDENCIAL_EN_ARCHIVO, ruta: str = "x.env", **extra) -> Finding:
    datos = {
        "ubicacion": Location(Ruta(ruta), 2), "tipo": tipo, "proveedor": Proveedor.DESCONOCIDO,
        "nivel": Nivel.HIPOTESIS, "motivo": Motivo.NO_DETERMINADO, "ajeno_a_tarea": Ajeno.NO_DETERMINADO,
        "plataforma": Plataforma.NO_DETERMINADA, "agente": Etiqueta("sin-agente"), "postura": Postura.NO_DETERMINADA,
    }
    datos.update(extra)
    return Finding(**datos)


def evaluador(sonda=None, verificador="sin", adaptadores=None, existe=True) -> Evaluador:
    if adaptadores is None:
        adaptadores = [AdaptadorFalso(Plataforma.CLAUDE_CODE)]
    return Evaluador(sonda or SondaFalsa(), None if verificador == "sin" else verificador, adaptadores, lambda r: existe)


TIPOS_DE_ARCHIVO = [t for t in Tipo if base_de(t) in (Base.ARCHIVO, Base.POR_NOMBRE, Base.BYTES)]


# ---- la política: una fila por tipo ----------------------------------------------------------------------------------


def test_cada_tipo_tiene_su_base_y_su_nivel_maximo():
    assert set(BASE_POR_TIPO) == set(Tipo) == set(NIVEL_MAXIMO)


@pytest.mark.parametrize("tipo", [Tipo.CONTEXTO_SOSPECHOSO, Tipo.SCRIPT_DE_DESPLIEGUE])
def test_th5_y_th9_no_pasan_de_hipotesis(tipo):
    assert maximo_de(tipo) is Nivel.HIPOTESIS and base_de(tipo) is Base.INDICIO
    d = calcular(tipo, hechos())
    assert (d.nivel, d.motivo) == (Nivel.HIPOTESIS, Motivo.INDICIO_DEBIL)


@pytest.mark.parametrize("tipo", [Tipo.CLAVE_PRIVADA_SSH, Tipo.CREDENCIALES_DE_NUBE, Tipo.ENLACE_FUERA_DEL_PROYECTO,
                                  Tipo.REGLA_PERMISIVA, Tipo.CAPACIDAD_DE_SHELL, Tipo.PLATAFORMA_SIN_SANDBOX])
def test_los_tipos_con_tope_potencial_no_pasan_de_potencial(tipo):  # pregunta 23
    assert maximo_de(tipo) is Nivel.POTENCIAL
    assert calcular(tipo, hechos()).nivel is Nivel.POTENCIAL


def test_el_nivel_nunca_supera_el_maximo_del_tipo_con_ningun_hecho():
    posturas, certezas = list(Postura), list(Certeza)
    for tipo in Tipo:
        for existe, perm, postura, certeza, conf in itertools.product(
            (True, False),
            (None, permisos(), permisos(PermisoLectura.NO), permisos(PermisoLectura.NO_DETERMINADO), permisos(ambiguo=True)),
            posturas, certezas, (None, Confirmacion.CONFIRMADO, Confirmacion.NO_CONFIRMADO),
        ):
            d = calcular(tipo, Hechos(existe, perm, postura, certeza, conf))
            assert not es_mayor(d.nivel, maximo_de(tipo)), (tipo, d)


# ---- (iv-a) una prueba por cada fila de la tabla de FR-5 -----------------------------------------------------------------


def test_fila_comprobado_existe_legible_y_sin_regla():
    assert calcular(Tipo.CREDENCIAL_EN_ARCHIVO, hechos()) == (Nivel.COMPROBADO, Motivo.EXISTE_LEGIBLE_SIN_REGLA) or \
        calcular(Tipo.CREDENCIAL_EN_ARCHIVO, hechos()).nivel is Nivel.COMPROBADO


def test_comprobado_con_o_sin_una_regla_allow_explicita():
    for postura in (Postura.SIN_REGLA, Postura.ALLOW):
        d = calcular(Tipo.CREDENCIAL_EN_ARCHIVO, hechos(postura=postura))
        assert (d.nivel, d.motivo) == (Nivel.COMPROBADO, Motivo.EXISTE_LEGIBLE_SIN_REGLA)


@pytest.mark.parametrize("cambio", [
    {"permiso": None}, {"permiso": permisos(PermisoLectura.NO_DETERMINADO)},
    {"postura": Postura.NO_DETERMINADA}, {"existe": False},
])
def test_fila_potencial_no_determinado(cambio):
    d = calcular(Tipo.CREDENCIAL_EN_ARCHIVO, hechos(**cambio))
    assert (d.nivel, d.motivo) == (Nivel.POTENCIAL, Motivo.NO_DETERMINADO)


def test_fila_potencial_regla_deny():
    d = calcular(Tipo.CREDENCIAL_EN_ARCHIVO, hechos(postura=Postura.DENY))
    assert (d.nivel, d.motivo) == (Nivel.POTENCIAL, Motivo.REGLA_DENY)


def test_fila_potencial_regla_ask():
    d = calcular(Tipo.CREDENCIAL_EN_ARCHIVO, hechos(postura=Postura.ASK))
    assert (d.nivel, d.motivo) == (Nivel.POTENCIAL, Motivo.REGLA_ASK)


def test_fila_potencial_existe_y_no_se_puede_leer():
    d = calcular(Tipo.CREDENCIAL_EN_ARCHIVO, hechos(permiso=permisos(PermisoLectura.NO)))
    assert (d.nivel, d.motivo) == (Nivel.POTENCIAL, Motivo.EXISTE_NO_LEGIBLE)


def test_fila_potencial_sin_fuente_verificada_al_reconocer_por_nombre():
    d = calcular(Tipo.SECRETO_DE_ALTO_PODER, hechos())
    assert (d.nivel, d.motivo) == (Nivel.POTENCIAL, Motivo.SIN_FUENTE_VERIFICADA)


def test_fila_hipotesis_indicio_debil():
    d = calcular(Tipo.CONTEXTO_SOSPECHOSO, hechos())
    assert (d.nivel, d.motivo) == (Nivel.HIPOTESIS, Motivo.INDICIO_DEBIL)


# ---- las cuatro reglas fijadas por Alex --------------------------------------------------------------------------------


def test_regla_1_la_herencia_no_baja_el_nivel():
    """El permiso heredado llega como un permiso normal y no ambiguo: PP-04 y PA-01 siguen comprobados."""
    d = calcular(Tipo.CREDENCIAL_EN_ARCHIVO, hechos(permiso=permisos(abierto=False, ambiguo=False)))
    assert d.nivel is Nivel.COMPROBADO


@pytest.mark.parametrize("ambiguo_por", ["regla de denegar", "ACL no estandar", "calculo incompleto"])
def test_regla_1_solo_baja_lo_ambiguo(ambiguo_por):
    d = calcular(Tipo.CREDENCIAL_EN_ARCHIVO, hechos(permiso=permisos(ambiguo=True)))
    assert (d.nivel, d.motivo) == (Nivel.POTENCIAL, Motivo.SIN_CERTEZA_DEL_ARCHIVO), ambiguo_por


@pytest.mark.parametrize("tipo", TIPOS_DE_ARCHIVO)
def test_regla_2_un_deny_solo_baja_a_potencial(tipo):
    d = calcular(tipo, hechos(postura=Postura.DENY))
    assert d.nivel is Nivel.POTENCIAL and d.motivo is Motivo.REGLA_DENY  # ni hipótesis ni se borra


def test_regla_3_la_verificacion_independiente_baja_si_discrepa_o_no_puede():
    d = calcular(Tipo.CREDENCIAL_EN_ARCHIVO, hechos(confirmacion=Confirmacion.NO_CONFIRMADO))
    assert (d.nivel, d.motivo) == (Nivel.POTENCIAL, Motivo.NO_CONFIRMADO_INDEPENDIENTE)
    assert calcular(Tipo.CREDENCIAL_EN_ARCHIVO, hechos(confirmacion=Confirmacion.CONFIRMADO)).nivel is Nivel.COMPROBADO


def test_regla_4_por_nombre_o_prefijo_sin_fuente_verificada_no_pasa_de_potencial():
    """Propiedad: ningún hecho, por favorable que sea, deja un tipo por nombre en comprobado."""
    por_nombre = [t for t in Tipo if base_de(t) is Base.POR_NOMBRE]
    assert por_nombre  # TH-17
    for tipo in por_nombre:
        for perm, postura, certeza, conf in itertools.product(
            (permisos(), permisos(abierto=True)), list(Postura), list(Certeza), (None, Confirmacion.CONFIRMADO)
        ):
            assert calcular(tipo, Hechos(True, perm, postura, certeza, conf)).nivel is not Nivel.COMPROBADO


def test_regla_4_con_fuente_verificada_el_tipo_por_nombre_si_podria_subir(monkeypatch):
    """Lo que limita es la marca, no el tipo: con la fuente verificada y sin tope del tipo, sube."""
    from agentreach.contracts import finding as f
    from agentreach.core import nivel as n
    from agentreach.core import politica as p

    monkeypatch.setitem(f.FUENTE_VERIFICADA, Tipo.SECRETO_DE_ALTO_PODER, True)
    monkeypatch.setitem(p.NIVEL_MAXIMO, Tipo.SECRETO_DE_ALTO_PODER, Nivel.COMPROBADO)
    assert n.calcular(Tipo.SECRETO_DE_ALTO_PODER, hechos()).nivel is Nivel.COMPROBADO


# ---- (b2) certeza ------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("tipo", [Tipo.CREDENCIAL_EN_ARCHIVO, Tipo.GIT_REMOTO_SOSPECHOSO])
def test_certeza_dudosa_deja_potencial(tipo):
    d = calcular(tipo, hechos(certeza=Certeza.DUDOSA))
    assert (d.nivel, d.motivo) == (Nivel.POTENCIAL, Motivo.SIN_CERTEZA_DEL_ARCHIVO)
    assert calcular(tipo, hechos()).nivel is Nivel.COMPROBADO


# ---- (i) invariantes ---------------------------------------------------------------------------------------------------


def _comprobado(tipo=Tipo.CREDENCIAL_EN_ARCHIVO) -> Finding:
    return candidato(tipo, nivel=Nivel.COMPROBADO, motivo=Motivo.EXISTE_LEGIBLE_SIN_REGLA)


def test_un_comprobado_correcto_no_viola_nada():
    assert comprobar(_comprobado(), hechos()) == ()


def test_un_comprobado_sin_hechos_se_rechaza():
    assert comprobar(_comprobado()) == (Violacion.COMPROBADO_SIN_HECHOS,)


@pytest.mark.parametrize("cambio, esperada", [
    ({"existe": False}, Violacion.COMPROBADO_SIN_ARCHIVO),  # hecho 1
    ({"permiso": permisos(PermisoLectura.NO)}, Violacion.COMPROBADO_SIN_PERMISO),  # hecho 2
    ({"permiso": None}, Violacion.COMPROBADO_SIN_PERMISO),
    ({"postura": Postura.DENY}, Violacion.COMPROBADO_CON_REGLA),  # hecho 3
    ({"postura": Postura.ASK}, Violacion.COMPROBADO_CON_REGLA),
    ({"postura": Postura.NO_DETERMINADA}, Violacion.COMPROBADO_REGLA_NO_DETERMINADA),
    ({"permiso": permisos(ambiguo=True)}, Violacion.COMPROBADO_AMBIGUO),
    ({"certeza": Certeza.DUDOSA}, Violacion.COMPROBADO_AMBIGUO),
    ({"confirmacion": Confirmacion.NO_CONFIRMADO}, Violacion.COMPROBADO_SIN_CONFIRMAR),
])
def test_un_comprobado_al_que_le_falta_un_hecho_se_rechaza(cambio, esperada):
    assert esperada in comprobar(_comprobado(), hechos(**cambio))


def test_un_comprobado_con_el_motivo_equivocado_se_rechaza():
    h = dataclasses.replace(_comprobado(), motivo=Motivo.NO_DETERMINADO)
    assert Violacion.COMPROBADO_MOTIVO_INCORRECTO in comprobar(h, hechos())


def test_un_potencial_sin_ninguno_de_sus_motivos_se_rechaza():
    for motivo in Motivo:
        h = candidato(nivel=Nivel.POTENCIAL, motivo=motivo)
        assert (Violacion.POTENCIAL_SIN_MOTIVO in comprobar(h)) == (motivo not in MOTIVOS_POTENCIAL)


def test_una_hipotesis_sin_indicio_se_rechaza():
    assert Violacion.HIPOTESIS_SIN_INDICIO in comprobar(candidato(Tipo.CONTEXTO_SOSPECHOSO, nivel=Nivel.HIPOTESIS, motivo=Motivo.NO_DETERMINADO))
    assert comprobar(candidato(Tipo.CONTEXTO_SOSPECHOSO, nivel=Nivel.HIPOTESIS, motivo=Motivo.INDICIO_DEBIL)) == ()


@pytest.mark.parametrize("tipo, nivel", [
    (Tipo.CONTEXTO_SOSPECHOSO, Nivel.POTENCIAL), (Tipo.SCRIPT_DE_DESPLIEGUE, Nivel.POTENCIAL),
    (Tipo.CONTEXTO_SOSPECHOSO, Nivel.COMPROBADO), (Tipo.CLAVE_PRIVADA_SSH, Nivel.COMPROBADO),
    (Tipo.REGLA_PERMISIVA, Nivel.COMPROBADO),
])
def test_un_hallazgo_por_encima_del_maximo_de_su_tipo_se_rechaza(tipo, nivel):
    h = candidato(tipo, nivel=nivel, motivo=Motivo.NO_DETERMINADO)
    assert Violacion.SUPERA_EL_MAXIMO_DEL_TIPO in comprobar(h, hechos())


def test_un_comprobado_reconocido_por_nombre_sin_fuente_se_rechaza(monkeypatch):
    from agentreach.core import politica as p

    monkeypatch.setitem(p.NIVEL_MAXIMO, Tipo.SECRETO_DE_ALTO_PODER, Nivel.COMPROBADO)  # solo se prueba la marca
    h = _comprobado(Tipo.SECRETO_DE_ALTO_PODER)
    assert Violacion.COMPROBADO_SIN_FUENTE in comprobar(h, hechos())


def test_un_tipo_que_no_se_apoya_en_un_hecho_medido_no_puede_ser_comprobado():
    h = candidato(Tipo.REGLA_PERMISIVA, nivel=Nivel.COMPROBADO, motivo=Motivo.EXISTE_LEGIBLE_SIN_REGLA)
    assert Violacion.COMPROBADO_SIN_BASE in comprobar(h, hechos())


def test_comprobar_acepta_todo_lo_que_calcula_nivel():
    """Coherencia entre las dos piezas: lo que ``calcular`` entrega, ``comprobar`` lo acepta."""
    for tipo in Tipo:
        for existe, perm, postura, certeza, conf in itertools.product(
            (True, False), (None, permisos(), permisos(PermisoLectura.NO), permisos(ambiguo=True)),
            list(Postura), list(Certeza), (None, Confirmacion.NO_CONFIRMADO),
        ):
            hs = Hechos(existe, perm, postura, certeza, conf)
            d = calcular(tipo, hs)
            assert comprobar(candidato(tipo, nivel=d.nivel, motivo=d.motivo), hs) == (), (tipo, hs, d)


# ---- (ii) contraejemplo mínimo por cada tipo que puede salir comprobado ----------------------------------------------


TIPOS_COMPROBABLES = [t for t in Tipo if maximo_de(t) is Nivel.COMPROBADO]

CONTRAEJEMPLOS = [
    ("deny", {"postura": Postura.DENY}, Motivo.REGLA_DENY),
    ("ask", {"postura": Postura.ASK}, Motivo.REGLA_ASK),
    ("borrar el archivo", {"existe": False}, Motivo.NO_DETERMINADO),
    ("hecho ambiguo", {"certeza": Certeza.DUDOSA}, Motivo.SIN_CERTEZA_DEL_ARCHIVO),
]
SOLO_ARCHIVO = [
    ("negar la lectura", {"permiso": permisos(PermisoLectura.NO)}, Motivo.EXISTE_NO_LEGIBLE),
    ("permiso ambiguo", {"permiso": permisos(ambiguo=True)}, Motivo.SIN_CERTEZA_DEL_ARCHIVO),
    ("no se puede confirmar", {"confirmacion": Confirmacion.NO_CONFIRMADO}, Motivo.NO_CONFIRMADO_INDEPENDIENTE),
]


def test_los_tipos_comprobables_son_los_esperados():
    # Historia 27: TH-1 (credencial reconocida solo por su nombre) ya no llega a comprobado
    assert {t.value for t in TIPOS_COMPROBABLES} == {"TH-12", "TH-13", "TH-18", "TH-19"}


@pytest.mark.parametrize("tipo", TIPOS_COMPROBABLES)
def test_contraejemplo_minimo_baja_el_nivel_con_la_razon_correcta(tipo):
    assert calcular(tipo, hechos()).nivel is Nivel.COMPROBADO  # se parte de un comprobado real
    casos = CONTRAEJEMPLOS + (SOLO_ARCHIVO if base_de(tipo) is Base.ARCHIVO else [])
    for nombre, cambio, motivo in casos:
        d = calcular(tipo, hechos(**cambio))
        assert (d.nivel, d.motivo) == (Nivel.POTENCIAL, motivo), (tipo, nombre)


def test_contraejemplo_quitar_la_fuente_verificada_baja_un_tipo_por_nombre(monkeypatch):
    from agentreach.contracts import finding as f
    from agentreach.core import nivel as n
    from agentreach.core import politica as p

    monkeypatch.setitem(p.NIVEL_MAXIMO, Tipo.SECRETO_DE_ALTO_PODER, Nivel.COMPROBADO)
    monkeypatch.setitem(f.FUENTE_VERIFICADA, Tipo.SECRETO_DE_ALTO_PODER, True)
    assert n.calcular(Tipo.SECRETO_DE_ALTO_PODER, hechos()).nivel is Nivel.COMPROBADO
    monkeypatch.setitem(f.FUENTE_VERIFICADA, Tipo.SECRETO_DE_ALTO_PODER, False)
    d = n.calcular(Tipo.SECRETO_DE_ALTO_PODER, hechos())
    assert (d.nivel, d.motivo) == (Nivel.POTENCIAL, Motivo.SIN_FUENTE_VERIFICADA)


# ---- el evaluador: hechos medidos, un hallazgo por agente, confirmación independiente ---------------------------------


def test_un_deny_conserva_el_hallazgo_con_la_regla_citada():
    regla = Location(Ruta("settings.json"), 7)
    ev = evaluador(adaptadores=[AdaptadorFalso(Plataforma.CLAUDE_CODE, Postura.DENY, regla)])
    [h] = ev.evaluar([candidato()])
    assert (h.nivel, h.motivo, h.postura, h.regla) == (Nivel.POTENCIAL, Motivo.REGLA_DENY, Postura.DENY, regla)


def test_nivel_por_agente_un_env_potencial_para_uno_y_comprobado_para_otro():
    ev = evaluador(adaptadores=[
        AdaptadorFalso(Plataforma.CLAUDE_CODE, Postura.DENY, Location(Ruta("s.json"), 3)),
        AdaptadorFalso(Plataforma.OPENCODE, Postura.ALLOW),
    ])
    por_agente = {h.agente: h for h in ev.evaluar([candidato()])}
    assert set(por_agente) == {"claude-code", "opencode"}
    assert por_agente["claude-code"].nivel is Nivel.POTENCIAL and por_agente["claude-code"].plataforma is Plataforma.CLAUDE_CODE
    assert por_agente["opencode"].nivel is Nivel.COMPROBADO and por_agente["opencode"].plataforma is Plataforma.OPENCODE


def test_sin_adaptadores_la_regla_queda_no_determinada():
    [h] = evaluador(adaptadores=[]).evaluar([candidato()])
    assert (h.nivel, h.motivo) == (Nivel.POTENCIAL, Motivo.NO_DETERMINADO)


def test_un_hallazgo_que_ya_es_de_un_agente_solo_se_mide_para_ese():
    ev = evaluador(adaptadores=[AdaptadorFalso(Plataforma.CLAUDE_CODE), AdaptadorFalso(Plataforma.OPENCODE)])
    [h] = ev.evaluar([candidato(Tipo.REGLA_PERMISIVA, plataforma=Plataforma.OPENCODE, agente=Etiqueta("opencode"))])
    assert h.plataforma is Plataforma.OPENCODE and h.nivel is Nivel.POTENCIAL  # TH-7: tope potencial


def test_la_confirmacion_independiente_que_discrepa_baja_a_potencial():
    principal = SondaFalsa(permisos(PermisoLectura.SI))
    verificador = SondaFalsa(permisos(PermisoLectura.NO))  # discrepa
    [h] = evaluador(sonda=principal, verificador=verificador).evaluar([candidato()])
    assert (h.nivel, h.motivo) == (Nivel.POTENCIAL, Motivo.NO_CONFIRMADO_INDEPENDIENTE)


@pytest.mark.parametrize("verificador", [
    SondaFalsa(permisos(PermisoLectura.NO_DETERMINADO)), SondaFalsa(error=OSError("x")),
])
def test_la_confirmacion_que_no_puede_determinar_o_falla_baja_a_potencial(verificador):
    [h] = evaluador(verificador=verificador).evaluar([candidato()])
    assert (h.nivel, h.motivo) == (Nivel.POTENCIAL, Motivo.NO_CONFIRMADO_INDEPENDIENTE)


def test_la_confirmacion_que_coincide_deja_comprobado_y_se_pide_una_vez_por_archivo():
    verificador = SondaFalsa(permisos())
    ev = evaluador(verificador=verificador, adaptadores=[AdaptadorFalso(Plataforma.CLAUDE_CODE), AdaptadorFalso(Plataforma.OPENCODE)])
    salida = ev.evaluar([candidato()])
    assert [h.nivel for h in salida] == [Nivel.COMPROBADO, Nivel.COMPROBADO]
    assert verificador.llamadas == 1


def test_la_confirmacion_no_se_pide_si_el_nivel_ya_bajo_o_no_depende_del_permiso():
    verificador = SondaFalsa(permisos())
    evaluador(verificador=verificador, adaptadores=[AdaptadorFalso(Plataforma.CLAUDE_CODE, Postura.DENY)]).evaluar([candidato()])
    evaluador(verificador=verificador).evaluar([candidato(Tipo.TEXTO_INVISIBLE)])  # un hecho de los bytes
    assert verificador.llamadas == 0


def test_una_sonda_que_falla_o_devuelve_otra_cosa_deja_no_determinado_sin_lanzar():
    for sonda in (SondaFalsa(error=RuntimeError("x")), SondaFalsa(error=OSError("y"))):
        [h] = evaluador(sonda=sonda).evaluar([candidato()])
        assert (h.nivel, h.motivo) == (Nivel.POTENCIAL, Motivo.NO_DETERMINADO)
    malo = SondaFalsa()
    malo.resultado = "texto"  # type: ignore[assignment]
    [h] = evaluador(sonda=malo).evaluar([candidato()])
    assert h.nivel is Nivel.POTENCIAL


def test_un_adaptador_que_falla_deja_la_regla_no_determinada_sin_lanzar():
    class Roto(AdaptadorFalso):
        def postura_para(self, ruta):
            raise RuntimeError("x")

    [h] = evaluador(adaptadores=[Roto(Plataforma.CLAUDE_CODE)]).evaluar([candidato()])
    assert (h.nivel, h.motivo, h.postura) == (Nivel.POTENCIAL, Motivo.NO_DETERMINADO, Postura.NO_DETERMINADA)


def test_el_archivo_borrado_baja_de_nivel():
    [h] = evaluador(existe=False).evaluar([candidato()])
    assert h.nivel is Nivel.POTENCIAL


def test_un_hecho_de_los_bytes_no_mide_el_permiso():
    sonda = SondaFalsa()
    [h] = evaluador(sonda=sonda).evaluar([candidato(Tipo.TEXTO_INVISIBLE)])
    assert h.nivel is Nivel.COMPROBADO and sonda.llamadas == 0


def test_cualquier_hallazgo_evaluado_pasa_las_invariantes():
    ev = evaluador(adaptadores=[AdaptadorFalso(Plataforma.CLAUDE_CODE), AdaptadorFalso(Plataforma.OPENCODE, Postura.ASK)])
    for tipo in Tipo:
        for h in ev.evaluar([candidato(tipo)]):
            assert not es_mayor(h.nivel, maximo_de(h.tipo))
            if h.nivel is not Nivel.COMPROBADO:
                assert comprobar(h) == ()


# ---- detectores: lo dudoso lo marca el detector ----------------------------------------------------------------------


def _proyecto_git(tmp_path: Path, config: str, hooks: dict[str, str] | None = None) -> Path:
    git = tmp_path / ".git"
    (git / "hooks").mkdir(parents=True)
    (git / "config").write_text(config, encoding="utf-8")
    for nombre, texto in (hooks or {}).items():
        (git / "hooks" / nombre).write_text(texto, encoding="utf-8")
    return tmp_path


def _certezas(proyecto: Path) -> dict[Tipo, list[Certeza]]:
    from agentreach.collectors.git_meta import DetectorGit
    from agentreach.infra.fs_solo_lectura import FsSoloLectura

    salida: dict[Tipo, list[Certeza]] = {}
    for h in DetectorGit(FsSoloLectura(str(proyecto))).detectar(Ruta(str(proyecto))):
        salida.setdefault(h.tipo, []).append(h.certeza)
    return salida


def test_git_clave_literal_en_el_remoto_es_certeza_completa_y_el_relleno_es_dudoso(tmp_path: Path):
    real = _proyecto_git(tmp_path / "a", '[remote "origin"]\n\turl = https://ana:s3cr3t-LARGO-9f2k@host.invalid/x.git\n')
    relleno = _proyecto_git(tmp_path / "b", '[remote "origin"]\n\turl = https://ana:TOKEN@host.invalid/x.git\n')
    assert _certezas(real)[Tipo.GIT_REMOTO_SOSPECHOSO] == [Certeza.COMPLETA]  # GT-03
    assert _certezas(relleno)[Tipo.GIT_REMOTO_SOSPECHOSO] == [Certeza.DUDOSA]  # GT-08


def test_git_un_programa_en_la_configuracion_es_cierto_pero_hooks_path_y_hooks_son_dudosos(tmp_path: Path):
    fsmonitor = _proyecto_git(tmp_path / "a", "[core]\n\tfsmonitor = ./senuelo.cmd\n")
    husky = _proyecto_git(tmp_path / "b", "[core]\n\thooksPath = .husky\n")
    hook = _proyecto_git(tmp_path / "c", "[core]\n\tbare = false\n", {"post-checkout": "x"})
    assert _certezas(fsmonitor)[Tipo.GIT_EJECUTA_PROGRAMAS] == [Certeza.COMPLETA]  # GT-04
    assert _certezas(husky)[Tipo.GIT_EJECUTA_PROGRAMAS] == [Certeza.DUDOSA]  # GT-05
    assert _certezas(hook)[Tipo.GIT_EJECUTA_PROGRAMAS] == [Certeza.DUDOSA]  # GT-07


# ---- auditar de punta a punta con sondas falsas ----------------------------------------------------------------------


def _auditar(carpeta: Path, sonda, verificador=None):
    from agentreach.app.auditar import auditar
    from agentreach.config import Configuracion

    return auditar(str(carpeta), Configuracion(), medidores=(sonda, verificador))


def test_auditar_calcula_el_nivel_real_por_agente(tmp_path: Path):
    (tmp_path / ".env").write_text("STRIPE_SECRET_KEY=sk_live_algo_largo_123\n", encoding="utf-8")
    (tmp_path / "notas.txt").write_text("RAILWAY_API_TOKEN=abcdef123456\n", encoding="utf-8")
    r = _auditar(tmp_path, SondaFalsa(), SondaFalsa())
    env = [h for h in r.hallazgos if h.tipo is Tipo.CREDENCIAL_EN_ARCHIVO]
    assert {h.agente for h in env} == {"claude-code", "opencode"}
    assert all(h.nivel in (Nivel.COMPROBADO, Nivel.POTENCIAL) for h in env)
    alto = [h for h in r.hallazgos if h.tipo is Tipo.SECRETO_DE_ALTO_PODER]
    assert alto and all((h.nivel, h.motivo) == (Nivel.POTENCIAL, Motivo.SIN_FUENTE_VERIFICADA) for h in alto)  # AT-08
    assert not [h for h in r.hallazgos if h.nivel is Nivel.COMPROBADO and h.motivo is not Motivo.EXISTE_LEGIBLE_SIN_REGLA]


def test_auditar_con_la_lectura_negada_deja_potencial_no_legible(tmp_path: Path):  # PP-03
    (tmp_path / ".env.production").write_text("API_TOKEN=valor-largo-123\n", encoding="utf-8")
    r = _auditar(tmp_path, SondaFalsa(permisos(PermisoLectura.NO)), SondaFalsa(permisos(PermisoLectura.NO)))
    env = {h.agente: h for h in r.hallazgos if h.tipo is Tipo.CREDENCIAL_EN_ARCHIVO}
    assert (env["claude-code"].nivel, env["claude-code"].motivo) == (Nivel.POTENCIAL, Motivo.EXISTE_NO_LEGIBLE)
    # opencode pregunta antes de leer *.env (política base): el ask se dice antes que lo no legible
    assert (env["opencode"].nivel, env["opencode"].motivo) == (Nivel.POTENCIAL, Motivo.REGLA_ASK)


def test_auditar_con_un_verificador_que_discrepa_baja_a_potencial(tmp_path: Path):  # PA-01, PP-04, PP-05
    (tmp_path / ".env.staging").write_text("API_TOKEN=valor-largo-123\n", encoding="utf-8")
    r = _auditar(tmp_path, SondaFalsa(permisos()), SondaFalsa(permisos(PermisoLectura.NO)))
    env = {h.agente: h for h in r.hallazgos if h.tipo is Tipo.CREDENCIAL_EN_ARCHIVO}
    assert (env["claude-code"].nivel, env["claude-code"].motivo) == (Nivel.POTENCIAL, Motivo.NO_CONFIRMADO_INDEPENDIENTE)


def test_auditar_el_texto_del_reporte_nunca_lleva_valores(tmp_path: Path):
    (tmp_path / ".env").write_text("STRIPE_SECRET_KEY=CANARIO-123456-ABCDEF\n", encoding="utf-8")
    r = _auditar(tmp_path, SondaFalsa(), SondaFalsa())
    assert "CANARIO" not in repr(r)


# ---- con el proyecto de prueba y las sondas reales (Windows) ---------------------------------------------------------


@pytest.fixture
def proyecto_prueba() -> Path:
    raiz = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")
    if not raiz or not (Path(raiz) / "proyecto").is_dir():
        pytest.skip("AGENTREACH_PROYECTO_PRUEBA no apunta al proyecto de prueba")
    return Path(raiz)


def _real(carpeta: Path):
    from agentreach.app.auditar import auditar
    from agentreach.config import Configuracion

    return auditar(str(carpeta), Configuracion())


def _nivel(r, sufijo: str, tipo: Tipo, agente: str) -> tuple[Nivel, Motivo]:
    [h] = [h for h in r.hallazgos if h.tipo is tipo and h.agente == agente
           and str(h.ubicacion.ruta).replace("\\", "/").endswith(sufijo)]
    return h.nivel, h.motivo


@pytest.mark.skipif(sys.platform != "win32", reason="las sondas reales del permiso son de Windows")
def test_casos_del_oraculo_con_las_sondas_reales(proyecto_prueba: Path):
    r = _real(proyecto_prueba / "proyecto")
    T1 = Tipo.CREDENCIAL_EN_ARCHIVO
    comprobado = (Nivel.COMPROBADO, Motivo.EXISTE_LEGIBLE_SIN_REGLA)
    for agente in ("claude-code", "opencode"):
        assert _nivel(r, "proyecto/.env.staging", T1, agente) == comprobado  # PP-04
        assert _nivel(r, "proyecto/.env.local", T1, agente) == comprobado  # PP-05
        assert _nivel(r, "config/servicio-rastreado.env", T1, agente) == comprobado  # GT-01
        assert _nivel(r, "config/exportacion-abierta.env", T1, agente) == comprobado  # PA-01
        assert _nivel(r, "proyecto/.env.production", T1, agente) == (Nivel.POTENCIAL, Motivo.EXISTE_NO_LEGIBLE)  # PP-03
        assert _nivel(r, "src/estilos/notas-tipografia.txt", Tipo.SECRETO_DE_ALTO_PODER, agente) == (
            Nivel.POTENCIAL, Motivo.SIN_FUENTE_VERIFICADA)  # AT-08
    pp01 = [h for h in r.hallazgos if h.tipo is T1 and str(h.ubicacion.ruta).replace("\\", "/").endswith("proyecto/.env")]
    claude = [h for h in pp01 if h.agente == "claude-code"]
    assert claude and all((h.nivel, h.motivo) == (Nivel.POTENCIAL, Motivo.REGLA_DENY) for h in claude)  # PP-01
    assert all(h.nivel is Nivel.COMPROBADO for h in pp01 if h.agente == "opencode")  # el read: allow gana


@pytest.mark.skipif(sys.platform != "win32", reason="las sondas reales del permiso son de Windows")
def test_git_del_oraculo_con_las_sondas_reales(proyecto_prueba: Path):
    gt03 = _real(proyecto_prueba / "proyecto")
    assert [h.nivel for h in gt03.hallazgos if h.tipo is Tipo.GIT_REMOTO_SOSPECHOSO] == [Nivel.COMPROBADO] * 2  # GT-03
    gt08 = _real(proyecto_prueba / "trampas-git" / "remoto-relleno")
    remotos = [h for h in gt08.hallazgos if h.tipo is Tipo.GIT_REMOTO_SOSPECHOSO]
    assert remotos and all((h.nivel, h.motivo) == (Nivel.POTENCIAL, Motivo.SIN_CERTEZA_DEL_ARCHIVO) for h in remotos)  # GT-08
    gt04 = _real(proyecto_prueba / "trampas-git" / "fsmonitor-malo")
    assert any(h.tipo is Tipo.GIT_EJECUTA_PROGRAMAS and h.nivel is Nivel.COMPROBADO for h in gt04.hallazgos)  # GT-04
    gt05 = _real(proyecto_prueba / "trampas-git" / "hookspath-dentro")
    assert any(h.tipo is Tipo.GIT_EJECUTA_PROGRAMAS and h.nivel is Nivel.POTENCIAL for h in gt05.hallazgos)  # GT-05


@pytest.mark.skipif(sys.platform != "win32", reason="el verificador real es de Windows")
def test_con_el_verificador_real_coinciden_y_siguen_comprobados(tmp_path: Path):
    from agentreach.app.auditar import auditar
    from agentreach.config import Configuracion

    (tmp_path / ".env.staging").write_text("API_TOKEN=valor-largo-123\n", encoding="utf-8")
    r = auditar(str(tmp_path), Configuracion())
    env = [h for h in r.hallazgos if h.tipo is Tipo.CREDENCIAL_EN_ARCHIVO]
    assert env and all(h.nivel is Nivel.COMPROBADO for h in env if h.agente == "claude-code")


def test_linea_no_determinada_sigue_siendo_valida_en_el_hallazgo_evaluado():
    [h] = evaluador().evaluar([candidato(ubicacion=Location(Ruta("x.env"), Linea.NO_DETERMINADA))])
    assert h.ubicacion.linea is Linea.NO_DETERMINADA


# ---- parches de la revisión ----------------------------------------------------------------------------------------


def test_un_adaptador_que_devuelve_algo_que_no_es_una_postura_no_deja_pasar_un_hecho_de_los_bytes():
    class Raro(AdaptadorFalso):
        def postura_para(self, ruta):
            return None

    [h] = evaluador(adaptadores=[Raro(Plataforma.CLAUDE_CODE)]).evaluar([candidato(Tipo.GIT_REMOTO_SOSPECHOSO)])
    assert (h.nivel, h.motivo) == (Nivel.POTENCIAL, Motivo.NO_DETERMINADO)


def test_si_solo_falla_citar_la_regla_el_deny_no_se_pierde():
    class SinRegla(AdaptadorFalso):
        def regla_para(self, ruta):
            raise RuntimeError("x")

    [h] = evaluador(adaptadores=[SinRegla(Plataforma.CLAUDE_CODE, Postura.DENY)]).evaluar([candidato(Tipo.GIT_REMOTO_SOSPECHOSO)])
    assert (h.nivel, h.motivo, h.regla) == (Nivel.POTENCIAL, Motivo.REGLA_DENY, None)


def test_sin_adaptador_se_conserva_la_postura_que_traia_el_candidato():
    c = candidato(Tipo.GIT_REMOTO_SOSPECHOSO, postura=Postura.DENY, plataforma=Plataforma.OPENCODE)
    [h] = evaluador(adaptadores=[]).evaluar([c])
    assert (h.nivel, h.postura) == (Nivel.POTENCIAL, Postura.DENY)


def test_la_confirmacion_compara_contra_el_mismo_permiso_que_decidio_el_nivel():
    class Cambiante:
        def __init__(self) -> None:
            self.n = 0

        def evaluar(self, ruta):
            self.n += 1
            return permisos(PermisoLectura.SI if self.n == 1 else PermisoLectura.NO)

    [h] = evaluador(sonda=Cambiante(), verificador=SondaFalsa(permisos(PermisoLectura.SI))).evaluar([candidato()])
    assert h.nivel is Nivel.COMPROBADO  # la sonda cambió después, pero se confirmó la misma medición


def test_las_cachés_no_distinguen_la_forma_de_escribir_la_ruta():
    sonda = SondaFalsa()
    ev = evaluador(sonda=sonda)
    ev.evaluar([candidato(ruta="x.env"), candidato(ruta="./x.env")])
    assert sonda.llamadas == 1


def test_las_instrucciones_que_el_agente_carga_solo_salen_una_vez_y_sin_regla_de_lectura():
    ev = evaluador(adaptadores=[AdaptadorFalso(Plataforma.CLAUDE_CODE), AdaptadorFalso(Plataforma.OPENCODE, Postura.ASK)])
    salida = ev.evaluar([candidato(Tipo.INSTRUCCIONES_FUERA_DE_PROYECTO)])
    assert len(salida) == 1 and salida[0].nivel is Nivel.COMPROBADO  # AT-10


def test_dos_adaptadores_de_la_misma_plataforma_no_duplican_los_hallazgos():
    ev = evaluador(adaptadores=[AdaptadorFalso(Plataforma.CLAUDE_CODE), AdaptadorFalso(Plataforma.CLAUDE_CODE)])
    assert len(ev.evaluar([candidato()])) == 1


def test_auditar_con_una_carpeta_relativa_mide_con_rutas_absolutas(tmp_path: Path, monkeypatch):
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / ".env").write_text("STRIPE_SECRET_KEY=sk_live_algo_largo_123\n", encoding="utf-8")
    vistas: list[str] = []

    class Espia(SondaFalsa):
        def evaluar(self, ruta):
            vistas.append(str(ruta))
            return super().evaluar(ruta)

    monkeypatch.chdir(tmp_path)
    _auditar(Path("p"), Espia(), None)
    assert vistas and all(os.path.isabs(v) for v in vistas)


def test_git_un_include_y_una_referencia_en_la_url_son_dudosos(tmp_path: Path):
    p = _proyecto_git(tmp_path / "a", '[include]\n\tpath = otro.cfg\n')
    (p / ".git" / "otro.cfg").write_text("[core]\n\tpager = calc.exe\n", encoding="utf-8")
    assert _certezas(p)[Tipo.GIT_EJECUTA_PROGRAMAS] == [Certeza.DUDOSA]  # GT-13
    ref = _proyecto_git(tmp_path / "b", '[remote "origin"]\n\turl = https://ana:${GH_TOKEN}@host.invalid/x.git\n')
    assert _certezas(ref)[Tipo.GIT_REMOTO_SOSPECHOSO] == [Certeza.DUDOSA]


@pytest.mark.skipif(sys.platform == "win32", reason="enlaces simbólicos de POSIX")
def test_la_sonda_posix_marca_ambiguo_un_enlace(tmp_path: Path):
    from agentreach.infra.sonda_posix import SondaPosix

    real = tmp_path / "a.env"
    real.write_text("X=1", encoding="utf-8")
    (tmp_path / "enlace.env").symlink_to(real)
    assert SondaPosix().evaluar(Ruta(str(tmp_path / "enlace.env"))).ambiguo is True
