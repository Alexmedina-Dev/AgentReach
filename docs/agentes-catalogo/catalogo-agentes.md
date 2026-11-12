# Catálogo de agentes de programación: firmas verificables

Consulta realizada el 2026-11-10. Solo lectura de documentación oficial. AgentReach no ejecuta nada: solo mira si existen archivos y carpetas. Este catálogo dice **qué agente está CONFIGURADO** (hay rastros de configuración), no **cuál ejecutó algo** (eso es de la fase 2, con registros de actividad).

Datos para el generador: `catalogo-agentes.json` (mismo contenido, campos estables). Cada ruta lleva `verificada: true|false`. Una ruta con `false` es **no verificada**: sale de conocimiento previo o de otra fuente, no de la documentación oficial de ese agente, y por la regla FR-7 del PRD nunca puede dar confianza alta por sí sola.

## Palabras que se usan

- **Firma fuerte**: un archivo o carpeta que, por su nombre exacto, solo crea ese agente. Basta para decir "configurado".
- **Firma débil**: un rastro que muchos agentes comparten o que puede existir sin el agente. Solo es indicio.
- **Falso positivo**: algo que parece prueba y no lo es.
- **MCP** (Model Context Protocol): forma estándar de conectar herramientas externas a un agente.
- **Subagente**: agente auxiliar definido en un archivo, con su propio prompt y herramientas.
- **Habilidad (skill)**: carpeta con un `SKILL.md` que enseña al agente una tarea.
- **Marco (framework)**: capa que se instala sobre un agente (gentle-ai, BMAD). No es un agente por sí mismo.
- `~` es la carpeta personal del usuario. En Windows es `%USERPROFILE%`.

## Cómo se decide

Niveles de confianza (los mismos del PRD): **alta**, **potencial**, **hipótesis** y **no se pudo determinar**.

1. **Confianza alta**: al menos una firma fuerte con `verificada: true` y la fuente oficial anotada. Dos firmas fuertes distintas (por ejemplo proyecto y usuario) refuerzan, pero una basta.
2. **Potencial**: una firma fuerte con `verificada: false` (sin fuente verificada, tope por FR-7), o una firma débil que coincide con otra pista propia del agente (por ejemplo `.cursor/` más una variable de entorno propia).
3. **Hipótesis**: solo firmas débiles, todas compartidas con otros agentes, pero con una sola candidata razonable.
4. **No se pudo determinar**: solo hay firmas débiles compartidas y varias candidatas, o el rastro no está en el catálogo. Es una respuesta correcta y se muestra así, con la lista de candidatos; nunca se rellena con una suposición.
5. **Regla de oro: nunca se afirma un agente por una firma débil.** Una firma débil sube como máximo a hipótesis y siempre se muestra con la palabra "indicio".
6. **Nombres compartidos no cuentan solos**: `AGENTS.md`, `.mcp.json`, `.vscode/`, `.github/`, `.env`, `~/.gemini/` y `~/.agents/` jamás identifican a un agente. `AGENTS.md` lo leen Codex, Cursor, Copilot, Windsurf, Kiro, Cline, Roo, Amp, Goose, Junie, Antigravity, opencode y Claude Code (en lugar de `CLAUDE.md`).
7. **Existencia no es uso**: carpetas de datos o historial (`~/.claude/projects/`, `.aider.chat.history.md`) prueban que el agente se ejecutó alguna vez, no que hoy esté configurado. Solo se reporta su existencia, nunca su contenido. Tampoco se lee `secrets.yaml` de Goose ni `~/.claude.json`.
8. **Varios agentes**: se reportan todos, cada uno con su propia evidencia y confianza, sin elegir uno "principal". Si un archivo (por ejemplo `GEMINI.md`) puede pertenecer a dos agentes, se muestra bajo el que tenga otra firma fuerte; si ninguno la tiene, ambos quedan como hipótesis.
9. **Marcos (gentle-ai, BMAD)**: se reportan como capa "instalada sobre" el agente cuya carpeta tocan. Una habilidad sola no basta: se necesita la huella propia del marco (`_bmad/`, `gentle-ai-NN-*.md`, o `jd-judge-a/b` más `jd-fix-agent`).
10. **Agentes personalizados**: un `.md` en `.claude/agents/` o `~/.claude/agents/` cuenta como subagente de Claude Code solo con `name` y `description` en el encabezado (si no, Claude Code lo salta). Es un hallazgo dentro de Claude Code, no un agente nuevo. Igual con `.opencode/agents/` y opencode. En `alex-dev.agent.md` el nombre termina en `.md`, pero que la doble extensión se cargue es **no verificado**: se reporta como potencial.
11. **Ámbitos separados**: lo gestionado (sistema), lo de usuario y lo de proyecto se reportan aparte; "configurado en el equipo" no es "configurado en este proyecto".
12. **Cambios de plataforma**: las rutas cambian (Windsurf pasó a documentarse en docs.devin.ai; Antigravity tiene `.agent/` antiguo y `.agents/` nuevo). Un rastro que no coincide con ninguna firma conocida se informa como "no reconocido", no se descarta en silencio.

## Resumen

| id | Agente | Fabricante | Verificado | Firma fuerte | Firma débil |
|---|---|---|---|---|---|
| claude-code | Claude Code | Anthropic | sí | Cualquiera de: CLAUDE.md, .claude/settings.json, .claude/settings.local.json, .claude/agents/*.md, .claude/skills/*/SKILL.md, .claude/commands/*.md, .claude/rules/*.md (proyecto) o ~/.claude/settings.json, ~/.claude/agents/ (usuario). | AGENTS.md; .mcp.json; ~/.claude.json sin nada mas. |
| opencode | opencode | SST / Anomaly (codigo abierto) | sí | opencode.json, opencode.jsonc, .opencode/opencode.json(c) o .opencode/agents/ en el proyecto; ~/.config/opencode/ en el usuario. | AGENTS.md; carpeta .opencode/ vacia. |
| gemini-cli | Gemini CLI | Google | sí | .gemini/settings.json (proyecto) o ~/.gemini/settings.json (usuario); GEMINI_CLI_HOME definida. | GEMINI.md solo; ~/.gemini/ solo; GEMINI_API_KEY (la usa cualquier cliente de Gemini). |
| codex-cli | OpenAI Codex CLI | OpenAI | sí | .codex/config.toml (proyecto) o ~/.codex/config.toml (usuario). | AGENTS.md; carpeta .codex/ sin config.toml. |
| copilot-vscode | GitHub Copilot (VS Code) | GitHub / Microsoft | sí | .github/copilot-instructions.md, .github/instructions/*.instructions.md o .github/agents/*.agent.md. | .vscode/ ; AGENTS.md ; CLAUDE.md ; GEMINI.md ; .github/ sola. |
| copilot-cli | GitHub Copilot CLI | GitHub / Microsoft | sí | ~/.copilot/ (o COPILOT_HOME) con copilot-instructions.md, instructions/ o config.json. | .github/copilot-instructions.md (no distingue de VS Code); AGENTS.md. |
| cursor | Cursor | Anysphere | sí | .cursor/rules/*.mdc en el proyecto. | AGENTS.md; ~/.cursor/ solo. |
| windsurf | Windsurf | Cognition (antes Codeium) | sí | .windsurf/rules/*.md o .windsurfrules. | AGENTS.md; ~/.codeium/ solo. |
| kiro | Kiro | Amazon Web Services | sí | .kiro/steering/ en el proyecto o ~/.kiro/steering/. | AGENTS.md. |
| cline | Cline | Cline Bot (codigo abierto) | sí | .clinerules/ o .cline/rules/ en el proyecto. | AGENTS.md; ~/.agents/AGENTS.md (otros agentes pueden usar ~/.agents). |
| roo-code | Roo Code | Roo Code Inc. (codigo abierto) | sí | .roo/rules/, .roorules o .roo/rules-<modo>/. | AGENTS.md; AGENT.md. |
| continue | Continue | Continue Dev | sí | ~/.continue/config.yaml (usuario, confirmado). | ~/.continue/ vacia; .continue/ de proyecto sin confirmar. |
| aider | Aider | Paul Gauthier (codigo abierto) | sí | .aider.conf.yml (proyecto o home) o variables AIDER_*. | .env con AIDER_ (indicio); CONVENTIONS.md. |
| amp | Amp | Sourcegraph | **no** | No hay firma fuerte confirmada. | AGENTS.md. |
| junie | JetBrains Junie | JetBrains | **no** | No hay firma fuerte confirmada. | .idea/ (solo prueba el IDE). |
| qwen-code | Qwen Code | Alibaba Cloud / Qwen (codigo abierto) | sí | QWEN.md o .qwen/settings.json. | Variables QWEN_* sueltas. |
| antigravity | Google Antigravity | Google | sí | .agents/rules/ o ~/.gemini/config/rules/ (carpeta propia 'config'). | AGENTS.md; GEMINI.md; ~/.gemini/ solo. |
| goose | Goose | Block (ahora Linux Foundation / AAIF; codigo abierto) | sí | config.yaml en la ruta de usuario; variables GOOSE_*. | AGENTS.md; .goosehints (sin confirmar). |
| gentle-ai | gentle-ai (marco que se instala sobre agentes) | Gentleman Programming | sí | Archivos gentle-ai-NN-*.md en ~/.gemini/config/rules/ ; ~/.gemini/gentle-ai/ ; agentes jd-judge-a/b + jd-fix-agent juntos. | Una sola habilidad con nombre parecido; linea '# gentle-ai installer' en el archivo de arranque del shell (solo prueba que se instalo el binario). |
| bmad | BMAD (BMad Method) | BMad Code | sí | Carpeta _bmad/ (la crea 'bmad setup') mas habilidades bmad-* en la carpeta de skills del agente. | Solo habilidades bmad-*; solo _bmad-output/. |
| claude-code-agente-personalizado | Agentes personalizados de Claude Code (subagentes) | Anthropic (definidos por el usuario) | sí | Archivo .md con encabezado YAML que tenga 'name' y 'description' dentro de .claude/agents/ o ~/.claude/agents/. | Archivo en .claude/agents/ sin 'name' o sin 'description' (Claude Code lo salta). |
| opencode-agente-personalizado | Agentes personalizados de opencode | SST / Anomaly (definidos por el usuario) | sí | Archivo .md en .opencode/agents/ o ~/.config/opencode/agents/, o clave agent dentro de opencode.json. | Carpeta .opencode/agents/ vacia. |

## Detalle por agente

### Claude Code (`claude-code`)

- Fabricante: Anthropic
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `CLAUDE.md` | instrucciones | fuerte | sí |
| `.claude/CLAUDE.md` | instrucciones | fuerte | sí |
| `CLAUDE.local.md` | instrucciones | fuerte | sí |
| `.claude/settings.json` | configuracion | fuerte | sí |
| `.claude/settings.local.json` | configuracion | fuerte | sí |
| `.claude/rules/*.md` | reglas | fuerte | sí |
| `.mcp.json` | mcp | debil | sí |
| `.claude/agents/*.md` | subagente | fuerte | sí |
| `.claude/skills/<nombre>/SKILL.md` | habilidad | fuerte | sí |
| `.claude/commands/*.md` | habilidad | fuerte | sí |
| `.claude/output-styles/*.md` | configuracion | debil | sí |
| `.claude/workflows/*.js` | configuracion | debil | sí |
| `.claude/agent-memory/<nombre>/` | datos | debil | sí |
| `.worktreeinclude` | configuracion | debil | sí |
| `AGENTS.md` | instrucciones | debil | sí |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\.claude\` | carpeta de configuracion | sí |
| Windows | `%USERPROFILE%\.claude\settings.json` | configuracion | sí |
| Windows | `%USERPROFILE%\.claude\CLAUDE.md` | instrucciones | sí |
| Windows | `%USERPROFILE%\.claude\agents\*.md` | subagente | sí |
| Windows | `%USERPROFILE%\.claude\skills\<nombre>\SKILL.md` | habilidad | sí |
| Windows | `%USERPROFILE%\.claude\commands\*.md` | habilidad | sí |
| Windows | `%USERPROFILE%\.claude\rules\*.md` | reglas | sí |
| Windows | `%USERPROFILE%\.claude.json` | estado y MCP personales | sí |
| Windows | `%USERPROFILE%\.claude\plugins\` | plugins | sí |
| Windows | `(ruta de sistema de managed-settings.json: no verificada en esta consulta)` | gestionada | no |
| Linux | `~/.claude/` | carpeta de configuracion | sí |
| Linux | `~/.claude/settings.json` | configuracion | sí |
| Linux | `~/.claude/CLAUDE.md` | instrucciones | sí |
| Linux | `~/.claude/agents/*.md` | subagente | sí |
| Linux | `~/.claude/skills/<nombre>/SKILL.md` | habilidad | sí |
| Linux | `~/.claude/commands/*.md` | habilidad | sí |
| Linux | `~/.claude/rules/*.md` | reglas | sí |
| Linux | `~/.claude.json` | estado y MCP personales | sí |
| Linux | `~/.claude/plugins/` | plugins | sí |
| Linux | `(no verificado)` | gestionada | no |
| macOS | `~/.claude/` | carpeta de configuracion | sí |
| macOS | `~/.claude/settings.json` | configuracion | sí |
| macOS | `~/.claude/CLAUDE.md` | instrucciones | sí |
| macOS | `~/.claude/agents/*.md` | subagente | sí |
| macOS | `~/.claude/skills/<nombre>/SKILL.md` | habilidad | sí |
| macOS | `~/.claude/commands/*.md` | habilidad | sí |
| macOS | `~/.claude/rules/*.md` | reglas | sí |
| macOS | `~/.claude.json` | estado y MCP personales | sí |
| macOS | `~/.claude/plugins/` | plugins | sí |
| macOS | `(no verificado)` | gestionada | no |

**Variables de entorno (solo nombres):** `CLAUDE_CONFIG_DIR`, `CLAUDE_CODE_TMPDIR`, `CLAUDE_CODE_SKIP_PROMPT_HISTORY`, `ANTHROPIC_MODEL`, `ANTHROPIC_DEFAULT_MODEL`

**Datos o historial (solo existencia, nunca contenido):** `~/.claude/projects/`, `~/.claude/history.jsonl`, `~/.claude/file-history/`, `~/.claude/plans/`

**Falsos positivos:**
- AGENTS.md solo: lo usan muchos agentes.
- .mcp.json solo: otros agentes (Cursor, Copilot, Kiro...) tambien lo leen.
- ~/.claude.json puede quedar tras desinstalar.
- Una carpeta .claude/ vacia no prueba configuracion.

**No verificado:** Rutas de managed-settings.json por sistema operativo (la pagina remite a otra); semantica de '.agent.md' como subagente (el doc solo dice .md).

**Notas:** Datos (solo existencia): ~/.claude/projects/, ~/.claude/history.jsonl, ~/.claude/file-history/. En Windows ~ es %USERPROFILE%. Si CLAUDE_CONFIG_DIR esta definida, todo ~/.claude vive alli.

**Fuentes (consultadas 2026-11-10):**
- https://code.claude.com/docs/en/claude-directory.md
- https://code.claude.com/docs/en/settings.md
- https://code.claude.com/docs/en/sub-agents.md

### opencode (`opencode`)

- Fabricante: SST / Anomaly (codigo abierto)
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `opencode.json` | configuracion | fuerte | sí |
| `opencode.jsonc` | configuracion | fuerte | sí |
| `.opencode/opencode.json(c)` | configuracion | fuerte | sí |
| `.opencode/agents/*.md` | subagente | fuerte | sí |
| `.opencode/skills/<nombre>/SKILL.md` | habilidad | fuerte | sí |
| `.opencode/commands/*.md` | habilidad | fuerte | no |
| `.opencode/plugins/` | configuracion | fuerte | no |
| `AGENTS.md` | instrucciones | debil | sí |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\.config\opencode\opencode.json (no documentado por la fuente; visto en la maquina de Alex y en el PRD FR-15)` | configuracion | sí |
| Windows | `%USERPROFILE%\.config\opencode\agents\*.md` | subagente | sí |
| Windows | `%USERPROFILE%\.config\opencode\skills\` | habilidad | sí |
| Windows | `%ProgramData%\opencode\` | gestionada | sí |
| Linux | `~/.config/opencode/opencode.json` | configuracion | sí |
| Linux | `~/.config/opencode/agents/*.md` | subagente | sí |
| Linux | `~/.config/opencode/skills/` | habilidad | sí |
| Linux | `/etc/opencode/` | gestionada | sí |
| macOS | `~/.config/opencode/opencode.json` | configuracion | sí |
| macOS | `~/.config/opencode/agents/*.md` | subagente | sí |
| macOS | `~/.config/opencode/skills/` | habilidad | sí |
| macOS | `/Library/Application Support/opencode/` | gestionada | sí |

**Variables de entorno (solo nombres):** `OPENCODE_MODEL`

**Falsos positivos:**
- AGENTS.md solo.
- Un opencode.json de otra herramienta (nombre generico).

**No verificado:** Ruta global en Windows (la doc no la da; el PRD usa %USERPROFILE%\.config\opencode); ubicacion de datos e historial; commands/ y plugins/ a nivel proyecto; variable de la carpeta de configuracion.

**Notas:** Adaptador existente cubre 1.x y 2.x. Los agentes viven en 'agents' (plural).

**Fuentes (consultadas 2026-11-10):**
- https://opencode.ai/docs/config/
- https://opencode.ai/docs/agents/

### Gemini CLI (`gemini-cli`)

- Fabricante: Google
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `GEMINI.md` | instrucciones | fuerte | sí |
| `.gemini/settings.json` | configuracion | fuerte | sí |
| `.gemini/` | carpeta | fuerte | sí |
| `.gemini/.env` | configuracion | debil | sí |
| `.gemini/skills/<nombre>/SKILL.md` | habilidad | fuerte | no |
| `.gemini/extensions/` | configuracion | fuerte | no |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\.gemini\settings.json` | configuracion | sí |
| Windows | `%USERPROFILE%\.gemini\GEMINI.md` | instrucciones | sí |
| Windows | `%USERPROFILE%\.gemini\` | carpeta | sí |
| Windows | `C:\ProgramData\gemini-cli\settings.json` | gestionada | sí |
| Linux | `~/.gemini/settings.json` | configuracion | sí |
| Linux | `~/.gemini/GEMINI.md` | instrucciones | sí |
| Linux | `~/.gemini/` | carpeta | sí |
| Linux | `/etc/gemini-cli/settings.json` | gestionada | sí |
| macOS | `~/.gemini/settings.json` | configuracion | sí |
| macOS | `~/.gemini/GEMINI.md` | instrucciones | sí |
| macOS | `~/.gemini/` | carpeta | sí |
| macOS | `/Library/Application Support/GeminiCli/settings.json` | gestionada | sí |

**Variables de entorno (solo nombres):** `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`, `GEMINI_MODEL`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `GEMINI_CLI_HOME`, `GEMINI_CLI_SYSTEM_SETTINGS_PATH`, `GEMINI_CLI_SYSTEM_DEFAULTS_PATH`, `GEMINI_CLI_TRUSTED_FOLDERS_PATH`, `GEMINI_CLI_TRUST_WORKSPACE`, `GEMINI_SANDBOX`, `GEMINI_SYSTEM_MD`

**Falsos positivos:**
- ~/.gemini/ lo comparten Antigravity y gentle-ai: la carpeta sola no prueba Gemini CLI.
- GEMINI.md lo leen tambien Copilot, Antigravity y otros.
- GOOGLE_API_KEY y GOOGLE_CLOUD_PROJECT son genericas de Google.

**No verificado:** Ruta de historial/sesiones; carpeta de skills y extensiones a nivel proyecto.

**Fuentes (consultadas 2026-11-10):**
- https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/reference/configuration.md

### OpenAI Codex CLI (`codex-cli`)

- Fabricante: OpenAI
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `.codex/config.toml` | configuracion | fuerte | sí |
| `AGENTS.md` | instrucciones | debil | sí |
| `AGENTS.override.md` | instrucciones | debil | no |
| `.codex/` | carpeta | debil | sí |
| `.agents/skills/<nombre>/SKILL.md` | habilidad | debil | no |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\.codex\config.toml` | configuracion | sí |
| Windows | `%USERPROFILE%\.codex\` | carpeta | sí |
| Windows | `%USERPROFILE%\.codex\AGENTS.md` | instrucciones | no |
| Windows | `%USERPROFILE%\.codex\prompts\` | habilidad | no |
| Windows | `(no documentado)` | gestionada | sí |
| Linux | `~/.codex/config.toml` | configuracion | sí |
| Linux | `~/.codex/` | carpeta | sí |
| Linux | `~/.codex/AGENTS.md` | instrucciones | no |
| Linux | `~/.codex/prompts/` | habilidad | no |
| Linux | `/etc/codex/config.toml` | gestionada | sí |
| macOS | `~/.codex/config.toml` | configuracion | sí |
| macOS | `~/.codex/` | carpeta | sí |
| macOS | `~/.codex/AGENTS.md` | instrucciones | no |
| macOS | `~/.codex/prompts/` | habilidad | no |
| macOS | `/etc/codex/config.toml (la doc solo dice 'Unix'; macOS no confirmado)` | gestionada | sí |

**Variables de entorno (solo nombres):** `CODEX_HOME`

**Falsos positivos:**
- AGENTS.md solo.
- CODEX_HOME: nombre no confirmado en esta consulta.

**No verificado:** CODEX_HOME, AGENTS.override.md, skills, prompts, ruta en Windows, historial (todo 'no cubierto' por la pagina consultada).

**Notas:** El config de proyecto solo se carga si el proyecto es de confianza.

**Fuentes (consultadas 2026-11-10):**
- https://learn.chatgpt.com/docs/config-file/config-basic

### GitHub Copilot (VS Code) (`copilot-vscode`)

- Fabricante: GitHub / Microsoft
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `.github/copilot-instructions.md` | instrucciones | fuerte | sí |
| `.github/instructions/*.instructions.md` | instrucciones | fuerte | sí |
| `.github/agents/*.agent.md` | subagente | fuerte | sí |
| `.github/prompts/*.prompt.md` | habilidad | fuerte | no |
| `.vscode/mcp.json` | mcp | debil | no |
| `.vscode/` | carpeta | debil | sí |
| `AGENTS.md` | instrucciones | debil | sí |
| `CLAUDE.md` | instrucciones | debil | sí |
| `GEMINI.md` | instrucciones | debil | sí |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%APPDATA%\Code\User\ (no verificado)` | subagente | no |
| Linux | `~/.config/Code/User/ (no verificado)` | subagente | no |
| macOS | `~/Library/Application Support/Code/User/ (no verificado)` | subagente | no |

**Falsos positivos:**
- .vscode/ existe sin Copilot (es de VS Code).
- AGENTS.md, CLAUDE.md y GEMINI.md los lee Copilot pero pertenecen a otros agentes.
- .github/ existe en casi todo repositorio de GitHub.
- copilot-instructions.md tambien lo usa Copilot de GitHub.com y la CLI: no distingue donde.

**No verificado:** Ruta exacta del perfil de usuario de VS Code para agentes/prompts; .github/prompts; .vscode/mcp.json.

**Notas:** Las rutas .github/ son compartidas con la CLI y Copilot en la nube: solo se sabe 'Copilot configurado', no en que superficie.

**Fuentes (consultadas 2026-11-10):**
- https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions
- https://code.visualstudio.com/docs/copilot/customization/custom-agents

### GitHub Copilot CLI (`copilot-cli`)

- Fabricante: GitHub / Microsoft
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `.github/copilot-instructions.md` | instrucciones | fuerte | sí |
| `.github/instructions/**/*.instructions.md` | instrucciones | fuerte | sí |
| `AGENTS.md` | instrucciones | debil | sí |
| `CLAUDE.md` | instrucciones | debil | sí |
| `.claude/CLAUDE.md` | instrucciones | debil | sí |
| `GEMINI.md` | instrucciones | debil | sí |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\.copilot\copilot-instructions.md` | instrucciones | sí |
| Windows | `%USERPROFILE%\.copilot\instructions\**\*.instructions.md` | instrucciones | sí |
| Windows | `%USERPROFILE%\.copilot\mcp-config.json` | mcp | no |
| Windows | `%USERPROFILE%\.copilot\skills\` | habilidad | no |
| Windows | `%USERPROFILE%\.copilot\config.json` | configuracion | no |
| Linux | `~/.copilot/copilot-instructions.md` | instrucciones | sí |
| Linux | `~/.copilot/instructions/**/*.instructions.md` | instrucciones | sí |
| Linux | `~/.copilot/mcp-config.json` | mcp | no |
| Linux | `~/.copilot/skills/` | habilidad | no |
| Linux | `~/.copilot/config.json` | configuracion | no |
| macOS | `~/.copilot/copilot-instructions.md` | instrucciones | sí |
| macOS | `~/.copilot/instructions/**/*.instructions.md` | instrucciones | sí |
| macOS | `~/.copilot/mcp-config.json` | mcp | no |
| macOS | `~/.copilot/skills/` | habilidad | no |
| macOS | `~/.copilot/config.json` | configuracion | no |

**Variables de entorno (solo nombres):** `COPILOT_HOME`, `COPILOT_CUSTOM_INSTRUCTIONS_DIRS`

**Falsos positivos:**
- Mismos archivos .github que Copilot en VS Code.
- Lee CLAUDE.md y GEMINI.md sin ser Claude ni Gemini.

**No verificado:** config.json, mcp-config.json (aparece en la doc de gentle-ai, no en la de GitHub), .github/agents para la CLI, historial.

**Fuentes (consultadas 2026-11-10):**
- https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions

### Cursor (`cursor`)

- Fabricante: Anysphere
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `.cursor/rules/*.mdc` | reglas | fuerte | sí |
| `.cursor/rules/` | carpeta | fuerte | sí |
| `.cursor/mcp.json` | mcp | fuerte | no |
| `.cursor/agents/` | subagente | fuerte | no |
| `.cursorrules` | reglas | fuerte | no |
| `.cursorignore` | reglas | debil | no |
| `AGENTS.md` | instrucciones | debil | sí |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\.cursor\mcp.json` | mcp | no |
| Windows | `%USERPROFILE%\.cursor\agents\` | subagente | sí |
| Linux | `~/.cursor/mcp.json` | mcp | no |
| Linux | `~/.cursor/agents/` | subagente | sí |
| macOS | `~/.cursor/mcp.json` | mcp | no |
| macOS | `~/.cursor/agents/` | subagente | sí |

**Falsos positivos:**
- AGENTS.md solo.
- Archivos .md dentro de .cursor/rules se ignoran (solo .mdc).
- ~/.cursor/agents/ tambien lo escribe gentle-ai: prueba que gentle-ai se instalo, no que el usuario use Cursor.

**No verificado:** .cursor/mcp.json y ~/.cursor/mcp.json, .cursorrules, .cursorignore (conocidos por uso comun, no en la pagina consultada); ruta de datos de la aplicacion por sistema operativo; reglas de usuario (se guardan en la aplicacion, sin archivo documentado).

**Fuentes (consultadas 2026-11-10):**
- https://cursor.com/docs/context/rules
- https://raw.githubusercontent.com/Gentleman-Programming/gentle-ai/main/docs/agents.md

### Windsurf (`windsurf`)

- Fabricante: Cognition (antes Codeium)
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `.windsurf/rules/*.md` | reglas | fuerte | sí |
| `.windsurfrules` | reglas | fuerte | sí |
| `.windsurf/` | carpeta | fuerte | sí |
| `AGENTS.md` | instrucciones | debil | sí |
| `AGENTS.local.md` | instrucciones | debil | sí |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\.windsurf\global_rules.md` | reglas | sí |
| Windows | `%USERPROFILE%\.devin\global_rules.md` | reglas | sí |
| Windows | `%USERPROFILE%\.codeium\windsurf\` | datos y MCP | no |
| Linux | `~/.windsurf/global_rules.md` | reglas | sí |
| Linux | `~/.devin/global_rules.md` | reglas | sí |
| Linux | `~/.codeium/windsurf/` | datos y MCP | no |
| macOS | `~/.windsurf/global_rules.md` | reglas | sí |
| macOS | `~/.devin/global_rules.md` | reglas | sí |
| macOS | `~/.codeium/windsurf/` | datos y MCP | no |

**Falsos positivos:**
- AGENTS.md solo.
- '.devin/' puede ser de Devin y no de Windsurf.

**No verificado:** ~/.codeium/windsurf/ (memorias, mcp_config.json) y .windsurf/workflows: no aparecen en la pagina consultada.

**Notas:** La doc se movio a docs.devin.ai; la ruta global exacta '~/.windsurf/global_rules.md' esta escrita como '.windsurf/global_rules.md' en la fuente (relativa a la carpeta del usuario, a confirmar).

**Fuentes (consultadas 2026-11-10):**
- https://docs.devin.ai/desktop/cascade/memories

### Kiro (`kiro`)

- Fabricante: Amazon Web Services
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `.kiro/steering/*.md` | instrucciones | fuerte | sí |
| `.kiro/specs/` | configuracion | fuerte | no |
| `.kiro/settings/mcp.json` | mcp | fuerte | no |
| `.kiro/hooks/` | configuracion | fuerte | no |
| `.kiro/` | carpeta | fuerte | sí |
| `AGENTS.md` | instrucciones | debil | sí |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\.kiro\steering\` | instrucciones | sí |
| Windows | `%USERPROFILE%\.kiro\settings\mcp.json` | mcp | no |
| Windows | `%USERPROFILE%\.kiro\` | carpeta | no |
| Linux | `~/.kiro/steering/` | instrucciones | sí |
| Linux | `~/.kiro/settings/mcp.json` | mcp | no |
| Linux | `~/.kiro/` | carpeta | no |
| macOS | `~/.kiro/steering/` | instrucciones | sí |
| macOS | `~/.kiro/settings/mcp.json` | mcp | no |
| macOS | `~/.kiro/` | carpeta | no |

**Falsos positivos:**
- AGENTS.md solo (Kiro tambien lo lee en ~/.kiro/steering/).

**No verificado:** .kiro/specs, .kiro/settings/mcp.json, .kiro/hooks (la pagina solo los enlaza).

**Fuentes (consultadas 2026-11-10):**
- https://kiro.dev/docs/steering/

### Cline (`cline`)

- Fabricante: Cline Bot (codigo abierto)
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `.clinerules/` | reglas | fuerte | sí |
| `.cline/rules/` | reglas | fuerte | sí |
| `AGENTS.md` | instrucciones | debil | sí |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\Documents\Cline\Rules` | reglas | sí |
| Windows | `%USERPROFILE%\.cline\rules` | reglas | sí |
| Windows | `%USERPROFILE%\Cline\Rules` | reglas | sí |
| Windows | `%USERPROFILE%\.agents\AGENTS.md` | instrucciones | sí |
| Windows | `(no verificado)` | mcp | no |
| Linux | `~/Documents/Cline/Rules` | reglas | sí |
| Linux | `~/.cline/rules` | reglas | sí |
| Linux | `~/Cline/Rules` | reglas | sí |
| Linux | `~/.agents/AGENTS.md` | instrucciones | sí |
| Linux | `(no verificado)` | mcp | no |
| macOS | `~/Documents/Cline/Rules` | reglas | sí |
| macOS | `~/.cline/rules` | reglas | sí |
| macOS | `~/Cline/Rules` | reglas | sí |
| macOS | `~/.agents/AGENTS.md` | instrucciones | sí |
| macOS | `(no verificado)` | mcp | no |

**Falsos positivos:**
- AGENTS.md solo.
- ~/Documents/Cline puede existir sin uso activo.

**No verificado:** cline_mcp_settings.json, workflows, hooks (la pagina remite a 'Configuration Directory Layout').

**Fuentes (consultadas 2026-11-10):**
- https://docs.cline.bot/customization/cline-rules

### Roo Code (`roo-code`)

- Fabricante: Roo Code Inc. (codigo abierto)
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `.roo/rules/` | reglas | fuerte | sí |
| `.roo/rules-<modo>/` | reglas | fuerte | sí |
| `.roorules` | reglas | fuerte | sí |
| `.roorules-<modo>` | reglas | fuerte | sí |
| `.roomodes` | subagente | fuerte | no |
| `.roo/mcp.json` | mcp | fuerte | no |
| `AGENTS.md` | instrucciones | debil | sí |
| `AGENT.md` | instrucciones | debil | sí |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\.roo\rules\` | reglas | sí |
| Windows | `%USERPROFILE%\.roo\rules-<modo>\` | reglas | sí |
| Windows | `%USERPROFILE%\.roo\` | carpeta | no |
| Linux | `~/.roo/rules/` | reglas | sí |
| Linux | `~/.roo/rules-<modo>/` | reglas | sí |
| Linux | `~/.roo/` | carpeta | no |
| macOS | `~/.roo/rules/` | reglas | sí |
| macOS | `~/.roo/rules-<modo>/` | reglas | sí |
| macOS | `~/.roo/` | carpeta | no |

**Falsos positivos:**
- AGENTS.md solo.
- .roo/ puede quedar de Roo y de bifurcaciones (Kilo Code usa nombres parecidos: no verificado).

**No verificado:** .roomodes, .roo/mcp.json y custom_modes.yaml (la pagina no los menciona).

**Fuentes (consultadas 2026-11-10):**
- https://roocodeinc.github.io/Roo-Code/features/custom-instructions

### Continue (`continue`)

- Fabricante: Continue Dev
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `.continue/` | carpeta | fuerte | no |
| `.continue/rules/` | reglas | fuerte | no |
| `.continue/agents/` | subagente | fuerte | no |
| `.continue/mcpServers/` | mcp | fuerte | no |
| `config.yaml en .continue/` | configuracion | fuerte | no |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\.continue\config.yaml` | configuracion | sí |
| Windows | `%USERPROFILE%\.continue\config.json` | configuracion (obsoleto) | sí |
| Linux | `~/.continue/config.yaml` | configuracion | sí |
| Linux | `~/.continue/config.json` | configuracion (obsoleto) | sí |
| macOS | `~/.continue/config.yaml` | configuracion | sí |
| macOS | `~/.continue/config.json` | configuracion (obsoleto) | sí |

**Variables de entorno (solo nombres):** `CONTINUE_GLOBAL_DIR`

**Falsos positivos:**
- 'config.yaml' sin la carpeta .continue/ es un nombre generico.
- CONTINUE_GLOBAL_DIR: no confirmado.

**No verificado:** Todo el nivel proyecto (.continue/rules, agents, mcpServers: la pagina dice 'no mencionado'), variable de entorno.

**Notas:** Verificado solo el nivel usuario.

**Fuentes (consultadas 2026-11-10):**
- https://docs.continue.dev/customize/deep-dives/configuration

### Aider (`aider`)

- Fabricante: Paul Gauthier (codigo abierto)
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `.aider.conf.yml` | configuracion | fuerte | sí |
| `.env` | configuracion | debil | sí |
| `.aiderignore` | reglas | fuerte | no |
| `.aider.chat.history.md` | datos | fuerte | no |
| `.aider.input.history` | datos | fuerte | no |
| `CONVENTIONS.md` | instrucciones | debil | no |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\.aider.conf.yml` | configuracion | sí |
| Windows | `%USERPROFILE%\.env` | configuracion | no |
| Linux | `~/.aider.conf.yml` | configuracion | sí |
| Linux | `~/.env` | configuracion | no |
| macOS | `~/.aider.conf.yml` | configuracion | sí |
| macOS | `~/.env` | configuracion | no |

**Variables de entorno (solo nombres):** `prefijo AIDER_ (por ejemplo AIDER_DARK_MODE)`

**Datos o historial (solo existencia, nunca contenido):** `historial (.aider.chat.history.md)`

**Falsos positivos:**
- .env lo usan todos los proyectos.
- CONVENTIONS.md es un nombre generico (Aider lo carga solo si se le pide).

**No verificado:** .aiderignore, archivos de historial, CONVENTIONS.md: la pagina no los menciona (conocidos por uso comun).

**Notas:** Aider escribe sus historiales en la raiz del repositorio: su existencia es indicio de uso pasado, no solo de configuracion.

**Fuentes (consultadas 2026-11-10):**
- https://aider.chat/docs/config.html

### Amp (`amp`)

- Fabricante: Sourcegraph
- Verificado en documentación oficial: no

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `AGENTS.md` | instrucciones | debil | no |
| `.agents/skills/` | habilidad | debil | no |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `(no verificado)` | configuracion | no |
| Windows | `(no verificado)` | instrucciones | no |
| Linux | `~/.config/amp/settings.json` | configuracion | no |
| Linux | `~/.config/AGENTS.md` | instrucciones | no |
| macOS | `~/.config/amp/settings.json` | configuracion | no |
| macOS | `~/.config/AGENTS.md` | instrucciones | no |

**Variables de entorno (solo nombres):** `(no verificado; prefijo AMP_ probable)`

**Falsos positivos:**
- AGENTS.md solo.

**No verificado:** Todo: la manual consultada solo enlaza paginas (agents-md, cli/settings, skills) que no se pudieron leer.

**Notas:** Sin fuente verificada: tope 'potencial' (FR-7).

**Fuentes (consultadas 2026-11-10):**
- https://ampcode.com/manual

### JetBrains Junie (`junie`)

- Fabricante: JetBrains
- Verificado en documentación oficial: no

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `.junie/guidelines.md` | instrucciones | fuerte | no |
| `.junie/` | carpeta | fuerte | no |
| `AGENTS.md` | instrucciones | debil | no |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\.junie\` | carpeta | no |
| Linux | `~/.junie/` | carpeta | no |
| macOS | `~/.junie/` | carpeta | no |

**Variables de entorno (solo nombres):** `(no verificado)`

**Falsos positivos:**
- AGENTS.md solo.
- '.idea/' existe en cualquier proyecto JetBrains sin Junie.

**No verificado:** Todo: la pagina oficial se obtuvo vacia; .junie/guidelines.md es conocimiento previo.

**Notas:** Sin fuente verificada: tope 'potencial'.

**Fuentes (consultadas 2026-11-10):**
- https://junie.jetbrains.com/docs/

### Qwen Code (`qwen-code`)

- Fabricante: Alibaba Cloud / Qwen (codigo abierto)
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `QWEN.md` | instrucciones | fuerte | sí |
| `.qwen/settings.json` | configuracion | fuerte | sí |
| `.qwen/` | carpeta | fuerte | sí |
| `.qwen/skills/<nombre>/SKILL.md` | habilidad | fuerte | sí |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\.qwen\settings.json` | configuracion | sí |
| Windows | `%USERPROFILE%\.qwen\` | carpeta | sí |
| Windows | `C:\ProgramData\qwen-code\settings.json` | gestionada | sí |
| Linux | `~/.qwen/settings.json` | configuracion | sí |
| Linux | `~/.qwen/` | carpeta | sí |
| Linux | `/etc/qwen-code/settings.json` | gestionada | sí |
| macOS | `~/.qwen/settings.json` | configuracion | sí |
| macOS | `~/.qwen/` | carpeta | sí |
| macOS | `/Library/Application Support/QwenCode/settings.json` | gestionada | sí |

**Variables de entorno (solo nombres):** `QWEN_CODE_SYSTEM_SETTINGS_PATH`, `QWEN_CODE_SYSTEM_DEFAULTS_PATH`, `QWEN_SANDBOX_IMAGE`, `QWEN_CODE_MAX_OUTPUT_TOKENS`

**Falsos positivos:**
- Es una bifurcacion de Gemini CLI: la estructura es parecida pero los nombres son .qwen y QWEN.md; no confundir con .gemini.

**No verificado:** Ruta de historial; segunda mitad de la pagina (no leida).

**Fuentes (consultadas 2026-11-10):**
- https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/

### Google Antigravity (`antigravity`)

- Fabricante: Google
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `.agents/rules/*.md` | reglas | fuerte | sí |
| `.agent/rules/*.md` | reglas | fuerte | sí |
| `.agents/AGENTS.md` | instrucciones | fuerte | sí |
| `.agents/GEMINI.md` | instrucciones | fuerte | sí |
| `.agents/rules.json` | configuracion | fuerte | sí |
| `AGENTS.md` | instrucciones | debil | sí |
| `GEMINI.md` | instrucciones | debil | sí |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\.gemini\config\rules\*.md` | reglas | sí |
| Windows | `%USERPROFILE%\.gemini\config\AGENTS.md` | instrucciones | sí |
| Windows | `%USERPROFILE%\.gemini\config\agents\` | subagente | no |
| Windows | `%USERPROFILE%\.gemini\AGENTS.md` | instrucciones | sí |
| Windows | `%USERPROFILE%\.gemini\GEMINI.md` | instrucciones | sí |
| Linux | `~/.gemini/config/rules/*.md` | reglas | sí |
| Linux | `~/.gemini/config/AGENTS.md` | instrucciones | sí |
| Linux | `~/.gemini/config/agents/` | subagente | no |
| Linux | `~/.gemini/AGENTS.md` | instrucciones | sí |
| Linux | `~/.gemini/GEMINI.md` | instrucciones | sí |
| macOS | `~/.gemini/config/rules/*.md` | reglas | sí |
| macOS | `~/.gemini/config/AGENTS.md` | instrucciones | sí |
| macOS | `~/.gemini/config/agents/` | subagente | no |
| macOS | `~/.gemini/AGENTS.md` | instrucciones | sí |
| macOS | `~/.gemini/GEMINI.md` | instrucciones | sí |

**Falsos positivos:**
- ~/.gemini/GEMINI.md es COMPARTIDO con Gemini CLI: no identifica a Antigravity.
- AGENTS.md y GEMINI.md en la raiz los leen varios agentes.

**No verificado:** Flujos de trabajo (workflows) y habilidades (la pagina remite a otras); ruta de datos de la aplicacion por sistema operativo.

**Notas:** Ojo: ~/.gemini/config/ lo usa tambien gentle-ai para Antigravity.

**Fuentes (consultadas 2026-11-10):**
- https://antigravity.google/docs/rules
- https://raw.githubusercontent.com/Gentleman-Programming/gentle-ai/main/docs/agents.md

### Goose (`goose`)

- Fabricante: Block (ahora Linux Foundation / AAIF; codigo abierto)
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `.goosehints` | instrucciones | fuerte | no |
| `AGENTS.md` | instrucciones | debil | no |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%APPDATA%\Block\goose\config\config.yaml` | configuracion | sí |
| Windows | `%APPDATA%\Block\goose\config\permission.yaml` | reglas | sí |
| Windows | `%APPDATA%\Block\goose\config\secrets.yaml` | secretos (no leer) | sí |
| Linux | `~/.config/goose/config.yaml` | configuracion | sí |
| Linux | `~/.config/goose/permission.yaml` | reglas | sí |
| Linux | `~/.config/goose/secrets.yaml` | secretos (no leer) | sí |
| macOS | `~/.config/goose/config.yaml` | configuracion | sí |
| macOS | `~/.config/goose/permission.yaml` | reglas | sí |
| macOS | `~/.config/goose/secrets.yaml` | secretos (no leer) | sí |

**Variables de entorno (solo nombres):** `GOOSE_PROVIDER`, `GOOSE_MODEL`, `GOOSE_MODE`, `GOOSE_MAX_TURNS`, `GOOSE_TOOL_DEFERRAL`, `GOOSE_TEMPERATURE`, `GOOSE_MAX_TOKENS`, `GOOSE_CACHE_TTL`, `GOOSE_TOOLSHIM`, `GOOSE_CLI_THEME`, `GOOSE_ALLOWLIST`, `GOOSE_RECIPE_GITHUB_REPO`, `GOOSE_TELEMETRY_ENABLED`

**Falsos positivos:**
- AGENTS.md solo.

**No verificado:** .goosehints y AGENTS.md a nivel proyecto (la pagina dice 'no cubierto'); carpeta de sesiones; secrets.yaml existe: solo contar su existencia, nunca leerlo.

**Fuentes (consultadas 2026-11-10):**
- https://goose-docs.ai/docs/guides/config-files

### gentle-ai (marco que se instala sobre agentes) (`gentle-ai`)

- Fabricante: Gentleman Programming
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `.gentle-ai/` | carpeta | fuerte | no |
| `skill-registry (.atl/skill-registry.md)` | habilidad | debil | no |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\.gemini\gentle-ai\guidance.md` | instrucciones | sí |
| Windows | `%USERPROFILE%\.gemini\gentle-ai\.gentle-ai-modules.json` | estado | sí |
| Windows | `%USERPROFILE%\.gemini\config\gentle-ai\guidance.md` | instrucciones | sí |
| Windows | `%USERPROFILE%\.gemini\config\rules\gentle-ai-NN-<seccion>.md` | reglas | sí |
| Windows | `%USERPROFILE%\.cursor\agents\jd-judge-a (y jd-judge-b, jd-fix-agent)` | subagente | sí |
| Windows | `%USERPROFILE%\.gemini\config\agents\jd-judge-a (y jd-judge-b, jd-fix-agent)` | subagente | sí |
| Windows | `%USERPROFILE%\.claude\skills\<nombre>\SKILL.md (habilidades de gentle-ai; ver nota)` | habilidad | no |
| Windows | `%USERPROFILE%\.copilot\copilot-instructions.md` | instrucciones | sí |
| Linux | `~/.gemini/gentle-ai/guidance.md` | instrucciones | sí |
| Linux | `~/.gemini/gentle-ai/.gentle-ai-modules.json` | estado | sí |
| Linux | `~/.gemini/config/gentle-ai/guidance.md` | instrucciones | sí |
| Linux | `~/.gemini/config/rules/gentle-ai-NN-<seccion>.md` | reglas | sí |
| Linux | `~/.cursor/agents/jd-judge-a (y jd-judge-b, jd-fix-agent)` | subagente | sí |
| Linux | `~/.gemini/config/agents/jd-judge-a (y jd-judge-b, jd-fix-agent)` | subagente | sí |
| Linux | `~/.claude/skills/<nombre>/SKILL.md (habilidades de gentle-ai; ver nota)` | habilidad | no |
| Linux | `~/.copilot/copilot-instructions.md` | instrucciones | sí |
| macOS | `~/.gemini/gentle-ai/guidance.md` | instrucciones | sí |
| macOS | `~/.gemini/gentle-ai/.gentle-ai-modules.json` | estado | sí |
| macOS | `~/.gemini/config/gentle-ai/guidance.md` | instrucciones | sí |
| macOS | `~/.gemini/config/rules/gentle-ai-NN-<seccion>.md` | reglas | sí |
| macOS | `~/.cursor/agents/jd-judge-a (y jd-judge-b, jd-fix-agent)` | subagente | sí |
| macOS | `~/.gemini/config/agents/jd-judge-a (y jd-judge-b, jd-fix-agent)` | subagente | sí |
| macOS | `~/.claude/skills/<nombre>/SKILL.md (habilidades de gentle-ai; ver nota)` | habilidad | no |
| macOS | `~/.copilot/copilot-instructions.md` | instrucciones | sí |

**Falsos positivos:**
- Los nombres jd-judge-a, jd-judge-b, jd-fix-agent indican gentle-ai solo si aparecen juntos.
- Una habilidad llamada 'judgment-day' o 'branch-pr' puede copiarse a mano.
- Es una capa sobre otro agente: nunca cuenta como agente por si mismo, sino como 'marco sobre X'.

**No verificado:** Rutas para Claude Code, opencode, Codex, Windsurf, VS Code Copilot, Kiro, Qwen y Trae (la doc dice 'no paths stated'); archivo de estado general; copias de seguridad.

**Notas:** Marco, no agente. Se reporta como capa 'instalada sobre' los agentes cuyas carpetas toca.

**Fuentes (consultadas 2026-11-10):**
- https://github.com/Gentleman-Programming/gentle-ai
- https://raw.githubusercontent.com/Gentleman-Programming/gentle-ai/main/docs/agents.md

### BMAD (BMad Method) (`bmad`)

- Fabricante: BMad Code
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `_bmad/` | carpeta | fuerte | sí |
| `_bmad/custom/` | configuracion | fuerte | sí |
| `_bmad-output/` | datos | debil | sí |
| `.claude/skills/bmad-*/SKILL.md` | habilidad | fuerte | no |
| `.agents/skills/bmad-*` | habilidad | debil | no |

**Nivel usuario**

Sin rutas de usuario propias (el marco vive en las carpetas de otros agentes).

**Falsos positivos:**
- Una habilidad 'bmad-*' sin la carpeta _bmad/ puede ser una copia suelta.
- _bmad-output/ puede quedar tras desinstalar.

**No verificado:** Carpeta de skills por cada agente (la guia dice que el instalador pregunta y no las nombra); en este repositorio se observan .claude/skills/bmad-* (observacion local, no fuente oficial).

**Notas:** Marco, no agente. La carpeta de skills donde aparezcan indica sobre que agente esta instalado.

**Fuentes (consultadas 2026-11-10):**
- https://docs.bmad-method.org/start/install-bmad/

### Agentes personalizados de Claude Code (subagentes) (`claude-code-agente-personalizado`)

- Fabricante: Anthropic (definidos por el usuario)
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `.claude/agents/*.md` | subagente | fuerte | sí |
| `.claude/agents/**/*.md` | subagente | fuerte | sí |
| `.claude/agent-memory/<nombre>/` | datos | debil | sí |
| `.claude/output-styles/*.md` | configuracion | debil | sí |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\.claude\agents\*.md` | subagente | sí |
| Windows | `%USERPROFILE%\.claude\agents\alex-dev.agent.md` | subagente (ejemplo de agente personal) | no |
| Windows | `%USERPROFILE%\.claude\agent-memory\<nombre>\` | datos | sí |
| Linux | `~/.claude/agents/*.md` | subagente | sí |
| Linux | `~/.claude/agents/alex-dev.agent.md` | subagente (ejemplo de agente personal) | no |
| Linux | `~/.claude/agent-memory/<nombre>/` | datos | sí |
| macOS | `~/.claude/agents/*.md` | subagente | sí |
| macOS | `~/.claude/agents/alex-dev.agent.md` | subagente (ejemplo de agente personal) | no |
| macOS | `~/.claude/agent-memory/<nombre>/` | datos | sí |

**Variables de entorno (solo nombres):** `CLAUDE_CONFIG_DIR`

**Falsos positivos:**
- La extension '.agent.md' es la convencion de Copilot en VS Code; en Claude Code el documento solo habla de '.md': un archivo '*.agent.md' bajo ~/.claude/agents/ se lee como subagente SI tiene 'name' y 'description' en el encabezado (la doc dice que sin ellos se salta).

**No verificado:** Que '*.agent.md' sea cargado igual que '*.md' (la doc no lo afirma ni lo niega); ruta de agentes gestionados (managed settings directory).

**Notas:** Prioridad si hay nombres repetidos: gestionada, --agents, proyecto, usuario, plugin. La identidad es el campo 'name', no el nombre del archivo.

**Fuentes (consultadas 2026-11-10):**
- https://code.claude.com/docs/en/sub-agents.md
- https://code.claude.com/docs/en/claude-directory.md

### Agentes personalizados de opencode (`opencode-agente-personalizado`)

- Fabricante: SST / Anomaly (definidos por el usuario)
- Verificado en documentación oficial: sí

**Nivel proyecto**

| Ruta | Tipo | Fuerza | Verificada |
|---|---|---|---|
| `.opencode/agents/<nombre>.md` | subagente | fuerte | sí |
| `.opencode/agents/<equipo>/<nombre>.md` | subagente | fuerte | sí |
| `opencode.json (clave agent)` | subagente | fuerte | sí |

**Nivel usuario**

| Sistema | Ruta | Tipo | Verificada |
|---|---|---|---|
| Windows | `%USERPROFILE%\.config\opencode\agents\<nombre>.md (ruta Windows no documentada; ver opencode)` | subagente | sí |
| Linux | `~/.config/opencode/agents/<nombre>.md` | subagente | sí |
| macOS | `~/.config/opencode/agents/<nombre>.md` | subagente | sí |

**Falsos positivos:**
- Carpeta 'agents' en plural; 'agent' en singular es la clave de opencode.json, no la carpeta.
- Una subcarpeta crea el id 'equipo/nombre'.

**No verificado:** Ruta global de agentes en Windows.

**Fuentes (consultadas 2026-11-10):**
- https://opencode.ai/docs/agents/
- https://opencode.ai/docs/config/
