---
title: 'Historia 6. Variables de entorno con nombre de credencial'
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

**Problema:** AgentReach no sabe si el entorno del proceso tiene variables con forma de credencial que un agente podría heredar.

**Enfoque:** `DetectorEntorno` recibe el entorno por el puerto `EnvView` (una lista de nombres), filtra por forma de credencial con los patrones de la Historia 4 y entrega hallazgos TH-4 con la ruta `entorno:NOMBRE`. `EnvVistaProceso` entrega solo los nombres de `os.environ`.

## Boundaries & Constraints

**Always:** nunca el valor; nunca volcar el entorno a un objeto; sin leer archivos (no usa `leer_seguro`); un hallazgo por nombre mostrado (las variantes de mayúsculas son variables distintas; en Windows el entorno no las repite).

**Never:** decidir si el agente hereda la variable (Historia 9); calcular nivel (Historia 11).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| EV-01 | dos variables falsas solo en el hijo | exactamente los dos nombres | — |
| Sin variables | entorno sin ellas | nada | — |
| Sin forma de credencial | PATH, HOME, NODE_ENV | se ignoran | — |
| Nombre con escapes | `API_TOKEN\x1b[2J` | ruta limpia | — |

</intent-contract>

## Code Map

- `src/agentreach/infra/env_view.py` -- `EnvVistaProceso.nombres()`.
- `src/agentreach/collectors/entorno.py` -- `DetectorEntorno`.
- `src/agentreach/collectors/detector/patrones.py` -- `clasificar_nombre` (reutilizado; proveedor de base de datos ampliado a `DATABASE_`, `DB_PASS`, `DB_USER`).

## Tasks & Acceptance

**Execution:**
- `tests/test_entorno.py` -- primero
- `infra/env_view.py`, `collectors/entorno.py`

**Acceptance Criteria:**
- Given (a)-(c) y EV-01, when se ejecutan, then se cumplen.

## Spec Change Log

## Review Triage Log

### 2026-11-09 - Review pass
- verdicts: ~30 findings (ciega 16, casos limite 10 mas 1 de afirmacion) - high 0, medium 3, low 5, false 0, maybe-false 0
- `[medium]` `[patch]` proveedor de base de datos demasiado ancho (DATABASE_, DB_USER como subcadena) - patrones anclados y prueba negativa
- `[medium]` `[patch]` dedup por el nombre en mayusculas daba duplicados al limpiar caracteres de control y unia variables distintas en Linux - se deduplica por el nombre ya limpio
- `[medium]` `[patch]` una vista de entorno que devuelve None o elementos que no son texto tumbaba el detector - se tolera
- `[low]` `[patch]` pruebas: ruta del hijo por argv (no por literal), diagnostico del hijo, sin skip en la prueba del generador
- `[defer]` los nombres de variables pueden ser sensibles por si mismos y no tienen tope de largo - sin caso en el oraculo
- `[reject]` guardia AST evadible (es una verificacion de higiene, no la garantia: el puerto solo ofrece nombres), constante para "sin-agente" y nivel provisional (Historias 9 y 11), nombres mezclados espanol/ingles, cableado en la CLI y flag --con-entorno (es del generador; el cableado es de la Historia 5b/13), orden de resultados

## Verification

**Commands:**
- `uv run pytest -q` -- expected: todo pasa
- `uv run ruff check src tests` -- expected: sin errores

## Auto Run Result

Resumen: `DetectorEntorno` (TH-4) sobre el puerto `EnvView` y `EnvVistaProceso` (solo nombres de `os.environ`). EV-01: sin las variables no sale nada; con ellas, exactamente `AGENTREACH_PRUEBA_API_TOKEN` y `AGENTREACH_PRUEBA_DB_PASSWORD`.
Archivos: `collectors/entorno.py`, `infra/env_view.py`, `collectors/detector/patrones.py` (proveedor de base de datos), `tests/test_entorno.py`.
Verificacion: con el proyecto de prueba 206 pasan, 7 omitidas; sin el 201 pasan, 12 omitidas. Ruff limpio.
Sin commit. Riesgo residual: nombres de variable sensibles por si mismos; nivel provisional.
