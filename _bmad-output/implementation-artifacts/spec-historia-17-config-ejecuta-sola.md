---
title: 'Historia 17. Configuración del proyecto que se ejecuta sola'
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

**Problema:** una carpeta puede traer configuración que ejecuta un programa al abrirla (hooks, servidores MCP de comando, tareas de VS Code) o que quita los frenos del agente (`bypassPermissions`, auto-aprobar), y AgentReach no lo marcaba.

**Enfoque:** `DetectorConfigEjecutaSola` lee solo texto del proyecto: usa los hechos del adaptador de Claude Code (hooks, MCP, bypass) y un lector propio de JSON con comentarios para `.mcp.json`, `.vscode/tasks.json` y `.vscode/settings.json`. Entrega TH-14, TH-15 y TH-16 con archivo y línea, y un rótulo por caso para el texto con la versión corregida. Nunca copia el comando ni ejecuta nada.

## Boundaries & Constraints

**Always:** nada se ejecuta; el comando y sus argumentos nunca salen; JSON con comentarios y comas finales se lee con el lector propio y la profundidad máxima 64; lo que no se puede leer sale como `NoRevisado`; `enableAllProjectMcpServers: false` y los controles CA-01/CA-04 no se reportan.

**Never:** nivel (máximo potencial, lo calcula la Historia 11); `ANTHROPIC_BASE_URL` y otras redirecciones, Cursor, `npx -y` sin versión, versiones del agente (fase 2).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| AT-04 | hooks en settings.json | TH-14, línea de `hooks` | — |
| AT-05 | `.mcp.json` con `command` | TH-14, línea de `command` | — |
| AT-06 | bypassPermissions | TH-15 | — |
| AT-07 | `runOn: folderOpen` | TH-16 | — |
| AT-12 | enableAllProjectMcpServers true | TH-14 (false: nada) | — |
| allowAutomaticTasks "on" | settings.json de VS Code | TH-16 y TH-15, rótulo freno_desactivado | — |
| JSON roto, 65 niveles, no UTF-8, gigante, tubería | archivo hostil | `NoRevisado` con motivo | sin excepción |

</intent-contract>

## Code Map

- `src/agentreach/infra/json_con_comentarios.py` -- `parsear_jsonc`, `limpiar_jsonc`.
- `src/agentreach/collectors/config_ejecuta_sola.py` -- `DetectorConfigEjecutaSola`.
- `src/agentreach/adapters/claude_code/__init__.py` -- `enabledMcpjsonServers` cuenta como el caso "mcp".
- `src/agentreach/app/auditar.py` -- registro.

## Tasks & Acceptance

**Execution:**
- `tests/test_config_ejecuta_sola.py` -- primero
- lector, detector, ajuste del adaptador y registro

**Acceptance Criteria:**
- Given (a)-(d) y AT-04 a AT-07 y AT-12, when se ejecutan, then se cumplen y CA-01/CA-04 no generan estos hallazgos.

## Spec Change Log

## Review Triage Log

### 2026-11-09 - Review pass
- verdicts: ~27 findings (ciega 13, casos limite 12 mas 2 de afirmaciones) - high 0, medium 9, low 5, false 1, maybe-false 1
- `[medium]` `[patch]` dos casos en la misma linea se pisaban los rotulos (hooks y mcp) - la clave es (ruta, linea, tipo) y el valor la tupla de rotulos
- `[medium]` `[patch]` un BOM de Windows y un retorno de carro suelto hacian fallar el lector (un comentario se tragaba el resto del archivo) - arreglado
- `[medium]` `[patch]` la bandera que salta los permisos no se buscaba en un archivo que no se podia interpretar, y una mencion en un comentario contaba - se busca en el texto sin comentarios (o crudo si no se puede limpiar)
- `[medium]` `[patch]` variantes de la bandera: --allow-dangerously-skip-permissions y --permission-mode bypassPermissions (con espacio o con =)
- `[medium]` `[patch]` autoApprove en forma de objeto con algun true se pasaba por alto; entradas de tarea mal formadas se descartaban en silencio - se informan
- `[medium]` `[patch]` .vscode/mcp.json (clave `servers`) era una superficie sin mirar; enabledMcpjsonServers con elementos vacios o que no son texto daba falso TH-14
- `[low]` `[patch]` parametro muerto, separador '/' en rutas de Windows
- `[low]` `[defer]` claves duplicadas en un JSON (el localizador no adivina: linea no determinada); mencion de la bandera dentro de una cadena o regla deny; la bandera en package.json, Makefile, scripts, CI y archivos de contexto
- `[low]` `[defer]` *.code-workspace, tareas por plataforma (windows/linux/osx), chat.tools.global.autoApprove, .devcontainer y .cursor/mcp.json (Cursor es fase 2)
- `[maybe-false]` task.allowAutomaticTasks en el .vscode/settings.json del proyecto podria no tener efecto (VS Code lo honra en el usuario) - se mantiene el reporte, que pide la historia; sin fuente verificada
- `[false]` hallazgos duplicados con DetectorClaudeCode - ese detector solo emite TH-10 y TH-11
- `[reject]` nivel provisional (Historia 11), rotulos y no_revisados que aun no llegan al reporte (Historia 13), atribucion de plataforma, doble lectura de la configuracion de Claude

## Verification

**Commands:**
- `uv run pytest -q` -- expected: todo pasa
- `uv run ruff check src tests` -- expected: sin errores

## Auto Run Result

Resumen: `DetectorConfigEjecutaSola` (TH-14, TH-15, TH-16) con los hechos del adaptador de Claude Code (hooks, MCP, bypassPermissions, enabledMcpjsonServers) y un lector propio de JSON con comentarios y comas finales (`infra/json_con_comentarios.py`) para .mcp.json, .vscode/mcp.json, tasks.json y settings.json de VS Code. Nunca copia el comando ni ejecuta nada.
Archivos: `infra/json_con_comentarios.py`, `collectors/config_ejecuta_sola.py`, `adapters/claude_code/__init__.py`, `app/auditar.py`, `tests/test_config_ejecuta_sola.py`, `tests/test_primera_ejecucion.py`.
Verificacion: ver el reporte de la vuelta. Ruff limpio. AT-04, AT-05, AT-06, AT-07 y AT-12 se detectan; CA-01 y CA-04 no.
Sin commit. Riesgo residual: los `defer`.
