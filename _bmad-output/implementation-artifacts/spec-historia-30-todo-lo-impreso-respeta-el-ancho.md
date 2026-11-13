---
title: 'Historia 30: todo lo que imprime la CLI respeta el ancho'
type: 'bugfix'
created: '2026-11-11'
status: 'done'
route: 'dispatch'
baseline_commit: 'b4c47638770eb8394d590df0f426000f754cfdcb'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** El reporte ajusta su texto al ancho de la terminal, pero los textos de bienvenida, las dos preguntas de permiso, los avisos y «Reporte HTML guardado en…» son cadenas largas que se imprimen sin ajuste. La terminal las corta donde se acaba la pantalla y parte palabras (en Orca: «Solo g / uarda»).

**Approach:** Que todo texto que la CLI imprime, o pasa a una pregunta, salga por el mismo ajuste de palabras que ya usa el reporte (`formato.ajustar`), con el ancho real de la terminal. El texto no cambia, solo dónde se corta.

## Boundaries & Constraints

**Always:** Ancho de ajuste = columnas reales de la terminal menos 1 (ya lo hace `ajustar`), con tope de 100 y mínimo de 20; sin terminal, 80 columnas. Nunca se parte una palabra; una ruta o ficha sin espacios más larga que el ancho va entera en su línea. Se respetan los saltos de línea y la sangría que ya trae un texto (por ejemplo la línea de la ruta en la pregunta). El texto final de una pregunta, «(S/N) » o «(Y/N) », no se parte ni se separa de la línea anterior. Español e inglés, tonos cercano y formal.

**Never:** Cambiar el contenido de los textos ni las reglas de las historias 22, 27 y 28 (solo cuentan s/S/n/N en español y y/Y/n/N en inglés; tres intentos; sin terminal no se lee nada). Tocar el cuerpo del reporte, el HTML, el banner ni `doctor` (su texto ya pasa por `formatear_doctor`). Cambiar códigos de salida. Escribir el ajuste a mano en cada mensaje: debe haber un solo punto por el que pase todo.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Anchos usuales | Terminal de 60, 80, 100 y 140 columnas | Ninguna línea pasa del ancho menos 1 (tope 100); ninguna palabra partida | N/A |
| Terminal angosta | Menos de 40 columnas (por ejemplo 30) | Ajusta a lo que haya, mínimo 20; sin excepción | Sin error |
| Ruta larga | Ruta sin espacios mayor que el ancho en la pregunta de permiso y en «guardado en» | La ruta queda entera en su línea | N/A |
| Pregunta con aviso | Carpeta personal o raíz (aviso de riesgo) y ruta real distinta | Cada línea ajustada; «(S/N) » al final intacto | N/A |
| Idiomas y tonos | ES/EN × cercano/formal, ambas preguntas | Se cumple en las cuatro combinaciones | N/A |
| Flujo completo | Bienvenida, dos preguntas, aviso de reporte guardado, pregunta de abrir | Toda la salida (stdout, stderr y el texto de cada pregunta) cumple | N/A |

</frozen-after-approval>

## Code Map

- `src/agentreach/cli/__init__.py` -- `_ERROR` (diccionario de textos, ~l.60-130) y `_PREGUNTA_REGLAS`; `_presentar` (~l.521, imprime la bienvenida por stderr); `_confirmar` (~l.475, imprime `solo_sn`); `_pedir_lectura` (~l.528, texto `pregunta_leer` con ruta y aviso, y `no_leyo`); `_pedir_reglas` (~l.545); `_reporte_html` (~l.556, `reporte_donde`, `reporte_que`, `reporte_no`, `pregunta_abrir`, `respuesta_guardada`, `no_abrio`); `_ejecutar` (~l.639, `aviso_config`); y los `print(_ERROR[...])` sueltos (~l.170, 407-462, 500, 601-666). `_ancho(args)` (~l.329) hoy mide para el reporte (mínimo 60) y NO sirve tal cual: aquí el mínimo es 20.
- `src/agentreach/reporting/formato.py` -- `ajustar(texto, ancho, primera, resto)`, `ancho_visible`, `ancho_de_trabajo`; reutilizar `ajustar`, no reescribirlo.
- `tests/test_historia_22.py`, `tests/test_historia_28.py`, `tests/test_historia_27.py` -- cómo se llama `main` con una `preguntar` falsa y cómo se captura stdout y stderr; deben seguir pasando sin cambios.

## Tasks & Acceptance

**Execution:**
- [x] `src/agentreach/cli/__init__.py` -- un solo ayudante que ajusta un texto (con saltos y sangría) al ancho de la terminal, y usarlo en todo mensaje impreso o pasado a `preguntar` -- un punto, sin copiar el ajuste
- [x] `tests/test_historia_30.py` -- ejecutar el flujo completo con una `preguntar` falsa que registra cada texto de pregunta, con anchos 30, 60, 80, 100 y 140, en los cuatro idiomas/tonos, y comprobar la salida completa (stdout, stderr y los textos de pregunta) -- cubre la matriz
- [x] `_bmad-output/implementation-artifacts/spec-historia-30-*.md` e `historias-mvp.md` -- Estado y «no verificado» al terminar

**Acceptance Criteria:**
- Given un ancho de 60 a 140, when se recorre el flujo completo, then ninguna línea supera el ancho menos 1 salvo una ficha sin espacios, y cada palabra de la salida es una palabra del texto original (ninguna partida).
- Given las pruebas de las historias 22, 27 y 28 y el resto de la suite, when se ejecutan con `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach`, then pasan sin cambios y `ruff` queda limpio.

## Implementation Notes

## Spec Change Log

## Review Triage Log

| # | Revisor | Hallazgo | Veredicto | Ruta | Evidencia |
|---|---------|----------|-----------|------|-----------|
| 1 | Ciego y casos límite | `_decir` ahora carga Ctrl+C, error interno y `_Parser.error`; si el ajuste fallara ahí se rompe «nunca una traza» | medium | patch (hecho) | `try/except` con salida sin ajustar y prueba que fuerza el fallo (código de salida intacto) |
| 2 | Casos límite y ciego | El reemplazo global de U+00A0 altera una ruta con ese carácter real | low | patch (hecho) | Marcador de uso privado ``; prueba con U+00A0 real |
| 3 | Brechas y casos límite | La comprobación «ninguna palabra partida» sobre stdout nunca podía fallar (`split` devuelve todo) | medium | patch (hecho) | Reescrita con el método de unir y comparar de las Design Notes; afirma el marcador antes de dividir |
| 4 | Brechas | Mensajes de salida anticipada sin comprobación de ancho | medium | patch (hecho) | Prueba parametrizada de 6 salidas a 30 columnas |
| 5 | Casos límite | «Un solo punto» es convención sin vigilancia | medium | patch (hecho) | Prueba con `ast` que falla ante un `print(` fuera de `_decir`; mutación comprobada |
| 6 | Ciego | La prueba de `--ancho` no puede fallar | false | rechazado | Mutación mía: ignorando `--ancho` la prueba falla |
| 7 | Casos límite | Una ruta con espacios puede partirse entre palabras | medium | diferido | Protegerla exige detectar qué línea es una ruta; anotado en `deferred-work.md` |
| 8 | Ciego | `_columnas` duplica `_ancho` | low | rechazado | Mínimos distintos por diseño (20 aquí, 60 en el reporte) |
| 9 | Ciego | `--ancho` ≤0 o no numérico usa 80 | low | rechazado | Opción explícita del usuario; argparse ya valida el tipo |
| 10 | Casos límite | Sangría ≥ ancho en una terminal muy angosta | low | rechazado | Los textos reales tienen sangría ≤4 y el mínimo es 20 |
| 11 | Casos límite | Espacio final reañadido a líneas que no son pregunta | low | rechazado | Solo los textos de pregunta terminan en espacio |
| 12 | Casos límite | `_FINAL_PREGUNTA` exige el espacio final | low | rechazado | Todas las preguntas terminan en «(S/N) » por diseño |
| 13 | Casos límite | stderr mide el ancho de stdout si este se redirige | low | rechazado | Sin stdout interactivo no hay preguntas ni lectura |
| 14 | Ciego y casos límite | `--help` y el banner no pasan por `_texto` | low | rechazado | argparse ya ajusta su ayuda; el banner está fuera de alcance por la spec |
| 15 | Ciego | Las pruebas viejas se relajaron con normalización de espacios | low | rechazado | Revisé el diff: 8 líneas, solo espacios; el texto esperado no cambió |
| 16 | Ciego y casos límite | Ajustar colapsa espacios repetidos; «el contenido no cambia» | low | rechazado | Solo texto de prosa; sin espacios dobles intencionales |
| 17 | Brechas | Exención de «ficha de una palabra» demasiado amplia en las pruebas | low | rechazado | Sin regresión concreta que oculte |

## Design Notes

Comprobar «ninguna palabra partida» sin conocer el texto original: unir las líneas ajustadas con un espacio y comparar con el texto original normalizado (espacios colapsados); si una palabra se hubiera partido, la unión tendría un espacio de más.

## Verification

**Commands:**
- `uv run ruff check src tests` -- expected: All checks passed
- `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach uv run pytest -q` -- expected: todo pasa

**Manual checks (if no CLI):**
- Alex ejecuta `agentreach` en Orca con la ventana angosta y ancha y confirma que no hay palabras partidas.
