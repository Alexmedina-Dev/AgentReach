"""Catálogo fijo de términos técnicos (Historias 32 y 33): 12 fichas, una por concepto, con su línea de terminal y su explicación larga.

Los textos son los del contrato de UX (``EXPERIENCE.md``, «Glosario y explicaciones»), copiados tal cual (la ficha 12, «camino de alcance», se añade en la Historia 33). Cada ficha existe en
español para «tú», español para «usted» e inglés; ningún texto remite a otra variante. No hay modelo de lenguaje: el mismo término
produce siempre el mismo texto, y ningún texto trae valores de secretos.

La terminal usa ``linea`` solo donde el término aparece. ``--detalle`` (y el HTML, Historia 33) usan ``que_es``,
``que_significa`` y ``que_hacer``. Es independiente del catálogo por tipo de hallazgo (``catalogo_explicaciones``).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agentreach.contracts import Idioma
from agentreach.core.catalogo_explicaciones import Tono

__all__ = ["ETIQUETAS", "FICHAS", "PUNTO_CIEGO", "Ficha", "Termino", "etiquetas", "explicacion", "linea", "nombre", "punto_ciego"]


class Termino(Enum):
    NIVEL_COMPROBADO = "nivel_comprobado"
    NIVEL_POTENCIAL = "nivel_potencial"
    NIVEL_HIPOTESIS = "nivel_hipotesis"
    NO_DETERMINADO = "no_determinado"
    NO_SE_PUDO_REVISAR = "no_se_pudo_revisar"
    HOOK = "hook"
    SANDBOX = "sandbox"
    CONFIGURADO_VS_ANALIZADO = "configurado_vs_analizado"
    AUTOCOMPROBACION = "autocomprobacion"
    LUGAR_NO_CONFIRMADO = "lugar_no_confirmado"
    CODIGO_DE_SALIDA = "codigo_de_salida"
    CAMINO_DE_ALCANCE = "camino_de_alcance"


@dataclass(frozen=True, slots=True)
class Variantes:
    """El mismo texto en las tres variantes: español de tú, español de usted e inglés."""

    tu: str
    usted: str
    en: str

    def de(self, idioma: Idioma, tono: Tono) -> str:
        if idioma is Idioma.EN:
            return self.en
        return self.usted if tono is Tono.FORMAL else self.tu


@dataclass(frozen=True, slots=True)
class Ficha:
    nombre: tuple[str, str]  # (español, inglés)
    linea: Variantes  # terminal: una frase de 90 caracteres o menos
    que_es: Variantes
    que_significa: Variantes
    que_hacer: Variantes


def _igual(es: str, en: str) -> Variantes:
    """Texto que no cambia entre «tú» y «usted»."""
    return Variantes(es, es, en)


ETIQUETAS: dict[str, tuple[str, str, str]] = {
    "tu": ("Qué es", "Qué significa para ti", "Qué puedes hacer"),
    "usted": ("Qué es", "Qué significa para usted", "Qué puede hacer"),
    "en": ("What it is", "What it means for you", "What you can do"),
}

# La fórmula neutra de «no determinado por un hook» (EXPERIENCE.md, ficha 6): lo que explica por qué todo sale «potencial».
PUNTO_CIEGO = Variantes(
    "No es una alarma ni una garantía: es un punto ciego; depende de lo que haga ese hook.",
    "No es una alarma ni una garantía: es un punto ciego; depende de lo que haga ese hook.",
    "Neither an alarm nor a guarantee: a blind spot; it depends on what that hook does.",
)

FICHAS: dict[Termino, Ficha] = {
    Termino.NIVEL_COMPROBADO: Ficha(
        ("Nivel comprobado", "Verified level"),
        Variantes(
            "Comprobado: el agente puede llegar a esto hoy. Atiéndelo primero.",
            "Comprobado: el agente puede llegar a esto hoy. Atiéndalo primero.",
            "Verified: the agent can reach this today. Deal with it first."),
        Variantes(
            "AgentReach confirmó tres cosas a la vez: el archivo o dato existe, el sistema operativo deja leerlo a quien ejecuta el agente y ninguna regla del agente lo impide. El permiso se calcula con los datos que guarda el sistema sobre quién puede leer el archivo, sin abrirlo para probarlo.",
            "AgentReach confirmó tres cosas a la vez: el archivo o dato existe, el sistema operativo deja leerlo a quien ejecuta el agente y ninguna regla del agente lo impide. El permiso se calcula con los datos que guarda el sistema sobre quién puede leer el archivo, sin abrirlo para probarlo.",
            "AgentReach confirmed three things at once: the file or data exists, the operating system lets whoever runs the agent read it, and no agent rule blocks it. The permission is worked out from the data the system keeps about who can read the file, without opening it to test it."),
        Variantes(
            "hoy mismo el agente puede leerlo. No es una sospecha, aunque tampoco quiere decir que ya lo haya leído.",
            "hoy mismo el agente puede leerlo. No es una sospecha, aunque tampoco quiere decir que ya lo haya leído.",
            "the agent can read it today. It is not a suspicion, though it does not mean the agent already read it."),
        Variantes(
            "atiéndelo primero; cada hallazgo trae su paso concreto.",
            "atiéndalo primero; cada hallazgo trae su paso concreto.",
            "handle it first; each finding comes with its concrete step."),
    ),
    Termino.NIVEL_POTENCIAL: Ficha(
        ("Nivel potencial", "Potential level"),
        Variantes(
            "Potencial: probable, falta confirmar algo. No es un riesgo menor.",
            "Potencial: probable, falta confirmar algo. No es un riesgo menor.",
            "Potential: likely, but something is unconfirmed. It is not a lesser risk."),
        Variantes(
            "existe y el agente quizá pueda llegar, pero una de las tres cosas de «comprobado» no se pudo confirmar (por ejemplo, no se sabe qué decide un hook, un programa que se ejecuta antes de cada acción del agente, no se pudo determinar un permiso, o una regla del agente lo prohíbe pero esa regla es una promesa de la plataforma, no una barrera real del sistema).",
            "existe y el agente quizá pueda llegar, pero una de las tres cosas de «comprobado» no se pudo confirmar (por ejemplo, no se sabe qué decide un hook, un programa que se ejecuta antes de cada acción del agente, no se pudo determinar un permiso, o una regla del agente lo prohíbe pero esa regla es una promesa de la plataforma, no una barrera real del sistema).",
            "it exists and the agent may be able to reach it, but one of the three checks behind «verified» could not be confirmed (for example, what a hook decides is unknown; a hook is a program that runs before each agent action, a permission could not be determined, or an agent rule forbids it but that rule is a platform promise, not a real system barrier)."),
        Variantes(
            "AgentReach no lo descarta ni lo confirma. No es un riesgo menor: es una pregunta abierta.",
            "AgentReach no lo descarta ni lo confirma. No es un riesgo menor: es una pregunta abierta.",
            "AgentReach neither rules it out nor confirms it. It is not a lesser risk: it is an open question."),
        Variantes(
            "lee el motivo que acompaña a cada hallazgo; resuelve lo que falta o, si el dato es delicado, trátalo como si ya fuera comprobado.",
            "lea el motivo que acompaña a cada hallazgo; resuelva lo que falta o, si el dato es delicado, trátelo como si ya fuera comprobado.",
            "read the reason shown with each finding; settle what is missing or, if the data is sensitive, treat it as verified."),
    ),
    Termino.NIVEL_HIPOTESIS: Ficha(
        ("Nivel hipótesis", "Hypothesis level"),
        Variantes(
            "Hipótesis: indicio débil o indirecto; revísalo a mano. No es un acceso comprobado.",
            "Hipótesis: indicio débil o indirecto; revíselo a mano. No es un acceso comprobado.",
            "Hypothesis: a weak or indirect sign; check it by hand. Not a confirmed access."),
        _igual(
            "una señal débil o indirecta de que algo podría estar al alcance del agente.",
            "a weak or indirect sign that something might be within the agent's reach."),
        Variantes(
            "es una pista, no un acceso comprobado ni un hallazgo menor que puedas ignorar sin mirar.",
            "es una pista, no un acceso comprobado ni un hallazgo menor que pueda ignorar sin mirar.",
            "a lead, not a confirmed access, and not a minor item to skip without looking."),
        Variantes(
            "revísalo a mano; si resulta cierto, AgentReach lo mostraría en un nivel superior.",
            "revíselo a mano; si resulta cierto, AgentReach lo mostraría en un nivel superior.",
            "check it by hand; if it holds, AgentReach would show it at a higher level."),
    ),
    Termino.NO_DETERMINADO: Ficha(
        ("No determinado", "Undetermined"),
        _igual(
            "No determinado: AgentReach no supo interpretar parte de la configuración.",
            "Undetermined: AgentReach could not interpret part of the configuration."),
        Variantes(
            "el nivel de un hallazgo que AgentReach no puede fijar porque la configuración del agente (la tuya o la del proyecto) incluye algo que no sabe leer, por ejemplo un hook. El reporte dice en qué archivo y qué clave, sin mostrar valores.",
            "el nivel de un hallazgo que AgentReach no puede fijar porque la configuración del agente (la suya o la del proyecto) incluye algo que no sabe leer, por ejemplo un hook. El reporte dice en qué archivo y qué clave, sin mostrar valores.",
            "the level of a finding AgentReach cannot set because the agent's configuration (yours or the project's) contains something it cannot read, for example a hook. The report names the file and key, never the values."),
        _igual(
            "no es una alarma ni una garantía: es un punto ciego; depende de lo que haga ese hook (o esa función). Por eso nada que dependa de ello puede salir «comprobado» y sale «potencial».",
            "neither an alarm nor a guarantee: it is a blind spot; it depends on what that hook (or feature) does. That is why nothing depending on it can be «verified»; it shows as «potential»."),
        Variantes(
            "averigua qué hace esa función; si no la escribiste tú ni la reconoces, desactívala hasta saberlo.",
            "averigüe qué hace esa función; si no la escribió usted ni la reconoce, desactívela hasta saberlo.",
            "find out what that feature does; if you did not write it and do not recognize it, turn it off until you know."),
    ),
    Termino.NO_SE_PUDO_REVISAR: Ficha(
        ("No se pudo revisar", "Could not check"),
        _igual(
            "No se pudo revisar: AgentReach no llegó a mirar esto. Es un hueco, no un veredicto.",
            "Could not check: AgentReach did not get to look here. A gap, not a verdict."),
        Variantes(
            "partes del equipo o del proyecto que AgentReach no pudo mirar por distintos motivos; por ejemplo, un archivo demasiado grande o una ubicación sensible que no activaste.",
            "partes del equipo o del proyecto que AgentReach no pudo mirar por distintos motivos; por ejemplo, un archivo demasiado grande o una ubicación sensible que no activó.",
            "parts of the machine or project AgentReach could not look at, for different reasons; for example, a file that is too large or a sensitive location you did not enable."),
        _igual(
            "no sabemos qué hay ahí; no quiere decir que esté bien ni que esté mal.",
            "we do not know what is there; that does not mean it is fine or that it is bad."),
        Variantes(
            "cada motivo trae cómo resolverlo (por ejemplo, convertir un archivo a UTF-8 o activar la revisión de esa ubicación) y después puedes volver a ejecutar.",
            "cada motivo trae cómo resolverlo (por ejemplo, convertir un archivo a UTF-8 o activar la revisión de esa ubicación) y después puede volver a ejecutar.",
            "each reason says how to fix it (for example, convert a file to UTF-8 or enable checking that location), and then you can run it again."),
    ),
    Termino.HOOK: Ficha(
        ("Hook", "Hook"),
        _igual(
            "Hook: programa que corre antes de cada acción del agente y puede bloquearla.",
            "Hook: a program that runs before each agent action and can block it."),
        Variantes(
            "un hook es un programa que se ejecuta antes de cada acción del agente y puede aprobarla o bloquearla; puede venir de tu configuración o de la del proyecto.",
            "un hook es un programa que se ejecuta antes de cada acción del agente y puede aprobarla o bloquearla; puede venir de su configuración o de la del proyecto.",
            "a hook is a program that runs before each agent action and can approve or block it; it can come from your configuration or from the project's."),
        _igual(
            "AgentReach no sabe qué decide ese programa, así que no puede asegurar nada y por eso todo lo que depende de él sale potencial. No es una alarma ni una garantía: es un punto ciego; depende de lo que haga ese hook.",
            "AgentReach does not know what that program decides, so it cannot assure anything and everything depending on it shows as potential. Neither an alarm nor a guarantee: a blind spot; it depends on what that hook does."),
        Variantes(
            "si lo escribiste tú, comprueba qué decide. Si viene del proyecto y no lo escribiste tú, trátalo con desconfianza y no abras el proyecto con el agente hasta revisarlo.",
            "si lo escribió usted, compruebe qué decide. Si viene del proyecto y no lo escribió usted, trátelo con desconfianza y no abra el proyecto con el agente hasta revisarlo.",
            "if you wrote it, check what it decides. If it comes from the project and you did not write it, treat it with distrust and do not open the project with the agent until you have reviewed it."),
    ),
    Termino.SANDBOX: Ficha(
        ("Sandbox", "Sandbox"),
        _igual(
            "Sandbox: caja que limita lo que el agente toca; sin ella, las reglas son solo promesas.",
            "Sandbox: a box that limits what the agent touches; without it, rules are only promises."),
        _igual(
            "una caja aislada que limita lo que un programa puede ver y tocar.",
            "an isolated box that limits what a program can see and touch."),
        _igual(
            "sin sandbox, las reglas del agente son promesas de la plataforma, no barreras del sistema operativo.",
            "without a sandbox, the agent's rules are the platform's promises, not operating-system barriers."),
        Variantes(
            "considera ejecutar el agente en un entorno aislado, como un contenedor o una máquina virtual.",
            "considere ejecutar el agente en un entorno aislado, como un contenedor o una máquina virtual.",
            "consider running the agent in an isolated environment, such as a container or a virtual machine."),
    ),
    Termino.CONFIGURADO_VS_ANALIZADO: Ficha(
        ("Agente configurado vs analizado", "Configured vs analyzed agent"),
        _igual(
            "Configurado: AgentReach vio sus archivos; no sabe si se ejecutó ni qué puede alcanzar.",
            "Configured: AgentReach saw its files; it does not know if it ran or what it can reach."),
        _igual(
            "tres cosas distintas. Configurado: existen archivos de configuración del agente. Analizado: AgentReach revisó qué puede alcanzar. Usado: el agente se ejecutó (esto AgentReach no lo sabe y nunca lo dice).",
            "three different things. Configured: the agent's configuration files exist. Analyzed: AgentReach checked what it can reach. Used: the agent ran (AgentReach does not know this and never says it)."),
        Variantes(
            "ver un agente en la lista no prueba que lo uses; «aún no analizado» significa que falta revisar qué puede alcanzar, no que no pueda alcanzar nada.",
            "ver un agente en la lista no prueba que lo use; «aún no analizado» significa que falta revisar qué puede alcanzar, no que no pueda alcanzar nada.",
            "seeing an agent listed does not prove you use it; «not analyzed yet» means what it can reach is still unchecked, not that it reaches nothing."),
        Variantes(
            "confirma qué agentes usas de verdad; si sale «solo un indicio», compruébalo a mano.",
            "confirme qué agentes usa de verdad; si sale «solo un indicio», compruébelo a mano.",
            "confirm which agents you really use; if it says «only a hint», check by hand."),
    ),
    Termino.AUTOCOMPROBACION: Ficha(
        ("Autocomprobación", "Self-check"),
        _igual(
            "Autocomprobación: AgentReach revisa su propio resultado antes de imprimirlo.",
            "Self-check: AgentReach reviews its own result before printing it."),
        _igual(
            "antes de mostrar el reporte, AgentReach vuelve a verificar cada hallazgo (que el archivo siga existiendo, que el nivel cumpla las reglas, que el lugar señalado se pueda confirmar).",
            "before showing the report, AgentReach re-verifies each finding (the file still exists, the level follows the rules, the pointed place can be confirmed)."),
        Variantes(
            "si uno no pasa, AgentReach lo baja de nivel en lugar de mostrar algo que no puede sostener. El aviso dice cuál hallazgo (tipo y ruta) y a qué nivel pasó. Es prudencia de la herramienta, no un fallo tuyo.",
            "si uno no pasa, AgentReach lo baja de nivel en lugar de mostrar algo que no puede sostener. El aviso dice cuál hallazgo (tipo y ruta) y a qué nivel pasó. Es prudencia de la herramienta, no un fallo suyo.",
            "if one fails, AgentReach lowers it instead of showing something it cannot back up. The notice says which finding (type and path) and which level it moved to. It is the tool being careful, not your fault."),
        Variantes(
            "nada obligatorio; si el archivo cambió mientras corría, vuelve a ejecutar.",
            "nada obligatorio; si el archivo cambió mientras corría, vuelva a ejecutar.",
            "nothing required; if the file changed while it ran, run it again."),
    ),
    Termino.LUGAR_NO_CONFIRMADO: Ficha(
        ("Lugar exacto no confirmado", "Exact place not confirmed"),
        _igual(
            "No se pudo confirmar dónde está: el archivo cambió o ya no coincide.",
            "Could not confirm where it is: the file changed or no longer matches."),
        _igual(
            "cada hallazgo señala un archivo y una línea; antes de imprimir, AgentReach comprueba que lo señalado siga ahí.",
            "each finding points to a file and a line; before printing, AgentReach checks the pointed text is still there."),
        _igual(
            "si no coincide, el hallazgo baja de nivel porque no se puede sostener con el lugar exacto.",
            "if it does not match, the finding is lowered because it cannot be backed with the exact place."),
        Variantes(
            "vuelve a ejecutar; si persiste, revisa ese archivo a mano.",
            "vuelva a ejecutar; si persiste, revise ese archivo a mano.",
            "run it again; if it persists, check that file by hand."),
    ),
    Termino.CODIGO_DE_SALIDA: Ficha(
        ("Código de salida", "Exit code"),
        _igual(
            "Código de salida: número que deja AgentReach al terminar; 1 si hay comprobados.",
            "Exit code: the number AgentReach leaves when it ends; 1 if there are verified findings."),
        _igual(
            "un número que otros programas (por ejemplo, una automatización) leen al terminar AgentReach.",
            "a number other programs (for example, an automation) read when AgentReach ends."),
        _igual(
            "0 = ningún hallazgo comprobado; 1 = hay hallazgos comprobados. Con `--estricto` el criterio es más exigente.",
            "0 = no verified findings; 1 = there are verified findings. With `--estricto` the rule is stricter."),
        Variantes(
            "si lo usas en una automatización, haz que falle con 1.",
            "si lo usa en una automatización, haga que falle con 1.",
            "if you use it in automation, make it fail on 1."),
    ),
    Termino.CAMINO_DE_ALCANCE: Ficha(
        ("Camino de alcance", "Reach route"),
        _igual(
            "Camino de alcance: cómo un agente llegaría de su carpeta a un efecto posible.",
            "Reach route: how an agent could get from its folder to a possible effect."),
        _igual(
            "cada hallazgo se muestra como un camino de cuatro pasos: Agente → Dónde → Qué hay → Efecto posible. Por ejemplo: un agente → `config/deploy.env`, línea 3 → un token de la nube → podría dar acceso a una cuenta de despliegue.",
            "each finding is shown as a four-step route: Agent → Where → What is there → Possible effect. For example: an agent → `config/deploy.env`, line 3 → a cloud token → it could give access to a deployment account."),
        _igual(
            "una línea continua significa que AgentReach comprobó ese paso; una línea discontinua, que no lo comprobó: es lo que podría pasar, no algo confirmado.",
            "a solid line means AgentReach checked that step; a dashed line means it did not: it is what could happen, not something confirmed."),
        Variantes(
            "empieza por los caminos con el trazo continuo; en los discontinuos, comprueba a mano el paso que falta.",
            "empiece por los caminos con el trazo continuo; en los discontinuos, compruebe a mano el paso que falta.",
            "start with the routes drawn in solid line; for the dashed ones, check the missing step by hand."),
    ),
}


def linea(termino: Termino, idioma: Idioma, tono: Tono = Tono.CERCANO) -> str:
    """La frase de terminal del término (90 caracteres o menos)."""
    return FICHAS[termino].linea.de(idioma, tono)


def nombre(termino: Termino, idioma: Idioma) -> str:
    return FICHAS[termino].nombre[1 if idioma is Idioma.EN else 0]


def etiquetas(idioma: Idioma, tono: Tono = Tono.CERCANO) -> tuple[str, str, str]:
    """Los tres encabezados de la explicación larga: qué es, qué significa y qué hacer."""
    return ETIQUETAS["en" if idioma is Idioma.EN else ("usted" if tono is Tono.FORMAL else "tu")]


def explicacion(termino: Termino, idioma: Idioma, tono: Tono = Tono.CERCANO) -> tuple[str, str, str]:
    """La explicación larga: (qué es, qué significa, qué hacer), mismo texto de la ficha."""
    f = FICHAS[termino]
    return f.que_es.de(idioma, tono), f.que_significa.de(idioma, tono), f.que_hacer.de(idioma, tono)


def punto_ciego(idioma: Idioma, tono: Tono = Tono.CERCANO) -> str:
    return PUNTO_CIEGO.de(idioma, tono)
