"""Modelo de hallazgo: Finding, Location y enumeraciones (Nivel, Tipo, Postura, etc.).

Un hallazgo es un elemento del entorno que un agente de IA podría alcanzar. Tiene ocho campos
(PRD, FR-9): (1) ubicación exacta (archivo y línea, o "línea no determinada"); (2) qué es y de
quién (tipo y proveedor, sin valor); (3) nivel de confianza y por qué; (4) si es ajeno a la tarea;
(5) plataforma y agente; (6) postura del agente (reglas allow/ask/deny); (7) qué hacer;
(8) qué significa.

Regla no negociable (FR-3): el hallazgo NUNCA contiene el valor de un secreto. Se garantiza por
diseño, no por disciplina:

- No existe ningún campo para guardar un valor.
- Los únicos campos de texto son ``Ruta`` y ``Etiqueta`` (tipos etiquetados). ``Ruta`` se limpia
  de secuencias de escape de terminal; ``Etiqueta`` solo admite un identificador corto
  (letras, números, punto, guion y guion bajo), sin espacios ni signos como ``=``.
- Los demás campos son enumeraciones, enteros o booleanos.
- Los campos 7 y 8 ("qué hacer", "qué significa") no se guardan: salen de un catálogo fijo, en
  español e inglés, por tipo de hallazgo. No se usa ningún modelo de lenguaje.

Solo biblioteca estándar. Las clases son inmutables (``frozen``) y con ``slots``.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, NewType

# TODO(Q4): tratamiento de falsos positivos y secretos de ejemplo (.env.example): decisión abierta.
# TODO(Q8): ¿se detecta "el mismo secreto en dos sitios"? Decisión abierta; no definir identificadores por contenido.

__all__ = [
    "CAMPOS_HALLAZGO",
    "CATALOGO_EXPLICACIONES",
    "FUENTE_VERIFICADA",
    "Ajeno",
    "Certeza",
    "Etiqueta",
    "Finding",
    "Idioma",
    "Linea",
    "Location",
    "Motivo",
    "Nivel",
    "Plataforma",
    "Postura",
    "Proveedor",
    "Ruta",
    "RutaReal",
    "Tipo",
    "etiqueta",
    "fuente_verificada",
    "limpiar_ruta",
    "ordenar",
    "texto_de_motivo",
]

# --- Textos etiquetados -------------------------------------------------------------------

Ruta = NewType("Ruta", str)
"""Ruta de archivo ya limpia de caracteres de control (ver ``limpiar_ruta``)."""

RutaReal = NewType("RutaReal", str)
"""La ruta tal cual existe en disco (puede traer caracteres de control). SOLO para reabrir el archivo: nunca se imprime."""

Etiqueta = NewType("Etiqueta", str)
"""Identificador corto (p. ej. nombre de un agente). Nunca texto libre (ver ``etiqueta``)."""

_ETIQUETA_RE = re.compile(r"[A-Za-z0-9_.\-]{1,64}")
# Secuencias de escape de terminal: OSC (ESC ]...BEL o ESC \), CSI (ESC [...) y escapes cortos.
_ESCAPES_RE = re.compile(
    r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)?"  # OSC: título de ventana, enlaces, etc.
    r"|\x1b\[[0-?]*[ -/]*[@-~]"  # CSI: colores, mover cursor, borrar pantalla
    r"|\x1b[@-Z\\-_]"  # escapes de dos caracteres
)
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_CATEGORIAS_OCULTAS = frozenset({"Cf", "Zl", "Zp"})


def limpiar_ruta(texto: str) -> Ruta:
    """Quita secuencias de escape y caracteres de control de una ruta.

    Una ruta con ``\\x1b[2J`` (borrar pantalla) o un título de ventana falso podría engañar a
    quien lea el reporte en una terminal. Lo que queda es texto imprimible.
    """
    sin_escapes = _ESCAPES_RE.sub("", texto)
    sin_control = _CONTROL_RE.sub("", sin_escapes)
    # Controles de dirección (U+202A-202E, U+2066-2069), ancho cero (U+200B-200D, U+2060, U+FEFF) y
    # el resto de la categoría Cf (formato), más separadores de línea y párrafo (Zl, Zp): no se
    # dibujan o cambian el orden visual, y podrían disfrazar una extensión.
    return Ruta("".join(c for c in sin_control if unicodedata.category(c) not in _CATEGORIAS_OCULTAS))


def etiqueta(texto: str) -> Etiqueta:
    """Valida un identificador corto; lanza ``ValueError`` si no lo es."""
    if not _ETIQUETA_RE.fullmatch(texto):
        raise ValueError("la etiqueta debe ser un identificador corto (letras, números, . - _)")
    return Etiqueta(texto)


# --- Enumeraciones ------------------------------------------------------------------------


class Nivel(Enum):
    """Nivel de confianza del hallazgo (FR-5). El valor numérico es su prioridad en el reporte."""

    COMPROBADO = "comprobado"
    POTENCIAL = "potencial"
    HIPOTESIS = "hipotesis"

    @property
    def prioridad(self) -> int:
        """0 = más grave (se muestra primero)."""
        return _PRIORIDAD_NIVEL[self]


_PRIORIDAD_NIVEL = {Nivel.COMPROBADO: 0, Nivel.POTENCIAL: 1, Nivel.HIPOTESIS: 2}


class Tipo(Enum):
    """Los 20 tipos de hallazgo del catálogo del MVP (FR-18, TH-1 a TH-20)."""

    CREDENCIAL_EN_ARCHIVO = "TH-1"
    CLAVE_PRIVADA_SSH = "TH-2"
    CREDENCIALES_DE_NUBE = "TH-3"
    VARIABLE_DE_ENTORNO = "TH-4"
    CONTEXTO_SOSPECHOSO = "TH-5"
    ENLACE_FUERA_DEL_PROYECTO = "TH-6"
    REGLA_PERMISIVA = "TH-7"
    CAPACIDAD_DE_SHELL = "TH-8"
    SCRIPT_DE_DESPLIEGUE = "TH-9"
    PLATAFORMA_SIN_SANDBOX = "TH-10"
    DEFINICION_DE_AGENTE = "TH-11"
    TEXTO_INVISIBLE = "TH-12"
    INSTRUCCIONES_FUERA_DE_PROYECTO = "TH-13"
    HOOK_O_MCP_DE_COMANDO = "TH-14"
    SALTO_DE_PERMISOS = "TH-15"
    TAREA_AL_ABRIR_CARPETA = "TH-16"
    SECRETO_DE_ALTO_PODER = "TH-17"
    GIT_EJECUTA_PROGRAMAS = "TH-18"
    GIT_REMOTO_SOSPECHOSO = "TH-19"
    GIT_NO_INTERPRETABLE = "TH-20"


class Motivo(Enum):
    """Por qué tiene ese nivel (tabla de FR-5). Sale de un catálogo, no de texto libre."""

    EXISTE_LEGIBLE_SIN_REGLA = "existe_legible_sin_regla"
    NO_DETERMINADO = "no_determinado"
    REGLA_DENY = "regla_deny"
    REGLA_ASK = "regla_ask"
    EXISTE_NO_LEGIBLE = "existe_no_legible"
    SIN_FUENTE_VERIFICADA = "sin_fuente_verificada"
    INDICIO_DEBIL = "indicio_debil"
    NO_CONFIRMADO_INDEPENDIENTE = "no_confirmado_independiente"  # la segunda vía (Historia 18) discrepa o no puede
    SIN_CERTEZA_DEL_ARCHIVO = "sin_certeza_del_archivo"  # el propio archivo no permite afirmarlo sin ambigüedad


class Certeza(Enum):
    """¿El texto o los metadatos del propio archivo permiten afirmar el hecho sin ambigüedad? (Historia 11).

    ``DUDOSA``: valor de relleno, ayudante de credenciales, un hook cuyo bit de ejecución no se verifica...
    Un detector la marca; el cálculo del nivel la usa para dejar el hallazgo en potencial.
    """

    COMPLETA = "completa"
    DUDOSA = "dudosa"


class Ajeno(Enum):
    """¿El elemento es ajeno a la tarea del agente? (FR-9; guía: README y ``--tarea``)."""

    SI = "si"
    NO = "no"
    NO_DETERMINADO = "no_determinado"


class Plataforma(Enum):
    """Programa anfitrión que ejecuta al agente."""

    CLAUDE_CODE = "claude_code"
    OPENCODE = "opencode"
    NO_DETERMINADA = "no_determinada"


class Postura(Enum):
    """Postura del agente ante el elemento: reglas allow, ask o deny de la plataforma (FR-6)."""

    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"
    SIN_REGLA = "sin_regla"
    NO_DETERMINADA = "no_determinada"


class Proveedor(Enum):
    """Quién emite la credencial, sin valor alguno.

    TODO(FR-9): el PRD dice "tipo y proveedor" sin fijar la lista de proveedores. Se elige la
    opción más simple: una enumeración corta; ampliarla es agregar miembros.
    """

    IA = "ia"
    PAGOS = "pagos"
    CODIGO = "codigo"
    DESPLIEGUE = "despliegue"
    BASE_DE_DATOS = "base_de_datos"
    NUBE = "nube"
    SSH = "ssh"
    FIRMA = "firma"
    NO_APLICA = "no_aplica"
    DESCONOCIDO = "desconocido"


class Idioma(Enum):
    """Idiomas del producto (FR-11)."""

    ES = "es"
    EN = "en"


class Linea(Enum):
    """Marcador explícito de una línea que no se pudo determinar (nunca 0 ni un número inventado).

    TODO(FR-10): no se distingue "no aplica" (p. ej. variable de entorno sin archivo) de
    "no determinada"; ambos usan este marcador hasta que el PRD los separe.
    """

    NO_DETERMINADA = "linea no determinada"


# --- Ubicación ----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Location:
    """Archivo y línea. La línea es un entero >= 1 o ``Linea.NO_DETERMINADA``."""

    ruta: Ruta
    linea: int | Linea = Linea.NO_DETERMINADA
    ruta_real: RutaReal | None = field(default=None, repr=False)  # la ruta antes de limpiarla (Historia 13)

    def __post_init__(self) -> None:
        # Se guarda la ruta tal cual llegó y se limpia ``ruta`` aquí, para que ninguna vía de creación deje pasar escapes.
        if self.ruta_real is None:
            object.__setattr__(self, "ruta_real", RutaReal(str(self.ruta)))
        object.__setattr__(self, "ruta", limpiar_ruta(self.ruta))
        linea = self.linea
        if isinstance(linea, bool) or not isinstance(linea, (int, Linea)):
            raise TypeError("linea debe ser un entero o Linea.NO_DETERMINADA")
        if isinstance(linea, int) and linea < 1:
            raise ValueError("linea empieza en 1; para 'no determinada' use Linea.NO_DETERMINADA")

    @property
    def linea_determinada(self) -> bool:
        return isinstance(self.linea, int)

    def a_dict(self) -> dict[str, Any]:
        """``linea`` es un entero o el texto ``"linea no determinada"``."""
        linea = self.linea.value if isinstance(self.linea, Linea) else self.linea
        return {"ruta": self.ruta, "linea": linea}


# --- Catálogos fijos (sin modelo de lenguaje) ---------------------------------------------

# FR-7: indicador "fuente verificada: sí/no" por tipo. Un tipo ausente cuenta como "no".
# TODO(FR-7): el PRD dice que el dato se rellena desde el checklist del oráculo; aún no se
# transcribe, así que todos quedan en False (lo más prudente: nunca llegan a "comprobado" por
# esta vía). Las historias de detectores lo actualizarán.
FUENTE_VERIFICADA: dict[Tipo, bool] = {tipo: False for tipo in Tipo}


def fuente_verificada(tipo: Tipo) -> bool:
    """Indicador de fuente verificada; si el tipo no tiene indicador, vale ``False``."""
    return FUENTE_VERIFICADA.get(tipo, False)


# Para cada tipo e idioma: (qué significa, qué hacer). Las siglas se explican la primera vez.
CATALOGO_EXPLICACIONES: dict[Tipo, dict[Idioma, tuple[str, str]]] = {
    Tipo.CREDENCIAL_EN_ARCHIVO: {
        Idioma.ES: (
            'Un archivo del proyecto guarda una credencial (una clave o contraseña que da acceso a un servicio). Un agente que pueda leer el proyecto podría leerla.',
            'Saca la credencial del proyecto o guárdala en un gestor de secretos (un programa que guarda claves cifradas) y rótala (rotar es cambiarla por una nueva y desactivar la vieja) si estuvo expuesta.',
        ),
        Idioma.EN: (
            'A project file stores a credential (a key or password that grants access to a service). An agent that can read the project could read it.',
            'Move the credential out of the project or into a secrets manager (a program that stores keys encrypted), and rotate it (replace it with a new one and disable the old one) if it was exposed.',
        ),
    },
    Tipo.CLAVE_PRIVADA_SSH: {
        Idioma.ES: (
            'Existe una clave privada SSH (Secure Shell: acceso remoto a servidores y repositorios) que abre servidores sin pedir contraseña.',
            'Usa claves con frase de paso (una contraseña extra que protege la clave), mantén al agente lejos de esa carpeta y revisa sus permisos.',
        ),
        Idioma.EN: (
            'A private SSH key (Secure Shell: remote access to servers and repositories) exists and opens servers without asking for a password.',
            'Use keys protected by a passphrase (an extra password that protects the key), keep the agent away from that folder and review its permissions.',
        ),
    },
    Tipo.CREDENCIALES_DE_NUBE: {
        Idioma.ES: (
            'Existe un archivo de credenciales de una cuenta en la nube (servicios en internet). Con él se podrían crear, leer o borrar recursos de esa cuenta.',
            'Usa credenciales temporales con solo los permisos que la tarea necesita y mantén el archivo fuera de donde el agente puede llegar.',
        ),
        Idioma.EN: (
            'A cloud account credentials file exists. With it, resources of that account could be created, read or deleted.',
            'Use temporary credentials with only the permissions the task needs, and keep the file where the agent cannot access it.',
        ),
    },
    Tipo.VARIABLE_DE_ENTORNO: {
        Idioma.ES: (
            'Una variable de entorno con nombre de credencial está disponible para los programas que lance el agente. Solo se informa su nombre, nunca su valor.',
            'Quita la variable del entorno del agente o limpia el entorno antes de iniciarlo.',
        ),
        Idioma.EN: (
            'An environment variable named like a credential is available to programs the agent launches. Only its name is reported, never its value.',
            "Remove the variable from the agent's environment or clean the environment before starting it.",
        ),
    },
    Tipo.CONTEXTO_SOSPECHOSO: {
        Idioma.ES: (
            'Un archivo de contexto (instrucciones que el agente lee, como CLAUDE.md o AGENTS.md) contiene un texto que parece pedir saltarse reglas o sacar datos.',
            'Revisa ese archivo a mano y elimina las instrucciones que no escribiste tú.',
        ),
        Idioma.EN: (
            'A context file (instructions the agent reads, such as CLAUDE.md or AGENTS.md) contains text that seems to ask to bypass rules or leak data.',
            'Review that file by hand and remove instructions you did not write.',
        ),
    },
    Tipo.ENLACE_FUERA_DEL_PROYECTO: {
        Idioma.ES: (
            'Un enlace (junction: enlace de carpeta de Windows) parece estar en el proyecto pero lleva a otro lugar del equipo. No se entró en él.',
            'Confirma que el destino es intencional o elimina el enlace.',
        ),
        Idioma.EN: (
            'A link (junction: Windows folder link) looks like part of the project but leads elsewhere on the machine. It was not entered.',
            'Confirm the destination is intentional or remove the link.',
        ),
    },
    Tipo.REGLA_PERMISIVA: {
        Idioma.ES: (
            'La configuración de la plataforma permite al agente acciones muy amplias (leer, editar, ejecutar comandos o descargar de la web) sin pedir confirmación.',
            'Cambia esas reglas a «pide confirmación» (el agente pregunta antes) o «lo bloquea» (el agente no puede) donde no sean necesarias.',
        ),
        Idioma.EN: (
            'The platform configuration lets the agent do very broad actions (read, edit, run commands or download from the web) without asking.',
            'Change those rules to «asks first» (the agent asks before acting) or «blocks it» (the agent cannot) wherever they are not needed.',
        ),
    },
    Tipo.CAPACIDAD_DE_SHELL: {
        Idioma.ES: (
            'El agente puede ejecutar comandos en tu equipo (la línea de comandos, llamada shell): con eso llega a lo que cualquier programa tuyo pueda tocar.',
            'Limita los comandos permitidos o exige confirmación antes de ejecutar comandos.',
        ),
        Idioma.EN: (
            'The agent can run commands on your computer (the command line, called a shell): with that it reaches whatever any of your programs can reach.',
            'Restrict the allowed commands or require confirmation before running commands.',
        ),
    },
    Tipo.SCRIPT_DE_DESPLIEGUE: {
        Idioma.ES: (
            'Hay un script con nombre de despliegue que el agente podría lanzar y que publicaría cambios. Se reconoce solo por el nombre, no por su contenido.',
            'Comprueba qué hace el script y protege su ejecución para que el agente pregunte antes o no pueda lanzarlo.',
        ),
        Idioma.EN: (
            'A script named like a deployment one exists that the agent could launch and that would publish changes. It is recognized by name only, not by content.',
            'Check what the script does and protect its execution so the agent asks first or cannot launch it.',
        ),
    },
    Tipo.PLATAFORMA_SIN_SANDBOX: {
        Idioma.ES: (
            'La plataforma no tiene sandbox (una caja que limita lo que el agente puede tocar): las reglas son promesas de la plataforma, no barreras del sistema operativo.',
            'Considera ejecutar el agente en un entorno aislado, como un contenedor o una máquina virtual.',
        ),
        Idioma.EN: (
            'The platform has no sandbox (a box that limits what the agent can touch): rules are promises of the platform, not operating system barriers.',
            'Consider running the agent in an isolated environment, such as a container or a virtual machine.',
        ),
    },
    Tipo.DEFINICION_DE_AGENTE: {
        Idioma.ES: (
            'Un archivo define un agente con las herramientas que tiene permitidas. Lo que puede tocar depende de esas herramientas y de la plataforma.',
            'Revisa las herramientas permitidas y deja solo las necesarias.',
        ),
        Idioma.EN: (
            'A file defines an agent with the tools it is allowed to use. What it can touch depends on those tools and on the platform.',
            'Review the allowed tools and keep only the necessary ones.',
        ),
    },
    Tipo.TEXTO_INVISIBLE: {
        Idioma.ES: (
            'Un archivo de instrucciones contiene caracteres que no se dibujan en pantalla (caracteres Unicode invisibles; Unicode es el estándar que define las letras y símbolos de todos los idiomas) pero que un agente sí lee: podría haber una orden que no ves.',
            'Abre el archivo en un editor que muestre los caracteres ocultos y elimínalos.',
        ),
        Idioma.EN: (
            'An instructions file contains characters that are not drawn on screen (invisible Unicode characters; Unicode is the standard that defines the letters and symbols of all languages) but that an agent does read: there could be an order you cannot see.',
            'Open the file in an editor that shows hidden characters and remove them.',
        ),
    },
    Tipo.INSTRUCCIONES_FUERA_DE_PROYECTO: {
        Idioma.ES: (
            'Hay un archivo de instrucciones suelto fuera de un proyecto: un agente lanzado desde esa carpeta lo leería como si fuera de confianza.',
            'Muévelo a un proyecto que controles o elimínalo.',
        ),
        Idioma.EN: (
            'A loose instructions file sits outside a project: an agent launched from that folder would read it as if it were trusted.',
            'Move it into a project you control or delete it.',
        ),
    },
    Tipo.HOOK_O_MCP_DE_COMANDO: {
        Idioma.ES: (
            'La configuración del proyecto define un hook (comando que una herramienta lanza sola ante un evento) o un servidor MCP (conexión del agente con herramientas externas) que arranca un programa cuando ocurre un evento, por ejemplo al abrir la carpeta.',
            'Revisa ese comando y desactiva el que no reconozcas antes de abrir el proyecto.',
        ),
        Idioma.EN: (
            "The project configuration defines a hook (a command a tool launches by itself on an event) or an MCP server (the agent's link to external tools) that starts a program when an event happens, for example when the folder is opened.",
            'Review that command and disable any you do not recognize before opening the project.',
        ),
    },
    Tipo.SALTO_DE_PERMISOS: {
        Idioma.ES: (
            'La configuración hace que el agente salte las confirmaciones de permisos: actúa sin pedir permiso.',
            'Quita esa opción y deja que el agente pida confirmación.',
        ),
        Idioma.EN: (
            'The configuration makes the agent skip permission confirmations: it acts without asking.',
            'Remove that option and let the agent ask for confirmation.',
        ),
    },
    Tipo.TAREA_AL_ABRIR_CARPETA: {
        Idioma.ES: (
            'Hay una tarea configurada para ejecutarse sola al abrir la carpeta en el editor.',
            'Elimina la tarea o desactiva las tareas automáticas del editor.',
        ),
        Idioma.EN: (
            'A task is configured to run by itself when the folder is opened in the editor.',
            'Delete the task or turn off automatic tasks in the editor.',
        ),
    },
    Tipo.SECRETO_DE_ALTO_PODER: {
        Idioma.ES: (
            'Hay un secreto de plataforma o de despliegue, reconocido por su nombre, en un archivo. Lo que ese secreto permite hacer no se ve.',
            'Retíralo del proyecto, rótala (rotar es cambiarla por una nueva y desactivar la vieja) y limita lo que permite en la plataforma.',
        ),
        Idioma.EN: (
            'A platform or deployment secret, recognized by its name, sits in a file. What that secret allows is not visible.',
            'Remove it from the project, rotate it (replace it with a new one and disable the old one) and limit what it allows on the platform.',
        ),
    },
    Tipo.GIT_EJECUTA_PROGRAMAS: {
        Idioma.ES: (
            'La configuración de git (el programa que guarda el historial del proyecto), o sus hooks (comandos que git lanza solos ante un evento) y filtros, puede ejecutar programas al hacer operaciones comunes sobre el repositorio.',
            'Revisa esas claves y hooks y elimina los que no reconozcas.',
        ),
        Idioma.EN: (
            'The git configuration (git is the program that keeps the project history), or its hooks (commands git launches by itself on an event) and filters, can run programs during common operations on the repository.',
            'Review those keys and hooks and remove any you do not recognize.',
        ),
    },
    Tipo.GIT_REMOTO_SOSPECHOSO: {
        Idioma.ES: (
            'Un remoto o submódulo de git (la dirección de donde se bajan o suben los cambios) trae una credencial dentro de la dirección o una dirección sospechosa.',
            'Quita la credencial de la dirección, rótala (rotar es cambiarla por una nueva y desactivar la vieja) y usa un ayudante de credenciales.',
        ),
        Idioma.EN: (
            'A git remote or submodule (the address changes are downloaded from or uploaded to) carries a credential inside the address, or a suspicious address.',
            'Remove the credential from the address, rotate it (replace it with a new one and disable the old one) and use a credential helper.',
        ),
    },
    Tipo.GIT_NO_INTERPRETABLE: {
        Idioma.ES: (
            'La configuración de git no pudo interpretarse con el lector propio de AgentReach; no se ejecutó nada.',
            'Revisa el archivo de configuración de git a mano.',
        ),
        Idioma.EN: (
            "The git configuration could not be interpreted by AgentReach's own reader; nothing was run.",
            'Review the git configuration file by hand.',
        ),
    },
}

# Textos fijos del motivo del nivel (FR-5), por idioma.
_TEXTO_MOTIVO: dict[Motivo, dict[Idioma, str]] = {
    Motivo.EXISTE_LEGIBLE_SIN_REGLA: {
        Idioma.ES: "Existe, el sistema operativo permite leerlo y ninguna regla del agente lo impide",
        Idioma.EN: "It exists, the operating system allows reading it and no agent rule prevents it",
    },
    Motivo.NO_DETERMINADO: {Idioma.ES: "No determinado", Idioma.EN: "Not determined"},
    Motivo.REGLA_DENY: {
        Idioma.ES: "Protegido por política del agente, no por barrera del sistema operativo",
        Idioma.EN: "Protected by agent policy, not by an operating system barrier",
    },
    Motivo.REGLA_ASK: {
        Idioma.ES: "El agente debe pedir confirmación antes de leerlo",
        Idioma.EN: "The agent must ask for confirmation before reading it",
    },
    Motivo.EXISTE_NO_LEGIBLE: {
        Idioma.ES: "Existe y hoy el agente no puede leerlo con los permisos verificados",
        Idioma.EN: "It exists and today the agent cannot read it with the verified permissions",
    },
    Motivo.SIN_FUENTE_VERIFICADA: {
        Idioma.ES: "Sin fuente verificada",
        Idioma.EN: "No verified source",
    },
    Motivo.INDICIO_DEBIL: {
        Idioma.ES: "Indicio débil o indirecto",
        Idioma.EN: "Weak or indirect hint",
    },
    Motivo.NO_CONFIRMADO_INDEPENDIENTE: {
        Idioma.ES: "No se pudo confirmar de forma independiente",
        Idioma.EN: "Could not be confirmed independently",
    },
    Motivo.SIN_CERTEZA_DEL_ARCHIVO: {
        Idioma.ES: "No se puede determinar con certeza desde el propio archivo",
        Idioma.EN: "Cannot be determined with certainty from the file itself",
    },
}


def texto_de_motivo(motivo: Motivo, idioma: Idioma = Idioma.ES) -> str:
    """Texto fijo del porqué de un nivel (el mismo que ``Finding.texto_motivo``)."""
    return _TEXTO_MOTIVO[motivo][idioma]


# --- Hallazgo -----------------------------------------------------------------------------

# Los ocho campos de FR-9, en orden. Seis son campos de la clase; "qué hacer" y "qué significa"
# se obtienen del catálogo fijo con ``que_hacer(idioma)`` y ``que_significa(idioma)``.
CAMPOS_HALLAZGO: tuple[str, ...] = (
    "ubicacion",
    "tipo",  # (2) qué es; el "de quién" es ``proveedor``
    "nivel",  # (3) con su ``motivo``
    "ajeno_a_tarea",
    "plataforma",  # (5) con su ``agente``
    "postura",
    "que_hacer",
    "que_significa",
)


@dataclass(frozen=True, slots=True)
class Finding:
    """Un hallazgo. Inmutable y sin ningún campo capaz de guardar el valor de un secreto."""

    ubicacion: Location
    tipo: Tipo
    proveedor: Proveedor
    nivel: Nivel
    motivo: Motivo
    ajeno_a_tarea: Ajeno
    plataforma: Plataforma
    agente: Etiqueta | None
    postura: Postura
    regla: Location | None = None  # archivo y línea de la regla que fija la postura
    certeza: Certeza = Certeza.COMPLETA  # DUDOSA: el propio archivo no permite afirmarlo sin ambigüedad (Historia 11)

    def __post_init__(self) -> None:
        # TODO(FR-7): aplicar "sin fuente verificada, máximo potencial" corresponde al cálculo
        # del nivel (Historia 11), porque FR-7 solo limita el reconocimiento por nombre o prefijo.
        if self.agente is not None:
            etiqueta(self.agente)

    def que_significa(self, idioma: Idioma = Idioma.ES) -> str:
        """Campo 8: explicación en lenguaje llano, del catálogo fijo."""
        return CATALOGO_EXPLICACIONES[self.tipo][idioma][0]

    def que_hacer(self, idioma: Idioma = Idioma.ES) -> str:
        """Campo 7: acción recomendada, del catálogo fijo."""
        return CATALOGO_EXPLICACIONES[self.tipo][idioma][1]

    def texto_motivo(self, idioma: Idioma = Idioma.ES) -> str:
        """Texto fijo del porqué del nivel."""
        return _TEXTO_MOTIVO[self.motivo][idioma]

    def clave_orden(self) -> tuple[int, int, str, int]:
        """Orden del reporte: nivel (comprobado primero), tipo, ruta y línea.

        Las líneas no determinadas van después de las numeradas.
        """
        linea = self.ubicacion.linea
        n = linea if isinstance(linea, int) else 2**31
        numero_tipo = int(self.tipo.value.split("-")[1])  # TH-2 antes que TH-12
        return (self.nivel.prioridad, numero_tipo, self.ubicacion.ruta, n)

    def a_dict(self, idioma: Idioma = Idioma.ES) -> dict[str, Any]:
        """Serializa a tipos simples (lo mismo que se pasa a JSON). Nunca incluye valores."""
        return {
            "ubicacion": self.ubicacion.a_dict(),
            "tipo": self.tipo.value,
            "proveedor": self.proveedor.value,
            "nivel": self.nivel.value,
            "motivo": self.motivo.value,
            "motivo_texto": self.texto_motivo(idioma),
            "ajeno_a_tarea": self.ajeno_a_tarea.value,
            "plataforma": self.plataforma.value,
            "agente": self.agente,
            "postura": self.postura.value,
            "regla": self.regla.a_dict() if self.regla else None,
            "fuente_verificada": fuente_verificada(self.tipo),
            "que_hacer": self.que_hacer(idioma),
            "que_significa": self.que_significa(idioma),
        }


def ordenar(hallazgos: list[Finding] | tuple[Finding, ...]) -> list[Finding]:
    """Ordena por nivel (comprobado, potencial, hipótesis) y luego por tipo, ruta y línea."""
    return sorted(hallazgos, key=Finding.clave_orden)
