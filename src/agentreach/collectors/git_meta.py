"""Git sin ejecutar nada (TH-18, TH-19, TH-20): remotos, submódulos, hooks y configuración peligrosa.

Se lee como TEXTO, con código propio, ``.git/config`` (y sus ``include``), ``.gitmodules`` y
``.gitattributes``, y se LISTA (solo nombres) ``.git/hooks/``. No se ejecuta ``git`` ni ningún otro
programa, no se abre ningún hook y el valor de una URL con credencial no se guarda ni se imprime.

Regla de oro: ante la duda no se ejecuta nada y se reporta. Si algo no se puede leer o interpretar
(bytes raros, sintaxis que el lector propio no entiende, límites superados) se emite TH-20 y además
queda en ``no_revisados`` con su motivo. El historial de commits no se mira: sale como
``historial_git_fase2``.

El nivel de cada hallazgo es provisional (hipótesis): la Historia 11 lo calcula.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable
from urllib.parse import unquote

from agentreach.collectors.detector.patrones import valor_es_referencia, valor_es_relleno
from agentreach.contracts import (
    Ajeno,
    ArchivoNoLegible,
    Certeza,
    Etiqueta,
    Finding,
    Idioma,
    Linea,
    Location,
    Metadatos,
    Motivo,
    MotivoNoRevisado,
    Nivel,
    NoRevisado,
    Plataforma,
    Postura,
    Proveedor,
    ReadOnlyFs,
    Ruta,
    Tipo,
)
from agentreach.infra.lector_config_git import (
    ConfigNoInterpretable,
    Entrada,
    es_booleano_git,
    leer_con_includes,
    parsear_config,
)

# Textos fijos de las sugerencias que no caben en el catálogo por tipo (solo texto, no se ejecuta nada).
SUGERENCIAS_TEXTO: dict[str, dict[Idioma, str]] = {
    "cambiar_ayudante_wincred": {
        Idioma.ES: ("El ayudante de credenciales «wincred» de Git for Windows tiene fallos de 2026 sin "
                    "corrección publicada (avisos de Git for Windows del 14-jul y el 28-sep-2026): use otro "
                    "ayudante de credenciales, por ejemplo Git Credential Manager."),
        Idioma.EN: ("Git for Windows' «wincred» credential helper has 2026 flaws with no published fix "
                    "(Git for Windows advisories of 14-Jul and 28-Sep-2026): use another credential helper, "
                    "for example Git Credential Manager."),
    },
}

# Claves de configuración que hacen que git lance un programa. (sección, nombre) sin subsección.
_CLAVES_PLANAS = {
    ("core", "sshcommand"), ("core", "pager"), ("core", "editor"), ("core", "askpass"), ("core", "gitproxy"),
    ("diff", "external"), ("gpg", "program"), ("sequence", "editor"),
    ("web", "browser"), ("uploadpack", "packobjectshook"),
}
# Con subsección: (sección, nombre).
_CLAVES_CON_SUBSECCION = {
    ("filter", "clean"), ("filter", "smudge"), ("filter", "process"),
    ("diff", "textconv"), ("diff", "command"), ("merge", "driver"),
    ("mergetool", "cmd"), ("difftool", "cmd"), ("gpg", "program"), ("gpg", "defaultkeycommand"),
    ("remote", "uploadpack"), ("remote", "receivepack"), ("remote", "vcs"),
    ("browser", "cmd"), ("man", "cmd"), ("trailer", "cmd"),
}
_TOKEN_EN_URL = re.compile(r"^(?:ghp_|gho_|ghu_|ghs_|ghr_|github_pat_|glpat-|xox[abprs]-)", re.IGNORECASE)
_AUTORIDAD = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://([^/?#]*)")
_RUTA_ABSOLUTA = re.compile(r"^(?:/|[A-Za-z]:[\\/]|\\\\)")


def _quita_comillas(valor: str | None) -> str:
    return (valor or "").strip()


def _url_sospechosa(valor: str, es_submodulo: bool) -> bool:
    """URL con credencial incrustada o con una forma que git interpretaría como orden."""
    v = valor.strip()
    if not v:
        return False
    if v.startswith("-") or "\n" in v or "\r" in v or v.lower().startswith("ext::"):
        return True
    if es_submodulo and ".." in re.split(r"[\\/]", v.split("://", 1)[-1])[1:]:
        return True
    m = _AUTORIDAD.match(v)
    if not m or "@" not in m.group(1):
        return False
    userinfo = m.group(1).rsplit("@", 1)[0]
    if v.lower().startswith(("http://", "https://")) and len(userinfo) >= 20:  # token largo como usuario
        return True
    if ":" in userinfo:  # usuario:clave (incluso de relleno: el hallazgo existe, el nivel lo decide la Historia 11)
        return True
    return bool(_TOKEN_EN_URL.match(userinfo))


def _url_con_clave_literal(valor: str) -> bool:
    """``usuario:clave@``: la clave existe y no es un valor de relleno. Solo pregunta, no guarda el valor."""
    m = _AUTORIDAD.match(valor.strip())
    if not m or "@" not in m.group(1):
        return False
    userinfo = m.group(1).rsplit("@", 1)[0]
    if ":" not in userinfo:
        return False
    clave = userinfo.split(":", 1)[1]
    return not (valor_es_relleno(clave) or valor_es_referencia(clave) or valor_es_referencia(unquote(clave)))


def _ejecuta_programa(e: Entrada) -> tuple[bool, str | None]:
    """¿Esta variable hace que git ejecute un programa? Devuelve (sí/no, clave de sugerencia o None)."""
    v = e.valor
    texto = _quita_comillas(v)
    s, n, sub = e.seccion, e.nombre, e.subseccion
    if (s, n) == ("core", "fsmonitor"):
        return es_booleano_git(v) is None, None  # un valor que no es booleano es un programa
    if (s, n) == ("core", "hookspath"):
        return bool(texto), None
    if sub is None and (s, n) in _CLAVES_PLANAS:
        return bool(texto), None
    if sub is not None and (s, n) in _CLAVES_CON_SUBSECCION:
        return bool(texto), None
    if s == "alias" or (s, n) == ("submodule", "update"):
        return texto.startswith("!"), None
    if s == "pager" and sub is None:
        return bool(texto) and es_booleano_git(v) is None, None
    if (s, n) == ("credential", "helper"):
        if texto.lower() == "wincred":
            return True, "cambiar_ayudante_wincred"
        return texto.startswith("!") or bool(_RUTA_ABSOLUTA.match(texto)), None
    return False, None


def _sin_duplicados(hallazgos: list[Finding]) -> list[Finding]:
    vistos: dict[tuple[str, str, str], Finding] = {}
    for h in hallazgos:
        vistos.setdefault((h.ubicacion.ruta, str(h.ubicacion.linea), h.tipo.value), h)
    return list(vistos.values())


class DetectorGit:
    """``no_revisados`` y ``sugerencias`` quedan con lo de la última llamada a ``detectar``.

    ``sugerencias`` asocia (ruta, línea) del hallazgo con la clave de ``SUGERENCIAS_TEXTO`` que el
    reporte añade a "qué hacer".
    """

    def __init__(self, fs: ReadOnlyFs) -> None:
        self._fs = fs
        self.no_revisados: tuple[NoRevisado, ...] = ()
        self.sugerencias: dict[tuple[str, int | Linea], str] = {}
        self._principal: str | None = None  # el .git/config: lo que venga de otro archivo (include) es dudoso

    # ---- punto de entrada --------------------------------------------------------------------------------

    def detectar(self, proyecto: Ruta) -> Iterable[Finding]:
        self.no_revisados = ()
        self.sugerencias = {}
        hallazgos: list[Finding] = []
        pendientes: list[NoRevisado] = []
        git = os.path.join(proyecto, ".git")
        carpeta = self._metadatos(git, pendientes)
        if carpeta is None:
            self.no_revisados = tuple(pendientes)  # un .git que no se pudo medir se informa, no se calla
            return []  # sin .git no hay nada que decir
        if carpeta.es_enlace:  # ante la duda se reporta: no se sigue y no se sabe qué hay detrás
            pendientes.append(NoRevisado(carpeta.ruta, MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR))
            hallazgos.append(self._th20(carpeta.ruta))
        elif not carpeta.es_carpeta:  # un archivo ``.git`` (gitfile): fuera del MVP
            pendientes.append(NoRevisado(carpeta.ruta, MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE))
            hallazgos.append(self._th20(carpeta.ruta))
        else:
            pendientes.append(NoRevisado(carpeta.ruta, MotivoNoRevisado.HISTORIAL_GIT_FASE2))  # GT-02
            hallazgos += self._config(git, pendientes)
            hallazgos += self._hooks(os.path.join(git, "hooks"), pendientes)
            hallazgos += self._gitmodules(os.path.join(proyecto, ".gitmodules"), pendientes)
            hallazgos += self._gitattributes(os.path.join(proyecto, ".gitattributes"), pendientes)
        self.no_revisados = tuple(pendientes)
        return hallazgos

    # ---- .git/config ----------------------------------------------------------------------------------------

    def _config(self, git: str, pendientes: list[NoRevisado]) -> list[Finding]:
        ruta = os.path.join(git, "config")
        if self._metadatos(ruta, pendientes) is None:
            return []
        self._principal = os.path.normcase(os.path.abspath(ruta))
        lectura = leer_con_includes(
            leer=lambda r: self._fs.leer_texto(Ruta(r)),
            existe=lambda r: self._existe(r),
            ruta=ruta,
        )
        hallazgos: list[Finding] = []
        for p in lectura.problemas:  # cualquier fallo del lector: TH-20 y no se pudo revisar
            pendientes.append(NoRevisado(Ruta(p.ruta), p.motivo))
            if p.th20:
                hallazgos.append(self._th20(p.ruta))
        for e in lectura.entradas:
            hallazgos += self._entrada(e)
        return _sin_duplicados(hallazgos)  # un include alcanzado por dos caminos no duplica hallazgos

    def _entrada(self, e: Entrada) -> list[Finding]:
        de_include = self._principal is not None and os.path.normcase(os.path.abspath(e.ruta)) != self._principal  # GT-13: lo de un include es dudoso
        if e.seccion == "url" and e.subseccion and _url_sospechosa(e.subseccion, es_submodulo=False):
            # [url "https://u:k@h/"] insteadOf = ...: la credencial está en el nombre de la subsección
            clave = _url_con_clave_literal(e.subseccion) and not de_include
            return [self._hallazgo(e.ruta, e.linea, Tipo.GIT_REMOTO_SOSPECHOSO, Proveedor.CODIGO, clave)]
        if e.seccion in ("remote", "submodule") and e.nombre in ("url", "pushurl") and e.valor is not None:
            if _url_sospechosa(e.valor, es_submodulo=e.seccion == "submodule"):
                clave = _url_con_clave_literal(e.valor) and not de_include  # relleno, token por prefijo o forma rara: no es certeza
                return [self._hallazgo(e.ruta, e.linea, Tipo.GIT_REMOTO_SOSPECHOSO, Proveedor.CODIGO, clave)]
            return []
        programa, sugerencia = _ejecuta_programa(e)
        if not programa:
            return []
        if sugerencia is not None:
            self.sugerencias[(Location(Ruta(e.ruta)).ruta, e.linea)] = sugerencia
        dudoso = (e.seccion, e.nombre) == ("core", "hookspath") or de_include or e.peculiar  # GT-05 (husky), GT-13 (include), GT-09 (formato)
        return [self._hallazgo(e.ruta, e.linea, Tipo.GIT_EJECUTA_PROGRAMAS, Proveedor.NO_APLICA, not dudoso)]

    # ---- hooks: solo se listan los nombres ---------------------------------------------------------------------

    def _hooks(self, carpeta: str, pendientes: list[NoRevisado]) -> list[Finding]:
        meta = self._metadatos(carpeta, pendientes)
        if meta is None:
            return []
        if not meta.es_carpeta or meta.es_enlace:
            pendientes.append(NoRevisado(meta.ruta, MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR))
            return [self._th20(meta.ruta)]
        try:
            entradas = list(self._fs.listar(meta.ruta_real or meta.ruta))
        except (OSError, ArchivoNoLegible, ValueError):
            pendientes.append(NoRevisado(meta.ruta, MotivoNoRevisado.ARCHIVO_ILEGIBLE))
            return [self._th20(meta.ruta)]
        hallazgos: list[Finding] = []
        for entrada in entradas:
            nombre = os.path.basename(entrada.ruta)
            if nombre.lower().endswith(".sample") or entrada.es_carpeta and not entrada.es_enlace:
                continue
            if entrada.es_enlace or not entrada.es_regular:  # git ejecuta un hook enlazado: se reporta y se informa
                pendientes.append(NoRevisado(entrada.ruta, MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR))
            hallazgos.append(self._hallazgo(entrada.ruta, Linea.NO_DETERMINADA, Tipo.GIT_EJECUTA_PROGRAMAS, Proveedor.NO_APLICA,
                                            cierto=False))  # GT-07: el bit de ejecución no está verificado
        return hallazgos

    # ---- .gitmodules y .gitattributes -----------------------------------------------------------------------------

    def _gitmodules(self, ruta: str, pendientes: list[NoRevisado]) -> list[Finding]:
        if self._metadatos(ruta, pendientes) is None:
            return []
        try:
            entradas = parsear_config(self._fs.leer_texto(Ruta(ruta)))
        except ArchivoNoLegible as error:
            pendientes.append(NoRevisado(Ruta(ruta), error.motivo))
            return [self._th20(ruta)]
        except (ConfigNoInterpretable, RecursionError, ValueError):
            pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE))
            return [self._th20(ruta)]
        # git solo lee de este archivo las variables ``submodule.*``: lo demás no se evalúa
        self._principal = None
        propias = (Entrada(e.seccion, e.subseccion, e.nombre, e.valor, e.linea, ruta) for e in entradas
                   if e.seccion == "submodule" and e.nombre == "url")
        return _sin_duplicados([h for e in propias for h in self._entrada(e)])

    def _gitattributes(self, ruta: str, pendientes: list[NoRevisado]) -> list[Finding]:
        """Se lee solo para saber si se puede leer; un filtro se reporta por su definición en la configuración."""
        if self._metadatos(ruta, pendientes) is None:
            return []
        try:
            self._fs.leer_texto(Ruta(ruta))
        except ArchivoNoLegible as error:
            pendientes.append(NoRevisado(Ruta(ruta), error.motivo))
            return [self._th20(ruta)]
        return []

    # ---- ayudas -------------------------------------------------------------------------------------------------------

    def _metadatos(self, ruta: str, pendientes: list[NoRevisado]) -> Metadatos | None:
        try:
            return self._fs.metadatos(Ruta(ruta))
        except OSError:
            pendientes.append(NoRevisado(Ruta(ruta), MotivoNoRevisado.ARCHIVO_ILEGIBLE))
            return None

    def _existe(self, ruta: str) -> bool:
        try:
            return self._fs.metadatos(Ruta(ruta)) is not None
        except OSError:
            return True  # que decida la lectura segura

    def _th20(self, ruta: str) -> Finding:
        return self._hallazgo(ruta, Linea.NO_DETERMINADA, Tipo.GIT_NO_INTERPRETABLE, Proveedor.NO_APLICA)

    @staticmethod
    def _hallazgo(ruta: str, linea: int | Linea, tipo: Tipo, proveedor: Proveedor, cierto: bool = True) -> Finding:
        return Finding(
            ubicacion=Location(Ruta(ruta), linea),
            tipo=tipo,
            proveedor=proveedor,
            nivel=Nivel.HIPOTESIS,
            motivo=Motivo.NO_DETERMINADO,
            ajeno_a_tarea=Ajeno.NO_DETERMINADO,
            plataforma=Plataforma.NO_DETERMINADA,
            agente=Etiqueta("sin-agente"),
            postura=Postura.NO_DETERMINADA,
            certeza=Certeza.COMPLETA if cierto else Certeza.DUDOSA,
        )
