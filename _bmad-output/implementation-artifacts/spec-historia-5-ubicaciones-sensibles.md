---
title: 'Historia 5. Ubicaciones sensibles: claves SSH, nube y .npmrc'
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

**Problema:** AgentReach no sabe si el usuario tiene claves SSH, credenciales de nube o un `.npmrc` en su carpeta personal, que un agente podría alcanzar.

**Enfoque:** `DetectorUbicacionesUsuario` mira solo metadatos de `~/.ssh`, `~/.aws` y `~/.npmrc`, solo con opt-in (flag o archivo global, nunca el proyecto). Con el opt-in apagado no toca el disco y cada ubicación sale como `NoRevisado(ubicacion_sensible_sin_activar)`.

## Boundaries & Constraints

**Always:** opt-in apagado por defecto; solo metadatos, nunca contenido; tipo comprobado con `lstat` antes de pedir permisos; enlaces y tuberías como `NoRevisado(no_es_archivo_regular)`; solo biblioteca estándar.

**Never:** `~/.gnupg`, kubeconfig, credenciales de agentes; leer contenido; que un archivo del proyecto active el opt-in.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Opt-in apagado | home-falso | sin hallazgos, 3 NoRevisado, sin tocar disco | — |
| Opt-in encendido | home-falso | HF-01 TH-2, HF-03 TH-3, HF-05 TH-1 | — |
| HF-02 / HF-04 | .pub, known_hosts, .aws/config | no se reportan | — |
| Tubería o enlace en .ssh | entrada no regular | NoRevisado, sin pedir permisos | — |
| Política en el proyecto | archivo con la clave en true | sigue apagado | — |

</intent-contract>

## Code Map

- `src/agentreach/collectors/ubicaciones_usuario.py` -- `DetectorUbicacionesUsuario`.
- `src/agentreach/config/__init__.py` -- `Configuracion`, `cargar_configuracion(flags, archivo_global)`.
- `src/agentreach/cli/__init__.py` -- flags `--incluir-ubicaciones-sensibles` y `--home`.
- `src/agentreach/contracts/ports.py` -- `Metadatos.es_regular`; `infra/fs_solo_lectura.py` lo calcula con `lstat`.

## Tasks & Acceptance

**Execution:**
- `tests/test_ubicaciones_sensibles.py` -- primero
- config, collectors, cli, ports, fs_solo_lectura

**Acceptance Criteria:**
- Given (a)-(e) de la historia, when se ejecutan, then se cumplen y HF-01, HF-03, HF-05 se detectan; HF-02 y HF-04 no.

## Spec Change Log

## Review Triage Log

### 2026-11-09 - Review pass
- verdicts: ~38 findings (ciega 17, casos limite 13 mas 1 de afirmacion) - high 0, medium 7, low 7, false 0, maybe-false 0
- `[medium]` `[patch]` clave privada con nombre no estandar (github, id_rsa.bak) no se detectaba - en ~/.ssh se reporta todo archivo regular salvo la lista de publicos/configuracion
- `[medium]` `[patch]` archivo global con ruta relativa podria caer dentro del proyecto - una ruta no absoluta nunca activa nada; la ruta se calcula al pedirla, no al importar
- `[medium]` `[patch]` listar/metadatos de ~/.ssh lanzaba OSError y abortaba todo - ahora NoRevisado y se sigue con lo demas
- `[medium]` `[patch]` Metadatos.es_regular fallaba abierto (default True) - ahora False
- `[medium]` `[patch]` home inexistente o relativo parecia "sin hallazgos" - sale NoRevisado; .npmrc que es carpeta se informa
- `[low]` `[patch]` doble stat en listar; sonda que falla; CLI callaba una configuracion global mala (ahora aviso por stderr); docstring "el flag manda" falso; os.chdir en pruebas
- `[low]` `[defer]` carpeta ~/.ssh que es enlace (gestores de dotfiles) se informa como no revisada sin mas explicacion; --home sin validar en la CLI; el detector aun no esta cableado en un reporte
- `[reject]` flag para apagar el opt-in global (store_true no lo distingue; fuera de alcance), nombres de flags provisionales (SUPUESTO ya marcado), cobertura extra de pruebas, nivel provisional

## Verification

**Commands:**
- `uv run pytest -q` -- expected: todo pasa
- `uv run ruff check src tests` -- expected: sin errores

## Auto Run Result

Resumen: `DetectorUbicacionesUsuario` (TH-2, TH-3, TH-1) solo con opt-in y solo metadatos; `Configuracion` y `cargar_configuracion` (flag o archivo global, nunca el proyecto); flags `--incluir-ubicaciones-sensibles` y `--home`; `Metadatos.es_regular` medido con lstat.
Archivos: `collectors/ubicaciones_usuario.py`, `config/__init__.py`, `cli/__init__.py`, `contracts/ports.py`, `infra/fs_solo_lectura.py`, `tests/test_ubicaciones_sensibles.py`.
Verificacion: con el proyecto de prueba 189 pasan, 7 omitidas; sin el 184 pasan, 12 omitidas. Ruff limpio. HF-01, HF-03 y HF-05 se detectan; HF-02 y HF-04 no; con el opt-in apagado no se toca el disco.
Sin commit. Riesgo residual: los `defer`.
