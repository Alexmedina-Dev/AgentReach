---
title: 'Historia 44: aviso cuando la carpeta revisada contiene varios proyectos'
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

**Problem:** Un reporte de una carpeta que reúne varios proyectos (por ejemplo `C:\dev`, que juntaba AgentReach, el proyecto de prueba del oráculo y otras carpetas) sale igual que uno de un solo proyecto: la carpeta solo aparece en el encabezado, y quien lo lee cree que son hallazgos de un único proyecto. Alex: «muestra cosas que no son».

**Approach:** Con los archivos que el recorrido final de `auditar()` ya vio (sin recorridos nuevos), se cuentan las carpetas **dentro** de la revisada (no ella misma) que tienen su propio punto de partida de un agente o de un repositorio. Si hay **2 o más**, el reporte (terminal y HTML) avisa arriba, antes de los hallazgos, cuántas son y que conviene revisar un proyecto a la vez. El aviso lleva solo la cantidad: ningún nombre ni ruta. No es un hallazgo: no cambia ningún nivel, conteo ni código de salida.

## Boundaries & Constraints

**Always:** Un nivel interno cuenta como proyecto aparte si contiene `.git/config`, `.claude/settings.json`, `.claude/settings.local.json`, `.opencode/opencode.json`, `CLAUDE.md`, `opencode.json` u `opencode.jsonc`; la raíz revisada nunca cuenta; no cuentan las que estén dentro de `.git`, `node_modules`, `.claude` u `.opencode`. Los manifiestos (`package.json`, `pyproject.toml`…) no son señal: un monorepo no avisa. Umbral `2` en una constante con nombre. El dato pasa por la compuerta (AD-15) y viaja en el HTML como campo aditivo y opcional (AD-17). El texto sale del catálogo (AD-16), sin pronombres para no necesitar variante tú/usted, y la terminal lo ajusta al ancho (AD-20). Solo biblioteca estándar.

**Never:** Un recorrido nuevo del árbol; mostrar nombres de carpeta o rutas en el aviso (pueden ser de clientes); tratarlo como hallazgo o como «no se pudo revisar»; cambiar niveles, conteos, orden, el código de salida o el oráculo; leer el contenido de ningún archivo para decidir.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Varios proyectos | carpeta con 3 subcarpetas, cada una con su `.git/config` o su `.claude/settings.json` | Aviso «3 carpetas que parecen proyectos distintos» en terminal y HTML | N/A |
| Un solo proyecto | raíz con `.git`, sin subcarpetas con punto de partida | Sin aviso | N/A |
| Una subcarpeta aparte | raíz con una subcarpeta que tiene `CLAUDE.md` | Sin aviso (1 < 2) | N/A |
| Monorepo | un `.git` en la raíz y 10 `package.json` en subcarpetas | Sin aviso | N/A |
| Dentro de herramientas | `node_modules/x/.git/config`, `.claude/algo/CLAUDE.md` | No cuentan | N/A |
| Aviso sin nombres | las subcarpetas se llaman como clientes | El texto no contiene ningún nombre ni ruta; los conteos, niveles y código de salida son los de siempre | N/A |
| Archivo grande o ilegible | el punto de partida pesa más de 1 MiB o no se pudo listar | No se ve, no cuenta | N/A |
| Terminal estrecha | ancho 20 a 59 columnas | El aviso se parte por palabras sin cortarlas | N/A |
| Oráculo | proyecto de prueba del oráculo, revisado desde su raíz (tiene `proyecto/`, `proyecto-opencode-sin-read/` y unos 20 repositorios de trampas en `trampas-git/`) | Sale el aviso (es correcto: son proyectos distintos); los mismos 67 casos, cifras y código de salida de siempre | N/A |

</frozen-after-approval>

## Code Map

- `src/agentreach/app/auditar.py` -- `auditar()` hace el recorrido final `recorrer(fs, proyecto)` (~l.187) y arma `ResultadoAuditoria` (~l.50-60); aquí se cuenta con `recorrido.archivos` (`Metadatos`, atributo `ruta`) y se añade un campo `proyectos_anidados: int = 0`. `recorrer` (`collectors/enlaces.py` l.81) ya baja por todo el árbol, incluso por `.git`, hasta `MAX_PROFUNDIDAD`.
- `src/agentreach/collectors/` -- archivo nuevo, por ejemplo `proyectos_anidados.py`, con una función pura `contar_proyectos_anidados(archivos, raiz)` y la constante del umbral; sin E/S.
- `src/agentreach/reporting/gate.py` -- `DatosReporte` (~l.100-130) gana `proyectos_anidados: int = 0`; `preparar` (l.~190-300) lo copia desde el resultado; no entra en `codigo_de_salida` ni en los conteos.
- `src/agentreach/reporting/texto.py` -- catálogo `_T` (~l.98-190, ES y EN) y el encabezado del reporte: el aviso va después de la cabecera y antes de los hallazgos; usa el punto de ajuste de texto existente.
- `src/agentreach/reporting/html.py` y `docs/reporte-html/esquema-datos.md` y `.schema.json` -- `construir_datos` añade `wide_folder: N` solo si hay aviso (opcional, entero ≥ 2).
- `src/agentreach/reporting/plantilla_reporte.html` (copia idéntica en `docs/reporte-html/plantilla.html`) -- un aviso arriba (junto al de secretos), con texto en los diccionarios es y en; oculto si no hay `wide_folder`.
- Detalles de la función pura: las rutas de `Metadatos` son absolutas; se comparan relativas a la raíz con la normalización de `collectors/enlaces.py` (`_norm`, sin distinguir mayúsculas en Windows). Un `.git` que sea un archivo (submódulo o árbol de trabajo) no tiene `.git/config` y no cuenta. Lo que está más hondo que `MAX_PROFUNDIDAD` o pesa más de 1 MiB no se ve y no cuenta.
- Pruebas que pueden tocar la salida de la terminal con proyectos que tengan subcarpetas con `CLAUDE.md` u `opencode.json`: revisar las del proyecto de prueba (`tests/oraculo/`, `tests/reglas_no_negociables/`) y las de la compuerta.

## Tasks & Acceptance

**Execution:**
- [ ] `src/agentreach/collectors/proyectos_anidados.py` -- función pura y constante del umbral, con las reglas de la matriz -- la decisión, probada sin disco
- [ ] `src/agentreach/app/auditar.py` -- usar la función con `recorrido.archivos` y guardar `proyectos_anidados` en `ResultadoAuditoria` -- sin recorridos nuevos
- [ ] `src/agentreach/reporting/gate.py` -- campo en `DatosReporte`, copiado en `preparar`, fuera del código de salida -- la compuerta
- [ ] `src/agentreach/reporting/texto.py` -- aviso en la terminal (ES y EN, ajustado al ancho) -- lo que ve la persona en la terminal
- [ ] `src/agentreach/reporting/html.py`, `docs/reporte-html/esquema-datos.*`, `plantilla_reporte.html` y su copia -- campo `wide_folder` y el aviso del HTML -- lo que ve la persona en el navegador
- [ ] `tests/test_historia_44.py` -- cada fila de la matriz (función pura, terminal y HTML) y que el código de salida y los conteos no cambian -- cubre la matriz
- [ ] `_bmad-output/implementation-artifacts/sprint-status.yaml` y `epics.md` -- estado de la historia 44 -- seguimiento

**Acceptance Criteria:**
- Given una carpeta con 2 o más subcarpetas con su propio punto de partida, when se genera el reporte, then sale el aviso con la cantidad, sin nombres.
- Given un proyecto normal o un monorepo, when se genera el reporte, then no hay aviso.
- Given `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach`, when se ejecutan la suite, el oráculo y las reglas no negociables, then pasan sin omitirlos y con los mismos resultados.
- Given `ruff`, when se ejecuta, then pasa.

## Implementation Notes

## Spec Change Log

## Review Triage Log

| # | Revisor | Hallazgo | Veredicto | Ruta | Evidencia |
|---|---------|----------|-----------|------|-----------|
| 1 | Brechas | El aviso del HTML solo se prueba en los datos y con `"wide" in html` | medium | patch | Pruebas en navegador con y sin `wide_folder` y con el dato inválido 1 |
| 2 | Ciego, casos límite | El borde del umbral (1 y 2 carpetas) no se prueba de punta a punta | low | patch | Pruebas con 1, 2 y raíz con `.git` más 1 |
| 3 | Casos límite | «Función pura sin E/S» pero `_norm` usa `realpath` | low | patch | Docstring corregido; la lógica no cambia |
| 4 | Ciego | Un monorepo con `CLAUDE.md` en cada paquete contaría cada paquete | medium | defer | Real, pero cambiar la señal (solo `.git/config`) es decisión de diseño de Alex |
| 5 | Ciego, casos límite | `.venv`, `vendor`, `dist` no se excluyen | low | defer | Caso raro; la ficha fija las cuatro carpetas de herramientas |
| 6 | Casos límite | El conteo puede quedar bajo si el recorrido omite algo, sin decirlo | low | defer | Un «al menos N» exigiría exponer el recorrido truncado |
| 7 | Ciego | Los `CLAUDE.md` anidados (`a/` y `a/b/`) cuentan por separado; el `.git` archivo (submódulo) no cuenta | low | rechazado | Comportamiento documentado en la spec y fijado por una prueba |
| 8 | Ciego | El módulo importa `_norm` de otro módulo | low | rechazado | La spec lo pedía para normalizar igual que el recorrido |
| 9 | Ciego | El umbral está en tres sitios (constante, esquema, documentos) | low | rechazado | El esquema documenta el mínimo; la constante manda |
| 10 | Ciego | El aviso no nombra las carpetas ni dice cómo repetir la revisión | low | rechazado | Decidido por Alex: sin nombres, por privacidad |
| 11 | Casos límite | `wide_folder = 1` desde un `DatosReporte` hecho a mano rompería el esquema | low | rechazado | Solo `auditar` aplica el umbral y el único camino de producción es la compuerta; lo cubre la prueba (c) del patch 1 |
| 12 | Casos límite | Un error del callback de avance aborta la revisión | false | rechazado | Ya cubierto en la Historia 41: `Avance.__call__` atrapa cualquier excepción |
| 13 | Ciego | La plantilla del HTML no está en el diff | false | rechazado | Descuido al armar el diff; está implementada (`#wide`, `WIDE_TXT`) y el revisor de brechas la vio |

## Design Notes

Texto del aviso, igual en todas las variantes (sin pronombres): ES «Esta carpeta contiene {n} carpetas que parecen proyectos distintos. El reporte mezcla los hallazgos de todas; para un reporte más claro conviene revisar un proyecto a la vez.» EN «This folder contains {n} folders that look like separate projects. The report mixes the findings of all of them; for a clearer report, review one project at a time.»

Por qué no manifiestos: un monorepo legítimo tiene muchos `package.json` y es un solo proyecto. Por qué estos puntos de partida: son los que usa un agente para decidir cuál es «su» proyecto (`.claude`, `CLAUDE.md`, `opencode.json`) o un repositorio aparte (`.git`). **Calibración hecha al revisar la spec (solo nombres de ruta, sin leer contenidos):** en `proyecto real local` solo existe el `.git/config` de la propia raíz, que no cuenta: **0 carpetas internas, sin aviso** (no hay falso positivo en el proyecto real). En `C:\dev` hay más de 20 (AgentReach, `proyecto`, `proyecto-opencode-sin-read` y los repositorios de `trampas-git`): el aviso se enciende con claridad. El proyecto de prueba del oráculo revisado desde su raíz también avisa, y es lo correcto; no altera sus conteos porque el aviso no es un hallazgo.

## Verification

**Commands:**
- `uv run ruff check src tests` -- expected: All checks passed
- `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach uv run pytest -q` -- expected: todo pasa; el oráculo no se omite
- `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach uv run --with playwright pytest -q tests/test_historia_44.py` -- expected: pasan en navegador real

**Manual checks (if no CLI):**
- Alex ejecuta `agentreach` sobre `C:\dev` y ve el aviso; sobre proyecto real local y no lo ve.
