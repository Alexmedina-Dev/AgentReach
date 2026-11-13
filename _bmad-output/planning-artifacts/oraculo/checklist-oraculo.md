---
title: "AgentReach — Checklist del oráculo (auditoría manual de solo lectura)"
type: checklist
status: draft
created: 2026-11-06
scope: línea base manual para comparar contra el núcleo automatizado (MVP, Fase 1)
companion: catalogo-explicaciones.md (mismos IDs)
sources:
  - memory.md
  - _bmad-output/planning-artifacts/prds/prd-agent-reach-2026-11-05/.memlog.md
  - _bmad-output/planning-artifacts/research/puntos-de-control-plataformas.md
  - _bmad-output/planning-artifacts/architecture/arquitectura-borrador.md
---

# Checklist del oráculo

Qué buscar en una auditoría manual de **solo lectura** de un entorno donde corre un agente de IA (Claude Code, opencode u otros). El resultado es la línea base ("oráculo") contra la que se compara el núcleo de AgentReach cuando automatice esta lista.

## 0. Cómo usar este documento

### 0.1 Reglas de la auditoría

1. **Solo lectura.** No se crea, mueve, edita ni borra nada en el entorno auditado. El registro de hallazgos se escribe fuera del árbol auditado.
2. **Nunca se anota ni se muestra un valor de secreto.** Solo ubicación, tipo, nivel y evidencia.
3. **Reconocer por nombre, ruta y estructura antes que por contenido.** Si hay que mirar dentro de un archivo para clasificarlo, se usan solo comandos que impriman **rutas o conteos** (por ejemplo `rg -l`, `rg -c`, `Select-String -List | Select-Object Path`), nunca las líneas que coinciden.
4. **Ubicaciones sensibles del usuario (`~/.ssh`, `~/.aws`, `~/.gnupg`, almacenes de credenciales): solo metadatos** (existe, tamaño, fecha, permisos). Nunca abrir el contenido. Regla opt-in propuesta, pendiente de confirmar por Alex (memory.md).
5. **Si quien audita es un agente (por ejemplo Claude Code), la salida de cada comando queda en su transcripción** en texto plano (ver CK-057). Otra razón para imprimir solo rutas.
6. **No afirmar alcanzabilidad solo porque exista una referencia.** Anotar qué se verificó y qué no.

### 0.2 Niveles y marcas

Nivel típico de cada ítem: **C** = comprobado (existe y los permisos del SO lo hacen legible para el usuario con que corre el agente), **P** = potencial (existe o hay referencia, pero el acceso no se pudo verificar), **H** = hipótesis (inferencia indirecta, p. ej. una variable que apunta a algo no visible). Definiciones de `.memlog.md` del PRD. "Nivel típico" es orientación, no regla: el nivel real lo da la evidencia.

Marca de fuente en cada ítem:
- **[I]** respaldado por la investigación del proyecto (`puntos-de-control-plataformas.md`, con su fuente oficial).
- **[G⚑]** conocimiento general sobre una herramienta de terceros, **no verificado en esta sesión**. Las rutas y nombres son por verificar contra la documentación de la herramienta antes de convertirlos en requisitos del núcleo.

### 0.3 IDs estables

`CK-NNN` para tipos de hallazgo y `FP-NNN` para falsos positivos conocidos. Un ID **nunca se reutiliza ni se renumera**. Un ítem nuevo recibe el siguiente número libre al final de su categoría o del documento. Un ítem retirado se marca "RETIRADO", no se borra. El catálogo de explicaciones usa los mismos IDs.

### 0.4 Cómo determinar "legible por el SO" sin abrir el archivo

Propuesta aprobada por Alex: ACL/metadatos + reglas del agente (memlog). Para el oráculo manual:

| Sistema | Comando de solo lectura | Qué mirar |
|---|---|---|
| Windows | `icacls <ruta>` o `(Get-Acl <ruta>).Access` | Si el usuario que corre el agente, su grupo o `Users`/`Everyone`/`Authenticated Users` tienen lectura (R, RX, M, F), directa o heredada |
| Windows | `Get-Item -Force <ruta> \| Select Attributes, LinkType, Target` | Atributos, si es junction o symlink y su destino |
| POSIX | `ls -l`, `stat <ruta>` | Propietario, grupo, bits de modo; `getfacl` si hay ACL |
| Ambos | `whoami` / `id` | Identidad con la que se evalúa; debe ser la del agente (supuesto S1: el usuario) |

Limitación: estos comandos miden lo que dicen los metadatos, no lo que hace el agente. Si el agente corre como otro usuario o en un contenedor, hay que anotarlo.

### 0.5 Reglas base de alcance de los agentes (referenciadas como BA-n)

Resumen de la investigación (todas **[I]**; fuentes oficiales en `puntos-de-control-plataformas.md`).

| ID | Regla |
|---|---|
| BA-1 | **Claude Code, herramienta Read.** Lectura libre en el directorio de trabajo y en `additionalDirectories`; fuera de ellos pide aprobación en modo Manual. |
| BA-2 | **Claude Code, shell.** Los comandos corren con los permisos del usuario. El sandbox es opcional, está desactivado por defecto y **no existe en Windows nativo** ("On native Windows, Claude Code runs commands unsandboxed"). Las lecturas por shell no están limitadas por defecto; Read tiene su propio control (corrección del memlog, 2026-11-06). |
| BA-3 | **Claude Code, reglas `deny`.** Orden deny, ask, allow; `deny` gana desde cualquier ámbito. `deny` de Read/Edit cubre herramientas integradas, comandos que Claude Code reconoce (`cat`, `head`, `tail`, `sed`, `tee`) y redirecciones; **no** cubre `grep -r` ni scripts (Python, Node) que abren archivos por su cuenta. Es política de aplicación, no barrera del SO. |
| BA-4 | **Claude Code, código auxiliar.** Hooks de comando, servidores MCP locales (stdio), `apiKeyHelper` y similares corren con el acceso completo del usuario, fuera del sandbox aunque existiera. |
| BA-5 | **opencode, permisos.** "Most permissions default to allow"; `external_directory` y `doom_loop` en `ask`; los archivos `.env` piden aprobación por defecto. Gana la **última** regla que coincide (semántica opuesta a Claude Code). |
| BA-6 | **opencode, `deny` y bash.** No documentado oficialmente si `read: deny` cubre bash. Un tercero (Intility) afirma que se evade; el issue oficial #42979 reporta evasión de `external_directory: deny` por redirección de shell (Linux, cerrado "not planned"). Por verificar en pruebas. Sin sandbox documentado. |
| BA-7 | **opencode lee archivos de Claude Code**: `CLAUDE.md`, `~/.claude/CLAUDE.md`, `.claude/skills/`, `~/.claude/skills/` (salvo variables `OPENCODE_DISABLE_CLAUDE_CODE*`). Un mismo archivo de instrucciones puede gobernar a dos agentes. |

### 0.6 Plantilla de registro de un hallazgo (campos confirmados por Alex)

Una fila por hallazgo, en un archivo fuera del árbol auditado.

| Campo | Contenido |
|---|---|
| `check_id` | ID del ítem (CK-NNN) |
| Dónde | Ruta exacta normalizada (o nombre de variable), ámbito (repo / home / sistema), línea solo como número |
| Qué es y de quién | Tipo y a qué cuenta/servicio pertenece (si se sabe por el nombre), nunca el valor |
| Nivel y por qué | comprobado / potencial / hipótesis, con la evidencia (comando de verificación y su resultado resumido) |
| Ajeno a la tarea | Sí/No: ¿no tiene relación con lo que el agente debía hacer en ese repo? |
| Plataforma y agente | Plataforma anfitriona (Claude Code, opencode...) y agente (p. ej. Dev-Alex) |
| Postura del agente | Reglas aplicables con archivo y línea: bloqueado por regla / pide aprobación / permitido / desconocido. Nota "protegido por política del agente, no por barrera del SO" si hay `deny` |
| Qué hacer | Acción sugerida (código de catálogo) |
| Qué significa | Texto del catálogo (mismo ID) |

### 0.7 Plantilla de comandos de reconocimiento (solo lectura, solo rutas)

```powershell
# Windows, PowerShell: listar archivos .env* sin mostrar contenido (incluye ocultos)
Get-ChildItem -Path <raiz> -Recurse -Force -File -Filter ".env*" -ErrorAction SilentlyContinue | Select-Object FullName, Length, LastWriteTime

# Archivos cuyo contenido contiene un patrón: SOLO rutas (nunca las líneas)
Select-String -Path <raiz>\* -Recurse -Pattern "<patron>" -List | Select-Object -ExpandProperty Path
```

```bash
# POSIX
find <raiz> -type f -name ".env*" -printf '%p %s %TY-%Tm-%Td\n'
rg -l -i --hidden "<patron>" <raiz>      # -l: solo rutas
rg -c -i --hidden "<patron>" <raiz>      # -c: solo conteos
```

Advertencia: no usar `rg -n`, `rg -o`, `grep -n`, `Select-String` sin `-List`, ni `cat`/`type` sobre archivos candidatos: imprimen el valor.

---

## Índice de categorías

| Cat. | Nombre | Ítems |
|---|---|---|
| A | Tokens y credenciales de nube y de plataformas | CK-001 a CK-012 |
| B | Claves privadas, certificados y firmas | CK-013 a CK-016 |
| C | Archivos `.env` y configuración con secretos | CK-017 a CK-022 |
| D | Credenciales de herramientas de línea de comandos (CLI) | CK-023 a CK-029 |
| E | Variables de entorno sensibles | CK-030 a CK-033 |
| F | Archivos de contexto e instrucciones que un agente obedecería | CK-034 a CK-040 |
| G | Configuración del agente: permisos, hooks, MCP, plugins | CK-041 a CK-052 |
| H | Scripts de despliegue, CI e infraestructura | CK-053 a CK-056 |
| I | Registros, historial y datos del agente | CK-057 a CK-060 |
| J | Git y repositorio | CK-061 a CK-064 |
| K | Alcance de rutas y sistema de archivos | CK-065 a CK-070 |
| L | Falsos positivos conocidos | FP-001 a FP-012 |

Total: 70 tipos de hallazgo (CK) en 11 categorías, más 12 falsos positivos (FP).

---

## A. Tokens y credenciales de nube y de plataformas

### CK-001 · Credenciales de AWS · típico C/P
- **Dónde:** Windows `%USERPROFILE%\.aws\credentials` y `config`; POSIX `~/.aws/credentials`, `~/.aws/config`. Ubicación sensible: solo metadatos.
- **Reconocer:** nombre fijo; secciones de perfil (`[default]`) y claves con prefijo `AKIA`/`ASIA` se reconocen solo mirando el contenido: **no hacerlo**. Basta con existencia, tamaño y ACL. En código: nombres de variable `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_PROFILE`.
- **Alcance del agente:** BA-1 (fuera del directorio de trabajo, la herramienta Read pide aprobación), BA-2 (por shell, sin límite en Windows nativo), BA-3 (un `deny` en `Read(~/.aws/**)` no cubre scripts). opencode: BA-5.
- **Falsos positivos:** FP-002, FP-003. Claves de ejemplo de la documentación de AWS.
- **Fuente:** [I] sobre alcance; [G⚑] sobre rutas y formato.

### CK-002 · Credenciales de Azure · típico C/P
- **Dónde:** `%USERPROFILE%\.azure\` / `~/.azure/` (perfiles y cachés de tokens, por verificar); variables `AZURE_CLIENT_SECRET`, `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`; cadenas de conexión de almacenamiento (`AccountKey=`).
- **Reconocer:** existencia del directorio y de archivos de caché de tokens por nombre (por verificar cuáles); nombres de variable.
- **Alcance del agente:** BA-1, BA-2, BA-3 o BA-5 según plataforma.
- **Falsos positivos:** FP-001, FP-004.
- **Fuente:** [G⚑].

### CK-003 · Credenciales de Google Cloud · típico C/P
- **Dónde:** Windows `%APPDATA%\gcloud\` (incluye credenciales por defecto de aplicación); POSIX `~/.config/gcloud/`. Archivos JSON de cuenta de servicio en cualquier carpeta; variable `GOOGLE_APPLICATION_CREDENTIALS` (apunta a un archivo: ver CK-032).
- **Reconocer:** por nombre de directorio; los JSON de cuenta de servicio llevan en su estructura los campos `type: service_account` y `private_key`; reconocerlo sin mostrar valores solo con `rg -l '"type": *"service_account"'`.
- **Alcance del agente:** BA-1, BA-2, BA-3 / BA-5.
- **Falsos positivos:** FP-003 (fixtures), FP-001.
- **Fuente:** [G⚑].

### CK-004 · Tokens de plataformas de despliegue y alojamiento (Railway, Vercel, Netlify, Fly.io, Heroku, Cloudflare...) · típico C/P
- **Dónde:** variables `RAILWAY_TOKEN`, `VERCEL_TOKEN`, `NETLIFY_AUTH_TOKEN`, `FLY_API_TOKEN`, `HEROKU_API_KEY`, `CLOUDFLARE_API_TOKEN` (nombres por verificar en la documentación de cada una); archivos de sesión del CLI de cada plataforma en el directorio de usuario (rutas distintas por plataforma, **por verificar**); archivos de enlace de proyecto en el repo (`.vercel/`, `.netlify/`, `fly.toml`, `railway.json`/`.railway`), que no son secretos pero indican a qué proyecto de producción está vinculada la carpeta.
- **Reconocer:** nombres de variable; presencia de los archivos de enlace; directorios de configuración del CLI en `%USERPROFILE%`, `%APPDATA%`, `%LOCALAPPDATA%` o `~/.config` (listar nombres).
- **Alcance del agente:** BA-1 a BA-6. Caso de referencia del proyecto: un token de Railway en un archivo ajeno a la tarea (PocketOS, memory.md). Con los valores por defecto de opencode, un token fuera de `.env` no pide aprobación (BA-5).
- **Falsos positivos:** FP-001, FP-004, FP-005.
- **Fuente:** [I] sobre alcance; [G⚑] sobre nombres y rutas de cada plataforma.

### CK-005 · Tokens personales de alojamiento de código (GitHub, GitLab, Bitbucket, Azure DevOps) · típico C/P
- **Dónde:** en archivos del repo o del usuario (scripts, `.env`, notas, `.npmrc`, `.git-credentials`); como variables (`GITHUB_TOKEN`, `GH_TOKEN`, `GITLAB_TOKEN`...).
- **Reconocer:** prefijos conocidos (`ghp_`, `github_pat_`, `glpat-`) solo mediante `rg -l` con el patrón de prefijo; nombre de variable.
- **Alcance del agente:** BA-1 a BA-6. Ver CK-033 para los tokens de GitHub que el agente hereda por entorno.
- **Falsos positivos:** FP-002, FP-004.
- **Fuente:** [G⚑] sobre prefijos; [I] sobre `GITHUB_TOKEN`/`GH_TOKEN`.

### CK-006 · Claves de API de proveedores de IA · típico C/P
- **Dónde:** `.env`, scripts, `settings.json` del agente (bloque `env`), `opencode.json`, perfiles de shell. Variables como `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `HF_TOKEN`.
- **Reconocer:** nombre de variable; en configs de agente, la clave `env` con nombres sensibles (listar nombres, no valores).
- **Alcance del agente:** el agente puede leerlas igual que cualquier archivo (BA-1/BA-5); el scrub opcional de Claude Code (CK-047) las limpia del entorno de subprocesos solo si se activa.
- **Falsos positivos:** FP-001, FP-004.
- **Fuente:** [I] sobre el scrub; [G⚑] sobre nombres.

### CK-007 · Claves de servicios SaaS: pagos, mensajería, correo, chat · típico C/P
- **Dónde:** `.env`, configs, código. Ejemplos de nombre: `STRIPE_SECRET_KEY`, `TWILIO_AUTH_TOKEN`, `SENDGRID_API_KEY`, `SLACK_BOT_TOKEN`, URLs de webhook (`hooks.slack.com/services/...`).
- **Reconocer:** nombre de variable; prefijos de proveedor (p. ej. `sk_live_`, `xoxb-`) vía `rg -l` solamente. Distinguir clave de producción (`live`) y de prueba (`test`) por el nombre de la variable o del archivo.
- **Alcance del agente:** BA-1 a BA-5.
- **Falsos positivos:** FP-001, FP-002, FP-004. Las claves `test`/sandbox son menos graves pero se reportan.
- **Fuente:** [G⚑].

### CK-008 · Cadenas de conexión de bases de datos · típico C/P
- **Dónde:** `.env`, `appsettings*.json`, `docker-compose.yml`, `config/database.yml`, scripts. Forma `motor://usuario:clave@host/bd` o `Server=...;Password=...`.
- **Reconocer:** nombres `DATABASE_URL`, `DB_PASSWORD`, `ConnectionStrings`; una URL con `:` y `@` entre `//` y el host. Verificar con `rg -l` del patrón, sin imprimir.
- **Alcance del agente:** BA-1 a BA-5. Si el host no es local, es acceso a datos reales.
- **Falsos positivos:** FP-004 (`user:password@localhost`), FP-003.
- **Fuente:** [G⚑].

### CK-009 · Configuración de Kubernetes (kubeconfig) · típico C/P
- **Dónde:** `%USERPROFILE%\.kube\config` / `~/.kube/config`; variable `KUBECONFIG` (CK-032).
- **Reconocer:** nombre y ruta; solo metadatos por ser ubicación sensible.
- **Alcance del agente:** BA-1 a BA-5.
- **Falsos positivos:** FP-003.
- **Fuente:** [G⚑].

### CK-010 · Credenciales y estado de Terraform y otras herramientas de infraestructura como código · típico C/P
- **Dónde:** `terraform.tfstate` y `*.tfstate.backup` (pueden contener secretos en texto plano), `*.tfvars`, credenciales de Terraform Cloud en `%APPDATA%\terraform.d\credentials.tfrc.json` / `~/.terraform.d/credentials.tfrc.json`; análogos de Pulumi.
- **Reconocer:** extensión y nombre; existencia y tamaño.
- **Alcance del agente:** BA-1 a BA-5.
- **Falsos positivos:** FP-001 (`*.tfvars.example`), FP-003.
- **Fuente:** [G⚑].

### CK-011 · Secretos de firma y de sesión de aplicaciones · típico C/P
- **Dónde:** variables y configs: `JWT_SECRET`, `SECRET_KEY`, `APP_KEY`, `SESSION_SECRET`, `ENCRYPTION_KEY`, `SIGNING_KEY`, `*_SALT`.
- **Reconocer:** nombre de variable o clave de config.
- **Alcance del agente:** BA-1 a BA-5.
- **Falsos positivos:** FP-004 (`changeme`), FP-010 (clave de traducción o de diccionario llamada `KEY`).
- **Fuente:** [G⚑].

### CK-012 · Archivos de credenciales exportadas o de cuenta de servicio, sin nombre fijo · típico C/P
- **Dónde:** cualquier carpeta; nombres como `credentials.json`, `service-account*.json`, `client_secret*.json`, `*-key.json`, `token.json`, `secrets.json`, `*.secret`, `id_token`.
- **Reconocer:** por nombre y por estar fuera de carpetas de pruebas. Confirmar el tipo con `rg -l` de los nombres de campo característicos, sin imprimir.
- **Alcance del agente:** BA-1 a BA-5.
- **Falsos positivos:** FP-003, FP-001.
- **Fuente:** [G⚑].

## B. Claves privadas, certificados y firmas

### CK-013 · Claves privadas SSH · típico C/P
- **Dónde:** `%USERPROFILE%\.ssh\id_rsa`, `id_ed25519`, `id_ecdsa` (sin extensión) y variantes con otro nombre; POSIX `~/.ssh/`. Ubicación sensible: solo metadatos (nombre, tamaño, ACL).
- **Reconocer:** nombre sin `.pub`; archivo con su par `.pub` al lado (la clave pública **no** es secreta). Un archivo con permisos amplios (POSIX distintos de 600; Windows con ACL a `Users`/`Everyone`) es señal de exposición adicional (ver CK-070).
- **Alcance del agente:** BA-1 (Read pide aprobación fuera del directorio de trabajo), BA-2 (por shell, sin límite en Windows nativo; ejemplo oficial del sandbox: "most of the machine, including credential files such as `~/.ssh`"), BA-3, BA-5.
- **Falsos positivos:** FP-006 (`.pub`, `known_hosts`), FP-003.
- **Fuente:** [I] sobre alcance; [G⚑] sobre nombres.

### CK-014 · Configuración SSH, agente SSH y listas de hosts · típico C/P
- **Dónde:** `~/.ssh/config`, `known_hosts`, `authorized_keys`; en Windows, el servicio "OpenSSH Authentication Agent"; variable `SSH_AUTH_SOCK` en POSIX.
- **Reconocer:** existencia de los archivos; estado del agente SSH con claves cargadas (solo si la verificación no expone claves; **por verificar** el comando de solo lectura exacto). `config` puede revelar a qué servidores llega el usuario y con qué archivo de clave (`IdentityFile`).
- **Alcance del agente:** un agente SSH en marcha puede permitir usar una clave **sin leer el archivo**. Esa vía no se ve por permisos de archivo. BA-2.
- **Falsos positivos:** FP-006.
- **Fuente:** [G⚑].

### CK-015 · Claves privadas y almacenes de claves genéricos (`.pem`, `.key`, `.pfx`, `.p12`, `.jks`, `.keystore`, `.ppk`) · típico C/P
- **Dónde:** cualquier carpeta del repo o del usuario.
- **Reconocer:** extensión y nombre; confirmar con `rg -l -- "-----BEGIN .*PRIVATE KEY-----"` (solo rutas). Los `.pfx`/`.p12`/`.jks` son binarios que pueden estar protegidos con contraseña, y esa contraseña a veces está en otro archivo (buscar al lado).
- **Alcance del agente:** BA-1 a BA-5.
- **Falsos positivos:** FP-006 (certificados públicos `.crt`/`.cer`/`.pem` sin clave privada), FP-003, FP-008.
- **Fuente:** [G⚑].

### CK-016 · Claves GPG y de firma · típico C/P
- **Dónde:** `~/.gnupg/` (POSIX); Windows `%APPDATA%\gnupg` o `%USERPROFILE%\.gnupg` según la distribución (**por verificar**). Ubicación sensible: solo metadatos.
- **Reconocer:** existencia y tamaño de `private-keys-v1.d/`; no abrir.
- **Alcance del agente:** BA-1 a BA-5.
- **Falsos positivos:** FP-006 (claves públicas exportadas).
- **Fuente:** [G⚑].

## C. Archivos `.env` y configuración con secretos

### CK-017 · Archivos `.env` y variantes · típico C
- **Dónde:** raíz del proyecto y subcarpetas: `.env`, `.env.local`, `.env.production`, `.env.development`, `.env.staging`, `.env.*.local`, `.envrc`, `env.txt`, `.flaskenv`; en Windows también copias renombradas (`.env.bak`, `.env - copia`).
- **Reconocer:** por nombre (patrón `.env*`, sin importar mayúsculas). Número de líneas por tamaño; **no** abrir.
- **Alcance del agente:** BA-1 (dentro del directorio de trabajo, libre en Claude Code), BA-5 (opencode **pide aprobación** para `.env` por defecto). BA-3: un `deny` de Read cubre la herramienta pero no scripts. Fuente de PocketOS: el secreto estaba en un archivo no relacionado con la tarea.
- **Falsos positivos:** FP-001 (`.env.example`, `.env.sample`, `.env.template`, `.env.dist`), FP-003.
- **Fuente:** [I] sobre alcance; [G⚑] sobre variantes.

### CK-018 · Archivos de configuración de aplicación con secretos · típico C/P
- **Dónde:** `appsettings.json`, `appsettings.*.json`, `web.config`, `application.properties`, `application.yml`, `config.yml`, `settings.py`, `wp-config.php`, `config/secrets.yml`. **Visual Studio / .NET:** almacén "User Secrets" fuera del repo en `%APPDATA%\Microsoft\UserSecrets\<id>\secrets.json` (POSIX `~/.microsoft/usersecrets/<id>/secrets.json`), enlazado por un `UserSecretsId` en el `.csproj`.
- **Reconocer:** nombre; un `.csproj` con `UserSecretsId` indica que existe un `secrets.json` correspondiente fuera del repo. Claves con nombres `Password`, `ConnectionString`, `Secret`, `ApiKey` se confirman con `rg -l`, sin imprimir.
- **Alcance del agente:** el repo: BA-1/BA-5. El User Secrets está fuera del directorio de trabajo: BA-1 (aprobación) y BA-2 (shell sin límite).
- **Falsos positivos:** FP-004, FP-001 (`appsettings.Example.json`), FP-003.
- **Fuente:** [G⚑].

### CK-019 · Docker y Compose con secretos embebidos · típico C/P
- **Dónde:** `docker-compose*.yml`, `Dockerfile` (`ENV`, `ARG` con valores), `.env` usado por Compose, `*.env` de contenedores.
- **Reconocer:** nombres de clave (`PASSWORD`, `TOKEN`, `SECRET`) en `environment:`/`ENV`. Confirmar con `rg -l`.
- **Alcance del agente:** BA-1/BA-5.
- **Falsos positivos:** FP-004 (`POSTGRES_PASSWORD: postgres` para desarrollo local), FP-005 (`${VAR}`).
- **Fuente:** [G⚑].

### CK-020 · Archivos de secretos dedicados · típico C/P
- **Dónde:** `*.tfvars`, `secrets.yaml`, `secrets.yml`, `secrets.json`, `.secrets`, `vault.yml` (Ansible, cifrado o no), `~/.vault-token`, `.htpasswd`, `.pgpass`, `.my.cnf`.
- **Reconocer:** por nombre. Un archivo de Ansible Vault empieza con `$ANSIBLE_VAULT;` (cifrado: se reporta igualmente, con nota); no abrir para comprobarlo, usar `rg -l '^\$ANSIBLE_VAULT'`.
- **Alcance del agente:** BA-1 a BA-5.
- **Falsos positivos:** FP-001, FP-003.
- **Fuente:** [G⚑].

### CK-021 · Perfiles de publicación y archivos de despliegue de Visual Studio · típico C/P
- **Dónde:** `*.pubxml`, `*.pubxml.user`, `*.PublishSettings` (pueden incluir usuario y contraseña de publicación), `Properties\PublishProfiles\`.
- **Reconocer:** extensión y carpeta. `*.pubxml.user` es un archivo local de usuario habitualmente fuera del control de versiones.
- **Alcance del agente:** BA-1/BA-5; entorno de Alex usa Visual Studio (memlog). Cómo integra Visual Studio al agente: **por verificar** (investigación, transversal).
- **Falsos positivos:** FP-004.
- **Fuente:** [G⚑].

### CK-022 · Copias de seguridad, volcados y exportaciones · típico C/P
- **Dónde:** `*.sql`, `*.dump`, `*.bak`, `*.sqlite`, `*.db`, `*.zip`/`*.tar.gz` con nombre de producción, `export*.csv`.
- **Reconocer:** extensión, tamaño, fecha, nombre (`prod`, `backup`). No abrir. Pueden contener datos personales o secretos.
- **Alcance del agente:** BA-1/BA-5.
- **Falsos positivos:** FP-003 (bases de datos de pruebas), FP-008.
- **Fuente:** [G⚑].

## D. Credenciales de herramientas de línea de comandos (CLI)

### CK-023 · GitHub CLI (`gh`) · típico C/P
- **Dónde:** Windows `%APPDATA%\GitHub CLI\hosts.yml`; POSIX `~/.config/gh/hosts.yml`. `gh` puede guardar el token en el llavero del sistema (Windows Credential Manager) en vez de en el archivo: la ausencia del token en `hosts.yml` no prueba que no haya sesión (**por verificar** el comportamiento exacto). Sesión activa: `gh auth status` muestra quién ha iniciado sesión y no imprime el token (**por verificar** que sea seguro en la versión instalada). La sesión de `gh` de esta máquina es de `<cuenta de GitHub>` (memory.md).
- **Reconocer:** existencia del archivo; entrada en Credential Manager (CK-028).
- **Alcance del agente:** BA-1 a BA-5. Con una sesión `gh` válida el agente puede actuar sobre GitHub **sin leer ningún archivo**, ejecutando el comando `gh`. Esa vía (comandos disponibles) no depende de permisos de archivo.
- **Falsos positivos:** ninguno propio; ver FP-003 para volcados en tests.
- **Fuente:** [G⚑]; [I] sobre `GH_TOKEN`.

### CK-024 · Docker (`config.json`) · típico C/P
- **Dónde:** `%USERPROFILE%\.docker\config.json` / `~/.docker/config.json`. Contiene `auths` (a veces en base64, que **no** es cifrado) o delega en un `credsStore` (llavero del sistema).
- **Reconocer:** existencia; si hay entrada `auths` o `credsStore`, vía `rg -c '"auths"|"credsStore"'` (solo conteos).
- **Alcance del agente:** BA-1 a BA-5.
- **Falsos positivos:** FP-003.
- **Fuente:** [G⚑].

### CK-025 · npm, Yarn y pnpm · típico C/P
- **Dónde:** `%USERPROFILE%\.npmrc` / `~/.npmrc`, `.npmrc` del proyecto, `.yarnrc.yml` (`npmAuthToken`).
- **Reconocer:** existencia; líneas con `_authToken` o `_auth` confirmadas con `rg -l`.
- **Alcance del agente:** BA-1 a BA-5.
- **Falsos positivos:** FP-005 (`_authToken=${NPM_TOKEN}` es solo una referencia).
- **Fuente:** [G⚑].

### CK-026 · PyPI, pip, uv y twine · típico C/P
- **Dónde:** `~/.pypirc` (`%USERPROFILE%\.pypirc`), `pip.ini` (Windows, `%APPDATA%\pip\`) / `pip.conf` con `index-url` con credenciales, `uv.toml`, variables `UV_PUBLISH_TOKEN`, `TWINE_PASSWORD`.
- **Reconocer:** existencia; URLs con `usuario:clave@` en `index-url`, vía `rg -l`.
- **Alcance del agente:** BA-1 a BA-5.
- **Falsos positivos:** FP-005.
- **Fuente:** [G⚑].

### CK-027 · NuGet, Maven, Gradle y Cargo · típico C/P
- **Dónde:** `NuGet.Config` (`%APPDATA%\NuGet\`), `~/.m2/settings.xml`, `~/.gradle/gradle.properties`, `~/.cargo/credentials.toml`.
- **Reconocer:** existencia; claves como `ClearTextPassword`, `<password>`, `token` confirmadas con `rg -l`.
- **Alcance del agente:** BA-1 a BA-5.
- **Falsos positivos:** FP-005.
- **Fuente:** [G⚑].

### CK-028 · Credenciales de Git, `.netrc` y Windows Credential Manager · típico C/P
- **Dónde:** `~/.git-credentials` (texto plano si se usa el helper `store`), `~/.netrc` / `%USERPROFILE%\_netrc`; Windows Credential Manager (almacén del sistema, no es un archivo legible directamente). `git config --get-all credential.helper` indica el helper en uso (no imprime secretos).
- **Reconocer:** existencia de los archivos; en Windows `cmdkey /list` enumera **nombres** de credenciales almacenadas, no sus contraseñas.
- **Alcance del agente:** los archivos: BA-1 a BA-5. Credential Manager: el agente no lee el almacén directamente, pero un comando `git` que use el helper puede autenticarse con él (vía "comandos disponibles").
- **Falsos positivos:** ninguno propio.
- **Fuente:** [G⚑].

### CK-029 · Credenciales propias de los agentes (Claude Code y opencode) · típico C/P
- **Dónde:** Claude Code `%USERPROFILE%\.claude\.credentials.json` (almacén real en Windows: **por verificar**; la investigación no leyó el archivo); opencode `%USERPROFILE%\.local\share\opencode\auth.json` (claves de API y tokens OAuth) y `mcp-auth.json`; `~/.claude.json` (cuenta y configuración de MCP). Ubicación sensible: solo metadatos; no leer.
- **Reconocer:** existencia, tamaño, ACL. La investigación no halló descripción de cifrado ni de controles de acceso de `auth.json`.
- **Alcance del agente:** BA-1/BA-2. Un agente con acceso al disco puede leer las credenciales de otro agente o de sí mismo.
- **Falsos positivos:** ninguno propio.
- **Fuente:** [I].

## E. Variables de entorno sensibles

> Las variables del entorno **real** de un proceso no son legibles estáticamente desde archivos (investigación P2). El oráculo solo puede inventariar **nombres**: del entorno del usuario y del sistema (registro de Windows, perfiles de shell) y del entorno de la sesión de auditoría. Nunca se imprimen valores.

### CK-030 · Variables de entorno con nombre de credencial · típico C/H
- **Dónde:** Windows: usuario `HKCU\Environment`, sistema `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment`; ver también `Get-ChildItem Env:` (**imprime valores**: usar `Get-ChildItem Env: | Select-Object -ExpandProperty Name`). POSIX: `env` (valores), `printenv` (valores); usar `env | cut -d= -f1`.
- **Reconocer:** nombres que contengan `TOKEN`, `SECRET`, `KEY`, `PASSWORD`, `PASSWD`, `CREDENTIAL`, `PRIVATE`, `AUTH`, o nombres específicos de CK-001 a CK-011.
- **Alcance del agente:** los subprocesos de Claude Code heredan su entorno (inferencia razonable de `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`: ver CK-047). Herencia en opencode: no documentada.
- **Falsos positivos:** FP-010 (`PATH`, `KEYBOARD_LAYOUT`...), nombres que coinciden sin ser secreto.
- **Fuente:** [I] sobre herencia; [G⚑] sobre ubicaciones del registro.

### CK-031 · Valores literales en perfiles de shell · típico C
- **Dónde:** Windows PowerShell `$PROFILE` (`Documents\PowerShell\...profile.ps1`, `Documents\WindowsPowerShell\...`), Git Bash `~/.bashrc`, `~/.bash_profile`; POSIX `~/.bashrc`, `~/.zshrc`, `~/.profile`, `~/.zshenv`.
- **Reconocer:** archivos existentes con líneas `export NOMBRE=` o `$env:NOMBRE =`; confirmar con `rg -l` por nombre de variable sensible, sin imprimir.
- **Alcance del agente:** cada shell nueva carga el perfil, así que el entorno se llena en cada comando del agente. BA-1/BA-2.
- **Falsos positivos:** FP-005 (variable que referencia otra), FP-004.
- **Fuente:** [G⚑].

### CK-032 · Variables que apuntan a ubicaciones de credenciales o a configuración del agente · típico H
- **Dónde:** nombres: `GOOGLE_APPLICATION_CREDENTIALS`, `AWS_SHARED_CREDENTIALS_FILE`, `KUBECONFIG`, `SSH_AUTH_SOCK`, `CLAUDE_CONFIG_DIR`, `OPENCODE_CONFIG`, `OPENCODE_CONFIG_DIR`, `OPENCODE_CONFIG_CONTENT`, `OPENCODE_DB`, `NPM_CONFIG_USERCONFIG`.
- **Reconocer:** solo el nombre y si apunta a una ruta existente (verificar existencia de la ruta, no su contenido). `CLAUDE_CONFIG_DIR` cambia dónde buscar `~/.claude` y no se puede fijar desde `.claude/settings.json` del proyecto [I].
- **Alcance del agente:** apuntan a algo posiblemente no visible: origen típico de una **hipótesis**.
- **Falsos positivos:** ninguno propio.
- **Fuente:** [I] para las de Claude Code y opencode; [G⚑] para el resto.

### CK-033 · Tokens de GitHub que el agente hereda aun con el scrub activado · típico C/H
- **Dónde:** variables `GITHUB_TOKEN`, `GH_TOKEN`, `GH_ENTERPRISE_TOKEN`, `GITHUB_ENTERPRISE_TOKEN`; también `HTTP_PROXY`/`HTTPS_PROXY`.
- **Reconocer:** nombre de variable en el entorno del usuario o en el bloque `env` de `settings.json` del agente.
- **Alcance del agente:** `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` quita credenciales de los subprocesos, pero **deja** estas variables "so that `gh` and scripts that call the GitHub API keep working". Oficial.
- **Falsos positivos:** FP-005.
- **Fuente:** [I].

## F. Archivos de contexto e instrucciones que un agente obedecería

> Son **contexto, no control** [I]. Un agente los lee y tiende a seguirlos. Niveles típicos: H (la inferencia es indirecta), salvo que contengan un secreto (entonces se reporta además como CK de su categoría).

### CK-034 · `CLAUDE.md`, `CLAUDE.local.md` y reglas de Claude Code · típico H
- **Dónde:** raíz y subcarpetas del repo; `%USERPROFILE%\.claude\CLAUDE.md`; `.claude\rules\*.md`.
- **Reconocer:** por nombre; leer solo para clasificar instrucciones (ver CK-040), nunca copiar fragmentos que parezcan secretos.
- **Alcance del agente:** se cargan como contexto automáticamente. opencode también lee `CLAUDE.md` y `~/.claude/CLAUDE.md` (BA-7).
- **Falsos positivos:** FP-012.
- **Fuente:** [I].

### CK-035 · `AGENTS.md` y reglas de opencode · típico H
- **Dónde:** raíz y subcarpetas del repo; opencode busca `AGENTS.md` y cae a `CLAUDE.md`. Claude Code puede leer `AGENTS.md` en lugar de `CLAUDE.md`.
- **Reconocer:** por nombre.
- **Alcance del agente:** contexto cargado automáticamente en ambos agentes.
- **Falsos positivos:** FP-012.
- **Fuente:** [I].

### CK-036 · Skills (con `allowed-tools` y hooks) · típico H/P
- **Dónde:** Claude Code `.claude\skills\<nombre>\SKILL.md` y `%USERPROFILE%\.claude\skills\`; opencode `.opencode\skills\`, `~/.config/opencode/skills/`, y también `.claude\skills\`, `.agents\skills\` (BA-7). Ruta Windows de skills gestionados: **por verificar**.
- **Reconocer:** carpetas con `SKILL.md`; en el encabezado del archivo buscar `allowed-tools` y `hooks`.
- **Alcance del agente:** `allowed-tools` concede aprobación previa de herramientas durante el turno; el campo no depende de la confianza del espacio de trabajo y funciona incluso en `-p` en carpeta no confiada. `deny` y `ask` siguen ganando [I]. Un skill de proyecto amplía lo que el agente hace sin preguntar.
- **Falsos positivos:** los skills de BMAD de `.claude/` (214 archivos, revisados en memory.md) son legítimos: se reportan como inventario, no como amenaza.
- **Fuente:** [I].

### CK-037 · Agentes y subagentes definidos · típico H/P
- **Dónde:** Claude Code `.claude\agents\*.md`, `%USERPROFILE%\.claude\agents\`; opencode `.opencode\agents\`, `~/.config/opencode/agents/` o clave `agent` en `opencode.json`.
- **Reconocer:** frontmatter con `tools`, `disallowedTools`, `permissionMode`, `mcpServers`, `hooks` (Claude Code); `permission`, `mode`, `prompt` (opencode). El efecto exacto de `permissionMode` sobre las reglas **no está verificado**.
- **Alcance del agente:** pueden ampliar o restringir permisos y traer servidores MCP o hooks propios.
- **Falsos positivos:** FP-012.
- **Fuente:** [I].

### CK-038 · Comandos y prompts personalizados · típico H
- **Dónde:** `.claude\commands\`, `%USERPROFILE%\.claude\commands\` (ubicación general conocida; **no cubierta por la investigación: por verificar**); `.opencode\commands\` (**por verificar**).
- **Reconocer:** archivos `.md` dentro de esas carpetas.
- **Alcance del agente:** se ejecutan como instrucciones cuando el usuario o el agente los invocan.
- **Falsos positivos:** FP-012.
- **Fuente:** [G⚑].

### CK-039 · Archivos de instrucciones de otras herramientas de IA · típico H
- **Dónde:** `.cursorrules`, `.cursor\rules\`, `.github\copilot-instructions.md`, `GEMINI.md`, `.windsurfrules`, `.aider*`. **Por verificar** la lista actual y qué agentes los leen (la investigación cubre solo Claude Code y opencode; Dev-Alex y ChatGPT no se investigaron).
- **Reconocer:** por nombre.
- **Alcance del agente:** solo lo gobiernan si el agente correspondiente está presente.
- **Falsos positivos:** FP-012.
- **Fuente:** [G⚑].

### CK-040 · Instrucciones sospechosas dentro de documentos, código o datos que el agente leería · típico H
- **Dónde:** `README.md`, `CONTRIBUTING.md`, documentación, comentarios de código, issues exportados, páginas descargadas, resultados de herramientas MCP.
- **Reconocer (patrones, solo rutas con `rg -l -i`):** frases dirigidas a una IA ("ignore previous instructions", "you are an AI", "as an assistant, you must", "system prompt"); órdenes de leer rutas sensibles (`~/.ssh`, `.env`), de ejecutar descargas encadenadas (`curl ... | sh`, `iwr ... | iex`) o de enviar contenido a una URL; texto oculto (comentarios HTML, caracteres de ancho cero, texto blanco en Markdown renderizado).
- **Alcance del agente:** el agente puede tratarlo como instrucción legítima. El control relevante es lo que el agente puede **hacer** después (permisos, CK-041 a CK-047).
- **Falsos positivos:** documentación legítima sobre seguridad de IA, tests de inyección de prompts (FP-003), `README` de AgentReach.
- **Fuente:** [G⚑]. El riesgo de inyección está sustentado en la investigación solo de forma indirecta (hace referencia a "prompt injection" en el scrub de entorno).

## G. Configuración del agente: permisos, hooks, MCP, plugins

> Cada ítem de esta categoría **cambia el alcance** del agente. Se reporta lo **configurado**; que esté **activo** depende de la confianza del espacio de trabajo, de `--settings` y de políticas gestionadas, lo que no se puede probar solo con lectura estática [I]. Una regla `deny` no baja ni borra el hallazgo que cubre: añade la nota "protegido por política del agente, no por barrera del SO" (decisión de Alex).

### CK-041 · Reglas de permisos de Claude Code · típico C (configurado)
- **Dónde:** `%USERPROFILE%\.claude\settings.json`, `.claude\settings.json`, `.claude\settings.local.json`; bloque `permissions` con `allow`, `ask`, `deny`, `additionalDirectories`. Listas se combinan entre ámbitos.
- **Reconocer:** claves `permissions.*`; anotar archivo y número de línea de cada regla relevante. Reglas amplias de riesgo: `Bash(*)`, `Read(//**)`, `Edit(*)`, `WebFetch`. Rutas de reglas en Windows se normalizan a POSIX (`C:\Users\alice` se vuelve `/c/Users/alice`; ejemplo oficial `//c/**/.env`): al comprobar si una regla cubre un archivo, normalizar primero.
- **Alcance del agente:** BA-3. `allow` y `additionalDirectories` del proyecto solo se aplican tras aceptar el diálogo de confianza; `deny` y `ask` se aplican de inmediato. Regla `Bash(...)` `deny` no coincide con el mismo programa por otra ruta ni dentro de `sh -c`: es heurística.
- **Falsos positivos:** FP-012 (archivo sin reglas).
- **Fuente:** [I].

### CK-042 · Modo por defecto y confianza del espacio de trabajo (Claude Code) · típico C (configurado)
- **Dónde:** `permissions.defaultMode` en settings: `acceptEdits`, `plan`, `dontAsk`, `auto`, `bypassPermissions`. Decisión de confianza por carpeta: se guarda en `%USERPROFILE%\.claude.json` (formato exacto **por verificar**).
- **Reconocer:** valor de `defaultMode` (el nombre del modo, no es secreto). `bypassPermissions` y `auto` no surten efecto desde configuración de proyecto o local: solo desde usuario o gestionada [I].
- **Alcance del agente:** `bypassPermissions` anula los avisos; `dontAsk` deniega lo no permitido. Si el modo viene de usuario o gestionada, el agente actúa sin pedir confirmación.
- **Falsos positivos:** ninguno propio.
- **Fuente:** [I].

### CK-043 · Sandbox de Claude Code ausente o no aplicable · típico C (configurado)
- **Dónde:** bloque `sandbox.*` en settings (`enabled`, filesystem allow/deny, network). **En Windows nativo no existe**; solo macOS, Linux y WSL2.
- **Reconocer:** en Windows 11 nativo el hallazgo es "sandbox no disponible en esta plataforma", independientemente de lo que diga el archivo. En WSL2/macOS/Linux, valor de `sandbox.enabled`.
- **Alcance del agente:** BA-2. Aunque exista, el sandbox cubre solo comandos de shell: Read/Edit/Write/WebFetch siguen las reglas de permisos, y hooks, MCP locales y helpers corren fuera (BA-4). Posible recomendación de producto: WSL2 para quien quiera sandbox (decisión 4 de la investigación, pendiente).
- **Falsos positivos:** ninguno propio.
- **Fuente:** [I].

### CK-044 · Política gestionada de Claude Code · típico C/P
- **Dónde:** `C:\Program Files\ClaudeCode\managed-settings.json` y `managed-settings.d\`; registro `HKLM\SOFTWARE\Policies\ClaudeCode` valor `Settings`; registro de usuario `HKCU\SOFTWARE\Policies\ClaudeCode` (escribible por el usuario, no cuenta como administrador); caché de servidor `~\.claude\remote-settings.json`. El ruta antigua `C:\ProgramData\ClaudeCode\managed-settings.json` **no se lee**.
- **Reconocer:** existencia de cada fuente. En un equipo personal lo esperable es que no haya nada: se reporta como "ninguna política gestionada encontrada", dato y no error. Una política de servidor es invisible salvo por `remote-settings.json`.
- **Alcance del agente:** la política gestionada gana sobre todo lo demás y el usuario no puede anularla.
- **Falsos positivos:** ninguno propio.
- **Fuente:** [I].

### CK-045 · Hooks de Claude Code · típico C (configurado)
- **Dónde:** `hooks` en cualquier settings, en `hooks/hooks.json` de plugins, y en el encabezado de skills y agentes. Tipos: command, http, mcp_tool, prompt, agent.
- **Reconocer:** claves `hooks`; para cada una anotar evento (p. ej. `PreToolUse`, `UserPromptSubmit`, `SessionStart`), tipo y comando o URL (si el comando incluye una credencial literal, también CK-005 a CK-007).
- **Alcance del agente:** BA-4 (un hook de comando es código arbitrario con el acceso del usuario). Un hook de `PreToolUse` puede endurecer pero no saltarse un `deny`; si falla o caduca no bloquea, salvo `onFailure: "block"`.
- **Falsos positivos:** FP-012.
- **Fuente:** [I].

### CK-046 · Servidores MCP de Claude Code · típico C (configurado)
- **Dónde:** `.mcp.json` (raíz del proyecto), `%USERPROFILE%\.claude.json` (local y usuario), `C:\Program Files\ClaudeCode\managed-mcp.json`.
- **Reconocer:** servidores con `command`/`args` (locales, stdio, corren como programa en la máquina), `url`/`headers` (remotos), y `env`; en `env`/`headers` listar solo **nombres** y si usan `${VAR}`.
- **Alcance del agente:** BA-4. Un `.mcp.json` en un repo clonado se carga **sin preguntar** en `claude -p` y en el Agent SDK. Los stdio heredan el entorno del shell por defecto (confirmado por la existencia de `CLAUDE_CODE_MCP_ALLOWLIST_ENV`).
- **Falsos positivos:** FP-005 (`${VAR}`).
- **Fuente:** [I].

### CK-047 · Herencia de entorno y bloque `env` (Claude Code) · típico C/H
- **Dónde:** bloque `env` de settings; variables `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`, `CLAUDE_CODE_MCP_ALLOWLIST_ENV`, `CLAUDE_CODE_USE_POWERSHELL_TOOL`.
- **Reconocer:** nombres en el bloque `env` (no valores) y si el scrub o la lista segura están activados (valor 1).
- **Alcance del agente:** el scrub (opt-in, desactivado por defecto) quita credenciales de los subprocesos por nombre y forma del valor, pero deja los tokens de GitHub (CK-033). Oficial: usarlo como una capa más, no como único control. Que los subprocesos hereden todo sin el scrub es **inferencia razonable**, no frase oficial.
- **Falsos positivos:** ninguno propio.
- **Fuente:** [I].

### CK-048 · Permisos de opencode · típico C (configurado)
- **Dónde:** clave `permission` en `opencode.json` del proyecto, `~/.config/opencode/opencode.json` (ruta Windows de la config global **no documentada**; sospecha `%USERPROFILE%\.config\opencode`, por verificar), archivos gestionados `%ProgramData%\opencode`, y en cada agente.
- **Reconocer:** claves `read`, `edit`, `bash`, `external_directory`, `webfetch`, `skill`... con `allow`/`ask`/`deny` y patrones. Recordar: gana la **última** regla coincidente (BA-5).
- **Alcance del agente:** BA-5 y BA-6. El modo `plan` no restringe bash. Un `read: deny` puede no cubrir bash (por verificar): el hallazgo se mantiene como potencial.
- **Falsos positivos:** FP-012.
- **Fuente:** [I].

### CK-049 · Capas de configuración de opencode y referencias a secretos · típico C/H
- **Dónde:** siete capas: remota (`.well-known/opencode`), global, `OPENCODE_CONFIG`, proyecto, `.opencode`, `OPENCODE_CONFIG_CONTENT`, gestionadas; se combinan, no se reemplazan. Referencias `{env:VAR}` y `{file:ruta}` dentro de la config.
- **Reconocer:** qué capas existen; las referencias `{file:...}` apuntan a un archivo que puede contener un secreto (registrar la ruta y aplicar CK-017/CK-020; nunca el valor).
- **Alcance del agente:** la capa de mayor precedencia gana por campo.
- **Falsos positivos:** FP-005.
- **Fuente:** [I].

### CK-050 · Plugins y dependencias de opencode · típico C (configurado)
- **Dónde:** `.opencode\plugins\`, `~/.config/opencode/plugins/`, clave `plugin` (paquetes npm), `.opencode\package.json`. opencode ejecuta `bun install` al arrancar para las dependencias declaradas.
- **Reconocer:** archivos de plugin y entradas `plugin`; un plugin o dependencia es código que se ejecuta al arrancar. Eventos que pueden aparecer: `tool.execute.before`, `permission.asked`, `shell.env`.
- **Alcance del agente:** código con los permisos del usuario. `shell.env` puede añadir variables al shell del agente y del usuario.
- **Falsos positivos:** ninguno propio.
- **Fuente:** [I].

### CK-051 · Servidores MCP de opencode · típico C (configurado)
- **Dónde:** clave `mcp` en la config, `type: local|remote`, `environment` del servidor local; tokens OAuth en `%USERPROFILE%\.local\share\opencode\mcp-auth.json` (ver CK-029).
- **Reconocer:** servidores y tipo; solo nombres de variables en `environment`.
- **Alcance del agente:** un servidor local es un programa con el acceso del usuario. Herencia de entorno **no documentada**.
- **Falsos positivos:** FP-005.
- **Fuente:** [I].

### CK-052 · Exposición de red y compartición de sesiones de opencode · típico P/H
- **Dónde:** scripts o accesos directos que lancen `opencode serve --hostname 0.0.0.0` (expone red; la documentación indica fijar `OPENCODE_SERVER_PASSWORD`); páginas de compartir sesiones. El valor por defecto de compartir **no se verificó** (la página `/docs/share/` devolvió 404).
- **Reconocer:** buscar `opencode serve` y `--hostname` en scripts (`rg -l`); presencia/ausencia de `OPENCODE_SERVER_PASSWORD` (nombre, no valor).
- **Alcance del agente:** riesgo de acceso remoto o de exfiltración de la conversación. Sin verificar en Windows.
- **Falsos positivos:** ninguno propio.
- **Fuente:** [I] para `serve`; el resto **por verificar**.

## H. Scripts de despliegue, CI e infraestructura

### CK-053 · Scripts de despliegue y operaciones · típico P/H
- **Dónde:** `deploy.sh`, `deploy.ps1`, `publish.ps1`, `release.*`, `rollback.*`, `migrate.*`, `scripts\`, `bin\`, `Makefile`, `justfile`, `Taskfile.yml`.
- **Reconocer:** por nombre; clasificar por lo que apuntan: entorno de producción, borrado (`drop`, `delete`, `rm -rf`, `destroy`, `--force`), comandos de CLIs de CK-004 y CK-023. Si el script contiene una credencial literal, se reporta además como CK-004 a CK-007.
- **Alcance del agente:** un script que el agente puede ejecutar usa las credenciales del usuario (comandos disponibles). BA-2.
- **Falsos positivos:** scripts de desarrollo local que solo tocan `localhost` (FP-004).
- **Fuente:** [G⚑].

### CK-054 · Workflows de CI/CD · típico C/P
- **Dónde:** `.github\workflows\*.yml`, `.gitlab-ci.yml`, `azure-pipelines.yml`, `Jenkinsfile`, `.circleci\config.yml`.
- **Reconocer:** secretos literales en el YAML (el problema real); referencias `${{ secrets.NOMBRE }}` son solo nombres (FP-005); pasos que despliegan a producción; permisos amplios del token del workflow.
- **Alcance del agente:** el agente puede editar el workflow (BA-1/BA-5, edición pide aprobación en modo Manual) y así ejecutar pasos con los secretos del repositorio al subir cambios (por verificar si aplica al flujo de Alex).
- **Falsos positivos:** FP-005.
- **Fuente:** [G⚑].

### CK-055 · Manifiestos de infraestructura y Kubernetes con secretos · típico C/P
- **Dónde:** `*.yaml` de Kubernetes con `kind: Secret` (valores en base64: no es cifrado), `values.yaml` de Helm, `*.tf`, `Pulumi.*.yaml`.
- **Reconocer:** `rg -l 'kind: Secret'`; cualquier campo `data:`/`stringData:`.
- **Alcance del agente:** BA-1/BA-5.
- **Falsos positivos:** FP-001, FP-003, FP-004.
- **Fuente:** [G⚑].

### CK-056 · Scripts de ciclo de vida y tareas del editor · típico P/H
- **Dónde:** `package.json` (`scripts`: `postinstall`, `prepare`, `preinstall`), `.vscode\tasks.json`, `.vscode\launch.json`, `*.csproj` (eventos `PreBuild`/`PostBuild`), `pyproject.toml` (scripts), `.pre-commit-config.yaml`.
- **Reconocer:** claves de scripts que ejecutan comandos de red o descargas; se ejecutan solos al instalar o compilar.
- **Alcance del agente:** el agente suele ejecutar `npm install`/`build`, que dispara esos scripts con los permisos del usuario. BA-2.
- **Falsos positivos:** scripts estándar de compilación (FP-008 en `node_modules`).
- **Fuente:** [G⚑].

## I. Registros, historial y datos del agente

> **ADVERTENCIA.** Estos archivos pueden contener valores de secretos en texto plano. En el oráculo solo se anotan existencia, tamaño, fecha y ACL. Nunca abrirlos ni listar su contenido.

### CK-057 · Transcripciones de Claude Code · típico C
- **Dónde:** `%USERPROFILE%\.claude\projects\<proyecto>\<sesion>.jsonl`, `...\<sesion>\subagents\`, `...\<sesion>\tool-results\`. Si existe `CLAUDE_CONFIG_DIR`, esa es la base.
- **Reconocer:** existencia, tamaño, fecha de la más antigua frente a `cleanupPeriodDays` (por defecto 30 días); variable `CLAUDE_CODE_SKIP_PROMPT_HISTORY=1` evita escribirlas.
- **Alcance del agente:** texto plano sin cifrar, "OS file permissions are the only protection"; si una herramienta lee un `.env` o un comando imprime una credencial, queda escrita en la transcripción [I]. Fase 2 las usará para el eje "observado", en memoria y solo metadatos.
- **Falsos positivos:** ninguno propio.
- **Fuente:** [I].

### CK-058 · Otros datos de Claude Code: historial, copias y cachés · típico C
- **Dónde:** `%USERPROFILE%\.claude\history.jsonl` (prompts escritos; se conserva hasta borrarse), `file-history\`, `paste-cache\`, `shell-snapshots\`, `debug\`, `session-env\`; `%TEMP%\claude\<proyecto>\<sesion>\scratchpad\`.
- **Reconocer:** existencia, tamaño, fecha, ACL.
- **Alcance del agente:** `file-history` guarda copias previas de archivos modificados (podría incluir un `.env` editado); `paste-cache` guarda pegados grandes.
- **Falsos positivos:** ninguno propio.
- **Fuente:** [I].

### CK-059 · Datos y base de sesiones de opencode · típico C
- **Dónde:** `%USERPROFILE%\.local\share\opencode\`: `opencode.db` (SQLite con sesiones y mensajes), `log\opencode.log`, `snapshot\`, `auth.json`, `mcp-auth.json`. `opencode db path` o `OPENCODE_DB` cambian la ubicación de la base.
- **Reconocer:** existencia, tamaño, fecha, ACL. Retención no documentada; esquema no verificado. La página de enterprise afirma "OpenCode does not store your code or context data", lo que parece contradecirse con `opencode.db`: sin resolver.
- **Alcance del agente:** BA-1/BA-2. `auth.json` y `mcp-auth.json` se reportan además como CK-029.
- **Falsos positivos:** ninguno propio.
- **Fuente:** [I].

### CK-060 · Volcados de memoria y snapshots de depuración · típico C/P
- **Dónde:** `*.heapsnapshot` (de `/heapdump` de Claude Code), `*.dmp`, `*.mdmp`, `core`, `hs_err_pid*.log`.
- **Reconocer:** extensión y nombre. Contienen conversación y credenciales que el proceso tenía en memoria y no se limpian solos [I].
- **Alcance del agente:** BA-1/BA-5.
- **Falsos positivos:** volcados de tests (FP-003).
- **Fuente:** [I] para `.heapsnapshot`; [G⚑] para los demás.

## J. Git y repositorio

### CK-061 · Remotos de Git con credenciales embebidas · típico C
- **Dónde:** `.git\config` (sección `[remote]`, campo `url`), `~/.gitconfig`.
- **Reconocer:** una URL `https://usuario:token@host/...`. Verificar con `rg -l 'https?://[^/\s:@]+:[^/\s@]+@' .git/config` (solo ruta). `git remote -v` imprime el valor: **no usarlo** si la URL lleva credencial.
- **Alcance del agente:** BA-1/BA-5; el agente suele ejecutar `git`, y el remoto autentica sin preguntar.
- **Falsos positivos:** FP-005 (`https://github.com/...` sin credencial).
- **Fuente:** [G⚑].

### CK-062 · Secretos versionados y `.gitignore` insuficiente · típico C/P
- **Dónde:** archivos de CK-017 a CK-022 que estén **rastreados** por Git (`git ls-files` imprime solo nombres); `.gitignore` que no cubre `.env*`, claves, `*.pfx`, volcados; historial de commits que contuvo un secreto ya borrado (sigue en el historial).
- **Reconocer:** `git ls-files | rg -i "(\.env|\.pem|\.key|id_rsa|secret|credential)"` (solo nombres); `git check-ignore -v <ruta>` indica qué regla ignora un archivo, o ninguna. Revisar el historial se hace con rutas de archivo (`git log --all --name-only`), no con diffs.
- **Alcance del agente:** el agente puede leer el historial local con `git log -p`. Un secreto ya publicado en un remoto debe tratarse como comprometido.
- **Falsos positivos:** FP-001, FP-003.
- **Fuente:** [G⚑].

### CK-063 · Hooks de Git activos · típico C/P
- **Dónde:** `.git\hooks\` (archivos sin extensión `.sample`), `core.hooksPath` en la config de Git.
- **Reconocer:** archivos ejecutables sin `.sample`; la clave `core.hooksPath` (que puede apuntar fuera del repo).
- **Alcance del agente:** corren en cada `git commit`/`push` con los permisos del usuario, también cuando los dispara el agente.
- **Falsos positivos:** FP-009 (`*.sample`).
- **Fuente:** [G⚑].

### CK-064 · Submódulos y árboles de trabajo que apuntan fuera del repo · típico P
- **Dónde:** `.gitmodules`, `.git` que sea un archivo (no una carpeta) con `gitdir:` a otra ruta (worktrees), `.git\worktrees\`.
- **Reconocer:** destino de cada submódulo/worktree y si queda fuera del directorio de trabajo.
- **Alcance del agente:** pueden ampliar el alcance sin ser un symlink. Cómo los trata cada agente: **por verificar**.
- **Falsos positivos:** ninguno propio.
- **Fuente:** [G⚑].

## K. Alcance de rutas y sistema de archivos

### CK-065 · Symlinks y junctions que salen del repo · típico C/P
- **Dónde:** cualquier carpeta del repo. Windows: junctions (`mklink /J`) y symlinks (`mklink /D`, `mklink`); POSIX: enlaces simbólicos.
- **Reconocer:** Windows `Get-ChildItem -Force -Recurse | Where-Object LinkType | Select FullName, LinkType, Target`; POSIX `find <raiz> -type l -printf '%p -> %l\n'`. Anotar destino y si sale del repo; detectar ciclos.
- **Alcance del agente:** Claude Code comprueba ambas rutas (la pedida y la resuelta), también junctions de Windows; qué hace con un enlace que sale del directorio de trabajo no se verificó. opencode: no verificado. Un enlace que sale del alcance no hace inalcanzable el destino: lo hace alcanzable por otro camino.
- **Falsos positivos:** enlaces dentro de `node_modules\.bin` y `.venv` (FP-008).
- **Fuente:** [I] sobre Claude Code; [G⚑] sobre comandos.

### CK-066 · Directorios adicionales concedidos al agente · típico C/P
- **Dónde:** `permissions.additionalDirectories` en settings (Claude Code); opción de línea de comandos `--add-dir` (efímera, **no legible estáticamente**); regla `external_directory` (opencode); unidades mapeadas aconsejadas con `--add-dir Z:\`.
- **Reconocer:** valores de `additionalDirectories` y reglas `external_directory: allow`. Evaluar a dónde apuntan (home, raíz de unidad, carpeta de claves).
- **Alcance del agente:** BA-1 (lectura libre en esos directorios), BA-5. Quita la aprobación que el agente pediría fuera del directorio de trabajo.
- **Falsos positivos:** ninguno propio.
- **Fuente:** [I].

### CK-067 · Rutas de red (UNC) y unidades mapeadas · típico P
- **Dónde:** `\\servidor\recurso`, unidades mapeadas (`net use`, `Get-PSDrive -PSProvider FileSystem`), puntos de montaje de red POSIX.
- **Reconocer:** unidades con `DisplayRoot` que empiece por `\\`; referencias UNC en scripts y configs.
- **Alcance del agente:** Claude Code pide confirmación para comandos con rutas UNC porque acceder a una ruta de red puede enviar las credenciales de Windows al host nombrado; las rutas UNC no se aceptan como directorios de trabajo. Una unidad mapeada con letra amplía el alcance sin figurar en archivos.
- **Falsos positivos:** ninguno propio.
- **Fuente:** [I].

### CK-068 · Carpetas sincronizadas con la nube · típico P
- **Dónde:** `%USERPROFILE%\OneDrive*`, Dropbox, Google Drive, iCloud Drive; el proyecto está deliberadamente en `C:\dev\AgentReach`, fuera de OneDrive (memory.md).
- **Reconocer:** la ruta del repo o de sus carpetas con secretos cae bajo una raíz sincronizada.
- **Alcance del agente:** un secreto en una carpeta sincronizada existe también en la nube y en otros equipos de la cuenta; el agente de otro equipo podría llegar a él. Qué hace cada agente con archivos "solo en la nube" (marcador de OneDrive): por verificar.
- **Falsos positivos:** ninguno propio.
- **Fuente:** [G⚑].

### CK-069 · Directorio de trabajo demasiado amplio · típico C/P
- **Dónde:** el agente se lanza desde `%USERPROFILE%`, la raíz de una unidad (`C:\`), `C:\dev` (que contiene varios repos) o un directorio padre de varios proyectos.
- **Reconocer:** desde el directorio de lanzamiento (acceso directo de terminal o de Visual Studio, perfil de Windows Terminal, scripts de arranque). La carpeta de trabajo define qué lee el agente libremente (BA-1).
- **Alcance del agente:** un directorio padre incluye los secretos de todos los repos hijos; es la causa típica de "acceso a archivos ajenos a la tarea".
- **Falsos positivos:** ninguno propio.
- **Fuente:** [I] sobre el efecto del directorio de trabajo; la forma de lanzarse **por verificar** en el entorno de Alex (incluye Visual Studio).

### CK-070 · Permisos del SO demasiado abiertos sobre archivos sensibles · típico C
- **Dónde:** cualquier archivo de CK-001 a CK-029 y CK-057 a CK-060.
- **Reconocer:** Windows: ACL con `Everyone`, `Users`, `Authenticated Users` o `BUILTIN\Users` con lectura (R, RX, M, F) sobre una clave privada o archivo de credenciales; POSIX: modo distinto de 600 en claves (p. ej. 644 o 664), grupo con lectura. Comando: ver sección 0.4.
- **Alcance del agente:** si el agente corre como otro usuario o en un contenedor, estos permisos determinan si lo lee. La investigación no dice nada sobre ACL de `~/.claude` ni de las transcripciones.
- **Falsos positivos:** archivos que Windows hereda con la ACL normal del perfil de usuario (propietario, `SYSTEM`, `Administrators`) no son hallazgo.
- **Fuente:** [G⚑]; la investigación indica solo que los permisos del SO son la única protección de las transcripciones.

## L. Falsos positivos conocidos

Un falso positivo **se reporta con nota, no se omite en silencio**, y toda supresión debe quedar visible (propuesta de arquitectura, Q4; pendiente de que Alex confirme). En el oráculo se registran como "FP" con su ID para poder medir cuántos produce el núcleo.

| ID | Qué es | Cómo reconocerlo | Items que suele disparar |
|---|---|---|---|
| FP-001 | Archivos de plantilla de variables (`.env.example`, `.env.sample`, `.env.template`, `.env.dist`, `*.example`, `*.sample`, `*.tfvars.example`, `appsettings.Example.json`) | Sufijo de plantilla; valores vacíos, `changeme` o nombres de variable sin valor | CK-017, 018, 020, 055 |
| FP-002 | Claves de ejemplo de la documentación del proveedor (por ejemplo las claves de ejemplo publicadas por AWS, que contienen la palabra `EXAMPLE`) | Aparecen en README, docs o tests; incluyen `EXAMPLE` en el valor; coinciden con ejemplos públicos | CK-001, 005, 007 |
| FP-003 | Fixtures, mocks y datos de prueba (`tests\fixtures`, `__mocks__`, `testdata`, `spec`, `samples`) | Carpeta de pruebas; secretos con aspecto falso; marcador canario del repo de pruebas | casi todos |
| FP-004 | Valores de marcador de posición o de desarrollo local (`changeme`, `xxx`, `<TOKEN>`, `your-key-here`, `password`, `postgres`, `localhost`) | Valor evidente de relleno; host local | CK-007, 008, 011, 018, 019, 053 |
| FP-005 | Referencia a un secreto sin valor (`${{ secrets.X }}`, `${VAR}`, `{env:VAR}`, `$env:VAR`, `_authToken=${NPM_TOKEN}`) | Sintaxis de sustitución en lugar de un valor | CK-004, 025 a 027, 033, 046, 049, 054, 061 |
| FP-006 | Material público: claves públicas (`.pub`), `known_hosts`, certificados sin clave privada | Extensión y encabezado `PUBLIC KEY`/`CERTIFICATE` | CK-013 a 016 |
| FP-007 | Sumas de verificación y hashes de integridad (`integrity: sha512-...`, `package-lock.json`, `Cargo.lock`, hashes de commits) | Archivos de bloqueo; campos `integrity`, `hash`, `checksum` | cadenas largas de aspecto aleatorio |
| FP-008 | Código de terceros: `node_modules`, `.venv`, `vendor`, `site-packages`, `dist`, `build` | Carpeta de dependencias o de salida de compilación | CK-015, 022, 056, 065 |
| FP-009 | Hooks de ejemplo de Git (`.git\hooks\*.sample`) | Extensión `.sample` | CK-063 |
| FP-010 | Nombres que coinciden con el patrón pero no son secretos (`KEY` como clave de diccionario o traducción, `token` como pieza de un analizador, `PATH`, `KEYBOARD_LAYOUT`) | Contexto del nombre; ausencia de valor con forma de credencial | CK-011, 030 |
| FP-011 | Los documentos y fixtures del propio proyecto AgentReach que **mencionan** nombres o prefijos de secretos para explicarlos | Rutas bajo `_bmad-output\`, `docs\`, `tests\fixtures\` del propio repo | CK-001 a 012, 040 |
| FP-012 | Archivos de configuración o de contexto del agente vacíos o inocuos (`settings.json` con `{}`, `CLAUDE.md` solo con convenciones de estilo, skills legítimos de BMAD en `.claude\`) | Contenido sin reglas ni órdenes; origen conocido | CK-034 a 038, 041, 045, 048 |

## M. Matriz resumida: qué cambia el alcance del agente

| Mecanismo | Claude Code | opencode |
|---|---|---|
| Reglas de permisos | CK-041 (deny gana, BA-3) | CK-048 (última coincidencia gana, BA-5) |
| Modo/aprobación | CK-042 | agentes `build`/`plan` (CK-037, CK-048) |
| Sandbox | CK-043 (no existe en Windows nativo) | no documentado |
| Política central | CK-044 | `%ProgramData%\opencode` (CK-048/049) |
| Código que corre con acceso completo | hooks CK-045, MCP stdio CK-046 | plugins CK-050, MCP local CK-051 |
| Instrucciones y skills | CK-034, 036, 037 | CK-035, 036, 037 (lee también `.claude/`, BA-7) |
| Entorno heredado | CK-047, CK-033 | no documentado |
| Directorios extra | CK-066 | `external_directory` (CK-066) |
| Enlaces y rutas | CK-065, 067 | no verificado |
| Registros | CK-057, 058 | CK-059 |

## N. Pendientes por verificar y preguntas

Resumen de lo marcado **por verificar** en este documento. Ninguna se convierte en requisito del núcleo hasta resolverse.

1. Todas las rutas de herramientas de terceros marcadas [G⚑] (AWS, Azure, gcloud, kube, Terraform, gh, Docker, npm, NuGet, Maven, Cargo, GPG, User Secrets, plataformas de despliegue): contrastar con su documentación o con una prueba en el equipo de Alex.
2. Ruta Windows de la configuración global de opencode y de skills gestionados de Claude Code.
3. Si `read: deny` de opencode cubre bash; comportamiento de `tool.execute.before`.
4. Almacén real de credenciales de Claude Code en Windows; ACL de `~/.claude`.
5. Formato de la decisión de confianza en `~/.claude.json`.
6. Qué agentes leen `.cursorrules`, `GEMINI.md`, etc.; Dev-Alex y ChatGPT no se investigaron.
7. Cómo se integra Visual Studio con Claude Code y opencode (afecta a CK-021, CK-069).
8. Comandos de solo lectura exactos para ver el estado del agente SSH y de `gh auth status` sin exponer secretos.
9. Decisión sobre ubicaciones sensibles opt-in (`~/.ssh`, `~/.aws`): sigue como propuesta.
10. Tratamiento de falsos positivos (reportar con nota, suprimir con aviso visible) y qué nivel recibe un archivo existente pero **no legible** por el usuario del agente (celda ambigua, Q3 de arquitectura).
