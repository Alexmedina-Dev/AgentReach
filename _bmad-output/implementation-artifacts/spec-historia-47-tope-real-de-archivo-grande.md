---
title: 'Historia 47. El texto de «archivo demasiado grande» dice el tope real'
type: 'bugfix'
created: '2026-11-17'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
context: ['{project-root}/_bmad-output/planning-artifacts/historias-mvp.md']
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problema:** el recorrido del proyecto no abre archivos de más de `LIMITE_BYTES` (1 MiB, `contracts/ports.py`), pero el catálogo de motivos decía «más de 5 MB». Un archivo de 2 MB salía como «no se pudo revisar» y la persona no entendía por qué.

**Enfoque:** el título del motivo `ARCHIVO_DEMASIADO_GRANDE` calcula el número desde `LIMITE_BYTES` (en español y en inglés), en vez de llevarlo escrito a mano. Si el tope cambia, el texto lo sigue solo.

## Boundaries & Constraints

**Siempre:** el número del texto sale de `LIMITE_BYTES`; no cambia ningún nivel, ningún hallazgo ni el tope de lectura.
**Nunca:** tocar `TOPE_BYTES` de `infra/lectura_segura.py` (5 MB): es otro límite, el de la lectura de archivos de configuración.

## Criterios de aceptación

- El título dice «1 MB» en español y en inglés, y no contiene «5 MB».
- `LIMITE_BYTES` vale 1 MiB; si cambia, esa prueba obliga a decidirlo a propósito.

## Pruebas

`tests/test_historia_47.py` (2 pruebas).

## Notas

El cambio es el mismo que ya estaba hecho y probado en la carpeta vieja (`PruebaAlex`, sin guardar); aquí se aplica sobre `development`. Pendiente para el PR de sincronización de documentos: la ficha en `epics.md` y el estado del avance.

</intent-contract>
