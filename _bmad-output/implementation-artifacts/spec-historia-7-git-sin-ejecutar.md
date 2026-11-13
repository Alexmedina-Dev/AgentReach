---
title: 'Historia 7. Git sin ejecutar nada: remotos, submódulos, hooks y configuración peligrosa'
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

**Problema:** una carpeta que trae su `.git` puede llevar configuración que ejecuta un programa o remotos con credenciales, y AgentReach no lo veía; ejecutar `git` para mirarlo sería peligroso.

**Enfoque:** un lector propio, fiel a git, del texto de `.git/config` (con `include`), `.gitmodules` y `.gitattributes`, más el listado de nombres de `.git/hooks/`, sin ejecutar nada. `DetectorGit` entrega TH-18 (ejecuta programas), TH-19 (remoto o submódulo con credencial o dirección sospechosa) y TH-20 (configuración no interpretable); el historial sale como `historial_git_fase2`.

## Boundaries & Constraints

**Always:** ningún programa ni `git`; solo `leer_seguro` a través del puerto; ante la duda se reporta; una clave de URL nunca sale; los hooks solo se listan; un fallo de lectura o interpretación es TH-20 más `NoRevisado` con motivo.

**Never:** historial de commits, `.git` como archivo, `safe.directory`, variables `GIT_*`, versión de git, calcular el nivel.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| fsmonitor con programa | `core.fsmonitor = prog` | TH-18 con su línea | — |
| fsmonitor booleano | true/false/yes/no/0/vacío | nada | — |
| Remoto con usuario:clave | `https://u:k@host` | TH-19, clave no sale | — |
| Ciclo de include | A incluye B, B incluye A | termina; TH-20 + profundidad_excedida | — |
| Config ilegible | 5 MB+1, no UTF-8, tubería, enlace | TH-20 + NoRevisado con motivo | sin excepción |
| Hook sin .sample | `post-checkout` | TH-18 sin abrirlo | — |
| wincred | `credential.helper = wincred` | TH-18 + sugerencia de otro ayudante | — |

</intent-contract>

## Code Map

- `src/agentreach/infra/lector_config_git.py` -- `parsear_config`, `es_booleano_git`, `leer_con_includes`.
- `src/agentreach/collectors/git_meta.py` -- `DetectorGit`, `SUGERENCIAS_TEXTO`.
- `src/agentreach/app/auditar.py` -- registro del detector (una línea).
- Proyecto de prueba: `trampas-git/<caso>/.git` (GT-04 a GT-18), `proyecto/.git` (GT-03).

## Tasks & Acceptance

**Execution:**
- `tests/test_git_estatico.py` -- primero
- lector, detector y registro

**Acceptance Criteria:**
- Given (a), (b), (c), (d), (e), (f), (g0) y (g) de la historia, when se ejecutan, then se cumplen y los controles GT-10 a GT-12 no se reportan.

## Spec Change Log

## Review Triage Log

### 2026-11-09 - Review pass
- verdicts: ~38 findings (ciega 12 agrupados, casos limite 18 mas 2 de afirmaciones) - high 0, medium 10, low 8, false 1, maybe-false 0
- `[medium]` `[patch]` un entero enorme en fsmonitor lanzaba ValueError y abortaba la auditoria - se trata como no booleano
- `[medium]` `[patch]` include con `~` metia texto del archivo como ruta y daba un TH-20 falso - se informa con la ruta del archivo que incluye y sin TH-20
- `[medium]` `[patch]` .gitmodules se evaluaba entero (git solo lee submodule.*) - solo se evaluan las URL de submodulos
- `[medium]` `[patch]` .git enlace o archivo, .gitmodules, .gitattributes y hooks ilegibles daban solo NoRevisado - ahora TH-20 mas NoRevisado (ante la duda se reporta)
- `[medium]` `[patch]` hook enlazado o raro solo se informaba - se reporta (git lo ejecuta) y se informa
- `[medium]` `[patch]` include alcanzado por dos caminos duplicaba hallazgos - se deduplica
- `[medium]` `[patch]` claves que faltaban: submodule.update con `!`, browser/man/trailer .cmd, remote.vcs, uploadpack.packObjectsHook, web.browser; credencial en el nombre de url.<base>.insteadOf; token largo como usuario de una URL http(s)
- `[low]` `[patch]` listar de hooks con excepciones mas amplias; orden de lineas en pruebas; BOM sin carácter invisible
- `[medium]` `[defer]` git.config.worktree, info/attributes, .gitattributes anidados, .git/modules y la carpeta de core.hooksPath no se miran, y un .git presente pero sin permiso de lectura parece ausente (el puerto no distingue) - fase 2 / historias posteriores
- `[low]` `[defer]` la sugerencia de wincred y no_revisados aun no se muestran en el reporte (Historia 13); SCP con usuario:clave, credenciales con %-codificacion y otras transport:: distintas de ext::
- `[false]` desfase de profundidad 10 en includes - la cadena de 12 archivos corta exactamente en el onceavo, igual que git
- `[reject]` credential.helper con nombre simple (git-credential-<nombre>), http.proxy, mutabilidad del detector, constante de las fechas de aviso, nivel provisional

## Verification

**Commands:**
- `uv run pytest -q` -- expected: todo pasa
- `uv run ruff check src tests` -- expected: sin errores

## Auto Run Result

Resumen: `parsear_config` y `leer_con_includes` (lector propio, fiel a git, solo texto) y `DetectorGit` (TH-18, TH-19, TH-20) registrado en la ejecucion de la 5b. Historial de commits como `historial_git_fase2`. Sin ejecutar nada.
Archivos: `infra/lector_config_git.py`, `collectors/git_meta.py`, `app/auditar.py` (una linea), `tests/test_git_estatico.py`, `tests/test_primera_ejecucion.py` (lista de detectores registrados).
Verificacion: con el proyecto de prueba 384 pasan, 11 omitidas; sin el 360 pasan, 35 omitidas. Ruff limpio. GT-03 a GT-09 y GT-13 a GT-18 se detectan; los controles GT-10 a GT-12 y los .sample no; TR-01 sin PWNED.txt; ninguna llamada a subprocess, os.system, os.popen, os.startfile, os.exec* ni os.spawn*.
Sin commit. Riesgo residual: los `defer`.
