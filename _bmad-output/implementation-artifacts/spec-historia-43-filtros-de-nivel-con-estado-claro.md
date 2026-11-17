---
title: 'Historia 43: los filtros de nivel dicen cuál está activo y qué muestran'
type: 'feature'
created: '2026-11-12'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** En el reporte HTML, las fichas «Caminos / Comprobado / Potencial / Hipótesis» son filtros, pero la activa y la inactiva se parecen: la inactiva solo pasa a fondo sólido con el número tachado (parece un dato borrado) y «Caminos», que es solo el total, se ve como un botón más. Alex: «no se colorea el contenedor de la sección seleccionada, no sé qué se está mostrando».

**Approach:** Solo cambia la plantilla HTML (y su copia en `docs/`). La ficha activa se rellena con un tinte de su color de nivel, con borde de su color y una marca de forma (✓); la inactiva queda apagada (sin tinte, borde discontinuo gris, marca ○) y sin tachar; «Caminos» se ve como un total, no como un botón. Una línea bajo las fichas dice qué se muestra («Mostrando 3 de 5 caminos · Niveles: Potencial») y se actualiza con cada filtro. Los demás grupos de selección (pestañas de agente, vistas, idioma, tema) se revisan: su estado seleccionado ya lleva relleno menta; solo se corrige lo que no se distinga con contraste 3:1 o dependa solo del color. No cambia ningún hallazgo ni su nivel.

## Boundaries & Constraints

**Always:** Estados `aria-pressed` y `aria-selected` intactos; foco visible; los textos nuevos van en los diccionarios es y en de la plantilla (sin «tú» ni «usted» fijo), la línea con `aria-live="polite"`; funciona en tema claro, oscuro y contraste alto; la copia `docs/reporte-html/plantilla.html` queda idéntica.

**Never:** Tocar `html.py`, el catálogo, los niveles, el esquema de datos ni la lógica de filtrado (`visible()`); añadir dependencias; usar solo el color para el estado.

</frozen-after-approval>

## Implementation Notes

- `src/agentreach/reporting/plantilla_reporte.html` y `docs/reporte-html/plantilla.html`: CSS de `.kpi` (l.137-144), `renderSummary` (~l.1238), un `<p id="showing">` bajo `#kpis`, y `showing`, `showingNone`, `allLevels` en `T_`.
- Pruebas: `tests/test_historia_43.py` (estáticas y de navegador con Playwright si está disponible); revisar pruebas existentes que dependan de `.kpi`, `line-through` o `style="border-color`.
- No verificado: vista en navegador real de Alex y contraste alto del sistema.
- Decisión al implementar: el reporte no deja apagar el último nivel activo (`S.levels.size>1`), así que «ningún nivel activo» no existe; se quitó ese texto de la ficha. La línea muestra solo los niveles visibles («Niveles visibles: …»), porque la cuenta de caminos ya la da `#status`. La ficha del último nivel activo lleva `aria-disabled` y un título que lo explica.

## Review Triage Log

| # | Revisor | Hallazgo | Veredicto | Ruta | Evidencia |
|---|---------|----------|-----------|------|-----------|
| 1 | Ciego | El último nivel activo no se puede apagar y la interfaz no lo dice | medium | patch (hecho) | `aria-disabled` y título «Siempre queda un nivel activo» en esa ficha; prueba |
| 2 | Ciego | El foco se pierde al pulsar una ficha (se reconstruye `#kpis`) | medium | patch (hecho) | Se devuelve el foco a la ficha pulsada; prueba con teclado |
| 3 | Ciego | La línea «Mostrando n de m» solo refleja el nivel y compite con la cuenta de `#status` | medium | patch (hecho) | La línea dice solo los niveles visibles; la cuenta sigue en `#status` |
| 4 | Ciego | `aria-live` anuncia en cada render | medium | patch (hecho) | El texto solo se reescribe si cambia |
| 5 | Ciego | Los niveles se distinguen solo por color | low | rechazado | Cada ficha lleva su icono y su nombre; el estado activo/apagado va por ✓/○ y borde, no por color |
| 6 | Ciego | El borde cambia de 2 a 1 px y mueve la ficha | low | patch (hecho) | Ambos estados usan 2 px; prueba de móvil a 360 px sin desborde |
| 7 | Ciego | Sin respaldo de `color-mix` ni en contraste alto o impresión | low | rechazado | Sin `color-mix` queda el fondo base con borde y marca; en contraste alto y en papel el estado se distingue por forma |
| 8 | Ciego | Faltan pruebas (contraste de las fichas, singular, Hipótesis punteada) | low | rechazado | El estado se prueba por forma; el contraste de borde y texto usa los tokens existentes |
| 9 | Ciego | La prueba de los demás grupos es alcance de más | false | rechazado | La ficha de la historia pide revisar esos grupos |
