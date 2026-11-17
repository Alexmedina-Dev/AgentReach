---
title: 'Historia 42: «Cómo leer este reporte», en corto'
type: 'feature'
created: '2026-11-12'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-6-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** La sección «Cómo leer este reporte» muestra a la vista 4 términos (los tres niveles y el camino de alcance) con tres bloques cada uno («Qué es», «Qué significa», «Qué puedes hacer»): unas 360 palabras antes del primer hallazgo. Alex: «esta sección está muy extensa, debe ser menos y que se entienda mejor».

**Approach:** Solo cambia la vista HTML (`renderHowto` y estilos). A la vista queda la frase de introducción y la frase corta (`line`) de cada uno de los 4 términos, con un máximo de 80 palabras en total; el detalle («Qué es», «Qué significa», «Qué puedes hacer») va plegado en un «Ver más» dentro de cada término, con el texto del catálogo sin cambios. El catálogo de términos (AD-16) y los datos no se tocan; el único texto nuevo es la etiqueta «Ver más» / «See more» en los diccionarios de la plantilla. Los otros 8 términos siguen plegados en «Otros términos». La vista Imprimir saca la versión corta, abierta. Los `id` `term-<id>` se conservan.

</frozen-after-approval>

## Implementation Notes

- Cambiar `src/agentreach/reporting/plantilla_reporte.html` y su copia idéntica `docs/reporte-html/plantilla.html` (una prueba las compara); no tocar `core/catalogo_terminos.py` ni `html.py`.
- `HOW_OPEN` (4 ids) se conserva; `renderHowto` (~l.1121) pasa de `card(x)` a una fila con `x.line` y un `<details>` «Ver más» que lleva `card(x, false)`. Conservar `wasOpen`/`openIds` para que cambiar de idioma no cierre lo que la persona abrió.
- Imprimir: hoy `beforeprint` abre los términos plegados; ahora la impresión muestra la versión corta (sin abrir el detalle).
- Las pruebas de la Historia 33 (`tests/test_historia_33.py`, `tests/test_historia_33_navegador.py`) pueden suponer el detalle a la vista: ajustarlas solo en eso, con un comentario.
- Prueba nueva `tests/test_historia_42.py`: cuenta las palabras visibles por defecto (≤ 80, ES y EN), el texto completo sigue en la página, `term-<id>` conservados, `<details>` nativo.
- No verificado: vista en navegador real (Alex).

## Review Triage Log

| # | Revisor | Hallazgo | Veredicto | Ruta | Evidencia |
|---|---------|----------|-----------|------|-----------|
| 1 | Ciego | En papel solo se abre la sección y se pierde el detalle («Qué es», etc.) | low | rechazado | Decidido en la ficha: la impresión sale en corto; el detalle sigue en los datos y en pantalla |
| 2 | Ciego | Los cuatro «Ver más» suenan igual con lector de pantalla | medium | patch (hecho) | Cada uno lleva el nombre del término en un texto solo para lectores (`.sr`) |
| 3 | Ciego | `brief` puede dejar el término sin nombre (la frase no empieza por el nombre) | medium | patch (hecho) | Comprobado: nombre «Nivel comprobado» y frase «Comprobado: …». Se pone en negrita lo que va antes de los dos puntos; sin etiqueta, se antepone el nombre; prueba de las 4 frases en ES y EN |
| 4 | Ciego | Prueba de 80 palabras frágil y con tolerancia «4» inventada | low | patch (hecho) | El navegador cuenta el texto tras quitar `Ver más`, plegados y encabezados |
| 5 | Ciego | Los enlaces a `#term-…` (Historia 36) aterrizan en el resumen sin abrir el detalle | medium | defer | Aún no existen esos enlaces; se anota para la Historia 36 |
| 6 | Ciego | Sin comprobación tras `afterprint` y riesgo de `howWas` con nodos sueltos | low | patch (hecho) | Prueba que restaura lo abierto y repite la impresión tras cambiar de idioma; `afterprint` ya vacía `howWas` |
| 7 | Ciego | Sin `:focus-visible` en el nuevo `summary` | false | rechazado | Existe una regla global `:focus-visible` (plantilla l.74) |
| 8 | Ciego | Contraste de `strong` en tema claro | false | rechazado | Usa `--text`, el mismo color del cuerpo |
| 9 | Ciego | Flecha de `summary` distinta en Safari | low | rechazado | Mismo patrón que `details.fold`; Safari no es objetivo |
| 10 | Ciego | `data-more` sin `esc()` | low | patch (hecho) | Ahora `esc(x.id)` |
| 11 | Ciego | El control «Ver más» sale como botón muerto al imprimir | low | patch (hecho) | `@media print { .howto details.more { display: none } }` |
| 12 | Ciego | Sin prueba de que la etiqueta cambie con el idioma | low | patch (hecho) | La prueba de navegador comprueba «Ver más» y «See more» |
