---
title: 'Historia 18. Segundo cálculo independiente del permiso en Windows'
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

**Problema:** el nivel "comprobado" de varios hallazgos depende de un solo cálculo del permiso en Windows (Historia 3); si ese cálculo se equivoca, nadie lo nota.

**Enfoque:** un verificador escrito aparte que calcula los mismos tres hechos (puede leer, entrada propia para Todos, ambiguo) por OTRA vía del sistema: `GetFileSecurityW`, derechos efectivos con `GetEffectiveRightsFromAclW` y la ACL en texto SDDL analizada; y `confirmar(principal, verificador, ruta)` en el núcleo, que dice "confirmado" o "no confirmado". La limitación compartida (ambas leen la misma ACL) queda como texto para el reporte.

## Boundaries & Constraints

**Always:** el verificador no importa nada de `sonda_windows.py`; no abre el archivo; no lanza `icacls` ni programas; misma definición de "ambiguo" que la principal (denegar, entrada no estándar, DACL nula, fallo; la herencia no); `confirmar` nunca lanza y no copia mensajes de excepción; el núcleo no importa infraestructura.

**Never:** decidir el nivel (lo usa la Historia 11); POSIX; verificar reglas deny/ask del agente.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| PP-04 / PP-05 | permiso normal | SI, no abierto, no ambiguo, coincide | — |
| PP-03 | `deny R` | NO, coincide | — |
| PA-01 | entrada propia para Todos | abierto e inequívoco, coincide | — |
| Heredado | Todos solo por herencia | abierto, no ambiguo, coincide | — |
| Todos + denegar | regla deny presente | abierto y ambiguo, coincide | — |
| Par que discrepa | cualquiera de los tres hechos | no confirmado | — |
| Verificador no determina o falla | NO_DETERMINADO o excepción | no confirmado | sin excepción |

</intent-contract>

## Code Map

- `src/agentreach/infra/verificador_permiso_windows.py` -- `VerificadorPermisoWindows`, `analizar_sddl`.
- `src/agentreach/core/verificacion_independiente.py` -- `confirmar`, `comparar`, `Confirmacion`, `LIMITACION_TEXTO`.
- `src/agentreach/contracts/ports.py` -- `PermisosArchivo` (sin cambios).

## Tasks & Acceptance

**Execution:**
- `tests/test_verificador_permiso.py` -- primero
- verificador y `confirmar`

**Acceptance Criteria:**
- Given (a)-(e) de la historia, when se ejecutan, then se cumplen: sin importar la sonda, sin abrir ni ejecutar, coincide en PP-03, PP-04, PP-05 y PA-01, y `confirmar` da "no confirmado" ante cualquier discrepancia.

## Spec Change Log

## Review Triage Log

### 2026-11-09 - Review pass
- verdicts: ~29 findings (ciega 12, casos limite 15 mas 3 de afirmaciones) - high 0, medium 7, low 6, false 0, maybe-false 1
- `[medium]` `[patch]` confirmar no toleraba un resultado mal formado de una sonda (None, otro tipo) - cuenta como fallo y nunca lanza
- `[medium]` `[patch]` el permiso del verificador usaba solo FILE_READ_DATA y "abierto a Todos" tambien los bits genericos - los dos usan los mismos bits
- `[medium]` `[patch]` el analizador de SDDL: "D:" se buscaba como subcadena (se ancla), SID y alias en minusculas, entradas vacias, banderas de largo impar o desconocidas y un D: pegado a otro campo se tratan como no estandar (ambiguo)
- `[medium]` `[patch]` una excepcion inesperada del verificador (API ausente, tipo de ruta raro) lanzaba - queda como no determinado; la primera llamada de tamano debe fallar con ERROR_INSUFFICIENT_BUFFER
- `[low]` `[patch]` pruebas: el nucleo no importa infraestructura (tambien `import x`), limitacion con frases exactas, prueba real de DACL nula que coincide en las dos vias, prueba que corre en cualquier sistema
- `[maybe-false]` ACCESS_DENIED al leer la ACL se lee como "no legible" - es la misma inferencia que hace la sonda principal (comparte el riesgo, dicho en LIMITACION_TEXTO); denegar solo READ_CONTROL sin denegar los datos es un caso raro sin prueba
- `[low]` `[defer]` token filtrado por UAC y SIDs de sesion de inicio (INTERACTIVE) en la ACL; grupos propietario/solo grupo sin prueba; LookupAccountSidW con nombres largos; carrera en la carga perezosa de la API
- `[low]` `[defer]` FR-24 (decir la limitacion en el reporte) y quien llama a `confirmar` llegan con las Historias 11 y 13
- `[reject]` comparar el usuario (las dos vias miden al mismo proceso), un verificador para POSIX (fuera de alcance), "no abre el archivo" porque GetFileSecurityW lo hace por dentro del sistema (no se abre con un manejador propio; la prueba vigila las vias de Python), icacls con nombres locales (se usa el SID *S-1-1-0)

## Verification

**Commands:**
- `uv run pytest -q` -- expected: todo pasa
- `uv run ruff check src tests` -- expected: sin errores

## Auto Run Result

Resumen: `VerificadorPermisoWindows` (segunda via: `GetFileSecurityW`, derechos efectivos con `GetEffectiveRightsFromAclW` y la ACL en texto SDDL analizada) y, en el nucleo, `confirmar`, `comparar`, `Confirmacion` y `LIMITACION_TEXTO`. No importa la sonda de la Historia 3, no abre el archivo ni ejecuta nada.
Archivos: `infra/verificador_permiso_windows.py`, `core/verificacion_independiente.py`, `tests/test_verificador_permiso.py`.
Verificacion: ver el reporte de la vuelta. Ruff limpio. Coincide con la sonda principal en PP-03, PP-04, PP-05 y PA-01, en el permiso heredado de Todos, en Todos con regla de denegar y en una DACL nula.
Sin commit. Riesgo residual: los `defer`.
