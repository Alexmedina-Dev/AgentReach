# Proyecto de prueba de AgentReach

Sirve para comparar a AgentReach contra una auditoría de referencia (el "oráculo"). Crea, fuera del repositorio, una carpeta con **secretos falsos** y **trampas conocidas**, más un archivo `respuestas-esperadas.md` que dice qué debería (y qué no debería) reportar AgentReach en cada caso.

## Por qué hay un generador y no archivos

Los secretos falsos no se guardan en el repositorio: GitHub los bloquearía y es mala práctica. El generador los arma al ejecutarse, a partir de fragmentos, así que ningún analizador de secretos los ve en el código. Cada valor lleva un marcador canario único (`CNR001` a `CNR024`) para comprobar que ningún reporte lo filtra. Son claramente falsos, pero tienen el formato que un detector reconoce.

Todo queda dentro de la carpeta de prueba. El "home" del usuario se simula con `home-falso`: el generador no lee ni toca `~/.ssh`, `~/.aws` ni nada real del equipo.

## Uso

Requiere Python 3.12 o superior (solo biblioteca estándar) y, en Windows, `icacls` y `mklink`.

```powershell
# Generar (por defecto en C:\dev\proyecto-prueba-agentreach; fuera del repo y de OneDrive)
python pruebas\generar_proyecto_prueba.py
python pruebas\generar_proyecto_prueba.py D:\otra\carpeta

# Comprobar que todo se creó (no imprime valores)
python pruebas\generar_proyecto_prueba.py --verificar

# Limpiar: quita el permiso de lectura negado (icacls /remove:d), quita los enlaces sin seguirlos y borra la carpeta
python pruebas\generar_proyecto_prueba.py --limpiar

# Ejecutar un comando con variables de entorno FALSAS, solo para ese proceso (no se guarda nada en el sistema)
python pruebas\generar_proyecto_prueba.py --con-entorno powershell -NoLogo
```

Si la carpeta ya existe y fue generada antes, se limpia y se regenera. Si existe y no tiene el marcador `.agentreach-prueba`, el generador se niega a tocarla.

## Qué contiene

| Carpeta | Contenido |
|---|---|
| `proyecto/` | Lo que se audita: `.env` con seis secretos falsos, `.env.example` (falso positivo), `.env.production` con lectura **negada** al usuario actual, `.env.staging` con permiso normal (par de control), `.env.local` ignorado por git, configuración de Claude Code (`.claude/settings.json`, con un `deny` de lectura sobre `.env`) y de opencode (`opencode.json`, casi todo `allow`), un agente de ejemplo, un `CLAUDE.md` inofensivo (fuera del alcance del MVP, el producto mínimo viable), una carpeta `cola/` que no debe reportarse y varios falsos positivos (ejemplo de documentación de AWS, referencia `${{ secrets.X }}`, nombres como `KEY` y `tokens` en código). También: un repositorio git con tres commits (`config/servicio-rastreado.env` que git ya sigue y `config/historial.env`, añadido y luego quitado, que sigue en el historial), un remoto `origin` con usuario y clave falsos en la URL (host `.invalid`, nunca se conecta), `config/exportacion-abierta.env` con lectura concedida a Todos (Everyone) y `AGENTS.md` con una instrucción sospechosa inventada. |
| `proyecto/` (ataques a agentes) | Casos AT-01 a AT-12, todo texto inofensivo: `.cursor/rules/estilo.mdc` con caracteres Unicode invisibles (y `docs/emoji.md` como control), un hook `SessionStart` en `.claude/settings.json`, `.mcp.json` con un servidor de tipo comando, `.claude/settings.local.json` con `bypassPermissions`, `.vscode/tasks.json` con `runOn: folderOpen` y `src/estilos/notas-tipografia.txt` con un token falso de alto poder (canario `CNR023`) sin relación con la tarea. En `home-falso/Downloads/AGENTS.md` y en `home-falso/AGENTS.md` (raíz), archivos de instrucciones fuera de un proyecto. Añadidos: `.github/copilot-instructions.md` con un carácter invisible de ancho cero U+200B (AT-09), `proyecto/enlace-denegado` (junction al mismo destino) con la regla `deny Read(./enlace-denegado/**)` en `settings.local.json` (AT-11) y `enableAllProjectMcpServers: true` en `settings.json` (AT-12). |
| `trampas/` | `senuelo.py`: programa señuelo inofensivo al que apuntan los hooks, el MCP, la tarea y las trampas de git. Solo escribiría `PWNED.txt` junto a él. **Nunca se ejecuta**; el caso TR-01 exige que `trampas/PWNED.txt` no exista después de correr AgentReach. |
| `trampas-git/` | Dieciséis `.git` **simulados**, solo archivos de texto (casos GT-04 a GT-19): `core.fsmonitor`, `core.hooksPath`, filtro en `.gitattributes`, hook sin `.sample`, remoto con credencial de relleno y config de formato retorcido; controles `fsmonitor = true` y `= false` (GT-10, GT-11) y `filter=lfs` legítimo (GT-12), config retorcida con ciclo de `include` (GT-13) y claves que ejecutan un programa: `core.sshCommand`, `core.pager`, alias con `!`, `diff.external` y `gpg.program` (GT-14 a GT-18) y `gpg.program` con `log.showSignature = true` (GT-19, donde un simple `git log` ejecutaría el programa). No tienen `HEAD`, así que git no los reconoce como repositorio, y están separados del `.git` real de `proyecto/`. |
| `proyecto-ajeno/` | Hermano del proyecto, con un secreto falso ajeno a la tarea (patrón del incidente PocketOS). |
| `proyecto-opencode-sin-read/` | Control de opencode (OC-01): un `opencode.json` con solo `edit: ask`, sin regla `read`, y un `.env` falso (canario `CNR024`). Como no hay regla que cubra el archivo, rige el `ask` base de opencode y el nivel es *potencial*. |
| `destino-enlace/` | Destino de una **junction** (`proyecto/enlace-externo`) y de un enlace simbólico opcional (`proyecto/enlace-simbolico`), fuera del proyecto. |
| `home-falso/` | Home simulado: clave SSH falsa, credenciales AWS falsas, `.npmrc` con token falso, más material público (`.pub`, `known_hosts`). |

Además: `respuestas-esperadas.md` (el oráculo: ID del checklist, ruta, qué es, nivel esperado, nota esperada y por qué) y `resultado-generacion.json` (qué se pudo crear y qué no, sin valores).

## Reglas del oráculo

*Comprobado* solo si el hecho se determina con certeza y sin ambigüedad; *potencial* si no; *hipótesis* es un indicio débil. "Sin fuente verificada" limita el nivel a *potencial* solo al reconocer secretos por nombre o prefijo. Reglas nuevas del 2026-11-09:

- **Permisos heredados:** no bajan el nivel (el cálculo de permisos efectivos ya incluye la herencia). Solo bajan a *potencial* las reglas de denegar, un cálculo que no se pueda completar o un resultado ambiguo.
- **Reglas del agente (allow, ask, deny, sin sandbox):** son contexto del campo "reglas del agente" de cada hallazgo; son hallazgo propio solo si debilitan la protección. Por eso CA-01 (reglas sanas) y CA-03 (limpieza del entorno) pasan a "no se reporta", y CA-02 (sin sandbox) y CA-04 (opencode permisivo) bajan a *potencial*.
- **Un reporte por agente:** el nivel de la tabla es el de Claude Code. En opencode (pregunta 25, cerrada el 2026-11-09) un `read: allow` que cubra el archivo anula el `ask` base de `*.env`, porque gana la última regla que coincide: PP-01, PP-04, PP-05, GT-01 y PA-01 son *comprobado*; AJ-01 queda *potencial* (el `opencode.json` con `read: allow` está en `proyecto/` y no cubre `proyecto-ajeno/`), y el control OC-01, sin regla `read`, es *potencial*. Salvedad: se verificó en la documentación oficial, no en el código fuente de opencode (ver "Niveles por agente" en `respuestas-esperadas.md`).
- **Ubicaciones sensibles** (apagadas por defecto): con el interruptor apagado, HF-01, HF-03, HF-05, AT-03 y AT-10 se esperan como "no se pudo revisar", nunca como "no se reporta".
- EV-01 pasa a *hipótesis*. GT-17 y GT-18 pasaron a *potencial* y, con la pregunta 26 cerrada (fuente primaria de git verificada), vuelven a *comprobado*; `log.showSignature = true` con `gpg.program` hace que un simple `git log` ejecute el programa (GT-19). `core.sshCommand` solo corre en operaciones de red y `diff.external` solo con diffs con contenido.
- AgentReach (MVP) no ejecuta git: el historial (GT-02) se espera como "no se pudo revisar". Un enlace que sale del proyecto se reporta como enlace (EN-01, potencial) y lo de detrás se declara no revisado (EN-02: "no se reporta" como hallazgo). Un archivo que existe pero el agente no puede leer es *potencial*, nunca "no alcanzable". Un `deny` no borra el hallazgo de PP-01: añade la nota "protegido por política del agente, no por barrera del SO".

El oráculo tiene 67 casos: **48 se esperan como hallazgo (18 comprobado, 28 potencial y 2 hipótesis en Claude Code; en opencode también 18, 28 y 2, con PP-01 en lugar de AJ-01 entre los comprobados)**, 16 no deben reportarse, 1 (GT-02) sale como "no se pudo revisar", 1 (EN-03) es "no aplicable" y 1 (TR-01) es una trampa. AJ-01 cuenta entre los comprobados solo si la raíz auditada es la carpeta que contiene a los dos proyectos; con otra raíz no se reporta.

## Límites conocidos

- Las trampas de git nuevas siguen la misma regla: el valor de `core.sshCommand`, `core.pager`, el alias con `!`, `diff.external`, `gpg.program` (también con `log.showSignature`) y `core.fsmonitor` (dentro del ciclo de `include`) apunta al señuelo y solo se escribe como texto; el generador no ejecuta git sobre ellas.
- La junction no necesita administrador en la prueba hecha en esta máquina (Windows 11); el enlace simbólico sí necesita privilegio o modo desarrollador, y por eso es opcional: si falla, el oráculo lo marca como "no aplicable" y `--verificar` lo informa como aviso.
- El repositorio git usa una identidad falsa solo local (`user.name` y `user.email` en `.git/config`) y se ejecuta ignorando la configuración global y del sistema del usuario; no se toca ninguna configuración real.
- Las variables de entorno falsas (`AGENTREACH_PRUEBA_API_TOKEN`, `AGENTREACH_PRUEBA_DB_PASSWORD`) solo existen dentro del proceso que lanza `--con-entorno`; `--verificar` comprueba que no quedan en el proceso actual. No usar `setx` ni perfiles de shell.
- El permiso abierto usa `icacls /grant *S-1-1-0:(R)` (Todos) solo sobre un archivo falso; en POSIX, `chmod 666`.
- Reglas de seguridad de las trampas: el generador solo **escribe** texto; nunca ejecuta git ni el señuelo sobre ellas, no instala nada y todo queda dentro de la carpeta de prueba. Los comandos escritos en el hook, el MCP, la tarea y los `.git` simulados apuntan al señuelo; si abres `proyecto/` en Claude Code o VS Code y aceptas la confianza, esos comandos podrían correr (solo escribirían `PWNED.txt`): no la aceptes. `--verificar` comprueba que ese marcador no existe.
- Para probar las ubicaciones sensibles del usuario, hay que apuntar el "home" de AgentReach a `home-falso`.
- Si la carpeta raíz de la prueba está en uso por otro proceso (por ejemplo una terminal abierta ahí), el generador borra el contenido, conserva la raíz vacía y la reutiliza.
