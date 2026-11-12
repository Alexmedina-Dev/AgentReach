# Puntos de control y auditoría por plataforma: Claude Code y opencode

- Fecha: 2026-11-06
- Alcance: insumo para el adaptador de AgentReach (fases 1 a 3) y para el PRD. Solo lectura, sin ejecutar nada en el sistema de Alex.
- Entorno objetivo: Windows 11 nativo (terminal y Visual Studio).
- Método: documentación oficial (code.claude.com, opencode.ai/docs) y repositorio oficial de opencode (github.com/anomalyco/opencode). Terceros marcados como `[TERCERO]`.
- Limitación de método: las páginas se leyeron con WebFetch, que resume con un modelo pequeño. Las citas entre comillas son lo que devolvió esa herramienta; antes de convertirlas en requisitos conviene releer la página original. Las páginas largas de Claude Code se leyeron solo hasta los primeros 100.000 caracteres (ver "No verificado").
- Versiones: la documentación de Claude Code cita funciones hasta v2.1.314; no se verificó qué versión tiene instalada Alex. opencode: el issue citado menciona 1.18.x.

---

## 1. Resumen ejecutivo

1. **Claude Code ofrece los tres niveles de control** (auditar, advertir, bloquear) y casi todo es legible como archivo JSON. Esto lo hace un buen primer adaptador. Los puntos de bloqueo son: reglas `deny`/`ask` (se evalúan deny, luego ask, luego allow, desde cualquier ámbito), el hook `PreToolUse` (puede denegar), y el sandbox.
2. **El sandbox de Claude Code no existe en Windows nativo.** Texto oficial: "On native Windows, Claude Code runs commands unsandboxed." Confirma el hallazgo preliminar. Consecuencia para Alex: en Windows nativo la única barrera real es la política de permisos de Claude Code, que es de nivel de aplicación, no del SO.
3. **Las reglas `deny` de lectura NO son una barrera del SO, ni siquiera en Claude Code.** Oficial: no aplican a subprocesos arbitrarios (un script Python o Node que abre archivos por su cuenta) ni a comandos que leen sin nombrar archivos (`grep -r`). Esto respalda la decisión ya tomada: un `deny` no baja el hallazgo, solo añade la nota "protegido por regla".
4. **Los hooks y los comandos de MCP locales corren con acceso completo del usuario**, fuera del sandbox aunque este estuviera activo. Un hook o un servidor MCP stdio es código arbitrario con los permisos de Alex. AgentReach debería listarlos como superficie de alcance.
5. **Los registros contienen secretos en texto plano.** Oficial: "If a tool reads a `.env` file or a command prints a credential, that value is written to `projects/<project>/<session>.jsonl`." Retención por defecto: 30 días. Esto es decisivo para la fase 2: AgentReach puede leer transcripciones para detectar "el agente lo leyó", pero debe tratarlas como material sensible y nunca copiar valores.
6. **opencode: permisos muy permisivos por defecto, sin sandbox documentado, y un issue de evasión sin resolver.** La mayoría de permisos es `allow` por defecto; solo `external_directory` y `doom_loop` son `ask`, y los `.env` piden aprobación. Existe un reporte oficial (issue #42979) de que `external_directory: deny` se evade vía redirección de shell; se cerró "not planned" por inactividad, sin respuesta de mantenedores. No está probado que `read: deny` se evada vía bash (eso solo lo afirma un tercero).
7. **opencode tiene un mecanismo de plugins** con `tool.execute.before` que, según un ejemplo oficial, bloquea lanzando un error. Eso da capacidad de "auditar y bloquear", pero requiere que el usuario instale un plugin JS/TS; no es configuración declarativa. La documentación no aclara si intercepta herramientas MCP o subagentes.
8. **opencode en Windows nativo está soportado pero no recomendado** por su propia documentación ("can run directly on Windows", pero recomienda WSL). Los datos viven en `%USERPROFILE%\.local\share\opencode` (SQLite `opencode.db`, `auth.json` con claves y tokens OAuth).
9. **Capacidad declarada propuesta para el adaptador (fase 3):**
   - Claude Code: auditar + advertir en MVP; **auditar y bloquear** técnicamente posible (hooks y reglas deny), con la salvedad de que el bloqueo es política y no barrera del SO en Windows.
   - opencode: auditar + advertir; bloqueo posible solo vía plugin o reglas `deny`, de fiabilidad parcial y sin verificar en Windows.

---

## 2. Tabla comparativa

| Aspecto | Claude Code | opencode |
|---|---|---|
| Config de usuario (Windows) | `%USERPROFILE%\.claude\settings.json` ("On Windows, `~/.claude` means `%USERPROFILE%\.claude`") | `~/.config/opencode/opencode.json`. Equivalente Windows no documentado (ver No verificado) |
| Config de proyecto | `.claude/settings.json` (compartido), `.claude/settings.local.json` (personal) | `opencode.json` en el proyecto, `.opencode/` |
| Config gestionada (Windows) | `C:\Program Files\ClaudeCode\managed-settings.json` (+ `managed-settings.d\`), registro `HKLM\SOFTWARE\Policies\ClaudeCode` valor `Settings`; también HKCU (escribible por el usuario) | `%ProgramData%\opencode` (archivos gestionados) |
| Precedencia | Gestionado > línea de comandos (`--settings`) > local > proyecto > usuario. Las listas se combinan; `deny` gana desde cualquier ámbito | De menor a mayor: remota (.well-known), global, `OPENCODE_CONFIG`, proyecto, `.opencode`, `OPENCODE_CONFIG_CONTENT`, archivos gestionados, preferencias gestionadas macOS. "Merged together, not replaced" |
| Reglas de permisos | `permissions.allow/ask/deny/additionalDirectories/defaultMode`. Orden deny, ask, allow; el primero que coincide manda | `permission` con allow/ask/deny por herramienta y patrón; gana la **última** regla que coincide |
| Valores por defecto | Lectura libre dentro del directorio de trabajo y directorios adicionales; Bash, edición, web piden aprobación en modo Manual | "Most permissions default to allow"; `external_directory` y `doom_loop` en `ask`; `.env` pide aprobación |
| Modos de aprobación | `defaultMode`, incluidos `acceptEdits`, `plan`, `dontAsk`, `auto`, `bypassPermissions` | Sin modos equivalentes documentados; agentes `build` (todo habilitado) y `plan` (deniega ediciones) |
| Sandbox | Opcional, **desactivado por defecto, no disponible en Windows nativo** (macOS, Linux, WSL2). Solo cubre comandos de shell | **No documentado** (las páginas de enterprise y troubleshooting no lo mencionan) |
| Hooks | 5 tipos (command, http, mcp_tool, prompt, agent); eventos que pueden bloquear: `PreToolUse`, `UserPromptSubmit`, `Stop`, `ConfigChange`, etc. | Plugins JS/TS con eventos (`tool.execute.before/after`, `permission.asked`, `session.*`, `shell.env`). Bloqueo por excepción (inferido de un ejemplo) |
| MCP | `.mcp.json` (proyecto), `~/.claude.json` (local y usuario), `managed-mcp.json`, `allowedMcpServers`/`deniedMcpServers` | clave `mcp` en la config, tipos `local`/`remote`, tokens OAuth en `~/.local/share/opencode/mcp-auth.json` |
| Agentes/skills | `.claude/agents/*.md`, `~/.claude/agents`, `skills/<n>/SKILL.md` en proyecto, usuario y gestionado | `.opencode/agents`, `~/.config/opencode/agents`; skills en `.opencode/`, `.claude/`, `.agents/` (proyecto y global) |
| Registros | `~/.claude/projects/<proyecto>/<sesion>.jsonl` (texto plano); `history.jsonl`; `file-history/`; `debug/` | `%USERPROFILE%\.local\share\opencode\opencode.db` (SQLite), `log\opencode.log`, `snapshot\`, `auth.json` |
| Retención | `cleanupPeriodDays`, por defecto 30 | No documentada |
| Telemetría estructurada | OpenTelemetry opcional, contenido bajo opt-in | No verificada |
| Herencia de entorno | Subprocesos heredan entorno; `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` lo limpia (opt-in) | No documentado; hook `shell.env` puede añadir variables |
| Symlinks/junctions | Revisa la ruta pedida y la resuelta, incluidas junctions de Windows | No verificado |
| Soporte Windows nativo | Sí; sandbox no | "Can run directly on Windows", recomienda WSL |
| Capacidad declarada del adaptador | Auditar, advertir, bloquear (con salvedades) | Auditar, advertir; bloqueo parcial y sin verificar |

---

## 3. Detalle por pregunta

### P1. Dónde viven las configuraciones, rutas en Windows y precedencia

#### Claude Code

**Settings (permisos, hooks, env, sandbox).** Fuente: https://code.claude.com/docs/en/settings

| Ámbito | Archivo |
|---|---|
| Usuario | `%USERPROFILE%\.claude\settings.json` |
| Proyecto compartido | `.claude/settings.json` |
| Proyecto local | `.claude/settings.local.json` |
| Gestionado | `managed-settings.json` y otras fuentes |

- "On Windows, `~/.claude` means `%USERPROFILE%\.claude`. To keep the home-directory files somewhere else, set `CLAUDE_CONFIG_DIR`". Esto cambia dónde AgentReach debe buscar; la variable está en el entorno del proceso de Claude Code, no necesariamente en el de AgentReach.
- Precedencia (mayor a menor): gestionado, línea de comandos (`--settings`), local, proyecto, usuario. Las listas (por ejemplo `permissions.allow`) se combinan en vez de reemplazarse. Cuatro claves de modelos tienen reglas propias, irrelevantes para AgentReach.
- Existe un quinto archivo, `~/.claude.json`, que "holds your account details, MCP server configurations, per-project state such as trust decisions".
- Edge case Windows: el archivo local se queda junto a `.claude/settings.json` (no en la raíz del repo) "on Windows" (https://code.claude.com/docs/en/settings, sección "Where Claude Code keeps the local file").
- Las reglas `permissions.allow` y `additionalDirectories` del `.claude/settings.json` del proyecto solo se aplican tras aceptar el diálogo de confianza del espacio de trabajo; `deny` y `ask` se aplican de inmediato (https://code.claude.com/docs/en/permissions). **Implicación:** la lectura estática de un `allow` en el repo no prueba que esté activo; depende de si Alex aceptó la confianza. Esa decisión se guarda en `~/.claude.json` (trust), pero el formato exacto no se verificó.
- `permissions.defaultMode` con valores `auto` y `bypassPermissions` no surte efecto desde configuración de proyecto o local, solo desde usuario o gestionado (https://code.claude.com/docs/en/settings).

**Gestionado (empresa).** Fuente: https://code.claude.com/docs/en/managed-settings
- Archivo: `C:\Program Files\ClaudeCode\managed-settings.json`, con directorio opcional `managed-settings.d\`. "Claude Code doesn't read the legacy Windows path `C:\ProgramData\ClaudeCode\managed-settings.json`."
- Registro: `HKLM\SOFTWARE\Policies\ClaudeCode`, valor `Settings` (REG_SZ o REG_EXPAND_SZ con el JSON).
- Registro de usuario: mismo valor bajo `HKCU\SOFTWARE\Policies\ClaudeCode`; se usa solo si no hay documento de administrador por encima. El propio texto lo describe como escribible por el usuario, por eso no cuenta como "fuente de administrador".
- Orden entre fuentes gestionadas: servidor, MDM/HKLM, archivos, HKCU. Por defecto `first-wins`: se usa la fuente de mayor rango y se ignoran las demás (salvo claves que se leen de todas).
- **Implicación:** en el equipo personal de Alex lo esperable es que no exista nada de esto; AgentReach debe reportar "ninguna política gestionada encontrada" como dato, no como error. Una configuración de servidor (consola claude.ai) es **invisible para lectura de archivos** salvo por el caché `~/.claude/remote-settings.json` (https://code.claude.com/docs/en/claude-directory).

**MCP.** Fuente: https://code.claude.com/docs/en/mcp
- Local (por defecto): `~/.claude.json` bajo la ruta del proyecto. Proyecto: `.mcp.json` en la raíz. Usuario: `~/.claude.json`.
- Precedencia: local, proyecto, usuario, plugins, conectores claude.ai; un servidor gestionado (`managedMcpServers`) está por encima de todos. La entrada completa de la fuente ganadora se usa, sin combinar campos.
- Los servidores de `.mcp.json` piden aprobación en sesiones interactivas, **pero en `claude -p` y en el Agent SDK se cargan sin preguntar**. Relevante: un `.mcp.json` malicioso en un repo clonado se ejecuta sin aviso en modo no interactivo.
- Gestionado: `C:\Program Files\ClaudeCode\managed-mcp.json` (https://code.claude.com/docs/en/managed-mcp).
- `.mcp.json` admite `${VAR}` y `${VAR:-default}` en `command`, `args`, `env`, `url`, `headers`. AgentReach puede ver qué variables de entorno se inyectan en servidores MCP, sin leer su valor.

**Agentes y skills.** Fuente: https://code.claude.com/docs/en/claude-directory y https://code.claude.com/docs/en/skills
- `agents/*.md` y `skills/<nombre>/SKILL.md`, en `.claude/` (proyecto) y `~/.claude/` (usuario). Los agentes tienen frontmatter con `tools`, `disallowedTools`, `permissionMode`, `mcpServers`, `hooks`. Los skills tienen `allowed-tools`, `hooks`, etc.
- Skills: "Enterprise over personal, and personal over project." Ruta empresarial: `.claude/skills/` dentro del directorio gestionado; solo se documenta un ejemplo Linux (`/etc/claude-code/.claude/skills/`). La ruta Windows no se verificó (ver No verificado).
- `allowed-tools` de un skill concede aprobación previa de herramientas durante ese turno, "Workspace trust doesn't gate this field" y se aplica incluso en `-p` en una carpeta no confiada. Los `deny` y `ask` siguen ganando. **Implicación:** un skill de proyecto puede ampliar lo que el agente hace sin preguntar. Es un hallazgo de alcance legible estáticamente.
- Un agente puede declarar `permissionMode` en su frontmatter; el efecto exacto sobre las reglas no se verificó.

**Hooks.** Fuente: https://code.claude.com/docs/en/hooks
- Se configuran en `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, política gestionada, `hooks/hooks.json` de plugins, y frontmatter de skill o agente. Las entradas se combinan entre niveles.

**Instrucciones.** `CLAUDE.md`, `CLAUDE.local.md`, `rules/*.md`, `AGENTS.md` (puede leerse en lugar de CLAUDE.md). Son contexto, no control.

#### opencode

**Config.** Fuente: https://opencode.ai/docs/config/
- De menor a mayor precedencia: (1) remota `.well-known/opencode`, (2) global `~/.config/opencode/opencode.json`, (3) `OPENCODE_CONFIG`, (4) `opencode.json` del proyecto, (5) directorios `.opencode`, (6) `OPENCODE_CONFIG_CONTENT`, (7) archivos gestionados, (8) preferencias gestionadas de macOS. "Configuration files are merged together, not replaced."
- `OPENCODE_CONFIG_DIR` apunta a un directorio extra que se carga tras global y `.opencode`.
- Gestionado: macOS `/Library/Application Support/opencode/`, Linux `/etc/opencode/`, **Windows `%ProgramData%\opencode`**.
- La documentación **no da la ruta Windows de la config global**; solo `~/.config/opencode/opencode.json`. Los datos usan `%USERPROFILE%\.local\share\opencode` (https://opencode.ai/docs/troubleshooting/), lo que sugiere `%USERPROFILE%\.config\opencode`, pero **no está verificado**.
- Sustitución: `{env:VAR}` (vacía si no existe) y `{file:ruta}`. **Implicación:** la config puede referenciar secretos por archivo o variable; AgentReach debe registrar la referencia, nunca el valor.

**Agentes.** https://opencode.ai/docs/agents/ : JSON bajo `agent` en la config, o Markdown en `~/.config/opencode/agents/` y `.opencode/agents/`. Campos: `description`, `mode`, `permission`, `model`, `steps`, `prompt`, `hidden`, `disable`. `tools` está obsoleto. Por defecto `build` tiene todo habilitado; `plan` deniega ediciones salvo `.opencode/plans/*.md` y **no restringe bash**. Los permisos de agente se combinan con los globales y los del agente tienen prioridad.

**Skills.** https://opencode.ai/docs/skills/ : `.opencode/skills/`, `~/.config/opencode/skills/`, `.claude/skills/`, `~/.claude/skills/`, `.agents/skills/`, `~/.agents/skills/`. Control con `permission.skill`.

**Instrucciones.** https://opencode.ai/docs/rules/ : `AGENTS.md`, con respaldo a `CLAUDE.md` y `~/.claude/CLAUDE.md`. Variables para desactivar compatibilidad: `OPENCODE_DISABLE_CLAUDE_CODE`, `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT`, `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS`.

**Implicación importante para Alex:** opencode **lee `~/.claude/skills/`, `.claude/skills/` y `CLAUDE.md`** si no se desactiva. En el entorno de Alex (repo con `.claude/` de BMAD), opencode puede cargar los mismos skills e instrucciones. Dos agentes distintos, un mismo conjunto de instrucciones: AgentReach debería saberlo al hacer el segundo adaptador.

**Plugins.** https://opencode.ai/docs/plugins/ : `.opencode/plugins/` y `~/.config/opencode/plugins/`, más la clave `plugin` (paquetes npm). "OpenCode runs `bun install` at startup" para dependencias declaradas en `.opencode/package.json`. **Implicación:** un plugin o dependencia en el proyecto es código que se ejecuta al arrancar; es superficie de alcance legible estáticamente.

**MCP.** https://opencode.ai/docs/mcp-servers/ : clave `mcp`, `type: local|remote`, campo `environment` para variables del servidor local.

### P2. Qué puede leer AgentReach de forma estática

| Dato | Claude Code | opencode |
|---|---|---|
| Reglas allow/ask/deny | Sí: `permissions` en 4 archivos + managed + registro HKLM/HKCU | Sí: `permission` en config y por agente |
| Orden de evaluación | deny > ask > allow, cualquier ámbito (https://code.claude.com/docs/en/permissions) | Última coincidencia gana (https://opencode.ai/docs/permissions/) |
| Directorios adicionales | `permissions.additionalDirectories`; también `--add-dir` (efímero, no legible estáticamente) | Regla `external_directory` |
| Sandbox | `sandbox.*` (enabled, filesystem allow/deny, network). En Windows nativo es irrelevante: no se aplica | Nada documentado |
| Variables de entorno | Bloque `env` en settings (visible), pero el entorno real heredado del shell **no** es legible estáticamente | `{env:VAR}` en config (referencias); entorno heredado no legible |
| MCP | Sí, 3 archivos + gestionado | Sí, clave `mcp` |
| Hooks/plugins | Sí (comandos, URLs, tipos) | Sí (archivos de plugin, paquetes npm) |
| Modo por defecto | `permissions.defaultMode` | n/a |

**Reglas de lectura relevantes (Claude Code).**
- Sintaxis de rutas en reglas de lectura/edición en Windows: "paths are normalized to POSIX form before matching. `C:\Users\alice` becomes `/c/Users/alice`, so use `//c/**/.env`" (https://code.claude.com/docs/en/permissions). AgentReach debe normalizar rutas Windows antes de comparar con reglas, o dará falsos "no protegido".
- Reglas con sintaxis `Bash(...)` de comandos: coinciden con subcomandos compuestos para deny/ask, y un `deny` "doesn't match the same program by path or inside `sh -c`" (https://code.claude.com/docs/en/permissions). Un `deny` de Bash es una heurística, no un cierre.
- Reglas `deny` de Read/Edit: ver advertencia en P3.

**Ambigüedad a dejar explícita en el reporte:** una regla escrita no equivale a una regla activa (confianza del espacio de trabajo, `--settings`, política gestionada de servidor, `bypassPermissions`). Por eso la lectura estática solo puede llegar a "comprobado" para lo **configurado**, y a "potencial" para lo **efectivo**, salvo que AgentReach pueda leer la política efectiva (p. ej. salida de `claude doctor` o `/status`, no verificados como API estable).

### P3. Puntos de control y capacidad declarada

#### Claude Code

| Mecanismo | Qué controla | Puede bloquear | Fuente |
|---|---|---|---|
| Permisos `deny`/`ask` | Herramientas y rutas | Sí (deny), pide confirmación (ask) | https://code.claude.com/docs/en/permissions |
| `PreToolUse` hook | Cada llamada a herramienta antes del prompt de permisos | Sí: salida `permissionDecision: deny`, o código de salida 2 | https://code.claude.com/docs/en/hooks |
| Otros hooks que bloquean con código 2 | `UserPromptSubmit`, `Stop`, `SubagentStop`, `ConfigChange` (no `policy_settings`), `PreCompact`, `WorktreeCreate`, etc. | Sí | https://code.claude.com/docs/en/hooks |
| Hooks que no bloquean | `PostToolUse`, `PostToolUseFailure`, `SessionStart`, `PermissionDenied`, etc. | No (solo observan) | https://code.claude.com/docs/en/hooks |
| Sandbox | Comandos de shell | Sí, a nivel de SO, **no en Windows nativo** | https://code.claude.com/docs/en/sandboxing |
| `blockReadsOutsideWorkingDirectories` | Lecturas con herramientas de archivo fuera del directorio de trabajo | Sí (v2.1.257+) | https://code.claude.com/docs/en/settings |
| Política gestionada | Lo anterior, con `allowManagedHooksOnly`, `allowManagedPermissionRulesOnly`, `allowManagedMcpServersOnly` | Sí; el usuario no puede anular | https://code.claude.com/docs/en/managed-settings |

Hechos importantes:
- Los hooks de `PreToolUse` **no pueden saltarse un deny**: "a matching deny rule blocks the call, and a matching ask rule still prompts even when the hook returned `allow`" (https://code.claude.com/docs/en/permissions). Un hook solo puede endurecer o no opinar.
- "Exit 0 with no output means the hook has no decision to report... The hook can deny the call, but staying silent doesn't approve it" (hooks).
- "Because the `if` filter is best-effort, use the permission system rather than a hook to enforce a hard allow or deny" (hooks). Un hook no es un cierre duro.
- **Hook que falla o expira no bloquea por defecto**: un `PreToolUse` que expira "doesn't block the tool call" salvo `onFailure: "block"`. Y en Windows sin Git Bash "any exit code other than 0 or 2 from that hook counts as a failure". Si AgentReach quisiera instalar un hook de protección en fase 3, debe fijar `onFailure: block`.
- En Windows el hook usa por defecto `powershell` si no hay Git Bash; `.cmd` y `.bat` no se pueden lanzar en forma exec (hooks).
- **Advertencia oficial sobre los `deny` de lectura** (https://code.claude.com/docs/en/permissions): "Read and Edit deny rules apply to Claude's built-in file tools, to file commands Claude Code recognizes in Bash, such as `cat`, `head`, `tail`, `sed`, and `tee`, and to the targets of Bash redirections. They don't apply to a command that reads files without naming them, such as `grep -r pattern .`... or to arbitrary subprocesses that read or write files indirectly, like a Python or Node script that opens files itself. For OS-level enforcement... enable the sandbox."
- **El sandbox solo cubre shell**: "Read, Edit, Write, WebFetch, and WebSearch follow permission rules instead. A `denyRead` entry doesn't stop the Read tool" (sandboxing). Y "command hooks, local MCP servers, plugin monitors, LSP servers, and helper commands such as your status line command and `apiKeyHelper` run with your full access."
- Lectura por defecto del sandbox (cuando existe): "Most of the machine, including credential files such as `~/.ssh` and `~/.aws/credentials`" (sandboxing). Confirma el hallazgo preliminar.
- Modos: `bypassPermissions` anula avisos; en `dontAsk` la reintento sin sandbox se deniega. El valor `auto` usa un clasificador.

**Capacidad declarada del adaptador Claude Code:** *auditar y bloquear* es técnicamente alcanzable (hooks `PreToolUse` y reglas `deny`), pero hay que declararlo con honestidad: en Windows nativo el bloqueo es de **política de aplicación**, no del SO, y tiene huecos documentados. Para el MVP basta *auditar y advertir*.

#### opencode

| Mecanismo | Qué controla | Puede bloquear | Fuente |
|---|---|---|---|
| `permission` allow/ask/deny | Herramientas y patrones | `deny` bloquea; `ask` pide | https://opencode.ai/docs/permissions/ |
| Plugin `tool.execute.before` | Llamadas a herramientas | Probable, lanzando error (inferido de un ejemplo `.env`; no declarado en el texto) | https://opencode.ai/docs/plugins/ |
| Plugin `permission.asked` / `permission.replied` | Eventos de permisos | Observación; no verificado si deciden | https://opencode.ai/docs/plugins/ |
| Config gestionada | Configuración central | Sí en principio; ruta Windows `%ProgramData%\opencode` | https://opencode.ai/docs/config/ |
| Sandbox | No documentado | No | páginas de enterprise y troubleshooting no lo mencionan |

Hechos importantes:
- "Most permissions default to allow"; `external_directory` y `doom_loop` en `ask`; `read` permitido pero archivos `.env` requieren aprobación por defecto (https://opencode.ai/docs/permissions/). Eso cubre `.env` pero no otros secretos (`~/.aws`, tokens en cualquier archivo): el patrón de PocketOS (un token en un archivo ajeno a la tarea) **no** se frenaría con los valores por defecto.
- Claves de permisos: `read`, `edit` (incluye write y patch), `glob`, `grep`, `bash`, `task`, `todowrite`, `skill`, `lsp`, `question`, `webfetch`, `websearch`, `external_directory`, `doom_loop`.
- "The last matching rule wins" y patrones con `*` y `?`. Contraste con Claude Code, donde manda deny. Un adaptador que evalúe reglas debe implementar la semántica correcta de cada plataforma; no es intercambiable.
- **La documentación oficial de permisos no dice si un `deny` de `read` afecta a comandos bash que tocan el mismo archivo.** Lo afirma `[TERCERO]` Intility (https://developers.intility.com/docs/external/inference/opencode-permissions/): "A determined agent can bypass read-deny rules via bash (cat, grep, python3 -c, base64)". Fuente de terceros, no verificada por mí.
- **Evidencia oficial parcial:** el issue #42979 de `anomalyco/opencode` ("Shell redirection bypasses the external_directory permission", https://github.com/anomalyco/opencode/issues/42979) reporta que con `external_directory: deny` las herramientas de archivo rechazan rutas fuera del espacio de trabajo pero **bash no**: la verificación de rutas solo corre para una lista de 14 comandos y no revisa objetivos de redirección. Reportó evasión en 9 de 35 intentos de escritura y 8 de 34 de lectura, con dos modelos, en Linux, versión 1.18.16 y 1.18.18. Estado: cerrado "not planned" el 17 de octubre de 2026 por un bot tras 60 días sin actividad; sin respuesta de un mantenedor. Es un reporte de un usuario, no una confirmación del proyecto; la reproducción no fue replicada por mí y es en Linux.
- Plan no restringe bash (https://opencode.ai/docs/agents/): el modo "solo planificar" no es una garantía de solo lectura.
- `tools` en agentes está obsoleto en favor de `permission`.

**Capacidad declarada del adaptador opencode:** *auditar y advertir*. El bloqueo no puede declararse como fiable: faltan sandbox documentado y confirmación de que `deny` cubre bash. Un plugin podría bloquear, pero no está claro que intercepte MCP ni subagentes, y requiere que el usuario lo instale.

### P4. Registros y transcripciones (relevante para fase 2)

> **ADVERTENCIA DE SECRETOS.** Los registros de ambas plataformas pueden contener valores de secretos en texto plano. AgentReach, si los lee en fase 2, debe procesarlos en memoria, extraer solo metadatos (qué ruta se leyó, qué herramienta, cuándo) y **nunca** volcar contenido, ni a reportes, ni a logs propios, ni a salida de error.

#### Claude Code (fuente: https://code.claude.com/docs/en/claude-directory, sección "Application data")

| Ruta bajo `~/.claude/` (`%USERPROFILE%\.claude\`, o `CLAUDE_CONFIG_DIR`) | Contenido |
|---|---|
| `projects/<proyecto>/<sesion>.jsonl` | Transcripción: mensajes, llamadas a herramientas y resultados, más el prompt de sistema, definiciones de herramientas y parámetros de las peticiones al modelo |
| `projects/<proyecto>/<sesion>/subagents/` | Transcripciones de subagentes, mismo formato |
| `projects/<proyecto>/<sesion>/tool-results/` | Salidas grandes de herramientas en archivos aparte |
| `file-history/<sesion>/` | Copias previas de archivos que Claude modificó (puntos de control) |
| `history.jsonl` | Prompts escritos, con fecha y ruta del proyecto; se conserva hasta que se borre |
| `debug/` | Registros de depuración (solo con `--debug` o `/debug`) |
| `paste-cache/` | Contenido de pegados grandes |
| `shell-snapshots/` | Alias, funciones y opciones del shell capturados al iniciar |
| `session-env/` | Metadatos de entorno por sesión (contenido exacto no verificado) |
| `%TEMP%\claude\<proyecto>\<sesion>\scratchpad\` | Archivos temporales de sesión |

- Retención: se borra todo lo anterior tras `cleanupPeriodDays`, por defecto **30 días**, mínimo 1.
- Texto plano: "Transcripts and history are not encrypted at rest. OS file permissions are the only protection. If a tool reads a `.env` file or a command prints a credential, that value is written to `projects/<project>/<session>.jsonl`."
- Mitigaciones oficiales: bajar `cleanupPeriodDays`; `CLAUDE_CODE_SKIP_PROMPT_HISTORY=1` (no escribe transcripciones ni historial; "Sessions started with this variable set do not appear in `--resume`"); reglas deny para credenciales; `claude purge`.
- Los `.heapsnapshot` (de `/heapdump`) contienen conversación y credenciales que el proceso tenía y no se limpian solos.
- Formato JSONL: una línea JSON por evento. **El esquema de cada línea (nombres de campos, cómo se enlaza una llamada con su resultado) no está en lo que verifiqué.** Hay que inspeccionar o hallar documentación oficial antes de diseñar el analizador. Un campo `transcript_path` llega a los hooks (https://code.claude.com/docs/en/hooks), pero se escribe de forma asíncrona y "may lag the in-memory conversation".
- **OpenTelemetry** (https://code.claude.com/docs/en/monitoring-usage): eventos `claude_code.tool_result` y `claude_code.tool_decision` (con `decision`, `source`, `permission_mode`). Parámetros de herramientas solo con `OTEL_LOG_TOOL_DETAILS=1`; salida de herramientas solo con `OTEL_LOG_TOOL_CONTENT=1` y trazas; cuerpos completos con `OTEL_LOG_RAW_API_BODIES` ("Bodies include the entire conversation history"). Un repo no puede activar la captura de contenido: se configura en entorno, usuario o gestionado. Requiere un colector; no es lectura estática de un archivo local.

**Para las etapas de "alcanzable":** la etapa 3 ("el agente lo leyó") es viable leyendo los `.jsonl` (hay llamadas a herramientas con rutas) y la etapa 4 ("lo usó") es mucho más difícil: requiere correlacionar un valor leído con una llamada posterior sin ver el valor. Supuesto sin verificar.

#### opencode (fuente: https://opencode.ai/docs/troubleshooting/)

- Datos: `%USERPROFILE%\.local\share\opencode` en Windows. `opencode.db` (SQLite con proyectos, sesiones y mensajes), `auth.json` (claves API y tokens OAuth), `log\opencode.log`, `snapshot\` (instantáneas para deshacer). Comando `opencode db path` para ubicar la base; `OPENCODE_DB` puede cambiarla.
- Tokens MCP OAuth: `~/.local/share/opencode/mcp-auth.json` (https://opencode.ai/docs/mcp-servers/).
- **La página no describe cifrado ni controles de acceso**, y `auth.json` guarda credenciales: si AgentReach audita ubicaciones sensibles, este archivo es un hallazgo de metadatos (existe, ACL).
- Retención no documentada. Esquema de tablas de SQLite no verificado. Una base SQLite puede estar bloqueada por el proceso en ejecución; leerla sin modificarla requiere abrirla en modo solo lectura (no verificado en Windows).
- La página de enterprise afirma "OpenCode does not store your code or context data", lo cual parece contradecir `opencode.db` con mensajes de sesión. **Contradicción aparente:** se interpreta como "no los almacena el servicio", no el disco local, pero el texto no lo aclara. Marcado como no resuelto.
- Compartir sesiones: la página `/docs/share/` devolvió 404. La página de enterprise recomienda "disabling the share pages", sin explicar cómo. Cuál es el valor por defecto de compartir **no se verificó**; es un riesgo de exfiltración que conviene resolver antes del adaptador.

### P5. Herencia de entorno, credenciales, symlinks y ACL

#### Claude Code

- Los subprocesos (Bash, PowerShell, hooks, MCP stdio) se inician con entorno propio de Claude Code. La documentación **no dice literalmente** "hereda todo el entorno"; lo que sí dice es que existe `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`, que "removes credentials from the environments of the subprocesses it starts, such as Bash commands, hooks, and stdio MCP servers. This reduces what a prompt injection attack can read" (https://code.claude.com/docs/en/env-vars). **Inferencia razonable:** sin esa variable, los subprocesos ven esas credenciales. Marcado como inferencia.
- Detalle del scrub: quita por nombre y por forma del valor (`ANTHROPIC_API_KEY`, `AWS_SECRET_ACCESS_KEY`, `NPM_TOKEN`, `DB_PASSWORD`, URLs con contraseña), pero **deja** `GITHUB_TOKEN`, `GH_TOKEN`, `GH_ENTERPRISE_TOKEN`, `GITHUB_ENTERPRISE_TOKEN` y `HTTP_PROXY`/`HTTPS_PROXY`, "so that `gh` and scripts that call the GitHub API keep working". Oficial: "use it as one layer alongside narrow permission rules rather than as the only control". El proyecto usa `gh` con sesión propia, así que ese token queda visible para el agente.
- Para servidores MCP stdio existe `CLAUDE_CODE_MCP_ALLOWLIST_ENV=1`: "spawn stdio MCP servers with only a safe baseline environment plus the server's configured `env`, instead of inheriting your shell environment". Esto confirma que el comportamiento por defecto de MCP stdio es heredar el entorno del shell.
- Claude Code exporta `CLAUDECODE=1` y `CLAUDE_CODE_CHILD_SESSION=1` en los subprocesos: AgentReach, si corre dentro de un hook o de una herramienta, puede saber que lo lanzó el agente (útil para el caso "AgentReach ejecutado por el agente").
- Las credenciales de Claude Code viven en `~/.claude/.credentials.json` (https://code.claude.com/docs/en/claude-directory). No se leyó el archivo; en Windows no se verificó si usa además otro almacén del sistema.
- El bloque `env` de settings fija variables; esas variables son legibles estáticamente. `CLAUDE_CONFIG_DIR` no se puede fijar desde `.claude/settings.json` del proyecto.
- Rutas UNC: "a command whose arguments include a network (UNC) path... prompts because accessing a network path can send your Windows credentials to the host it names" (https://code.claude.com/docs/en/permissions). Reconoce el riesgo de credenciales NTLM; los UNC no se aceptan como directorios de trabajo.
- Unidades de red: se aconseja mapear a una letra y usar `--add-dir Z:\`. Un directorio adicional así amplía el alcance y no es visible en archivos.
- **Symlinks y junctions (oficial):** "When a file path Claude requests goes through a symlink, the permission check covers two paths: the one Claude requested and the file it resolves to. This applies to symbolic links on macOS, Linux, and Windows, and to directory junctions on Windows" (https://code.claude.com/docs/en/permissions). Para AgentReach: una junction dentro del repo que apunta fuera extiende el alcance, y Claude Code la evalúa por ambas rutas. Los detalles de qué hace con un enlace que sale del directorio de trabajo no se verificaron.
- **ACL de Windows:** la documentación leída **no dice nada** sobre ACL de `~/.claude` ni de los transcripts; solo "OS file permissions are the only protection". Que Claude Code ajuste ACL o no, no se verificó.
- Directorio de trabajo: el agente puede leer sin preguntar en el directorio de trabajo y los directorios adicionales; fuera de ellos pide aprobación, salvo que se haya concedido (tabla de permisos). Esto matiza el hallazgo previo "lee casi todo por defecto, incl. ~/.ssh": **sin sandbox y con una regla allow amplia, o vía Bash con aprobación, sí**; con la herramienta Read en modo Manual, fuera del directorio de trabajo pide confirmación. Reconciliación pendiente con el memlog (ver No verificado): el hallazgo previo se refería al sandbox ("Reads: most of the machine"), donde la lectura es por defecto muy amplia; la herramienta Read tiene otro comportamiento.

#### opencode

- Entorno heredado de bash/MCP local: **no documentado** (solo se documenta `environment` para servidores MCP locales y el hook `shell.env`, que "can set environment variables for shell execution, covering both AI tools and user terminals"). Asumir que hereda es inferencia sin verificar.
- Credenciales: `auth.json` y `mcp-auth.json` en `%USERPROFILE%\.local\share\opencode` (ver P4).
- Symlinks, junctions, ACL: no verificado.
- Servidor remoto: si se usa `opencode serve --hostname 0.0.0.0`, se expone red; "set `OPENCODE_SERVER_PASSWORD`" (https://opencode.ai/docs/windows-wsl/). Es un riesgo de configuración legible (flags en scripts de arranque), no de archivo de config.

---

## 4. Lista de no verificado

Cada ítem se debe leer como "no lo confirmé", no como "es falso".

**Claude Code**
1. Esquema de cada línea de `projects/<proyecto>/<sesion>.jsonl` (campos, enlace llamada-resultado). Hace falta documentación oficial o una muestra inspeccionada con cuidado de no leer valores.
2. Que los subprocesos hereden el entorno completo por defecto: inferido de la existencia de `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` y `CLAUDE_CODE_MCP_ALLOWLIST_ENV`; no hay frase oficial que lo diga de Bash.
3. Ruta Windows del directorio de skills gestionados (la página de skills solo da un ejemplo Linux).
4. Cómo y dónde se guarda la decisión de confianza del espacio de trabajo en `~/.claude.json` y si AgentReach puede leerla de forma estable.
5. Si `claude doctor` o `/status` ofrecen salida estable para leer la política efectiva; no se verificó que sean interfaz soportada para herramientas.
6. Comportamiento exacto de `permissionMode` en el frontmatter de agentes y su efecto sobre reglas.
7. Almacén real de credenciales de Claude Code en Windows (solo vi `.credentials.json`); no leí ningún archivo de credenciales.
8. ACL de `~/.claude` y de los transcripts.
9. Conducta de los enlaces que salen del directorio de trabajo (más allá de "se comprueban ambas rutas").
10. Lectura incompleta: se leyó solo el primer tramo de las páginas largas (hooks, env-vars, mcp, skills, monitoring-usage, sandboxing: 100.000 de 110.000 a 290.000 caracteres). Pueden existir matices de hooks (`PreToolUse` `allow`/`defer`) y de seguridad no leídos. No se leyeron las páginas `security`, `permission-modes` ni `settings-reference`.
11. Si los hooks `PreToolUse` interceptan herramientas MCP y de subagentes en todos los casos (los eventos incluyen `agent_id`, pero no verifiqué la cobertura).
12. Si el entorno de Alex tiene Git Bash instalado (determina si se usa Bash o PowerShell como herramienta de shell por defecto); la página dice que Claude Code "routes shell commands through Git Bash unless you set `CLAUDE_CODE_USE_POWERSHELL_TOOL=1`" en cuentas claude.ai y Console con Git Bash.
13. Contradicción aparente a reconciliar con el memlog: el memlog dice "lee por defecto casi todo, incl. ~/.ssh y ~/.aws"; la documentación dice eso del **sandbox** (lectura por defecto), mientras que la herramienta Read pide aprobación fuera del directorio de trabajo. Ambos pueden ser ciertos; la formulación del PRD debería precisar a qué se refiere.

**opencode**
1. Ruta Windows de la configuración global (solo se documenta `~/.config/opencode/`).
2. Si `read: deny` se evade vía bash (solo `[TERCERO]` Intility lo afirma; la documentación oficial no lo trata). El issue #42979 trata `external_directory`, en Linux, y se cerró por inactividad.
3. Si `tool.execute.before` bloquea (inferido de un ejemplo) y si intercepta MCP y subagentes (la página no lo dice).
4. Shell que usa la herramienta bash en Windows nativo.
5. Herencia de entorno en bash y MCP locales.
6. Modo y valor por defecto de compartir sesiones (`/docs/share/` devolvió 404; la página de enterprise recomienda desactivarlo sin explicar cómo). Riesgo de exfiltración sin cerrar.
7. Esquema de `opencode.db` y retención.
8. Telemetría estructurada (no se buscó página equivalente).
9. Symlinks, junctions y ACL en Windows.
10. Si existe sandbox no documentado, o un modo restringido. Solo puedo decir "no documentado en las páginas leídas": config, permissions, troubleshooting, enterprise y tools.
11. La contradicción aparente entre "OpenCode does not store your code or context data" (enterprise) y la base `opencode.db` con mensajes (troubleshooting).
12. Posible diferencia entre la versión "OpenCode 1" de la documentación (que cita límites como "In OpenCode 1, webfetch accepts only allow, ask, or deny") y la que Alex tenga instalada.

**Transversal**
- Dev-Alex (agente personal de Alex) no se investigó: no tengo fuente.
- Visual Studio: no se investigó cómo Claude Code u opencode se integran con Visual Studio ni dónde guardan configuración si lo hacen a través de él. La documentación de Claude Code menciona extensiones para VS Code y JetBrains, no Visual Studio. **Esto afecta a Alex directamente y queda abierto.**
- Incidentes (PocketOS, etc.) no se reverificaron aquí; no eran parte de esta tarea.

---

## 5. Implicaciones para el adaptador y el PRD

### Para la definición de "alcanzable" y los niveles

1. **"Comprobado" en etapa 2 es posible en Windows nativo, pero con una precisión:** el agente corre con los permisos del usuario y sin sandbox, así que "los permisos del SO lo hacen legible" es verificable. Lo que **no** es verificable estáticamente es si el agente **lo intentaría sin pedir permiso**: eso depende de reglas, modo y confianza. Propuesta: separar en el hallazgo dos campos, *legible por el SO* (comprobado) y *postura del agente* (política: bloqueado por regla / pide aprobación / permitido / desconocido).
2. **Lectura de reglas `deny`:** la decisión ya tomada (reportar igual, nota "protegido por regla") queda **respaldada por fuente oficial** para Claude Code y por fuente parcial para opencode. Sugerencia de redacción para el reporte: "protegido por política del agente; no es barrera del SO".
3. **Estimación honesta de `potencial` frente a `hipótesis`:** una regla `deny` válida en Claude Code, sin sandbox, cubre herramientas conocidas pero no scripts arbitrarios; por eso tiene sentido que el hallazgo se mantenga como "comprobado legible" con nota, y no baje a potencial.
4. Superficies de alcance que AgentReach debería inventariar además de archivos y variables (todas legibles estáticamente): hooks (código que corre con acceso completo), servidores MCP stdio (ídem), plugins de opencode (se ejecutan al arrancar), skills con `allowed-tools`, directorios adicionales, junctions dentro del repo, `.mcp.json` que se carga sin aprobar en modo no interactivo, y el token `GITHUB_TOKEN`/`GH_TOKEN` que el scrub de Claude Code deja pasar.

### Para el diseño del adaptador

1. **Contrato del adaptador:** cada adaptador debe declarar (a) rutas de configuración por ámbito y orden de precedencia, (b) semántica de evaluación de reglas (deny gana en Claude Code; última coincidencia gana en opencode; no son intercambiables), (c) normalización de rutas (Claude Code usa forma POSIX con `//c/` para unidades), (d) capacidad de control, (e) ubicación y formato de registros, (f) qué no puede saber (p. ej. política de servidor).
2. **Cuatro estados para el origen de un dato de configuración**, para no mentir: *leído de archivo*, *no encontrado*, *ilegible* (permiso o formato), *fuente no visible* (política de servidor, registro no accesible). La política de servidor no deja rastro estático salvo `remote-settings.json`.
3. **Declaración de capacidad (fase 3):**
   - Claude Code: `audit + warn` en MVP; `block` posible con hooks y reglas, declarado como "política de aplicación, sin barrera de SO en Windows nativo".
   - opencode: `audit + warn`; `block` marcado como "no garantizado" hasta verificar.
4. **Si en fase 3 AgentReach instalara hooks** (rompe la regla de solo lectura del MVP, así que es una decisión de producto, no técnica): usar `onFailure: block`, porque un hook que falla o expira no bloquea por defecto, y recordar que el propio hook corre con acceso completo del usuario. Un hook no sustituye a las reglas `deny`.
5. **Fase 2:** leer transcripciones obliga a un modo explícito (opt-in) y a un analizador que descarte contenido al leer. Para Claude Code los `.jsonl` están en `%USERPROFILE%\.claude\projects\`; para opencode hay una base SQLite. Si se pide solo "el agente leyó la ruta X", la etapa 3 es viable; la etapa 4 ("lo usó") es mucho más débil y probablemente solo alcance "hipótesis".

### Para el PRD (cambios o preguntas concretas)

1. Actualizar el memlog: el sandbox no existe en Windows nativo (confirmado, fuente primaria) y los hooks y servidores MCP quedan fuera del sandbox aunque existiera. Precisar la afirmación "lee por defecto casi todo" (ver No verificado, Claude Code, punto 13).
2. Añadir como requisito de seguridad: AgentReach no lee ni muestra el contenido de transcripciones ni de archivos de credenciales; si la fase 2 los lee, es en memoria y solo extrae metadatos.
3. Añadir como hallazgo de primera clase "transcripciones del agente con posibles secretos en texto plano" (existen, ubicación, antigüedad frente a `cleanupPeriodDays`, ACL), como ubicación sensible bajo la misma regla opt-in.
4. Dejar explícito que opencode puede leer `.claude/` (skills, CLAUDE.md): el segundo adaptador no es independiente del primero en este entorno.
5. Pendiente del PRD, derivado de esta investigación: cómo representar lo "declarado pero no necesariamente efectivo" (reglas sin confianza de espacio de trabajo, política de servidor invisible).

---

## 6. Decisiones que se desprenden para Alex

1. **¿Qué significa "protegido" en Windows nativo?** Confirmar que el reporte dirá "protegido por política del agente, no barrera del SO", sin nunca decir "no alcanzable". (Ya decidido en parte; aquí se reafirma con fuente oficial.)
2. **¿Se declara "comprobado" solo lo legible por el SO, o también la postura del agente?** Recomendación: dos campos separados.
3. **¿Fase 3 incluye instalar hooks?** Rompería "solo lectura" del MVP. Opciones: (a) AgentReach solo genera el texto del hook o regla sugerida y el usuario lo aplica; (b) AgentReach lo instala con confirmación explícita. Recomendación: (a) primero.
4. **¿Hay que recomendar WSL2 para quien quiera sandbox?** En Windows nativo no hay sandbox en Claude Code. Es una recomendación de producto (y un posible hallazgo "sandbox no disponible en esta plataforma").
5. **¿Cuándo se lee el historial?** Las transcripciones tienen secretos; decidir si la fase 2 las lee por defecto o solo con opt-in, y si se acepta un analizador que lea el archivo completo en memoria.
6. **¿Segundo adaptador?** Alex usa opencode en otro PC; su control es más débil y menos documentado. Decidir si se acepta un adaptador opencode con capacidad "auditar y advertir" y varias lagunas, o se espera a verificar en un PC con opencode (rutas Windows, comportamiento de `deny` y de compartir sesiones).
7. **Visual Studio:** ¿cómo accede el agente desde Visual Studio (extensión, terminal integrada)? No se investigó y afecta qué configuración aplica.
8. **Dev-Alex:** agente personal sin investigar; hace falta decidir si entra en el alcance del primer ciclo y, si sí, de dónde sale su documentación.

---

## 7. Fuentes consultadas

Primarias, Claude Code (documentación oficial):
- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/permissions
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/sandboxing
- https://code.claude.com/docs/en/managed-settings
- https://code.claude.com/docs/en/managed-mcp
- https://code.claude.com/docs/en/mcp
- https://code.claude.com/docs/en/claude-directory
- https://code.claude.com/docs/en/env-vars
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/monitoring-usage

Primarias, opencode:
- https://opencode.ai/docs/config/
- https://opencode.ai/docs/permissions/
- https://opencode.ai/docs/plugins/
- https://opencode.ai/docs/agents/
- https://opencode.ai/docs/skills/
- https://opencode.ai/docs/rules/
- https://opencode.ai/docs/mcp-servers/
- https://opencode.ai/docs/tools/
- https://opencode.ai/docs/troubleshooting/
- https://opencode.ai/docs/enterprise/
- https://opencode.ai/docs/windows-wsl/
- https://github.com/anomalyco/opencode/issues/42979 (reporte de usuario en el repositorio oficial)

Intentada sin éxito: https://opencode.ai/docs/share/ (404).

Terceros (solo apoyo, no verificados):
- `[TERCERO]` https://developers.intility.com/docs/external/inference/opencode-permissions/ (afirma evasión de `read: deny` vía bash)
