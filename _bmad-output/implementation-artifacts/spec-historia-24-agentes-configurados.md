# Historia 24: reconocer los agentes configurados con el catálogo de firmas

**Estado: terminada (2026-11-10).** Usa `docs/agentes-catalogo/catalogo-agentes.json` (22 entradas; copia empaquetada en `src/agentreach/data/`, una prueba comprueba que son idénticas).

## Reglas (de `catalogo-agentes.md`)
- Solo EXISTENCIA de archivos y carpetas y NOMBRES de variables de entorno; nunca el contenido ni el valor. Dice **«configurado»**, nunca «ejecutado».
- **Alta:** firma fuerte con fuente verificada. **Potencial:** fuerte sin fuente verificada (tope FR-7). **Hipótesis («solo un indicio»):** solo firmas débiles de un único candidato (p. ej. una carpeta del usuario sola).
- Nombres compartidos (`AGENTS.md`, `.mcp.json`, `.vscode/`, `.github/`, `.env`, `.gemini/`, `.agents/`, `.idea/`, `GEMINI.md`...) jamás identifican a un agente; un rastro débil que es firma fuerte de otro agente (`CLAUDE.md` en la lista de Copilot) tampoco. `AGENTS.md` solo, sin un agente claro: **«No determinado»** con la lista de candidatos.
- Historial, estado y secretos (`tipo` datos/estado/secretos) no cuentan ni se mencionan.
- Marcos (BMAD, gentle-ai): «marco instalado sobre» el agente cuya carpeta tocan; una habilidad sola no basta (necesita su huella propia).
- Varios agentes: se reportan todos, cada uno con su evidencia, sin elegir uno «principal». Ámbitos separados: proyecto, usuario, entorno.

## Dónde sale
Terminal («AGENTES CONFIGURADOS», con `--detalle` lista la evidencia), HTML (`configured_agents` con `kind`, `confidence`, `analyzed`, `on`, más `undetermined_traces`) y su selector: solo los agentes con adaptador (Claude Code, opencode) entran al selector; los demás (y los marcos) se listan como configurados con «AgentReach todavía no analiza qué puede alcanzar este agente».

## Pruebas
`tests/test_historia_24.py` (51, incluida una en el navegador).

## Diferido
- Cabecera YAML (`name` y `description`) de los agentes personalizados (los dos ids `*-agente-personalizado` se omiten: sus rastros ya cuentan para Claude Code y opencode).
- Rastros «no reconocidos» (carpetas de agentes que no están en el catálogo).
- Variables de entorno: solo `GEMINI_CLI_HOME`, `AIDER_*`, `GOOSE_*` y `QWEN_*` (el catálogo las describe en prosa).
- Rutas gestionadas/del sistema y `CLAUDE_CONFIG_DIR`.
