---
title: 'Historia 1. Contratos del hallazgo y tubería mínima'
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

**Problema:** el modelo de hallazgo ya existe, pero solo con 11 tipos (TH-1 a TH-11); el catálogo del PRD tiene 20 (TH-12 a TH-20 se añadieron el 2026-11-09). Además falta la tubería mínima `core/pipeline.py`.

**Enfoque:** ampliar `Tipo`, el catálogo de explicaciones ES/EN y el indicador de fuente verificada hasta TH-20; añadir una tubería que reúna los candidatos de los detectores registrados, sin importar `adapters`, `infra` ni `reporting`.

## Boundaries & Constraints

**Always:** solo biblioteca estándar; solo lectura; ningún texto del catálogo con valores de secreto; cada tipo con explicación en ES y EN; tipo sin indicador = "sin fuente verificada".

**Never:** detectar nada, calcular niveles, reporte, puerto Narrator con lógica; tocar `infra/localizador.py`; hacer commit.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Sin detectores | `Pipeline([])` ejecutado sobre una ruta | lista vacía | — |
| Varios detectores | dos detectores falsos con hallazgos | todos los hallazgos, ordenados con `ordenar` | — |
| Detector que falla | detector que lanza excepción | la excepción se propaga con el nombre del detector; no se pierde en silencio | `RuntimeError` encadenado |

</intent-contract>

## Code Map

- `src/agentreach/contracts/finding.py` -- `Tipo` (línea ~110), `FUENTE_VERIFICADA`, `CATALOGO_EXPLICACIONES`, `ordenar`.
- `src/agentreach/contracts/ports.py` -- puerto `Detector.detectar(proyecto) -> Iterable[Finding]`.
- `src/agentreach/core/__init__.py` -- paquete vacío; `core/pipeline.py` no existe.
- `tests/test_contratos.py` -- hoy afirma 11 tipos (línea ~119); la prueba (d) de importaciones ya recorre `core/`.

## Tasks & Acceptance

**Execution:**
- `src/agentreach/contracts/finding.py` -- añadir TH-12..TH-20 a `Tipo`, con explicaciones ES/EN; `FUENTE_VERIFICADA` sigue en False -- PRD FR-18
- `src/agentreach/core/pipeline.py` -- clase `Pipeline` con `registrar`/`ejecutar` -- tubería mínima
- `tests/test_contratos.py` -- 20 tipos; pruebas de la tubería -- criterio de terminado

**Acceptance Criteria:**
- Given el catálogo, when se listan los tipos, then son TH-1 a TH-20 con explicación ES y EN.
- Given dos detectores falsos, when se ejecuta la tubería, then devuelve sus hallazgos ordenados.
- Given `core/`, when se revisan sus importaciones, then no usa `adapters`, `infra` ni `reporting`.

## Verification

**Commands:**
- `uv run pytest -q` -- expected: todo pasa
- `uv run ruff check src tests` -- expected: sin errores

## Review Triage Log

### 2026-11-09 — Review pass
- verdicts: 20 findings (blind 9 agrupados, edge 11) — high 0, medium 1, low 4, false 0, maybe-false 0
- `[medium]` `[patch]` orden por tipo lexicográfico (TH-12 antes de TH-2) — corregido con clave numérica y prueba `test_orden_por_tipo_es_numerico`
- `[low]` `[reject]` pipeline pierde resultados parciales / excepción genérica / sin validación de Detector / duplicados / proyecto inválido — decisión de diseño: falla ruidosa, sin lógica extra en una tubería mínima; los detectores validan su entrada
- `[low]` `[reject]` pruebas del catálogo más estrictas, redacción de remedios, paréntesis, número mágico 20 — la prueba existente ya exige texto no vacío ES/EN; el resto es cosmético

## Auto Run Result

Resumen: Tipo ampliado a TH-1..TH-20 con explicaciones ES/EN; `core/pipeline.py` (clase `Pipeline`); orden por tipo numérico.
Archivos: `contracts/finding.py`, `core/pipeline.py`, `tests/test_contratos.py`.
Verificación: `uv run pytest -q` 65 pasan, 3 omitidas; `uv run ruff check src tests` limpio.
Sin commit (el usuario lo prohíbe sin pedirlo). Riesgo residual: `FUENTE_VERIFICADA` queda en False para todos los tipos.
