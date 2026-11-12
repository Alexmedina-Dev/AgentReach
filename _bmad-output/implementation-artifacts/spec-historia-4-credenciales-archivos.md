---
title: 'Historia 4. Credenciales en archivos (.env y similares)'
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

**Problema:** AgentReach no reconoce archivos de credenciales del proyecto ni qué tipo de secreto guardan.

**Enfoque:** `DetectorCredencialesArchivos` recorre el proyecto (Historia 2), reconoce por nombre `.env`, `.env.*`, `*.env`, `.npmrc`, `credentials.json` y variables con nombre de credencial, y entrega hallazgos TH-1 (o TH-17 si es un token de plataforma en un archivo que no es `.env`) con proveedor y línea. El valor se descarta al instante.

## Boundaries & Constraints

**Always:** solo biblioteca estándar; el valor nunca sale del análisis; línea o "línea no determinada"; plantillas, valores de relleno y referencias se omiten; un archivo conocido ilegible se reporta por nombre (PP-03).

**Never:** nivel real, ubicaciones fuera del proyecto, git, reglas del agente.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| PP-01 | `.env` con 6 variables | 6 hallazgos con proveedor y línea | — |
| PP-02 | `.env.example` | ninguno | — |
| PP-03 | `.env.production` ilegible | 1 hallazgo, línea no determinada | sin traza con contenido |
| AT-08 | `RAILWAY_API_TOKEN=...` en un .txt | TH-17, línea | — |
| NO-01/03/04 | código sin valor, EXAMPLE, `${{ secrets.X }}` | ninguno | — |

</intent-contract>

## Code Map

- `src/agentreach/collectors/detector/patrones.py` -- nombres, relleno y referencias.
- `src/agentreach/collectors/detector/archivos.py` -- clasificación de archivos y análisis.
- `src/agentreach/collectors/archivos_repo.py` -- `DetectorCredencialesArchivos`.
- `src/agentreach/contracts/ports.py` -- `ArchivoNoLegible` (movido desde infra).
- `src/agentreach/infra/localizador.py` -- línea de claves repetidas / JSON.

## Tasks & Acceptance

**Execution:**
- `tests/test_credenciales_archivos.py` -- pruebas primero
- los tres módulos de `collectors` -- implementación

**Acceptance Criteria:**
- Given un valor canario, when se detecta, then no aparece en ningún objeto, texto ni excepción.
- Given PP-01..PP-05, GT-01, PA-01 y AT-08, when se detecta, then salen; PP-02, NO-01, NO-03 y NO-04 no.

## Spec Change Log

## Review Triage Log

### 2026-11-09 - Review pass
- verdicts: ~45 findings (ciega 17, casos limite 24 mas 3 de afirmaciones) - high 0, medium 8, low 8, false 2, maybe-false 0
- `[medium]` `[patch]` .git/node_modules se buscaban en la ruta absoluta: un proyecto bajo esas carpetas salia limpio - ahora solo dentro del proyecto
- `[medium]` `[patch]` relleno sin anclar descartaba claves reales (todo, replace, xxx, localhost en cualquier parte) - patrones anclados y localhost solo como anfitrion
- `[medium]` `[patch]` referencias `${X}`, `$(cmd)`, `%X%` en .env contaban como valores; el criterio "(" descartaba claves reales - patron de referencia estricto y aplicado tambien a .env
- `[medium]` `[patch]` BOM y saltos de linea distintos del localizador (splitlines) daban linea equivocada o fallaban - se quita el BOM y se usan los mismos saltos
- `[medium]` `[patch]` duplicados identicos con variable repetida - se reducen a uno
- `[medium]` `[patch]` .env de mas de 1 MiB (omitido) no daba hallazgo - se reporta por nombre
- `[low]` `[patch]` .npmrc comentado se reportaba y _password no se miraba; valores solo numericos; nombres PASS y _URI
- `[medium]` `[defer]` credentials.json: valor de relleno/vacio, claves anidadas (OAuth), varias claves, proveedor fijo NUBE - mejorar con lectura de valores en la Historia 13 o cuando haya un caso del oraculo
- `[medium]` `[defer]` claves entre comillas (JSON/YAML) y valores multilinea (PEM) en archivos de texto; TH-17 solo para plataformas de despliegue; _KEY$ da falsos positivos (SORT_KEY) - alcance del oraculo; ajustar con casos reales
- `[low]` `[defer]` archivos de texto ilegibles no se anotan como no revisados - los declara el reporte (Historia 13)
- `[false]` ArchivoNoLegible ya no se importa de infra - sigue disponible: infra lo importa de contracts
- `[reject]` otros formatos (.pem, .netrc, tfvars), rendimiento, documentacion, cableado en CLI, pruebas de entorno - fuera del alcance escrito de la historia

## Verification

**Commands:**
- `uv run pytest -q` -- expected: todo pasa
- `uv run ruff check src tests` -- expected: sin errores

## Auto Run Result

Resumen: `DetectorCredencialesArchivos` (TH-1 y TH-17) con patrones por nombre, descarte inmediato del valor, linea o "no determinada", y `ArchivoNoLegible` movido a los contratos.
Archivos: `collectors/archivos_repo.py`, `collectors/detector/{__init__,patrones,archivos}.py`, `contracts/ports.py`, `contracts/__init__.py`, `infra/fs_solo_lectura.py`, `tests/test_credenciales_archivos.py`.
Verificacion: con el proyecto de prueba 132 pasan, 7 omitidas; sin el 128 pasan, 11 omitidas. Ruff limpio. PP-01a a PP-01f, PP-03 a PP-05, GT-01, PA-01, AT-08 y AJ-01 se detectan; PP-02, NO-01, NO-03 y NO-04 no.
Sin commit. Riesgo residual: los `defer` (credentials.json, claves entre comillas, TH-17 acotado a despliegue).
