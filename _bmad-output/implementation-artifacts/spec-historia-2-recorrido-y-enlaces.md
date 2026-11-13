---
title: 'Historia 2. Recorrido del proyecto y enlaces que salen'
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

**Problema:** AgentReach aún no recorre el proyecto ni reconoce enlaces (junctions y symlinks) que llevan fuera de él.

**Enfoque:** un sistema de archivos de solo lectura (`infra/fs_solo_lectura.py`, implementa el puerto `ReadOnlyFs`) y un recolector (`collectors/enlaces.py`) que lista archivos, reporta los enlaces que salen del proyecto con su destino y **nunca entra** a ellos; el detector entrega hallazgos TH-6.

## Boundaries & Constraints

**Always:** solo biblioteca estándar; solo lectura; no ejecutar programas externos; del enlace solo ruta y destino, nunca el contenido de detrás (FR-19); ruta de red (UNC) = "no revisada" sin tocarla; archivo gigante (> 1 MiB) o binario se salta.

**Never:** reconocer secretos, calcular permisos o niveles reales, leer el destino del enlace, seguir enlaces.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Junction externa | `proyecto/enlace-externo` -> carpeta fuera | 1 enlace (ruta, destino) y 1 hallazgo TH-6; no se lista nada detrás | — |
| Ciclo de enlaces | enlace que apunta a su propia carpeta o al padre | termina; no se entra | — |
| Enlace interno | enlace cuyo destino está dentro del proyecto | no es hallazgo; no se sigue | — |
| Ruta UNC | raíz o carpeta que empieza por `\\` | aparece en `no_revisadas`; no se llama al sistema | — |
| Archivo gigante / binario | > 1 MiB o con byte NUL | se salta (`omitidos` / `ArchivoNoLegible`) | sin traza con contenido |

</intent-contract>

## Code Map

- `src/agentreach/contracts/ports.py` -- `ReadOnlyFs`, `Metadatos` (ya tiene `es_enlace`, `destino_enlace`), `Detector`.
- `src/agentreach/contracts/finding.py` -- `Finding`, `Tipo.ENLACE_FUERA_DEL_PROYECTO` (TH-6), `limpiar_ruta`.
- `src/agentreach/core/pipeline.py` -- `Pipeline` que usará el detector.
- Proyecto de prueba: variable `AGENTREACH_PROYECTO_PRUEBA` (EN-01, EN-02, EN-03, NO-02, NO-05).

## Tasks & Acceptance

**Execution:**
- `tests/test_recorrido.py` -- pruebas (a)-(d) y casos del oráculo -- primero la prueba
- `src/agentreach/infra/fs_solo_lectura.py` -- `FsSoloLectura` (sin escritura; no sigue enlaces) y `ArchivoNoLegible`
- `src/agentreach/collectors/enlaces.py` -- `Enlace`, `Recorrido`, `recorrer`, `DetectorEnlaces`

**Acceptance Criteria:**
- Given un ciclo de enlaces, when se recorre, then termina.
- Given un archivo canario tras el enlace, when se recorre y se produce toda salida, then el canario no aparece.
- Given una ruta UNC, when se recorre, then queda como no revisada.
- Given EN-01, when se detecta, then hay un hallazgo TH-6 con destino; EN-02 no genera hallazgo.

## Spec Change Log

## Review Triage Log

### 2026-11-09 — Review pass
- verdicts: ~33 findings (blind 16, edge 17) — high 0, medium 2, low 4, false 3, maybe-false 0
- `[low]` `[patch]` leer_texto sobre archivo no regular (FIFO/dispositivo) — rechazado con S_ISREG
- `[low]` `[patch]` LIMITE_BYTES duplicado — movido a `contracts/ports.py`; docstring de `_norm` corregido (realpath sí consulta metadatos de enlaces)
- `[medium]` `[defer]` un OSError en una sola entrada descarta toda la carpeta (queda como no revisada, no en silencio) — afinar por entrada cuando el reporte (Historia 13) declare cobertura
- `[medium]` `[defer]` unidades de red mapeadas (Z:) y componentes intermedios que son enlaces en `leer_texto` — fuera del alcance escrito (solo UNC); revisar en Historias 4 y 13
- `[false]` prefijo `\??\` de junction — `os.readlink` ya devuelve `\?\` y la prueba con junction real lo cubre
- `[reject]` destino ausente del Finding — decisión de diseño: Finding no tiene texto libre; el destino vive en `Enlace`
- `[reject]` Python < 3.12 sin `isjunction` — el proyecto exige 3.12+
- `[reject]` nivel/plataforma provisionales, UTF-16 como binario, pruebas adicionales, constantes y estilo — nivel lo calcula la Historia 11; el resto cosmético o fuera de alcance

## Verification

**Commands:**
- `uv run pytest -q` -- expected: todo pasa
- `uv run ruff check src tests` -- expected: sin errores

## Auto Run Result

Resumen: `FsSoloLectura` (puerto ReadOnlyFs, no sigue enlaces), `recorrer` y `DetectorEnlaces` (TH-6, nivel provisional hipótesis).
Archivos: `infra/fs_solo_lectura.py`, `collectors/enlaces.py`, `contracts/ports.py` (LIMITE_BYTES), `contracts/__init__.py`, `tests/test_recorrido.py`.
Verificación: con el proyecto de prueba 74 pasan, 4 omitidas (EN-03: el enlace simbólico no existe); sin él 73 pasan, 5 omitidas. Ruff limpio.
Sin commit. Riesgo residual: ver los dos `defer`.
