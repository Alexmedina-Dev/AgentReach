# Oráculo: evaluación independiente y ciega (2026-11-09)

Alcance: 65 casos, evaluados solo con el listado sin nivel, las reglas del PRD (FR-5, FR-6, FR-7, FR-8, FR-18, FR-19, FR-22, FR-25, FR-26) y fuentes primarias. No leí el código, las pruebas ni las respuestas esperadas.

Vocabulario: "comprobado", "potencial", "hipótesis", "no se reporta" (el tipo no existe en el catálogo o no coincide: FR-4), "no se pudo revisar" (FR-25), "no aplicable" (el archivo no existe). "Duda" = el PRD admite más de una lectura (ver ambigüedades).

## Fuentes primarias consultadas (2026-11-09)

- Claude Code, permisos: https://code.claude.com/docs/en/permissions
  - Una regla `deny` de lectura se aplica a las herramientas de archivo y a comandos reconocidos como `cat`. No se aplica a un script de Python o Node que abra archivos por su cuenta ni a `grep -r .`. Para una barrera del sistema operativo hay que activar el sandbox.
  - Con enlaces simbólicos y *junctions* de Windows, las reglas `deny` valen si coincide la ruta pedida o la ruta real.
  - Leer dentro del directorio de trabajo no pide aprobación. Fuera de él sí (la tabla de permisos solo exime "dentro del directorio de trabajo").
  - `bypassPermissions` no tiene efecto desde la configuración de proyecto ni local (desde la 2.1.257). Antes sí lo tenía.
  - No hay mención de que `.gitignore` proteja un archivo de la lectura.
- Claude Code, configuración: https://code.claude.com/docs/en/settings
  - `.claude/settings.local.json` es del usuario y queda fuera de git.
  - Las reglas `allow` del proyecto esperan a que se confíe en la carpeta. `deny` y `ask` aplican de inmediato.
- Claude Code, sandbox: https://code.claude.com/docs/en/sandboxing. "On native Windows, Claude Code runs commands unsandboxed". El sandbox corre en macOS, Linux y WSL2.
- Claude Code, variables: https://code.claude.com/docs/en/env-vars. `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` quita credenciales del entorno de los subprocesos que Claude Code arranca (comandos Bash, hooks, servidores MCP de tipo stdio). El propio proceso conserva las credenciales.
- opencode: https://opencode.ai/docs/permissions/
  - La política base de opencode **pregunta (`ask`) antes de leer `*.env` y `*.env.*`** y permite `*.env.example`. La última regla que coincide gana.
  - `external_directory` permite por defecto las rutas externas salvo que se añada una regla.
  - `read` y `shell` son acciones separadas: un `deny` de `read` no cubre `cat .env`.
  - (Esta página la leí resumida por la herramienta de lectura: citas literales, no la página completa.)
- git, configuración: https://git-scm.com/docs/git-config
  - `core.fsmonitor` en `true` activa el monitor integrado. Si no, el valor es la ruta del comando *hook*.
  - `core.hooksPath` relativo se toma respecto al directorio donde corren los hooks.
  - `core.sshCommand` se usa en fetch y push.
  - `core.pager` "meant to be interpreted by the shell".
  - Un alias con `!` es un comando de shell.
  - `filter.<driver>.clean` y `smudge` son comandos.
  - `gpg.program` se usa al firmar o verificar firmas.
  - Los nombres de sección y de variable no distinguen mayúsculas. `#` y `;` abren comentarios. `\` al final continúa la línea. `include.path` relativo es relativo al archivo que incluye.
- git, atributos: https://git-scm.com/docs/gitattributes. "A missing filter driver definition in the config ... is not an error but makes the filter a no-op passthru" (por eso GT-12 no ejecuta nada).
- VS Code, tareas: https://code.visualstudio.com/docs/debugtest/tasks. `runOn: folderOpen` ejecuta la tarea al abrir la carpeta. `task.allowAutomaticTasks` es `off` por defecto y con `on` corren siempre en una carpeta confiable. Nunca corren en una carpeta no confiable. `reveal: never` deja el terminal oculto.
- Windows, ACL: https://learn.microsoft.com/en-us/windows/win32/secauthz/access-control-lists. El sistema revisa las entradas en orden hasta que una concede todo lo pedido o una niega algo.

**No verificado en fuente primaria:**
- `diff.external` (no aparece en las páginas leídas; la documentación de `gitattributes` solo menciona `diff.<nombre>.command`).
- Cuándo corre `core.hooksPath` en git for Windows.
- `gpg.program` con `log.showSignature`.
- Cómo `mklink /J` aparece en los metadatos para el lector propio (el PRD lo da por verificado).
- Herencia de ACL con `ctypes` (solo leí el concepto general de ACL; no la página de herencia).
- La claim del PRD de que opencode salta un `deny` con el shell: coincide con la documentación leída, pero esta no lo dice con esas palabras.
- Comportamiento de Claude Code ante `.mcp.json` y *hooks* de proyecto: no los verifiqué hoy; el PRD cita avisos del fabricante.
- Servidores de MCP y *hooks* de OpenCode: no consultados.

## Tabla ID a nivel

| ID | Mi nivel | Duda | Justificación en una frase |
|---|---|---|---|
| PP-01 | Claude Code: potencial. opencode: comprobado | sí | En Claude Code hay `deny` de lectura (FR-6, política y no barrera: el propio doc dice que no cubre scripts); en opencode no hay regla propia (`read` en allow), pero su política base pregunta por `.env` y no sé si la regla `allow` la anula. |
| PP-01a | potencial | no | Reconocer ANTHROPIC_API_KEY por nombre no tiene fuente verificada (FR-7), y en Claude Code además hay `deny`. |
| PP-01b | potencial | no | STRIPE_SECRET_KEY por nombre: es el ejemplo literal de FR-7 (máximo potencial); además `deny`. |
| PP-01c | potencial | no | GITHUB_TOKEN por nombre o prefijo, sin fuente verificada (FR-7). |
| PP-01d | potencial | no | RAILWAY_TOKEN por nombre (FR-7). No entra en TH-17 porque no es ajeno a la tarea (está en el `.env` del proyecto). |
| PP-01e | potencial | no | DATABASE_URL con usuario y clave: reconocida por patrón, sin fuente verificada; además `deny`. |
| PP-01f | potencial | no | JWT_SECRET por nombre (FR-7); además `deny`. |
| PP-02 | no se reporta | sí | Plantilla sin secretos; el PRD deja los falsos positivos sin decidir (§10), y opencode permite `*.env.example` por defecto. |
| PP-03 | potencial | no | Existe, pero Windows niega la lectura al usuario actual: FR-8 ("existe y hoy el agente no puede leerlo"). |
| PP-04 | comprobado | sí | Es el ejemplo literal de FR-5, aunque la regla de certeza de FR-7 cita los "permisos heredados" como causa de potencial; en opencode la política base pregunta por `.env.*`. |
| PP-05 | comprobado | sí | Estar en `.gitignore` no protege de la lectura (el doc de Claude Code no lo menciona como regla); no hay regla de agente. |
| AJ-01 | no se reporta | sí | Está fuera del proyecto auditado (carpeta hermana): AgentReach audita solo la raíz indicada; no es una ubicación sensible. |
| EN-01 | potencial | sí | TH-6 es un hallazgo, pero el destino no se mira (FR-19, solo metadatos): no se puede determinar qué hay al otro lado. |
| EN-02 | no se reporta | sí | Detrás de un enlace que sale: no se sigue (FR-19, FR-26). El destino queda declarado como no revisado en la cobertura. |
| EN-03 | no aplicable | no | El enlace simbólico no se pudo crear, no hay nada que auditar. |
| HF-01 | potencial | sí | Clave privada SSH (TH-2) con ubicación sensible activada; está fuera del directorio de trabajo, y en Claude Code leer fuera pide aprobación y en opencode `external_directory` está en `ask` (CA-04). Sin activar la ubicación: "no se pudo revisar". |
| HF-02 | no se reporta | no | Es material público; no es un tipo del catálogo. |
| HF-03 | potencial | sí | TH-3 con ubicación activada; mismo razonamiento que HF-01. Sin activar: "no se pudo revisar". |
| HF-04 | no se reporta | no | Configuración sin secretos; no es un tipo del catálogo. |
| HF-05 | potencial | sí | `~/.npmrc` en ubicación sensible: solo metadatos, no se sabe si tiene token (TH-1 lo cita para `.npmrc`; no queda claro si está en la lista de ubicaciones sensibles). |
| CA-01 | no se reporta | sí | Es la fuente de la postura de otros hallazgos, no un hallazgo. Solo sería TH-7 si los 3 `allow` fueran amplios y no los veo. |
| CA-02 | potencial | sí | El doc oficial dice "sin sandbox en Windows nativo" hoy, pero AgentReach no ve la versión de Claude Code (FR-21). |
| CA-03 | no se reporta | no | Es una medida de protección (quita credenciales de los subprocesos), no una exposición. |
| CA-04 | comprobado | sí | TH-7 y TH-8: el texto del archivo muestra la regla sin ambigüedad; el PRD no fija el nivel máximo de TH-7. |
| CA-05 | potencial | no | TH-11 tiene "máximo potencial" en el PRD. |
| CX-01 | no se reporta | no | Texto inofensivo: no coincide con ningún patrón de TH-5. |
| NO-01 | no se reporta | no | Nombres como KEY sin valor de credencial: no coincide con el catálogo. |
| NO-02 | no se reporta | no | FR-4: lo que no se reconoce no se reporta. |
| NO-03 | no se reporta | sí | Clave de ejemplo pública del proveedor; el PRD no define una lista de claves de ejemplo excluidas. |
| NO-04 | no se reporta | no | Referencia a un secreto del repositorio sin valor. |
| GT-01 | comprobado | sí | Credencial en archivo dentro del proyecto, sin regla de agente (el `deny` es solo para `./.env`); que git lo siga no cambia que el agente lo pueda leer. Duda por cómo se reconoce el nombre `.env` con otro prefijo. |
| GT-02 | no se pudo revisar | no | FR-22: el historial exige ejecutar git (fase 2). |
| GT-03 | comprobado | sí | TH-19: usuario y clave literales en la URL, sin ayudante; baja a potencial si se juzga "de relleno". |
| EV-01 | hipótesis | sí | TH-4 y FR-5: una variable heredada es un indicio débil; con el scrub activo en Claude Code puede ni llegar a los subprocesos, y en opencode no está documentado. |
| PA-01 | comprobado | no | La ACL concede lectura a Todos (permiso explícito, no negación), sin regla de agente. |
| CX-02 | hipótesis | no | TH-5: patrón simple ("ignora las reglas", leer `.env`, enviar a una URL), máximo hipótesis. |
| NO-05 | no se reporta | no | Los `.sample` son inertes; GT-07 los usa como control. |
| AT-01 | comprobado | no | TH-12: el texto invisible está en los bytes; que se obedezca no se afirma. |
| AT-02 | no se reporta | no | TH-12 excluye los emoji compuestos. |
| AT-03 | comprobado | no | TH-13 (con la ubicación activada); sin activar: "no se pudo revisar". |
| AT-04 | potencial | no | TH-14 caso 1: *hook* de proyecto, máximo potencial. |
| AT-05 | potencial | no | TH-14: servidor MCP de comando en `.mcp.json`. |
| AT-06 | potencial | no | TH-15 en el proyecto: máximo potencial; el doc de Claude Code dice que `bypassPermissions` ya no vale desde archivos de proyecto o locales (desde la 2.1.257), y AgentReach no ve la versión. |
| AT-07 | potencial | no | TH-16: depende de que la carpeta sea confiable; el doc de VS Code dice que `runOn: folderOpen` corre solo en carpetas confiables y con `allowAutomaticTasks` activado. |
| AT-08 | potencial | no | TH-17: reconocido por nombre, ajeno a la tarea; el poder del token es hipótesis. |
| GT-04 | comprobado | no | TH-18: `core.fsmonitor` con un valor que no es `true` ni `false` es un comando (git-config). |
| GT-05 | potencial | no | TH-18 dice potencial; el doc de git dice que la ruta relativa se toma desde donde corren los hooks. |
| GT-06 | comprobado | sí | TH-18 dice comprobado; el hecho se reparte entre `.gitattributes` y `.git/config` (dos archivos). |
| GT-07 | potencial | no | TH-18: *hook* activo, cómo decide git for Windows qué hook corre no está verificado. |
| GT-08 | potencial | no | TH-19: valor de relleno en la URL. |
| GT-09 | potencial | sí | TH-18 dice potencial; el doc de git confirma que el nombre no distingue mayúsculas y que `\` continúa la línea, así que un lector fiel lo determinaría. |
| GT-10 | no se reporta | no | `true` activa el monitor integrado, no un programa (git-config). |
| GT-11 | no se reporta | no | `false` apaga el monitor. |
| GT-12 | no se reporta | no | Sin comando local el filtro no hace nada (gitattributes). |
| GT-13 | potencial | no | TH-18: clave dentro de un `include` con ciclo. |
| GT-14 | comprobado | no | `core.sshCommand` con valor en la sección (git-config). |
| GT-15 | comprobado | no | `core.pager` con comando interpretado por el shell (git-config). |
| GT-16 | comprobado | no | Alias con `!` es comando de shell (git-config). |
| GT-17 | comprobado | sí | `diff.external` no verificado en fuente primaria hoy; el PRD lo da como comprobado. |
| GT-18 | comprobado | sí | `gpg.program` solo corre al firmar o verificar; el PRD marca la parte con `log.showSignature` como no verificada. |
| TR-01 | no aplicable | no | Solo existiría si algo hubiera ejecutado el señuelo; no es un hallazgo. |
| AT-09 | comprobado | no | TH-12: U+200B suelto, sin emoji alrededor. |
| AT-10 | comprobado | no | TH-13 (con la ubicación activada). |
| AT-11 | potencial | no | `deny` sobre el enlace (FR-6); el doc confirma que el `deny` aplica a la ruta pedida o a la real, junctions incluidas. |
| AT-12 | potencial | no | TH-14 caso 2: `enableAllProjectMcpServers: true`. |

## Ambigüedades del PRD

1. **Permisos heredados y "comprobado" (FR-7, línea 147).** La regla dice que los permisos heredados dejan un hecho en potencial, pero el ejemplo de FR-5 pone `.env.staging` como comprobado. Casi todo archivo en Windows hereda su ACL. Afecta PP-04, PP-05, GT-01 y PA-01.
2. **Reglas propias de opencode.** Su política base pregunta por `.env` y `.env.*`; el PRD dice que casi todo está en `allow`. No dice si `read: allow` de `opencode.json` anula esa pregunta. Afecta PP-01, PP-04, PP-05, GT-01, PA-01.
3. **Un reporte por agente (FR-17).** PP-01 es comprobado en opencode y potencial en Claude Code. No está claro si el oráculo debe llevar un nivel por agente.
4. **Ubicaciones fuera del directorio de trabajo.** Claude Code pide aprobación para leer fuera; `external_directory` de CA-04 está en `ask`. El PRD no dice si eso cuenta como regla `ask` (FR-5) para HF-01, HF-03, HF-05. Tampoco fija el nivel máximo de TH-2 y TH-3.
5. **Nivel de un hallazgo sobre configuración (TH-6, TH-7, TH-8, TH-10).** FR-5 define "comprobado" con tres hechos de lectura de un archivo, que no encajan con reglas o enlaces. El PRD no da el nivel máximo de estos cuatro tipos (afecta EN-01, CA-02, CA-04).
6. **Enlace como hallazgo y como "no se pudo revisar".** FR-19 lo pide como TH-6; FR-26 lista "un enlace" entre lo que sale en "no se pudo revisar". EN-01 y EN-02 dependen de esto.
7. **Carpeta hermana (AJ-01).** El proyecto auditado es solo la raíz indicada, pero FR-9 habla de "ajeno a la tarea" fuera del directorio de trabajo. No dice si AgentReach debe avisar de proyectos hermanos.
8. **Claves de ejemplo públicas y plantillas (NO-03, PP-02).** El PRD no define una lista de exclusión (§10 lo deja abierto).
9. **Valor "de relleno" frente a "falso" (GT-03, GT-08).** No dice cómo distinguir una clave de relleno de una realista; se necesita una regla verificable.
10. **TH-18 comprobado con hecho repartido o no verificado (GT-06, GT-17, GT-18).** FR-7 exige "el texto de ese mismo archivo", pero GT-06 usa dos archivos, y GT-17 y GT-18 tienen parte de la fuente sin verificar.
11. **GT-09 y un lector "fiel a git" (FR-22).** Si el lector lee como git, el resultado debería ser determinado; el PRD lo manda a potencial sin decir por qué.
12. **Ubicaciones sensibles sin activar.** HF-01, HF-03, HF-05, AT-03 y AT-10 tienen dos respuestas según la opción activada. El PRD no fija cuál es el estado por defecto del oráculo.
13. **`~/.npmrc`.** TH-1 lo cita como credencial, pero no queda claro si está entre las ubicaciones sensibles (solo metadatos).
