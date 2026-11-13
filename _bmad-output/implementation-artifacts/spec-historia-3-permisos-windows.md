---
title: 'Historia 3. Permisos del sistema en Windows (sin abrir archivos)'
type: 'feature'
created: '2026-11-09'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
context: ['{project-root}/_bmad-output/planning-artifacts/historias-mvp.md']
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problema:** AgentReach no sabe si el usuario que lo ejecuta puede leer un archivo ni si el archivo está abierto a "Todos", y no puede medirlo abriéndolo ni con `icacls`.

**Enfoque:** `SondaWindows` lee la ACL con `ctypes` (`GetNamedSecurityInfoW`, `AccessCheck` con el token del proceso) y entrega `PermisosArchivo` (permiso, abierto a Todos, ambiguo, usuario, comando de verificación en texto). `SondaPosix` da modo y propietario.

## Boundaries & Constraints

**Always:** solo biblioteca estándar; no abrir el archivo medido; no lanzar `icacls` ni ningún programa; el comando de verificación es solo texto; solo mide al usuario que ejecuta AgentReach.

**Never:** permisos de otros usuarios o de administrador; decidir el nivel; crear hallazgos.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| PP-04 / PP-05 | permiso normal | SI, no abierto, no ambiguo | — |
| PP-03 | `deny R` al usuario | NO, ambiguo (se deduce de la negativa) | — |
| PA-01 | entrada propia para Todos | SI, abierto, inequívoco | — |
| Heredado | Todos solo por herencia | abierto, ambiguo | — |
| Denegar + Todos | regla deny presente | abierto, ambiguo | — |
| No existe / API falla | ruta inválida | NO_DETERMINADO, ambiguo | sin excepción |

</intent-contract>

## Code Map

- `src/agentreach/infra/sonda_windows.py` -- `SondaWindows.evaluar`, ACL con ctypes.
- `src/agentreach/infra/sonda_posix.py` -- `SondaPosix`.
- `src/agentreach/contracts/ports.py` -- `PermisosArchivo` (nuevo), `FsProbe`.
- `tests/test_permisos_windows.py` -- (a) no abrir, (b) usuario y comando, (c) sin programas, casos PP-03/04/05, PA-01.

## Tasks & Acceptance

**Execution:**
- `tests/test_permisos_windows.py` -- pruebas primero
- `src/agentreach/infra/sonda_windows.py`, `sonda_posix.py`, `contracts/ports.py` -- implementación

**Acceptance Criteria:**
- Given un archivo medido, when se evalúa, then no se abre y no se lanza ningún programa.
- Given PP-03, PP-04, PP-05 y PA-01, when se evalúan, then dan no legible, legible, legible y abierto inequívoco.

## Spec Change Log

## Review Triage Log

### 2026-11-09 - Review pass
- verdicts: ~35 findings (ciega 16, casos limite 17 mas 2 de afirmaciones) - high 0, medium 5, low 6, false 0, maybe-false 0
- `[medium]` `[patch]` entrada de Todos solo para hijos (INHERIT_ONLY) contaba como abierto - se excluye
- `[medium]` `[patch]` denegar que deja sin lectura (no solo READ_CONTROL) salia no ambiguo - ambiguo si no legible y hay denegar
- `[medium]` `[patch]` entradas de otro tipo (callback, objeto) invisibles - vuelven el resultado ambiguo
- `[medium]` `[patch]` ruta invalida o fallo de ctypes lanzaba excepcion - ahora NO_DETERMINADO ambiguo (fuera de Windows sigue OSError, documentado)
- `[medium]` `[patch]` comando de verificacion POSIX permitia inyeccion con comillas - comillas simples a mano y prueba
- `[low]` `[patch]` usuario vacio en salidas tempranas; prueba dependiente del idioma (Everyone) - se usa el SID *S-1-1-0
- `[medium]` `[defer]` ruta que es enlace (el API sigue el destino) y rutas mayores de 260 caracteres - las historias que llamen a la sonda solo pasan archivos listados; revisar en Historia 4/5
- `[low]` `[defer]` SID amplios (Authenticated Users, Usuarios) y deny de un SID ajeno inflan o ocultan abierto - alcance escrito: solo Todos
- `[reject]` POSIX ambiguo siempre False, uid real vs efectivo, factoria por plataforma, validacion de PermisosArchivo, hilos, pruebas extra - sin pruebas obligatorias en POSIX en el MVP; el cableado lo hace la Historia 5/13

## Verification

**Commands:**
- `uv run pytest -q` -- expected: todo pasa
- `uv run ruff check src tests` -- expected: sin errores

## Auto Run Result

Resumen: `SondaWindows` (ACL con ctypes, AccessCheck con el token del proceso, sin abrir el archivo ni lanzar programas), `SondaPosix` (modo y propietario) y `PermisosArchivo` en los contratos.
Archivos: `infra/sonda_windows.py`, `infra/sonda_posix.py`, `contracts/ports.py`, `contracts/__init__.py`, `tests/test_permisos_windows.py`.
Verificacion: con el proyecto de prueba 88 pasan, 5 omitidas; sin el 86 pasan, 7 omitidas. Ruff limpio. PP-03 no legible, PP-04 y PP-05 legibles, PA-01 abierto e inequivoco.
Sin commit. Riesgo residual: los dos `defer` (enlaces y rutas largas; SID amplios).
