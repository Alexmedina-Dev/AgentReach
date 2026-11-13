---
title: 'Historia 32: la terminal explica cada término técnico en lenguaje llano'
type: 'feature'
created: '2026-11-11'
status: 'done'
route: 'dispatch'
baseline_commit: 'b4c47638770eb8394d590df0f426000f754cfdcb'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-6-context.md'
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-agent-reach-2026-11-11/EXPERIENCE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** El resumen de la terminal usa jerga que una persona no experta no entiende: «16 hallazgos sin nivel determinado · hooks.PreToolUse · función que AgentReach no modela», «se corrigieron 1 hallazgo(s) … autocomprobación (la línea citada…)». No explica qué es un *hook*, no dice cuál hallazgo se corrigió ni a qué nivel pasó, y «LO MÁS URGENTE» no dice qué hacer.

**Approach:** Un catálogo fijo de 11 términos (fichas del contrato de UX `EXPERIENCE.md`, sección «Glosario y explicaciones», copiadas tal cual) con línea de terminal y explicación larga en español (tú y usted) e inglés. La terminal usa la línea corta solo donde el término aparece, y `--detalle` agrega la explicación larga. La autocomprobación conserva tipo, ubicación y nivel antes y después para decir cuál hallazgo cambió.

## Boundaries & Constraints

**Always:** Los textos salen del contrato de UX, sin reescribirlos ni inventar otros. Solo biblioteca estándar; sin modelo de lenguaje. Tono «tú» por defecto y «usted» con `--tono formal`; en inglés no varía. El resumen sin `--detalle` crece como máximo 12 líneas frente a hoy en la carpeta de prueba (ancho 80). Cada término sale solo si aparece en ese reporte, una vez. Todo texto respeta el ancho sin partir palabras (usar el ajuste que ya tiene el reporte). La clave técnica, si se muestra, va entre paréntesis después de la frase llana.

**Never:** Valores de secretos en cualquier texto. Las palabras «seguro», «sin riesgo» y sus equivalentes en inglés en el catálogo; la jerga «no modela», «línea citada», «regla de nivel violada», «esquema de configuración». Presentar «potencial» como riesgo menor. Cambiar niveles, el cálculo de `comprobado`, códigos de salida o el oráculo. Tocar la plantilla HTML y el README (historias 33 y 34), el banner o `doctor`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Niveles presentes | Hallazgos potencial e hipótesis, sin comprobados | En RESUMEN la frase de cada nivel presente sale de la ficha (potencial incluye «no es un riesgo menor»); no sale la de un nivel ausente | N/A |
| Hook sin nivel determinado | Causa `hooks.PreToolUse` | Frase llana de la ficha «no determinado» + una sola explicación de *hook* con la fórmula «no es una alarma ni una garantía: es un punto ciego»; la clave entre paréntesis; sin «no modela» | N/A |
| Autocomprobación | 1 hallazgo bajado por línea no confirmada | Dice cuál (tipo y ruta, sin valores) y a qué nivel pasó; con más de 3, lista 3 y «y N más» | Si faltan los datos, el aviso actual sin romperse |
| Agentes configurados | Un agente reconocido pero no analizado | Una frase de la ficha «configurado vs analizado», una vez | N/A |
| LO MÁS URGENTE | 3 hallazgos | Cada uno con una línea «→ qué hacer» tomada del catálogo existente | Sin «qué hacer» disponible: se omite la línea |
| Detalle | `--detalle` | Sección con la explicación larga (qué es, qué significa, qué hacer) de los términos presentes; ahí pueden verse las claves técnicas | N/A |
| Idiomas y tonos | ES tú, ES usted, EN | Cada variante completa; el inglés igual con ambos tonos | Término sin entrada: la prueba de cobertura falla |
| Reporte vacío o sin color/ASCII | Sin hallazgos; `--ascii`; sin color | No sale ningún término ausente; ningún símbolo fuera de ASCII en modo ASCII | N/A |

</frozen-after-approval>

## Code Map

- `src/agentreach/core/catalogo_explicaciones.py` y `src/agentreach/contracts/finding.py` (`CATALOGO_EXPLICACIONES`, `TITULO_MOTIVO`, `COMO_RESOLVER`, `EXPLICACIONES_FORMAL`) -- hoy indexados por tipo y por motivo; ahí vive el tono cercano/formal. El catálogo de términos nuevo va junto a ellos y sigue el mismo patrón ES/EN y tono.
- `src/agentreach/core/autocomprobacion.py` -- `Correccion(ubicacion, tipo, razon, plataforma)` y `RazonCorreccion`; ampliar con nivel antes y después.
- `src/agentreach/reporting/gate.py` (~l.112-113 y ~l.260-261) -- hoy pasa solo `correcciones: tuple[RazonCorreccion]` y `hallazgos_corregidos: int`; pasar tipo, ubicación y niveles (sin valores).
- `src/agentreach/reporting/texto.py` -- `_T` (textos), RESUMEN (~l.65-75, ~l.284-290), AGENTES CONFIGURADOS (~l.134-143), POR QUÉ HAY NIVELES «NO DETERMINADO» (~l.147-153, ~l.394-410; la causa viene de `TITULO_MOTIVO` y de la clave del adaptador), LO MÁS URGENTE (~l.154, ~l.422), aviso de correcciones (~l.122-128, ~l.296-299), orden en `_pasada` (~l.525-542).
- `_bmad-output/planning-artifacts/ux-designs/ux-agent-reach-2026-11-11/EXPERIENCE.md` -- «Glosario y explicaciones» (11 fichas con sus tres variantes) y «Cuándo y dónde aparece cada explicación»: fuente de los textos y de las reglas.
- `tests/test_reporte.py`, `tests/test_historia_25.py` -- pruebas actuales sobre las frases del resumen y el bloque «no determinado»; los cambios de texto en ellas son deliberados.

## Tasks & Acceptance

**Execution:**
- [ ] `src/agentreach/core/catalogo_terminos.py` (nuevo) -- las 11 fichas con línea de terminal y explicación larga (qué es, qué significa, qué puedes hacer) en ES tú, ES usted y EN, copiadas del contrato -- un solo catálogo
- [ ] `src/agentreach/core/autocomprobacion.py` y `src/agentreach/reporting/gate.py` -- conservar tipo, ubicación y nivel antes y después de cada corrección y pasarlos a la vista, sin valores -- decir cuál hallazgo cambió
- [ ] `src/agentreach/reporting/texto.py` -- usar las fichas en RESUMEN, «no determinado» (frase llana, sin «no modela», clave entre paréntesis), AGENTES CONFIGURADOS y el aviso de autocomprobación; añadir «→ qué hacer» a LO MÁS URGENTE; con `--detalle`, sección con la explicación larga de los términos presentes -- la experiencia
- [ ] `tests/test_historia_32.py` -- cobertura término contra entrada y de las tres variantes, longitud ≤90 de las líneas de terminal, ausencia de las palabras prohibidas, canario sin valores, cada fila de la matriz, tope de 12 líneas, ancho 60/80/100 sin palabras partidas y prueba de que ningún identificador técnico aparece sin su explicación en el resumen -- cubre la matriz
- [ ] `tests/test_reporte.py`, `tests/test_historia_25.py` y las demás que afirmaban las frases antiguas -- actualizarlas a los textos nuevos y anotar el cambio en la spec -- cambio deliberado
- [ ] `_bmad-output/implementation-artifacts/spec-historia-32-*.md` e `historias-mvp.md` -- Estado y «no verificado»; registrar las historias 33 (HTML «Cómo leer este reporte») y 34 (README) como pendientes

**Acceptance Criteria:**
- Given la carpeta de prueba con los hooks de Alex, when se ejecuta, then el resumen no contiene «no modela», «línea citada» ni «autocomprobación» sin explicación, y explica en una o dos frases qué es un hook sin decir «seguro».
- Given la suite completa, ruff y `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach`, when se ejecutan, then pasan sin omitir el oráculo.

## Implementation Notes

- Estado (2026-11-11): implementada. Catálogo en `core/catalogo_terminos.py` (11 fichas, tú/usted/EN, copiadas del contrato); `Correccion` guarda `nivel_antes` y `nivel_despues`; `gate.py` pasa `CorreccionVista` (tipo, ruta, razón, niveles; sin valores); `texto.py` usa las fichas.
- Decisiones: los niveles presentes dicen su frase una vez; «no determinado» + una sola explicación de hook con la fórmula del punto ciego; la clave técnica va entre paréntesis tras la frase llana; causas del mismo archivo comparten su línea de ruta; «configurado» sustituye la frase vieja del encabezado cuando hay un agente no analizado.
- Para no pasar de 12 líneas más en la carpeta de prueba (ancho 80), `sandbox`, `no se pudo revisar` y `código de salida` salen con la explicación larga de `--detalle`; la línea de conteo de «no se pudo revisar» conserva su descripción de siempre.
- Textos antiguos retirados deliberadamente: «no modela» (ahora «no sabe interpretar»), «sin nivel determinado», «línea citada», «regla de nivel violada», «Esquema de configuración» (ahora «Configuración (versión 1.x)»); las descripciones por nivel del resumen (ahora las da la ficha). Pruebas actualizadas: `test_reporte`, `test_historia_24`, `test_historia_25`, `test_primera_ejecucion`, `test_presentacion_marca`, `test_opencode_1x_2x`.
- Pendientes registrados en `historias-mvp.md`: Historia 33 (HTML «Cómo leer este reporte») y 34 (README).
- No verificado: la lectura de Alex en Orca con sus hooks reales.

## Spec Change Log

## Review Triage Log

| # | Revisor | Hallazgo | Veredicto | Ruta | Evidencia |
|---|---------|----------|-----------|------|-----------|
| 1 | Casos límite | «Sigue en X, sin línea» se muestra aunque la razón no sea de línea | medium | patch (hecho) | `corr_sin_linea` solo con `LINEA_NO_CONFIRMADA`; si no, `corr_corregido`; prueba por cada rama |
| 2 | Casos límite y ciego | Un hallazgo corregido por dos reglas sale dos veces con el mismo texto y gasta el tope de 3 | medium | patch (hecho) | Deduplicación por (tipo, ruta, nivel antes, nivel después); prueba con dos razones |
| 3 | Brechas, ciego y casos límite | El tope de 12 líneas se omite sin el proyecto de prueba y usa un 59 sin explicar | medium | patch (hecho) | Falla en vez de omitirse con `CI` o `AGENTREACH_EXIGIR_PRUEBAS`; comentario de cómo se midió el 59 |
| 4 | Brechas y ciego | Ramas `corr_corregido` y `corr_bajo_a` y las variantes usted/EN del aviso sin prueba | low | patch (hecho) | Pruebas en tú, usted e inglés |
| 5 | Ciego | `urgentes()` traga `KeyError` y un hueco del catálogo pasaría en silencio | low | patch (hecho) | Prueba: todo `Tipo` tiene «qué hacer» en ES, EN y formal |
| 6 | Ciego | `.replace("--tono formal", "")` sin efecto en una prueba | low | patch (hecho) | Eliminado |
| 7 | Casos límite | Una causa sin clave haría caer el reporte (`.lower()` sobre `None`) | false | rechazado | `clave: str = ""` en `NoRevisado` y `CausaVista`; nunca es `None` |
| 8 | Ciego | Los términos no se reinician entre pasadas | false | rechazado | La salida real simulada muestra cada término una vez |
| 9 | Ciego y casos límite | `_es_hook` y `_es_sandbox` por prefijo de la clave | low | rechazado | Las claves salen de una lista fija de los adaptadores (Historia 25) |
| 10 | Ciego | Las frases nuevas no tienen variante formal propia | low | rechazado | Voz impersonal; no llevan pronombre |
| 11 | Ciego y casos límite | Tres líneas de terminal (sandbox, no se pudo revisar, código de salida) no se imprimen nunca | medium | diferido | Consecuencia del tope de 12 líneas fijado en la spec; salen con `--detalle`; decisión de Alex pendiente |
| 12 | Casos límite | `--detalle` puede explicar un término que el resumen no mostró, o al revés | medium | diferido | No verificado; lo resolvería una prueba de que los términos de `--detalle` incluyen los del resumen |
| 13 | Ciego | Se perdió «se muestra sin sus valores» dentro del bloque no determinado | low | rechazado | El aviso general de arriba («No se muestran valores de secretos») y la prueba del canario siguen |
| 14 | Ciego | «Configurado» solo se explica con un agente no analizado; «analizado» no se dice | low | rechazado | Por el presupuesto de líneas; la ficha completa sale con `--detalle` |
| 15 | Casos límite | Dedupe por ruta visible puede fusionar hallazgos con distinta línea | low | rechazado | Sin caso real mostrado; el recuento total (`hallazgos_corregidos`) no cambia |
| 16 | Casos límite | «Lugar no confirmado» se explica aunque su corrección quede fuera del tope | low | rechazado | Cosmético; el término es el mismo concepto |
| 17 | Casos límite | El fallback genérico pierde las razones | low | rechazado | Solo cuando faltan los datos; la spec acepta el aviso reducido |
| 18 | Casos límite | Las exenciones de la prueba de ancho son amplias | low | rechazado | Sin regresión concreta que oculten |
| 19 | Casos límite | `hallazgos_corregidos` con filtro de agente | low | rechazado | Se calcula sobre lo visible, igual que la lista |
| 20 | Ciego | Frágil: `nivel_despues` se rellena por rango de índices | low | rechazado | Correcto mientras no se reordene; cubierto por la prueba del dedupe |

## Design Notes

El catálogo de términos es independiente del de hallazgos: se indexa por concepto (nivel_comprobado, nivel_potencial, nivel_hipotesis, no_determinado, no_se_pudo_revisar, hook, sandbox, configurado_vs_analizado, autocomprobacion, lugar_no_confirmado, codigo_de_salida). La terminal toma `linea`; el HTML (Historia 33) y `--detalle` toman `que_es`, `que_significa`, `que_hacer`.

## Verification

**Commands:**
- `uv run ruff check src tests` -- expected: All checks passed
- `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach uv run pytest -q` -- expected: todo pasa

**Manual checks (if no CLI):**
- Alex ejecuta `agentreach` en Orca con sus hooks y confirma que entiende por qué todo sale «potencial».
