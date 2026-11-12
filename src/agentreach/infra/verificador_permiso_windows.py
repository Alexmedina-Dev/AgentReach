"""Verificador independiente del permiso en Windows (Historia 18): una SEGUNDA vía, escrita aparte.

Calcula los mismos tres hechos que la sonda de la Historia 3 (puede leer, hay entrada de "Todos", ambiguo)
por un camino distinto del sistema, y NO importa nada de ``sonda_windows.py``:

=========================  ===================================  ====================================
paso                       sonda principal (Historia 3)         este verificador
=========================  ===================================  ====================================
obtener la ACL             ``GetNamedSecurityInfoW``            ``GetFileSecurityW``
permiso de lectura         ``AccessCheck`` con un token         ``GetEffectiveRightsFromAclW``
entradas de "Todos"        recorre las entradas con ``GetAce``  la ACL como texto SDDL, analizada
=========================  ===================================  ====================================

No abre el archivo, no ejecuta ``icacls`` ni ningún programa. Comparte con la sonda principal el riesgo de
interpretar mal la ACL (se dice en el reporte, FR-24). Definición de "ambiguo" (igual que la principal):
una regla de denegar, una entrada que no es permitir ni denegar (o que no se entiende), una DACL nula o un
cálculo que no se pudo completar. La herencia NO es ambigua.
"""

from __future__ import annotations

import ctypes
import re
import sys
from ctypes import wintypes as w
from dataclasses import dataclass

from agentreach.contracts import PermisoLectura, PermisosArchivo, Ruta

_INFO_DACL = 4
_SDDL_REVISION_1 = 1
_FILE_READ_DATA = 0x1
_GENERIC_READ = 0x80000000
_GENERIC_ALL = 0x10000000
_LEER = _FILE_READ_DATA | _GENERIC_READ | _GENERIC_ALL
_ERROR_ACCESO_DENEGADO = 5
_ERROR_BUFFER_INSUFICIENTE = 122
_TOKEN_QUERY = 0x0008
_TOKEN_USER = 1
_TODOS = ("WD", "S-1-1-0")
_BANDERAS_CONOCIDAS = frozenset({"OI", "CI", "IO", "NP", "ID", "SA", "FA", "AI", "AR", "PP"})  # el alias de SDDL y el SID escrito completo

# Derechos de SDDL: tokens de dos letras y su máscara.
_DERECHOS = {
    "GA": 0x10000000, "GR": 0x80000000, "GW": 0x40000000, "GX": 0x20000000,
    "RC": 0x20000, "SD": 0x10000, "WD": 0x40000, "WO": 0x80000,
    "CC": 0x1, "DC": 0x2, "LC": 0x4, "SW": 0x8, "RP": 0x10, "WP": 0x20, "DT": 0x40, "LO": 0x80, "CR": 0x100,
    "FA": 0x1F01FF, "FR": 0x120089, "FW": 0x100116, "FX": 0x1200A0,
    "KA": 0xF003F, "KR": 0x20019, "KW": 0x20006, "KX": 0x20019,
}


@dataclass(frozen=True, slots=True)
class AnalisisAcl:
    abierto_a_todos: bool  # hay una entrada de permitir lectura para Todos que aplica al objeto
    hay_denegar: bool
    hay_otras: bool  # entrada que no es permitir/denegar, condicional, o que no se entiende


def _mascara(derechos: str) -> int | None:
    """La máscara de un campo de derechos de SDDL (hexadecimal o tokens de dos letras), o ``None`` si no se entiende."""
    if derechos.lower().startswith("0x"):
        try:
            return int(derechos, 16)
        except ValueError:
            return None
    if len(derechos) % 2:
        return None
    total = 0
    for i in range(0, len(derechos), 2):
        token = derechos[i:i + 2]
        if token not in _DERECHOS:
            return None
        total |= _DERECHOS[token]
    return total


def _entradas_de_dacl(sddl: str) -> tuple[list[str], bool]:
    """Los textos de las entradas de la DACL (entre paréntesis de primer nivel) y si algo quedó sin entender."""
    # solo se pide la DACL, así que el texto empieza por "D:"; se ancla para no confundirlo con el final de otro campo
    m = re.search(r"(?:^|\))D:", sddl)
    if m is None:
        return [], True
    resto = sddl[m.end():]
    sacl = re.search(r"(?<=\))S:", resto)
    if sacl is not None:
        resto = resto[:sacl.start()]
    entradas: list[str] = []
    no_entendido = False
    profundidad = 0
    actual: list[str] = []
    anidada = False
    for c in resto:
        if c == "(":
            profundidad += 1
            if profundidad > 1:
                anidada = True
            if profundidad == 1:
                actual, anidada = [], False
                continue
        elif c == ")":
            if profundidad == 0:
                no_entendido = True
                continue
            profundidad -= 1
            if profundidad == 0:
                texto = "".join(actual)
                if anidada:  # una condición dentro de la entrada: ACL no estándar
                    no_entendido = True
                    entradas.append("")  # no se interpreta
                else:
                    entradas.append(texto)
                continue
        if profundidad >= 1:
            actual.append(c)
    if profundidad != 0:  # paréntesis sin cerrar
        no_entendido = True
    return entradas, no_entendido


def analizar_sddl(sddl: str) -> AnalisisAcl:
    """Analiza la DACL de un SDDL: pura, sin Windows. Ante lo que no entiende, ``hay_otras`` (ambiguo)."""
    entradas, otras = _entradas_de_dacl(sddl)
    abierto = False
    denegar = False
    for texto in entradas:
        if not texto.strip():
            otras = True  # una entrada vacía "()" o una condicional que no se interpreta
            continue
        partes = texto.split(";")
        if len(partes) < 6:
            otras = True
            continue
        tipo, banderas, derechos, sid = partes[0], partes[1], partes[2], partes[5]
        if tipo == "D":
            denegar = True
        elif tipo == "A":
            mascara = _mascara(derechos)
            if mascara is None:
                otras = True
                continue
            fichas = [banderas[i:i + 2] for i in range(0, len(banderas), 2)]
            if len(banderas) % 2 or any(f not in _BANDERAS_CONOCIDAS for f in fichas):
                otras = True  # banderas que no se entienden: no se afirma nada
                continue
            solo_hijos = "IO" in fichas
            if sid.upper() in _TODOS and not solo_hijos and mascara & _LEER:
                abierto = True
        else:
            otras = True  # objeto, condicional, auditoría... no se interpreta
    return AnalisisAcl(abierto, denegar, otras)


# ---- la vía del sistema (solo Windows) ------------------------------------------------------------------------------------------------------


class _Trustee(ctypes.Structure):
    _fields_ = [("pMultipleTrustee", ctypes.c_void_p), ("MultipleTrusteeOperation", w.DWORD),
                ("TrusteeForm", w.DWORD), ("TrusteeType", w.DWORD), ("ptstrName", ctypes.c_void_p)]


class _Api:
    def __init__(self) -> None:
        adv = ctypes.WinDLL("advapi32", use_last_error=True)
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        vp = ctypes.c_void_p
        adv.GetFileSecurityW.argtypes = [w.LPCWSTR, w.DWORD, vp, w.DWORD, ctypes.POINTER(w.DWORD)]
        adv.GetSecurityDescriptorDacl.argtypes = [vp, ctypes.POINTER(w.BOOL), ctypes.POINTER(vp), ctypes.POINTER(w.BOOL)]
        adv.BuildTrusteeWithSidW.argtypes = [ctypes.POINTER(_Trustee), vp]
        adv.GetEffectiveRightsFromAclW.argtypes = [vp, ctypes.POINTER(_Trustee), ctypes.POINTER(w.DWORD)]
        adv.GetEffectiveRightsFromAclW.restype = w.DWORD
        adv.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = [
            vp, w.DWORD, w.DWORD, ctypes.POINTER(w.LPWSTR), ctypes.POINTER(w.ULONG)]
        adv.OpenProcessToken.argtypes = [w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE)]
        adv.GetTokenInformation.argtypes = [w.HANDLE, w.DWORD, vp, w.DWORD, ctypes.POINTER(w.DWORD)]
        adv.LookupAccountSidW.argtypes = [w.LPCWSTR, vp, w.LPWSTR, ctypes.POINTER(w.DWORD), w.LPWSTR,
                                          ctypes.POINTER(w.DWORD), ctypes.POINTER(w.DWORD)]
        k32.GetCurrentProcess.restype = w.HANDLE
        k32.LocalFree.argtypes = [vp]
        k32.CloseHandle.argtypes = [w.HANDLE]
        self.adv, self.k32 = adv, k32


_api: _Api | None = None


def _get_api() -> _Api:
    global _api
    if _api is None:
        _api = _Api()
    return _api


def _sid_y_nombre_del_usuario(api: _Api) -> tuple[ctypes.Array | None, int | None, str]:
    """(buffer, puntero al SID, nombre) del usuario del proceso. El buffer debe mantenerse vivo mientras se usa el SID."""
    token = w.HANDLE()
    if not api.adv.OpenProcessToken(api.k32.GetCurrentProcess(), _TOKEN_QUERY, ctypes.byref(token)):
        return None, None, ""
    try:
        largo = w.DWORD()
        api.adv.GetTokenInformation(token, _TOKEN_USER, None, 0, ctypes.byref(largo))
        if not largo.value:
            return None, None, ""
        buf = ctypes.create_string_buffer(largo.value)
        if not api.adv.GetTokenInformation(token, _TOKEN_USER, buf, largo, ctypes.byref(largo)):
            return None, None, ""
        sid = ctypes.c_void_p.from_buffer(buf).value  # TOKEN_USER empieza con el puntero al SID
        nombre, dominio = ctypes.create_unicode_buffer(256), ctypes.create_unicode_buffer(256)
        n1, n2, uso = w.DWORD(256), w.DWORD(256), w.DWORD()
        if not api.adv.LookupAccountSidW(None, sid, nombre, ctypes.byref(n1), dominio, ctypes.byref(n2), ctypes.byref(uso)):
            return buf, sid, ""
        return buf, sid, f"{dominio.value}\\{nombre.value}" if dominio.value else nombre.value
    finally:
        api.k32.CloseHandle(token)


class VerificadorPermisoWindows:
    """Implementa ``Sonda`` (``evaluar``) por la segunda vía. No abre el archivo ni lanza programas."""

    def evaluar(self, ruta: Ruta) -> PermisosArchivo:
        if sys.platform != "win32":
            raise OSError("VerificadorPermisoWindows solo funciona en Windows")
        comando = f'icacls "{ruta}"'  # texto para la persona; nunca se ejecuta
        try:
            return self._evaluar(ruta, comando)
        except Exception:  # noqa: BLE001 - una API ausente o una ruta rara: no se determina, no se cae
            return PermisosArchivo(PermisoLectura.NO_DETERMINADO, False, True, "", comando)

    def _evaluar(self, ruta: Ruta, comando: str) -> PermisosArchivo:
        api = _get_api()
        buffer_usuario, sid_usuario, usuario = _sid_y_nombre_del_usuario(api)

        def no_determinado() -> PermisosArchivo:
            return PermisosArchivo(PermisoLectura.NO_DETERMINADO, False, True, usuario, comando)

        largo = w.DWORD()
        api.adv.GetFileSecurityW(ruta, _INFO_DACL, None, 0, ctypes.byref(largo))
        error = ctypes.get_last_error()
        if error == _ERROR_ACCESO_DENEGADO:
            # Una regla de denegar lectura también impide leer la propia ACL: se deduce "no legible", pero de la
            # negativa y no de la ACL, así que queda ambiguo (igual que la sonda principal).
            return PermisosArchivo(PermisoLectura.NO, False, True, usuario, comando)
        if error != _ERROR_BUFFER_INSUFICIENTE or not largo.value:  # la primera llamada solo debe pedir el tamaño
            return no_determinado()
        descriptor = ctypes.create_string_buffer(largo.value)
        if not api.adv.GetFileSecurityW(ruta, _INFO_DACL, descriptor, largo, ctypes.byref(largo)):
            if ctypes.get_last_error() == _ERROR_ACCESO_DENEGADO:
                return PermisosArchivo(PermisoLectura.NO, False, True, usuario, comando)
            return no_determinado()
        presente, por_defecto, acl = w.BOOL(), w.BOOL(), ctypes.c_void_p()
        if not api.adv.GetSecurityDescriptorDacl(descriptor, ctypes.byref(presente), ctypes.byref(acl), ctypes.byref(por_defecto)):
            return no_determinado()
        if not presente.value or not acl.value:
            # sin DACL (o nula): todos acceden y ninguna entrada propia lo dice
            return PermisosArchivo(PermisoLectura.SI, True, True, usuario, comando)
        if sid_usuario is None or buffer_usuario is None:
            return no_determinado()
        trustee, derechos = _Trustee(), w.DWORD()
        api.adv.BuildTrusteeWithSidW(ctypes.byref(trustee), sid_usuario)
        if api.adv.GetEffectiveRightsFromAclW(acl, ctypes.byref(trustee), ctypes.byref(derechos)) != 0:
            return no_determinado()
        permiso = PermisoLectura.SI if derechos.value & _LEER else PermisoLectura.NO  # los mismos bits que 'abierto a Todos'
        texto = w.LPWSTR()
        if not api.adv.ConvertSecurityDescriptorToStringSecurityDescriptorW(
            descriptor, _SDDL_REVISION_1, _INFO_DACL, ctypes.byref(texto), None
        ):
            return no_determinado()
        try:
            sddl = texto.value or ""
        finally:
            api.k32.LocalFree(ctypes.cast(texto, ctypes.c_void_p))
        analisis = analizar_sddl(sddl)
        return PermisosArchivo(permiso, analisis.abierto_a_todos, analisis.hay_denegar or analisis.hay_otras, usuario, comando)

    def permiso_lectura(self, ruta: Ruta) -> PermisoLectura:
        return self.evaluar(ruta).permiso


__all__ = ["AnalisisAcl", "VerificadorPermisoWindows", "analizar_sddl"]
