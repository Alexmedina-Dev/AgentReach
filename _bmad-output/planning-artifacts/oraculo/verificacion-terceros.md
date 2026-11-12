---
title: "AgentReach — Verificación de ítems [G⚑] del checklist contra documentación oficial"
type: verification
status: draft
created: 2026-11-06
updated: 2026-11-07
scope: ítems [G⚑] de checklist-oraculo.md sobre herramientas de terceros (rutas, variables, comandos de solo lectura)
method: solo web (documentación oficial del proveedor). No se ejecutó ningún comando en este equipo ni se leyó ninguna ubicación de credenciales.
note: no modifica checklist-oraculo.md. Los cambios propuestos los aplica quien mantenga el checklist.
---

# Verificación de ítems [G⚑] (terceros)

## Resumen

- Ítems evaluados: 19 (CK-001, 002, 003, 004, 005, 009, 010, 013, 014, 016, 018, 023, 024, 025, 026, 027, 028, 030, 032).
- Marca [G⚑] removible por completo: 5 (CK-009, CK-013 en la primera pasada; CK-001, CK-024 y CK-030 tras la segunda pasada del 2026-11-07).
- Verificados en parte (se divide la marca: lo verificado pasa a [I]/oficial, el resto conserva [G⚑]): 14. Ninguno quedó en "no se pudo verificar" como ítem completo; las afirmaciones sueltas no verificadas están en la sección "Verificación ampliada" (Fly.io, Railway, Bitbucket, `hosts.yml` de gh, nombres de archivos de caché de Azure y gcloud, `.netrc` general).
- Hallazgos que corrigen o precisan el checklist: ver sección "Contradictorio o matizado".
- Fuera del alcance pedido (no se intentó; conservan [G⚑]): CK-007, 008, 011, 012, 015, 019, 020, 021 (`*.pubxml`), 022, 031, 038, 039, 040, 053 a 056, 060 a 064, 068, 070.

Estados: **Verificado** = todas las afirmaciones de ruta, variable y comando del ítem están en documentación oficial; **Parcial** = una parte verificada y otra no; el detalle dice cuál.

## Tabla

| ID | Antes (checklist) | Ahora (documentación oficial) | Fuente principal | Estado | Fecha de consulta |
|---|---|---|---|---|---|
| CK-001 AWS | `~/.aws/credentials`, `config`; `%USERPROFILE%\.aws\` | Confirmado. Variables que cambian la ruta: `AWS_SHARED_CREDENTIALS_FILE`, `AWS_CONFIG_FILE`. Añade `~/.aws/cli/cache` (credenciales temporales de roles). Comando: `aws configure list-profiles` (solo nombres); `aws configure list` enmascara pero muestra los últimos 4 caracteres | docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html | Verificado (2.ª pasada: variables y prefijos confirmados, ver sección ampliada) | 2026-11-06 |
| CK-002 Azure | `~/.azure/`; cachés de token "por verificar" | Directorio = `AZURE_CONFIG_DIR`; por defecto `$HOME/.azure` (Linux/macOS) y `%USERPROFILE%\.azure` (Windows). El archivo `config` puede contener `storage.key`, `sas_token`, `connection_string`. Nombres de los archivos de caché de token: no documentados | learn.microsoft.com/en-us/cli/azure/azure-cli-configuration | Parcial | 2026-11-06 |
| CK-003 gcloud | Win `%APPDATA%\gcloud`, POSIX `~/.config/gcloud` | Confirmado. `CLOUDSDK_CONFIG` lo cambia. ADC: `%APPDATA%\gcloud\application_default_credentials.json` / `$HOME/.config/gcloud/application_default_credentials.json`. `GOOGLE_APPLICATION_CREDENTIALS` confirmada | docs.cloud.google.com/sdk/docs/configurations ; docs.cloud.google.com/docs/authentication/application-default-credentials | Parcial: estructura JSON de cuenta de servicio no verificada | 2026-11-06 |
| CK-004 Plataformas | Variables y rutas "por verificar" | Vercel: `VERCEL_TOKEN`; `auth.json` en `%APPDATA%\Roaming\xdg.data\com.vercel.cli` (Win), `~/.local/share/com.vercel.cli` (Linux); `--global-config` cambia el directorio; `.vercel/project.json`. Netlify: `NETLIFY_AUTH_TOKEN`; `config.json` en `AppData\Roaming\netlify\Config` (Win) / `.config/netlify` (Linux); `.netlify/state.json`; `NETLIFY_SITE_ID`. Railway: `RAILWAY_TOKEN` (proyecto), `RAILWAY_API_TOKEN` (cuenta); archivo de sesión no documentado. Heroku: `.netrc` (`_netrc` en Windows) como respaldo del llavero. Cloudflare: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`. Fly.io: sin confirmar | ver detalle | Parcial | 2026-11-06 |
| CK-005 Tokens de código | prefijos `ghp_`, `github_pat_`, `glpat-` | Confirmados, y hay más: `gho_`, `ghu_`, `ghs_`, `ghr_`; GitLab `gldt-`, `glrt-`, `glcbt-`, etc. Bitbucket y Azure DevOps: no verificados | docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github ; docs.gitlab.com/security/tokens/ | Parcial | 2026-11-06 |
| CK-009 kubeconfig | `~/.kube/config`; `KUBECONFIG` | Confirmado. `KUBECONFIG` es una lista (separador `:` en Linux/macOS, `;` en Windows) y se fusiona | kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/ | Verificado | 2026-11-06 |
| CK-010 Terraform | `terraform.tfstate`; `%APPDATA%\terraform.d\credentials.tfrc.json` | `credentials.tfrc.json` existe y guarda el token en texto plano; su carpeta no está en la documentación consultada. El estado se guarda en texto plano con los secretos. Config de CLI: `%APPDATA%\terraform.rc` / `~/.terraformrc`; `TF_CLI_CONFIG_FILE`; `TF_DATA_DIR` (por defecto `.terraform`) | developer.hashicorp.com/terraform/cli/commands/login ; .../cli/config/config-file ; .../cli/config/environment-variables ; .../language/state/sensitive-data | Parcial: ruta de `credentials.tfrc.json` y nombre `terraform.tfstate` sin confirmar | 2026-11-06 |
| CK-013 Claves SSH | `id_rsa`, `id_ed25519`, `id_ecdsa` en `~/.ssh` / `%USERPROFILE%\.ssh` | Confirmado. Lista oficial por defecto: `id_rsa`, `id_ecdsa`, `id_ecdsa_sk`, `id_ed25519`, `id_ed25519_sk`, `id_mldsa44_ed25519` | man.openbsd.org/ssh_config ; man.openbsd.org/ssh-add ; learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_keymanagement | Verificado | 2026-11-06 |
| CK-014 SSH config y agente | `~/.ssh/config`, `known_hosts`, `authorized_keys`; servicio "OpenSSH Authentication Agent"; `SSH_AUTH_SOCK`; comando "por verificar" | Confirmados `~/.ssh/config`, `known_hosts`, `authorized_keys`, `SSH_AUTH_SOCK`. Servicio de Windows: `ssh-agent` (el nombre para mostrar no aparece). `ssh-add -l` = huellas (no claves); `ssh-add -L` = claves públicas. Windows añade `C:\ProgramData\ssh` (claves de host) y `administrators_authorized_keys` | man.openbsd.org/ssh-add ; man.openbsd.org/sshd ; learn.microsoft.com/...openssh_keymanagement | Parcial: nombre para mostrar del servicio y comportamiento de `ssh-add -l` en Windows no documentados | 2026-11-06 |
| CK-016 GPG | `~/.gnupg/`; Windows "por verificar" | `~/.gnupg` por defecto; `GNUPGHOME` o `--homedir` lo cambian; `private-keys-v1.d/` lo usa gpg-agent. Ruta de Windows (`%APPDATA%\gnupg`): no documentada | gnupg.org/documentation/manuals/gnupg/GPG-Configuration.html ; .../Agent-Configuration.html | Parcial | 2026-11-06 |
| CK-018 User Secrets | `%APPDATA%\Microsoft\UserSecrets\<id>\secrets.json`; `~/.microsoft/usersecrets/<id>/secrets.json`; `UserSecretsId` | Confirmado exacto. Sin cifrado. **`dotnet user-secrets list` imprime los valores**: no es comando permitido | learn.microsoft.com/en-us/aspnet/core/security/app-secrets | Parcial: otros archivos del ítem (`web.config`, `wp-config.php`...) fuera de alcance | 2026-11-06 |
| CK-023 gh | `%APPDATA%\GitHub CLI\hosts.yml`; `~/.config/gh/hosts.yml`; `gh auth status` "no imprime el token" | Directorio: `GH_CONFIG_DIR` > `$XDG_CONFIG_HOME/gh` > `$AppData/GitHub CLI` (Windows) > `$HOME/.config/gh`. Token en el almacén del sistema; si falla, texto plano. El nombre `hosts.yml` no aparece en la documentación consultada. `gh auth status` oculta el token salvo `--show-token`, pero **refresca tokens por defecto** (usar `--no-refresh`) | cli.github.com/manual/gh_help_environment ; .../gh_auth_status ; .../gh_auth_login | Parcial | 2026-11-06 |
| CK-024 Docker | `~/.docker/config.json`; `auths` base64; `credsStore` | Confirmado. `%USERPROFILE%\.docker\config.json`; `auths` en base64 sin almacén; `credsStore`, `credHelpers`; en Windows el ayudante por defecto es `wincred`. `DOCKER_CONFIG`: no aparece | docs.docker.com/reference/cli/docker/login/ | Verificado (2.ª pasada: `DOCKER_CONFIG`) | 2026-11-06 |
| CK-025 npm | `~/.npmrc`, `.npmrc` de proyecto | Confirmado: proyecto, usuario `$HOME/.npmrc`, global `$PREFIX/etc/npmrc`, incorporado. Variable: `npm_config_userconfig` (sin distinguir mayúsculas, así que `NPM_CONFIG_USERCONFIG` vale). `_authToken` va con ámbito de registro `//host/:_authToken`; admite `${VAR}`. Yarn y pnpm: no verificados | docs.npmjs.com/cli/v10/configuring-npm/npmrc ; .../using-npm/config | Parcial | 2026-11-06 |
| CK-026 pip, uv, twine | `pip.ini` en `%APPDATA%\pip\` | pip confirmado: Windows `%APPDATA%\pip\pip.ini` (más `%HOME%\pip\pip.ini` heredado y `C:\ProgramData\pip\pip.ini`); Unix `~/.config/pip/pip.conf` y `~/.pip/pip.conf`; `PIP_CONFIG_FILE`. `.pypirc`, `uv.toml`, `UV_PUBLISH_TOKEN`, `TWINE_PASSWORD`: no verificados | pip.pypa.io/en/stable/topics/configuration/ | Parcial | 2026-11-06 |
| CK-027 NuGet, Maven, Cargo | rutas de los cuatro | NuGet: `%appdata%\NuGet\NuGet.Config`; Linux/macOS `~/.nuget/NuGet/NuGet.Config` (CLI .NET) o `~/.config/NuGet/NuGet.Config` (Mono, nuget.exe). Maven: `${user.home}/.m2/settings.xml`; `<password>` puede ir cifrada. Cargo: `$CARGO_HOME/credentials.toml` (`~/.cargo` o `%USERPROFILE%\.cargo`), también `credentials` sin extensión; `CARGO_REGISTRY_TOKEN`. Gradle: no verificado | learn.microsoft.com/en-us/nuget/consume-packages/configuring-nuget-behavior ; maven.apache.org/settings.html ; doc.rust-lang.org/cargo/reference/config.html | Parcial: Gradle y `ClearTextPassword` sin verificar | 2026-11-06 |
| CK-028 Git, netrc, Credential Manager | `~/.git-credentials`, `~/.netrc`, `cmdkey /list` | `~/.git-credentials` y `$XDG_CONFIG_HOME/git/credentials` (o `~/.config/git/credentials`), en texto plano. `cmdkey /list` lista usuarios y credenciales; documentado que las contraseñas no se muestran una vez guardadas. `_netrc` en Windows solo confirmado por Heroku. `git config credential.helper`: no verificado aquí | git-scm.com/docs/git-credential-store ; learn.microsoft.com/en-us/windows-server/administration/windows-commands/cmdkey ; devcenter.heroku.com/articles/heroku-cli | Parcial | 2026-11-06 |
| CK-030 Registro | `HKCU\Environment`; `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment` | HKLM confirmada. HKCU no aparece en la documentación consultada. `Get-ChildItem Env:` imprime valores (el ejemplo oficial los muestra) | learn.microsoft.com/en-us/windows/win32/procthread/environment-variables ; .../powershell/.../about_environment_variables | Verificado (2.ª pasada: HKCU confirmado) | 2026-11-06 |
| CK-032 Variables que apuntan | lista de nombres | Confirmadas: `GOOGLE_APPLICATION_CREDENTIALS`, `AWS_SHARED_CREDENTIALS_FILE`, `KUBECONFIG`, `SSH_AUTH_SOCK`, `NPM_CONFIG_USERCONFIG` (= `npm_config_userconfig`). Faltan en el checklist: `AWS_CONFIG_FILE`, `AZURE_CONFIG_DIR`, `CLOUDSDK_CONFIG`, `GH_CONFIG_DIR`, `GNUPGHOME`, `TF_CLI_CONFIG_FILE`, `TF_DATA_DIR`, `PIP_CONFIG_FILE`, `CARGO_HOME`, `NUGET_COMMON_APPLICATION_DATA`, `VERCEL_TOKEN`... | las de cada herramienta | Parcial (las de terceros ya verificadas) | 2026-11-06 |

## Verificación ampliada (segunda pasada, 2026-11-07)

Alcance: las afirmaciones que la primera pasada dejó sin confirmar. Cada fila trae ruta en Windows, ruta en Linux/macOS, qué guarda, fuente y fecha de consulta. Estados: **Verificada** (la página oficial lo dice), **Parcial** (la página oficial confirma una parte), **No verificada** (no hay documentación oficial en lo consultado; el dato, si aparece, viene de fuentes no oficiales y se marca como tal). Fecha de consulta de todas las filas: 2026-11-07.

| ID | Afirmación | Windows | Linux/macOS | Qué guarda | Fuente | Estado |
|---|---|---|---|---|---|---|
| CK-001 | Variables de credenciales de AWS CLI | `setx`/`$Env:` con `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_PROFILE` | `export` de las mismas | Clave de acceso, clave secreta, token de sesión temporal, nombre de perfil | docs.aws.amazon.com/cli/v1/userguide/cli-configure-envvars.html | Verificada |
| CK-001 | Prefijos de identificadores de AWS | igual | igual | `AKIA` = clave de acceso; `ASIA` = clave temporal (STS, el servicio de tokens temporales de AWS), "única solo en combinación con la clave secreta y el token de sesión" | docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html | Verificada |
| CK-001 | Historial de comandos de AWS CLI (hallazgo nuevo) | `%USERPROFILE%\.aws\cli\history\history.db` (la página da `~/.aws/cli/history/history.db`; el equivalente de Windows se deduce del resto de la página, no está escrito) | `~/.aws/cli/history/history.db` | Historial de comandos, solo si la función `cli_history` está activa; `AWS_CLI_HISTORY_FILE` cambia la ruta | docs.aws.amazon.com/cli/v1/userguide/cli-configure-envvars.html | Parcial (ruta de Windows deducida) |
| CK-002 | Variables de Azure CLI | `AZURE_{sección}_{nombre}` en mayúsculas (ejemplos oficiales `AZURE_CORE_OUTPUT`, `AZURE_DEFAULTS_LOCATION`) | igual | Valores por defecto. `AZURE_CLIENT_*` no aparece en la página | learn.microsoft.com/en-us/cli/azure/azure-cli-configuration | Parcial (patrón verificado; `AZURE_CLIENT_*` no) |
| CK-002 | Archivos de caché de token de Azure CLI | `%USERPROFILE%\.azure\msal_token_cache.json` y `azureProfile.json` | `~/.azure/msal_token_cache.bin` o `.json` y `azureProfile.json` | Tokens y cuentas/suscripciones. Solo hay fuentes no oficiales (incidencias del repositorio github.com/Azure/azure-cli): no confirmado por la documentación del fabricante | github.com/Azure/azure-cli/issues/23911 (no oficial en sentido de manual) | No verificada en documentación oficial |
| CK-003 | Estructura del JSON de cuenta de servicio de Google | `%APPDATA%\gcloud\...` solo para ADC; la clave es un archivo que el usuario guarda donde quiera | igual | Campos `type` ("service_account"), `project_id`, `private_key_id`, `private_key`, `client_email` | docs.cloud.google.com/iam/docs/keys-create-delete | Verificada |
| CK-003 | Dónde guarda `gcloud auth login` | `%APPDATA%\gcloud` | `~/.config/gcloud` | "Los archivos de credenciales" en el directorio de configuración; nombres `credentials.db` y `access_tokens.db` no aparecen | docs.cloud.google.com/sdk/docs/authorizing | Parcial (directorio sí, nombres de archivo no) |
| CK-004 | Heroku `HEROKU_API_KEY` | `HEROKU_API_KEY` tiene precedencia sobre el llavero y sobre `_netrc` | idem sobre `~/.netrc` | Clave de la API de Heroku | devcenter.heroku.com/articles/authentication | Verificada |
| CK-004 | Fly.io | No documentado | No documentado | La página de `fly auth token` solo muestra `-t, --access-token`; `FLY_API_TOKEN` y `~/.fly/config.yml` no aparecen | docs.fly.io/flyctl/auth-token | No verificada |
| CK-004 | Railway, archivo de sesión | No documentado | No documentado | Solo se documenta la instalación en `~/.railway/bin` y `.railway/railway.ts` (configuración como código, no sesión) | docs.railway.com/guides/cli | No verificada |
| CK-004 | Cloudflare `wrangler login` | Comunidad: `%APPDATA%\xdg.config\.wrangler\config\default.toml` (incidencias de github.com/cloudflare/workers-sdk, no oficial) | Documentación (según resumen de búsqueda, página no abierta): típicamente `~/.config/.wrangler/config/default.toml` | Tokens OAuth (acceso y renovación) en un TOML de texto plano ("legacy plaintext TOML file" en la documentación de variables de entorno); `--use-keyring` los guarda cifrados | developers.cloudflare.com/workers/wrangler/system-environment-variables/ ; developers.cloudflare.com/workers/wrangler/commands/general/ | Parcial |
| CK-005 | Azure DevOps | n/a | n/a | PAT (token de acceso personal) de 84 caracteres con la firma fija `AZDO` en las posiciones 76 a 80 | learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate | Verificada |
| CK-005 | Bitbucket | n/a | n/a | La documentación de Atlassian no da prefijo. Un mensaje de la comunidad de Atlassian (no oficial, sin respuesta) cita `ATCTT3xFfGN0` (tokens de acceso), `ATATT3xFfGF0` (tokens de API) y `ATBB` (contraseñas de aplicación); Git usa el usuario literal `x-token-auth` | support.atlassian.com/bitbucket-cloud/docs/access-tokens/ ; community.atlassian.com (no oficial) | No verificada |
| CK-010 | Archivo de estado de Terraform | `terraform.tfstate` en el directorio de trabajo | igual | Estado local de cada espacio de trabajo: "By default, Terraform stores each workspace's state in a local file named `terraform.tfstate`" | developer.hashicorp.com/terraform/language/state | Verificada |
| CK-010 | Carpeta de `credentials.tfrc.json` | No documentada (la página de `terraform login` solo dice que el comando muestra dónde lo guardará); la configuración de CLI es `%APPDATA%\terraform.rc` | `~/.terraformrc` | Token de HCP Terraform/Terraform Cloud en texto plano | developer.hashicorp.com/terraform/cli/commands/login ; .../cli/config/config-file | Parcial |
| CK-016 | Carpeta de GnuPG en Windows | `%APPDATA%\gnupg` (Gpg4win, el empaquetado oficial para Windows; la guía es antigua, solo se vio el resumen de búsqueda) | `~/.gnupg` | Claves privadas, certificados, confianza y configuración | gpg4win.org/doc/en/gpg4win-compendium_28.html ; wiki.gnupg.org/TroubleShooting | Parcial |
| CK-016 | Clave de registro que cambia la carpeta (`HKCU\Software\GNU\GnuPG`) | Solo foros | n/a | No oficial | forum.gnupg.org (no oficial) | No verificada |
| CK-023 | Nombre `hosts.yml` de gh | No aparece | No aparece | `GH_CONFIG_DIR` es "el directorio donde gh guarda archivos de configuración", sin nombrar el archivo | cli.github.com/manual/gh_help_environment | No verificada |
| CK-024 | `DOCKER_CONFIG` | `%USERPROFILE%\.docker` (por defecto) | `$HOME/.docker` | "The location of your client configuration files"; la tabla de variables no da valor por defecto, la sección de configuración dice que es `.docker` en el directorio personal | docs.docker.com/reference/cli/docker/ | Verificada |
| CK-025 | Yarn | `.yarnrc.yml` en el proyecto o directorios superiores; carpeta global `${HOME}/.yarn/berry` | igual | `npmAuthToken` (token) y `npmAuthIdent` (credenciales sin cifrar). La página no dice que lea el `.yarnrc.yml` del directorio personal | yarnpkg.com/configuration/yarnrc | Parcial |
| CK-025 | pnpm | `~/AppData/Local/pnpm/config/` (`auth.ini`, `config.yaml`); `~/.npmrc` | `~/.config/pnpm/` (Linux), `~/Library/Preferences/pnpm/` (macOS), `$XDG_CONFIG_HOME/pnpm/` | `auth.ini` guarda los tokens que escriben `pnpm login` y `pnpm config set`; `//<URL>:_authToken`, `tokenHelper`, `_auth` | pnpm.io/npmrc | Verificada |
| CK-026 | `.pypirc` | Solo `$HOME/.pypirc`; no hay ruta de Windows en la especificación | `~/.pypirc` | Usuario y contraseña o token en texto plano ("this stores your password in plain text"); Twine lo busca en el directorio personal o con `--config-file` | packaging.python.org/en/latest/specifications/pypirc/ ; twine.readthedocs.io/en/stable/ | Parcial |
| CK-026 | `uv.toml` | `%APPDATA%\uv\uv.toml` | `~/.config/uv/uv.toml` | Configuración de uv (puede incluir índices) | docs.astral.sh/uv/concepts/configuration-files/ | Verificada |
| CK-026 | `UV_PUBLISH_TOKEN`, `TWINE_USERNAME`, `TWINE_PASSWORD` | variables de entorno | idem | Token o contraseña para publicar; uv usa el usuario `__token__` | docs.astral.sh/uv/reference/environment/ ; twine.readthedocs.io/en/stable/ | Verificada |
| CK-027 | Gradle | `%USERPROFILE%\.gradle\gradle.properties` | `~/.gradle/gradle.properties` | Propiedades; `GRADLE_USER_HOME` cambia la carpeta (por defecto `USER_HOME/.gradle`). Nombres de propiedades de credenciales no verificados | docs.gradle.org/current/userguide/build_environment.html | Parcial |
| CK-027 | NuGet `ClearTextPassword` | `%appdata%\NuGet\NuGet.Config` | rutas ya listadas | `Password` cifrada (solo Windows, solo misma máquina y mismo usuario) o `ClearTextPassword` sin cifrar; claves de API en `apikeys` cifradas | learn.microsoft.com/en-us/nuget/reference/nuget-config-file | Verificada |
| CK-028 | `credential.helper` de Git | n/a | n/a | Se configura con `git config [--global] credential.helper <nombre>`; ayudantes `cache` (memoria), `store` (disco, "desaconsejado"), Git Credential Manager (incluido en Git for Windows), `wincred`, `osxkeychain`, `libsecret` | git-scm.com/docs/gitcredentials | Verificada |
| CK-028 | `.netrc` fuera de Heroku | No documentado en lo consultado | No documentado | Solo Heroku lo cita | devcenter.heroku.com/articles/authentication | No verificada (como regla general) |
| CK-030 | `HKCU\Environment` | `HKEY_CURRENT_USER\Environment` | n/a | Variables de entorno de usuario: "stored in the HKEY_CURRENT_USER\Environment key"; las de equipo en `HKEY_LOCAL_MACHINE\SYSTEM\ControlSet001\Control\Session Manager\Environment` | learn.microsoft.com/en-us/dotnet/api/system.environment.setenvironmentvariable | Verificada |

Cobertura de las pendientes que no se pudieron comprobar:

- Los nombres exactos de los archivos de caché de token de Azure CLI y de `credentials.db` de gcloud solo aparecen en fuentes no oficiales; no se afirman.
- `*.tfvars`, Pulumi, Yarn en el directorio personal, URLs con credenciales en pip, nombres de propiedades de credenciales de Gradle, `web.config` y `wp-config.php` (CK-018): sin fuente oficial hallada o no consultados.

## Contradictorio o matizado

1. **CK-023, `gh auth status` no es estrictamente de solo lectura.** La página oficial dice que por defecto refresca los tokens caducados o por caducar; `--no-refresh` lo evita. Para el oráculo: `gh auth status --no-refresh`. Además `--show-token` imprime el token: nunca usarlo. Fuente: cli.github.com/manual/gh_auth_status.
2. **CK-023, ruta de `gh` en Windows.** El checklist da `%APPDATA%\GitHub CLI`, pero `GH_CONFIG_DIR` y `XDG_CONFIG_HOME` tienen precedencia en cualquier sistema; si `XDG_CONFIG_HOME` está definida en Windows, la ruta cambia. Fuente: cli.github.com/manual/gh_help_environment.
3. **CK-018, comando peligroso cercano.** `dotnet user-secrets list` imprime claves y valores. El oráculo debe limitarse a existencia, tamaño y ACL del `secrets.json`. Fuente: learn.microsoft.com/en-us/aspnet/core/security/app-secrets.
4. **CK-001, `aws configure list` no oculta del todo.** Enmascara con asteriscos pero deja visibles los últimos 4 caracteres de la clave de acceso y de la secreta (ejemplo oficial `****************ABCD`). Es cuestionable para la regla "nunca mostrar valores". Preferir `aws configure list-profiles`. Fuente: docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html.
5. **CK-002, el comando típico de Azure expone secretos.** `az account get-access-token` imprime el token de acceso. Y el archivo `config` puede traer `storage.key`/`sas_token`/`connection_string` en texto plano. Fuente: learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli ; .../azure-cli-configuration.
6. **CK-010, la ruta del checklist no se confirma.** `credentials.tfrc.json` existe y es texto plano, pero la documentación consultada no da `terraform.d`. En cambio hay otro archivo que el checklist no menciona: `terraform.rc`/`.terraformrc` (configuración del CLI, puede incluir `credentials` en HCL; esto último no confirmado). Fuente: developer.hashicorp.com/terraform/cli/config/config-file.
7. **CK-013, lista incompleta.** El checklist cita tres nombres; la documentación oficial lista seis (añade `id_ecdsa_sk`, `id_ed25519_sk`, `id_mldsa44_ed25519`).
8. **CK-014, el agente en Windows.** La documentación de Microsoft dice que el agente guarda las claves "dentro de un contexto de seguridad asociado a tu cuenta de Windows" y recomienda borrar el archivo privado tras añadirlo al agente. Consecuencia: un usuario puede tener la clave solo en el agente y no en `~/.ssh`. La ausencia del archivo no prueba que no haya acceso. Fuente: learn.microsoft.com/...openssh_keymanagement.
9. **CK-004, Vercel en Windows.** Ruta atípica: `%APPDATA%\Roaming\xdg.data\com.vercel.cli`. Un buscador que asuma `~/.config` no la encuentra. Fuente: vercel.com/docs/project-configuration/global-configuration.
10. **CK-027, NuGet en Linux/macOS.** Dos rutas posibles según la herramienta (`~/.nuget/NuGet` o `~/.config/NuGet`). Fuente: learn.microsoft.com/en-us/nuget/consume-packages/configuring-nuget-behavior.
11. **CK-001, historial de comandos (hallazgo nuevo).** AWS CLI puede guardar el historial de comandos en `~/.aws/cli/history/history.db` (solo si se activa `cli_history`; `AWS_CLI_HISTORY_FILE` lo mueve). El historial puede contener parámetros con secretos pasados en línea de comandos. El checklist no lo menciona. Fuente: docs.aws.amazon.com/cli/v1/userguide/cli-configure-envvars.html (2026-11-07).
12. **CK-005, Azure DevOps.** El PAT (token de acceso personal) tiene formato identificable: 84 caracteres con la firma `AZDO` en las posiciones 76 a 80. La misma página da dos fechas distintas para el fin de los PAT globales (27 de enero de 2027 y 1 de diciembre de 2026); no usar la fecha como dato. Fuente: learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate (2026-11-07).
13. **CK-025, pnpm guarda tokens en un archivo propio.** `auth.ini` en la carpeta de configuración de pnpm (`~/AppData/Local/pnpm/config/` en Windows), además de `~/.npmrc`. Un buscador que solo mire `.npmrc` lo pierde. Fuente: pnpm.io/npmrc (2026-11-07).
14. **CK-027, cifrado de NuGet solo en Windows.** La contraseña cifrada de `NuGet.Config` solo se descifra en la misma máquina y con el mismo usuario; fuera de Windows no hay cifrado. Fuente: learn.microsoft.com/en-us/nuget/reference/nuget-config-file (2026-11-07).
15. **CK-004, Cloudflare.** `wrangler login` guarda los tokens OAuth en un TOML de texto plano ("legacy plaintext TOML file"); la ruta de Windows solo está en incidencias de la comunidad. Fuente: developers.cloudflare.com/workers/wrangler/system-environment-variables/ (2026-11-07).

Ninguna afirmación del checklist quedó **refutada** de forma directa; las diferencias son omisiones, precedencias y comandos con efectos colaterales.

## Detalle por ítem

Formato: afirmación, fuente, comando de solo lectura (si existe).

### CK-001 AWS
- Archivos `credentials` y `config` en `%UserProfile%` (Windows) y `$HOME` (Unix); `AWS_CONFIG_FILE` y `AWS_SHARED_CREDENTIALS_FILE` los cambian. https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html (v1 equivalente: https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html).
- Credenciales temporales de rol en `~/.aws/cli/cache`. Misma página (v1).
- Comandos: `aws configure list-profiles` imprime solo nombres; `aws configure list` muestra el origen y valores enmascarados con últimos 4 visibles. Misma página.
- Sin confirmar: variables `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`/`AWS_SESSION_TOKEN`/`AWS_PROFILE` y prefijos `AKIA`/`ASIA`.

### CK-002 Azure
- Config en `$AZURE_CONFIG_DIR/config`; por defecto `$HOME/.azure` y `%USERPROFILE%\.azure`. https://learn.microsoft.com/en-us/cli/azure/azure-cli-configuration
- Secciones de `config` con secretos posibles: `[storage] key`, `sas_token`, `connection_string`; `[batch] access_key`. Misma página.
- La CLI genera y guarda un token de refresco (ubicación no indicada). https://learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli
- Comando de solo lectura sin secretos: no confirmado. `az account get-access-token` queda excluido.
- Sin confirmar: nombres de archivos de caché (`msal_token_cache`, `azureProfile.json`) y variables `AZURE_CLIENT_*`.

### CK-003 gcloud
- Directorio típico `~/.config/gcloud` (Linux/macOS) o `%APPDATA%\gcloud` (Windows); `CLOUDSDK_CONFIG` lo cambia; `gcloud info --format='value(config.paths.global_config_dir)'` da la ruta. https://docs.cloud.google.com/sdk/docs/configurations
- ADC en `$HOME/.config/gcloud/application_default_credentials.json` y `%APPDATA%\gcloud\application_default_credentials.json`; `GOOGLE_APPLICATION_CREDENTIALS` apunta a un JSON (clave de cuenta de servicio o federación). https://docs.cloud.google.com/docs/authentication/application-default-credentials
- La página de configuraciones no dice dónde se guardan las credenciales de `gcloud auth login`. Sin confirmar: `gcloud auth list` (no consultado).

### CK-004 Plataformas
- Vercel: `VERCEL_TOKEN` y `--token`; `--global-config` / `-Q`; `.vercel/project.json` de `vercel link`. https://vercel.com/docs/cli/global-options. `auth.json` y `config.json` en `com.vercel.cli` dentro de `XDG_DATA_HOME` (Linux `~/.local/share/com.vercel.cli`, macOS `~/Library/Application Support/com.vercel.cli`, Windows `%APPDATA%\Roaming\xdg.data\com.vercel.cli`). https://vercel.com/docs/project-configuration/global-configuration
- Railway: `RAILWAY_TOKEN` (acciones de proyecto), `RAILWAY_API_TOKEN` (cuenta), `railway whoami`. https://docs.railway.com/guides/cli. Ubicación de sesión y de enlace: no documentadas. `railway.json`: sin confirmar.
- Netlify: `NETLIFY_AUTH_TOKEN`; `config.json` en `Library/Preferences/netlify`, `.config/netlify`, `AppData\Roaming\netlify\Config`; `.netlify/state.json` con `siteId`; `NETLIFY_SITE_ID`. https://docs.netlify.com/cli/get-started/. `netlify status`: no documentado en esa página.
- Fly.io: la documentación de `fly auth token` solo muestra `-t, --access-token`; `FLY_API_TOKEN`, `~/.fly/config.yml` y `fly.toml` sin confirmar. https://docs.fly.io/flyctl/auth-token
- Heroku: token en el llavero y, si falla, en `~/.netrc` (`_netrc` en Windows). https://devcenter.heroku.com/articles/heroku-cli. `heroku auth:whoami` listado en https://devcenter.heroku.com/articles/heroku-cli-commands; `heroku auth:token` imprime el token (excluir). `HEROKU_API_KEY`: sin confirmar.
- Cloudflare: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`; ruta de `wrangler login`: no documentada en esa página (menciona `CLOUDFLARE_AUTH_USE_KEYRING`). https://developers.cloudflare.com/workers/wrangler/system-environment-variables/

### CK-005 Prefijos
- GitHub: `ghp_`, `github_pat_`, `gho_`, `ghu_`, `ghs_`, `ghr_`; desde 2026-04-27 `ghs_` puede tener formato más largo (no asumir longitud fija). https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github
- GitLab: `glpat-` (personal, impersonación, proyecto, grupo), `gldt-`, `glrt-`, `glcbt-`, `glptt-`, `glft-`, `glagent-`, entre otros. https://docs.gitlab.com/security/tokens/

### CK-009 kubeconfig
- `$HOME/.kube/config` por defecto; `KUBECONFIG` lista de archivos, `:` en Linux/macOS y `;` en Windows; se fusionan. https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/
- `kubectl config view` oculta datos sensibles salvo con `--raw` (descripción del flag: "Display raw byte data and sensitive data"). https://kubernetes.io/docs/reference/kubectl/generated/kubectl_config/kubectl_config_view/. La página no afirma el enmascarado de forma explícita; no es comando seguro de adoptar sin prueba. Para el oráculo basta metadatos del archivo.

### CK-010 Terraform
- `terraform login` guarda el token en texto plano en `credentials.tfrc.json`. https://developer.hashicorp.com/terraform/cli/commands/login
- Estado local en texto plano con los secretos. https://developer.hashicorp.com/terraform/language/state/sensitive-data (no nombra `terraform.tfstate`).
- `terraform.rc` (`%APPDATA%`), `.terraformrc` (home), `TF_CLI_CONFIG_FILE`. https://developer.hashicorp.com/terraform/cli/config/config-file
- `TF_DATA_DIR` (por defecto `.terraform` en el directorio de trabajo). https://developer.hashicorp.com/terraform/cli/config/environment-variables
- Comando de solo lectura: no hay (no consultado). `*.tfvars` y Pulumi: sin verificar.

### CK-013 y CK-014 SSH
- Cliente: `~/.ssh/config`; `~/.ssh/known_hosts` y `known_hosts2`; `/etc/ssh/ssh_known_hosts`; claves por defecto listadas arriba. https://man.openbsd.org/ssh_config
- Servidor: `~/.ssh/authorized_keys`. https://man.openbsd.org/sshd
- `ssh-add -l` lista huellas; `-L` lista claves públicas; `SSH_AUTH_SOCK` es el socket. https://man.openbsd.org/ssh-add. Comando de solo lectura que no expone secretos: **`ssh-add -l`** (huellas). Si no hay agente sale con error, sin cambios.
- Windows: servicio `ssh-agent` (`Get-Service ssh-agent`), claves de usuario en `C:\Users\<usuario>\.ssh\`, claves de host en `C:\ProgramData\ssh`, `administrators_authorized_keys` en `C:\ProgramData\ssh\` para administradores. https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_keymanagement
- Sin confirmar: que `ssh-add -l` en Windows hable con el servicio (no documentado en lo consultado); nombre para mostrar "OpenSSH Authentication Agent". Una página del wiki de Win32-OpenSSH no devolvió contenido útil.

### CK-016 GPG
- `~/.gnupg` por defecto; `GNUPGHOME` o `--homedir` lo sustituyen. https://www.gnupg.org/documentation/manuals/gnupg/GPG-Configuration.html
- `private-keys-v1.d/`: "the directory where gpg-agent stores the private keys". https://www.gnupg.org/documentation/manuals/gnupg/Agent-Configuration.html
- Windows: no documentado en esas páginas. Comando de solo lectura sin secretos: no consultado (`gpg --list-secret-keys` muestra identificadores, no se verificó).

### CK-018 User Secrets
- Rutas exactas y `UserSecretsId`; no cifrado; "Don't write code that depends on the location or format". https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets
- `dotnet user-secrets list` imprime valores (ejemplo oficial). No usar.

### CK-023 gh
- Ver contradicciones 1 y 2. Almacén del sistema por defecto, texto plano si falla o con `--insecure-storage`; "Run `gh auth status` to see where the token is stored". https://cli.github.com/manual/gh_auth_login
- Variables: `GH_TOKEN` > `GITHUB_TOKEN` (github.com y ghe.com); `GH_ENTERPRISE_TOKEN` > `GITHUB_ENTERPRISE_TOKEN` (servidores Enterprise); `GH_CONFIG_DIR`. https://cli.github.com/manual/gh_help_environment
- Comando: `gh auth status --no-refresh` (también `--json hosts` incluye el token solo con `--show-token`). Salida con código 1 si hay problemas de autenticación.

### CK-024 Docker
- `$HOME/.docker/config.json` (Linux) y `%USERPROFILE%/.docker/config.json` (Windows); base64 sin almacén; `credsStore`; `credHelpers`; `wincred` por defecto en Windows; Docker Desktop usa el llavero. https://docs.docker.com/reference/cli/docker/login/
- `DOCKER_CONFIG`: no aparece en la página. Sin comando de solo lectura confirmado.

### CK-025 a CK-027 Gestores de paquetes
- npm: https://docs.npmjs.com/cli/v10/configuring-npm/npmrc ; https://docs.npmjs.com/cli/v10/using-npm/config (`npm whoami` solo se enlaza, sin describir).
- pip: https://pip.pypa.io/en/stable/topics/configuration/ (no cubre credenciales en `index-url`).
- NuGet, Maven, Cargo: enlaces en la tabla. NuGet: `NuGet.Config` de usuario y de equipo (`%ProgramFiles(x86)%\NuGet\Config`), configs adicionales en `%appdata%\NuGet\config\*.Config`.

### CK-028 Git y Credential Manager
- `git-credential-store`: "store your passwords unencrypted on disk, protected only by filesystem permissions". https://git-scm.com/docs/git-credential-store
- `cmdkey /list` lista; no imprime contraseñas almacenadas. https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/cmdkey

### CK-030 y CK-032 Variables
- HKLM `...\Session Manager\Environment` confirmada; HKCU `Environment`: sin fuente oficial en lo consultado. https://learn.microsoft.com/en-us/windows/win32/procthread/environment-variables
- Las variables de usuario y de equipo se escriben en el Registro desde el Panel de control. https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_environment_variables
- Listar solo nombres con `Get-ChildItem Env: | Select-Object -ExpandProperty Name` es coherente con la documentación (el cmdlet por sí solo imprime valores); `env | cut -d= -f1` (POSIX) es técnica de shell, no documentación de proveedor.

## Lista de marcas

### Pueden quitar [G⚑] por completo
- CK-009 (rutas y variable de kubeconfig).
- CK-001 (segunda pasada): variables de entorno y prefijos `AKIA`/`ASIA` verificados.
- CK-024 (segunda pasada): `DOCKER_CONFIG` verificado.
- CK-030 (segunda pasada): `HKCU\Environment` verificado.
- CK-013 (nombres de claves SSH y ubicación). Conviene ampliar la lista de nombres.

### Conservan [G⚑], pero solo en lo no verificado (dividir la marca)
Lo verificado pasa a [I]/oficial con la URL; el resto sigue como [G⚑]:
- CK-001: `AWS_ACCESS_KEY_ID` y compañía, prefijos `AKIA`/`ASIA`.
- CK-002: nombres de caché de token, variables `AZURE_CLIENT_*`, patrón `AccountKey=`.
- CK-003: estructura JSON de cuenta de servicio, `gcloud auth list`.
- CK-004: Fly.io (todo), Heroku `HEROKU_API_KEY`, Railway sesión y `railway.json`, Cloudflare ruta de `wrangler login`, `fly.toml`.
- CK-005: Bitbucket y Azure DevOps.
- CK-010: carpeta de `credentials.tfrc.json`, nombre `terraform.tfstate`, `*.tfvars`, Pulumi.
- CK-014: nombre para mostrar del servicio y `ssh-add -l` en Windows.
- CK-016: ruta de GPG en Windows y comando.
- CK-018: demás archivos de configuración (`web.config`, `wp-config.php`...).
- CK-023: nombre `hosts.yml`.
- CK-024: `DOCKER_CONFIG`.
- CK-025: Yarn (`.yarnrc.yml`, `npmAuthToken`) y pnpm.
- CK-026: `.pypirc`, `uv.toml`, `UV_PUBLISH_TOKEN`, `TWINE_PASSWORD`, URLs con credenciales.
- CK-027: Gradle (`gradle.properties`), `ClearTextPassword`.
- CK-028: `.netrc` fuera de Heroku, `git config credential.helper`.
- CK-030: `HKCU\Environment`.
- CK-032: ninguna de las de terceros; solo permanecen como [G⚑] las variables que no se verificaron en otros ítems (`NPM_CONFIG_USERCONFIG` sí quedó verificada).

### Fuera de este alcance, conservan [G⚑] sin cambios
CK-007, 008, 011, 012, 015, 019, 020, 021, 022, 031, 038, 039, 040, 053 a 056, 060 a 064, 068, 070 (no son rutas/variables/comandos de las herramientas listadas, o no se intentó).

## Efecto sobre la regla del memlog

Regla vigente: un ítem con [G⚑] solo produce potencial o hipótesis, nunca comprobado. Para los ítems divididos, la parte que pase a fuente oficial podría producir "comprobado" solo en lo que se refiere a ubicación y nombre; la existencia de credenciales dentro del archivo sigue sin leerse. La decisión de relajar la regla es de Alex.

## Limitaciones de esta verificación

- Todo se hizo con extractos de páginas web resumidos por un modelo auxiliar. Las citas literales son del resumen. Antes de convertir una fila en requisito del núcleo, abrir la URL y confirmar el texto exacto.
- Páginas con redirección (gcloud, Fly.io) se consultaron en su destino oficial (`docs.cloud.google.com`, `docs.fly.io`).
- Las versiones de la documentación son las vigentes a 2026-11-06; las rutas pueden cambiar entre versiones (p. ej. `ghs_`, NuGet).
- No se probó ningún comando. "Solo lectura" aquí significa "la documentación no dice que escriba ni imprima secretos"; la comprobación empírica queda para las pruebas contra el oráculo.
