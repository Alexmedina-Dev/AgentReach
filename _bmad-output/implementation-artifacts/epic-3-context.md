# Epic 3 Context: Saber con cuánta certeza llega el agente

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Cada hallazgo debe llegar con su nivel de confianza (comprobado, potencial o hipótesis) y su motivo, calculado con los permisos reales de Windows y las reglas de Claude Code y opencode, para que la persona distinga "no lo sé" de "sé que no se puede". Incluye marcar lo ajeno a la tarea, el tope por nombre y la atribución correcta de cada hallazgo a su agente. La épica está terminada salvo las Stories 3.12 y 3.13, añadidas el 2026-11-12 y pendientes.

## Stories

- Story 3.1: Permisos del sistema en Windows
- Story 3.2: Adaptador de Claude Code
- Story 3.3: Adaptador de opencode
- Story 3.4: opencode 1.x y 2.x
- Story 3.5: Configuración del proyecto que se ejecuta sola
- Story 3.6: Segundo cálculo independiente del permiso
- Story 3.7: Cálculo del nivel de confianza y sus invariantes
- Story 3.8: Correcciones de la revisión de las historias 9 a 11
- Story 3.9: Claves repetidas, patrones con `./` o `..` y `.claude` que es un archivo
- Story 3.10: «Ajeno a la tarea»
- Story 3.11: Tope por nombre y letras de las preguntas
- Story 3.12: ¿`ORCA_PANE_KEY` es una credencial? Confirmar antes de ajustar la regla (pendiente)
- Story 3.13: Lo que sale de `.claude/settings*.json` es de Claude Code (pendiente)

## Requirements & Constraints

- El nivel sigue una tabla de decisión; una regla `deny` o `ask` del agente nunca borra ni oculta el hallazgo.
- Sin fuente verificada, el máximo es potencial; una credencial reconocida solo por su nombre nunca sale comprobada.
- Un archivo existente pero ilegible se trata de forma explícita, no se ignora.
- Los adaptadores de Claude Code y opencode (1.x y 2.x) deben tener la misma calidad; el adaptador es agnóstico del agente.
- Un segundo cálculo independiente del permiso (sin compartir código con el primero) debe confirmar todo "comprobado".
- Un nombre de archivo compartido por varios agentes (p. ej. `.mcp.json`) no asigna un agente; queda "sin agente específico".
- Meta de producto: cero "comprobado" falsos.

## Technical Decisions

- El nivel lo decide una sola función; `NIVEL_MAXIMO` pone el tope por tipo de hallazgo. Una segunda pasada de invariantes solo puede bajar un nivel, nunca subirlo, y se aplica antes de imprimir.
- En Windows el permiso se calcula con `ctypes` (lectura de ACL y comprobación de acceso efectivo) sin abrir el archivo, sin `icacls` ni `pywin32`. Todo lo dudoso baja a "no determinado". `icacls` solo aparece como texto sugerido, nunca se ejecuta. En POSIX solo `os.access` y modo; sin verificador. La sonda mide al usuario que ejecuta AgentReach, no al agente real.
- Si el agente tiene una función no modelada (p. ej. hooks `PreToolUse`), el nivel queda no determinado y se informa archivo y clave, nunca el valor.
- Piezas relevantes: `core/nivel.py`, `core/politica.py`, `core/invariantes.py`, `core/evaluador.py`, `adapters/`, `collectors/config_ejecuta_sola.py`, `collectors/detector/patrones.py`.
- 3.12: si se confirma que `ORCA_PANE_KEY` es un identificador, la excepción es una lista corta de nombres exactos, nunca por sufijo `_KEY`; `ORCA_AGENT_HOOK_TOKEN` debe seguir reportándose. Si no se confirma, no cambia ninguna regla.
- 3.13: el detector atribuye a Claude Code lo de `.claude/settings.json` y `.claude/settings.local.json`; `.mcp.json` sigue sin agente. No cambia ningún nivel, solo la pertenencia.

## Cross-Story Dependencies

- 3.5 depende de 3.2 (lee reglas de Claude Code).
- 3.12 depende de la Story 1.7 (detector por nombre) y exige que el caso nuevo del oráculo no altere los otros 67.
- 3.13 depende de 2.2 y 3.5; obliga a recalcular `tests/oraculo/expected.json` y las cifras de SM-7 del PRD (conteos por agente), y debe respetar la regla de la Historia 40 (no ocultar un agente configurado con pestaña) y el filtro `--agente`.
- Las letras `(S/N)` de la 3.11 pertenecen a FR-30 (Épica 5); sus cifras del oráculo: 13 comprobado, 33 potencial, 2 hipótesis por agente (desde la Historia 46, opencode: 13, 30 y 2).
