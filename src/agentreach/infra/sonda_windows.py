"""Sonda de permisos de Windows con ``ctypes``: lee la ACL sin abrir el archivo (FR-5).

ACL (lista de control de acceso) es la lista que Windows guarda de quién puede leer cada archivo.
Se calcula con la API del sistema (``GetNamedSecurityInfoW`` y ``AccessCheck``) usando el token del
proceso: el usuario que ejecuta AgentReach y sus grupos. Nunca se abre el archivo, porque abrirlo
mediría los permisos de AgentReach y no diría nada de la ACL; y nunca se ejecuta ``icacls`` ni
ningún otro programa (el comando de verificación es solo texto para la persona).

Solo mide al usuario que ejecuta AgentReach, no a otros usuarios ni a "administrador".
"""

from __future__ import annotations

import ctypes
import os
import stat
import sys
from ctypes import wintypes as w
from dataclasses import replace

from agentreach.contracts import PermisoLectura, PermisosArchivo, Ruta
from agentreach.contracts.rutas import es_ruta_de_red, tiene_nombre_reservado

_SE_FILE_OBJECT = 1
_INFO_DACL = 4 | 1 | 2  # DACL + propietario + grupo (AccessCheck los exige)
_FILE_READ_DATA = 0x1
_GENERIC_READ = 0x80000000
_GENERIC_ALL = 0x10000000
_TOKEN_DUPLICATE = 0x0002
_TOKEN_QUERY = 0x0008
_TOKEN_USER = 1
_SECURITY_IMPERSONATION = 2
_ACL_REVISION_INFORMATION = 2
_ACCESS_ALLOWED = 0
_ACCESS_DENIED = 1
_INHERITED_ACE = 0x10
_INHERIT_ONLY_ACE = 0x08  # solo aplica a los hijos, no al objeto mismo
_ERROR_ACCESO_DENEGADO = 5
_SID_TODOS = "S-1-1-0"  # Everyone / Todos


class _GenericMapping(ctypes.Structure):
    _fields_ = [("R", w.DWORD), ("W", w.DWORD), ("X", w.DWORD), ("A", w.DWORD)]


class _PrivilegeSet(ctypes.Structure):
    _fields_ = [("Count", w.DWORD), ("Control", w.DWORD), ("Priv", w.DWORD * 3)]


class _AclSizeInformation(ctypes.Structure):
    _fields_ = [("AceCount", w.DWORD), ("AclBytesInUse", w.DWORD), ("AclBytesFree", w.DWORD)]


class _AceHeader(ctypes.Structure):
    _fields_ = [("Type", ctypes.c_ubyte), ("Flags", ctypes.c_ubyte), ("Size", w.WORD)]


class _AceConMascara(ctypes.Structure):
    _fields_ = [("Header", _AceHeader), ("Mask", w.DWORD)]  # el SID sigue a la máscara


class _Api:
    """Enlaces a las funciones de Windows, cargados una sola vez."""

    def __init__(self) -> None:
        adv = ctypes.WinDLL("advapi32", use_last_error=True)
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        vp = ctypes.c_void_p
        adv.GetNamedSecurityInfoW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, vp, vp, vp, vp, vp]
        adv.GetNamedSecurityInfoW.restype = w.DWORD
        adv.OpenProcessToken.argtypes = [w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE)]
        adv.DuplicateToken.argtypes = [w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE)]
        adv.AccessCheck.argtypes = [
            vp, w.HANDLE, w.DWORD, ctypes.POINTER(_GenericMapping), ctypes.POINTER(_PrivilegeSet),
            ctypes.POINTER(w.DWORD), ctypes.POINTER(w.DWORD), ctypes.POINTER(w.BOOL),
        ]
        adv.GetAclInformation.argtypes = [vp, vp, w.DWORD, w.DWORD]
        adv.GetAce.argtypes = [vp, w.DWORD, ctypes.POINTER(vp)]
        adv.ConvertSidToStringSidW.argtypes = [vp, ctypes.POINTER(w.LPWSTR)]
        adv.GetTokenInformation.argtypes = [w.HANDLE, w.DWORD, vp, w.DWORD, ctypes.POINTER(w.DWORD)]
        adv.LookupAccountSidW.argtypes = [
            w.LPCWSTR, vp, w.LPWSTR, ctypes.POINTER(w.DWORD), w.LPWSTR,
            ctypes.POINTER(w.DWORD), ctypes.POINTER(w.DWORD),
        ]
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


def _sid_a_texto(api: _Api, sid: int) -> str:
    texto = w.LPWSTR()
    if not api.adv.ConvertSidToStringSidW(sid, ctypes.byref(texto)):
        return ""
    try:
        return texto.value or ""
    finally:
        api.k32.LocalFree(ctypes.cast(texto, ctypes.c_void_p))


def _usuario(api: _Api, token: w.HANDLE) -> str:
    """Nombre del usuario del token (``DOMINIO\\usuario``); vacío si no se puede leer."""
    largo = w.DWORD()
    api.adv.GetTokenInformation(token, _TOKEN_USER, None, 0, ctypes.byref(largo))
    if not largo.value:
        return ""
    buf = ctypes.create_string_buffer(largo.value)
    if not api.adv.GetTokenInformation(token, _TOKEN_USER, buf, largo, ctypes.byref(largo)):
        return ""
    sid = ctypes.c_void_p.from_buffer(buf).value  # TOKEN_USER empieza con el puntero al SID
    nombre, dominio = ctypes.create_unicode_buffer(256), ctypes.create_unicode_buffer(256)
    n_nombre, n_dominio, uso = w.DWORD(256), w.DWORD(256), w.DWORD()
    if not api.adv.LookupAccountSidW(
        None, sid, nombre, ctypes.byref(n_nombre), dominio, ctypes.byref(n_dominio), ctypes.byref(uso)
    ):
        return ""
    return f"{dominio.value}\\{nombre.value}" if dominio.value else nombre.value


def _usuario_actual(api: _Api) -> str:
    token = w.HANDLE()
    if not api.adv.OpenProcessToken(api.k32.GetCurrentProcess(), _TOKEN_QUERY, ctypes.byref(token)):
        return ""
    try:
        return _usuario(api, token)
    finally:
        api.k32.CloseHandle(token)


def _acceso_de_lectura(api: _Api, token_imp: w.HANDLE, descriptor: int) -> bool:
    mapa = _GenericMapping(0x120089, 0x120116, 0x1200A0, 0x1F01FF)
    privilegios = _PrivilegeSet()
    largo, concedido, ok = w.DWORD(ctypes.sizeof(privilegios)), w.DWORD(), w.BOOL()
    if not api.adv.AccessCheck(
        descriptor, token_imp, _FILE_READ_DATA, ctypes.byref(mapa), ctypes.byref(privilegios),
        ctypes.byref(largo), ctypes.byref(concedido), ctypes.byref(ok),
    ):
        raise OSError(ctypes.get_last_error())
    return bool(ok.value)


def _entradas(api: _Api, dacl: int) -> list[tuple[int, int, int, str]]:
    """Entradas de la DACL como (tipo, banderas, máscara, SID en texto). Solo se leen permitir y denegar."""
    info = _AclSizeInformation()
    if not api.adv.GetAclInformation(dacl, ctypes.byref(info), ctypes.sizeof(info), 2):
        raise OSError(ctypes.get_last_error())
    salida: list[tuple[int, int, int, str]] = []
    for i in range(info.AceCount):
        ace = ctypes.c_void_p()
        if not api.adv.GetAce(dacl, i, ctypes.byref(ace)):
            raise OSError(ctypes.get_last_error())
        cabecera = _AceConMascara.from_address(ace.value)
        if cabecera.Header.Type in (_ACCESS_ALLOWED, _ACCESS_DENIED):
            sid = ace.value + ctypes.sizeof(_AceConMascara)
            salida.append(
                (cabecera.Header.Type, cabecera.Header.Flags, cabecera.Mask, _sid_a_texto(api, sid))
            )
        else:  # otro tipo de entrada (callback, objeto...): no se interpreta, pero vuelve ambiguo
            salida.append((cabecera.Header.Type, cabecera.Header.Flags, 0, ""))
    return salida


def _comando(ruta: str) -> str:
    return f'icacls "{ruta}"'


def _ruta_medible(ruta: str, permitir_carpeta: bool) -> bool:
    """True solo si la ruta es absoluta, local y de un archivo regular (o carpeta si se pide).

    Se rechazan rutas relativas, prefijos de dispositivo (``\\\\.\\``, ``\\\\?\\``), rutas de red,
    nombres reservados (CON, NUL, COM1...), tuberías, dispositivos y cualquier ruta que no exista.
    """
    if "\x00" in ruta or not os.path.isabs(ruta) or ruta.startswith(("\\\\.\\", "\\\\?\\", "//")):
        return False
    unidad = os.path.splitdrive(ruta)[0]
    if not unidad or es_ruta_de_red(ruta) or tiene_nombre_reservado(ruta):
        return False
    modo = os.stat(ruta).st_mode  # sigue enlaces; lanza OSError si no existe
    return stat.S_ISREG(modo) or (permitir_carpeta and stat.S_ISDIR(modo))


def _pasa_por_enlace(ruta: str) -> bool:
    """True si la ruta o alguno de sus padres es un enlace simbólico o una junction."""
    unidad, resto = os.path.splitdrive(os.path.abspath(ruta))
    actual = unidad + os.sep
    for parte in [p for p in resto.split(os.sep) if p]:
        actual = os.path.join(actual, parte)
        if os.path.islink(actual) or os.path.isjunction(actual):
            return True
    return False


class SondaWindows:
    """Implementa ``FsProbe`` para Windows. No abre el archivo ni lanza programas."""

    def evaluar(self, ruta: Ruta, permitir_carpeta: bool = False) -> PermisosArchivo:
        """Permiso de lectura del usuario actual, si hay entrada propia para Todos y si es ambiguo.

        Una ruta inválida o un fallo de la API dan ``NO_DETERMINADO`` y ambiguo, sin excepción.
        Fuera de Windows lanza ``OSError``.
        """
        if sys.platform != "win32":
            raise OSError("SondaWindows solo funciona en Windows")
        no_determinado = PermisosArchivo(PermisoLectura.NO_DETERMINADO, False, True, "", _comando(ruta))
        try:
            if not _ruta_medible(ruta, permitir_carpeta):
                return no_determinado
            resultado = self._evaluar(ruta)
            if _pasa_por_enlace(ruta):  # se midió el destino, no la ruta escrita: se avisa
                return replace(resultado, ambiguo=True, pasa_por_enlace=True)
            return resultado
        except Exception:  # noqa: BLE001 - cualquier fallo cae a "no determinado", nunca a comprobado
            return no_determinado

    def _evaluar(self, ruta: Ruta) -> PermisosArchivo:
        api = _get_api()
        comando = _comando(ruta)
        descriptor, dacl = ctypes.c_void_p(), ctypes.c_void_p()
        token, token_imp = w.HANDLE(), w.HANDLE()
        usuario = _usuario_actual(api)
        try:
            rc = api.adv.GetNamedSecurityInfoW(
                ruta, _SE_FILE_OBJECT, _INFO_DACL, None, None,
                ctypes.byref(dacl), None, ctypes.byref(descriptor),
            )
            if rc == _ERROR_ACCESO_DENEGADO:
                # Una regla de denegar lectura también impide leer la propia ACL: se deduce "no
                # legible", pero no de la ACL sino de la negativa, así que queda ambiguo.
                return PermisosArchivo(PermisoLectura.NO, False, True, usuario, comando)
            if rc:
                return PermisosArchivo(PermisoLectura.NO_DETERMINADO, False, True, usuario, comando)
            if not api.adv.OpenProcessToken(
                api.k32.GetCurrentProcess(), _TOKEN_DUPLICATE | _TOKEN_QUERY, ctypes.byref(token)
            ):
                return PermisosArchivo(PermisoLectura.NO_DETERMINADO, False, True, usuario, comando)
            usuario = _usuario(api, token)
            if not api.adv.DuplicateToken(token, _SECURITY_IMPERSONATION, ctypes.byref(token_imp)):
                return PermisosArchivo(PermisoLectura.NO_DETERMINADO, False, True, usuario, comando)
            try:
                legible = _acceso_de_lectura(api, token_imp, descriptor.value)
                entradas = _entradas(api, dacl.value) if dacl.value else []
            except OSError:
                return PermisosArchivo(PermisoLectura.NO_DETERMINADO, False, True, usuario, comando)
            permiso = PermisoLectura.SI if legible else PermisoLectura.NO
            if not dacl.value:  # sin DACL: todos acceden, y no hay entrada propia que lo diga
                return PermisosArchivo(permiso, True, True, usuario, comando)
            todos = [
                e for e in entradas
                if e[0] == _ACCESS_ALLOWED and e[3] == _SID_TODOS
                and not e[1] & _INHERIT_ONLY_ACE
                and e[2] & (_FILE_READ_DATA | _GENERIC_READ | _GENERIC_ALL)
            ]
            hay_denegar = any(e[0] == _ACCESS_DENIED for e in entradas)
            hay_otras = any(e[0] not in (_ACCESS_ALLOWED, _ACCESS_DENIED) for e in entradas)
            abierto = bool(todos)
            # La herencia NO baja el nivel: AccessCheck ya la incluye. Es ambiguo solo si hay una
            # regla de denegar (que puede cambiar el resultado) o una entrada no interpretada.
            ambiguo = hay_denegar or hay_otras
            return PermisosArchivo(permiso, abierto, ambiguo, usuario, comando)
        finally:
            for h in (token_imp, token):
                if h.value:
                    api.k32.CloseHandle(h)
            if descriptor.value:
                api.k32.LocalFree(descriptor)

    def permiso_lectura(self, ruta: Ruta) -> PermisoLectura:
        return self.evaluar(ruta).permiso
