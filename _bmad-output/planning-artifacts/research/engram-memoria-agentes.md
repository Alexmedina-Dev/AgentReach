# Engram: memoria persistente para agentes de código (investigación de solo lectura)

Fecha: 2026-11-09. Fuente: repo Gentleman-Programming/engram (rama main, archivos leídos vía raw.githubusercontent.com y API de releases). No se instaló ni ejecutó nada. Lo no leído se marca "no verificado". Nota: las páginas fueron resumidas por un modelo intermedio (WebFetch), no leídas literalmente; conviene confirmar los puntos críticos en la fuente.

## 1. SECURITY.md
- Solo el último release estable recibe parches. Reporte privado por GitHub Security Advisories; acuse en 48 h, evaluación en 5 días hábiles, meta de 30 días para críticos.
- Amenazas en alcance: escalada de privilegios, corrupción de datos, path traversal (escribir fuera de la carpeta prevista), inyección por entradas del MCP o del API HTTP, fugas de datos sensibles por memoria.
- Fuera de alcance: acceso físico o atacante que ya tiene tu carpeta de usuario. Ejemplo: si un malware ya lee tu carpeta personal, Engram no lo considera su problema.
- No habla de autenticación ni de escucha en localhost (eso está en DOCS.md). Incluye reglas para mantenedores (2FA en npm, publicación con OIDC).

## 2. Instalación en Windows (docs/INSTALLATION.md)
- A: `go install github.com/Gentleman-Programming/engram/v3/cmd/engram@latest` (requiere Go 1.26+; deja engram.exe en `%USERPROFILE%\go\bin`). B: compilar desde el código. C: bajar `engram_<versión>_windows_amd64.zip` de GitHub Releases.
- Los binarios de Windows NO están firmados y pueden disparar el antivirus (lo dice el doc). El doc no explica verificación. La API de releases muestra un `checksums.txt` (suma SHA-256 de cada archivo, para comprobar que la descarga no fue alterada) y ningún archivo de firma (.sig/.asc). Ejemplo: tras bajar el zip, calcular su hash y compararlo con checksums.txt. Quien lo descargue del mismo sitio no gana protección contra un release comprometido.
- Versión estable actual: v3.7.0, publicada 2026-11-07.
- Variables: `ENGRAM_DATA_DIR`, `ENGRAM_PORT` (7437), `ENGRAM_SOCKET` (solo POSIX), `ENGRAM_PROJECT`, `ENGRAM_HTTP_TOKEN`, `ENGRAM_NO_UPDATE_CHECK`, y varias `ENGRAM_CLOUD_*`.

## 3. Qué hace `engram setup <agente>` (docs/AGENT-SETUP.md y docs/PLUGINS.md)
**Claude Code** (`setup claude-code`; exige `jq` y `curl`):
- Instala/actualiza un plugin del marketplace en alcance de usuario (trae hooks, scripts y una skill de "protocolo de memoria").
- Entrada MCP en `~/.claude.json` (la escribe el CLI de Claude): `mcpServers.engram`, comando `<ruta-absoluta-engram> mcp --tools=agent`, transporte stdio.
- Hooks del plugin (hooks/hooks.json): PreToolUse (`engram hook claude-pre-tool-use`, vincula la sesión y bloquea herramientas de escritura de Engram si no se confirma), SessionStart (inyecta contexto), UserPromptSubmit (recordatorios; en Windows script `.ps1`), SubagentStop (captura pasiva), SessionEnd.
- Permisos: por defecto el doc dice que solo registra MCP y pregunta si añadir permisos (no describe qué lista exacta). Con `--allow-memory-writes` añade a `~/.claude/settings.json` en `permissions.allow` 12 herramientas (mem_save, mem_update, mem_review, mem_save_prompt, mem_pin, mem_unpin, mem_session_summary, mem_session_start, mem_session_end, mem_capture_passive, mem_judge, mem_compare) con los prefijos `mcp__engram__` y `mcp__plugin_engram_engram__`. Sin comodines, sin mem_delete ni mem_merge_projects. Esas entradas saltan los avisos de permiso. Cuidado: con el aviso interactivo puede quedar abierto sin que Alex lo note (no verificado qué añade exactamente).
- Captura de prompts: el hook guarda el texto de tus mensajes (salvo los que empiezan con etiquetas del sistema). En Git Bash/MSYS2 en Windows "safe mode" se omite.

**opencode** (`setup opencode`): plugin `~/.config/opencode/plugins/engram.ts` (en Windows el directorio es `%APPDATA%\opencode\` según INSTALLATION.md; hay inconsistencia entre docs, no verificado cuál prevalece); entrada `mcp.engram` (o `mcp.servers.engram`) con `--tools=agent` en `opencode.json(c)`; añade `opencode-subagent-statusline` a `tui.json(c)`. Permisos: no mencionados.

**Cursor**: `mcpServers.engram` en `~/.cursor/mcp.json` y archivo informativo `~/.cursor/engram-memory-protocol.md`. **VS Code/Copilot**: entrada `servers.engram` (stdio) en `%APPDATA%\Code\User\mcp.json` y `prompts\engram.instructions.md` con `applyTo: "**"` (esa instrucción se aplica a todos los archivos). Sin hooks documentados.

## 4. Qué guarda y filtros de secretos
- Base SQLite `~/.engram/engram.db` (Windows `%USERPROFILE%\.engram`, o `ENGRAM_DATA_DIR`, absoluta; rechaza NFS/SMB). Guarda sesiones, observaciones (título, contenido, tipo, herramienta, proyecto), prompts del usuario, relaciones y colas de sincronización.
- Filtro: SOLO elimina el texto marcado manualmente con `<private>...</private>` (queda `[REDACTED]`), en el plugin y en el almacén. Ejemplo: "clave `<private>sk-abc</private>`" se guarda sin la clave. No hay detección automática de secretos (el doc dice "content is redacted before the storage limit" pero solo describe las etiquetas). Si pegas una clave sin etiqueta, se guarda. Pi redacta y trunca prompts; para otros agentes no se describe.
- Permisos del archivo: NO verificado (no documentados). En Windows hereda las ACL de tu carpeta de usuario.

## 5. API HTTP local
- `engram serve`: `127.0.0.1:7437` por defecto (DOCS.md). ARCHITECTURE.md no menciona la dirección. `ENGRAM_PORT` lo cambia.
- Autenticación opcional: `ENGRAM_HTTP_TOKEN` protege solo DELETE de sesiones/observaciones/prompts, `GET /export` y `POST /import`; las demás rutas (incluidas lecturas y escrituras de memorias) quedan abiertas si no hay token. El doc admite que escuchar en loopback no autentica: cualquier proceso local (o una página web mediante peticiones al localhost, riesgo no analizado en la fuente) podría consultar. Ejemplo: otro programa tuyo puede leer tus memorias en `http://127.0.0.1:7437`. Nota: el servidor HTTP no se necesita para MCP (usa stdio), pero los hooks de Claude lo llaman.

## 6. Cloud y Git Sync
- Por defecto todo es local: "Local SQLite is authoritative; cloud is optional" y solo sincronizan proyectos inscritos (`engram cloud enroll`) con autosync activado por `ENGRAM_CLOUD_AUTOSYNC=1` (confirmado en DOCS.md).
- Git Sync (`engram sync`): exporta memorias a `.engram/` en el repo (sin prompts salvo `--include-prompts`). Advierte que puede haber secretos y que lo subido queda en el historial de Git.
- Cloud: servidor propio (`engram cloud serve`, Postgres, Docker Compose), token + JWT secret; el sync SÍ incluye prompts. Un servicio alojado por Engram: no aparece en lo leído (no verificado). Hay modo `ENGRAM_CLOUD_INSECURE_NO_AUTH=1` solo para desarrollo.

## 7. Telemetría
- No se encontró telemetría en lo leído. Única comunicación saliente descrita: comprobación de actualizaciones contra GitHub, desactivable con `ENGRAM_NO_UPDATE_CHECK=1`. Parte de DOCS.md (últimos ~14k caracteres y secciones truncadas) no leída: no verificado del todo.

## 8. Riesgos para el equipo (Claude Code, opencode, Cursor, VS Code+Copilot) y recomendación
Riesgos: (a) memoria persistente = vector de inyección: un texto malicioso guardado hoy puede influir al agente mañana en todos los proyectos; (b) secretos sin etiquetar quedan en texto plano en el disco; (c) hooks y plugin con ejecución de scripts en cada prompt; (d) permisos auto-aprobados de escritura con `--allow-memory-writes`; (e) API local sin auth en lecturas; (f) binario sin firmar y sin verificación documentada; (g) Git Sync/Cloud pueden publicar memorias con secretos; (h) una sola base compartida entre 4 agentes mezcla contexto de proyectos distintos.
Recomendación: usarlo solo como piloto por persona, no como estándar del equipo todavía. Configuración mínima: instalar por `go install` con versión fija (v3.7.0) o zip con hash comprobado contra checksums.txt; `ENGRAM_NO_UPDATE_CHECK=1`; NO usar `--allow-memory-writes`; no activar Cloud ni Git Sync; definir `ENGRAM_HTTP_TOKEN` o no ejecutar `engram serve`; no usar `<private>` como única defensa (no pegar secretos en chats); `ENGRAM_PROJECT` por repo; revisar `~/.engram` y `.engram/` antes de cualquier commit.

## 9. Señales para AgentReach (solo lectura de archivos) y confianza máxima
| Señal | Dónde | Confianza máx. |
|---|---|---|
| Base de datos | `%USERPROFILE%\.engram\engram.db` (o ruta de `ENGRAM_DATA_DIR`) | Alta: existencia = Engram se ha usado; no prueba que siga activo |
| Entrada MCP Claude Code | `~/.claude.json` → `mcpServers.engram` (comando termina en engram, args `mcp`) | Alta |
| Plugin y hooks Claude | plugin `engram` en la config de plugins de Claude; comando `engram hook claude-pre-tool-use` en hooks | Alta si aparece el comando; Media si solo el nombre del plugin (ubicación exacta no verificada) |
| Permisos abiertos | `~/.claude/settings.json` → `permissions.allow` con `mcp__engram__*mem_*` o `mcp__plugin_engram_engram__*` | Alta |
| opencode | `~/.config/opencode/plugins/engram.ts` o `%APPDATA%\opencode\...`; `mcp.engram` en opencode.json(c); `tui.json` con opencode-subagent-statusline (señal débil, es otro paquete) | Alta para plugin y MCP; Baja para statusline |
| Cursor | `~/.cursor/mcp.json` → `mcpServers.engram`; `~/.cursor/engram-memory-protocol.md` | Alta / Media (el .md puede copiarse a mano) |
| VS Code | `%APPDATA%\Code\User\mcp.json` → `servers.engram`; `prompts\engram.instructions.md`; `.vscode/mcp.json` por proyecto | Alta |
| Carpeta del repo | `.engram/` (Git Sync) | Media-alta: indica memorias posiblemente versionadas |
| Variables de entorno | `ENGRAM_DATA_DIR`, `ENGRAM_HTTP_TOKEN`, `ENGRAM_CLOUD_*` en `env` de configs MCP o archivos de perfil | Media: leer solo configs, no el entorno vivo; no guardar valores de tokens, solo su presencia |
| Binario | `engram.exe` en `%USERPROFILE%\go\bin` o carpeta PATH | Media (no se ejecuta; solo existencia) |
Regla: reportar presencia, nunca contenidos de la base ni valores de tokens. Rutas de Windows para opencode y de plugins de Claude: no verificado en un equipo real.
