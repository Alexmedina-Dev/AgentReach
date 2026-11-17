---
title: 'Historia 46: lo que sale de `.claude/settings*.json` es de Claude Code'
type: 'bugfix'
created: '2026-11-12'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-3-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** El detector de configuración que se ejecuta sola (`collectors/config_ejecuta_sola.py`) marca todos sus hallazgos como `Plataforma.NO_DETERMINADA` y agente «sin-agente», aunque los de `.claude/settings.json` y `.claude/settings.local.json` solo los lee Claude Code. En el reporte real, `.claude/settings.json:2` salió bajo «Sin agente específico». Con la Historia 40 es peor: esos hallazgos seguirían apareciendo aunque Claude Code no se mostrara.

**Approach:** Lo que sale de `.claude/settings.json` y `.claude/settings.local.json` se atribuye a Claude Code (plataforma `CLAUDE_CODE`, agente `claude-code`): los hooks y `enableAllProjectMcpServers` o `enabledMcpjsonServers` (TH-14) y la bandera que salta los permisos (TH-15). Lo de `.mcp.json`, `.vscode/mcp.json`, `tasks.json` y los ajustes de VS Code sigue «sin agente» (esos nombres los comparten varios agentes, FR-31). No cambia ningún nivel ni motivo: solo a qué agente pertenece el hallazgo.

## Boundaries & Constraints

**Always:** TH-14 y TH-15 siguen en potencial como máximo con motivo «no determinado» (AD-11, SM-1); la etiqueta de agente es `claude-code`, la misma que usa el evaluador; los 67 casos del oráculo siguen siendo los mismos y sus cifras nuevas se calculan de `expected.json`, no se estiman; solo biblioteca estándar.

**Never:** Tocar el evaluador (`core/evaluador.py`, `core/nivel.py`, `core/politica.py`), el adaptador de Claude Code, la compuerta ni `html.py` y `texto.py`; atribuir a un agente lo que sale de `.mcp.json` o `.vscode/`; cambiar un nivel, un motivo o la autocomprobación.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Hook en settings | `hooks` en `.claude/settings.json` | TH-14 de Claude Code, potencial | N/A |
| Servidores MCP en settings | `enableAllProjectMcpServers: true` o `enabledMcpjsonServers` | TH-14 de Claude Code, potencial | N/A |
| Salto de permisos | `bypassPermissions` en `.claude/settings.local.json` | TH-15 de Claude Code, potencial | N/A |
| Servidor de comando en `.mcp.json` | `mcpServers` con `command` | TH-14 sin agente (como hoy) | N/A |
| Archivos de VS Code | `.vscode/mcp.json`, `tasks.json`, ajustes | Sin agente (como hoy) | N/A |
| `--agente opencode` | proyecto con hooks en `.claude/` y servidor en `.mcp.json` | No sale el de `.claude/`; sí el de `.mcp.json` | N/A |
| Solo `.claude/settings.json` | sin otras señales | Claude Code figura entre los configurados y tiene pestaña (Historia 40) | N/A |
| Oráculo | AT-04, AT-12 y AT-06 | Claude Code: potencial; opencode: «no se reporta»; AT-05 y AT-07 sin cambio | Los totales por agente cambian y se documentan |

</frozen-after-approval>

## Code Map

- `src/agentreach/collectors/config_ejecuta_sola.py` -- `detectar` (l.72-90) reúne cuatro fuentes: (a) el adaptador de Claude Code (`config_proyecto`, claves `hooks`, `mcp` y `salto_de_permisos` en `_DEL_ADAPTADOR`, l.55-59), con la ruta en `caso.ubicacion.ruta`; (b) `_bandera` sobre los dos `settings*.json`; (c) `_mcp_json` sobre `.mcp.json` y `.vscode/mcp.json`; (d) `_tasks` y `_ajustes_vscode`. `_hallazgo` (l.135-149) fija `NO_DETERMINADA` y «sin-agente»: necesita un parámetro de plataforma que llegue a `CLAUDE_CODE` solo desde (a) y (b). El origen se distingue por la ruta, no hay identificador de archivo.
- `src/agentreach/core/evaluador.py` (l.96-98), `core/nivel.py` (l.74-75) -- para TH-14 y TH-15 (`Base.CONFIG`) el nivel sale de `calcular(...)` sin mirar la plataforma ni consultar adaptadores: potencial y «no determinado». No se toca; la plataforma del candidato llega intacta al reporte. La etiqueta del evaluador es `claude-code`.
- `src/agentreach/app/agentes.py`, `data/catalogo-agentes.json` -- `.claude/settings*.json` ya es firma fuerte y verificada de Claude Code; `.mcp.json` es débil y está en `COMPARTIDOS`. No se toca.
- `src/agentreach/reporting/gate.py` (l.177-218) -- con la Historia 40 los hallazgos de Claude Code se descartan si Claude Code no se muestra o con `--agente opencode`. Es el comportamiento buscado. No se toca.
- `tests/oraculo/expected.json` y `tests/oraculo/test_oraculo.py` (l.100, 159-171, 206) -- AT-04, AT-12 (TH-14 de `proyecto/.claude/settings.json`) y AT-06 (TH-15 de `settings.local.json`) están como cadena «potencial» para los dos agentes; pasan a `{"claude-code": "potencial", "opencode": "no_se_reporta"}`. `test_expected_json_tiene_los_67_casos` exige las cifras por agente (l.163-171): se recalculan desde `expected.json`.
- `tests/test_config_ejecuta_sola.py` (l.114-180, 383) -- sin aserciones de plataforma hoy; añadir las de esta historia. `tests/test_opencode_1x_2x.py` (l.207) y `tests/test_adaptador_claude_code.py` (l.299) no deben cambiar.
- Documentos con cifras del oráculo: PRD §7.3 (punto 2) y SM-7, FR-17, `historias-mvp.md`, README del oráculo.

## Tasks & Acceptance

**Execution:**
- [ ] `src/agentreach/collectors/config_ejecuta_sola.py` -- parámetro de plataforma y agente en `_hallazgo`; `CLAUDE_CODE` y `claude-code` para lo del adaptador y para `_bandera` de los dos `settings*.json`; el resto, sin agente -- el cambio
- [ ] `tests/test_config_ejecuta_sola.py` -- una prueba por fila de la matriz (plataforma y etiqueta, nivel y motivo sin cambio) -- cubre la matriz
- [ ] `tests/test_historia_46.py` -- reporte de extremo a extremo: TH-14 bajo Claude Code, `.mcp.json` bajo «sin agente», `--agente opencode`, y solo `.claude/settings.json` con pestaña de Claude Code -- lo que ve la persona
- [ ] `tests/oraculo/expected.json` y `tests/oraculo/test_oraculo.py` -- AT-04, AT-12 y AT-06 como diccionario por agente y las cifras por agente recalculadas -- el oráculo
- [ ] `_bmad-output/planning-artifacts/prds/prd-agent-reach-2026-11-05/prd.md` (§7.3, SM-7, FR-17), `historias-mvp.md` y README del oráculo -- las cifras nuevas, con los números reales -- documentación
- [ ] `sprint-status.yaml` y `epics.md` -- estado de la historia 46 -- seguimiento

**Acceptance Criteria:**
- Given un proyecto con `hooks` en `.claude/settings.json`, when se genera el reporte, then el TH-14 sale en la pestaña de Claude Code y no bajo «Sin agente específico».
- Given un servidor de comando en `.mcp.json`, when se genera el reporte, then sigue bajo «Sin agente específico».
- Given `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach`, when se ejecutan la suite, el oráculo y las reglas no negociables, then pasan sin omitirlos, con los mismos 67 casos y con las cifras por agente documentadas.
- Given `ruff`, when se ejecuta, then pasa.

## Implementation Notes

## Spec Change Log

## Review Triage Log

| # | Revisor | Hallazgo | Veredicto | Ruta | Evidencia |
|---|---------|----------|-----------|------|-----------|
| 1 | Ciego, casos límite | Todo lo del adaptador se marca como Claude Code sin mirar la ruta | false | rechazado | `_casos_del_proyecto` del adaptador (l.278-289) solo lee `.claude/settings*.json`; el adaptador de opencode no se usa aquí |
| 2 | Ciego | `_bandera` pasa `claude_code` por posición y el resto por nombre | low | patch (hecho) | Ahora `claude_code=claude_code` |
| 3 | Ciego | No se prueba `~/.claude/settings.json` ni la configuración gestionada | false | rechazado | Este detector solo revisa el proyecto; el equipo lo lee el adaptador con el permiso de reglas |
| 4 | Casos límite | Posibles duplicados entre el caso del adaptador y `_bandera` en la misma línea | low | rechazado | Existía igual antes; la atribución no los crea, y el oráculo (AT-06) pasa |
| 5 | Ciego, casos límite | `claude_code` es un booleano con valor por defecto; un llamador nuevo caería en «sin agente» | low | rechazado | Hoy hay dos llamadores y las pruebas fallan si se revierte |
| 6 | Ciego | Las cifras de «no se reporta» del oráculo no se afirman por agente | low | rechazado | `test_cada_caso_coincide_con_el_oraculo` ya comprueba cada caso por agente |
| 7 | Ciego | La prueba de `--agente opencode` mira solo el nombre de archivo | low | rechazado | Mira el reporte entero de ambos agentes; no hay otra ruta posible |
| 8 | Casos límite | Sin caso de `settings.json` mal formado | low | rechazado | La atribución no depende de que se pueda interpretar el JSON |
| 9 | Ciego | Ayudantes de prueba repetidos, documentación sin actualizar | false | rechazado | PRD, SM-7, README del oráculo, `avance-del-proyecto.md` y `epics.md` ya están al día |
| 10 | Brechas | Ninguna brecha de verificación | n/a | n/a | Revertir la bandera en cualquier sentido hace fallar las pruebas |

## Design Notes

Decisión al planificar: TH-15 (la bandera que salta los permisos) también pasa a Claude Code cuando sale de `.claude/settings*.json`, por coherencia con el título de la historia: `bypassPermissions` y sus equivalentes son de Claude Code. Efecto esperado en el oráculo: Claude Code queda en 13 comprobados, 33 potenciales y 2 hipótesis (sin cambio) y opencode baja en 3 potenciales (AT-04, AT-12 y AT-06) que pasan a «no se reporta»; el implementador debe confirmarlo corriendo el oráculo y documentar los números exactos.

## Verification

**Commands:**
- `uv run ruff check src tests` -- expected: All checks passed
- `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach uv run pytest -q` -- expected: todo pasa; el oráculo no se omite

**Manual checks (if no CLI):**
- Alex ejecuta `agentreach` sobre proyecto real local y confirma que `.claude/settings.json:2` y `.claude/settings.local.json:2` salen bajo Claude Code.
