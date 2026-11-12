# Política de seguridad

AgentReach es una herramienta de seguridad. Tomamos en serio los reportes de vulnerabilidades.

## Reportar una vulnerabilidad

No abras un issue público para reportar una vulnerabilidad. Usa el mecanismo privado de GitHub: **Security → Report a vulnerability** en el repositorio.

Incluye:
- Descripción del problema y su impacto.
- Pasos para reproducirlo, con un repositorio de prueba si es posible.
- Versión o commit afectado.

Responderemos en un plazo razonable y coordinaremos la publicación del fix.

## Alcance

Son especialmente relevantes los reportes que:
- Hagan que AgentReach **modifique** un repositorio analizado (debe ser solo lectura).
- Hagan que un reporte **imprima valores de secretos**.
- Envíen información del entorno del usuario a servidores externos sin que se haya pedido.
- Permitan que un repositorio analizado engañe al análisis (por ejemplo, mediante enlaces simbólicos o instrucciones maliciosas en archivos de contexto).
