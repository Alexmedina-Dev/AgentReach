# Verificación preguntas 25 y 26 (fuentes primarias)

Investigación de solo lectura. Fecha de consulta: 2026-11-09.

---

## PREGUNTA 25 — opencode: ¿una regla `read: allow` global anula el `ask` base para `.env`?

**Respuesta corta: sí, lo anula.** Una regla amplia (`"*"` → `allow`) colocada después de la política base, ya sea en el `opencode.json` global o en el del proyecto, gana sobre el `ask` por defecto de `*.env` / `*.env.*`, porque opencode no evalúa "la regla más específica gana", evalúa "la última regla que coincide (en el orden en que se cargan los archivos) gana".

### 1. Política base por defecto (todo agente la trae incorporada)
Fuente primaria: `https://opencode.ai/docs/permissions.md` (consultado 2026-11-09), que cita el archivo fuente `packages/opencode/src/agent/agent.ts` (no se pudo abrir el archivo .ts directamente en GitHub — devolvió 404 tanto en `sst/opencode` como en `anomalyco/opencode`, posiblemente por reorganización de ramas/paquetes; esto queda **no verificado** contra el código .ts en sí, solo contra la doc oficial que lo cita).

```jsonc
{ "action": "*",    "resource": "*",           "effect": "allow" },
{ "action": "read", "resource": "*.env",       "effect": "ask"   },
{ "action": "read", "resource": "*.env.*",     "effect": "ask"   },
{ "action": "read", "resource": "*.env.example","effect": "allow" }
```

Ejemplo: sin ninguna configuración extra, si el agente intenta leer `.env` o `config.env.local`, opencode pregunta (`ask`); si intenta leer `.env.example`, lo permite directo porque esa regla "allow" viene después en la lista y por eso gana sobre el `*` inicial.

### 2. Orden de evaluación
Cita textual de la doc: *"OpenCode combines rules in order and uses the last match."* Y sobre la carga de configuraciones: *"Lower-priority configuration is loaded first, global rules are appended next, and agent rules are appended last."* Si ninguna regla coincide, el valor por defecto es `ask`. Para operaciones que tocan varios recursos a la vez: cualquier `deny` bloquea todo; si no hay deny, cualquier `ask` dispara la pregunta; si no hay ninguno de los dos, se permite.

Ejemplo de orden real: base (allow `*`, ask `.env`, ask `.env.*`, allow `.env.example`) → luego se agregan las reglas del `opencode.json` global → luego las reglas de nivel de agente (las del agente especificado en el .json del proyecto o global, según cuál agente esté corriendo). Una regla de proyecto `{"action":"read","resource":"*","effect":"allow"}` puesta en el arreglo de permisos del agente, al estar al final, coincide con `.env` (porque `*` matchea todo) y por ir después, gana sobre el `ask` base de `.env`.

### 3. Reglas globales frente a las del proyecto
Cita: *"Global and Console-managed policies override project configuration, which is how an organization blocks a command that a repository would allow."* Esto aplica a **policies** (un mecanismo aparte, de "hard-deny" que corre después de evaluar las reglas normales y solo puede denegar, nunca conceder). Para las reglas normales de permisos (`permission`/`permissions`), la doc no dice que lo global siempre gane sobre el proyecto en términos de "quién se carga primero": dice que lo global se agrega después de "la configuración de menor prioridad" (que normalmente es el proyecto) y lo de agente se agrega al final de todo. Es decir, para reglas normales, el orden terminal es: proyecto → global → agente, y gana la última que coincida en ese orden — no hay una jerarquía de "proyecto no puede nunca ganarle a global", salvo que exista una `policy` explícita de la organización, que sí es inapelable y solo deniega.

Ejemplo: si el proyecto tiene `allow` amplio para `read:*` y el global no toca el tema `.env`, gana el allow del proyecto (porque va antes que las reglas de agente pero después de la base, y nada posterior lo contradice). Si, en cambio, existe una `policy` de consola/organización que diga "`.env` siempre `deny`", esa policy corre después y gana sin importar lo anterior, porque las policies solo pueden denegar, nunca permitir de más.

### 4. `shell` frente a `bash`
Cita textual: *"In V2, use `permissions`, `shell`, and `subagent` instead of `permission`, `bash`, and `task`."* O sea: `bash` es el nombre de la clave en la sintaxis V1 (`permission.bash`); `shell` es el nombre equivalente en V2 (`permissions.shell`). Se refieren a la misma acción (ejecutar comandos de shell), con nombre distinto según la versión del esquema de config. Ejemplo: en V1 se escribe `"permission": {"bash": "ask"}`; en V2 el equivalente es `{"action":"shell","resource":"*","effect":"ask"}` dentro de `permissions`.

### 5. Qué nivel debería dar AgentReach en cada combinación

| Combinación | Nivel recomendado | Por qué |
|---|---|---|
| Config base, sin tocar nada | Dejar el default (`ask` en `.env`/`.env.*`) | Ya protege por defecto; no hay motivo para bajar la guardia. |
| Proyecto con `read: allow (*)` sin matizar | **No usar así.** Si se necesita un allow amplio para lectura (por velocidad), agregar **después** una regla específica `ask` o `deny` para `*.env` y `*.env.*`, igual que hace el ejemplo oficial ("the specific exceptions follow the broad rule"). | Porque la última regla que matchea gana; un allow amplio sin excepción posterior anula la protección de `.env`. |
| Global con `read: allow (*)` | Igual que el caso anterior: agregar excepción de `.env` después, a nivel global, para que aplique a todos los proyectos. | El global se agrega después del proyecto pero antes del agente; si el proyecto no tiene excepción, el allow global la sobrescribe igual. |
| Se requiere blindaje "no negociable" para `.env` en todos los proyectos/agentes de AgentReach | Usar una **policy** de organización/consola que deniegue lectura de `*.env`/`*.env.*`, no solo una regla de `permissions`. | Las policies corren después de las reglas normales y solo pueden denegar — es el único mecanismo que ninguna config de proyecto puede destrabar. |
| `shell`/`bash` (ejecución de comandos) | Mantener en `ask` o `deny` por defecto, igual criterio que `.env`: si hay un allow amplio de `shell`, no hay forma de matizarlo por archivo como con `.env` (no aplica "resource" de archivo), así que conviene dejarlo en `ask` explícito en vez de depender del allow general. | Evita que un allow de lectura "arrastre" sin querer la ejecución de comandos, ya que son acciones distintas (`read` vs `shell`), pero conviene no mezclar un `*` de acción con efecto allow que cubra ambas. |

No verificado directamente en el archivo fuente `.ts` (solo en la documentación oficial que lo cita): el nombre exacto de la variable/constante dentro de `agent.ts` y el rango de líneas 46-57 citado por una guía de terceros (`learnopencode.com`), que no es fuente primaria de opencode.

**Fuentes:**
- https://opencode.ai/docs/permissions (consultado 2026-11-09)
- https://opencode.ai/docs/permissions.md (consultado 2026-11-09)
- https://opencode.ai/v2/permissions.md (consultado 2026-11-09)
- https://learnopencode.com/en/5-advanced/05-permissions (fuente secundaria, no oficial — citada solo como referencia cruzada, marcada no verificada contra el .ts real)

---

## PREGUNTA 26 — git: cuándo corren `diff.external`, `gpg.program` y otras claves, en comandos de solo lectura

1. `diff.external` (fuente: `git-scm.com/docs/git-config`, sección `diff.external`, consultado 2026-11-09): *"If this config variable is set, diff generation is not performed using the internal diff machinery, but using the given command."* Solo corre cuando Git realmente **genera un diff** mostrando contenido (`git diff`, `git show` de un commit con cambios, `git log -p`/`-u`/`--stat` con contenido). Para `git log` y comandos "amigos" la doc de `--ext-diff` dice explícitamente: *"If you set an external diff driver with gitattributes, you need to use this option with git-log and friends"* — es decir, en `git log -p` el driver por atributos (`gitattributes`) NO corre automáticamente, requiere `--ext-diff` explícito. `git status` no genera diff de contenido por defecto (ni siquiera con `-v`, que solo imita el formato de `git diff --cached` pero no lo dice que invoque el driver externo) y no se menciona que use `diff.external`.
2. `gpg.program` (fuente: `git-scm.com/docs/git-config`, sección `gpg.program`): se usa para firmar o **verificar** una firma PGP; en lectura, corre cuando algo pide verificar una firma, no por defecto en `git log` simple.
3. `log.showSignature` (misma fuente): *"If true, makes git-log, git-show, and git-whatchanged assume --show-signature."* Esto confirma que **un simple `git log` sí ejecuta gpg-verify** si `log.showSignature=true` está puesto en config, sin necesitar pasar `--show-signature` a mano — también lo activan `git show` y `git whatchanged`. `commit.gpgSign` (sección `commit.gpgSign`: *"A boolean to specify whether all commits should be GPG signed"*) no aplica a lectura, solo a crear commits (`git commit`), así que para AgentReach "solo lee" es irrelevante. `git verify-commit` y `git log --show-signature` invocan gpg siempre que se pasan explícitamente.
4. `core.pager` (misma fuente): *"Text viewer for use by Git commands... The value is meant to be interpreted by the shell."* Corre en casi cualquier comando de lectura con salida larga (`git log`, `git diff`, `git show`, `git status` en terminales interactivas) salvo que se use `--no-pager` o salida no-tty.
5. `core.sshCommand`: *"If this variable is set, git fetch and git push will use the specified command instead of ssh... when they need to connect to a remote system."* No corre en comandos locales de solo lectura como `git log`/`git status`; solo en red (`fetch`/`push`/`clone`/`pull`).
6. Alias con `!` (fuente: `Documentation/config/alias.adoc`): *"If the alias expansion is prefixed with an exclamation point, it will be treated as a shell command."* Esto corre un comando de shell arbitrario cada vez que el usuario invoca ese alias (p. ej. `git new`), independientemente de si el alias "parece" de lectura.
7. `core.fsmonitor` (fuente: `Documentation/config/core.adoc`): si es `true` activa el monitor de archivos integrado; si es una ruta, *"contains the pathname of the fsmonitor hook command"* que Git ejecuta para acelerar `git status`/`git diff` al detectar cambios en el árbol de trabajo — por tanto si es un hook externo, corre en comandos de solo lectura habituales como `git status`.
8. Recomendación para AgentReach (solo lee el repositorio, no ejecuta git): dar nivel máximo **solo lectura del valor de texto**, nunca permiso para que el valor apunte a un programa que se ejecute.

**Tabla clave → comando que la activa → nivel máximo propuesto → fuente:**

| Clave | Comando que la ejecuta | Nivel máximo propuesto para AgentReach | Fuente |
|---|---|---|---|
| `diff.external` | `git diff`, `git show`, `git log -p` (con `--ext-diff` si es por gitattributes) | Leer el valor (string), nunca ejecutar | git-scm.com/docs/git-config#diff.external |
| `gpg.program` | Cualquier verificación de firma (`git verify-commit`, `log.showSignature=true`, `--show-signature`) | Leer el valor, nunca ejecutar | git-scm.com/docs/git-config#gpg.program |
| `log.showSignature` | `git log`, `git show`, `git whatchanged` (simple, sin flags) si está en `true` | Leer el valor (booleano) | git-scm.com/docs/git-config#log.showSignature |
| `commit.gpgSign` | `git commit` (creación, no lectura) | No aplica / no usar | git-scm.com/docs/git-config#commit.gpgSign |
| `core.pager` | Casi todo comando de lectura con salida larga | Leer el valor, nunca ejecutar | git-scm.com/docs/git-config#core.pager |
| `core.sshCommand` | `git fetch`/`git push` (red, no lectura local) | No aplica a lectura local | git-scm.com/docs/git-config#core.sshCommand |
| `alias.*` con `!` | El comando del alias invocado por el usuario | Leer el valor, nunca ejecutar | git-scm.com/.../config/alias.adoc |
| `core.fsmonitor` | `git status`, `git diff` (hook externo acelerador) | Leer el valor, nunca ejecutar como hook | git-scm.com/.../config/core.adoc |

**Fuentes:**
- https://git-scm.com/docs/git-config (secciones `diff.external`, `gpg.program`, `log.showSignature`, `commit.gpgSign`, `core.pager`, `core.sshCommand`, `core.fsmonitor`) — consultado 2026-11-09
- https://raw.githubusercontent.com/git/git/master/Documentation/config/alias.adoc — consultado 2026-11-09
- https://raw.githubusercontent.com/git/git/master/Documentation/diff-options.adoc (`--ext-diff`, `--textconv`) — consultado 2026-11-09
- https://raw.githubusercontent.com/git/git/master/Documentation/pretty-options.adoc (`--show-signature`) — consultado 2026-11-09
