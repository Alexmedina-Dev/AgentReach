---
title: 'Historia 41: se ve que AgentReach avanza mientras revisa'
type: 'feature'
created: '2026-11-12'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Mientras AgentReach revisa una carpeta grande no imprime nada, y la persona no sabe si la herramienta funciona o se trabó (visto por Alex al usarla en un proyecto real de 2089 archivos).

**Approach:** Una sola línea en la terminal, por la salida de errores, que se actualiza en su sitio con el paso en el que va, la cantidad de carpetas recorridas y el tiempo transcurrido. Solo con terminal interactiva; en cualquier otro caso la salida es idéntica a la de hoy.

**Decisión (Alex, 2026-11-12):** «paso X de 12» con una barra por pasos, más carpetas y tiempo. No se muestra un porcentaje de archivos, porque el total no se conoce de antemano y sería inventado.

## Boundaries & Constraints

**Always:** Solo biblioteca estándar, sin hilos ni temporizadores (la señal de vida sale de que el recorrido avanza y del reloj al actualizar). Toda cadena visible sale de un catálogo en español e inglés y pasa por `formato.ajustar` (AD-20, 60 a 100 columnas). El avance escribe solo en `sys.stderr`, sin abrir archivos (AD-3, AD-19) ni usar red (AD-4). La línea se borra antes de imprimir cualquier otra cosa, también ante Ctrl+C (código 130) o un error. El núcleo (`core/`) no importa `reporting/` ni `infra/`: recibe un `Callable` simple.

**Never:** Mostrar nombres de archivo, rutas ni valores (AD-15): solo paso, cantidades y tiempo. Imprimir avance con `--salida`, `--json`, salida redirigida, `TERM=dumb` o sin terminal interactiva. Cambiar hallazgos, niveles, el orden de los detectores o el contenido del reporte. Cachear o unificar el recorrido repetido del árbol (queda fuera de esta historia).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Terminal interactiva | stdin, stdout y stderr son terminal | Una línea que se reescribe: paso X de Y, carpetas, tiempo; al terminar se borra | N/A |
| Salida redirigida o `--salida` | stdout no es terminal, o `--salida` | Ningún avance; salida idéntica a la de hoy | N/A |
| `NO_COLOR` o `TERM=dumb` | variable presente | `NO_COLOR`: avance sin color; `TERM=dumb`: sin avance | N/A |
| Terminal estrecha | ancho 20 a 59 columnas | La línea se acota al ancho de trabajo y no se parte | N/A |
| Ctrl+C a mitad | interrupción | La línea se borra y sale con código 130 | La limpieza va en `finally` |
| Fallo de un detector | `RuntimeError` del pipeline | La línea se borra antes del mensaje de error | Código 3 como hoy |
| Codificación sin UTF-8 | consola sin símbolos | Solo ASCII, sin caracteres de barra | Sin traza |

</frozen-after-approval>

## Code Map

- `src/agentreach/core/pipeline.py` -- `Pipeline.ejecutar` recorre los detectores en orden: recibe un `al_avanzar(indice, total)` opcional; sin él, igual que hoy. Es puro: no importa `infra` ni `reporting`.
- `src/agentreach/app/auditar.py` -- `auditar(...)` (l.111) crea `FsSoloLectura` y `Pipeline(detectores)`; recibe `avance` opcional, lo pasa al pipeline y envuelve `fs.listar` para contar carpetas. Registro `_detectores` (12 fábricas, l.62). No cambiar el orden ni el contenido del resultado.
- `src/agentreach/infra/fs_solo_lectura.py` -- `listar` (l.103) es un generador de `os.scandir`; no tocar su contrato (`ReadOnlyFs`, `contracts/ports.py`).
- `src/agentreach/reporting/avance.py` -- archivo nuevo: indicador que formatea la línea (catálogo es/en, `formato.ajustar`, límite de actualización con `time.monotonic`) y la escribe con `\r`.
- `src/agentreach/cli/__init__.py` -- `_ejecutar` llama a `auditar` en l.685; antes crea el indicador solo si stdout y stderr son terminal (`_es_terminal`, l.380), sin `--salida`, sin `--json` y sin `TERM=dumb`; lo cierra en `finally`. Usar `_escribir` (l.395), no `print` (`test_historia_30.py:223` solo permite `print` en `_decir`). `main` (l.451) ya devuelve 130 en Ctrl+C.
- `tests/test_historia_30.py` -- modelo de terminal simulada (`Tty`, fixture `entorno`, `_correr`).
- `tests/reglas_no_negociables/` -- `test_solo_lectura.py`, `test_sin_red.py`, `test_sin_ejecutar_programas.py`, `test_sin_valores_de_secretos.py` deben seguir pasando; revisar los dos últimos antes de escribir.

## Tasks & Acceptance

**Execution:**
- [x] `src/agentreach/core/pipeline.py` -- `ejecutar(proyecto, al_avanzar=None)` avisa antes de cada detector con (indice, total) -- base del paso X de Y
- [x] `src/agentreach/app/auditar.py` -- parámetro `avance`, envoltura de `listar` que cuenta carpetas, avisos de «evaluando» y «ordenando» -- fuente de las señales
- [x] `src/agentreach/reporting/avance.py` -- indicador con catálogo es/en, ajuste de ancho, límite de actualización, borrado final, sin color si `NO_COLOR` -- la línea visible
- [x] `src/agentreach/cli/__init__.py` -- crear el indicador solo con terminal interactiva y cerrarlo en `finally` -- cableado
- [x] `tests/test_historia_41.py` -- matriz de I/O, ausencia de avance fuera de terminal, línea limpia antes del reporte, canario sin nombres ni valores en el avance, Ctrl+C -- cubre la matriz
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` y `epics.md` -- estado de la historia 41 al terminar -- seguimiento

**Acceptance Criteria:**
- Given una revisión en una terminal interactiva, when AgentReach analiza la carpeta, then una sola línea se actualiza en su sitio y al terminar se borra, sin restos en el reporte.
- Given salida redirigida, `--salida`, `--json` o `TERM=dumb`, when se ejecuta, then no se imprime ningún avance.
- Given un proyecto con un archivo cuyo nombre lleva un valor canario, when se revisa en terminal, then el avance no contiene el nombre ni el valor.
- Given `ruff` y la suite con `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach`, when se ejecutan, then pasan sin omitir el oráculo ni las reglas no negociables.

## Implementation Notes

## Spec Change Log

## Review Triage Log

| # | Revisor | Hallazgo | Veredicto | Ruta | Evidencia |
|---|---------|----------|-----------|------|-----------|
| 1 | Ciego, casos límite | Una excepción del callback (`columnas()`, `ajustar`, `pintar`, LookupError al re-codificar) aborta la revisión; una en `cerrar()` enmascara el error o el 130 | medium | patch | El callback corre dentro de `listar` y del pipeline; solo `_escribir` estaba protegido |
| 2 | Ciego, casos límite | `reporte` se emite antes del segundo recorrido completo y esa fase no muestra carpetas | medium | patch | `auditar.py`: el aviso va antes de `recorrer(fs, proyecto)` y solo la fase «revisando» pinta el contador |
| 3 | Brechas | Fallos de escritura (OSError, UnicodeEncodeError) sin prueba | medium | patch | Los flujos de prueba nunca lanzan; borrar el `except` no hace fallar nada |
| 4 | Brechas | Tiempo mayor a un minuto, miles sin UTF-8 y singular sin afirmar | low | patch | Solo se afirman `0 s` y `8 s`; la rama de 1000 o más en ASCII no se ejercita |
| 5 | Ciego | Prueba de Ctrl+C con aserción permisiva (`or "ancel" in mensaje`) | low | patch | `tests/test_historia_41.py` ~l.570 |
| 6 | Ciego | Pruebas con «12» fijo | low | patch | Añadir o quitar un detector las rompe por un motivo ajeno |
| 7 | Ciego, casos límite | Línea quieta dentro de un detector lento sin carpetas nuevas | medium | defer | Real pero inevitable sin temporizador (prohibido por el spec); se verifica en una terminal real |
| 8 | Ciego, casos límite | Terminal estrechada tras dibujar deja restos al borrar | low | rechazado | Arreglarlo exige mover el cursor, que el spec prohíbe; cambiar el ancho a mitad de revisión es raro |
| 9 | Ciego | Sin opción para apagar el avance (`CI`, lectores de pantalla) | low | defer | La intención no la excluye, pero añade una opción nueva; `CI` suele implicar sin terminal |
| 10 | Ciego, casos límite | `_FsContado` copia 3 métodos; el conjunto de rutas crece con el árbol; el conteo puede inflarse por mayúsculas | low | rechazado | El puerto `ReadOnlyFs` solo tiene esos tres métodos y los detectores ya guardan todos los archivos en memoria |
| 11 | Casos límite | Carpetas ilegibles cuentan como recorridas | low | rechazado | Es una cantidad aproximada, no un hallazgo |
| 12 | Casos límite | Una pregunta o aviso choca con la línea | false | rechazado | `_crear_avance` se llama después de todas las preguntas y avisos |
| 13 | Casos límite | «paso 0 de 0» si no llega el evento «paso» | false | rechazado | El pipeline avisa antes de cada detector y `listar` solo se llama dentro de ellos |
| 14 | Ciego | Separador de miles es un espacio normal | false | rechazado | Es U+00A0, comprobado en el archivo |
| 15 | Ciego | Faltan importaciones de `Callable` y `ReadOnlyFs` en `auditar.py` | false | rechazado | Ya existen (l.13 y l.36) y la suite pasa |
| 16 | Casos límite | El spec dice «ordenando» y el código emite «reporte» | low | rechazado | La nota de diseño del spec dice «preparando el reporte»; el texto de la tarea era impreciso |
| 17 | Brechas | Inglés y `AGENTREACH_ASCII` no probados por la CLI | low | rechazado | Cubiertos por la prueba unitaria del catálogo y por la de codificación ASCII |

## Design Notes

Línea de ejemplo (opción A, 24 bits o ASCII): `Revisando… paso 3 de 12 [###-------] · 1 240 carpetas · 8 s`. Sin UTF-8 la barra usa `#` y `-`. Con `NO_COLOR` no hay secuencias de color. Los pasos son los 12 detectores del registro; después vienen dos señales cortas («evaluando», «preparando el reporte») sin contar en la barra.

## Verification

**Commands:**
- `uv run ruff check src tests` -- expected: All checks passed
- `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach uv run pytest -q` -- expected: todo pasa; el oráculo no se omite

**Manual checks (if no CLI):**
- Alex ejecuta `agentreach` en una terminal real sobre una carpeta grande y confirma que la línea se mueve, se lee bien y desaparece antes del reporte.
