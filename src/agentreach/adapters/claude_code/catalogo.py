"""Los tres casos de configuración DEL PROYECTO de Claude Code que ejecutan algo, con su versión corregida.

Textos fijos del catálogo (FR-11): AgentReach no ejecuta Claude Code, así que no sabe qué versión hay
instalada; solo dice desde qué versión está corregido. Fuentes: avisos oficiales de Anthropic, CVE-2025-59536
y CVE-2026-21852 (un CVE es el número público de una vulnerabilidad).
"""

from __future__ import annotations

from dataclasses import dataclass

from agentreach.contracts import Idioma


@dataclass(frozen=True, slots=True)
class CasoConfig:
    clave: str
    version_corregida: str
    referencia: str  # el número público de la vulnerabilidad o el aviso
    que_significa: dict[Idioma, str]
    que_hacer: dict[Idioma, str]


CASOS_CONFIG_PROYECTO: dict[str, CasoConfig] = {
    "hooks": CasoConfig(
        clave="hooks",
        version_corregida="1.0.87",
        referencia="aviso de seguridad de Anthropic, sin identificador público",
        que_significa={
            Idioma.ES: ("La configuración del proyecto define hooks (comandos que Claude Code lanza solo ante "
                        "un evento). Corren DESPUÉS de que la persona acepta el aviso de confianza, pero ese aviso no "
                        "explicaba que aceptar permite ejecutar archivos de la carpeta."),
            Idioma.EN: ("The project configuration defines hooks (commands Claude Code launches by itself on an "
                        "event). They run AFTER the person accepts the trust prompt, but that prompt did not explain "
                        "that accepting lets files in the folder run."),
        },
        que_hacer={
            Idioma.ES: ("Revise cada hook antes de aceptar la confianza en la carpeta y use Claude Code 1.0.87 o "
                        "posterior, que corrige el aviso."),
            Idioma.EN: ("Review every hook before trusting the folder and use Claude Code 1.0.87 or later, which "
                        "fixes the prompt."),
        },
    ),
    "mcp": CasoConfig(
        clave="mcp",
        version_corregida="1.0.111",
        referencia="CVE-2025-59536",
        que_significa={
            Idioma.ES: ("La configuración del proyecto activa todos los servidores MCP (la conexión del agente con "
                        "herramientas externas) con enableAllProjectMcpServers. En versiones anteriores a la corregida "
                        "corrían antes del aviso de confianza."),
            Idioma.EN: ("The project configuration enables every MCP server (the agent's link to external tools) "
                        "with enableAllProjectMcpServers. In versions before the fixed one they ran before the trust "
                        "prompt."),
        },
        que_hacer={
            Idioma.ES: ("Desactive enableAllProjectMcpServers, revise los servidores del proyecto y use Claude Code "
                        "1.0.111 o posterior (CVE-2025-59536)."),
            Idioma.EN: ("Turn off enableAllProjectMcpServers, review the project's servers and use Claude Code "
                        "1.0.111 or later (CVE-2025-59536)."),
        },
    ),
    "base_url": CasoConfig(
        clave="base_url",
        version_corregida="2.0.65",
        referencia="CVE-2026-21852",
        que_significa={
            Idioma.ES: ("La configuración del proyecto fija ANTHROPIC_BASE_URL: puede desviar las llamadas del agente "
                        "(y su clave) a otro servidor. En versiones anteriores a la corregida corría antes del aviso "
                        "de confianza."),
            Idioma.EN: ("The project configuration sets ANTHROPIC_BASE_URL: it can redirect the agent's calls (and "
                        "its key) to another server. In versions before the fixed one it took effect before the trust "
                        "prompt."),
        },
        que_hacer={
            Idioma.ES: ("Quite ANTHROPIC_BASE_URL de la configuración del proyecto y use Claude Code 2.0.65 o "
                        "posterior (CVE-2026-21852)."),
            Idioma.EN: ("Remove ANTHROPIC_BASE_URL from the project configuration and use Claude Code 2.0.65 or "
                        "later (CVE-2026-21852)."),
        },
    ),
}
