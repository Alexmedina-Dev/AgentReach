---
title: 'Historia 4b. Endurecimiento: lectura segura y "no se pudo revisar" con motivo'
type: 'refactor'
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

**Problema:** los lectores de las Historias 2 y 4 saltaban en silencio lo que no podían leer y cada uno tenía sus propios límites de lectura.

**Enfoque:** una única función `leer_seguro` (tipo con `lstat` antes de abrir, sin seguir enlaces, tope de 5 MB, UTF-8 estricto), el contrato `NoRevisado` con motivos de lista cerrada, y recorrido y detector de credenciales que informan lo que no revisaron.

## Boundaries & Constraints

**Always:** las pruebas `test_recorrido.py` y `test_credenciales_archivos.py` siguen pasando sin cambios; los motivos son solo razones de imposibilidad; `NoRevisado` nunca lleva contenido; en `collectors/` ningún `open`/`read_text`/`read_bytes`.

**Never:** nuevos detectores, textos de "cómo resolverlo", cambiar lo que detectan las Historias 2 y 4, tocar `finding.py`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| 5 MB + 1 byte | archivo grande | `NoRevisado(archivo_demasiado_grande)` sin abrir | — |
| No UTF-8 / NUL | bytes inválidos | `codificacion_no_utf8` | — |
| Tubería / junction | `lstat` falso, enlace | `no_es_archivo_regular` sin abrir | — |
| JSON 65 niveles | credentials.json | `profundidad_excedida` | — |
| Motivo inválido | cualquier otro valor | `TypeError` | — |

</intent-contract>

## Code Map

- `src/agentreach/infra/lectura_segura.py` -- `leer_seguro`, `revisar_profundidad_json`, `TOPE_BYTES`, `PROFUNDIDAD_MAXIMA`.
- `src/agentreach/contracts/no_revisado.py` -- `MotivoNoRevisado`, `NoRevisado`.
- `src/agentreach/contracts/ports.py` -- `ArchivoNoLegible.motivo`.
- `src/agentreach/infra/fs_solo_lectura.py` -- `leer_texto` delega en `leer_seguro` (tope de configuración 1 MiB).
- `src/agentreach/collectors/enlaces.py` -- `Recorrido.no_revisados`; `archivos_repo.py` -- `DetectorCredencialesArchivos.no_revisados`.

## Tasks & Acceptance

**Execution:**
- `tests/test_lectura_segura.py` -- primero la prueba
- `infra/lectura_segura.py`, `contracts/no_revisado.py`, y los cambios en `ports`, `fs_solo_lectura`, `enlaces`, `archivos_repo`

**Acceptance Criteria:**
- Given los casos de (a)-(f) de la historia, when se ejecutan, then salen como `NoRevisado` con el motivo correcto y sin abrir cuando no corresponde.
- Given las pruebas de las Historias 2 y 4, when se ejecutan sin cambios, then pasan.

## Spec Change Log

## Review Triage Log

### 2026-11-09 - Review pass
- verdicts: ~30 findings (ciega 12, casos limite 9 mas 1 de afirmacion) - high 0, medium 4, low 6, false 1, maybe-false 0
- `[medium]` `[patch]` FueraDelProyecto salia con motivo archivo_ilegible - ahora no_es_archivo_regular
- `[medium]` `[patch]` credentials.json demasiado anidado perdia su hallazgo por nombre - lo conserva y ademas informa NoRevisado
- `[medium]` `[patch]` enlaces internos no seguidos se saltaban en silencio - se informan como no_es_archivo_regular
- `[low]` `[patch]` no_revisados desactualizado tras una llamada anterior o un error; descriptor abierto si fdopen falla; docstring del tope
- `[low]` `[defer]` motivos sin productor todavia (ubicacion_sensible_sin_activar, configuracion_no_interpretable, version_no_reconocida, historial_git_fase2) - los producen las Historias 5, 7 y 9
- `[low]` `[defer]` nada muestra aun `no_revisados` al usuario - lo consume el reporte (Historia 13)
- `[medium]` `[defer]` puntos de reparse de Windows que no son enlaces (marcadores de nube) y NUL de UTF-16 como no UTF-8 - sin caso en el oraculo
- `[reject]` isjunction en Python < 3.12 (el proyecto exige 3.12+), dos topes 1 MiB / 5 MB (intencional: configuracion pequena, maximo absoluto de 5 MB; documentado), NoRevisado con ruta real (limpiar_ruta ya la limpia), campos paralelos de Recorrido (compatibilidad pedida por la historia), pickle de la excepcion, cobertura de AST mas amplia

## Verification

**Commands:**
- `uv run pytest -q` -- expected: todo pasa
- `uv run ruff check src tests` -- expected: sin errores

## Auto Run Result

Resumen: `leer_seguro` como unica lectura (lstat antes de abrir, sin seguir enlaces, tope 5 MB, UTF-8 estricto con BOM), `NoRevisado` con 10 motivos cerrados, `revisar_profundidad_json` (64 niveles), y recorrido y detector de credenciales que informan lo que no revisaron.
Archivos: `infra/lectura_segura.py`, `contracts/no_revisado.py`, `contracts/ports.py`, `contracts/__init__.py`, `infra/fs_solo_lectura.py`, `collectors/enlaces.py`, `collectors/archivos_repo.py`, `tests/test_lectura_segura.py`.
Verificacion: con el proyecto de prueba 161 pasan, 7 omitidas; sin el 157 pasan, 11 omitidas. Ruff limpio. `tests/test_recorrido.py` y `tests/test_credenciales_archivos.py` pasan sin cambios.
Sin commit. Riesgo residual: los `defer`.
