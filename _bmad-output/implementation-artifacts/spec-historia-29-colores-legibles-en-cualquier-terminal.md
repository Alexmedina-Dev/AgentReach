---
title: 'Historia 29: el logo se lee en cualquier fondo de terminal'
type: 'bugfix'
created: '2026-11-11'
status: 'done'
route: 'dispatch'
baseline_commit: 'b4c47638770eb8394d590df0f426000f754cfdcb'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-4-context.md'
  - '{project-root}/docs/presentacion-terminal/vista-previa/logo-temas.html'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** El logo se dibuja con la paleta de fondo oscuro cuando AgentReach no sabe el tema (Orca y Windows Terminal no definen `COLORFGBG`). Sobre blanco «AGENT» (#EAF4F2) tiene 1,1:1 y «REACH» (#3DF5D0) 1,4:1: casi no se ven. Además el tema viaja como un `bool`, así que no existe el estado «no sé».

**Approach:** Tema de tres estados (claro, oscuro, desconocido). Con fondo conocido, «REACH» conserva el matiz menta y solo mueve su luminosidad hasta 3:1; «AGENT» usa #EAF4F2 o #0B1114, el de más contraste. Sin saber el fondo, no se adivina: «AGENT» usa el texto normal de la terminal y «REACH» un menta-teal (#07856C) legible en blanco y en negro (4,5:1 con ambos); en 16 colores, «REACH» usa el cian normal (36).

## Boundaries & Constraints

**Always:** Solo biblioteca estándar. Sin color, `NO_COLOR` o salida no terminal, nada cambia (no hay banner). Prioridad: `--tema` > `AGENTREACH_TEMA` > `COLORFGBG` > desconocido. `COLORFGBG` solo da claro/oscuro: se asume blanco o negro puro. En fondo oscuro conocido, los colores siguen siendo exactamente #EAF4F2 y #3DF5D0. Mismo criterio en banner grande, mediano y mínimo (incluido el respaldo ASCII) y en `doctor`.

**Never:** Consultar el color de fondo a la terminal (OSC 11): leer la entrada de la terminal choca con FR-30 y con la Historia 7.4 (M1), y no se puede verificar fuera de una terminal real; queda como historia aparte tras la prueba de Alex en Orca. No cambiar los colores del cuerpo del reporte (comprobado, potencial…): salvo el logo, el comportamiento sin tema conocido queda como hoy. No tocar niveles ni el oráculo ni `resolver_tema` (su contrato `bool` lo prueban los tests actuales).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Fondo claro conocido | `--tema claro` o `COLORFGBG=0;15`, 24 bits | AGENT #0B1114 (19,0:1), REACH ≈ #08A585 (≥3:1 sobre blanco) | N/A |
| Fondo oscuro conocido | `--tema oscuro` o `COLORFGBG=15;0` | AGENT #EAF4F2, REACH #3DF5D0, sin cambios | N/A |
| Fondo desconocido, 24 bits | sin opción ni variables | AGENT sin color propio (texto normal), REACH #07856C | N/A |
| Fondo desconocido, 16 colores | sin opción ni variables | AGENT sin color propio, REACH `ESC[36m`; nunca `97` ni `96` | N/A |
| Fondo RGB cualquiera (función pura) | malla de miles de colores | REACH ≥3:1 con matiz menta; si ninguna luminosidad llega, la de más contraste entre 20 % y 80 % | Si el fondo es casi menta y no llega, cae al caso «desconocido» y se registra |
| Sin color / no terminal | `NO_COLOR`, tubería | Sin banner, sin `ESC` | N/A |

</frozen-after-approval>

## Code Map

- `src/agentreach/reporting/formato.py` -- `_PALETA` (roles `marca_agent`, `marca_reach`), `resolver_tema` (bool, se conserva), `pintar`; aquí van el estado «desconocido» y los colores de marca por fondo.
- `src/agentreach/reporting/marca.py` -- `banner`, `_letras`, `_minimo`, `_mediano_ascii`: reciben `claro: bool` y deben aceptar `None` (desconocido).
- `src/agentreach/cli/__init__.py` -- tres sitios deciden el tema: `_banner_si_corresponde` (~l.374), `_banner_segun_opciones` (~l.386), `doctor` (~l.418) y revisión (~l.621); el cuerpo del reporte sigue usando el `bool`.
- `tests/test_presentacion_marca.py` -- hoy suponen «sin tema = oscuro» en `test_los_colores_de_24_bits_son_exactamente_los_de_la_marca` (l.199) y `test_en_16_colores_con_fondo_claro...` (l.530); y los colores claros viejos (#1E3A34, #005F4D) en l.322.
- `docs/presentacion-terminal/vista-previa/logo-temas.html` -- referencia visual aprobada; sus valores sirven de control.

## Tasks & Acceptance

**Execution:**
- [ ] `src/agentreach/reporting/formato.py` -- función pura que, dado un fondo RGB, devuelve (AGENT, REACH) con el algoritmo de las Boundaries; constante del color universal; función que resuelve el tema en tres estados -- base testeable sin terminal
- [ ] `src/agentreach/reporting/marca.py` -- pintar el logo con esos colores y con el caso desconocido (24 bits y 16 colores) en los tres tamaños y en ASCII -- el arreglo visible
- [ ] `src/agentreach/cli/__init__.py` -- pasar el estado desconocido al banner de la revisión, `doctor`, `--help` y sin argumentos; el cuerpo sigue con `bool` -- cableado mínimo
- [ ] `tests/test_historia_29.py` -- contraste sobre la lista de fondos reales (blanco, #F2F2F2, #F6F8FA, #FDF6E3, #FBF1C7, #002B36, negro, #0C0C0C, #282A36, #282C34, #1A1B26, #808080, #000080), distinción AGENT/REACH, barrido de una malla RGB (≥4000 colores), valores de referencia exactos, caso desconocido en 24 y 16 colores -- cubre la matriz
- [ ] `tests/test_presentacion_marca.py` -- las pruebas que suponían «sin tema = oscuro» pasan a pedir `--tema oscuro`; la de fondo claro espera los colores nuevos -- cambio deliberado, con comentario
- [ ] `_bmad-output/implementation-artifacts/spec-historia-29-*.md` e `historias-mvp.md` -- Estado y «no verificado» al terminar

**Acceptance Criteria:**
- Given sin tema detectable, when se dibuja el logo en 24 bits o 16 colores, then ningún color propio de «AGENT» y «REACH» baja de 4,5:1 contra blanco ni contra negro.
- Given cualquier fondo de la lista y de la malla, when se calculan los colores, then «REACH» llega a 3:1 o cae al caso desconocido, y «AGENT» y «REACH» se distinguen (contraste entre ellos ≥1,5:1 o matiz distinto).
- Given `ruff` y la suite, when se ejecutan con `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach`, then pasan sin omitir el oráculo ni las reglas no negociables.

## Implementation Notes

- `formato.py`: `colores_de_marca(fondo_rgb)`, `resolver_tema_marca` (tres estados), `REACH_UNIVERSAL` (#07856C), `contraste`; `pintar` acepta `claro=None`.
- Con 3:1 exacto, el blanco da REACH #09A888 y el gris #808080 da #6BF7DB (el spec dice «≈ #08A585» y «≈ #6DF8DC»).
- Aprox. 18 % de una malla RGB uniforme cae al caso «desconocido» (fondos de luminancia media donde el menta limitado a 20-80 % no llega a 3:1).
- Pendiente: verificación visual de Alex en Orca.

## Spec Change Log

## Review Triage Log

| # | Revisor | Hallazgo | Veredicto | Ruta | Evidencia |
|---|---------|----------|-----------|------|-----------|
| 1 | Brechas | `doctor` y la revisión no tienen prueba con tema desconocido | medium | patch (hecho) | Solo `--help` pasaba por el cableado; revertir `claro_marca` hace fallar 2 pruebas nuevas (mutación comprobada) |
| 2 | Casos límite y ciego | `colores_de_marca` sin uso en runtime; dos fuentes de verdad | low | patch (hecho) | Prueba que ata `_PALETA` con la función para blanco y negro; ya coincidían |
| 3 | Casos límite | REACH <3:1 sobre fondos crema con `--tema claro` | low | rechazado | El tema claro/oscuro asume blanco o negro puro; el fondo RGB real espera la Historia 31 |
| 4 | Ciego | Versión y lema del banner sin tema siguen en paleta oscura (lema 1,9:1 sobre blanco) | medium | patch (hecho) | Roles `marca_sec` y `marca_lema`; sin tema, gris 767676 (≥4,5:1) y ESC[90m en 16 colores |
| 5 | Ciego | Sin detección, Windows Terminal y Orca ven el menta-teal de reserva aun en oscuro | low | diferido | Compromiso aprobado en la spec; lo resuelve la Historia 31 (`deferred-work.md`) |
| 6 | Casos límite y ciego | Centinela `_SIN_DECIDIR` tipado como `object` | low | rechazado | Función privada con dos llamadores fijos; sin daño demostrado |
| 7 | Casos límite y ciego | `COLORFGBG` con un solo valor, `default;default` o índice >15 | low | rechazado | Igual que el `fondo_claro` previo; `_tema_colorfgbg` ya devuelve desconocido fuera de 0 a 15 |
| 8 | Casos límite y ciego | `AGENTREACH_TEMA` inválido se ignora en silencio | low | rechazado | Igual que `resolver_tema` antes de esta historia |
| 9 | Casos límite | `colores_de_marca` sin validar canales | low | rechazado | Uso interno con tuplas propias |
| 10 | Casos límite y ciego | El cian normal (36) no garantiza 4,5:1 | low | rechazado | Lo decide la paleta del tema del usuario; se declara en «no verificado» |
| 11 | Ciego | Aserción de «se distinguen» casi siempre verdadera | low | patch (hecho) | Reemplazada por saturación HLS (REACH ≥0,5, AGENT ≤0,35) o contraste ≥1,5 |
| 12 | Ciego | Cota 0,1<luminancia<0,5 sin justificar en el barrido | low | rechazado | Es de prueba, no de producto |
| 13 | Ciego | Comentario de `_PALETA` desactualizado | low | patch (hecho) | Corregido |
| 14 | Ciego | Nombre `contraste` repetido entre formato y una prueba | low | rechazado | Alcances distintos, sin colisión real |
| 15 | Ciego | `resolver_tema` y `resolver_tema_marca` casi duplicadas | low | rechazado | Tocaría una función con contrato probado; se reevalúa con la Historia 31 |
| 16 | Ciego | Costo y log INFO de `colores_de_marca` en cada banner | false | rechazado | Esa función no se llama en ejecución |
| 17 | Brechas | `pintar` con `claro=None` en otros roles sin prueba | low | rechazado | Comportamiento documentado en el docstring y sin cambio respecto a antes |

## Design Notes

Luminancia que da el mismo contraste con blanco y con negro: (L+0,05) = √(1,05·0,05) → L ≈ 0,179; con eso un solo color cumple 4,5:1 en ambos fondos. Ejemplo de control: fondo #FFFFFF → AGENT #0B1114, REACH ≈ #08A585; fondo #808080 → REACH ≈ #6DF8DC.

## Verification

**Commands:**
- `uv run ruff check src tests` -- expected: All checks passed
- `AGENTREACH_PROYECTO_PRUEBA=C:/dev/proyecto-prueba-agentreach uv run pytest -q` -- expected: todo pasa; el oráculo no se omite

**Manual checks (if no CLI):**
- Alex ejecuta `agentreach` en Orca (fondo claro) y confirma que «AGENT» y «REACH» se leen y combinan.
