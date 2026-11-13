# Segunda pasada independiente: arreglos de las historias 11b y 10b

Fecha: 2026-11-10. Nota: mi copia aislada (worktree) desapareció otra vez durante la pausa; este informe se escribe en el
repositorio principal (C:\dev\AgentReach, solo este archivo, sin tocar src ni tests, sin commit). Los casos corrieron sobre el
código del repositorio principal, que contiene los arreglos 11b/10b (se comprobó que existe `reglas_incompletas`).

## Resultados ejecutados
- `uv run pytest -q` (corrido en la copia, antes de que desapareciera): 1098 pasaron, 153 omitidas, 1 fallo esperado (xfail), 0 fallaron.
- `uv run ruff check src tests`: 4 errores, todos "imports sin ordenar" (I001) en archivos de `tests/` (por ejemplo
  `tests/reglas_no_negociables/test_sin_ejecutar_programas.py`, `test_sin_red.py`). Ninguno en `src`. Se arreglan con `ruff --fix`.
  La historia 11b dice "Ruff limpio": no es cierto ahora mismo (gravedad baja, pero rompe una puerta de calidad).
- 90 casos mínimos, cada uno en una carpeta temporal propia (fuera del repo) con un `.env` que contiene una clave falsa
  (`STRIPE_SECRET_KEY=...`) y un `--home` vacío propio. Se ejecutó `auditar()` con el medidor real de permisos de Windows
  y se anotó el nivel del `.env` por agente. Además se ejecutó la línea de comandos real (`python -m agentreach CARPETA`) sobre
  el control: sale "comprobado" y código de salida 1, igual que la biblioteca. El valor del bloque `env` del usuario
  (caso 17) no aparece en ninguna parte de la salida.
- Alcance: Windows, solo. Nada de `trampas*` ni de `proyecto-prueba-agentreach` se ejecutó. Sin red.
- Leyenda: C = comprobado, P = potencial. "Esperado" es la regla del PRD: comprobado solo si existe + permiso permite leer +
  ninguna regla lo bloquea; si algo no se entiende, nunca comprobado; deny baja a potencial.

## Tabla de casos (ejecutados)
Archivo creado: `.claude/settings.json` (Claude Code) u `opencode.json` (opencode) en la carpeta del caso, con el contenido indicado.

| # | Defecto | Contenido | Esperado | Obtenido | Veredicto |
|---|---|---|---|---|---|
| 1 | H1 | JSON cortado, con deny Read(./.env) | P | P no determinado + aviso "configuración no interpretable" | arreglado |
| 2 | H1 | comentario `//` | P | P no determinado | arreglado |
| 3 | H1 | UTF-8 inválido | P | P no determinado | arreglado |
| 4 | H1 | más de 10 MB | P | P no determinado | arreglado |
| 5 | H1 | lista con un elemento que no es texto | P | P no determinado | arreglado |
| 6 | H1 | `settings.local.json` roto + proyecto válido | P | P no determinado | arreglado |
| 7 | H1 | `settings.json` es una carpeta | P | P no determinado | arreglado |
| 8-9 | H1 | JSON es lista / `permissions` es texto | P | P no determinado | arreglado |
| 10 | H1 | con BOM (marca de orden de bytes) válido | P (deny) | P deny | arreglado (no es sobre-corrección) |
| 11-12 | H1 | control: sin settings / `{}` | C | C | arreglado (sin sobre-corrección) |
| 14-16 | H2 | `~/.claude/settings.json` del usuario con deny (`./.env`, `**/.env`) / roto | P / P / P no det. | P deny / P deny / P no determinado | arreglado |
| 17 | H2 | usuario con bloque `env` con valor | C y sin imprimir el valor | C; valor y nombre no aparecen | arreglado |
| 18-19 | H3 | `Read(*.env)`, `Read(**/*.env)` | P | P deny | arreglado |
| 35-36 | H3 | lo mismo sobre `sec/.env` anidado | P | P deny | arreglado |
| 20, 34 | H3 | `Read(.\sec\**)` (barras de Windows) | no determinado | P no determinado | arreglado |
| 21 | H3 | `Read()` | no determinado | P no determinado | arreglado |
| 22, 26, 27 | H3 | `[v]`, `!`, `{n,x}` | no determinado | P no determinado | arreglado |
| 23, 24, 32, 46-48 | H3 | `/.env`, `.env`, `Read` sin paréntesis, `**`, `.e?v`, `.en*` | P | P deny | arreglado |
| 37 | H3 | deny entendido + patrón raro | P | P deny (manda el deny) + aviso | arreglado |
| 25, 28-30, 33 | H3 | no cubren el `.env` (`//c/nada/**`, `*.txt`, `./sub/*.env`, `sub/**`, `~/.env`) | C | C | arreglado (sin sobre-corrección) |
| 38-39, 41-42 | H3 | ask / allow / deny de `Edit` / deny de `Bash(cat .env)` | P / C / C / C | P ask / C / C / C | arreglado |
| 44 | H3 | `Read(././.env)` | P o no determinado | **C** | sigue fallando (ver N1) |
| 45 | H3 | `Read(sub/../.env)` | P o no determinado | **C** | sigue fallando (ver N1) |
| 49-50 | H5 | opencode 1.x: sin config / `permission` objeto con `bash`, `edit` allow | C | C (en opencode sale P ask por defecto en `.env`, ver nota) | arreglado |
| 51, 62, 76 | H5 | 1.x `read: deny`, `permission: "deny"`, `**/.env: deny` | P | P deny | arreglado |
| 53, 54, 6x | H5 | 2.x `permissions` lista (con `shell`, con `read` deny) | P no determinado | P no determinado | arreglado |
| 63-64, 73 | H5 | `permission` raro, valor numérico, 1.x y 2.x mezclados | P no determinado | P no determinado | arreglado |
| 55-56 | H4 | `tools: {read:false}` / `{bash:false}` | P no determinado | P no determinado + `funcion_no_modelada` | arreglado |
| 57-58 | H4 | `agent.x.permission` deny / `agent.x.tools` | P no determinado | P no determinado | arreglado |
| 66-68 | H1 opencode | JSON cortado / UTF-8 inválido / > 10 MB | P no determinado | P no determinado | arreglado |
| 65, 61, 75 | opencode | comentario JSONC, `permission: "allow"`, `read: {"*.env":"allow"}` | C | C | arreglado (sin sobre-corrección) |
| X1 | H4 | `read: allow` + `.opencode/agent/a.md` sin permisos en el encabezado | C | C | correcto (solo importa si el encabezado trae `permission`/`tools`; no lo probé con encabezado, solo leído) |
| X2-X3 | H4 | `read: allow` + `agent.x.permission` deny / `tools.read=false` | P no determinado | P no determinado | arreglado |
| X7-X8 | H4 | Claude Code con hook `PreToolUse` / `sandbox` | P no determinado | P no determinado + `funcion_no_modelada` | arreglado |
| X9, X10, X12 | H3 | `Read(.\.env)`, deny + clave desconocida, `Read(//**/.env)` | P | P no determinado / P deny / P deny | arreglado |
| 70 | nuevo | opencode con clave duplicada `permission` (`read: deny` y luego `read: allow`) | P o no determinado | **C** | sigue fallando (N2) |
| 52 | nuevo | `read: {"*.env":"deny","*":"allow"}` (el último gana) | P (prudente) | **C** | discutible (N3) |
| X13 | nuevo | `.claude` es un archivo, no carpeta | no determinado | **C** | sigue fallando (N4) |
| X11 | nuevo | `defaultMode: bypassPermissions` + `allow Read` | C | C | correcto |

Nota opencode: cuando no hay reglas, opencode pide permiso para `.env` por defecto, así que el nivel es P ask. Es coherente
con el PRD (potencial) y no es un defecto.

## Veredicto por defecto
- H1 (configuración rota deja "comprobado"): ARREGLADO en los 9 casos de Claude Code y los 3 de opencode.
- H2 (usuario y gestionada): ARREGLADO por defecto (casos 14-17). Verificado ejecutando solo la configuración de usuario; la
  gestionada (`managed-settings.json` y su carpeta `.d`) y `XDG_CONFIG_HOME`/`OPENCODE_CONFIG` solo las leí en el código y en
  `tests/test_correcciones_11b.py`, no las ejecuté (escribir en carpetas de programa del sistema no es seguro desde esta revisión).
- H3 (patrones): ARREGLADO para los patrones pedidos (`*.env`, `**/*.env`, barras de Windows, `Read()`, corchetes). Quedan dos rarezas (N1).
- H4: ARREGLADO para `agent.*.permission`, `agent.*.tools`, `tools`, hooks y `sandbox`.
- H5 (1.x frente a 2.x): ARREGLADO (lista `permissions` y `shell` dan no determinado, `permission` objeto con `bash` funciona).

## Defectos que siguen o nuevos (gravedad y arreglo sugerido)
- N1 (media-baja): `Read(././.env)` y `Read(sub/../.env)` salen "comprobado" aunque hay un deny que quizá aplique. Un patrón con
  `./` repetido o `..` debería ser "no determinado". Arreglo: en `reglas.py` normalizar solo un `./` inicial y devolver "no
  interpretado" si el patrón contiene `..` o `./` en el medio.
- N2 (media): clave duplicada en `opencode.json`: gana la última (`allow`) y el `deny` anterior se pierde, con nivel "comprobado". Si
  opencode resuelve la duplicada de otra forma, es un "comprobado" falso. Arreglo: al leer el JSON detectar claves repetidas
  (`object_pairs_hook`) y marcar la fuente como no interpretable. Lo mismo para Claude Code.
- N3 (baja, decisión de diseño): en opencode gana la última regla que coincide; `{"*.env":"deny","*":"allow"}` da comprobado. Es
  correcto si esa semántica es la real, pero el PRD dice que deny baja a potencial. Pedir a Alex que lo confirme y dejarlo escrito.
- N4 (baja): `.claude` existente pero que es un archivo (no carpeta) se ignora y sale "comprobado". Arreglo: tratar un `.claude`
  o `.opencode` que no es carpeta como "no se pudo leer".
- N5 (baja, calidad): ruff falla con 4 errores de orden de imports en `tests/`; corregir con `uv run ruff check --fix tests`.

## Regresiones por los arreglos
No encontré regresiones de sobre-corrección: los controles (sin settings, `{}`, allow solo, `deny Edit`, `deny Bash`, patrones que no
cubren el `.env`, `Read(~/.env)`) siguen en "comprobado"; el BOM válido se acepta. Las pruebas pasan (1098).
Riesgo residual que no ejecuté: enlaces simbólicos y la configuración por política del registro de Windows (la historia 11b los deja diferidos).

## Qué verifiqué ejecutando y qué solo leyendo
- Ejecutado: pytest, ruff, los 90 casos de la tabla, un caso con la línea de comandos real, y la ausencia de fuga del valor del bloque `env`.
- Solo leído: configuración gestionada y carpeta `managed-settings.d`, `XDG_CONFIG_HOME`, `OPENCODE_CONFIG`, `.opencode/agent/*.md` con
  encabezado con permisos, enlaces simbólicos, y la sintaxis gitignore frente a la documentación de Claude Code (no consulté la red).
