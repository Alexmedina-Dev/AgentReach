---
title: 'Historia 10. Adaptador de opencode'
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

**Problema:** AgentReach no entiende las reglas de opencode: no sabe qué lee o pregunta su política, y su semántica ("gana la última regla que coincide") es la opuesta a la de Claude Code.

**Enfoque:** `AdaptadorOpencode` (capacidad "auditar y advertir") lee `opencode.json` y `opencode.jsonc` del proyecto, y con el opt-in la global y la gestionada, con la lectura segura. Aplica la semántica de opencode (orden base, global, proyecto, gestionada; gana la última; fuera del proyecto manda `external_directory`) y entrega reglas con archivo y línea. `DetectorOpencode` marca como hallazgo solo las reglas que debilitan la protección (TH-7 y TH-8). Pasa el mismo kit de conformidad que Claude Code.

## Boundaries & Constraints

**Always:** `shell` y `bash` son lo mismo; un `deny` de read/edit no baja ningún hallazgo del shell; el texto de los patrones nunca sale; lo que no se reconoce da `NoRevisado` (`configuracion_no_interpretable` o `version_no_reconocida`), nunca una excepción; la política base pregunta antes de leer `*.env` y `*.env.*`.

**Never:** probar contra una instalación real de opencode (no está instalada: se asume 2.x), calcular el nivel, un hallazgo de sandbox para opencode (se reconoce como hecho).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| CA-04 | read, edit, bash, webfetch en allow; external_directory ask | 5 reglas con línea; TH-7 (read, edit, webfetch) y TH-8 (shell) | — |
| PP-01 en opencode | `read: allow` en el proyecto | postura ALLOW (gana a la base que pregunta) | — |
| OC-01 | sin regla de read | postura ASK (la base) | — |
| AJ-01 | archivo fuera del proyecto | postura ASK (external_directory) | — |
| Última regla | `{"*.env": "deny", "*": "allow"}` | ALLOW (al revés que Claude Code) | — |
| Valor o forma desconocidos | `"read": "quizas"` | `NoRevisado(version_no_reconocida)` | sin excepción |

</intent-contract>

## Code Map

- `src/agentreach/adapters/opencode/__init__.py` -- `AdaptadorOpencode`, `DetectorOpencode`.
- `src/agentreach/adapters/base.py` -- contrato común (Historia 9); `adapters/conformance` -- kit compartido.
- `src/agentreach/app/auditar.py` -- registro.

## Tasks & Acceptance

**Execution:**
- `tests/test_adaptador_opencode.py` -- primero
- adaptador, detector y registro

**Acceptance Criteria:**
- Given CA-04, PP-01, AJ-01, OC-01 y el kit de conformidad, when se ejecutan, then se cumplen.

## Spec Change Log

## Review Triage Log

### 2026-11-09 - Review pass
- verdicts: ~25 findings (ciega 8, casos limite 14 mas 3 de afirmaciones) - high 0, medium 8, low 6, false 2, maybe-false 0
- `[medium]` `[patch]` un allow amplio escrito como `**`, `*/*` o `?*` no se reportaba - se reconoce por lo que acepta (cualquier ruta), no por el texto
- `[medium]` `[patch]` un allow amplio que una regla posterior ask/deny amplia anula (gana la ultima) daba un falso TH-7/TH-8 - ya no
- `[medium]` `[patch]` patrones con barra de Windows, `./` o ruta absoluta nunca coincidian - se comparan contra la forma relativa y la absoluta
- `[medium]` `[patch]` los permisos por agente (agent.<nombre>.permission) no se modelan y no avisaban - NoRevisado(version_no_reconocida) y se conservan las reglas generales
- `[medium]` `[patch]` home no resoluble buscaba la global en el directorio actual; ProgramData vacio daba una ruta relativa; una ruta con caracteres imposibles lanzaba ValueError
- `[low]` `[patch]` sistema de archivos externo inyectable; nombre de una prueba que no probaba lo que decia
- `[low]` `[defer]` la politica base de opencode puede dejar leer `*.env.example` (la PRD solo fija `*.env` y `*.env.*`); `tools` heredado de la version 1; postura de edit/webfetch/shell sobre rutas; enlaces simbolicos (sin realpath)
- `[low]` `[defer]` opencode.json y opencode.jsonc a la vez: el orden .json luego .jsonc es una suposicion; permiso bash y shell en el mismo archivo se tratan como dos reglas
- `[false]` ruta relativa con barra invertida (relativa_a ya devuelve con `/`); postura SIN_REGLA para un archivo que no es .env (OC-01 habla del .env)
- `[reject]` nivel provisional (Historia 11), hallazgo TH-10 para opencode (el oraculo solo lo pide para Claude Code), regla `*` global mezclada entre fuentes (cubierto por el orden)

## Verification

**Commands:**
- `uv run pytest -q` -- expected: todo pasa
- `uv run ruff check src tests` -- expected: sin errores

## Auto Run Result

Resumen: `AdaptadorOpencode` (capacidad auditar y advertir) con la semantica de opencode (orden base, global, proyecto, gestionada; gana la ultima regla que coincide; fuera del proyecto manda `external_directory`), la base que pregunta antes de leer `*.env` y `*.env.*`, `shell` y `bash` como el mismo permiso, JSONC con el lector propio y el reconocimiento de "sin sandbox documentado". `DetectorOpencode` entrega TH-7 y TH-8 solo para reglas amplias que debilitan la proteccion. Pasa el mismo kit de conformidad que Claude Code.
Archivos: `adapters/opencode/__init__.py`, `app/auditar.py`, `tests/test_adaptador_opencode.py`, `tests/test_primera_ejecucion.py`.
Verificacion: ver el reporte de la vuelta. Ruff limpio. CA-04 (TH-7 x3 y TH-8), PP-01 en opencode (ALLOW), AJ-01 (ASK) y OC-01 (ASK) se cumplen.
Sin commit. Riesgo residual: los `defer`.
