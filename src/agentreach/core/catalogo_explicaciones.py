"""Textos fijos del reporte, en español (tono de «tú») e inglés: títulos cortos, motivos, límites y nombres legibles.

Todo sale de tablas fijas (nunca de un modelo de lenguaje). Las explicaciones largas de cada tipo («qué significa» y «qué
hacer») viven en ``contracts.finding.CATALOGO_EXPLICACIONES``; aquí están el título corto de cada tipo y de cada motivo de
«no se pudo revisar», su «cómo resolverlo», los nombres de proveedor, postura, nivel y «ajeno a la tarea», y los límites
declarados (FR-21). Ningún texto afirma que un agente «obedecerá» o «es vulnerable»: habla de condiciones presentes.
"""

from __future__ import annotations

from enum import Enum

from agentreach.contracts import (
    CATALOGO_EXPLICACIONES,
    Ajeno,
    Idioma,
    MotivoNoRevisado,
    Nivel,
    Postura,
    Proveedor,
    Tipo,
)

__all__ = [
    "AJENO",
    "COMO_RESOLVER",
    "COMO_RESOLVER_FORMAL",
    "EXPLICACIONES_FORMAL",
    "LIMITES",
    "LIMITES_TAMBIEN",
    "NIVEL",
    "POSTURA",
    "PROVEEDOR",
    "TITULO_MOTIVO",
    "TITULO_TIPO",
    "Tono",
    "como_resolver",
    "que_hacer",
    "que_significa",
    "titulo_corto",
]

ES, EN = Idioma.ES, Idioma.EN

TITULO_TIPO: dict[Tipo, dict[Idioma, str]] = {
    Tipo.CREDENCIAL_EN_ARCHIVO: {ES: "Credencial en un archivo", EN: "Credential in a file"},
    Tipo.CLAVE_PRIVADA_SSH: {ES: "Llave privada para entrar a servidores", EN: "Private key to log in to servers"},
    Tipo.CREDENCIALES_DE_NUBE: {ES: "Credenciales de una cuenta en la nube", EN: "Cloud account credentials"},
    Tipo.VARIABLE_DE_ENTORNO: {
        ES: "Variable de entorno con nombre de credencial", EN: "Environment variable named like a credential"},
    Tipo.CONTEXTO_SOSPECHOSO: {
        ES: "Archivo de instrucciones con texto sospechoso", EN: "Instructions file with suspicious text"},
    Tipo.ENLACE_FUERA_DEL_PROYECTO: {ES: "Enlace que sale de la carpeta", EN: "Link that leaves the folder"},
    Tipo.REGLA_PERMISIVA: {ES: "Regla del agente demasiado permisiva", EN: "Agent rule that is too permissive"},
    Tipo.CAPACIDAD_DE_SHELL: {
        ES: "El agente puede ejecutar programas del equipo", EN: "The agent can run programs on the computer"},
    Tipo.SCRIPT_DE_DESPLIEGUE: {
        ES: "Script de despliegue (publica cambios)", EN: "Deployment script (publishes changes)"},
    Tipo.PLATAFORMA_SIN_SANDBOX: {
        ES: "Sin caja de aislamiento (sandbox)", EN: "No isolation box (sandbox)"},
    Tipo.DEFINICION_DE_AGENTE: {ES: "Definición de agente", EN: "Agent definition"},
    Tipo.TEXTO_INVISIBLE: {
        ES: "Texto invisible en un archivo de instrucciones", EN: "Invisible text in an instructions file"},
    Tipo.INSTRUCCIONES_FUERA_DE_PROYECTO: {
        ES: "Archivo de instrucciones fuera de un proyecto", EN: "Instructions file outside a project"},
    Tipo.HOOK_O_MCP_DE_COMANDO: {
        ES: "Programa que arranca solo con la configuración del proyecto",
        EN: "Program that starts by itself from the project settings"},
    Tipo.SALTO_DE_PERMISOS: {
        ES: "Configuración que salta las confirmaciones de permiso", EN: "Setting that skips permission checks"},
    Tipo.TAREA_AL_ABRIR_CARPETA: {
        ES: "Tarea que arranca al abrir la carpeta", EN: "Task that starts when the folder is opened"},
    Tipo.SECRETO_DE_ALTO_PODER: {
        ES: "Secreto de plataforma o de despliegue", EN: "Platform or deployment secret"},
    Tipo.GIT_EJECUTA_PROGRAMAS: {
        ES: "Git configurado para ejecutar programas", EN: "Git set up to run programs"},
    Tipo.GIT_REMOTO_SOSPECHOSO: {
        ES: "Dirección de git con credencial o sospechosa", EN: "Git address with a credential, or suspicious"},
    Tipo.GIT_NO_INTERPRETABLE: {
        ES: "Configuración de git que AgentReach no pudo leer", EN: "Git configuration AgentReach could not read"},
}

TITULO_MOTIVO: dict[MotivoNoRevisado, dict[Idioma, str]] = {
    MotivoNoRevisado.UBICACION_SENSIBLE_SIN_ACTIVAR: {ES: "Ubicación sensible sin activar", EN: "Sensitive location not turned on"},
    MotivoNoRevisado.ARCHIVO_ILEGIBLE: {ES: "No se pudo abrir el archivo", EN: "The file could not be opened"},
    MotivoNoRevisado.ARCHIVO_DEMASIADO_GRANDE: {
        ES: "Archivo demasiado grande (más de 5 MB)", EN: "File too large (over 5 MB)"},
    MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR: {
        ES: "No es un archivo normal (tubería, dispositivo u otro)", EN: "Not a regular file (pipe, device or other)"},
    MotivoNoRevisado.CODIFICACION_NO_UTF8: {
        ES: "Texto en una codificación que no se pudo leer", EN: "Text in an encoding that could not be read"},
    MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA: {ES: "Demasiados niveles de anidación", EN: "Too many nesting levels"},
    MotivoNoRevisado.RUTA_DE_RED: {ES: "Ruta de red", EN: "Network path"},
    MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE: {
        ES: "Configuración que AgentReach no entiende", EN: "Configuration AgentReach does not understand"},
    MotivoNoRevisado.VERSION_NO_RECONOCIDA: {
        ES: "Versión de la herramienta no reconocida", EN: "Tool version not recognized"},
    MotivoNoRevisado.HISTORIAL_GIT_FASE2: {
        ES: "Historial de git (llega en una fase futura)", EN: "Git history (comes in a future phase)"},
    MotivoNoRevisado.FUNCION_NO_MODELADA: {
        ES: "Parte de la configuración que AgentReach no sabe interpretar", EN: "Part of the configuration AgentReach cannot interpret"},
    MotivoNoRevisado.SIN_PERMISO_FUERA_DEL_PROYECTO: {
        ES: "No se leyeron las reglas de fuera del proyecto (no se dio permiso)",
        EN: "The rules outside the project were not read (permission was not given)"},
}

COMO_RESOLVER: dict[MotivoNoRevisado, dict[Idioma, str]] = {
    MotivoNoRevisado.UBICACION_SENSIBLE_SIN_ACTIVAR: {
        ES: ("Si quieres que AgentReach mire solo el nombre, el tamaño y los permisos (nunca el contenido) de estas carpetas, "
             "ejecútalo de nuevo con --incluir-ubicaciones-sensibles."),
        EN: ("If you want AgentReach to look only at the name, size and permissions (never the content) of these folders, "
             "run it again with --incluir-ubicaciones-sensibles.")},
    MotivoNoRevisado.ARCHIVO_ILEGIBLE: {
        ES: "Comprueba que el archivo existe y que tu usuario tiene permiso de lectura; luego ejecútalo de nuevo.",
        EN: "Check that the file exists and that your user has read permission; then run it again."},
    MotivoNoRevisado.ARCHIVO_DEMASIADO_GRANDE: {
        ES: "Por seguridad AgentReach no abre archivos tan grandes. Si puede guardar secretos, revísalo a mano.",
        EN: "For safety AgentReach does not open files this large. If it may hold secrets, review it by hand."},
    MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR: {
        ES: "No requiere acción. Si no debería estar en el proyecto, retíralo.",
        EN: "No action needed. If it should not be in the project, remove it."},
    MotivoNoRevisado.CODIFICACION_NO_UTF8: {
        ES: "Guárdalo como UTF-8 (un formato de texto estándar) y ejecútalo de nuevo.",
        EN: "Save it as UTF-8 (a standard text format) and run it again."},
    MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA: {
        ES: "Simplifica el archivo o revísalo a mano.", EN: "Simplify the file or review it by hand."},
    MotivoNoRevisado.RUTA_DE_RED: {
        ES: "AgentReach no sale a la red. Copia la carpeta al equipo y ejecútalo de nuevo.",
        EN: "AgentReach does not go onto the network. Copy the folder to this computer and run it again."},
    MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE: {
        ES: "Revisa ese archivo a mano.", EN: "Review that file by hand."},
    MotivoNoRevisado.VERSION_NO_RECONOCIDA: {
        ES: "Revisa esa configuración a mano.", EN: "Review that configuration by hand."},
    MotivoNoRevisado.HISTORIAL_GIT_FASE2: {
        ES: "Esta versión no ejecuta git. Si te preocupa el historial, revísalo con una herramienta aparte.",
        EN: "This version does not run git. If the history worries you, review it with a separate tool."},
    MotivoNoRevisado.FUNCION_NO_MODELADA: {
        ES: "Esa configuración cambia qué puede leer el agente y AgentReach aún no lo interpreta: revísala a mano.",
        EN: "That configuration changes what the agent can read and AgentReach does not interpret it yet: review it by hand."},
    MotivoNoRevisado.SIN_PERMISO_FUERA_DEL_PROYECTO: {
        ES: ("Sin esas reglas AgentReach no puede decidir bien los niveles, y los que dependen de ellas quedan en «potencial». "
             "Para que las lea (solo las reglas, nunca los valores), ejecútalo de nuevo y responde S a la segunda pregunta."),
        EN: ("Without those rules AgentReach cannot decide the levels properly, and the ones that depend on them stay at \"potential\". "
             "For it to read them (only the rules, never the values), run it again and answer Y to the second question.")},
}

PROVEEDOR: dict[Proveedor, dict[Idioma, str]] = {
    Proveedor.IA: {ES: "servicio de inteligencia artificial", EN: "AI service"},
    Proveedor.PAGOS: {ES: "servicio de pagos", EN: "payments service"},
    Proveedor.CODIGO: {ES: "servicio de alojamiento de código", EN: "code hosting service"},
    Proveedor.DESPLIEGUE: {ES: "plataforma de despliegue", EN: "deployment platform"},
    Proveedor.BASE_DE_DATOS: {ES: "base de datos", EN: "database"},
    Proveedor.NUBE: {ES: "cuenta en la nube", EN: "cloud account"},
    Proveedor.SSH: {ES: "acceso remoto a servidores", EN: "remote server access"},
    Proveedor.FIRMA: {ES: "firma de aplicación", EN: "application signing"},
    Proveedor.DESCONOCIDO: {ES: "proveedor desconocido", EN: "unknown provider"},
    Proveedor.NO_APLICA: {ES: "", EN: ""},
}

POSTURA: dict[Postura, dict[Idioma, str]] = {
    Postura.ALLOW: {ES: "lo permite", EN: "allows it"},
    Postura.ASK: {ES: "pide confirmación", EN: "asks first"},
    Postura.DENY: {ES: "lo bloquea (solo por regla)", EN: "blocks it (rule only)"},
    Postura.SIN_REGLA: {ES: "sin regla", EN: "no rule"},
    Postura.NO_DETERMINADA: {ES: "no determinadas", EN: "not determined"},
}

AJENO: dict[Ajeno, dict[Idioma, str]] = {
    Ajeno.SI: {ES: "sí", EN: "yes"},
    Ajeno.NO: {ES: "no", EN: "no"},
    Ajeno.NO_DETERMINADO: {ES: "no determinado", EN: "not determined"},
}

NIVEL: dict[Nivel, dict[Idioma, str]] = {
    Nivel.COMPROBADO: {ES: "COMPROBADO", EN: "VERIFIED"},
    Nivel.POTENCIAL: {ES: "POTENCIAL", EN: "POTENTIAL"},
    Nivel.HIPOTESIS: {ES: "HIPÓTESIS", EN: "HYPOTHESIS"},
}

# FR-21: lo que AgentReach no puede ver. Ver una condición en un archivo no es ver el ataque.
LIMITES: dict[Idioma, tuple[str, ...]] = {
    ES: (
        "La versión del agente. Varios ataques dependen de que el agente sea de una versión con el defecto; AgentReach no da por sabida esa versión.",
        "Si el modelo obedecería. Un archivo con una orden escondida es una condición; que el modelo la siga depende del modelo.",
        "Instrucciones maliciosas en lenguaje natural sin trucos de formato. Solo se marcan por un patrón simple y como máximo como hipótesis.",
        "Las descripciones de las herramientas MCP. Lo que dicen solo aparece al ejecutar el servidor, y AgentReach no ejecuta nada.",
        "Paquetes inventados por el modelo. Saber si un paquete existe exige consultar internet, y AgentReach no sale a la red.",
        "El poder real de un token. AgentReach ve que existe y de qué tipo, no qué puede hacer con él en el servicio.",
    ),
    EN: (
        "The agent version. Several attacks depend on the agent being a version with the flaw; AgentReach does not assume that version.",
        "Whether the model would obey. A file with a hidden order is a condition; whether the model follows it depends on the model.",
        "Malicious instructions in plain language with no formatting tricks. They are only flagged by a simple pattern and at most as a hypothesis.",
        "MCP tool descriptions. What they say only shows up when the server runs, and AgentReach runs nothing.",
        "Packages invented by the model. Knowing whether a package exists requires checking the internet, and AgentReach does not go onto the network.",
        "The real power of a token. AgentReach sees that it exists and of what type, not what it can do with it on the service.",
    ),
}
LIMITES_TAMBIEN: dict[Idioma, str] = {
    ES: ("Tampoco se revisan en esta versión: el historial de commits de git, los cambios de una configuración después de "
         "aprobarla y los procesos y puertos en ejecución."),
    EN: ("Also not checked in this version: the git commit history, changes to a configuration after it was approved, and "
         "running processes and ports."),
}

_TH17_AJENO: dict[Ajeno, dict[Idioma, str]] = {
    Ajeno.SI: {ES: " Está en un archivo sin relación con la tarea.", EN: " It is in a file unrelated to the task."},
    Ajeno.NO: {ES: "", EN: ""},
    Ajeno.NO_DETERMINADO: {
        ES: " No se puede saber si el archivo tiene relación con la tarea.",
        EN: " It cannot be known whether the file is related to the task."},
}


class Tono(Enum):
    """Tono del español: «cercano» (de tú, por defecto) o «formal» (de usted). En inglés solo cambia el registro: el texto es el mismo."""

    CERCANO = "cercano"
    FORMAL = "formal"


# Lo que cambia en español formal. Lo que no está aquí no usa pronombres y se comparte con el tono cercano.
EXPLICACIONES_FORMAL: dict[Tipo, tuple[str | None, str]] = {
    Tipo.CREDENCIAL_EN_ARCHIVO: (None, "Saque la credencial del proyecto o guárdela en un gestor de secretos (un programa que guarda claves cifradas) y rótela (rotar es cambiarla por una nueva y desactivar la vieja) si estuvo expuesta."),
    Tipo.CLAVE_PRIVADA_SSH: (None, "Use claves con frase de paso (una contraseña extra que protege la clave), mantenga al agente lejos de esa carpeta y revise sus permisos."),
    Tipo.CREDENCIALES_DE_NUBE: (None, "Use credenciales temporales con solo los permisos que la tarea necesita y mantenga el archivo fuera de donde el agente puede llegar."),
    Tipo.VARIABLE_DE_ENTORNO: (None, "Quite la variable del entorno del agente o limpie el entorno antes de iniciarlo."),
    Tipo.CONTEXTO_SOSPECHOSO: (None, "Revise ese archivo a mano y elimine las instrucciones que no escribió usted."),
    Tipo.ENLACE_FUERA_DEL_PROYECTO: (None, "Confirme que el destino es intencional o elimine el enlace."),
    Tipo.REGLA_PERMISIVA: (None, "Cambie esas reglas a «pide confirmación» (el agente pregunta antes) o «lo bloquea» (el agente no puede) donde no sean necesarias."),
    Tipo.CAPACIDAD_DE_SHELL: (
        "El agente puede ejecutar comandos en su equipo (la línea de comandos, llamada shell): con eso llega a lo que cualquier programa suyo pueda tocar.",
        "Limite los comandos permitidos o exija confirmación antes de ejecutar comandos."),
    Tipo.SCRIPT_DE_DESPLIEGUE: (None, "Compruebe qué hace el script y proteja su ejecución para que el agente pregunte antes o no pueda lanzarlo."),
    Tipo.PLATAFORMA_SIN_SANDBOX: (None, "Considere ejecutar el agente en un entorno aislado, como un contenedor o una máquina virtual."),
    Tipo.DEFINICION_DE_AGENTE: (None, "Revise las herramientas permitidas y deje solo las necesarias."),
    Tipo.TEXTO_INVISIBLE: (
        "Un archivo de instrucciones contiene caracteres que no se dibujan en pantalla (caracteres Unicode invisibles; Unicode es el estándar que define las letras y símbolos de todos los idiomas) pero que un agente sí lee: podría haber una orden que usted no ve.",
        "Abra el archivo en un editor que muestre los caracteres ocultos y elimínelos."),
    Tipo.INSTRUCCIONES_FUERA_DE_PROYECTO: (None, "Muévalo a un proyecto que usted controle o elimínelo."),
    Tipo.HOOK_O_MCP_DE_COMANDO: (None, "Revise ese comando y desactive el que no reconozca antes de abrir el proyecto."),
    Tipo.SALTO_DE_PERMISOS: (None, "Quite esa opción y deje que el agente pida confirmación."),
    Tipo.TAREA_AL_ABRIR_CARPETA: (None, "Elimine la tarea o desactive las tareas automáticas del editor."),
    Tipo.SECRETO_DE_ALTO_PODER: (None, "Retírelo del proyecto, rótelo (rotar es cambiarlo por uno nuevo y desactivar el viejo) y limite lo que permite en la plataforma."),
    Tipo.GIT_EJECUTA_PROGRAMAS: (None, "Revise esas claves y hooks y elimine los que no reconozca."),
    Tipo.GIT_REMOTO_SOSPECHOSO: (None, "Quite la credencial de la dirección, rótela (rotar es cambiarla por una nueva y desactivar la vieja) y use un ayudante de credenciales."),
    Tipo.GIT_NO_INTERPRETABLE: (None, "Revise el archivo de configuración de git a mano."),
}

COMO_RESOLVER_FORMAL: dict[MotivoNoRevisado, str] = {
    MotivoNoRevisado.UBICACION_SENSIBLE_SIN_ACTIVAR: "Si desea que AgentReach mire solo el nombre, el tamaño y los permisos (nunca el contenido) de estas carpetas, ejecútelo de nuevo con --incluir-ubicaciones-sensibles.",
    MotivoNoRevisado.ARCHIVO_ILEGIBLE: "Compruebe que el archivo existe y que su usuario tiene permiso de lectura; luego ejecútelo de nuevo.",
    MotivoNoRevisado.ARCHIVO_DEMASIADO_GRANDE: "Por seguridad AgentReach no abre archivos tan grandes. Si puede guardar secretos, revíselo a mano.",
    MotivoNoRevisado.NO_ES_ARCHIVO_REGULAR: "No requiere acción. Si no debería estar en el proyecto, retírelo.",
    MotivoNoRevisado.CODIFICACION_NO_UTF8: "Guárdelo como UTF-8 (un formato de texto estándar) y ejecútelo de nuevo.",
    MotivoNoRevisado.PROFUNDIDAD_EXCEDIDA: "Simplifique el archivo o revíselo a mano.",
    MotivoNoRevisado.RUTA_DE_RED: "AgentReach no sale a la red. Copie la carpeta al equipo y ejecútelo de nuevo.",
    MotivoNoRevisado.CONFIGURACION_NO_INTERPRETABLE: "Revise ese archivo a mano.",
    MotivoNoRevisado.VERSION_NO_RECONOCIDA: "Revise esa configuración a mano.",
    MotivoNoRevisado.HISTORIAL_GIT_FASE2: "Esta versión no ejecuta git. Si le preocupa el historial, revíselo con una herramienta aparte.",
    MotivoNoRevisado.FUNCION_NO_MODELADA: "Esa configuración cambia qué puede leer el agente y AgentReach aún no lo interpreta: revísela a mano.",
    MotivoNoRevisado.SIN_PERMISO_FUERA_DEL_PROYECTO: (
        "Sin esas reglas AgentReach no puede decidir bien los niveles, y los que dependen de ellas quedan en «potencial». "
        "Para que las lea (solo las reglas, nunca los valores), ejecútelo de nuevo y responda S a la segunda pregunta."),
}


def como_resolver(motivo: MotivoNoRevisado, idioma: Idioma, tono: Tono = Tono.CERCANO) -> str:
    if idioma is Idioma.ES and tono is Tono.FORMAL:
        return COMO_RESOLVER_FORMAL[motivo]
    return COMO_RESOLVER[motivo][idioma]


def titulo_corto(tipo: Tipo, idioma: Idioma) -> str:
    return TITULO_TIPO[tipo][idioma]


def que_significa(tipo: Tipo, ajeno: Ajeno, idioma: Idioma, tono: Tono = Tono.CERCANO) -> str:
    """El «qué significa» del catálogo; el de TH-17 cambia según «ajeno a la tarea» (no afirma lo que no sabe)."""
    texto = CATALOGO_EXPLICACIONES[tipo][idioma][0]
    if idioma is Idioma.ES and tono is Tono.FORMAL and EXPLICACIONES_FORMAL[tipo][0]:
        texto = EXPLICACIONES_FORMAL[tipo][0] or texto
    if tipo is Tipo.SECRETO_DE_ALTO_PODER:
        texto += _TH17_AJENO[ajeno][idioma]
    return texto


def que_hacer(tipo: Tipo, idioma: Idioma, tono: Tono = Tono.CERCANO) -> str:
    if idioma is Idioma.ES and tono is Tono.FORMAL:
        return EXPLICACIONES_FORMAL[tipo][1]
    return CATALOGO_EXPLICACIONES[tipo][idioma][1]
