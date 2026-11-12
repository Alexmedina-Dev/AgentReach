---
title: 'Historia 9. Adaptador de Claude Code'
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

**Problema:** AgentReach no entiende las reglas de Claude Code: no sabe qué lee o niega su política, qué entorno hereda, si hay sandbox ni qué agentes hay definidos.

**Enfoque:** `AdaptadorClaudeCode` (capacidad "auditar y advertir") lee la configuración de cuatro niveles (gestionada, local, proyecto, usuario; las dos externas solo con el opt-in) con la lectura segura y entrega reglas con archivo y línea, solo nombres del entorno, definiciones de agente y los hechos de la configuración del proyecto que se ejecuta sola. Un kit de conformidad común (`adapters/conformance`) comprueba que cualquier adaptador informa lo que no puede leer y nunca filtra valores.

## Boundaries & Constraints

**Always:** reglas = contexto, no hallazgo propio; hallazgo solo TH-10 (sin sandbox en Windows nativo) y TH-11 (agentes); del entorno solo nombres; todo se lee con `leer_seguro`; una configuración que no se reconoce da `NoRevisado`, nunca una excepción; deny > ask > allow; la versión corregida de los tres casos del proyecto es texto fijo.

**Never:** nivel, bloquear nada, leer transcripciones, ejecutar Claude Code.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| CA-01 | settings.json con 3 allow, 2 ask, 1 deny | 6 reglas con archivo y línea, sin hallazgo | — |
| CA-02 | Windows nativo | TH-10 | — |
| CA-03 | env con limpieza activada | solo nombres y `limpieza_de_entorno` | valor nunca sale |
| CA-05 | `.claude/agents/revisor-ejemplo.md` | TH-11 con su nombre y la línea de `tools:` | cuerpo no sale |
| JSON roto / forma rara / 65 niveles / no UTF-8 / gigante / tubería | configuración hostil | `NoRevisado` con motivo | sin excepción |

</intent-contract>

## Code Map

- `src/agentreach/adapters/base.py` -- `Regla`, `DefinicionAgente`, `CasoConfigProyecto`, `ResultadoAdaptador`, `AdaptadorBase`.
- `src/agentreach/adapters/claude_code/` -- `__init__.py` (adaptador y `DetectorClaudeCode`), `reglas.py` (globs y precedencia), `catalogo.py` (tres casos con versión corregida).
- `src/agentreach/adapters/conformance/__init__.py` -- `ejecutar_conformidad`.
- `src/agentreach/app/auditar.py` -- registro.

## Tasks & Acceptance

**Execution:**
- `tests/test_adaptador_claude_code.py` -- primero
- base, adaptador, reglas, catálogo, kit y registro

**Acceptance Criteria:**
- Given (a), (b), (b2) y los casos CA-01, CA-02, CA-03 y CA-05, when se ejecutan, then se cumplen.

## Spec Change Log

## Review Triage Log

### 2026-11-09 - Review pass
- verdicts: ~34 findings (ciega 17, casos limite 14 mas 3 de afirmaciones) - high 0, medium 10, low 6, false 0, maybe-false 0
- `[medium]` `[patch]` `cargar` podia lanzar ValueError con una ruta rara - se informa como NoRevisado
- `[medium]` `[patch]` una regla Read sin especificador (bloqueo total) se ignoraba - alcanza a todos los archivos
- `[medium]` `[patch]` una regla con texto que no se entiende se descartaba en silencio - se informa (configuracion_no_interpretable)
- `[medium]` `[patch]` la limpieza del entorno no respetaba la precedencia (el valor 0 de una fuente superior no ganaba) - decide la fuente de mayor precedencia
- `[medium]` `[patch]` patrones "./", ".", "/" y "~/" (toda la carpeta base) no alcanzaban a nada; rutas relativas se resolvian contra el directorio actual - arreglado
- `[medium]` `[patch]` hooks en forma de lista se ignoraban; agentes con lista entre corchetes, BOM o sin `tools` (hereda todas: el caso mas amplio) - arreglado, con `hereda_todas`
- `[medium]` `[patch]` el kit se caia con argumentos peligrosos o con un adaptador que no cumple el contrato - valida ruta relativa y clave, y anota el fallo; prueba de que detecta una fuga del valor
- `[low]` `[patch]` nombres de entorno sin sanear; mayusculas segun el sistema inyectado (no el real); import muerto; pruebas tautologicas
- `[low]` `[defer]` agentes en subcarpetas de .claude/agents y agentes de plugins; enlaces dentro de la ruta de un archivo (sin realpath); ~/.claude.json, CLAUDE_CONFIG_DIR y .mcp.json no se leen; frontmatter YAML completo
- `[medium]` `[defer]` TH-10 sale en toda auditoria en Windows aunque el proyecto no use Claude Code (CA-02 pide "solo en Windows"); el catalogo de los tres casos lo consume la Historia 17
- `[reject]` nivel provisional (Historia 11), versiones y CVE sin enlace (provienen del informe aprobado y estan en la especificacion), estado mutable del adaptador (un adaptador por auditoria), un hallazgo TH-11 por archivo de agente

## Verification

**Commands:**
- `uv run pytest -q` -- expected: todo pasa
- `uv run ruff check src tests` -- expected: sin errores

## Auto Run Result

Resumen: `AdaptadorClaudeCode` (capacidad auditar y advertir) con reglas allow/ask/deny con archivo y linea, postura de lectura (deny > ask > allow, fuente de mayor precedencia), solo nombres del entorno, definiciones de agente, sandbox ausente en Windows nativo y los hechos de la configuracion del proyecto que se ejecuta sola, mas el catalogo de los tres casos con su version corregida. `DetectorClaudeCode` entrega TH-10 y TH-11. Modulo base comun (`adapters/base.py`) y kit de conformidad reutilizable (`adapters/conformance`).
Archivos: `adapters/base.py`, `adapters/claude_code/{__init__,reglas,catalogo}.py`, `adapters/conformance/__init__.py`, `app/auditar.py`, `tests/test_adaptador_claude_code.py`, `tests/test_primera_ejecucion.py`.
Verificacion: ver el reporte de la vuelta. Ruff limpio. CA-01 y CA-03 no son hallazgo; CA-02 (TH-10) y CA-05 (TH-11) si.
Sin commit. Riesgo residual: los `defer`.
