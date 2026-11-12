---
title: 'Historia 5b. Primera ejecución completa (rebanada mínima)'
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

**Problema:** hasta la Historia 5 las piezas existían, pero `agentreach` solo imprimía la versión.

**Enfoque:** `agentreach <carpeta>` conecta los detectores terminados (enlaces, credenciales en archivos, ubicaciones sensibles con opt-in) mediante la tubería y imprime un reporte de texto provisional. No agrega detección nueva.

## Boundaries & Constraints

**Always:** solo lectura; sin red ni programas externos; todo detector pasa por `app/auditar.py` y la tubería; nivel impreso siempre `potencial (provisional)`; nunca valores de secretos; `NoRevisado` visible con su motivo.

**Never:** niveles reales, explicaciones, JSON, escribir archivos, reabrir historias ya hechas.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior |
|----------|--------------|---------------------------|
| Carpeta válida | proyecto con `.env` | `ruta:línea  TH-1 credencial en archivo  potencial (provisional)`, código 0 |
| Archivo gigante / no UTF-8 | 5 MB + 1 byte, bytes inválidos | sección "No se pudo revisar" con `archivo_demasiado_grande` / `codificacion_no_utf8` |
| Sin opt-in | sin flag | `~/.ssh`, `~/.aws`, `~/.npmrc` como `ubicacion_sensible_sin_activar` |
| Carpeta inexistente o archivo | ruta inválida | mensaje breve en stderr, código 2 |
| Hallazgo comprobado | inyectado | código 1 |

</intent-contract>

## Code Map

- `src/agentreach/app/auditar.py` -- registro de detectores (una línea cada uno), tubería, reúne `no_revisados`.
- `src/agentreach/reporting/texto_minimo.py` -- formato provisional (lo reemplaza `reporting/texto.py` en la Historia 13).
- `src/agentreach/cli/__init__.py` -- argumento posicional `carpeta`, código de salida; `parsear_argumentos` sigue devolviendo `Configuracion`; sin carpeta se conserva el aviso pre-MVP.
- `tests/test_primera_ejecucion.py` -- pruebas con `main(argv)`, canarios armados en la prueba, árbol idéntico, sin procesos, opt-in, códigos de salida y caso real (con `AGENTREACH_PROYECTO_PRUEBA`).

## Auto Run Result

Status: done. `uv run pytest -q`: 215 passed, 8 skipped (con `AGENTREACH_PROYECTO_PRUEBA`); `ruff check src tests`: limpio.
Límite: la segunda corrida sobre la raíz de la carpeta de prueba (entra en `trampas*`) queda detrás de `AGENTREACH_PRUEBA_RAIZ=1` y no se ejecutó. El criterio (g) lo confirma Alex a mano.
