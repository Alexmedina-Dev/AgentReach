---
title: 'Historia 40: un agente que no está en la carpeta ni en el equipo no aparece'
type: 'feature'
created: '2026-11-12'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-6-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** El reporte arma una pestaña y un listado por cada agente que AgentReach sabe analizar (Claude Code y opencode), con hallazgos, aunque el agente no esté en la carpeta ni en el equipo. En el reporte real de proyecto real local (2026-11-12) opencode tuvo 4 hallazgos y no figuraba entre los agentes configurados. Alex: «muestra cosas que no son».

**Approach:** Un agente con adaptador solo se muestra (terminal y HTML) si aparece entre los «Agentes configurados» del propio reporte. Si no se detecta ninguno, se muestran los dos con la aclaración «analizado sin señales de configuración»; con `--agente` se muestra el pedido aunque no se detecte, con la misma aclaración. El código de salida cuenta solo los agentes mostrados. El filtrado va en la compuerta (`gate.preparar`); no cambia el cálculo de ningún nivel.

## Boundaries & Constraints

**Always:** Regla única y explicable: hay pestaña y sección de un agente ⇔ aparece en «Agentes configurados», con cualquier confianza (también hipótesis). «Sin agente específico» (`none`) sigue como hoy. Todo texto nuevo sale de los catálogos fijos (AD-16), en español con tú y usted y en inglés; el esquema de datos del HTML solo crece con un campo opcional (AD-17); todo pasa por la compuerta (AD-15). Solo biblioteca estándar.

**Never:** Cambiar el cálculo de un nivel, los hallazgos de un agente que sí se muestra, el oráculo (sus 67 casos siguen igual con los dos agentes detectados), `--estricto` ni la lista de «no se pudo revisar». Ocultar un agente cuando no se detecta ninguno. Añadir dependencias.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Solo Claude Code detectado | `.claude/settings.json`, sin `opencode.json`, `--home` vacío | Claude Code y «Sin agente específico»; ninguna sección de opencode en terminal ni HTML | N/A |
| Solo opencode detectado | `opencode.json`, sin `.claude` | opencode y «Sin agente específico»; ningún Claude Code | N/A |
| Los dos detectados | proyecto del oráculo (`.claude` y `opencode.json`) | Los dos, con los mismos hallazgos y niveles de siempre | N/A |
| Ninguno detectado | carpeta con solo `.env` | Los dos agentes, cada uno con «analizado sin señales de configuración» | Nunca un reporte sin agentes |
| `--agente opencode` sin detectar | solo Claude Code | opencode y «Sin agente específico», con la aclaración | N/A |
| `--agente opencode` detectado | opencode presente | Igual que hoy, sin aclaración | N/A |
| Hallazgo comprobado de un agente oculto | comprobado solo en opencode no detectado | No cuenta para el código de salida; si opencode se muestra, cuenta | N/A |
| Detección por hipótesis | solo firma débil de un agente | Aparece en «Agentes configurados» y, por tanto, tiene pestaña | N/A |
| Sin permiso de reglas del usuario | respuesta «n» a la segunda pregunta | Sin leer el equipo; si el proyecto no tiene señales, se muestran los dos con la aclaración | N/A |

</frozen-after-approval>

## Code Map

- `src/agentreach/reporting/gate.py` -- `preparar` (l.173-284): ya filtra por `agente` en correcciones (l.187), hallazgos (l.198), reglas (l.217) y configurados (l.240-246); el código de salida se calcula con los hallazgos ya filtrados (`codigo_de_salida`, l.166-170, llamado en l.280). Aquí se decide qué plataformas se muestran y se añade `sin_senales` a `DatosReporte`. No hay mapeo central id↔`Plataforma` (duplicado en `cli/__init__.py` l.155, `gate.py` l.241, `html.py` `_ID`, `tests/oraculo`): crear una función y usarla solo en lo nuevo.
- `src/agentreach/app/agentes.py` -- `AgenteDetectado` (id `claude-code`/`opencode`, `analizado`, confianza); `ANALIZADOS` (l.77). No se toca.
- `src/agentreach/reporting/html.py` -- `_agentes` (l.95-128): hoy emite siempre `claude_code` y `opencode`; pasa a omitir los no mostrados y a marcar `no_signals`. Campo opcional nuevo en `docs/reporte-html/esquema-datos.md` y `.schema.json`.
- `src/agentreach/reporting/plantilla_reporte.html` (copia idéntica en `docs/reporte-html/plantilla.html`) -- pestañas (`AGENTS_DEF`, l.~1238) y diccionarios es/en (`notAnalyzed`, l.743/790): texto de la aclaración en el panel del agente.
- `src/agentreach/reporting/texto.py` -- `_secciones` (l.505), `reglas` (l.355), `no_determinado` (l.443) iteran `(CLAUDE_CODE, OPENCODE)`; `configurados` (l.415) es el bloque «AGENTES CONFIGURADOS»; textos en `_T` (l.98-190, con la variante formal tras l.187).
- Pruebas que fijan «siempre los dos»: `tests/test_reporte_html.py` (l.209-250, 272), `test_historia_24.py`, `test_historia_25.py`, `test_historia_28.py`, `test_reporte.py`; oráculo en `tests/oraculo/` y `tests/reglas_no_negociables/test_sin_valores_de_secretos.py` (necesitan `AGENTREACH_PROYECTO_PRUEBA`). Los `DatosReporte` hechos a mano sin `configurados` caen en «ninguno detectado»: siguen mostrando los dos.
- Repro mínimo: `tmp_path` con `p/.claude/settings.json` y `p/.env`, `--home` vacío y absoluto (el `.env` es nombre compartido y no cuenta; fixtures `mundo`/`poner` en `tests/test_historia_24.py`).

## Tasks & Acceptance

**Execution:**
- [ ] `src/agentreach/reporting/gate.py` -- función de plataformas mostradas (detectados ∪ `--agente`; ninguno → los dos con `sin_senales`), filtrar hallazgos, reglas, causas y correcciones, y `sin_senales` en `DatosReporte` -- el filtrado y el código de salida coherente
- [ ] `src/agentreach/reporting/html.py`, `docs/reporte-html/esquema-datos.*` -- omitir agentes no mostrados y `no_signals` opcional por agente -- el HTML
- [ ] `src/agentreach/reporting/plantilla_reporte.html` y `docs/reporte-html/plantilla.html` -- aclaración en el panel del agente, es y en -- lo que ve la persona
- [ ] `src/agentreach/reporting/texto.py` -- secciones, reglas, no determinado y bloque de configurados filtrados, con la aclaración (tú, usted, inglés) -- la terminal
- [ ] `tests/test_historia_40.py` -- cada fila de la matriz (terminal y HTML) y el código de salida; ajustar solo lo necesario en las pruebas que suponían «siempre los dos», con comentario -- cubre la matriz
- [ ] `_bmad-output/implementation-artifacts/sprint-status.yaml` y `epics.md` -- estado de la historia 40 -- seguimiento

**Acceptance Criteria:**
- Given proyecto real local (solo Claude Code), when se genera el reporte, then no hay nada de opencode en la terminal ni en el HTML.
- Given el proyecto de prueba del oráculo y `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach`, when se ejecutan la suite, el oráculo y las reglas no negociables, then pasan sin omitirlos y con los mismos resultados.
- Given `ruff`, when se ejecuta, then pasa.

## Implementation Notes

## Spec Change Log

## Review Triage Log

| # | Revisor | Hallazgo | Veredicto | Ruta | Evidencia |
|---|---------|----------|-----------|------|-----------|
| 1 | Ciego | El texto «sin señales» dice «en la carpeta ni en el equipo» aunque con «n» el equipo no se miró | medium | patch | Redactado sin afirmar lo no revisado |
| 2 | Ciego | Líneas «analizado sin señales» bajo el título «AGENTES CONFIGURADOS» se contradicen | medium | patch | Una sola línea propia, sin el título cuando no hay configurados |
| 3 | Brechas | `no_signals` y las pestañas del caso «ninguno detectado» sin prueba en navegador | medium | patch | Prueba nueva con Playwright |
| 4 | Ciego | Un comprobado de un agente oculto no cuenta ni se avisa | low | rechazado | Regla 4 decidida por Alex: el agente no está en la carpeta ni en el equipo |
| 5 | Ciego | Si solo se detecta un agente sin adaptador, los dos con adaptador salen «sin señales» | low | rechazado | La spec dice «ningún agente con adaptador» |
| 6 | Ciego | El mapeo id↔plataforma está repetido en tres sitios | low | rechazado | Duplicación anterior a esta historia |
| 7 | Ciego, casos límite | El filtro de `contextos` ya no deja pasar `NO_DETERMINADA` | false | rechazado | `contextos` solo trae los adaptadores de Claude Code y opencode, nunca `NO_DETERMINADA` |
| 8 | Ciego | Tipado flojo de `plataformas_mostradas` | low | rechazado | Uso interno con dos llamadores fijos |
| 9 | Ciego | La nota solo sale en `#agentnote` (no en pestaña, impresión ni exportaciones) | low | defer | Mejora posterior; no cambia lo que se muestra de cada agente |
| 10 | Ciego | Ayudantes de prueba frágiles (`r{len(extra)}.html`, `in (0, 1)`) | low | rechazado | Pasan y se usan una vez cada uno |
| 11 | Ciego | El diff de la plantilla mezcla cambios ajenos | false | rechazado | Son las historias 42 y 43 en el mismo árbol sin commit |
| 12 | Brechas | No hay aserción de que `cfg_intro` no sale en el caso sin agentes | low | patch | Cubierta por el cambio 2 |
| 13 | Casos límite | Agente detectado solo por un marco (BMAD) sin su propio rastro | low | rechazado | El marco se detecta con la carpeta del agente anfitrión; caso raro |
| 14 | Casos límite | `showTxt` vacío, placeholder sin agentes, foco tras refrescar | false | rechazado | Con ninguno detectado salen los dos agentes; `setAgent` reinicia los niveles |
| 15 | Casos límite | El último nivel pulsado por teclado no avisa que se rechazó | low | rechazado | La ficha ya lleva `aria-disabled` y título (Historia 43) |
| 16 | Casos límite | No hay prueba de que reglas y causas de un agente oculto no salen | low | rechazado | Un agente sin detectar no tiene reglas: sin configuración, `contextos` viene vacío |

## Design Notes

Regla de detección: tiene pestaña quien aparece en «Agentes configurados» (`AgenteDetectado` con `analizado`), con cualquier confianza; así lo que se ve arriba (configurados) y lo que se ve abajo (pestañas) nunca se contradice. Un agente detectado solo por `~/.claude` o `~/.config/opencode` exige el permiso de lectura de las reglas del equipo (segunda pregunta); sin ese permiso cuenta lo que haya en el proyecto.

## Verification

**Commands:**
- `uv run ruff check src tests` -- expected: All checks passed
- `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach uv run pytest -q` -- expected: todo pasa; el oráculo no se omite
- `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach uv run --with playwright pytest -q tests/test_historia_40.py tests/test_reporte_html.py` -- expected: pasan en navegador real

**Manual checks (if no CLI):**
- Alex ejecuta `agentreach` sobre proyecto real local y confirma que no hay pestaña de opencode.
