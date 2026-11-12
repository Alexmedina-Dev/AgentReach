"""Historia 18: segundo cálculo, independiente, del permiso en Windows, y ``confirmar``."""

from __future__ import annotations

import ast
import builtins
import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agentreach.contracts import Idioma, PermisoLectura, PermisosArchivo, Ruta
from agentreach.core.verificacion_independiente import (
    LIMITACION_TEXTO,
    Confirmacion,
    comparar,
    confirmar,
)
from agentreach.infra.verificador_permiso_windows import analizar_sddl

pytestmark = pytest.mark.sin_tope_por_nombre  # motor de niveles: TH-1 puede llegar a comprobado (el tope real se prueba en test_historia_27.py)

RAIZ = Path(__file__).resolve().parents[1]
FUENTES = RAIZ / "src" / "agentreach"
solo_windows = pytest.mark.skipif(sys.platform != "win32", reason="solo Windows")


def _permisos(permiso=PermisoLectura.SI, abierto=False, ambiguo=False) -> PermisosArchivo:
    return PermisosArchivo(permiso, abierto, ambiguo, "usuario", "icacls ruta")


class SondaFalsa:
    def __init__(self, resultado: PermisosArchivo | None = None, error: Exception | None = None) -> None:
        self._resultado, self._error = resultado, error

    def evaluar(self, ruta: Ruta) -> PermisosArchivo:
        if self._error is not None:
            raise self._error
        return self._resultado  # type: ignore[return-value]


# ---- confirmar y comparar (no dependen de Windows) -------------------------------------------------------------------------------


def test_coinciden_los_tres_hechos_confirma():
    r = confirmar(SondaFalsa(_permisos(abierto=True)), SondaFalsa(_permisos(abierto=True)), Ruta("x"))
    assert r.estado is Confirmacion.CONFIRMADO and r.discrepancias == ()


@pytest.mark.parametrize("principal,verificador,hecho", [
    (_permisos(PermisoLectura.SI), _permisos(PermisoLectura.NO), "permiso"),
    (_permisos(abierto=False), _permisos(abierto=True), "abierto_a_todos"),
    (_permisos(ambiguo=False), _permisos(ambiguo=True), "ambiguo"),
])
def test_si_discrepan_en_cualquiera_de_los_tres_hechos_no_confirma(principal, verificador, hecho):
    r = confirmar(SondaFalsa(principal), SondaFalsa(verificador), Ruta("x"))
    assert r.estado is Confirmacion.NO_CONFIRMADO and r.discrepancias == (hecho,)


def test_varias_discrepancias_se_listan_todas_y_en_orden():
    r = comparar(_permisos(PermisoLectura.SI, False, False), _permisos(PermisoLectura.NO, True, True))
    assert r.discrepancias == ("permiso", "abierto_a_todos", "ambiguo")


def test_si_el_verificador_no_determina_no_confirma():
    nd = _permisos(PermisoLectura.NO_DETERMINADO, False, True)
    r = confirmar(SondaFalsa(_permisos()), SondaFalsa(nd), Ruta("x"))
    assert r.estado is Confirmacion.NO_CONFIRMADO and r.discrepancias == ("verificador_no_determinado",)


def test_si_la_principal_no_determina_tampoco_se_puede_confirmar_nada():
    nd = _permisos(PermisoLectura.NO_DETERMINADO, False, True)
    r = confirmar(SondaFalsa(nd), SondaFalsa(_permisos()), Ruta("x"))
    assert r.estado is Confirmacion.NO_CONFIRMADO and r.discrepancias == ("principal_no_determinado",)


def test_si_el_verificador_o_la_principal_fallan_no_se_propaga_la_excepcion():
    r = confirmar(SondaFalsa(_permisos()), SondaFalsa(error=OSError("rota")), Ruta("x"))
    assert r.estado is Confirmacion.NO_CONFIRMADO and r.discrepancias == ("verificador_fallo",)
    r = confirmar(SondaFalsa(error=ValueError("rota")), SondaFalsa(_permisos()), Ruta("x"))
    assert r.estado is Confirmacion.NO_CONFIRMADO and r.discrepancias == ("principal_fallo",)
    assert "rota" not in repr(r)  # el mensaje de la excepción no se copia


def test_la_limitacion_compartida_se_dice_en_los_dos_idiomas():
    assert "misma ACL" in LIMITACION_TEXTO[Idioma.ES] and "comparten el riesgo" in LIMITACION_TEXTO[Idioma.ES]
    assert "same ACL" in LIMITACION_TEXTO[Idioma.EN] and "share the risk" in LIMITACION_TEXTO[Idioma.EN]


def test_el_nucleo_no_importa_la_infraestructura():
    arbol = ast.parse((FUENTES / "core" / "verificacion_independiente.py").read_text(encoding="utf-8"))
    for n in ast.walk(arbol):
        nombres = [n.module] if isinstance(n, ast.ImportFrom) and n.module else (
            [a.name for a in n.names] if isinstance(n, ast.Import) else [])
        for nombre in nombres:
            assert not nombre.startswith(("agentreach.infra", "agentreach.adapters", "agentreach.reporting")), nombre


# ---- el analizador de la ACL en texto (SDDL): puro, sin Windows --------------------------------------------------------------------


@pytest.mark.parametrize("sddl,abierto,denegar,otras", [
    ("D:PAI(A;;FA;;;BA)(A;;FA;;;SY)(A;;0x1200a9;;;BU)(A;;0x1301bf;;;AU)", False, False, False),  # ACL normal del perfil
    ("D:PAI(A;;FR;;;WD)(A;ID;FA;;;BA)", True, False, False),  # PA-01: entrada propia para Todos
    ("D:AI(A;ID;FR;;;WD)", True, False, False),  # heredada: también cuenta (la herencia no es ambigua)
    ("D:(A;;0x1200a9;;;S-1-1-0)", True, False, False),  # el SID escrito completo
    ("D:(A;IO;FR;;;WD)", False, False, False),  # solo para los hijos: no aplica al objeto
    ("D:(A;;0x100116;;;WD)", False, False, False),  # Todos pero sin derecho de lectura (escribir)
    ("D:(A;;GR;;;WD)", True, False, False),  # lectura genérica
    ("D:(A;;GA;;;WD)", True, False, False),
    ("D:(D;;FR;;;WD)(A;;FR;;;WD)", True, True, False),  # hay una regla de denegar: ambiguo
    ("D:(D;;CC;;;S-1-5-21-1-2-3-1001)", False, True, False),
    ("D:(XA;;FR;;;WD;(@User.Dept == \"x\"))", False, False, True),  # entrada condicional: no estándar
    ("D:(OA;;FR;;;WD)", False, False, True),  # entrada de objeto: no estándar
    ("D:(A;;ZZ;;;WD)", False, False, True),  # derecho que no se reconoce: no estándar
    ("D:(A;;FR;;;WD", False, False, True),  # paréntesis sin cerrar: no se entiende
    ("D:PAI", False, False, False),  # DACL vacía (no da nada)
    ("D:(A;;FR;;;wd)", True, False, False),  # el alias en minúsculas
    ("D:(A;;FR;;;s-1-1-0)", True, False, False),  # el SID en minúsculas
    ("D:()", False, False, True),  # entrada vacía: no se entiende
    ("D:(A;OICIIO;FR;;;WD)", False, False, False),  # solo para los hijos con varias banderas
    ("D:(A;XX;FR;;;WD)", False, False, True),  # bandera que no se conoce
    ("D:(A;I;FR;;;WD)", False, False, True),  # banderas de largo impar
    ("O:BAG:SYD:(A;;FR;;;WD)", False, False, True),  # el D: pegado a otro campo no se toma como la DACL
    ("D:(A;;FR;;;WD)S:(AU;SA;FA;;;WD)", True, False, False),  # la SACL no se mezcla con la DACL
])
def test_analizar_sddl(sddl, abierto, denegar, otras):
    a = analizar_sddl(sddl)
    assert (a.abierto_a_todos, a.hay_denegar, a.hay_otras) == (abierto, denegar, otras), sddl


def test_un_sddl_sin_dacl_se_trata_como_no_estandar():
    assert analizar_sddl("O:BAG:SY").hay_otras is True


# ---- independencia: no usa la primera vía, no abre el archivo, no ejecuta nada ---------------------------------------------------------


def _importados(ruta: Path) -> set[str]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    nombres: set[str] = set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            nombres |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            base = ("." * n.level) + (n.module or "")
            nombres.add(base)
            nombres |= {f"{base}.{a.name}" for a in n.names}
    return nombres


def test_el_verificador_no_importa_la_sonda_de_la_historia_3():
    importados = _importados(FUENTES / "infra" / "verificador_permiso_windows.py")
    assert not [i for i in importados if "sonda_windows" in i or "sonda_posix" in i]
    assert not [i for i in importados if i.split(".")[0] in {"subprocess", "multiprocessing", "shlex"}]


def test_el_verificador_no_usa_las_llamadas_de_la_primera_via():
    arbol = ast.parse((FUENTES / "infra" / "verificador_permiso_windows.py").read_text(encoding="utf-8"))
    usados = {n.attr for n in ast.walk(arbol) if isinstance(n, ast.Attribute)} | {n.id for n in ast.walk(arbol) if isinstance(n, ast.Name)}
    assert not usados & {"GetNamedSecurityInfoW", "AccessCheck", "GetAclInformation", "GetAce", "DuplicateToken"}
    assert {"GetFileSecurityW", "GetEffectiveRightsFromAclW", "ConvertSecurityDescriptorToStringSecurityDescriptorW"} <= usados


def _icacls(*args: str) -> None:
    subprocess.run(["icacls", *args], check=True, capture_output=True)


def _yo() -> str:
    return subprocess.run(["whoami"], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def archivo(tmp_path: Path) -> Path:
    f = tmp_path / ".env.staging"
    f.write_bytes(b"CLAVE=valor-falso")
    return f


@pytest.fixture
def verificador():
    from agentreach.infra.verificador_permiso_windows import VerificadorPermisoWindows

    return VerificadorPermisoWindows()


@pytest.fixture
def principal():
    from agentreach.infra.sonda_windows import SondaWindows

    return SondaWindows()


@solo_windows
def test_no_se_abre_el_archivo_medido_ni_se_lanza_un_programa(verificador, archivo, monkeypatch):
    objetivo = os.path.normcase(os.path.abspath(archivo))

    def vigilar(original):
        def envoltura(ruta, *a, **k):
            if isinstance(ruta, (str, bytes, os.PathLike)) and os.path.normcase(os.path.abspath(os.fsdecode(ruta))) == objetivo:
                raise AssertionError("se abrió el archivo medido")
            return original(ruta, *a, **k)

        return envoltura

    def prohibido(*a, **k):
        raise AssertionError("se intentó lanzar un programa")

    monkeypatch.setattr(builtins, "open", vigilar(builtins.open))
    monkeypatch.setattr(io, "open", vigilar(io.open))
    monkeypatch.setattr(os, "open", vigilar(os.open))
    monkeypatch.setattr(subprocess, "Popen", prohibido)
    monkeypatch.setattr(os, "system", prohibido)
    assert verificador.evaluar(Ruta(str(archivo))).permiso is PermisoLectura.SI


# ---- coincide con la sonda principal (Windows) ---------------------------------------------------------------------------------------------


def _coinciden(principal, verificador, ruta: Path):
    r = confirmar(principal, verificador, Ruta(str(ruta)))
    esperado = principal.evaluar(Ruta(str(ruta)))
    obtenido = verificador.evaluar(Ruta(str(ruta)))
    assert r.estado is Confirmacion.CONFIRMADO, (r.discrepancias, esperado, obtenido)
    return obtenido


@solo_windows
def test_pp04_y_pp05_permiso_normal_legible_y_no_abierto(principal, verificador, archivo):
    r = _coinciden(principal, verificador, archivo)
    assert r.permiso is PermisoLectura.SI and r.abierto_a_todos is False and r.ambiguo is False


@solo_windows
def test_pp03_lectura_negada_no_legible(principal, verificador, archivo):
    _icacls(str(archivo), "/deny", f"{_yo()}:(R)")
    assert _coinciden(principal, verificador, archivo).permiso is PermisoLectura.NO


@solo_windows
def test_pa01_entrada_propia_para_todos_es_abierto_e_inequivoco(principal, verificador, archivo):
    _icacls(str(archivo), "/grant", "*S-1-1-0:(R)")
    r = _coinciden(principal, verificador, archivo)
    assert r.abierto_a_todos is True and r.ambiguo is False


@solo_windows
def test_el_permiso_heredado_de_todos_coincide_y_no_es_ambiguo(principal, verificador, tmp_path: Path):
    carpeta = tmp_path / "heredada"
    carpeta.mkdir()
    _icacls(str(carpeta), "/grant", "*S-1-1-0:(OI)(CI)(R)")
    hijo = carpeta / "datos.env"
    hijo.write_bytes(b"X=1")
    r = _coinciden(principal, verificador, hijo)
    assert r.abierto_a_todos is True and r.ambiguo is False


@solo_windows
def test_todos_junto_a_una_regla_de_denegar_es_ambiguo_en_las_dos(principal, verificador, archivo):
    _icacls(str(archivo), "/grant", "*S-1-1-0:(R)")
    _icacls(str(archivo), "/deny", f"{_yo()}:(W)")
    r = _coinciden(principal, verificador, archivo)
    assert r.abierto_a_todos is True and r.ambiguo is True


@solo_windows
def test_un_archivo_que_no_existe_no_se_determina_en_las_dos_y_por_eso_no_se_confirma(principal, verificador, tmp_path: Path):
    ruta = Ruta(str(tmp_path / "no-existe.env"))
    esperado, obtenido = principal.evaluar(ruta), verificador.evaluar(ruta)
    assert esperado.permiso is obtenido.permiso is PermisoLectura.NO_DETERMINADO and obtenido.ambiguo is True
    assert comparar(esperado, obtenido).discrepancias == ()  # los hechos coinciden...
    r = confirmar(principal, verificador, ruta)  # ...pero ninguna pudo determinar: no hay nada que confirmar
    assert r.estado is Confirmacion.NO_CONFIRMADO and r.discrepancias == ("principal_no_determinado", "verificador_no_determinado")


@solo_windows
def test_una_ruta_imposible_no_lanza_excepcion(verificador):
    r = verificador.evaluar(Ruta("C:\\carpeta\\x00rara"))
    assert r.permiso is PermisoLectura.NO_DETERMINADO and r.ambiguo is True


@solo_windows
def test_el_verificador_da_el_usuario_y_el_comando_de_verificacion(verificador, archivo):
    r = verificador.evaluar(Ruta(str(archivo)))
    assert r.usuario and r.comando_verificacion == f'icacls "{archivo}"'


def test_fuera_de_windows_el_verificador_lanza_oserror(monkeypatch, verificador):
    monkeypatch.setattr(sys, "platform", "linux")
    with pytest.raises(OSError):
        verificador.evaluar(Ruta("x"))


@pytest.fixture
def proyecto_prueba() -> Path:
    raiz = os.environ.get("AGENTREACH_PROYECTO_PRUEBA")
    if not raiz or not (Path(raiz) / "proyecto").is_dir():
        pytest.skip("AGENTREACH_PROYECTO_PRUEBA no apunta al proyecto de prueba")
    return Path(raiz) / "proyecto"


@solo_windows
def test_pp03_pp04_pp05_y_pa01_con_el_proyecto_de_prueba(principal, verificador, proyecto_prueba: Path):
    assert _coinciden(principal, verificador, proyecto_prueba / ".env.production").permiso is PermisoLectura.NO  # PP-03
    assert _coinciden(principal, verificador, proyecto_prueba / ".env.staging").permiso is PermisoLectura.SI  # PP-04
    assert _coinciden(principal, verificador, proyecto_prueba / ".env.local").permiso is PermisoLectura.SI  # PP-05
    pa01 = _coinciden(principal, verificador, proyecto_prueba / "config" / "exportacion-abierta.env")  # PA-01
    assert pa01.abierto_a_todos is True and pa01.ambiguo is False


# ---- parches de la revisión ----------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("malo", [None, 3, "texto", object()])
def test_un_resultado_mal_formado_de_una_sonda_cuenta_como_fallo_y_no_lanza(malo):
    class Mala:
        def evaluar(self, ruta):
            return malo

    r = confirmar(SondaFalsa(_permisos()), Mala(), Ruta("x"))
    assert r.estado is Confirmacion.NO_CONFIRMADO and r.discrepancias == ("verificador_fallo",)
    r = confirmar(Mala(), Mala(), Ruta("x"))
    assert r.estado is Confirmacion.NO_CONFIRMADO and r.discrepancias == ("principal_fallo", "verificador_fallo")


@solo_windows
def test_una_dacl_nula_da_lo_mismo_en_las_dos_vias(principal, verificador, tmp_path: Path):
    import ctypes

    f = tmp_path / "nula.env"
    f.write_bytes(b"X=1")
    adv = ctypes.WinDLL("advapi32")
    adv.SetNamedSecurityInfoW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p,
                                          ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    # DACL_SECURITY_INFORMATION | UNPROTECTED_DACL_SECURITY_INFORMATION con una DACL nula: todos acceden
    if adv.SetNamedSecurityInfoW(str(f), 1, 0x4 | 0x20000000, None, None, None, None) != 0:
        pytest.skip("el entorno no permite poner una DACL nula")
    r = _coinciden(principal, verificador, f)
    assert r.permiso is PermisoLectura.SI and r.abierto_a_todos is True and r.ambiguo is True


@solo_windows
def test_el_verificador_no_lanza_ni_con_un_tipo_de_ruta_inesperado(verificador):
    assert verificador.evaluar(None).permiso is PermisoLectura.NO_DETERMINADO  # type: ignore[arg-type]
